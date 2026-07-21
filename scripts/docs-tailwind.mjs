import { mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import postcss from 'postcss';
import tailwindcss from 'tailwindcss';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const DOCS = join(ROOT, 'docs');
const MANIFEST = join(DOCS, 'tailwind-pages.json');
const INPUT = join(DOCS, 'tailwind-input.css');
const OUTPUT_DIR = join(DOCS, 'assets', 'tailwind');
const PLAY_CDN_SCRIPT = /<script\b[^>]*\bsrc\s*=\s*(["'])https:\/\/cdn\.tailwindcss\.com(?:\/[^"']*)?\1[^>]*>/iu;
const INLINE_CONFIG = /\btailwind\.config\s*=/u;
const BUILD_VERSION = '3.4.19';
const LINK_PATTERN = /<link rel="stylesheet" href="([^"]+)" data-tailwind-build="3\.4\.19">/gu;

function htmlFiles(dir = DOCS, files = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) htmlFiles(path, files);
    else if (entry.isFile() && entry.name.endsWith('.html')) files.push(path);
  }
  return files.sort();
}

function relativePage(file) {
  return relative(DOCS, file).split(sep).join('/');
}

function outputName(page) {
  if (page === 'index.html') return 'index.css';
  return page.replace(/\/index\.html$/u, '').replaceAll('/', '--') + '.css';
}

function stylesheetHref(file) {
  const target = join(OUTPUT_DIR, outputName(relativePage(file)));
  return relative(dirname(file), target).split(sep).join('/');
}

async function compilePage(file, config) {
  const html = readFileSync(file, 'utf8');
  const input = readFileSync(INPUT, 'utf8');
  const result = await postcss([
    tailwindcss({
      ...config,
      content: [{ raw: html, extension: 'html' }],
    }),
  ]).process(input, { from: INPUT, to: undefined });
  return `/* Generated for ${relativePage(file)} by Tailwind CSS ${BUILD_VERSION}. */\n${result.css}`;
}

function readManifest() {
  return JSON.parse(readFileSync(MANIFEST, 'utf8'));
}

async function writeBuild() {
  const manifest = readManifest();
  mkdirSync(OUTPUT_DIR, { recursive: true });
  for (const [page, config] of Object.entries(manifest)) {
    const file = join(DOCS, page);
    writeFileSync(join(OUTPUT_DIR, outputName(page)), await compilePage(file, config));
  }
}

async function checkBuild() {
  const manifest = readManifest();
  const expectedPages = new Set(Object.keys(manifest));
  const expectedOutputs = new Set([...expectedPages].map(outputName));
  const linkedPages = new Set();
  const problems = [];

  for (const file of htmlFiles()) {
    const source = readFileSync(file, 'utf8');
    const page = relativePage(file);
    if (PLAY_CDN_SCRIPT.test(source) || INLINE_CONFIG.test(source)) {
      problems.push(`${page}: runtime Tailwind remains`);
    }
    const links = [...source.matchAll(LINK_PATTERN)];
    if (links.length > 1) problems.push(`${page}: multiple generated stylesheet links`);
    const link = links[0];
    if (!link) continue;
    linkedPages.add(page);
    if (!expectedPages.has(page)) problems.push(`${page}: link is absent from manifest`);
    if (link[1] !== stylesheetHref(file)) problems.push(`${page}: stylesheet href drifted`);
  }

  for (const [page, config] of Object.entries(manifest)) {
    const file = join(DOCS, page);
    if (!linkedPages.has(page)) problems.push(`${page}: generated stylesheet link missing`);
    const output = join(OUTPUT_DIR, outputName(page));
    let current = null;
    try { current = readFileSync(output, 'utf8'); } catch {}
    const expected = await compilePage(file, config);
    if (current !== expected) problems.push(`${page}: generated CSS is stale or missing`);
  }

  let actualOutputs = [];
  try {
    actualOutputs = readdirSync(OUTPUT_DIR).filter((name) => name.endsWith('.css'));
  } catch {}
  for (const output of actualOutputs) {
    if (!expectedOutputs.has(output)) problems.push(`${output}: orphaned generated stylesheet`);
  }
  for (const output of expectedOutputs) {
    if (!actualOutputs.includes(output)) problems.push(`${output}: generated stylesheet missing`);
  }

  if (problems.length > 0) {
    for (const problem of problems) console.error(problem);
    process.exitCode = 1;
  } else {
    console.log(`Verified ${expectedPages.size} page-specific Tailwind stylesheets`);
  }
}

const mode = process.argv[2];
if (mode === '--write') await writeBuild();
else if (mode === '--check') await checkBuild();
else throw new Error('Usage: node scripts/docs-tailwind.mjs --write|--check');
