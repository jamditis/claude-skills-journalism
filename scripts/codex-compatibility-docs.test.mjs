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
  assert.match(
    matrix,
    /`journalism-core` \| 1\.2\.0; 14 nested skills \| Runtime pilot passed on the Claude package and Codex project-standards paths/u,
  );

  const evidenceCells = matrix
    .split('\n')
    .filter((line) => /^\| `[^`]+` \|/u.test(line))
    .map((line) => line.split('|')[5].trim());
  assert.equal(evidenceCells.length, 12);
  for (const evidence of evidenceCells) {
    assert.match(evidence, /\[[^\]]+\]\(#[^)]+\)/u);
  }
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
