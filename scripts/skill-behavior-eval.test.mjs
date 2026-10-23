import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
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
import { parse as parseYaml } from 'yaml';

import {
  DEFAULT_FIXTURES,
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
const COMPAT_FIXTURES = join(ROOT, 'scripts', 'fixtures', 'compat-smoke.json');
const CLAUDE_ENVELOPES = JSON.parse(readFileSync(
  join(ROOT, 'scripts', 'fixtures', 'claude-output-envelopes.json'),
  'utf8',
));

const EXPLICIT_ONLY_SKILLS = new Set(['director']);

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

test('compatibility smoke fixtures cover the catalog and refresh skills exactly twice', () => {
  const fixtureSet = loadFixtureSet(COMPAT_FIXTURES);
  const catalog = parseYaml(readFileSync(join(ROOT, 'skills-catalog.yaml'), 'utf8'));
  // These skills come from the refresh layers and are not present on this branch yet.
  const refreshSkills = new Map([
    ['ponytail-dev', 'dev-toolkit'],
    ['surface-completeness', 'dev-toolkit'],
    ['goal-progress-bar', 'project-templates-toolkit'],
    ['unattended-agent-runs', 'newsroom-agent-ops'],
    ['scheduled-briefing', 'newsroom-agent-ops'],
    ['deadline-and-reply-tracking', 'newsroom-agent-ops'],
    ['email-request-intake', 'newsroom-agent-ops'],
    ['document-delivery', 'newsroom-agent-ops'],
    ['chat-mention-triage', 'newsroom-agent-ops'],
    ['record-reconciliation', 'newsroom-agent-ops'],
    ['multi-agent-coordinator', 'newsroom-agent-ops'],
    ['issue-pool-progression', 'newsroom-agent-ops'],
    ['meeting-transcript-actions', 'journalism-core'],
  ]);
  const expectedPackages = new Map(catalog.skills.map((skill) => [skill.name, skill.package]));
  for (const [skill, packageName] of refreshSkills) expectedPackages.set(skill, packageName);

  const ids = new Set();
  const casesBySkill = new Map();
  for (const fixture of fixtureSet.cases) {
    assert.ok(!ids.has(fixture.id), `duplicate fixture id: ${fixture.id}`);
    ids.add(fixture.id);
    assert.ok(
      ['activation', 'implicit-activation', 'unrelated-non-trigger'].includes(fixture.category),
      `${fixture.id} has an unknown category`,
    );
    assert.equal(fixture.package, expectedPackages.get(fixture.skill), fixture.id);
    assert.ok(
      fixture.expect.terms.length >= 1 && fixture.expect.terms.length <= 3,
      `${fixture.id} needs one to three expected terms`,
    );
    for (const term of fixture.expect.terms) {
      assert.equal(typeof term, 'string', `${fixture.id} terms must be strings`);
      assert.ok(term.trim().split(/\s+/u).length <= 3, `${fixture.id} term is too long`);
    }
    const cases = casesBySkill.get(fixture.skill) ?? [];
    cases.push(fixture);
    casesBySkill.set(fixture.skill, cases);
  }

  assert.deepEqual(
    [...casesBySkill.keys()].sort(),
    [...expectedPackages.keys()].sort(),
  );
  for (const [skill, cases] of casesBySkill) {
    // Explicit-only skills have no implicit case: they must not activate unprompted.
    const expected = EXPLICIT_ONLY_SKILLS.has(skill)
      ? ['activation', 'unrelated-non-trigger']
      : ['activation', 'implicit-activation', 'unrelated-non-trigger'];
    assert.deepEqual(cases.map((fixture) => fixture.category).sort(), expected, skill);
    const implicit = cases.find((fixture) => fixture.category === 'implicit-activation');
    if (implicit) {
      const activation = cases.find((fixture) => fixture.category === 'activation');
      assert.equal(implicit.prompt, activation.prompt, `${skill} implicit prompt must match activation`);
      assert.equal(implicit.expect.decision, 'use');
      assert.doesNotMatch(implicit.prompt.replaceAll('-', ' '), new RegExp(skill.replaceAll('-', ' '), 'iu'));
    }
    assert.equal(cases.find((fixture) => fixture.category === 'activation').expect.decision, 'use');
    assert.equal(
      cases.find((fixture) => fixture.category === 'unrelated-non-trigger').expect.decision,
      'reject',
    );
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

test('variant preparation supports root-level skill packages', () => {
  const temp = mkdtempSync(join(tmpdir(), 'skill-eval-root-test-'));
  try {
    const source = join(temp, 'source');
    const authHome = join(temp, 'codex-auth');
    mkdirSync(authHome);
    mkdirSync(join(source, 'visual-explainer'), { recursive: true });
    writeFileSync(
      join(source, 'visual-explainer', 'SKILL.md'),
      '---\nname: visual-explainer\ndescription: test\n---\n',
    );
    const prepared = prepareVariant({
      client: 'codex',
      sourceRoot: source,
      runRoot: join(temp, 'run'),
      packageName: 'visual-explainer',
      skillName: 'visual-explainer',
      authSourceHome: authHome,
    });
    assert.equal(
      readFileSync(
        join(prepared.projectDir, '.agents', 'skills', 'visual-explainer', 'SKILL.md'),
        'utf8',
      ),
      '---\nname: visual-explainer\ndescription: test\n---\n',
    );
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
  assert.ok(claude.args.includes('--strict-mcp-config'));
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
    assert.match(prompt, /load it through the runtime's skill mechanism/u);
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
    parseRuntimeEvidence('claude', claude, 'zero-build-frontend').candidateSkillActivated,
    true,
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
    parseRuntimeEvidence('codex', codex, 'zero-build-frontend').candidateSkillActivated,
    true,
  );
  assert.deepEqual(
    parseRuntimeEvidence('codex', codex, 'source-verification').candidateSkillActivated,
    false,
  );
  const windowsArrayCommand = codex.replace(
    JSON.stringify("sed -n '1,220p' .agents/skills/zero-build-frontend/SKILL.md"),
    JSON.stringify(['cmd', '/c', 'type .agents\\skills\\zero-build-frontend\\SKILL.md']),
  );
  assert.deepEqual(
    parseRuntimeEvidence('codex', windowsArrayCommand, 'zero-build-frontend').candidateSkillActivated,
    true,
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
      parseRuntimeEvidence('codex', changedDirectoryCommand, 'zero-build-frontend').candidateSkillActivated,
      true,
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
      parseRuntimeEvidence('codex', unrelatedRead, 'zero-build-frontend').candidateSkillActivated,
      false,
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
      candidateOnly: false,
      fixturesPath: DEFAULT_FIXTURES,
      concurrency: 1,
      competitive: false,
    },
  );
});

test('CLI parses and validates candidate-only, fixture, and concurrency options', () => {
  assert.deepEqual(
    parseCliArgs([
      '--candidate-only', '--candidate', '/candidate', '--fixtures', '/fixtures.json',
      '--all', '--runtime', 'both', '--max-cases', '100', '--concurrency', '4',
      '--output', '/results', '--dry-run',
    ]),
    {
      baselineRoot: undefined,
      candidateRoot: '/candidate',
      caseId: undefined,
      all: true,
      runtime: 'both',
      outputDir: '/results',
      dryRun: true,
      maxCases: 100,
      candidateOnly: true,
      fixturesPath: '/fixtures.json',
      concurrency: 4,
      competitive: false,
    },
  );
  for (const concurrency of ['0', '5', '1.5', 'no']) {
    assert.throws(
      () => parseCliArgs([
        '--candidate-only', '--candidate', '/candidate', '--case', 'one',
        '--concurrency', concurrency, '--output', '/results',
      ]),
      /--concurrency must be an integer from 1 through 4/u,
    );
  }
  assert.throws(
    () => parseCliArgs([
      '--candidate-only', '--baseline', '/base', '--candidate', '/candidate',
      '--case', 'one', '--output', '/results',
    ]),
    /--baseline cannot be used with --candidate-only/u,
  );
  assert.throws(
    () => parseCliArgs([
      '--candidate-only', '--candidate', '/candidate', '--fixtures',
      '--case', 'one', '--output', '/results',
    ]),
    /--fixtures requires a value/u,
  );
});

test('candidate-only dry-run uses the selected fixture and preserves result ordering', async () => {
  const temp = mkdtempSync(join(tmpdir(), 'skill-eval-dry-run-'));
  try {
    const fixturesPath = join(temp, 'fixtures.json');
    const outputDir = join(temp, 'output');
    const fixtureSet = {
      schemaVersion: 1,
      cases: [
        {
          id: 'visual-explainer-activation',
          skill: 'visual-explainer',
          package: 'visual-explainer',
          category: 'activation',
          prompt: 'Create an HTML timeline.',
          expect: { decision: 'use', branch: 'timeline', terms: ['HTML'] },
        },
        {
          id: 'missing-skill-unrelated',
          skill: 'missing-skill',
          package: 'missing-package',
          category: 'unrelated-non-trigger',
          prompt: 'Copyedit one sentence.',
          expect: { decision: 'reject', branch: 'copyediting', terms: ['copyedit'] },
        },
      ],
    };
    writeFileSync(fixturesPath, `${JSON.stringify(fixtureSet, null, 2)}\n`);
    let invocations = 0;
    await runCli([
      '--candidate-only', '--candidate', ROOT, '--fixtures', fixturesPath,
      '--all', '--runtime', 'both', '--max-cases', '2', '--concurrency', '3',
      '--output', outputDir, '--dry-run',
    ], {
      runInvocation: async () => {
        invocations += 1;
        throw new Error('dry-run invoked a client');
      },
    });

    assert.equal(invocations, 0);
    const report = JSON.parse(readFileSync(
      join(outputDir, 'skill-behavior-evaluation.json'),
      'utf8',
    ));
    assert.equal(
      report.fixtureDigest,
      createHash('sha256').update(readFileSync(fixturesPath)).digest('hex'),
    );
    assert.deepEqual(report.selection, {
      caseId: null,
      all: true,
      maxCases: 2,
      candidateOnly: true,
      competitive: false,
      installedSkills: 1,
      concurrency: 3,
    });
    assert.deepEqual(
      report.results.map((result) => [result.case, result.client, result.variant]),
      [
        ['visual-explainer-activation', 'claude', 'candidate'],
        ['visual-explainer-activation', 'codex', 'candidate'],
        ['missing-skill-unrelated', 'claude', 'candidate'],
        ['missing-skill-unrelated', 'codex', 'candidate'],
      ],
    );
    assert.deepEqual(report.missingSkills, [{ package: 'missing-package', skill: 'missing-skill' }]);
    assert.ok(report.results.slice(2).every((result) => result.status === 'missing-skill'));
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
});

test('CLI rejects an existing report before any client invocation', async () => {
  const temp = mkdtempSync(join(tmpdir(), 'skill-eval-existing-report-'));
  try {
    const reportPath = join(temp, 'skill-behavior-evaluation.json');
    writeFileSync(reportPath, '{}\n');
    let clientInvocations = 0;
    await assert.rejects(
      runCli([
        '--baseline', join(temp, 'baseline'),
        '--candidate', join(temp, 'candidate'),
        '--case', 'zbf-activation',
        '--runtime', 'codex',
        '--output', temp,
      ], {
        runInvocation: async () => {
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

test('implicit activation passes only when the client selected the skill itself', () => {
  const fixture = {
    id: 'x-implicit',
    skill: 'web-scraping',
    package: 'dev-toolkit',
    category: 'implicit-activation',
    prompt: 'Collect public agenda pages.',
    expect: { decision: 'use', branch: 'public scraping', terms: ['robots'] },
  };
  const response = { decision: 'use', skill: 'web-scraping', branch: 'public scraping', notes: 'robots' };
  assert.equal(scoreResult(fixture, response, { candidateSkillActivated: true }).pass, true);
  const missing = scoreResult(fixture, response, { candidateSkillActivated: false });
  assert.equal(missing.pass, false);
  assert.deepEqual(missing.failed, ['activation']);
  assert.equal(scoreResult(fixture, response, {}).pass, false);
});

test('selection scoring gates on decision, skill, and activation and keeps wording advisory', () => {
  const fixture = {
    id: 'x-implicit',
    skill: 'web-scraping',
    package: 'dev-toolkit',
    category: 'implicit-activation',
    scoring: 'selection',
    prompt: 'Collect public agenda pages.',
    expect: { decision: 'use', branch: 'public scraping', terms: ['provenance'] },
  };
  const response = { decision: 'use', skill: 'skill-evaluation:web-scraping', branch: 'agenda collection' };
  const result = scoreResult(fixture, response, { candidateSkillActivated: true });
  assert.equal(result.pass, true);
  assert.deepEqual(result.advisory, ['branch', 'terms']);
  assert.equal(scoreResult(fixture, { ...response, decision: 'reject' }, { candidateSkillActivated: true }).pass, false);
  assert.equal(scoreResult(fixture, { ...response, decision: 'ask' }, { candidateSkillActivated: true }).pass, true);
  assert.equal(scoreResult(fixture, { ...response, decision: 'ask' }, { candidateSkillActivated: false }).pass, false);
});

test('competitive runs install every fixture skill, drop the hint, and skip named cases', async () => {
  assert.throws(
    () => parseCliArgs([
      '--baseline', '/base', '--candidate', '/candidate', '--competitive',
      '--all', '--output', '/results',
    ]),
    /--competitive requires --candidate-only/u,
  );
  const temp = mkdtempSync(join(tmpdir(), 'skill-eval-competitive-'));
  try {
    const fixturesPath = join(temp, 'fixtures.json');
    const outputDir = join(temp, 'output');
    const fixtureSet = {
      schemaVersion: 1,
      cases: [
        {
          id: 'ws-activation',
          skill: 'web-scraping',
          package: 'dev-toolkit',
          category: 'activation',
          prompt: 'Collect public agenda pages.',
          expect: { decision: 'use', branch: 'scraping', terms: ['robots'] },
        },
        {
          id: 'ws-implicit',
          skill: 'web-scraping',
          package: 'dev-toolkit',
          category: 'implicit-activation',
          prompt: 'Collect public agenda pages.',
          expect: { decision: 'use', branch: 'scraping', terms: ['robots'] },
        },
        {
          id: 've-unrelated',
          skill: 'visual-explainer',
          package: 'visual-explainer',
          category: 'unrelated-non-trigger',
          prompt: 'Copyedit one sentence.',
          expect: { decision: 'reject', branch: 'copyediting', terms: ['copyedit'] },
        },
      ],
    };
    writeFileSync(fixturesPath, `${JSON.stringify(fixtureSet, null, 2)}\n`);
    await runCli([
      '--candidate-only', '--competitive', '--candidate', ROOT, '--fixtures', fixturesPath,
      '--all', '--runtime', 'codex', '--max-cases', '2', '--output', outputDir, '--dry-run',
    ]);
    const report = JSON.parse(readFileSync(
      join(outputDir, 'skill-behavior-evaluation.json'),
      'utf8',
    ));
    assert.deepEqual(report.results.map((item) => item.case), ['ws-implicit', 've-unrelated']);
    assert.equal(report.selection.competitive, true);
    assert.equal(report.selection.installedSkills, 2);
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }

  const runRoot = mkdtempSync(join(tmpdir(), 'skill-eval-competitive-prepare-'));
  try {
    const prepared = prepareVariant({
      client: 'codex',
      sourceRoot: ROOT,
      runRoot,
      packageName: 'dev-toolkit',
      skillName: 'web-scraping',
      authSourceHome: runRoot,
      extraSkills: [
        { package: 'dev-toolkit', skill: 'web-scraping' },
        { package: 'visual-explainer', skill: 'visual-explainer' },
      ],
    });
    assert.deepEqual(
      readdirSync(join(prepared.projectDir, '.agents', 'skills')).sort(),
      ['visual-explainer', 'web-scraping'],
    );
    const fixture = {
      id: 'ws-implicit',
      skill: 'web-scraping',
      category: 'implicit-activation',
      prompt: 'Collect public agenda pages.',
    };
    const prompt = buildInvocation('codex', fixture, prepared, {}, true).args.at(-1);
    assert.doesNotMatch(prompt, /candidate|single/iu);
    assert.doesNotMatch(prompt, /web-scraping/u);
  } finally {
    rmSync(runRoot, { recursive: true, force: true });
  }
});

test('selection-scored unrelated cases gate only on leaving the candidate alone', () => {
  const fixture = {
    id: 've-unrelated',
    skill: 'visual-explainer',
    package: 'visual-explainer',
    category: 'unrelated-non-trigger',
    scoring: 'selection',
    prompt: 'Copyedit one sentence.',
    expect: { decision: 'reject', branch: 'copyediting', terms: ['copyedit'] },
  };
  const otherSkill = { decision: 'use', skill: 'newsroom-style', branch: 'copyediting' };
  const evidence = { candidateSkillActivated: false, activatedSkills: ['newsroom-style'] };
  assert.equal(scoreResult(fixture, otherSkill, evidence).pass, true);
  assert.equal(scoreResult({ ...fixture, scoring: undefined }, otherSkill, evidence).pass, false);
  assert.equal(
    scoreResult(fixture, { ...otherSkill, skill: null }, { candidateSkillActivated: true }).pass,
    false,
  );
  assert.equal(
    scoreResult(fixture, { ...otherSkill, skill: 'visual-explainer' }, evidence).pass,
    false,
  );
});

test('runtime evidence lists every skill a Codex session read', () => {
  const codex = [
    {
      type: 'item.completed',
      item: {
        type: 'command_execution',
        command: 'cat .agents/skills/web-scraping/SKILL.md .agents/skills/web-archiving/SKILL.md',
        status: 'completed',
        exit_code: 0,
      },
    },
    { type: 'turn.completed', usage: { input_tokens: 1, output_tokens: 1 } },
  ].map((event) => JSON.stringify(event)).join('\n');
  assert.deepEqual(
    parseRuntimeEvidence('codex', codex, 'web-scraping').activatedSkills,
    ['web-archiving', 'web-scraping'],
  );
});
