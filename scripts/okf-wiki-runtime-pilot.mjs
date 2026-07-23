import { spawnSync } from 'node:child_process';
import {
  existsSync,
  lstatSync,
  readFileSync,
  readdirSync,
  realpathSync,
} from 'node:fs';
import {
  isAbsolute,
  relative,
  resolve,
} from 'node:path';
import { pathToFileURL } from 'node:url';
import { isDeepStrictEqual } from 'node:util';

export const OKF_PILOT_TIMEOUT_MS = 300_000;
export const OKF_VALIDATION_TIMEOUT_MS = 60_000;

const PORTABLE_FILES = Object.freeze([
  'README.md',
  'SPEC.md',
  'bundle/concepts/example-concept.md',
  'bundle/concepts/index.md',
  'bundle/decisions/example-concept.md',
  'bundle/decisions/index.md',
  'bundle/index.md',
  'requirements.txt',
  'scripts/validate.py',
]);

const CLAUDE_ADAPTER_FILES = Object.freeze([
  '.claude/hooks/okf-anchor.py',
  '.claude/hooks/okf-orient.py',
  '.claude/settings.json',
]);

const COPIED_RESOURCES = Object.freeze([
  Object.freeze({ source: 'requirements.txt', output: 'requirements.txt' }),
  Object.freeze({ source: 'spec/SPEC.md', output: 'SPEC.md' }),
  Object.freeze({ source: 'scripts/validate.py', output: 'scripts/validate.py' }),
  Object.freeze({
    source: 'templates/hooks/okf-anchor.py',
    output: '.claude/hooks/okf-anchor.py',
  }),
  Object.freeze({
    source: 'templates/hooks/okf-orient.py',
    output: '.claude/hooks/okf-orient.py',
  }),
]);

export const OKF_PILOT_FIXTURES = Object.freeze({
  'okf-1': Object.freeze({
    target: 'okf-1',
    title: 'Codex no-Claude pilot',
    sections: Object.freeze(['concepts', 'decisions']),
    portableFiles: PORTABLE_FILES,
    claudeAdapterFiles: CLAUDE_ADAPTER_FILES,
    prompt:
      '$okf-wiki Scaffold an internal-only empty OKF knowledge base at '
      + './okf-1 titled "Codex no-Claude pilot" with exactly the sections '
      + 'concepts and decisions. All onboarding choices are settled: scaffold '
      + 'only, do not populate from sources, and do not publish. Use the '
      + 'installed skill copy under .agents/skills/okf-wiki. No Claude '
      + 'configuration is available outside this project, and do not invoke '
      + 'any Claude executable. Keep the default Claude hook generation '
      + 'enabled so this pilot can record '
      + 'those files as inert Claude adapter output; do not execute the hooks '
      + 'or treat them as Codex configuration. Do not read or write outside '
      + 'this disposable project and its supplied client home. Run the '
      + 'scaffolder once, validate the portable bundle, and report the exact '
      + 'installed files read, commands run, files created, and any trust or '
      + 'approval prompt. Leave the generated project in place for verification.',
  }),
});

function fixtureFor(id) {
  if (!Object.hasOwn(OKF_PILOT_FIXTURES, id)) {
    throw new Error(`Unsupported okf-wiki fixture: ${id}`);
  }
  return OKF_PILOT_FIXTURES[id];
}

function childPath(root, child, label) {
  const absoluteRoot = resolve(root);
  const absoluteChild = resolve(absoluteRoot, child);
  const fromRoot = relative(absoluteRoot, absoluteChild);
  if (!fromRoot || fromRoot.startsWith('..') || isAbsolute(fromRoot)) {
    throw new Error(`${label} must resolve below the disposable project`);
  }
  return absoluteChild;
}

function requireDirectory(path, label) {
  if (!existsSync(path)) throw new Error(`Missing ${label}: ${path}`);
  const stat = lstatSync(path);
  if (!stat.isDirectory() || stat.isSymbolicLink()) {
    throw new Error(`${label} must be a real directory: ${path}`);
  }
}

function requireRegularFile(path, label) {
  if (!existsSync(path)) throw new Error(`Missing ${label}: ${path}`);
  const stat = lstatSync(path);
  if (!stat.isFile() || stat.isSymbolicLink()) {
    throw new Error(`${label} must be a regular file: ${path}`);
  }
}

function requireContainedRealPath(path, root, label) {
  const realRoot = realpathSync(root);
  const realPath = realpathSync(path);
  const fromRoot = relative(realRoot, realPath);
  if (!fromRoot || fromRoot.startsWith('..') || isAbsolute(fromRoot)) {
    throw new Error(`${label} escapes the installed skill root: ${path}`);
  }
}

function relativeFiles(root) {
  const files = [];

  function walk(directory, prefix = '') {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const relativePath = prefix ? `${prefix}/${entry.name}` : entry.name;
      const path = resolve(directory, entry.name);
      const stat = lstatSync(path);
      if (stat.isSymbolicLink()) {
        files.push(relativePath);
      } else if (stat.isDirectory()) {
        walk(path, relativePath);
      } else if (stat.isFile()) {
        files.push(relativePath);
      } else {
        throw new Error(`unsupported generated path: ${relativePath}`);
      }
    }
  }

  walk(root);
  return files.sort();
}

export function verifyNoClaudePreconditions(
  projectDir,
  clientHome,
  fixtureId,
  { allowOutput = false } = {},
) {
  const fixture = fixtureFor(fixtureId);
  const project = resolve(projectDir);
  const home = resolve(clientHome);
  requireDirectory(project, 'disposable project');
  requireDirectory(home, 'disposable client home');
  if (existsSync(resolve(project, '.claude'))) {
    throw new Error('disposable project must not contain .claude before the pilot');
  }
  if (existsSync(resolve(home, '.claude'))) {
    throw new Error('disposable client home must not contain .claude');
  }
  const target = childPath(project, fixture.target, 'Fixture target');
  if (!allowOutput && existsSync(target)) {
    throw new Error('fixture target must not already exist');
  }
  if (allowOutput) requireDirectory(target, 'generated fixture target');
  return { project, home, target };
}

export function verifyOkfInstall(projectDir, fixtureId) {
  fixtureFor(fixtureId);
  const project = resolve(projectDir);
  requireDirectory(project, 'disposable project');
  const skillRoot = childPath(
    project,
    '.agents/skills/okf-wiki',
    'Installed skill root',
  );
  requireDirectory(skillRoot, 'installed skill root');
  requireContainedRealPath(skillRoot, project, 'Installed skill root');
  const resources = [
    'SKILL.md',
    'requirements.txt',
    'scripts/scaffold.py',
    'scripts/validate.py',
    'spec/SPEC.md',
    'templates/hooks/okf-anchor.py',
    'templates/hooks/okf-orient.py',
  ];
  for (const resource of resources) {
    const resourcePath = resolve(skillRoot, resource);
    requireRegularFile(resourcePath, `installed resource ${resource}`);
    requireContainedRealPath(
      resourcePath,
      skillRoot,
      `installed resource ${resource}`,
    );
  }
  return { project, skillRoot, resources };
}

export function verifyOkfOutput(projectDir, fixtureId) {
  const fixture = fixtureFor(fixtureId);
  const project = resolve(projectDir);
  const target = childPath(project, fixture.target, 'Fixture target');
  requireDirectory(target, 'generated fixture target');

  const expected = [...fixture.portableFiles, ...fixture.claudeAdapterFiles].sort();
  const actual = relativeFiles(target);
  for (const relativePath of expected) {
    if (!actual.includes(relativePath)) {
      throw new Error(`missing generated file: ${relativePath}`);
    }
    const path = resolve(target, relativePath);
    const stat = lstatSync(path);
    if (!stat.isFile() || stat.isSymbolicLink()) {
      throw new Error(`generated file must be regular and not linked: ${relativePath}`);
    }
    requireContainedRealPath(path, target, `Generated file ${relativePath}`);
  }
  for (const relativePath of actual) {
    if (!expected.includes(relativePath)) {
      throw new Error(`unexpected generated file: ${relativePath}`);
    }
  }

  const skillRoot = childPath(
    project,
    '.agents/skills/okf-wiki',
    'Installed skill root',
  );
  requireDirectory(skillRoot, 'installed skill root');
  requireContainedRealPath(skillRoot, project, 'Installed skill root');
  for (const { source, output } of COPIED_RESOURCES) {
    const sourcePath = resolve(skillRoot, source);
    requireRegularFile(sourcePath, `installed resource ${source}`);
    requireContainedRealPath(sourcePath, skillRoot, `Installed resource ${source}`);
    if (!readFileSync(sourcePath).equals(readFileSync(resolve(target, output)))) {
      throw new Error(`generated file differs from installed source: ${output}`);
    }
  }

  const readmeLines = readFileSync(resolve(target, 'README.md'), 'utf8')
    .split(/\r?\n/u);
  if (readmeLines[0] !== `# ${fixture.title}`) {
    throw new Error('generated README title does not match the fixture');
  }

  const bundleIndexLines = readFileSync(
    resolve(target, 'bundle/index.md'),
    'utf8',
  ).split(/\r?\n/u);
  const bundleTitle = bundleIndexLines.find((line) => line.startsWith('# '));
  if (bundleTitle !== `# ${fixture.title}`) {
    throw new Error('generated bundle title does not match the fixture');
  }
  const sectionsHeading = bundleIndexLines.indexOf('## Sections');
  const sectionNavigation = sectionsHeading === -1
    ? []
    : bundleIndexLines
      .slice(sectionsHeading + 1)
      .filter((line) => line.length > 0);
  const expectedNavigation = fixture.sections.map(
    (section) => `- [${section}](${section}/index.md)`,
  );
  if (!isDeepStrictEqual(sectionNavigation, expectedNavigation)) {
    throw new Error('generated section navigation does not match the fixture');
  }
  for (const section of fixture.sections) {
    const sectionLines = readFileSync(
      resolve(target, `bundle/${section}/index.md`),
      'utf8',
    ).split(/\r?\n/u);
    if (sectionLines[0] !== `# ${section}`) {
      throw new Error(`generated section heading does not match: ${section}`);
    }
  }

  const settingsPath = resolve(target, '.claude/settings.json');
  let settings;
  try {
    settings = JSON.parse(readFileSync(settingsPath, 'utf8'));
  } catch (error) {
    throw new Error(`generated Claude settings are not valid JSON: ${error.message}`);
  }
  const interpreter = process.platform === 'win32' ? 'python' : 'python3';
  const expectedSettings = {
    hooks: {
      SessionStart: [{
        hooks: [{
          type: 'command',
          command: interpreter,
          args: ['${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-anchor.py'],
        }],
      }],
      PreToolUse: [{
        hooks: [{
          type: 'command',
          command: interpreter,
          args: ['${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-orient.py'],
        }],
      }],
    },
  };
  if (!isDeepStrictEqual(settings, expectedSettings)) {
    throw new Error('generated Claude settings do not match the expected adapter');
  }

  return {
    project,
    target,
    portableFiles: [...fixture.portableFiles],
    claudeAdapterFiles: [...fixture.claudeAdapterFiles],
    settings,
  };
}

export function buildOkfInvocation(
  client,
  fixtureId,
  {
    projectDir,
    clientHome,
    codexHome,
    unboxed = false,
  } = {},
) {
  if (client !== 'codex') {
    throw new Error(`Unsupported okf-wiki pilot client: ${client}`);
  }
  const fixture = fixtureFor(fixtureId);
  if (!projectDir) throw new Error('A disposable --project directory is required');
  if (!clientHome) throw new Error('A disposable --client-home directory is required');
  if (!codexHome) throw new Error('CODEX_HOME is required for the okf-wiki pilot');
  const cwd = resolve(projectDir);
  const home = resolve(clientHome);
  const resolvedCodexHome = resolve(codexHome);
  const codexHomeFromClient = relative(home, resolvedCodexHome);
  if (
    !codexHomeFromClient
    || codexHomeFromClient.startsWith('..')
    || isAbsolute(codexHomeFromClient)
  ) {
    throw new Error('CODEX_HOME must resolve below the disposable client home');
  }
  const isolationArgs = unboxed
    ? ['--dangerously-bypass-approvals-and-sandbox']
    : ['--sandbox', 'workspace-write'];
  return {
    command: 'codex',
    args: [
      'exec',
      '--ignore-user-config',
      '--ignore-rules',
      '--ephemeral',
      ...isolationArgs,
      '--skip-git-repo-check',
      '-C',
      cwd,
      '--json',
      fixture.prompt,
    ],
    cwd,
    env: {
      CODEX_HOME: resolvedCodexHome,
      HOME: home,
      USERPROFILE: home,
    },
    unsetEnv: ['CLAUDE_CONFIG_DIR', 'CLAUDE_PROJECT_DIR'],
  };
}

function isolatedEnvironment(invocation, env) {
  const childEnv = { ...env, ...invocation.env };
  for (const name of invocation.unsetEnv ?? []) delete childEnv[name];
  return childEnv;
}

export function runOkfPilot(
  invocation,
  {
    run = spawnSync,
    env = process.env,
  } = {},
) {
  const result = run(invocation.command, invocation.args, {
    cwd: invocation.cwd,
    env: isolatedEnvironment(invocation, env),
    shell: false,
    stdio: 'inherit',
    timeout: OKF_PILOT_TIMEOUT_MS,
    windowsHide: true,
  });
  if (result.status !== 0) {
    throw new Error(
      `${invocation.command} okf-wiki pilot failed with status `
      + `${result.status ?? 'unknown'}`,
    );
  }
}

export function runOkfValidation(
  projectDir,
  fixtureId,
  {
    pythonCommand = process.platform === 'win32' ? 'python' : 'python3',
    run = spawnSync,
    env = process.env,
  } = {},
) {
  const fixture = fixtureFor(fixtureId);
  const target = childPath(projectDir, fixture.target, 'Fixture target');
  requireDirectory(target, 'generated fixture target');
  const result = run(
    pythonCommand,
    ['scripts/validate.py', '--bundle', 'bundle'],
    {
      cwd: target,
      env,
      encoding: 'utf8',
      shell: false,
      timeout: OKF_VALIDATION_TIMEOUT_MS,
      windowsHide: true,
    },
  );
  if (result.status !== 0) {
    throw new Error(
      `generated OKF validation failed with status ${result.status ?? 'unknown'}: `
      + `${result.stderr ?? ''}`.trim(),
    );
  }
  if (!/\bPASS\b/u.test(result.stdout ?? '')) {
    throw new Error('generated OKF validation did not report PASS');
  }
  return {
    command: pythonCommand,
    stdout: result.stdout,
    target,
  };
}

export function verifyOkfPythonDependencies(
  {
    pythonCommand = process.platform === 'win32' ? 'python' : 'python3',
    run = spawnSync,
    env = process.env,
  } = {},
) {
  const result = run(
    pythonCommand,
    ['-c', 'import yaml'],
    {
      env,
      encoding: 'utf8',
      shell: false,
      timeout: OKF_VALIDATION_TIMEOUT_MS,
      windowsHide: true,
    },
  );
  if (result.status !== 0) {
    throw new Error(
      'PyYAML is required before running the okf-wiki pilot; install '
      + '.agents/skills/okf-wiki/requirements.txt into the selected '
      + 'Python environment',
    );
  }
  return { command: pythonCommand };
}

export function parseCliArgs(args) {
  const [client, fixtureId, ...options] = args;
  let projectDir;
  let clientHome;
  let unboxed = false;
  let dryRun = false;
  let verifyOnly = false;

  for (let index = 0; index < options.length; index += 1) {
    const option = options[index];
    if (option === '--project' || option === '--client-home') {
      const value = options[index + 1];
      if (!value || value.startsWith('--')) {
        throw new Error(`${option} requires a directory value`);
      }
      if (option === '--project') projectDir = value;
      else clientHome = value;
      index += 1;
    } else if (option === '--unboxed') {
      unboxed = true;
    } else if (option === '--dry-run') {
      dryRun = true;
    } else if (option === '--verify-only') {
      verifyOnly = true;
    } else {
      throw new Error(`Unsupported option: ${option}`);
    }
  }

  if (!client || !fixtureId) {
    throw new Error(
      'Usage: node scripts/okf-wiki-runtime-pilot.mjs codex okf-1 '
      + '--project <disposable-project> --client-home <disposable-home> '
      + '[--unboxed] [--dry-run|--verify-only]',
    );
  }
  if (client !== 'codex') {
    throw new Error(`Unsupported okf-wiki pilot client: ${client}`);
  }
  fixtureFor(fixtureId);
  if (!projectDir) throw new Error('A disposable --project directory is required');
  if (!clientHome) throw new Error('--client-home is required');
  if (dryRun && verifyOnly) {
    throw new Error('--dry-run and --verify-only cannot be combined');
  }
  return {
    client,
    fixtureId,
    projectDir,
    clientHome,
    unboxed,
    dryRun,
    verifyOnly,
  };
}

function runCli() {
  const {
    client,
    fixtureId,
    projectDir,
    clientHome,
    unboxed,
    dryRun,
    verifyOnly,
  } = parseCliArgs(process.argv.slice(2));

  if (verifyOnly) {
    verifyNoClaudePreconditions(projectDir, clientHome, fixtureId, {
      allowOutput: true,
    });
    verifyOkfInstall(projectDir, fixtureId);
    verifyOkfPythonDependencies();
    const output = verifyOkfOutput(projectDir, fixtureId);
    const validation = runOkfValidation(projectDir, fixtureId);
    console.log(JSON.stringify({
      fixture: fixtureId,
      target: output.target,
      portableFiles: output.portableFiles,
      claudeAdapterFiles: output.claudeAdapterFiles,
      validation: validation.stdout.trim(),
    }, null, 2));
    return;
  }

  const invocation = buildOkfInvocation(client, fixtureId, {
    projectDir,
    clientHome,
    codexHome: process.env.CODEX_HOME,
    unboxed,
  });
  if (dryRun) {
    console.log(JSON.stringify(invocation, null, 2));
    return;
  }

  verifyNoClaudePreconditions(projectDir, clientHome, fixtureId);
  verifyOkfInstall(projectDir, fixtureId);
  verifyOkfPythonDependencies();
  runOkfPilot(invocation);
  const output = verifyOkfOutput(projectDir, fixtureId);
  const validation = runOkfValidation(projectDir, fixtureId);
  console.log(JSON.stringify({
    fixture: fixtureId,
    target: output.target,
    portableFiles: output.portableFiles,
    claudeAdapterFiles: output.claudeAdapterFiles,
    validation: validation.stdout.trim(),
  }, null, 2));
}

const entryPoint = process.argv[1] ? pathToFileURL(resolve(process.argv[1])).href : '';
if (entryPoint === import.meta.url) {
  try {
    runCli();
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
