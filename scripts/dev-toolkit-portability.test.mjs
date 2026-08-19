import assert from 'node:assert/strict';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

import {
  ROOT,
  SKILLS_SUBDIR,
  MATRIX_PATH,
  SHARED,
  ADAPTER_REQUIRED,
  CLAUDE_ONLY,
  CLASSES,
  discoverSkills,
  classifySkill,
  buildMatrix,
  renderMatrixMarkdown,
} from './dev-toolkit-portability.mjs';

function skillDirsOnDisk() {
  const dir = join(ROOT, SKILLS_SUBDIR);
  return readdirSync(dir, { withFileTypes: true })
    .filter((e) => e.isDirectory() && existsSync(join(dir, e.name, 'SKILL.md')))
    .map((e) => e.name)
    .sort();
}

test('inventory is discovered from the repository, not hard-coded (AC1)', () => {
  const discovered = discoverSkills().map((s) => s.name);
  assert.deepEqual(discovered, skillDirsOnDisk());
  // The module source must not carry a hard-coded skill list or count.
  const source = readFileSync(join(ROOT, 'scripts', 'dev-toolkit-portability.mjs'), 'utf8');
  assert.doesNotMatch(source, /accessibility-compliance/u);
  assert.doesNotMatch(source, /\b12 skills\b/u);
});

test('every skill classifies into a known class with a reason (AC2)', () => {
  for (const row of buildMatrix()) {
    assert.ok(CLASSES.includes(row.class), `${row.name} has class ${row.class}`);
    assert.ok(row.reason.trim().length > 0, `${row.name} has a reason`);
    assert.equal(typeof row.automatic, 'boolean');
  }
});

test('instruction-file coupling: CLAUDE.md target vs AGENTS.md-aware', () => {
  const rows = Object.fromEntries(buildMatrix().map((r) => [r.name, r]));
  // Targets CLAUDE.md, no AGENTS.md mapping -> needs an adapter.
  assert.equal(rows['claude-md-updater'].class, ADAPTER_REQUIRED);
  assert.match(rows['claude-md-updater'].reason, /CLAUDE\.md/u);
  // Mentions CLAUDE.md but documents AGENTS.md as canonical -> portable.
  assert.equal(rows['vibe-coding'].class, SHARED);
});

test('tool coupling is the mechanic, not the noun', () => {
  const rows = Object.fromEntries(buildMatrix().map((r) => [r.name, r]));
  // Invokes the Task tool with subagent_type -> needs an adapter.
  assert.equal(rows['test-first-bugs'].class, ADAPTER_REQUIRED);
  assert.match(rows['test-first-bugs'].reason, /subagent_type/u);
  // It also auto-activates through a hook it names, so the matrix must not
  // record its auto-activation as "no".
  assert.equal(rows['test-first-bugs'].automatic, true);
  assert.ok(rows['test-first-bugs'].hooks.includes('bug-report-detector.md'));
  // Mentions "subagents" only as design advice -> portable.
  assert.equal(rows['context-engineering-fundamentals'].class, SHARED);
});

test('one-way-door is adapter-required and automatic with approval semantics (AC6)', () => {
  const row = buildMatrix().find((r) => r.name === 'one-way-door');
  assert.equal(row.class, ADAPTER_REQUIRED);
  assert.equal(row.automatic, true);
  assert.ok(row.hooks.includes('one-way-door-check.md'));
  assert.match(row.reason, /AskUserQuestion/u);
  assert.match(row.reason, /approval/u);
});

test('a portable skill stays shared', () => {
  const row = buildMatrix().find((r) => r.name === 'accessibility-compliance');
  assert.equal(row.class, SHARED);
  assert.equal(row.automatic, false);
});

test('the classifier reaches all three classes (trigger and non-trigger)', () => {
  const shared = classifySkill({ name: 'x', body: '# just guidance, no tools' });
  assert.equal(shared.class, SHARED);

  const adapter = classifySkill({ name: 'x', body: 'ask with AskUserQuestion here' });
  assert.equal(adapter.class, ADAPTER_REQUIRED);

  // ${CLAUDE_SKILL_DIR} is a Claude runtime path with no Codex equivalent.
  const claudeOnly = classifySkill({ name: 'x', body: 'reads ${CLAUDE_SKILL_DIR}/data' });
  assert.equal(claudeOnly.class, CLAUDE_ONLY);

  // Auto-activation comes from the skill naming its hook. A hook the skill does
  // not name (only cited as an example) is not attributed.
  const hooks = new Map([
    ['x-check.md', 'x-check'],
    ['other.md', 'other-hook'],
  ]);
  const auto = classifySkill({ name: 'x', body: 'activated by the x-check hook' }, hooks);
  assert.equal(auto.automatic, true);
  assert.deepEqual(auto.hooks, ['x-check.md']);
});

test('committed matrix matches the classifier output (drift guard, AC8)', () => {
  const committed = readFileSync(join(ROOT, MATRIX_PATH), 'utf8');
  assert.equal(
    committed,
    renderMatrixMarkdown(buildMatrix()),
    'plans/dev-toolkit-portability-matrix.md is stale; regenerate with `node scripts/dev-toolkit-portability.mjs`',
  );
});
