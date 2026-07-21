import assert from 'node:assert/strict';
import { lstatSync, readFileSync, readdirSync } from 'node:fs';
import { extname, join, relative } from 'node:path';
import test from 'node:test';

const ROOT = new URL('..', import.meta.url).pathname;
const SKIP = new Set(['.git', 'docs', 'node_modules', 'plans', 'research']);
const CDN_URL = /https:\/\/(?:cdn\.jsdelivr\.net\/npm|unpkg\.com|esm\.sh|cdnjs\.cloudflare\.com\/ajax\/libs|cdn\.tailwindcss\.com)[^'"`\s<>)]*/gi;

function sourceFiles(dir = ROOT, out = []) {
  for (const name of readdirSync(dir)) {
    if (SKIP.has(name)) continue;
    const path = join(dir, name);
    const stat = lstatSync(path);
    if (stat.isSymbolicLink()) continue;
    if (stat.isDirectory()) sourceFiles(path, out);
    else if (['.md', '.html'].includes(extname(path))) out.push(path);
  }
  return out;
}

function executableSource(path) {
  const source = readFileSync(path, 'utf8');
  if (extname(path) === '.html') return source;
  return [...source.matchAll(/```[^\n]*\n([\s\S]*?)```/g)]
    .map((match) => match[1])
    .join('\n');
}

function packageVersion(url) {
  if (url.startsWith('https://cdn.tailwindcss.com')) return null;
  const parsed = new URL(url);
  const parts = parsed.pathname.split('/').filter(Boolean);
  let spec;
  if (parsed.hostname === 'cdnjs.cloudflare.com') {
    return /^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$/.test(parts[3] || '')
      ? parts[3]
      : null;
  }
  if (parsed.hostname === 'cdn.jsdelivr.net') parts.shift();
  if (parts[0]?.startsWith('@')) spec = `${parts[0]}/${parts[1] || ''}`;
  else spec = parts[0] || '';
  const at = spec.lastIndexOf('@');
  if (at <= 0) return null;
  const version = spec.slice(at + 1);
  return /^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$/.test(version) ? version : null;
}

test('published code has no mutable runtime CDN package specifiers', () => {
  const violations = [];
  for (const path of sourceFiles()) {
    for (const match of executableSource(path).matchAll(CDN_URL)) {
      if (!packageVersion(match[0])) {
        violations.push(`${relative(ROOT, path)}: ${match[0]}`);
      }
    }
  }
  assert.deepEqual(violations, []);
});

test('audited security examples execute dependencies only from local paths', () => {
  const audited = [
    'dev-toolkit/skills/accessibility-compliance/SKILL.md',
    'dev-toolkit/skills/mobile-debugging/SKILL.md',
    'dev-toolkit/skills/zero-build-frontend/SKILL.md',
    'security-toolkit/skills/secure-auth/SKILL.md',
    'visual-explainer/references/libraries.md',
    'visual-explainer/templates/mermaid-flowchart.html',
    'visual-explainer/templates/slide-deck.html',
  ];
  const violations = audited.flatMap((file) =>
    [...executableSource(join(ROOT, file)).matchAll(CDN_URL)]
      .map((match) => `${file}: ${match[0]}`));
  assert.deepEqual(violations, []);

  const mobileDocs = readFileSync(join(ROOT, 'docs/mobile-debugging/index.html'), 'utf8');
  const zeroBuildDocs = readFileSync(join(ROOT, 'docs/zero-build-frontend/index.html'), 'utf8');
  assert.doesNotMatch(mobileDocs, /cdn\.jsdelivr\.net\/npm\/eruda/);
  assert.match(mobileDocs, /\/debug\/eruda-3\.4\.3\.js/);
  assert.doesNotMatch(zeroBuildDocs, /esm\.sh\/(?:react|htm)|unpkg\.com\/leaflet/);
  assert.match(zeroBuildDocs, /\/vendor\/react-runtime-19\.2\.8\.mjs/);
});

test('CDN version parser distinguishes exact versions from mutable tags', () => {
  assert.equal(packageVersion('https://unpkg.com/pkg@1.2.3/dist/x.js'), '1.2.3');
  assert.equal(packageVersion('https://esm.sh/@scope/pkg@2.3.4'), '2.3.4');
  assert.equal(packageVersion('https://cdnjs.cloudflare.com/ajax/libs/pkg/4.5.6/x.js'), '4.5.6');
  assert.equal(packageVersion('https://cdn.jsdelivr.net/npm/pkg@latest/x.js'), null);
  assert.equal(packageVersion('https://cdn.jsdelivr.net/npm/pkg@4/x.js'), null);
  assert.equal(packageVersion('https://unpkg.com/@scope/pkg/dist/x.js'), null);
});
