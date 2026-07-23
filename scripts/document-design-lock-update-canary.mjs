import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import {
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { isAbsolute, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  computeSkillFolderHash,
  migrateDocumentDesignProject,
  verifyCanonicalDocumentDesignProject,
} from './document-design-lock-migration.mjs';
import { buildCommandInvocation } from './journalism-core-install-canary.mjs';

export const SKILLS_CLI_VERSION = '1.5.20';
export const CODEX_CLI_VERSION = '0.145.0';
export const HISTORICAL_SOURCE_COMMIT = '64dc95d8584d66e35ceb79e3c43e7fa3d201d3e4';
export const HISTORICAL_CONTENT_HASH =
  '1a388f259e5894a04617d8b599719ec5e1adcf778eec81dbdf8324816b1ed8dc';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const FIXTURE_PATH = join(ROOT, 'scripts', 'fixtures', 'document-design-lock-v1.json');
const SOURCE_SKILL_PATH = 'pdf-playground/skills/document-design';
const REMOTE_URL = 'https://github.com/jamditis/claude-skills-journalism.git';
const REMOTE_REF = 'refs/heads/master';
const SUBPROCESS_TIMEOUT_MS = 180_000;

function digest(value) {
  return createHash('sha256').update(value).digest('hex');
}

function stripAnsi(value) {
  return value.replace(/\u001b\[[0-?]*[ -/]*[@-~]/gu, '');
}

function runCommand(command, args, { cwd = ROOT, env = process.env } = {}) {
  const invocation = buildCommandInvocation(command, args, { env });
  return spawnSync(invocation.command, invocation.args, {
    cwd,
    encoding: 'utf8',
    env,
    maxBuffer: 10 * 1024 * 1024,
    shell: false,
    timeout: SUBPROCESS_TIMEOUT_MS,
    windowsHide: true,
  });
}

function commandOutput(result) {
  return stripAnsi(`${result.stdout ?? ''}${result.stderr ?? ''}`);
}

function assertStatus(result, expected, label) {
  if (result.error) throw result.error;
  if (result.signal) throw new Error(`${label} ended with signal ${result.signal}`);
  if (result.status !== expected) {
    throw new Error(`${label} exited ${result.status}; expected ${expected}:\n${commandOutput(result)}`);
  }
}

function runGit(args, { encoding = 'utf8' } = {}) {
  const result = spawnSync('git', args, {
    cwd: ROOT,
    encoding,
    maxBuffer: 10 * 1024 * 1024,
    shell: false,
    timeout: SUBPROCESS_TIMEOUT_MS,
  });
  assertStatus(result, 0, `git ${args[0]}`);
  return result.stdout;
}

function remoteMasterCommit() {
  const output = runGit(['ls-remote', REMOTE_URL, REMOTE_REF]).trim();
  const [commit, ref, extra] = output.split(/\s+/u);
  if (!/^[a-f0-9]{40}$/u.test(commit ?? '') || ref !== REMOTE_REF || extra !== undefined) {
    throw new Error(`could not resolve exactly one ${REMOTE_REF} commit`);
  }
  return commit;
}

function materializeHistoricalSkill(project) {
  const list = runGit([
    'ls-tree',
    '-r',
    '--name-only',
    HISTORICAL_SOURCE_COMMIT,
    '--',
    SOURCE_SKILL_PATH,
  ]);
  const repoPaths = list.trim().split('\n').filter(Boolean);
  if (repoPaths.length === 0) throw new Error('historical document-design tree is empty');

  const installedRoot = join(project, '.agents', 'skills', 'document-design');
  for (const repoPath of repoPaths) {
    const relativePath = relative(SOURCE_SKILL_PATH, repoPath);
    if (
      !relativePath
      || relativePath.startsWith('..')
      || isAbsolute(relativePath)
    ) {
      throw new Error(`historical skill path escaped its source root: ${repoPath}`);
    }
    const destination = join(installedRoot, relativePath);
    mkdirSync(resolve(destination, '..'), { recursive: true });
    const content = runGit(
      ['show', `${HISTORICAL_SOURCE_COMMIT}:${repoPath}`],
      { encoding: null },
    );
    writeFileSync(destination, content);
  }
  const contentHash = computeSkillFolderHash(installedRoot);
  if (contentHash !== HISTORICAL_CONTENT_HASH) {
    throw new Error(`historical content hash drifted: ${contentHash}`);
  }
  return installedRoot;
}

function removeCanaryRoot(directory) {
  const temporaryRoot = resolve(tmpdir());
  const resolved = resolve(directory);
  const pathFromTemporaryRoot = relative(temporaryRoot, resolved);
  if (
    !pathFromTemporaryRoot
    || pathFromTemporaryRoot.startsWith('..')
    || isAbsolute(pathFromTemporaryRoot)
    || !pathFromTemporaryRoot.startsWith('document-design-lock-canary-')
  ) {
    throw new Error(`refusing to remove non-canary path: ${resolved}`);
  }
  rmSync(resolved, { recursive: true, force: true });
}

export function runDocumentDesignLockCanary() {
  const canaryRoot = mkdtempSync(join(tmpdir(), 'document-design-lock-canary-'));
  try {
    const project = join(canaryRoot, 'project');
    const cache = join(canaryRoot, 'npm-cache');
    const clientHome = join(canaryRoot, 'home');
    mkdirSync(project);
    mkdirSync(cache);
    mkdirSync(clientHome);
    const installedRoot = materializeHistoricalSkill(project);
    const fixtureBytes = readFileSync(FIXTURE_PATH);
    const lockPath = join(project, 'skills-lock.json');
    writeFileSync(lockPath, fixtureBytes);

    const env = {
      ...process.env,
      DISABLE_TELEMETRY: '1',
      DO_NOT_TRACK: '1',
      HOME: clientHome,
      USERPROFILE: clientHome,
      npm_config_cache: cache,
    };
    const npxArgs = ['--yes', `skills@${SKILLS_CLI_VERSION}`];
    const sourceCommit = remoteMasterCommit();
    const sourceHash = computeSkillFolderHash(join(ROOT, SOURCE_SKILL_PATH));
    const initialLockDigest = digest(fixtureBytes);

    const codexVersion = runCommand('codex', ['--version'], { env });
    assertStatus(codexVersion, 0, 'codex --version');
    assert.match(commandOutput(codexVersion), new RegExp(`codex-cli ${CODEX_CLI_VERSION}\\b`, 'u'));

    const skillsVersion = runCommand('npx', [...npxArgs, '--version'], { env });
    assertStatus(skillsVersion, 0, 'skills --version');
    assert.match(commandOutput(skillsVersion), new RegExp(`^${SKILLS_CLI_VERSION}\\b`, 'mu'));

    const prechange = runCommand(
      'npx',
      [...npxArgs, 'update', '--project', '-y'],
      { cwd: project, env },
    );
    assertStatus(prechange, 1, 'historical-key update');
    assert.match(commandOutput(prechange), /Failed to update Document design/u);
    assert.equal(digest(readFileSync(lockPath)), initialLockDigest);
    assert.equal(computeSkillFolderHash(installedRoot), HISTORICAL_CONTENT_HASH);

    const migration = migrateDocumentDesignProject(project);
    assert.equal(migration.status, 'migrated');

    const firstUpdate = runCommand(
      'npx',
      [...npxArgs, 'update', '--project', '-y'],
      { cwd: project, env },
    );
    assertStatus(firstUpdate, 0, 'first canonical update');
    assert.match(commandOutput(firstUpdate), /Updated document-design/u);
    const first = verifyCanonicalDocumentDesignProject(project);
    assert.equal(first.computedHash, sourceHash);
    assert.equal(remoteMasterCommit(), sourceCommit);
    const firstLockBytes = readFileSync(lockPath);
    assert.deepEqual(
      Object.keys(JSON.parse(firstLockBytes.toString('utf8')).skills),
      ['document-design'],
    );

    const secondUpdate = runCommand(
      'npx',
      [...npxArgs, 'update', '--project', '-y'],
      { cwd: project, env },
    );
    assertStatus(secondUpdate, 0, 'second canonical update');
    assert.match(commandOutput(secondUpdate), /Updated document-design/u);
    const second = verifyCanonicalDocumentDesignProject(project);
    assert.equal(second.computedHash, first.computedHash);
    assert.deepEqual(readFileSync(lockPath), firstLockBytes);
    assert.equal(remoteMasterCommit(), sourceCommit);

    return {
      client: `Codex CLI ${CODEX_CLI_VERSION}`,
      finalContentHash: second.computedHash,
      finalLockDigest: digest(firstLockBytes),
      fixtureDigest: initialLockDigest,
      historicalContentHash: HISTORICAL_CONTENT_HASH,
      prechangeExit: prechange.status,
      skillsCli: `skills CLI ${SKILLS_CLI_VERSION}`,
      sourceCommit,
      updateExits: [firstUpdate.status, secondUpdate.status],
    };
  } finally {
    removeCanaryRoot(canaryRoot);
  }
}

const invokedPath = process.argv[1] ? resolve(process.argv[1]) : '';
if (invokedPath === fileURLToPath(import.meta.url)) {
  try {
    console.log(JSON.stringify(runDocumentDesignLockCanary(), null, 2));
  } catch (error) {
    assert(error instanceof Error);
    console.error(error.message);
    process.exitCode = 1;
  }
}
