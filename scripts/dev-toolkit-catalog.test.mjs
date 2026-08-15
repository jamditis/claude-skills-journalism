import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const DEV_SKILLS = join(ROOT, 'dev-toolkit', 'skills');
const DOCS = join(ROOT, 'docs');

test('every dev-toolkit skill has a public docs page', () => {
  const missing = readdirSync(DEV_SKILLS, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .filter((name) => !existsSync(join(DOCS, name, 'index.html')));

  assert.deepEqual(missing, []);
});

test('the public dev-toolkit card uses the current count and scope', () => {
  const homepage = readFileSync(join(DOCS, 'index.html'), 'utf8');

  assert.match(homepage, /Twelve development skills/u);
  assert.match(homepage, /08 \/ Development[\s\S]*?<span class="section-label">12 Skills<\/span>/u);
  assert.match(homepage, /context engineering/u);
  assert.doesNotMatch(homepage, /Eleven development skills/u);
});

test('llms.txt skill total matches its listed skills', () => {
  const catalog = readFileSync(join(DOCS, 'llms.txt'), 'utf8');
  const skillsSection = catalog.match(/## Skills \((\d+) total\)\n([\s\S]*?)\n## Hooks/u);

  assert.ok(skillsSection);
  const listedSkills = skillsSection[2].match(/^- /gmu) ?? [];
  assert.equal(listedSkills.length, Number(skillsSection[1]));
});

test('the context skill page shows plugin and standards-based install paths', () => {
  const page = readFileSync(join(DOCS, 'context-engineering-fundamentals', 'index.html'), 'utf8');

  assert.match(page, /\/plugin install dev-toolkit@claude-skills-journalism/u);
  assert.match(page, /npx skills@latest add jamditis\/claude-skills-journalism/u);
});

test('context guidance does not present universal recall percentages', () => {
  const skill = readFileSync(
    join(DEV_SKILLS, 'context-engineering-fundamentals', 'SKILL.md'),
    'utf8',
  );

  assert.doesNotMatch(skill, /Recall Accuracy/u);
  assert.doesNotMatch(skill, /~?\d{2}(?:-\d{2})?%/u);
  assert.doesNotMatch(skill, /Full attention, reliable recall/u);
  assert.match(skill, /Measure retrieval and reasoning quality on your own model and task/u);
});
