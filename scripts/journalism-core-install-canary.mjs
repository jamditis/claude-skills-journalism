import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync } from 'node:fs';
import { basename, isAbsolute, join, relative, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';

export const EXPECTED_SKILL_NAMES = [
  'ai-writing-detox',
  'crisis-communications',
  'data-journalism',
  'editorial-workflow',
  'fact-check-workflow',
  'foia-requests',
  'interview-prep',
  'interview-transcription',
  'newsletter-publishing',
  'newsroom-style',
  'photo-metadata',
  'social-media-intelligence',
  'source-verification',
  'story-pitch',
];

const PLUGIN_ID = 'journalism-core@claude-skills-journalism';
const EXPECTED_VERSION = '1.2.0';
export const SUBPROCESS_TIMEOUT_MS = 180_000;

export function buildCommandPlan(client, repoRoot, tempRoot) {
  if (client === 'claude') {
    return {
      envName: 'CLAUDE_CONFIG_DIR',
      commands: [
        ['claude', ['plugin', 'validate', '--strict', repoRoot]],
        ['claude', ['plugin', 'marketplace', 'add', repoRoot, '--scope', 'user']],
        ['claude', ['plugin', 'install', PLUGIN_ID, '--scope', 'user']],
        ['claude', ['plugin', 'list', '--json']],
      ],
    };
  }

  if (client === 'codex') {
    return {
      envName: 'CODEX_HOME',
      commands: [
        ['codex', ['plugin', 'marketplace', 'add', repoRoot, '--json']],
        ['codex', ['plugin', 'add', PLUGIN_ID, '--json']],
        ['codex', ['plugin', 'list', '--json']],
      ],
    };
  }

  if (client === 'codex-skills') {
    return {
      cwd: tempRoot,
      commands: [[
        'skills',
        [
          'add',
          join(repoRoot, 'journalism-core'),
          '--skill',
          '*',
          '--agent',
          'codex',
          '--copy',
          '-y',
        ],
      ]],
    };
  }

  throw new Error(`Unsupported client: ${client}`);
}

function findSkillNames(directory, names = []) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) findSkillNames(path, names);
    else if (entry.isFile() && entry.name === 'SKILL.md') names.push(basename(resolve(path, '..')));
  }
  return names.sort();
}

function findFiles(directory, root = directory, files = []) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) findFiles(path, root, files);
    else if (entry.isFile()) files.push(relative(root, path).replaceAll('\\', '/'));
  }
  return files.sort();
}

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex');
}

export function verifyCopiedSkillTree(sourceSkillsPath, installedSkillsPath) {
  const sourceFiles = findFiles(sourceSkillsPath);
  const installedFiles = findFiles(installedSkillsPath);
  if (JSON.stringify(installedFiles) !== JSON.stringify(sourceFiles)) {
    throw new Error('Installed skill resource paths differed from the source package');
  }
  for (const path of sourceFiles) {
    if (sha256(join(sourceSkillsPath, path)) !== sha256(join(installedSkillsPath, path))) {
      throw new Error(`Installed skill resource content differed from source: ${path}`);
    }
  }
  return { fileCount: sourceFiles.length };
}

function assertPathInside(root, candidate) {
  const pathFromRoot = relative(resolve(root), resolve(candidate));
  if (!pathFromRoot || pathFromRoot.startsWith('..') || isAbsolute(pathFromRoot)) {
    throw new Error(`Install path escaped the disposable client home: ${candidate}`);
  }
}

export function verifyInstalledPackage(
  client,
  listOutput,
  tempRoot,
  installPathOverride,
  sourceSkillsPath,
) {
  let parsed;
  try {
    parsed = JSON.parse(listOutput);
  } catch (error) {
    throw new Error(`Could not parse ${client} plugin list JSON: ${error.message}`);
  }

  const records = client === 'claude' ? parsed : parsed.installed;
  if (!Array.isArray(records)) throw new Error(`${client} plugin list did not contain installed records`);

  const record = records.find((item) => (item.id ?? item.pluginId) === PLUGIN_ID);
  if (!record) throw new Error(`${PLUGIN_ID} was not listed as installed by ${client}`);
  if (record.version !== EXPECTED_VERSION) {
    throw new Error(`${client} installed version ${record.version}; expected ${EXPECTED_VERSION}`);
  }
  if (record.enabled !== true || (client === 'codex' && record.installed !== true)) {
    throw new Error(`${PLUGIN_ID} was not installed and enabled by ${client}`);
  }

  const installPath = installPathOverride ?? record.installPath;
  if (!installPath) throw new Error(`${client} did not report the installed package path`);
  assertPathInside(tempRoot, installPath);

  const skillsPath = join(installPath, 'skills');
  if (!existsSync(skillsPath)) throw new Error(`${client} install did not contain a skills directory`);
  const skillNames = findSkillNames(skillsPath);
  if (JSON.stringify(skillNames) !== JSON.stringify(EXPECTED_SKILL_NAMES)) {
    throw new Error(
      `The installed skill set did not match journalism-core: ${skillNames.join(', ')}`,
    );
  }

  const copied = sourceSkillsPath
    ? verifyCopiedSkillTree(sourceSkillsPath, skillsPath)
    : { fileCount: undefined };

  return { installPath, record, skillNames, fileCount: copied.fileCount };
}

function verifySourceContract(repoRoot) {
  const manifestPath = join(repoRoot, 'journalism-core', '.claude-plugin', 'plugin.json');
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  if (manifest.name !== 'journalism-core' || manifest.version !== EXPECTED_VERSION) {
    throw new Error('journalism-core Claude manifest does not match the canary contract');
  }

  const nativePaths = [
    join(repoRoot, '.agents', 'plugins', 'marketplace.json'),
    join(repoRoot, 'journalism-core', '.codex-plugin', 'plugin.json'),
  ];
  const nativeManifest = nativePaths.find((path) => existsSync(path));
  if (nativeManifest) throw new Error(`Phase one must not add a native Codex manifest: ${nativeManifest}`);
}

function verifyStandardsInstall(tempRoot, sourceSkillsPath) {
  const skillsPath = join(tempRoot, '.agents', 'skills');
  if (!existsSync(skillsPath)) throw new Error('Standards install did not create .agents/skills');
  const skillNames = findSkillNames(skillsPath);
  if (JSON.stringify(skillNames) !== JSON.stringify(EXPECTED_SKILL_NAMES)) {
    throw new Error(`The installed skill set did not match journalism-core: ${skillNames.join(', ')}`);
  }

  const lockPath = join(tempRoot, 'skills-lock.json');
  if (!existsSync(lockPath)) throw new Error('Standards install did not create skills-lock.json');
  const lock = JSON.parse(readFileSync(lockPath, 'utf8'));
  const lockNames = Object.keys(lock.skills ?? {}).sort();
  if (JSON.stringify(lockNames) !== JSON.stringify(EXPECTED_SKILL_NAMES)) {
    throw new Error(`The standards lock did not match journalism-core: ${lockNames.join(', ')}`);
  }
  for (const [name, record] of Object.entries(lock.skills)) {
    if (!/^[a-f0-9]{64}$/u.test(record.computedHash ?? '')) {
      throw new Error(`The standards lock has no content hash for ${name}`);
    }
  }

  const copied = verifyCopiedSkillTree(sourceSkillsPath, skillsPath);

  return { installPath: skillsPath, skillNames, fileCount: copied.fileCount };
}

function runCommand(command, args, env, cwd) {
  const result = spawnSync(command, args, {
    cwd,
    encoding: 'utf8',
    env,
    shell: process.platform === 'win32',
    timeout: SUBPROCESS_TIMEOUT_MS,
    windowsHide: true,
  });
  if (result.status !== 0) {
    const detail = `${result.stdout ?? ''}${result.stderr ?? ''}${result.error?.message ?? ''}`.trim();
    throw new Error(`${command} ${args.join(' ')} failed${detail ? `:\n${detail}` : ''}`);
  }
  return { stdout: result.stdout ?? '', stderr: result.stderr ?? '' };
}

function removeDisposableHome(client, directory) {
  const tempRoot = resolve(tmpdir());
  const resolved = resolve(directory);
  const pathFromTemp = relative(tempRoot, resolved);
  if (
    !pathFromTemp
    || pathFromTemp.startsWith('..')
    || isAbsolute(pathFromTemp)
    || !basename(resolved).startsWith(`journalism-core-${client}-`)
  ) {
    throw new Error(`Refusing to remove non-canary path: ${resolved}`);
  }
  rmSync(resolved, { recursive: true, force: true });
}

export function runInstallCanary(client, repoRoot) {
  const sourceRoot = resolve(repoRoot);
  verifySourceContract(sourceRoot);
  const tempRoot = mkdtempSync(join(tmpdir(), `journalism-core-${client}-`));
  const plan = buildCommandPlan(client, sourceRoot, tempRoot);
  const env = { ...process.env, DISABLE_TELEMETRY: '1', DO_NOT_TRACK: '1' };
  if (plan.envName) env[plan.envName] = tempRoot;

  try {
    const outputs = plan.commands.map(([command, args]) => runCommand(command, args, env, plan.cwd));
    const sourceSkillsPath = join(sourceRoot, 'journalism-core', 'skills');
    if (client === 'codex-skills') {
      const result = verifyStandardsInstall(tempRoot, sourceSkillsPath);
      console.log(
        `PASS codex standards path: ${result.skillNames.length} skills and ${result.fileCount} files`,
      );
      return result;
    }

    let installPath;
    if (client === 'codex') {
      try {
        installPath = JSON.parse(outputs[1].stdout).installedPath;
      } catch (error) {
        throw new Error(`Could not parse Codex install JSON: ${error.message}`);
      }
    }

    const result = verifyInstalledPackage(
      client,
      outputs.at(-1).stdout,
      tempRoot,
      installPath,
      sourceSkillsPath,
    );
    console.log(
      `PASS ${client}: ${result.skillNames.length} skills and ${result.fileCount} files at version ${EXPECTED_VERSION}`,
    );
    return result;
  } finally {
    removeDisposableHome(client, tempRoot);
  }
}

function runCli() {
  const client = process.argv[2];
  if (!['claude', 'codex', 'codex-skills'].includes(client)) {
    console.error('Usage: node scripts/journalism-core-install-canary.mjs <claude|codex|codex-skills>');
    process.exitCode = 2;
    return;
  }
  const repoRoot = fileURLToPath(new URL('..', import.meta.url));
  runInstallCanary(client, repoRoot);
}

const entryPoint = process.argv[1] ? pathToFileURL(resolve(process.argv[1])).href : '';
if (entryPoint === import.meta.url) runCli();
