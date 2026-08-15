import assert from 'node:assert/strict';
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from 'node:fs';
import { spawnSync } from 'node:child_process';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const DOCS = join(ROOT, 'docs');
const PLAY_CDN_SCRIPT = /<script\b[^>]*\bsrc\s*=\s*(["'])https:\/\/cdn\.tailwindcss\.com(?:\/[^"']*)?\1[^>]*>/iu;
const INLINE_CONFIG = /\btailwind\.config\s*=/u;

function htmlFiles(dir = DOCS, files = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) htmlFiles(path, files);
    else if (entry.isFile() && entry.name.endsWith('.html')) files.push(path);
  }
  return files;
}

test('docs pages use committed Tailwind CSS instead of the Play CDN runtime', () => {
  const migrated = [];
  const violations = [];

  for (const file of htmlFiles()) {
    const source = readFileSync(file, 'utf8');
    const name = relative(ROOT, file);
    if (PLAY_CDN_SCRIPT.test(source) || INLINE_CONFIG.test(source)) violations.push(name);

    const match = source.match(
      /<link rel="stylesheet" href="([^"]+)" data-tailwind-build="3\.4\.19">/,
    );
    if (!match) continue;
    const stylesheet = resolve(dirname(file), match[1]);
    assert.equal(existsSync(stylesheet), true, `${name}: missing ${match[1]}`);
    assert.ok(statSync(stylesheet).size > 1000, `${name}: generated CSS is unexpectedly small`);
    migrated.push(name);
  }

  assert.deepEqual(violations, []);
  assert.equal(migrated.length, 51);
});

test('docs Tailwind build inputs and CI freshness gate are pinned', () => {
  const manifest = JSON.parse(readFileSync(join(DOCS, 'tailwind-pages.json'), 'utf8'));
  assert.equal(Object.keys(manifest).length, 51);

  const pkg = JSON.parse(readFileSync(join(ROOT, 'package.json'), 'utf8'));
  assert.equal(pkg.devDependencies.tailwindcss, '3.4.19');
  assert.equal(pkg.devDependencies.postcss, '8.5.21');
  assert.equal(pkg.scripts['build:docs-css'], 'node scripts/docs-tailwind.mjs --write');
  assert.equal(pkg.scripts['check:docs-css'], 'node scripts/docs-tailwind.mjs --check');

  const workflow = readFileSync(join(ROOT, '.github/workflows/docs-tailwind.yml'), 'utf8');
  assert.match(workflow, /npm ci/);
  assert.match(workflow, /npm run check:docs-css/);

  const builder = readFileSync(join(ROOT, 'scripts/docs-tailwind.mjs'), 'utf8');
  assert.match(builder, /fileURLToPath\(new URL\('\.\.', import\.meta\.url\)\)/u);
  assert.doesNotMatch(builder, /import\.meta\.url\)\.pathname/u);
});

test('docs Tailwind freshness check accepts a CRLF checkout', () => {
  const fixtureRoot = mkdtempSync(join(ROOT, '.tmp-docs-tailwind-'));

  try {
    mkdirSync(join(fixtureRoot, 'scripts'));
    mkdirSync(join(fixtureRoot, 'docs', 'assets', 'tailwind'), { recursive: true });

    const manifest = JSON.parse(readFileSync(join(DOCS, 'tailwind-pages.json'), 'utf8'));
    const lf = (source) => source.replaceAll('\r\n', '\n');
    const crlf = (source) => lf(source).replaceAll('\n', '\r\n');

    writeFileSync(
      join(fixtureRoot, 'scripts', 'docs-tailwind.mjs'),
      readFileSync(join(ROOT, 'scripts', 'docs-tailwind.mjs'), 'utf8'),
    );
    writeFileSync(
      join(fixtureRoot, 'docs', 'tailwind-pages.json'),
      JSON.stringify({ 'index.html': manifest['index.html'] }),
    );
    writeFileSync(
      join(fixtureRoot, 'docs', 'tailwind-input.css'),
      lf(readFileSync(join(DOCS, 'tailwind-input.css'), 'utf8')),
    );
    writeFileSync(
      join(fixtureRoot, 'docs', 'index.html'),
      lf(readFileSync(join(DOCS, 'index.html'), 'utf8')),
    );
    writeFileSync(
      join(fixtureRoot, 'docs', 'assets', 'tailwind', 'index.css'),
      crlf(readFileSync(join(DOCS, 'assets', 'tailwind', 'index.css'), 'utf8')),
    );

    const result = spawnSync(process.execPath, ['scripts/docs-tailwind.mjs', '--check'], {
      cwd: fixtureRoot,
      encoding: 'utf8',
    });

    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /Verified 1 page-specific Tailwind stylesheet/u);
  } finally {
    rmSync(fixtureRoot, { recursive: true, force: true });
  }
});
