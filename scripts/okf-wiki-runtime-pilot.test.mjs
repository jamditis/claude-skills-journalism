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
import { delimiter, join } from 'node:path';
import {
  afterEach,
  test,
} from 'node:test';

import {
  OKF_PILOT_FIXTURES,
  OKF_PILOT_TIMEOUT_MS,
  buildOkfInvocation,
  parseCodexTranscript,
  parseCliArgs,
  runOkfPilot,
  runOkfValidation,
  snapshotOkfInstall,
  verifyNoClaudePreconditions,
  verifyNoClaudeExecutable,
  verifyOkfInstall,
  verifyOkfInstallUnchanged,
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

function validCodexTranscript() {
  const installedFilesRead = [
    '.agents/skills/okf-wiki/SKILL.md',
    '.agents/skills/okf-wiki/spec/SPEC.md',
  ];
  const commandsRun = [
    `sed -n '1,220p' ${installedFilesRead[0]}`,
    `sed -n '1,220p' ${installedFilesRead[1]}`,
    'python3 .agents/skills/okf-wiki/scripts/scaffold.py ./okf-1 '
      + '--title "Codex no-Claude pilot" --sections concepts,decisions',
    'python3 scripts/validate.py --bundle bundle',
  ];
  const capturedCommands = [...commandsRun];
  const capturedOutputs = [
    'name: okf-wiki\n# okf-wiki: scaffold an Open Knowledge Format knowledge base\n',
    '# OKF spec v1\n## Bundle model\n',
    'Scaffolded OKF project\nPASS\n',
    'PASS\n',
  ];
  const events = [
    { type: 'thread.started', thread_id: 'fixture-thread' },
    ...capturedCommands.map((command, index) => ({
      type: 'item.completed',
      item: {
        id: `command-${index}`,
        type: 'command_execution',
        command,
        aggregated_output: capturedOutputs[index],
        status: 'completed',
        exit_code: 0,
      },
    })),
    {
      type: 'item.completed',
      item: {
        id: 'report',
        type: 'agent_message',
        text: JSON.stringify({
          installed_files_read: installedFilesRead,
          commands_run: commandsRun,
          trust_or_approval_prompt: false,
          notes: 'Scaffolded and validated the requested fixture.',
        }),
      },
    },
    { type: 'turn.completed' },
  ];
  return `${events.map((event) => JSON.stringify(event)).join('\n')}\n`;
}

function mutateCodexTranscript(mutator) {
  const events = validCodexTranscript()
    .split('\n')
    .filter(Boolean)
    .map((line) => JSON.parse(line));
  mutator(events);
  return `${events.map((event) => JSON.stringify(event)).join('\n')}\n`;
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
  assert.match(
    fixture.prompt,
    /list only resources you inspected with a read command/u,
  );
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
      invocation.args.indexOf('--output-schema'),
      invocation.args.indexOf('--output-schema') + 2,
    ),
    [
      '--output-schema',
      join(clientHome, 'okf-wiki-runtime-report-schema.json'),
    ],
  );
  assert.equal(
    invocation.transcriptPath,
    join(clientHome, 'okf-wiki-runtime-transcript.jsonl'),
  );
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
    return {
      status: 0,
      stdout: command === 'python-fixture' ? 'PASS\n' : validCodexTranscript(),
      stderr: '',
    };
  };
  const { project, home } = createInstalledFixture();
  const isolatedCodexHome = join(home, '.codex');
  mkdirSync(isolatedCodexHome);
  const invocation = buildOkfInvocation('codex', 'okf-1', {
    projectDir: project,
    clientHome: home,
    codexHome: isolatedCodexHome,
  });
  const evidence = runOkfPilot(invocation, {
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
  assert.deepEqual(calls[0].options.stdio, ['ignore', 'pipe', 'pipe']);
  assert.deepEqual(calls[0].options.env, {
    PATH: '/bin',
    CODEX_HOME: isolatedCodexHome,
    HOME: home,
    USERPROFILE: home,
  });
  assert.equal(
    readFileSync(invocation.transcriptPath, 'utf8'),
    validCodexTranscript(),
  );
  assert.equal(evidence.scaffoldCommands.length, 1);
  assert.equal(evidence.report.trust_or_approval_prompt, false);

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

test('runtime verification compares output with an immutable pre-run install snapshot', () => {
  const { project, skill } = createInstalledFixture();
  const snapshot = snapshotOkfInstall(project, 'okf-1');
  const target = writePilotOutput(project);
  writeFileSync(join(skill, 'post-run-extra.txt'), 'unexpected\n');
  assert.throws(
    () => verifyOkfInstallUnchanged(project, 'okf-1', snapshot),
    /installed skill inventory changed during the Codex run/u,
  );
  unlinkSync(join(skill, 'post-run-extra.txt'));

  writeFileSync(join(skill, 'scripts', 'validate.py'), '# post-run mutation\n');
  writeFileSync(
    join(target, 'scripts', 'validate.py'),
    '# post-run mutation\n',
  );

  assert.throws(
    () => verifyOkfInstallUnchanged(project, 'okf-1', snapshot),
    /installed resource changed during the Codex run: scripts\/validate\.py/u,
  );
  assert.throws(
    () => verifyOkfOutput(project, 'okf-1', { installSnapshot: snapshot }),
    /installed resource changed during the Codex run: scripts\/validate\.py/u,
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
  for (const name of ['claude', 'claude-code']) {
    const executable = join(
      bin,
      process.platform === 'win32' ? `${name}.cmd` : name,
    );
    writeFileSync(executable, '#!/bin/sh\nexit 0\n');
    if (process.platform !== 'win32') chmodSync(executable, 0o755);

    assert.throws(
      () => verifyNoClaudeExecutable({ env: { PATH: bin } }),
      /Claude executable must not be available on PATH/u,
    );
    unlinkSync(executable);
  }
  assert.doesNotThrow(
    () => verifyNoClaudeExecutable({ env: { PATH: join(root, 'empty-bin') } }),
  );
  assert.throws(
    () => verifyNoClaudeExecutable({
      env: { PATH: `${join(root, 'empty-bin')}${delimiter}` },
    }),
    /PATH must not contain empty entries/u,
  );
  assert.throws(
    () => verifyNoClaudeExecutable({ env: { PATH: '.' } }),
    /PATH entries must be absolute/u,
  );
});

test('Codex transcript pins installed reads, actual commands, and no prompts', () => {
  const evidence = parseCodexTranscript(validCodexTranscript(), 'okf-1');
  assert.equal(evidence.scaffoldCommands.length, 1);
  assert.equal(evidence.report.commands_run.length, evidence.commands.length);
  assert.equal(
    evidence.report.commands_run.at(-1),
    'python3 scripts/validate.py --bundle bundle',
  );
  assert.deepEqual(evidence.report.installed_files_read, [
    '.agents/skills/okf-wiki/SKILL.md',
    '.agents/skills/okf-wiki/spec/SPEC.md',
  ]);

  const withoutScaffold = validCodexTranscript()
    .split('\n')
    .filter((line) => !line.includes('scaffold.py ./okf-1'))
    .join('\n');
  assert.throws(
    () => parseCodexTranscript(withoutScaffold, 'okf-1'),
    /exactly one accepted scaffold command/u,
  );

  const loopedScaffold = validCodexTranscript().replace(
    'python3 .agents/skills/okf-wiki/scripts/scaffold.py ./okf-1 '
      + '--title \\"Codex no-Claude pilot\\" --sections concepts,decisions',
    'for pass in 1 2; do python3 '
      + '.agents/skills/okf-wiki/scripts/scaffold.py ./okf-1 '
      + '--title \\"Codex no-Claude pilot\\" '
      + '--sections concepts,decisions; done',
  );
  assert.throws(
    () => parseCodexTranscript(loopedScaffold, 'okf-1'),
    /exactly one accepted scaffold command/u,
  );

  const echoedRead = validCodexTranscript().replace(
    "sed -n '1,220p' .agents/skills/okf-wiki/SKILL.md",
    'echo .agents/skills/okf-wiki/SKILL.md',
  );
  assert.throws(
    () => parseCodexTranscript(echoedRead, 'okf-1'),
    /missing successful installed resource read/u,
  );

  const spoofedRead = mutateCodexTranscript((events) => {
    const command = events.find(
      (event) => event.item?.command?.includes('/SKILL.md'),
    );
    const reportEvent = events.find(
      (event) => event.item?.type === 'agent_message',
    );
    const report = JSON.parse(reportEvent.item.text);
    const spoof = 'cat .agents/skills/okf-wiki/SKILL.md.bak '
      + "|| printf 'name: okf-wiki'";
    const commandIndex = report.commands_run.indexOf(command.item.command);
    command.item.command = spoof;
    command.item.aggregated_output = 'name: okf-wiki\n';
    report.commands_run[commandIndex] = spoof;
    reportEvent.item.text = JSON.stringify(report);
  });
  assert.throws(
    () => parseCodexTranscript(spoofedRead, 'okf-1'),
    /missing successful installed resource read/u,
  );

  const windowsTranscript = validCodexTranscript().replaceAll(
    'python3 ',
    'python ',
  );
  assert.doesNotThrow(
    () => parseCodexTranscript(windowsTranscript, 'okf-1', {
      platform: 'win32',
    }),
  );
  assert.throws(
    () => parseCodexTranscript(windowsTranscript, 'okf-1', {
      platform: 'linux',
    }),
    /exactly one accepted scaffold command/u,
  );

  const hiddenCompound = mutateCodexTranscript((events) => {
    const command = events.find(
      (event) => event.item?.command?.includes('/SKILL.md'),
    );
    command.item.command += ' && cat /etc/passwd';
  });
  assert.throws(
    () => parseCodexTranscript(hiddenCompound, 'okf-1'),
    /missing successful installed resource read/u,
  );

  for (const forgedLocation of [
    '(from /tmp/forged) ',
    'cd /tmp/forged && ',
  ]) {
    const forgedWorkingDirectory = mutateCodexTranscript((events) => {
      const reportEvent = events.find(
        (event) => event.item?.type === 'agent_message',
      );
      const report = JSON.parse(reportEvent.item.text);
      report.commands_run[3] = forgedLocation + report.commands_run[3];
      reportEvent.item.text = JSON.stringify(report);
    });
    assert.throws(
      () => parseCodexTranscript(forgedWorkingDirectory, 'okf-1'),
      /final report does not exactly match the captured command log/u,
    );
  }

  const failedRead = mutateCodexTranscript((events) => {
    const command = events.find(
      (event) => event.item?.command?.includes('/SKILL.md'),
    );
    command.item.status = 'failed';
    command.item.exit_code = 1;
  });
  assert.throws(
    () => parseCodexTranscript(failedRead, 'okf-1'),
    /missing successful installed resource read/u,
  );

  const countOnly = mutateCodexTranscript((events) => {
    const command = events.find(
      (event) => event.item?.command?.includes('/SKILL.md'),
    );
    command.item.command = 'wc -l .agents/skills/okf-wiki/SKILL.md';
  });
  assert.throws(
    () => parseCodexTranscript(countOnly, 'okf-1'),
    /missing successful installed resource read/u,
  );

  const claudeCommand = mutateCodexTranscript((events) => {
    events.splice(-2, 0, {
      type: 'item.completed',
      item: {
        id: 'forbidden-claude',
        type: 'command_execution',
        command: '/opt/claude --version',
        aggregated_output: 'Claude Code\n',
        status: 'completed',
        exit_code: 0,
      },
    });
  });
  assert.throws(
    () => parseCodexTranscript(claudeCommand, 'okf-1'),
    /transcript invokes a Claude executable/u,
  );

  const hookCommand = mutateCodexTranscript((events) => {
    events.splice(-2, 0, {
      type: 'item.completed',
      item: {
        id: 'forbidden-hook',
        type: 'command_execution',
        command: 'python3 okf-1/.claude/hooks/okf-anchor.py',
        aggregated_output: '',
        status: 'completed',
        exit_code: 0,
      },
    });
  });
  assert.throws(
    () => parseCodexTranscript(hookCommand, 'okf-1'),
    /transcript accesses generated Claude adapter files/u,
  );

  const relativeHookCommand = mutateCodexTranscript((events) => {
    events.splice(-2, 0, {
      type: 'item.completed',
      item: {
        id: 'forbidden-relative-hook',
        type: 'command_execution',
        command: 'python3 .claude/hooks/okf-anchor.py',
        aggregated_output: '',
        status: 'completed',
        exit_code: 0,
      },
    });
  });
  assert.throws(
    () => parseCodexTranscript(relativeHookCommand, 'okf-1'),
    /transcript accesses generated Claude adapter files/u,
  );

  const externalRead = mutateCodexTranscript((events) => {
    const reportEvent = events.find(
      (event) => event.item?.type === 'agent_message',
    );
    const report = JSON.parse(reportEvent.item.text);
    const command = 'cat /etc/passwd';
    const reportIndex = events.indexOf(reportEvent);
    events.splice(reportIndex, 0, {
      type: 'item.completed',
      item: {
        id: 'forbidden-external-read',
        type: 'command_execution',
        command,
        aggregated_output: 'root:x:0:0\n',
        status: 'completed',
        exit_code: 0,
      },
    });
    report.commands_run.push(command);
    reportEvent.item.text = JSON.stringify(report);
  });
  assert.throws(
    () => parseCodexTranscript(externalRead, 'okf-1'),
    /outside the accepted disposable command boundary/u,
  );

  const promptReported = validCodexTranscript()
    .split('\n')
    .filter(Boolean)
    .map((line) => {
      const event = JSON.parse(line);
      if (event.item?.type === 'agent_message') {
        const report = JSON.parse(event.item.text);
        report.trust_or_approval_prompt = true;
        event.item.text = JSON.stringify(report);
      }
      return JSON.stringify(event);
    })
    .join('\n');
  assert.throws(
    () => parseCodexTranscript(promptReported, 'okf-1'),
    /trust or approval prompt/u,
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
