import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const SKIP_DIRECTORIES = new Set(['.git', 'node_modules']);

function findNativeCodexManifests(directory = ROOT, manifests = []) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    if (entry.isDirectory() && SKIP_DIRECTORIES.has(entry.name)) continue;
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      findNativeCodexManifests(path, manifests);
      continue;
    }
    const repoPath = relative(ROOT, path).replaceAll('\\', '/');
    if (
      repoPath === '.agents/plugins/marketplace.json'
      || repoPath.endsWith('/.codex-plugin/plugin.json')
      || repoPath === '.codex-plugin/plugin.json'
      || repoPath.endsWith('/agents/openai.yaml')
      || repoPath === 'agents/openai.yaml'
    ) {
      manifests.push(repoPath);
    }
  }
  return manifests.sort();
}

test('the compatibility matrix classifies every marketplace package', () => {
  const matrix = readFileSync(join(ROOT, 'plans', 'codex-compatibility-matrix.md'), 'utf8');
  const rows = [...matrix.matchAll(/^\| `([^`]+)` \|/gmu)].map((match) => match[1]);

  assert.deepEqual(rows, [
    'autocontext',
    'dev-toolkit',
    'journalism-core',
    'okf-wiki',
    'pdf-design',
    'pdf-playground',
    'project-templates-toolkit',
    'research-toolkit',
    'security-toolkit',
    'superjawn',
    'video-toolkit',
    'visual-explainer',
  ]);
  assert.match(matrix, /`pdf-playground` \| 1\.3\.2/u);
  assert.match(matrix, /`video-toolkit` \| 1\.0\.3/u);
  assert.match(matrix, /V-phase-1: repaired standards baseline/u);
  assert.match(matrix, /J-release-1: paired journalism-core runtime pilot/u);
  assert.match(matrix, /V-ex-release-1: visual-explainer root-skill runtime pilot/u);
  assert.match(matrix, /Okf-release-1: okf-wiki no-Claude runtime pilot/u);
  assert.match(
    matrix,
    /`journalism-core` \| 1\.2\.0; 14 nested skills \| Runtime pilot passed on the Claude package and Codex project-standards paths/u,
  );
  assert.match(
    matrix,
    /`visual-explainer` \| 0\.7\.1; one root skill; eight source commands \| Runtime pilot passed on the Codex project-standards path; command surfaces unclaimed/u,
  );
  assert.match(
    matrix,
    /`okf-wiki` \| 0\.6\.1; one root skill; scripts and generated Claude settings \| Pre-set portable runtime pilot passed; instruction and Claude-output adapters remain/u,
  );
  assert.match(
    matrix,
    /Exclude the unadapted general instructions that name `AskUserQuestion` and `\$\{CLAUDE_SKILL_DIR\}`/u,
  );
  assert.match(matrix, /scripts\/okf-wiki-runtime-pilot\.mjs/u);
  assert.match(matrix, /scripts\/visual-explainer-runtime-pilot\.mjs/u);

  const evidenceCells = matrix
    .split('\n')
    .filter((line) => /^\| `[^`]+` \|/u.test(line))
    .map((line) => line.split('|')[5].trim());
  assert.equal(evidenceCells.length, 12);
  for (const evidence of evidenceCells) {
    assert.match(evidence, /\[[^\]]+\]\(#[^)]+\)/u);
  }
});

test('okf-wiki no-Claude evidence keeps Claude adapters outside Codex behavior', () => {
  const record = readFileSync(
    join(ROOT, 'plans', '2026-07-23-okf-wiki-runtime-pilot.md'),
    'utf8',
  );
  const skill = readFileSync(join(ROOT, 'okf-wiki', 'SKILL.md'), 'utf8');

  assert.match(record, /Tracking issue: \[#226\]/u);
  assert.match(record, /Codex CLI 0\.145\.0/u);
  assert.match(record, /skills CLI 1\.5\.20/u);
  assert.match(record, /`cabb43bc2515c6c30a3d0839909f786e7afbcba8`/u);
  assert.match(
    record,
    /f0af5c80f9daa4afcc71fa8e8919afa2098e59fe2f584bb85cc08df9807c99f1/u,
  );
  assert.match(
    record,
    /4a4689788d8d28e5b4d2a778dad5a246dd449abe56bb6a3fe05465e2256a47bd/u,
  );
  assert.match(record, /No interactive trust or approval prompt appeared/u);
  assert.match(record, /allowlisted executable path containing Codex/u);
  assert.match(record, /no Claude executable/u);
  assert.match(record, /byte-for-byte identical to the first run/u);
  assert.match(record, /runner now checks this before invoking Codex/u);
  assert.match(
    record,
    /runner also resolves both `claude` and `claude-code` on `PATH` without/u,
  );
  assert.match(record, /immutable pre-run snapshot/u);
  assert.match(record, /captured a JSONL transcript/u);
  assert.match(
    record,
    /installed-resource reads above to name the exact files, succeed/u,
  );
  assert.match(
    record,
    /fixture's narrow read, precheck, scaffold, validator, or inventory allowlist/u,
  );
  assert.match(record, /required the structured\s+command report to match/u);
  assert.match(record, /rejected any Claude executable/u);
  assert.match(
    record,
    /invoking session supplied an\s+external-isolation policy/u,
  );
  assert.doesNotMatch(record, /repository's `AGENTS\.md`/u);
  assert.match(record, /`AskUserQuestion` and `\$\{CLAUDE_SKILL_DIR\}` remain outside/u);
  assert.match(record, /removed the installed skill without touching the generated OKF project/u);
  assert.match(record, /The three `.claude\/` files are Claude adapter output/u);
  assert.doesNotMatch(record, /repository-wide Codex support/u);

  assert.match(skill, /The three generated `.claude\/` files are a Claude Code adapter/u);
  assert.match(skill, /Codex does not read them as project configuration/u);
  assert.match(
    skill,
    /does not establish that the unadapted\s+general route is portable/u,
  );
});

test('visual-explainer runtime evidence stays scoped to the tested Codex path', () => {
  const record = readFileSync(
    join(ROOT, 'plans', '2026-07-23-visual-explainer-runtime-pilot.md'),
    'utf8',
  );

  assert.match(record, /Tracking issue: \[#228\]/u);
  assert.match(record, /Codex CLI 0\.145\.0/u);
  assert.match(record, /skills CLI 1\.5\.20/u);
  assert.match(record, /project's `\.agents\/skills\/visual-explainer` directory/u);
  assert.match(
    record,
    /83e44cc015b0ebb5b3c19cb5e5f2127b873dec8f5b07d3dc0e3e865d082b6215/u,
  );
  assert.match(record, /did not register it under a standards skill root/u);
  assert.match(record, /three untested migrated-command wrapper skills/u);
  assert.match(record, /outside this root-skill pilot/u);
  assert.doesNotMatch(record, /repository-wide Codex support/u);
});

test('the README routes Codex users without implying mixed-install support', () => {
  const readme = readFileSync(join(ROOT, 'README.md'), 'utf8');

  assert.match(readme, /^# Journalism agent skills$/mu);
  assert.match(readme, /https:\/\/learn\.chatgpt\.com\/docs\/codex\/cli/u);
  assert.doesNotMatch(readme, /https:\/\/learn\.chatgpt\.com\/docs\/get-started/u);
  assert.match(readme, /npx skills@latest add[\s\S]*journalism-core[\s\S]*--agent codex --copy -g -y/u);
  assert.match(readme, /`~\/\.agents\/skills`/u);
  assert.match(readme, /codex plugin marketplace add jamditis\/claude-skills-journalism/u);
  assert.match(readme, /codex plugin add journalism-core@claude-skills-journalism/u);
  assert.match(readme, /use only one Codex installation path/u);
  assert.match(readme, /does not ship native Codex manifests yet/u);
  assert.doesNotMatch(readme, /Every skill in this repo now lives inside a plugin's `skills\/` directory/u);
  assert.match(readme, /root-skill packages/u);
  assert.match(readme, /visual-explainer\/SKILL\.md/u);
});

test('marketplace and child plugin metadata agree', () => {
  const marketplace = JSON.parse(
    readFileSync(join(ROOT, '.claude-plugin', 'marketplace.json'), 'utf8'),
  );

  for (const plugin of marketplace.plugins) {
    const childPath = join(ROOT, plugin.source, '.claude-plugin', 'plugin.json');
    const child = JSON.parse(readFileSync(childPath, 'utf8'));
    assert.equal(child.name, plugin.name, `${plugin.name} name drifted`);
    assert.equal(child.version, plugin.version, `${plugin.name} version drifted`);
    assert.equal(child.description, plugin.description, `${plugin.name} description drifted`);
  }
});

test('skill lint runs for compatibility claims and native Codex manifests', () => {
  const workflow = readFileSync(
    join(ROOT, '.github', 'workflows', 'skill-lint.yml'),
    'utf8',
  );

  for (const path of [
    'README.md',
    'plans/codex-compatibility-matrix.md',
    '.agents/plugins/**',
    '**/.codex-plugin/**',
    '**/agents/openai.yaml',
    '.github/workflows/compatibility-canary.yml',
  ]) {
    assert.match(workflow, new RegExp(`- '${path.replaceAll('*', '\\*')}'`, 'u'));
  }
});

test('phase one adds no native Codex manifest', () => {
  assert.deepEqual(findNativeCodexManifests(), []);
});
