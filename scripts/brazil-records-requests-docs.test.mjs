import assert from 'node:assert/strict';
import { existsSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const DOCS = join(ROOT, 'docs');
const PAGE = join(DOCS, 'brazil-records-requests', 'index.html');
const STYLESHEET = join(DOCS, 'assets', 'tailwind', 'brazil-records-requests.css');

test('Brazil records requests has a public skill page', () => {
  assert.equal(existsSync(PAGE), true, 'docs/brazil-records-requests/index.html is missing');
  const page = readFileSync(PAGE, 'utf8');

  assert.match(page, /Brazilian public records requests/u);
  assert.match(page, /Fala\.BR/u);
  assert.match(page, /reclamação/u);
  assert.match(page, /public record.*public-interest publication/iu);
  assert.match(page, /\/plugin install journalism-core@claude-skills-journalism/u);
  assert.match(
    page,
    /<link rel="stylesheet" href="\.\.\/assets\/tailwind\/brazil-records-requests\.css" data-tailwind-build="3\.4\.19">/u,
  );
});

test('Brazil records requests is listed in the public catalogs', () => {
  const index = readFileSync(join(DOCS, 'index.html'), 'utf8');
  const llms = readFileSync(join(DOCS, 'llms.txt'), 'utf8');
  const sitemap = readFileSync(join(DOCS, 'sitemap.xml'), 'utf8');

  assert.equal((index.match(/href="brazil-records-requests\//gu) || []).length, 1);
  assert.match(llms, /brazil-records-requests — Brazilian public records requests/iu);
  assert.equal((sitemap.match(/https:\/\/skills\.amditis\.tech\/brazil-records-requests\//gu) || []).length, 1);
});

test('Brazil records requests is part of the pinned Tailwind build', () => {
  const manifest = JSON.parse(readFileSync(join(DOCS, 'tailwind-pages.json'), 'utf8'));

  assert.ok(manifest['brazil-records-requests/index.html']);
  assert.equal(existsSync(STYLESHEET), true, 'generated brazil-records-requests.css is missing');
  assert.ok(statSync(STYLESHEET).size > 1000, 'generated stylesheet is unexpectedly small');
});
