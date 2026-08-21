import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import test from 'node:test';

import {
  EVALUATION_TIMEOUT_MS,
  buildInvocation,
  loadFixtureSet,
  parseCliArgs,
  parseResponse,
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
    const categories = fixtureSet.cases
      .filter((item) => item.skill === skill)
      .map((item) => item.category)
      .sort();
    assert.deepEqual(categories, [...required].sort());
  }
  assert.equal(fixtureSet.cases.length, 21);
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
  const fixture = loadFixtureSet(FIXTURES).cases[0];
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

test('redaction removes common credentials and long bearer values', () => {
  const text = 'Authorization: Bearer abcdefghijklmnopqrstuvwxyz token=secret-value ANTHROPIC_API_KEY=abc123';
  const redacted = redactText(text);
  assert.doesNotMatch(redacted, /abcdefghijklmnopqrstuvwxyz|secret-value|abc123/u);
  assert.match(redacted, /\[REDACTED\]/u);
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
