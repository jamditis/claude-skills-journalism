// Classify every dev-toolkit skill by how much work it needs to run under Codex
// instead of Claude Code. The inventory is read from the repository, not
// hard-coded, so a skill added to dev-toolkit/skills is picked up on the next
// run. Regenerate the committed matrix with:
//   node scripts/dev-toolkit-portability.mjs
// The drift test in scripts/dev-toolkit-portability.test.mjs fails if the
// committed matrix and this classifier disagree.

import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = fileURLToPath(new URL('..', import.meta.url));
export const SKILLS_SUBDIR = join('dev-toolkit', 'skills');
export const HOOKS_SUBDIR = 'hooks';

export const SHARED = 'shared';
export const ADAPTER_REQUIRED = 'adapter-required';
export const CLAUDE_ONLY = 'claude-only';
export const CLASSES = [SHARED, ADAPTER_REQUIRED, CLAUDE_ONLY];

// Discover skills from the repository. A skill is any directory under
// dev-toolkit/skills that holds a SKILL.md. Returns records sorted by name.
export function discoverSkills(root = ROOT) {
  const dir = join(root, SKILLS_SUBDIR);
  const skills = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const skillPath = join(dir, entry.name, 'SKILL.md');
    if (!existsSync(skillPath)) continue;
    skills.push({ name: entry.name, body: readFileSync(skillPath, 'utf8') });
  }
  return skills.sort((a, b) => a.name.localeCompare(b.name));
}

function frontmatterName(body) {
  const match = body.match(/^---\n([\s\S]*?)\n---/u);
  if (!match) return '';
  const line = match[1].split('\n').find((l) => l.startsWith('name:'));
  return line ? line.slice('name:'.length).trim() : '';
}

// Top-level hooks/*.md files are Claude auto-activation wiring (PreToolUse,
// PostToolUse, UserPromptSubmit). A hook belongs to a skill when the skill's
// own SKILL.md names it, which is the skill declaring its wiring
// (test-first-bugs names bug-report-detector; one-way-door names
// one-way-door-check). Keying on the skill's declaration, not on the hook
// mentioning the skill, keeps a hook that only cites a skill as an example
// (pre-commit-review) from being miscounted. Returns filename -> hook name,
// repo-driven, no hand-kept table.
export function autoActivationHooks(root = ROOT) {
  const dir = join(root, HOOKS_SUBDIR);
  if (!existsSync(dir)) return new Map();
  const byFile = new Map();
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isFile() || !entry.name.endsWith('.md')) continue;
    const body = readFileSync(join(dir, entry.name), 'utf8');
    byFile.set(entry.name, frontmatterName(body) || entry.name.replace(/\.md$/u, ''));
  }
  return byFile;
}

function hasWord(body, word) {
  return new RegExp(`\\b${word}\\b`, 'u').test(body);
}

// Signals are the concrete, verifiable reasons a skill is coupled to Claude.
// Each carries a Codex mapping note or, for Claude-only, why none exists.
// `mappable: false` forces the Claude-only class.
export function detectSignals(body) {
  const signals = [];
  const namesClaudeMd = body.includes('CLAUDE.md');
  const namesAgentsMd = body.includes('AGENTS.md');

  // Instruction-file coupling. A skill that writes or targets CLAUDE.md is
  // coupled unless it already treats AGENTS.md as the canonical instruction
  // file (vibe-coding documents both, so it is not coupled).
  if (namesClaudeMd && !namesAgentsMd) {
    signals.push({
      kind: 'instruction-file',
      mappable: true,
      detail: 'targets CLAUDE.md; map the instruction file to AGENTS.md for Codex',
    });
  }

  // Claude tool vocabulary.
  if (hasWord(body, 'AskUserQuestion')) {
    signals.push({
      kind: 'claude-tool',
      mappable: true,
      detail: 'uses the AskUserQuestion tool; map to a Codex prompt or approval step',
    });
  }
  // The mechanic, not the noun: a bare mention of "subagents" as design advice
  // is not coupling. Require the Task tool or its subagent_type parameter.
  if (/\bTask tool\b/u.test(body) || /subagent_type/u.test(body)) {
    signals.push({
      kind: 'claude-tool',
      mappable: true,
      detail:
        'invokes the Task tool with subagent_type; map to a Codex multi-attempt run',
    });
  }

  // Claude hook auto-activation inside the skill body.
  if (/\bPostToolUse\b|\bPreToolUse\b|"matcher"/u.test(body)) {
    signals.push({
      kind: 'claude-hook',
      mappable: true,
      detail:
        'wires Claude PreToolUse/PostToolUse hooks; reproduce the failure and approval semantics before mapping, do not drop them',
    });
  }

  // Claude-only runtime coupling. ${CLAUDE_SKILL_DIR} names the installed skill
  // directory at Claude runtime and has no Codex equivalent; the package matrix
  // already treats it as an unadapted Claude marker.
  if (body.includes('CLAUDE_SKILL_DIR')) {
    signals.push({
      kind: 'claude-runtime',
      mappable: false,
      detail: 'depends on ${CLAUDE_SKILL_DIR}, a Claude runtime path with no Codex equivalent',
    });
  }

  return signals;
}

export function classifySkill(skill, hooks = new Map()) {
  const signals = detectSignals(skill.body);
  const hookFiles = [];
  for (const [hookFile, hookName] of hooks) {
    if (skill.body.includes(hookName)) hookFiles.push(hookFile);
  }
  const automatic =
    signals.some((s) => s.kind === 'claude-hook') || hookFiles.length > 0;

  let cls;
  if (signals.some((s) => s.mappable === false)) {
    cls = CLAUDE_ONLY;
  } else if (signals.length > 0) {
    cls = ADAPTER_REQUIRED;
  } else {
    cls = SHARED;
  }

  const rawReason =
    cls === SHARED
      ? 'No Claude-specific mechanic; runs under Codex as written.'
      : signals.map((s) => s.detail).join('; ') + '.';
  const reason = rawReason.charAt(0).toUpperCase() + rawReason.slice(1);

  return {
    name: skill.name,
    class: cls,
    automatic,
    hooks: hookFiles.sort(),
    reason,
  };
}

export function buildMatrix(root = ROOT) {
  const hooks = autoActivationHooks(root);
  return discoverSkills(root).map((skill) => classifySkill(skill, hooks));
}

function escapeCell(text) {
  return text.replaceAll('|', '\\|');
}

// Render the committed matrix. No timestamps or environment data, so the drift
// test can compare bytes. Ends with a trailing newline.
export function renderMatrixMarkdown(rows) {
  const counts = Object.fromEntries(CLASSES.map((c) => [c, 0]));
  for (const row of rows) counts[row.class] += 1;

  const lines = [];
  lines.push('# dev-toolkit per-skill portability');
  lines.push('');
  lines.push(
    'How far each dev-toolkit skill is from running under Codex instead of',
  );
  lines.push(
    'Claude Code. Generated from the repository by the classifier; do not edit by',
  );
  lines.push('hand. Regenerate with `node scripts/dev-toolkit-portability.mjs`.');
  lines.push('');
  lines.push(
    'Classes: **shared** runs as written; **adapter-required** needs a documented',
  );
  lines.push(
    'Codex mapping (instruction file, tool vocabulary, or hook); **Claude-only**',
  );
  lines.push('depends on a Claude runtime mechanic with no Codex equivalent.');
  lines.push('');
  lines.push(
    `Inventory: ${rows.length} skills discovered from \`dev-toolkit/skills\` ` +
      `(${counts[SHARED]} shared, ${counts[ADAPTER_REQUIRED]} adapter-required, ` +
      `${counts[CLAUDE_ONLY]} Claude-only).`,
  );
  lines.push('');
  lines.push('| Skill | Class | Auto-activation | Reason |');
  lines.push('| --- | --- | --- | --- |');
  for (const row of rows) {
    const auto = row.automatic
      ? `yes${row.hooks.length ? ` (${row.hooks.join(', ')})` : ''}`
      : 'no';
    lines.push(
      `| \`${row.name}\` | ${row.class} | ${auto} | ${escapeCell(row.reason)} |`,
    );
  }
  lines.push('');
  lines.push(
    'Adapter and Claude-only skills stay behind the one-installation-path rule in',
  );
  lines.push(
    '`plans/codex-compatibility-matrix.md` until each has a tested Codex mapping.',
  );
  lines.push('');
  return lines.join('\n');
}

const MATRIX_PATH = join('plans', 'dev-toolkit-portability-matrix.md');
export { MATRIX_PATH };

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  process.stdout.write(renderMatrixMarkdown(buildMatrix()));
}
