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
  prepareVariant,
  redactText,
  scoreResult,
} from './skill-behavior-eval.mjs';

const ROOT = resolve(import.meta.dirname, '..');
const FIXTURES = join(ROOT, 'scripts', 'fixtures', 'lean-skill-evaluations.json');

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

test('redaction removes common credentials and long bearer values', () => {
  const text = 'Authorization: Bearer abcdefghijklmnopqrstuvwxyz token=secret-value ANTHROPIC_API_KEY=abc123';
  const redacted = redactText(text);
  assert.doesNotMatch(redacted, /abcdefghijklmnopqrstuvwxyz|secret-value|abc123/u);
  assert.match(redacted, /\[REDACTED\]/u);
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
