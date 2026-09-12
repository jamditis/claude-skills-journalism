import assert from 'node:assert/strict';
import {
  existsSync,
  mkdtempSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  readlinkSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import test from 'node:test';

import {
  EVALUATION_TIMEOUT_MS,
  buildInvocation,
  loadFixtureSet,
  parseCliArgs,
  parseResponse,
  parseRuntimeEvidence,
  prepareVariant,
  redactText,
  runCli,
  runInvocation,
  scoreResult,
} from './skill-behavior-eval.mjs';

const ROOT = resolve(import.meta.dirname, '..');
const FIXTURES = join(ROOT, 'scripts', 'fixtures', 'lean-skill-evaluations.json');
const CLAUDE_ENVELOPES = JSON.parse(readFileSync(
  join(ROOT, 'scripts', 'fixtures', 'claude-output-envelopes.json'),
  'utf8',
));

test('fixture set covers every required category for each pilot skill', () => {
  const fixtureSet = loadFixtureSet(FIXTURES);
  const required = [
    'activation',
    'near-neighbor-rejection',
    'branch-selection',
    'safety-invariant',
    'incomplete-input',
    'authority-boundary',
    'output-artifact',
  ];
  for (const skill of ['zero-build-frontend', 'source-verification', 'data-journalism']) {
    const categories = new Set(fixtureSet.cases
      .filter((item) => item.skill === skill)
      .map((item) => item.category));
    for (const category of required) {
      assert.ok(categories.has(category), `${skill} needs a ${category} fixture`);
    }
  }
});

test('variant preparation copies only the selected regular skill tree', () => {
  const temp = mkdtempSync(join(tmpdir(), 'skill-eval-test-'));
  try {
    const source = join(temp, 'source');
    const runRoot = join(temp, 'run');
    const authHome = join(temp, 'codex-auth');
    mkdirSync(authHome);
    mkdirSync(join(source, 'dev-toolkit', 'skills', 'zero-build-frontend'), { recursive: true });
    writeFileSync(
      join(source, 'dev-toolkit', 'skills', 'zero-build-frontend', 'SKILL.md'),
      '---\nname: zero-build-frontend\ndescription: test\n---\n',
    );
    const prepared = prepareVariant({
      client: 'codex',
      sourceRoot: source,
      runRoot,
      packageName: 'dev-toolkit',
      skillName: 'zero-build-frontend',
      authSourceHome: authHome,
    });
    assert.equal(
      readFileSync(join(prepared.projectDir, '.agents', 'skills', 'zero-build-frontend', 'SKILL.md'), 'utf8'),
      '---\nname: zero-build-frontend\ndescription: test\n---\n',
    );
    assert.ok(prepared.outputSchema.endsWith('response-schema.json'));
    assert.notEqual(prepared.codexHome, authHome);
    assert.equal(existsSync(join(prepared.clientHome, '.codex', 'auth.json')), false);
    const invocation = buildInvocation('codex', {
      skill: 'zero-build-frontend',
      category: 'activation',
      prompt: 'Build a page.',
    }, prepared);
    assert.deepEqual(invocation.env, {
      CODEX_HOME: prepared.codexHome,
      HOME: prepared.clientHome,
      USERPROFILE: prepared.clientHome,
    });
    assert.equal(invocation.args.includes('--enable'), false);
    assert.equal(invocation.args.includes('skip_host_skill_discovery'), false);
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
});

test('client discovery homes expose only linked authentication files', () => {
  const temp = mkdtempSync(join(tmpdir(), 'skill-eval-auth-test-'));
  try {
    for (const [client, authFile] of [['codex', 'auth.json'], ['claude', '.credentials.json']]) {
      const authHome = join(temp, `${client}-auth`);
      mkdirSync(join(authHome, 'skills', 'zero-build-frontend'), { recursive: true });
      writeFileSync(join(authHome, authFile), '{}');
      writeFileSync(join(authHome, 'skills', 'zero-build-frontend', 'SKILL.md'), 'stale skill');
      writeFileSync(join(authHome, 'settings.json'), '{}');
      const prepared = prepareVariant({
        client, sourceRoot: ROOT, runRoot: join(temp, client),
        packageName: 'dev-toolkit', skillName: 'zero-build-frontend', authSourceHome: authHome,
      });
      const isolated = client === 'codex' ? prepared.codexHome : prepared.claudeConfigDir;
      assert.notEqual(isolated, authHome);
      assert.deepEqual(readdirSync(isolated), [authFile]);
      assert.equal(readlinkSync(join(isolated, authFile)), join(authHome, authFile));
      const invocation = buildInvocation(client, loadFixtureSet(FIXTURES).cases[0], prepared);
      assert.equal(invocation.env.HOME, prepared.clientHome);
      assert.equal(invocation.env.USERPROFILE, prepared.clientHome);
      rmSync(join(temp, client), { recursive: true });
      assert.equal(readFileSync(join(authHome, authFile), 'utf8'), '{}');
    }
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
});

test('invocations use bounded isolated print sessions without direct APIs', () => {
  const fixture = loadFixtureSet(FIXTURES).cases[0];
  const claude = buildInvocation('claude', fixture, {
    projectDir: '/tmp/eval/project',
    pluginDir: '/tmp/eval/plugin',
    outputSchema: '/tmp/eval/schema.json',
    claudeConfigDir: '/home/test/.claude',
  });
  assert.equal(claude.command, 'claude');
  assert.ok(claude.args.includes('-p'));
  assert.ok(claude.args.includes('--plugin-dir'));
  assert.ok(claude.args.includes('--no-session-persistence'));
  assert.deepEqual(claude.args.slice(-2), ['--tools', '']);

  const codex = buildInvocation('codex', fixture, {
    projectDir: '/tmp/eval/project',
    codexHome: '/tmp/eval/codex',
    outputSchema: '/tmp/eval/schema.json',
  });
  assert.equal(codex.command, 'codex');
  assert.ok(codex.args.includes('exec'));
  assert.ok(codex.args.includes('--ephemeral'));
  assert.deepEqual(
    codex.args.slice(codex.args.indexOf('--sandbox'), codex.args.indexOf('--sandbox') + 2),
    ['--sandbox', 'read-only'],
  );
  assert.equal(EVALUATION_TIMEOUT_MS, 180_000);

  const pinnedClaude = buildInvocation('claude', fixture, {
    projectDir: '/tmp/eval/project',
    pluginDir: '/tmp/eval/plugin',
    outputSchema: '/tmp/eval/schema.json',
    claudeConfigDir: '/home/test/.claude',
  }, { SKILL_EVAL_CLAUDE_MODEL: 'claude-opus-5' });
  assert.deepEqual(
    pinnedClaude.args.slice(pinnedClaude.args.indexOf('--model'), pinnedClaude.args.indexOf('--model') + 2),
    ['--model', 'claude-opus-5'],
  );
});

test('unrelated fixtures use implicit discovery without forcing either client syntax', () => {
  const fixture = loadFixtureSet(FIXTURES).cases.find(
    (item) => item.id === 'zbf-unrelated',
  );
  for (const [client, forcedSyntax] of [
    ['codex', /\$zero-build-frontend/u],
    ['claude', /\/skill-evaluation:zero-build-frontend/u],
  ]) {
    const invocation = buildInvocation(client, fixture, {
      projectDir: '/tmp/eval/project',
      pluginDir: '/tmp/eval/plugin',
      codexHome: '/tmp/eval/codex',
      claudeConfigDir: '/home/test/.claude',
      outputSchema: '/tmp/eval/schema.json',
      responsePath: '/tmp/eval/response.json',
    });
    const prompt = client === 'claude'
      ? invocation.args[invocation.args.indexOf('-p') + 1]
      : invocation.args.at(-1);

    assert.doesNotMatch(prompt, forcedSyntax);
    assert.doesNotMatch(prompt, /project skill/u);
    assert.match(prompt, /candidate skill/u);
    assert.match(prompt, /Do not activate it merely because it is installed/u);
    assert.match(prompt, /never name the rejected candidate skill/u);
    assert.match(prompt, /Use only the runtime's skill mechanism/u);
    if (client === 'claude') {
      assert.ok(invocation.args.includes('--verbose'));
      assert.deepEqual(
        invocation.args.slice(
          invocation.args.indexOf('--output-format'),
          invocation.args.indexOf('--output-format') + 2,
        ),
        ['--output-format', 'stream-json'],
      );
      assert.deepEqual(
        invocation.args.slice(-4),
        ['--tools', 'Skill', '--allowedTools', 'Skill'],
      );
    }
  }
});

test('runtime evidence detects candidate skill activation in both client transcripts', () => {
  const claude = [
    { type: 'system', subtype: 'init' },
    {
      type: 'assistant',
      message: {
        content: [{
          type: 'tool_use',
          name: 'Skill',
          input: { skill: 'skill-evaluation:zero-build-frontend' },
        }],
      },
    },
    CLAUDE_ENVELOPES.legacy,
  ].map((event) => JSON.stringify(event)).join('\n');
  assert.deepEqual(
    parseRuntimeEvidence('claude', claude, 'zero-build-frontend'),
    { candidateSkillActivated: true },
  );

  const codex = [
    { type: 'thread.started', thread_id: 'thread-1' },
    {
      type: 'item.completed',
      item: {
        type: 'command_execution',
        command: "sed -n '1,220p' .agents/skills/zero-build-frontend/SKILL.md",
        status: 'completed',
        exit_code: 0,
      },
    },
    { type: 'turn.completed', usage: { input_tokens: 1, output_tokens: 1 } },
  ].map((event) => JSON.stringify(event)).join('\n');
  assert.deepEqual(
    parseRuntimeEvidence('codex', codex, 'zero-build-frontend'),
    { candidateSkillActivated: true },
  );
  assert.deepEqual(
    parseRuntimeEvidence('codex', codex, 'source-verification'),
    { candidateSkillActivated: false },
  );
  const windowsArrayCommand = codex.replace(
    JSON.stringify("sed -n '1,220p' .agents/skills/zero-build-frontend/SKILL.md"),
    JSON.stringify(['cmd', '/c', 'type .agents\\skills\\zero-build-frontend\\SKILL.md']),
  );
  assert.deepEqual(
    parseRuntimeEvidence('codex', windowsArrayCommand, 'zero-build-frontend'),
    { candidateSkillActivated: true },
  );
  for (const command of [
    'cd .agents/skills/zero-build-frontend && cat SKILL.md',
    'cd .agents/skills && cat zero-build-frontend/SKILL.md',
    'Set-Location .agents\\skills\\zero-build-frontend; Get-Content SKILL.md',
    'sl -LiteralPath ".agents/skills/zero-build-frontend"; Get-Content SKILL.md',
    "chdir -Path '.agents/skills/zero-build-frontend'; Get-Content SKILL.md",
    'Set-Location -Path "C:/work with spaces/.agents/skills/zero-build-frontend"; Get-Content SKILL.md',
  ]) {
    const changedDirectoryCommand = codex.replace(
      JSON.stringify("sed -n '1,220p' .agents/skills/zero-build-frontend/SKILL.md"),
      JSON.stringify(command),
    );
    assert.deepEqual(
      parseRuntimeEvidence('codex', changedDirectoryCommand, 'zero-build-frontend'),
      { candidateSkillActivated: true },
    );
  }
  for (const command of [
    'echo .agents/skills/zero-build-frontend && cat other/SKILL.md',
    'cat .agents/skills/source-verification/SKILL.md',
  ]) {
    const unrelatedRead = codex.replace(
      JSON.stringify("sed -n '1,220p' .agents/skills/zero-build-frontend/SKILL.md"),
      JSON.stringify(command),
    );
    assert.deepEqual(
      parseRuntimeEvidence('codex', unrelatedRead, 'zero-build-frontend'),
      { candidateSkillActivated: false },
    );
  }
  assert.throws(
    () => parseRuntimeEvidence('codex', '', 'source-verification'),
    /transcript is empty/u,
  );
  assert.throws(
    () => parseRuntimeEvidence(
      'codex',
      JSON.stringify({ type: 'thread.started', thread_id: 'thread-1' }),
      'source-verification',
    ),
    /did not complete/u,
  );
});

test('full-run documentation stays aligned with the fixture count', () => {
  const fixtureCount = loadFixtureSet(FIXTURES).cases.length;
  const docs = readFileSync(join(ROOT, 'docs', 'skill-behavior-evaluations.md'), 'utf8');

  assert.match(docs, new RegExp(`full set starts ${fixtureCount * 4} sessions`, 'u'));
  assert.match(docs, new RegExp(`from ${fixtureCount} cases, two clients, and two variants`, 'u'));
  assert.match(docs, new RegExp(`--max-cases ${fixtureCount}\\b`, 'u'));
});

test('Claude parser accepts legacy objects and current event arrays', () => {
  assert.deepEqual(
    parseResponse('claude', JSON.stringify(CLAUDE_ENVELOPES.legacy)),
    CLAUDE_ENVELOPES.response,
  );
  assert.deepEqual(
    parseResponse('claude', JSON.stringify(CLAUDE_ENVELOPES.current)),
    CLAUDE_ENVELOPES.response,
  );
});

test('Claude parser fails closed on error, ambiguous, missing, and malformed results', () => {
  assert.throws(
    () => parseResponse('claude', JSON.stringify(CLAUDE_ENVELOPES.error)),
    /reported an error/u,
  );
  assert.throws(
    () => parseResponse('claude', JSON.stringify(CLAUDE_ENVELOPES.ambiguous)),
    /exactly one result event/u,
  );
  assert.throws(
    () => parseResponse('claude', JSON.stringify(CLAUDE_ENVELOPES.missing)),
    /exactly one result event/u,
  );
  assert.throws(
    () => parseResponse('claude', JSON.stringify({ type: 'result', subtype: 'success' })),
    /did not contain output/u,
  );
  assert.throws(
    () => parseResponse('claude', JSON.stringify({
      type: 'result',
      subtype: 'success',
      result: 'not JSON',
    })),
    /output was not valid JSON/u,
  );
});

test('scoring checks the decision, branch, skill, and required terms', () => {
  const fixture = loadFixtureSet(FIXTURES).cases.find(
    (item) => item.id === 'zbf-activation',
  );
  const pass = scoreResult(fixture, {
    decision: 'use',
    skill: 'zero-build-frontend',
    branch: 'zero-build',
    rationale: 'Use static files that execute in the browser.',
    actions: ['Create static files'],
    artifact: { name: 'page', required_fields: ['files'] },
    safety: [],
  });
  assert.equal(pass.pass, true);
  assert.equal(pass.score, 4);

  const fail = scoreResult(fixture, {
    decision: 'reject',
    skill: null,
    branch: 'other',
    rationale: 'No match.',
    actions: [],
    artifact: null,
    safety: [],
  });
  assert.equal(fail.pass, false);
  assert.deepEqual(fail.failed, ['decision', 'skill', 'branch', 'terms']);
});

test('scoring accepts declared branch and term alternatives without weakening other checks', () => {
  const fixture = {
    skill: 'source-verification',
    expect: {
      decision: 'stop',
      branch: 'source-protection',
      branchAlternatives: ['source protection', 'privacy safe verification'],
      terms: [['redact', 'do not publish'], ['confidential', 'private source']],
    },
  };
  const response = {
    decision: 'stop',
    skill: 'source-verification',
    branch: 'privacy-safe image verification',
    rationale: 'Do not publish the private source metadata.',
    actions: [],
    artifact: null,
    safety: ['Protect the confidential source.'],
  };
  assert.equal(scoreResult(fixture, response).pass, true);
  assert.equal(
    scoreResult(fixture, { ...response, decision: 'use' }).pass,
    false,
  );
  assert.equal(
    scoreResult(fixture, { ...response, skill: 'data-journalism' }).pass,
    false,
  );
});

test('near-neighbor rejection requires a named workflow branch', () => {
  const fixtures = loadFixtureSet(FIXTURES).cases
    .filter((fixture) => fixture.category === 'near-neighbor-rejection');

  for (const fixture of fixtures) {
    const response = {
      decision: 'reject',
      skill: null,
      branch: 'none',
      rationale: `This request needs ${JSON.stringify(fixture.expect.terms)}.`,
      actions: [],
      artifact: null,
      safety: [],
    };
    const result = scoreResult(fixture, response);
    assert.equal(result.pass, false, fixture.id);
    assert.ok(result.failed.includes('branch'), fixture.id);
    assert.ok(!result.failed.includes('decision'), fixture.id);
    assert.ok(!result.failed.includes('skill'), fixture.id);
  }
});

test('unrelated rejection fails when the runtime activated the candidate skill', () => {
  const fixture = loadFixtureSet(FIXTURES).cases.find(
    (item) => item.id === 'zbf-unrelated',
  );
  const response = {
    decision: 'reject',
    skill: null,
    branch: fixture.expect.branch,
    rationale: `This request needs ${JSON.stringify(fixture.expect.terms)}.`,
    actions: [],
    artifact: null,
    safety: [],
  };

  assert.equal(
    scoreResult(fixture, response, { candidateSkillActivated: false }).pass,
    true,
  );
  for (const skill of ['zero-build-frontend', 'skill-evaluation:zero-build-frontend', '/skill-evaluation:zero-build-frontend']) {
    const rejectedCandidate = scoreResult(fixture, { ...response, skill }, { candidateSkillActivated: false });
    assert.equal(rejectedCandidate.pass, false);
    assert.ok(rejectedCandidate.failed.includes('skill'));
  }
  const activated = scoreResult(
    fixture,
    response,
    { candidateSkillActivated: true },
  );
  assert.equal(activated.pass, false);
  assert.equal(activated.score, 4);
  assert.ok(activated.failed.includes('activation'));
  const missingEvidence = scoreResult(fixture, response);
  assert.equal(missingEvidence.pass, false);
  assert.ok(missingEvidence.failed.includes('activation'));

  const failedResponse = scoreResult(fixture, {
    decision: 'use',
    skill: fixture.skill,
    branch: 'none',
    rationale: 'No match.',
    actions: [],
    artifact: null,
    safety: [],
  }, { candidateSkillActivated: true });
  assert.equal(failedResponse.score, 0);
  assert.deepEqual(
    failedResponse.failed,
    ['decision', 'skill', 'branch', 'terms', 'activation'],
  );
});

test('redaction removes common credentials and long bearer values', () => {
  const text = 'Authorization: Bearer abcdefghijklmnopqrstuvwxyz token=secret-value ANTHROPIC_API_KEY=abc123';
  const redacted = redactText(text);
  assert.doesNotMatch(redacted, /abcdefghijklmnopqrstuvwxyz|secret-value|abc123/u);
  assert.match(redacted, /\[REDACTED\]/u);
});

test('redaction removes provider token formats without matching short lookalikes', () => {
  const secrets = [
    'sk-ant-api03-abcdefghijklmnopqrstuvwxyz0123456789',
    'sk-proj-abcdefghijklmnopqrstuvwxyz0123456789',
    'sk-abcdefghijklmnopqrstuvwxyz0123456789',
    'ghp_abcdefghijklmnopqrstuvwxyz0123456789',
    'gho_abcdefghijklmnopqrstuvwxyz0123456789',
    'ghu_abcdefghijklmnopqrstuvwxyz0123456789',
    'ghs_abcdefghijklmnopqrstuvwxyz0123456789',
    'ghr_abcdefghijklmnopqrstuvwxyz0123456789',
    'github_pat_abcdefghijklmnopqrstuvwxyz_0123456789',
  ];
  const nearMisses = [
    'sk-ant-example',
    'sk-proj-demo',
    'sk-documentation',
    'ghp_example',
    'gho_sample',
    'ghu_placeholder',
    'ghs_test',
    'ghr_short',
    'github_pat_example',
  ];
  const redacted = redactText([...secrets, ...nearMisses].join(' '));

  for (const secret of secrets) assert.ok(!redacted.includes(secret), secret);
  for (const nearMiss of nearMisses) assert.ok(redacted.includes(nearMiss), nearMiss);
  assert.equal(redacted.match(/\[REDACTED\]/gu)?.length, secrets.length);
});

test('runtime failures include safe process launch and timeout details', () => {
  const invocation = {
    command: 'missing-client',
    args: [],
    cwd: '/tmp',
    env: {},
  };
  assert.throws(
    () => runInvocation(invocation, '/tmp/no-response', 'codex', () => ({
      status: null,
      signal: null,
      stderr: '',
      stdout: '',
      error: Object.assign(new Error('spawnSync missing-client ENOENT'), { code: 'ENOENT' }),
    })),
    /ENOENT: spawnSync missing-client ENOENT/u,
  );
  assert.throws(
    () => runInvocation(invocation, '/tmp/no-response', 'codex', () => ({
      status: null,
      signal: 'SIGTERM',
      stderr: '',
      stdout: '',
      error: Object.assign(new Error('spawnSync missing-client ETIMEDOUT'), { code: 'ETIMEDOUT' }),
    })),
    /signal SIGTERM; ETIMEDOUT: spawnSync missing-client ETIMEDOUT/u,
  );
  assert.throws(
    () => runInvocation(invocation, '/tmp/no-response', 'codex', () => ({
      status: null,
      signal: null,
      stderr: 'x'.repeat(3_000),
      stdout: '',
      error: Object.assign(new Error('spawnSync missing-client ENOENT'), { code: 'ENOENT' }),
    })),
    /ENOENT: spawnSync missing-client ENOENT/u,
  );
});

test('CLI requires an explicit bounded selection and rejects unsafe overlap', () => {
  assert.throws(
    () => parseCliArgs(['--baseline', '/a', '--candidate', '/b', '--output', '/results']),
    /Select one case with --case or explicitly use --all/u,
  );
  assert.throws(
    () => parseCliArgs([
      '--baseline', '/same', '--candidate', '/same', '--case', 'zbf-activation',
      '--output', '/results',
    ]),
    /must be different/u,
  );
  assert.deepEqual(
    parseCliArgs([
      '--baseline', '/base', '--candidate', '/candidate', '--case', 'zbf-activation',
      '--runtime', 'claude', '--output', '/results', '--dry-run',
    ]),
    {
      baselineRoot: '/base',
      candidateRoot: '/candidate',
      caseId: 'zbf-activation',
      all: false,
      runtime: 'claude',
      outputDir: '/results',
      dryRun: true,
      maxCases: 1,
    },
  );
});

test('CLI rejects an existing report before any client invocation', () => {
  const temp = mkdtempSync(join(tmpdir(), 'skill-eval-existing-report-'));
  try {
    const reportPath = join(temp, 'skill-behavior-evaluation.json');
    writeFileSync(reportPath, '{}\n');
    let clientInvocations = 0;
    assert.throws(
      () => runCli([
        '--baseline', join(temp, 'baseline'),
        '--candidate', join(temp, 'candidate'),
        '--case', 'zbf-activation',
        '--runtime', 'codex',
        '--output', temp,
      ], {
        run: () => {
          clientInvocations += 1;
          return { status: 0, stderr: '', stdout: '' };
        },
      }),
      /Report already exists/u,
    );
    assert.equal(clientInvocations, 0);
    assert.equal(readFileSync(reportPath, 'utf8'), '{}\n');
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
});
