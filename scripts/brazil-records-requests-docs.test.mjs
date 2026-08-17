import assert from 'node:assert/strict';
import { existsSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const DOCS = join(ROOT, 'docs');
const PAGE = join(DOCS, 'brazil-records-requests', 'index.html');
const STYLESHEET = join(DOCS, 'assets', 'tailwind', 'brazil-records-requests.css');
const SKILL = join(ROOT, 'journalism-core', 'skills', 'brazil-records-requests', 'SKILL.md');
const TEMPLATES = join(ROOT, 'journalism-core', 'skills', 'brazil-records-requests', 'templates');
const EXAMPLES = join(ROOT, 'journalism-core', 'skills', 'brazil-records-requests', 'examples');
const README = join(ROOT, 'README.md');

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
  assert.match(llms, /brazil-records-requests, Brazilian public records requests/iu);
  assert.equal((sitemap.match(/https:\/\/skills\.amditis\.tech\/brazil-records-requests\//gu) || []).length, 1);
});

test('Brazil records requests is part of the pinned Tailwind build', () => {
  const manifest = JSON.parse(readFileSync(join(DOCS, 'tailwind-pages.json'), 'utf8'));

  assert.ok(manifest['brazil-records-requests/index.html']);
  assert.equal(existsSync(STYLESHEET), true, 'generated brazil-records-requests.css is missing');
  assert.ok(statSync(STYLESHEET).size > 1000, 'generated stylesheet is unexpectedly small');
});

test('Brazil records requests keeps the legal routes in scope', () => {
  const skill = readFileSync(SKILL, 'utf8');
  const request = readFileSync(join(TEMPLATES, 'pedido-inicial.md'), 'utf8');
  const firstAppeal = readFileSync(join(TEMPLATES, 'recurso-1a-instancia.md'), 'utf8');
  const secondAppeal = readFileSync(join(TEMPLATES, 'recurso-2a-instancia.md'), 'utf8');
  const cguAppeal = readFileSync(join(TEMPLATES, 'recurso-cgu.md'), 'utf8');
  const example = readFileSync(join(EXAMPLES, 'exemplo-completo.md'), 'utf8');

  assert.match(skill, /sensitive, personal, classified,\s+or otherwise restricted information may be redacted or excluded/iu);
  assert.match(skill, /Decree 7\.724\/2012 binds the federal executive only/iu);
  assert.match(skill, /LGPD does not apply to processing carried\s+out exclusively for journalistic purposes/iu);
  assert.match(skill, /art\. 11, §1º, III/iu);
  assert.doesNotMatch(skill, /art\. 11, III/iu);
  assert.match(skill, /if it knows where the source information is/iu);
  assert.match(skill, /maximum restriction periods/iu);
  assert.match(skill, /120-day period\s+from notice of the challenged act/iu);

  assert.match(request, /art\. 11, §5º/iu);
  assert.match(request, /ENDEREÇO FÍSICO OU ELETRÔNICO PARA COMUNICAÇÕES/u);
  assert.match(request, /art\. 11, §1º, III/iu);
  assert.doesNotMatch(request, /art\. 8º, §3º,\s*incisos II e III/iu);

  assert.match(firstAppeal, /Poder\s+Executivo federal/u);
  assert.match(firstAppeal, /parágrafo\s+único/u);
  assert.doesNotMatch(firstAppeal, /não respondeu no prazo legal/u);
  assert.doesNotMatch(firstAppeal, /Ausência de resposta/u);
  assert.match(firstAppeal, /caso tenha conhecimento/u);

  assert.match(secondAppeal, /Poder\s+Executivo federal/u);
  assert.match(secondAppeal, /regra local/u);

  assert.match(cguAppeal, /informação não classificada/u);
  assert.match(cguAppeal, /autoridade classificadora/u);
  assert.match(cguAppeal, /procedimentos de classificação de informação não foram observados/u);
  assert.match(cguAppeal, /prazos ou outros procedimentos/u);

  assert.match(example, /caso tenha conhecimento/iu);
});

test('Brazil records requests page supplies the Open Graph image size', () => {
  const page = readFileSync(PAGE, 'utf8');

  assert.match(page, /<meta property="og:image:width" content="1200">/u);
  assert.match(page, /<meta property="og:image:height" content="630">/u);
});

test('Brazil records requests credits its contributor', () => {
  const page = readFileSync(PAGE, 'utf8');
  const skill = readFileSync(SKILL, 'utf8');

  assert.match(page, /Reinaldo Chaves/u);
  assert.match(page, /https:\/\/github\.com\/reichaves/u);
  assert.match(page, /https:\/\/github\.com\/jamditis\/claude-skills-journalism\/pull\/267/u);
  assert.match(skill, /Reinaldo Chaves/u);
  assert.match(skill, /https:\/\/github\.com\/reichaves/u);
  assert.match(skill, /https:\/\/github\.com\/jamditis\/claude-skills-journalism\/pull\/267/u);
});

test('Codex guidance gives the current journalism-core skill count', () => {
  const readme = readFileSync(README, 'utf8');

  assert.match(readme, /legacy-compatible package route exposes the 15 nested/u);
  assert.match(readme, /makes the 15 core skills available/u);
  assert.doesNotMatch(readme, /makes the 14 core skills available/u);
});
