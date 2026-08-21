import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { parse } from 'yaml';

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

  assert.match(homepage, /Thirteen development skills/u);
  assert.match(homepage, /08 \/ Development[\s\S]*?<span class="section-label">13 Skills<\/span>/u);
  assert.match(homepage, /context management/u);
  assert.match(homepage, /href="director\/"/u);
  assert.doesNotMatch(homepage, /Eleven development skills/u);
  assert.doesNotMatch(homepage, /Twelve development skills/u);
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

test('director is explicit-only and uses environment policy', () => {
  const skill = readFileSync(join(DEV_SKILLS, 'director', 'SKILL.md'), 'utf8');
  const frontmatter = skill.match(/^---\n([\s\S]*?)\n---/u);

  assert.ok(frontmatter);
  const metadata = parse(frontmatter[1]);
  assert.equal(metadata.name, 'director');
  assert.equal(metadata['disable-model-invocation'], true);
  assert.match(skill, /`CLAUDE\.md` policy that is applicable/u);
  assert.match(skill, /Delegate research, code writing, file changes, tests, and command execution/u);
  assert.doesNotMatch(skill, /\/home\/|gpt-\d|claude-(?:opus|sonnet|haiku)/iu);
});

test('director has one canonical page with exact invocation guidance', () => {
  const page = readFileSync(join(DOCS, 'director', 'index.html'), 'utf8');
  const homepage = readFileSync(join(DOCS, 'index.html'), 'utf8');
  const sitemap = readFileSync(join(DOCS, 'sitemap.xml'), 'utf8');

  assert.match(page, /property="og:url" content="https:\/\/skills\.amditis\.tech\/director\/"/u);
  assert.match(page, /tree\/master\/dev-toolkit\/skills\/director/u);
  assert.match(page, /\/dev-toolkit:director/u);
  assert.match(page, /literal <code>\/director<\/code>/u);
  assert.equal((homepage.match(/href="director\/"/gu) ?? []).length, 1);
  assert.equal(
    (sitemap.match(/https:\/\/skills\.amditis\.tech\/director\//gu) ?? []).length,
    1,
  );
});
