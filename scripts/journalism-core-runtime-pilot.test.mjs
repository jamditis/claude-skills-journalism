import assert from 'node:assert/strict';
import test from 'node:test';

import {
  RUNTIME_PILOT_FIXTURES,
  RUNTIME_PILOT_TIMEOUT_MS,
  buildRuntimeInvocation,
  runRuntimePilot,
} from './journalism-core-runtime-pilot.mjs';

const projectDir = '/tmp/journalism-core-runtime/project';
const claudeConfigDir = '/tmp/journalism-core-runtime/claude';
const codexHome = '/tmp/journalism-core-runtime/codex';

test('runtime pilot fixtures preserve the accepted prompts and modes', () => {
  assert.deepEqual(Object.keys(RUNTIME_PILOT_FIXTURES), [
    'j-core-1',
    'j-core-2',
    'j-core-3',
    'j-core-resource',
  ]);
  assert.equal(RUNTIME_PILOT_FIXTURES['j-core-1'].mode, 'explicit');
  assert.match(
    RUNTIME_PILOT_FIXTURES['j-core-1'].prompt,
    /unsigned screenshot claiming that a city budget doubled in 2025/u,
  );
  assert.equal(RUNTIME_PILOT_FIXTURES['j-core-2'].mode, 'implicit');
  assert.equal(RUNTIME_PILOT_FIXTURES['j-core-3'].mode, 'non-trigger');
  assert.equal(
    RUNTIME_PILOT_FIXTURES['j-core-3'].prompt,
    'Calculate an 18% tip on a $42 meal.',
  );
  assert.match(RUNTIME_PILOT_FIXTURES['j-core-resource'].prompt, /sibling reference\.md/u);
});

test('Claude plans isolate sessions and expose only the fixture-required tool', () => {
  const explicit = buildRuntimeInvocation('claude', 'j-core-1', {
    projectDir,
    claudeConfigDir,
  });
  assert.equal(explicit.command, 'claude');
  assert.equal(explicit.cwd, projectDir);
  assert.deepEqual(explicit.env, { CLAUDE_CONFIG_DIR: claudeConfigDir });
  assert.equal(
    explicit.args[1],
    '/journalism-core:fact-check-workflow '
      + RUNTIME_PILOT_FIXTURES['j-core-1'].prompt,
  );
  assert.ok(explicit.args.includes('--no-session-persistence'));
  assert.deepEqual(explicit.args.slice(-2), ['--tools', '']);

  const implicit = buildRuntimeInvocation('claude', 'j-core-2', {
    projectDir,
    claudeConfigDir,
  });
  assert.deepEqual(
    implicit.args.slice(-4),
    ['--tools', 'Skill', '--allowedTools', 'Skill'],
  );

  const resource = buildRuntimeInvocation('claude', 'j-core-resource', {
    projectDir,
    claudeConfigDir,
  });
  assert.equal(
    resource.args[1],
    '/journalism-core:photo-metadata '
      + RUNTIME_PILOT_FIXTURES['j-core-resource'].prompt,
  );
  assert.deepEqual(
    resource.args.slice(-6),
    ['--tools', 'Read', '--allowedTools', 'Read', '--add-dir', claudeConfigDir],
  );
});

test('Codex plans use project standards skills and default to a read-only sandbox', () => {
  const explicit = buildRuntimeInvocation('codex', 'j-core-1', {
    projectDir,
    codexHome,
  });
  assert.equal(explicit.command, 'codex');
  assert.equal(explicit.cwd, projectDir);
  assert.deepEqual(explicit.env, { CODEX_HOME: codexHome });
  assert.ok(explicit.args.includes('--ignore-user-config'));
  assert.ok(explicit.args.includes('--ephemeral'));
  assert.deepEqual(
    explicit.args.slice(explicit.args.indexOf('--sandbox'), explicit.args.indexOf('--sandbox') + 2),
    ['--sandbox', 'read-only'],
  );
  assert.equal(
    explicit.args.at(-1),
    '$fact-check-workflow ' + RUNTIME_PILOT_FIXTURES['j-core-1'].prompt,
  );

  const resource = buildRuntimeInvocation('codex', 'j-core-resource', {
    projectDir,
    codexHome,
    unboxed: true,
  });
  assert.ok(resource.args.includes('--dangerously-bypass-approvals-and-sandbox'));
  assert.ok(!resource.args.includes('--sandbox'));
  assert.equal(
    resource.args.at(-1),
    '$photo-metadata ' + RUNTIME_PILOT_FIXTURES['j-core-resource'].prompt,
  );
});

test('runtime runner avoids a shell and preserves the subprocess timeout', () => {
  const calls = [];
  runRuntimePilot(
    {
      command: 'fixture-client',
      args: ['--json'],
      cwd: projectDir,
      env: { FIXTURE_HOME: '/tmp/fixture-home' },
    },
    {
      env: { PATH: '/bin' },
      run: (command, args, options) => {
        calls.push({ command, args, options });
        return { status: 0 };
      },
    },
  );

  assert.equal(RUNTIME_PILOT_TIMEOUT_MS, 300_000);
  assert.equal(calls[0].options.shell, false);
  assert.equal(calls[0].options.timeout, RUNTIME_PILOT_TIMEOUT_MS);
  assert.deepEqual(calls[0].options.env, {
    PATH: '/bin',
    FIXTURE_HOME: '/tmp/fixture-home',
  });
});

test('runtime pilot plans require explicit disposable client homes', () => {
  assert.throws(
    () => buildRuntimeInvocation('claude', 'j-core-1', { projectDir }),
    /CLAUDE_CONFIG_DIR is required/u,
  );
  assert.throws(
    () => buildRuntimeInvocation('codex', 'j-core-1', { projectDir }),
    /CODEX_HOME is required/u,
  );
  assert.throws(
    () => buildRuntimeInvocation('codex', 'unknown', { projectDir, codexHome }),
    /Unsupported runtime pilot fixture/u,
  );
});
