import assert from 'node:assert/strict';
import {
  chmodSync,
  copyFileSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  symlinkSync,
  unlinkSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import {
  afterEach,
  test,
} from 'node:test';

import {
  OKF_PILOT_FIXTURES,
  OKF_PILOT_TIMEOUT_MS,
  buildOkfInvocation,
  parseCliArgs,
  runOkfPilot,
  runOkfValidation,
  verifyNoClaudePreconditions,
  verifyNoClaudeExecutable,
  verifyOkfInstall,
  verifyOkfOutput,
  verifyOkfPythonDependencies,
} from './okf-wiki-runtime-pilot.mjs';

const projectDir = '/tmp/okf-wiki-runtime/project';
const clientHome = '/tmp/okf-wiki-runtime/home';
const codexHome = '/tmp/okf-wiki-runtime/home/.codex';
const disposableRoots = [];

function createInstalledFixture() {
  const root = mkdtempSync(join(tmpdir(), 'okf-wiki-pilot-test-'));
  disposableRoots.push(root);
  const project = join(root, 'project');
  const home = join(root, 'home');
  const skill = join(project, '.agents', 'skills', 'okf-wiki');
  mkdirSync(join(skill, 'scripts'), { recursive: true });
  mkdirSync(join(skill, 'spec'), { recursive: true });
  mkdirSync(join(skill, 'templates', 'hooks'), { recursive: true });
  mkdirSync(home);
  writeFileSync(join(skill, 'SKILL.md'), '---\nname: okf-wiki\n---\n');
  writeFileSync(join(skill, 'requirements.txt'), 'PyYAML>=5.1\n');
  writeFileSync(join(skill, 'scripts', 'scaffold.py'), '# scaffold\n');
  writeFileSync(join(skill, 'scripts', 'validate.py'), '# validate\n');
  writeFileSync(join(skill, 'spec', 'SPEC.md'), '# OKF\n');
  writeFileSync(join(skill, 'templates', 'hooks', 'okf-anchor.py'), '# anchor\n');
  writeFileSync(join(skill, 'templates', 'hooks', 'okf-orient.py'), '# orient\n');
  return { root, project, home, skill };
}

function writePilotOutput(project) {
  const fixture = OKF_PILOT_FIXTURES['okf-1'];
  const target = join(project, fixture.target);
  for (const relativePath of fixture.portableFiles) {
    const path = join(target, relativePath);
    mkdirSync(join(path, '..'), { recursive: true });
    writeFileSync(path, `fixture ${relativePath}\n`);
  }
  for (const relativePath of fixture.claudeAdapterFiles) {
    const path = join(target, relativePath);
    mkdirSync(join(path, '..'), { recursive: true });
    const content = relativePath === '.claude/settings.json'
      ? JSON.stringify({
        hooks: {
          SessionStart: [{
            hooks: [{
              type: 'command',
              command: process.platform === 'win32' ? 'python' : 'python3',
              args: ['${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-anchor.py'],
            }],
          }],
          PreToolUse: [{
            hooks: [{
              type: 'command',
              command: process.platform === 'win32' ? 'python' : 'python3',
              args: ['${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-orient.py'],
            }],
          }],
        },
      })
      : `fixture ${relativePath}\n`;
    writeFileSync(path, content);
  }
  const skill = join(project, '.agents', 'skills', 'okf-wiki');
  for (const [source, output] of [
    ['requirements.txt', 'requirements.txt'],
    ['spec/SPEC.md', 'SPEC.md'],
    ['scripts/validate.py', 'scripts/validate.py'],
    ['templates/hooks/okf-anchor.py', '.claude/hooks/okf-anchor.py'],
    ['templates/hooks/okf-orient.py', '.claude/hooks/okf-orient.py'],
  ]) {
    copyFileSync(join(skill, source), join(target, output));
  }
  writeFileSync(join(target, 'README.md'), `# ${fixture.title}\n`);
  writeFileSync(
    join(target, 'bundle', 'index.md'),
    [
      '---',
      'okf_version: "0.3"',
      '---',
      `# ${fixture.title}`,
      '',
      '## Sections',
      '',
      ...fixture.sections.map(
        (section) => `- [${section}](${section}/index.md)`,
      ),
      '',
    ].join('\n'),
  );
  for (const section of fixture.sections) {
    writeFileSync(
      join(target, 'bundle', section, 'index.md'),
      `# ${section}\n`,
    );
  }
  return target;
}

afterEach(() => {
  for (const root of disposableRoots.splice(0)) {
    rmSync(root, { recursive: true, force: true });
  }
});

test('Okf-1 preserves the accepted no-Claude prompt and output inventory', () => {
  assert.deepEqual(Object.keys(OKF_PILOT_FIXTURES), ['okf-1']);
  const fixture = OKF_PILOT_FIXTURES['okf-1'];
  assert.equal(fixture.target, 'okf-1');
  assert.deepEqual(fixture.sections, ['concepts', 'decisions']);
  assert.match(fixture.prompt, /^\$okf-wiki /u);
  assert.match(fixture.prompt, /No Claude configuration is available/u);
  assert.match(fixture.prompt, /do not invoke any Claude executable/u);
  assert.match(fixture.prompt, /Keep the default Claude hook generation enabled/u);
  assert.deepEqual(fixture.claudeAdapterFiles, [
    '.claude/hooks/okf-anchor.py',
    '.claude/hooks/okf-orient.py',
    '.claude/settings.json',
  ]);
  assert.ok(fixture.portableFiles.includes('bundle/index.md'));
  assert.ok(fixture.portableFiles.includes('scripts/validate.py'));
});

test('Codex invocation isolates HOME and defaults to a writable sandbox', () => {
  const invocation = buildOkfInvocation('codex', 'okf-1', {
    projectDir,
    clientHome,
    codexHome,
  });
  assert.equal(invocation.command, 'codex');
  assert.equal(invocation.cwd, projectDir);
  assert.deepEqual(invocation.env, {
    CODEX_HOME: codexHome,
    HOME: clientHome,
    USERPROFILE: clientHome,
  });
  assert.ok(invocation.unsetEnv.includes('CLAUDE_CONFIG_DIR'));
  assert.ok(invocation.unsetEnv.includes('CLAUDE_PROJECT_DIR'));
  assert.ok(invocation.args.includes('--ignore-user-config'));
  assert.ok(invocation.args.includes('--ignore-rules'));
  assert.ok(invocation.args.includes('--ephemeral'));
  assert.deepEqual(
    invocation.args.slice(
      invocation.args.indexOf('--sandbox'),
      invocation.args.indexOf('--sandbox') + 2,
    ),
    ['--sandbox', 'workspace-write'],
  );
  assert.equal(invocation.args.at(-1), OKF_PILOT_FIXTURES['okf-1'].prompt);

  const unboxed = buildOkfInvocation('codex', 'okf-1', {
    projectDir,
    clientHome,
    codexHome,
    unboxed: true,
  });
  assert.ok(unboxed.args.includes('--dangerously-bypass-approvals-and-sandbox'));
  assert.ok(!unboxed.args.includes('--sandbox'));

  assert.throws(
    () => buildOkfInvocation('codex', 'okf-1', {
      projectDir,
      clientHome,
      codexHome: '/tmp/external-codex-home',
    }),
    /CODEX_HOME must resolve below the disposable client home/u,
  );
});

test('preconditions require a clean target and no project or home Claude state', () => {
  const { project, home } = createInstalledFixture();
  assert.doesNotThrow(() => verifyNoClaudePreconditions(project, home, 'okf-1'));

  mkdirSync(join(home, '.claude'));
  assert.throws(
    () => verifyNoClaudePreconditions(project, home, 'okf-1'),
    /client home must not contain \.claude/u,
  );
  rmSync(join(home, '.claude'), { recursive: true });

  mkdirSync(join(project, '.claude'));
  assert.throws(
    () => verifyNoClaudePreconditions(project, home, 'okf-1'),
    /project must not contain \.claude/u,
  );
  rmSync(join(project, '.claude'), { recursive: true });

  mkdirSync(join(project, 'okf-1'));
  assert.throws(
    () => verifyNoClaudePreconditions(project, home, 'okf-1'),
    /fixture target must not already exist/u,
  );
});

test('install and output verifiers classify every generated file', () => {
  const { project, home, skill } = createInstalledFixture();
  const install = verifyOkfInstall(project, 'okf-1');
  assert.equal(install.skillRoot, skill);
  const target = writePilotOutput(project);
  const output = verifyOkfOutput(project, 'okf-1');
  assert.equal(output.target, target);
  assert.deepEqual(
    output.portableFiles,
    OKF_PILOT_FIXTURES['okf-1'].portableFiles,
  );
  assert.deepEqual(
    output.claudeAdapterFiles,
    OKF_PILOT_FIXTURES['okf-1'].claudeAdapterFiles,
  );
  assert.equal(output.settings.hooks.SessionStart.length, 1);
  assert.equal(output.settings.hooks.PreToolUse.length, 1);
  assert.doesNotThrow(() => verifyNoClaudePreconditions(project, home, 'okf-1', {
    allowOutput: true,
  }));

  writeFileSync(join(target, 'unexpected.txt'), 'unexpected\n');
  assert.throws(
    () => verifyOkfOutput(project, 'okf-1'),
    /unexpected generated file: unexpected\.txt/u,
  );
});

test('install verifier rejects required resources behind linked parents', () => {
  const {
    root,
    project,
    skill,
  } = createInstalledFixture();
  const external = join(root, 'external-scripts');
  mkdirSync(external);
  writeFileSync(join(external, 'scaffold.py'), '# external\n');
  writeFileSync(join(external, 'validate.py'), '# external\n');
  rmSync(join(skill, 'scripts'), { recursive: true });
  symlinkSync(external, join(skill, 'scripts'), 'dir');
  assert.throws(
    () => verifyOkfInstall(project, 'okf-1'),
    /installed resource scripts\/scaffold\.py escapes the installed skill root/u,
  );
});

test('output verifier rejects missing or linked generated files', () => {
  const { project } = createInstalledFixture();
  const target = writePilotOutput(project);
  unlinkSync(join(target, 'bundle', 'index.md'));
  assert.throws(
    () => verifyOkfOutput(project, 'okf-1'),
    /missing generated file: bundle\/index\.md/u,
  );

  writeFileSync(join(target, 'bundle', 'index.md'), 'restored\n');
  const external = join(project, 'external.md');
  writeFileSync(external, 'external\n');
  unlinkSync(join(target, 'bundle', 'index.md'));
  symlinkSync(external, join(target, 'bundle', 'index.md'));
  assert.throws(
    () => verifyOkfOutput(project, 'okf-1'),
    /generated file must be regular and not linked: bundle\/index\.md/u,
  );
});

test('pilot and validator runners avoid a shell and remove Claude environment', () => {
  const calls = [];
  const run = (command, args, options) => {
    calls.push({ command, args, options });
    return { status: 0, stdout: 'PASS\n', stderr: '' };
  };
  const invocation = buildOkfInvocation('codex', 'okf-1', {
    projectDir,
    clientHome,
    codexHome,
  });
  runOkfPilot(invocation, {
    env: {
      PATH: '/bin',
      CLAUDE_CONFIG_DIR: '/real/claude',
      CLAUDE_PROJECT_DIR: '/real/project',
    },
    run,
  });
  assert.equal(OKF_PILOT_TIMEOUT_MS, 300_000);
  assert.equal(calls[0].options.shell, false);
  assert.equal(calls[0].options.timeout, OKF_PILOT_TIMEOUT_MS);
  assert.deepEqual(calls[0].options.env, {
    PATH: '/bin',
    CODEX_HOME: codexHome,
    HOME: clientHome,
    USERPROFILE: clientHome,
  });

  const { project } = createInstalledFixture();
  writePilotOutput(project);
  runOkfValidation(project, 'okf-1', {
    pythonCommand: 'python-fixture',
    run,
  });
  assert.equal(calls[1].command, 'python-fixture');
  assert.deepEqual(calls[1].args, [
    'scripts/validate.py',
    '--bundle',
    'bundle',
  ]);
  assert.equal(calls[1].options.cwd, join(project, 'okf-1'));
  assert.equal(calls[1].options.shell, false);
});

test('output verifier rejects altered Claude adapter commands', () => {
  const { project } = createInstalledFixture();
  const target = writePilotOutput(project);
  const settingsPath = join(target, '.claude', 'settings.json');
  const settings = JSON.parse(readFileSync(settingsPath, 'utf8'));
  settings.hooks.PreToolUse[0].hooks[0].command = 'codex-hook';
  writeFileSync(settingsPath, JSON.stringify(settings));

  assert.throws(
    () => verifyOkfOutput(project, 'okf-1'),
    /generated Claude settings do not match the expected adapter/u,
  );
});

test('output verifier rejects generated resources that diverge from the install', () => {
  const { project } = createInstalledFixture();
  const target = writePilotOutput(project);
  writeFileSync(
    join(target, '.claude', 'hooks', 'okf-anchor.py'),
    '# altered adapter\n',
  );

  assert.throws(
    () => verifyOkfOutput(project, 'okf-1'),
    /generated file differs from installed source: \.claude\/hooks\/okf-anchor\.py/u,
  );
});

test('output verifier rejects a title that differs from the accepted fixture', () => {
  const { project } = createInstalledFixture();
  const target = writePilotOutput(project);
  writeFileSync(join(target, 'README.md'), '# Wrong title\n');

  assert.throws(
    () => verifyOkfOutput(project, 'okf-1'),
    /generated README title does not match the fixture/u,
  );
});

test('output verifier rejects changed section navigation', () => {
  const { project } = createInstalledFixture();
  const target = writePilotOutput(project);
  writeFileSync(
    join(target, 'bundle', 'index.md'),
    [
      '---',
      'okf_version: "0.3"',
      '---',
      '# Codex no-Claude pilot',
      '',
      '## Sections',
      '',
      '- [decisions](decisions/index.md)',
      '- [concepts](concepts/index.md)',
      '',
    ].join('\n'),
  );

  assert.throws(
    () => verifyOkfOutput(project, 'okf-1'),
    /generated section navigation does not match the fixture/u,
  );
});

test('Python dependency preflight requires PyYAML without using a shell', () => {
  const calls = [];
  const run = (command, args, options) => {
    calls.push({ command, args, options });
    return { status: 0, stdout: '', stderr: '' };
  };
  const result = verifyOkfPythonDependencies({
    pythonCommand: 'python-fixture',
    run,
  });
  assert.equal(result.command, 'python-fixture');
  assert.deepEqual(calls[0].args, ['-c', 'import yaml']);
  assert.equal(calls[0].options.shell, false);

  assert.throws(
    () => verifyOkfPythonDependencies({
      pythonCommand: 'python-fixture',
      run: () => ({ status: 1, stdout: '', stderr: 'missing yaml' }),
    }),
    /PyYAML is required before running the okf-wiki pilot/u,
  );
});

test('no-Claude preflight rejects a Claude executable on PATH', () => {
  const root = mkdtempSync(join(tmpdir(), 'okf-wiki-claude-path-test-'));
  disposableRoots.push(root);
  const bin = join(root, 'bin');
  mkdirSync(bin);
  const executable = join(
    bin,
    process.platform === 'win32' ? 'claude.cmd' : 'claude',
  );
  writeFileSync(executable, '#!/bin/sh\nexit 0\n');
  if (process.platform !== 'win32') chmodSync(executable, 0o755);

  assert.throws(
    () => verifyNoClaudeExecutable({ env: { PATH: bin } }),
    /Claude executable must not be available on PATH/u,
  );
  assert.doesNotThrow(
    () => verifyNoClaudeExecutable({ env: { PATH: join(root, 'empty-bin') } }),
  );
});

test('CLI rejects ambiguous homes, clients, fixtures, and modes', () => {
  assert.throws(
    () => parseCliArgs(['codex', 'okf-1', '--project', '--client-home']),
    /--project requires a directory value/u,
  );
  assert.throws(
    () => parseCliArgs(['codex', 'okf-1', '--project', projectDir]),
    /--client-home is required/u,
  );
  assert.throws(
    () => parseCliArgs([
      'codex',
      'okf-1',
      '--project',
      projectDir,
      '--client-home',
      clientHome,
      '--dry-run',
      '--verify-only',
    ]),
    /cannot be combined/u,
  );
  assert.throws(
    () => buildOkfInvocation('claude', 'okf-1', {
      projectDir,
      clientHome,
      codexHome,
    }),
    /Unsupported okf-wiki pilot client/u,
  );
  assert.throws(
    () => buildOkfInvocation('codex', 'toString', {
      projectDir,
      clientHome,
      codexHome,
    }),
    /Unsupported okf-wiki fixture/u,
  );
  assert.deepEqual(
    parseCliArgs([
      'codex',
      'okf-1',
      '--project',
      projectDir,
      '--client-home',
      clientHome,
      '--unboxed',
      '--verify-only',
    ]),
    {
      client: 'codex',
      fixtureId: 'okf-1',
      projectDir,
      clientHome,
      unboxed: true,
      dryRun: false,
      verifyOnly: true,
    },
  );
});
