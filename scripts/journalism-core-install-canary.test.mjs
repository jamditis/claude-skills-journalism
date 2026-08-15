import assert from 'node:assert/strict';
import {
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import {
  EXPECTED_SKILL_NAMES,
  SUBPROCESS_TIMEOUT_MS,
  assertPathInside,
  buildCommandInvocation,
  buildCommandPlan,
  verifyCopiedSkillTree,
  verifyInstalledPackage,
  verifyStandardsInstall,
} from './journalism-core-install-canary.mjs';

test('Claude and Codex canaries use isolated config homes and local source', () => {
  const repo = '/repo';
  const home = '/tmp/canary';

  assert.deepEqual(buildCommandPlan('claude', repo, home), {
    envName: 'CLAUDE_CONFIG_DIR',
    commands: [
      ['claude', ['plugin', 'validate', '--strict', repo]],
      ['claude', ['plugin', 'marketplace', 'add', repo, '--scope', 'user']],
      ['claude', ['plugin', 'install', 'journalism-core@claude-skills-journalism', '--scope', 'user']],
      ['claude', ['plugin', 'list', '--json']],
    ],
  });

  assert.deepEqual(buildCommandPlan('codex', repo, home), {
    envName: 'CODEX_HOME',
    commands: [
      ['codex', ['plugin', 'marketplace', 'add', repo, '--json']],
      ['codex', ['plugin', 'add', 'journalism-core@claude-skills-journalism', '--json']],
      ['codex', ['plugin', 'list', '--json']],
    ],
  });

  assert.deepEqual(buildCommandPlan('codex-skills', repo, home), {
    cwd: home,
    commands: [[
      'skills',
      [
        'add',
        join(repo, 'journalism-core'),
        '--skill',
        '*',
        '--agent',
        'codex',
        '--copy',
        '-y',
      ],
    ]],
  });

  assert.deepEqual(buildCommandPlan('codex-skills-global', repo, home), {
    cwd: join(home, 'project'),
    globalHome: join(home, 'home'),
    commands: [[
      'skills',
      [
        'add',
        join(repo, 'journalism-core'),
        '--skill',
        '*',
        '--agent',
        'codex',
        '--copy',
        '-g',
        '-y',
      ],
    ]],
  });
});

test('Claude and Codex install records must contain the exact journalism-core skill set', (t) => {
  const root = mkdtempSync(join(tmpdir(), 'journalism-core-canary-test-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const installPath = join(root, 'plugins', 'journalism-core', '1.3.1');

  for (const name of EXPECTED_SKILL_NAMES) {
    const directory = join(installPath, 'skills', name);
    mkdirSync(directory, { recursive: true });
    writeFileSync(join(directory, 'SKILL.md'), `---\nname: ${name}\ndescription: Fixture\n---\n`);
  }

  const claude = JSON.stringify([{
    id: 'journalism-core@claude-skills-journalism',
    version: '1.3.1',
    enabled: true,
    installPath,
  }]);
  const codex = JSON.stringify({
    installed: [{
      pluginId: 'journalism-core@claude-skills-journalism',
      version: '1.3.1',
      installed: true,
      enabled: true,
      source: { source: 'local', path: '/repo/journalism-core' },
    }],
  });

  assert.deepEqual(verifyInstalledPackage('claude', claude, root).skillNames, EXPECTED_SKILL_NAMES);
  assert.deepEqual(
    verifyInstalledPackage('codex', codex, root, installPath).skillNames,
    EXPECTED_SKILL_NAMES,
  );
});

test('the canary rejects a partial package install', (t) => {
  const root = mkdtempSync(join(tmpdir(), 'journalism-core-canary-test-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const installPath = join(root, 'plugin');
  const directory = join(installPath, 'skills', EXPECTED_SKILL_NAMES[0]);
  mkdirSync(directory, { recursive: true });
  writeFileSync(join(directory, 'SKILL.md'), '---\nname: fixture\ndescription: Fixture\n---\n');

  const output = JSON.stringify([{
    id: 'journalism-core@claude-skills-journalism',
    version: '1.3.1',
    enabled: true,
    installPath,
  }]);

  assert.throws(
    () => verifyInstalledPackage('claude', output, root),
    /installed skill set did not match/u,
  );
});

test('the canary rejects missing or changed installed resources', (t) => {
  const root = mkdtempSync(join(tmpdir(), 'journalism-core-canary-test-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const source = join(root, 'source');
  const installed = join(root, 'installed');
  mkdirSync(join(source, 'photo-metadata'), { recursive: true });
  mkdirSync(join(installed, 'photo-metadata'), { recursive: true });
  writeFileSync(join(source, 'photo-metadata', 'SKILL.md'), 'same');
  writeFileSync(join(installed, 'photo-metadata', 'SKILL.md'), 'same');

  assert.equal(verifyCopiedSkillTree(source, installed).fileCount, 1);
  writeFileSync(join(installed, 'photo-metadata', 'SKILL.md'), 'changed');
  assert.throws(
    () => verifyCopiedSkillTree(source, installed),
    /content differed/u,
  );
});

test('install containment rejects linked paths that escape the disposable home', (t) => {
  const root = mkdtempSync(join(tmpdir(), 'journalism-core-containment-test-'));
  const outside = mkdtempSync(join(tmpdir(), 'journalism-core-outside-test-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  t.after(() => rmSync(outside, { recursive: true, force: true }));
  mkdirSync(join(outside, 'journalism-core'));
  symlinkSync(outside, join(root, 'plugins'), 'dir');

  assert.throws(
    () => assertPathInside(root, join(root, 'plugins', 'journalism-core')),
    /linked path|escaped the disposable client home/u,
  );
});

test('standards installs reject a linked destination outside the disposable root', (t) => {
  const root = mkdtempSync(join(tmpdir(), 'journalism-core-standards-containment-test-'));
  const outside = mkdtempSync(join(tmpdir(), 'journalism-core-standards-outside-test-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  t.after(() => rmSync(outside, { recursive: true, force: true }));
  mkdirSync(join(outside, 'skills'));
  symlinkSync(outside, join(root, '.agents'), 'dir');

  assert.throws(
    () => verifyStandardsInstall(root, join(root, 'source')),
    /linked path|escaped the disposable client home/u,
  );
});

test('exact tree verification rejects linked skill resources', (t) => {
  const root = mkdtempSync(join(tmpdir(), 'journalism-core-symlink-test-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const source = join(root, 'source');
  const installed = join(root, 'installed');
  mkdirSync(source);
  mkdirSync(installed);
  writeFileSync(join(source, 'SKILL.md'), 'same');
  writeFileSync(join(installed, 'SKILL.md'), 'same');
  symlinkSync('SKILL.md', join(source, 'linked.md'));

  assert.throws(
    () => verifyCopiedSkillTree(source, installed),
    /linked skill resource/u,
  );
});

test('Windows canaries invoke npm command shims without a shell', () => {
  const args = ['add', 'C:\\Users\\Joe & Team\\repo', '--skill', '*'];
  assert.deepEqual(
    buildCommandInvocation('skills', args, {
      platform: 'win32',
      env: {},
      findShim: () => 'C:\\npm\\skills.ps1',
    }),
    {
      command: 'powershell.exe',
      args: [
        '-NoLogo',
        '-NoProfile',
        '-NonInteractive',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        'C:\\npm\\skills.ps1',
        ...args,
      ],
    },
  );
  assert.deepEqual(
    buildCommandInvocation('skills', args, { platform: 'linux' }),
    { command: 'skills', args },
  );

  const runner = readFileSync(
    new URL('./journalism-core-install-canary.mjs', import.meta.url),
    'utf8',
  );
  assert.doesNotMatch(runner, /shell:\s*process\.platform/u);
  assert.match(runner, /shell:\s*false/u);
});

test('CI runs clean install canaries against current Claude and Codex releases', () => {
  const workflow = readFileSync(
    new URL('../.github/workflows/compatibility-canary.yml', import.meta.url),
    'utf8',
  );

  assert.match(workflow, /workflow_dispatch:/u);
  assert.match(workflow, /schedule:/u);
  assert.match(workflow, /@anthropic-ai\/claude-code@latest/u);
  assert.match(workflow, /@openai\/codex@latest/u);
  assert.match(workflow, /package: 'skills@latest'/u);
  assert.match(workflow, /client: codex-skills-global/u);
  assert.match(workflow, /journalism-core-install:[\s\S]*timeout-minutes: 15/u);
  assert.match(workflow, /node scripts\/journalism-core-install-canary\.mjs \$\{\{ matrix\.client \}\}/u);

  const runner = readFileSync(
    new URL('./journalism-core-install-canary.mjs', import.meta.url),
    'utf8',
  );
  assert.equal(SUBPROCESS_TIMEOUT_MS, 180_000);
  assert.match(runner, /timeout: SUBPROCESS_TIMEOUT_MS/u);
});
