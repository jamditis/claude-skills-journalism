import assert from 'node:assert/strict';
import { existsSync, lstatSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { extname, join, posix, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
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

function globMatches(pattern, value) {
  const memo = new Map();

  function match(patternIndex, valueIndex) {
    const key = `${patternIndex}:${valueIndex}`;
    if (memo.has(key)) return memo.get(key);

    let result;
    if (patternIndex === pattern.length) {
      result = valueIndex === value.length;
    } else if (pattern[patternIndex] === '\\' && patternIndex + 1 < pattern.length) {
      result = value[valueIndex] === pattern[patternIndex + 1]
        && match(patternIndex + 2, valueIndex + 1);
    } else if (
      pattern.startsWith('**/', patternIndex)
      && (patternIndex === 0 || pattern[patternIndex - 1] === '/')
    ) {
      result = match(patternIndex + 3, valueIndex);
      for (let cursor = valueIndex; !result && cursor < value.length; cursor += 1) {
        if (value[cursor] === '/') result = match(patternIndex + 3, cursor + 1);
      }
    } else if (
      pattern.startsWith('**', patternIndex)
      && (patternIndex === 0 || pattern[patternIndex - 1] === '/')
      && patternIndex + 2 === pattern.length
    ) {
      result = match(patternIndex + 2, valueIndex)
        || (valueIndex < value.length && match(patternIndex, valueIndex + 1));
    } else if (pattern[patternIndex] === '*') {
      result = match(patternIndex + 1, valueIndex)
        || (valueIndex < value.length
          && value[valueIndex] !== '/'
          && match(patternIndex, valueIndex + 1));
    } else if (pattern[patternIndex] === '?') {
      result = valueIndex < value.length
        && value[valueIndex] !== '/'
        && match(patternIndex + 1, valueIndex + 1);
    } else if (pattern[patternIndex] === '[') {
      const end = pattern.indexOf(']', patternIndex + 1);
      if (end === -1) {
        result = value[valueIndex] === '[' && match(patternIndex + 1, valueIndex + 1);
      } else {
        let body = pattern.slice(patternIndex + 1, end);
        const negated = body.startsWith('!') || body.startsWith('^');
        if (negated) body = body.slice(1);
        let included = false;
        for (let index = 0; index < body.length; index += 1) {
          if (index + 2 < body.length && body[index + 1] === '-') {
            included ||= value[valueIndex] >= body[index] && value[valueIndex] <= body[index + 2];
            index += 2;
          } else {
            included ||= value[valueIndex] === body[index];
          }
        }
        result = valueIndex < value.length
          && value[valueIndex] !== '/'
          && (negated ? !included : included)
          && match(end + 1, valueIndex + 1);
      }
    } else {
      result = value[valueIndex] === pattern[patternIndex]
        && match(patternIndex + 1, valueIndex + 1);
    }

    memo.set(key, result);
    return result;
  }

  return match(0, 0);
}

const GLOB_META = new Set(['*', '?', '[', ']', '{', '}', '\\']);

function shellWords(input) {
  const words = [];
  let text = '';
  let pattern = '';
  let quote = null;
  let started = false;

  function append(character, active) {
    text += character;
    pattern += !active && GLOB_META.has(character) ? `\\${character}` : character;
    started = true;
  }

  function finish() {
    if (started) words.push({ text, pattern });
    text = '';
    pattern = '';
    started = false;
  }

  for (let index = 0; index < input.length; index += 1) {
    const character = input[index];
    if (quote) {
      if (character === quote) {
        quote = null;
        started = true;
      } else if (character === '\\' && quote === '"' && index + 1 < input.length) {
        append(input[index + 1], false);
        index += 1;
      } else {
        append(character, false);
      }
    } else if (character === '"' || character === "'") {
      quote = character;
      started = true;
    } else if (character === '\\' && index + 1 < input.length) {
      append(input[index + 1], false);
      index += 1;
    } else if (/\s/u.test(character)) {
      finish();
    } else {
      append(character, true);
    }
  }
  finish();
  return words;
}

function isEscaped(pattern, index) {
  let backslashes = 0;
  for (let cursor = index - 1; cursor >= 0 && pattern[cursor] === '\\'; cursor -= 1) {
    backslashes += 1;
  }
  return backslashes % 2 === 1;
}

function expandBraces(pattern) {
  let open = -1;
  for (let index = 0; index < pattern.length; index += 1) {
    if (pattern[index] === '{' && !isEscaped(pattern, index)) {
      open = index;
      break;
    }
  }
  if (open === -1) return [pattern];

  let depth = 0;
  let close = -1;
  const commas = [];
  for (let index = open + 1; index < pattern.length; index += 1) {
    if (isEscaped(pattern, index)) continue;
    if (pattern[index] === '{') depth += 1;
    else if (pattern[index] === '}' && depth === 0) {
      close = index;
      break;
    } else if (pattern[index] === '}') depth -= 1;
    else if (pattern[index] === ',' && depth === 0) commas.push(index);
  }
  if (close === -1 || commas.length === 0) return [pattern];

  const parts = [];
  let start = open + 1;
  for (const comma of [...commas, close]) {
    parts.push(pattern.slice(start, comma));
    start = comma + 1;
  }

  return parts.flatMap((part) => expandBraces(
    pattern.slice(0, open) + part + pattern.slice(close + 1),
  ));
}

function hasActiveGlob(pattern) {
  for (let index = 0; index < pattern.length; index += 1) {
    if (pattern[index] === '\\') index += 1;
    else if (pattern[index] === '*' || pattern[index] === '?' || pattern[index] === '[') {
      return true;
    }
  }
  return false;
}

function selfIncludingChecksumGlobs(source) {
  const flattened = source.replace(/\\\r?\n\s*/g, ' ');
  const violations = [];
  const command = /\bsha256sum\b\s+([^>\n]*?)\s*(>>?)\s*((?:"[^"]+"|'[^']+'|[^\s;|&]+))/gu;

  for (const match of flattened.matchAll(command)) {
    const inputs = match[1].trim();
    const redirect = match[2];
    const rawOutput = match[3];
    const output = shellWords(rawOutput)[0]?.text || '';
    if (posix.basename(output) !== 'SHA256SUMS') continue;

    const includesOutput = shellWords(inputs).some((word) => {
      if (word.text.startsWith('-')) return false;
      return expandBraces(posix.normalize(word.pattern)).some((pattern) =>
        hasActiveGlob(pattern) && globMatches(pattern, posix.normalize(output)));
    });
    if (includesOutput) violations.push(`${inputs} ${redirect} ${rawOutput}`);
  }

  return violations;
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

test('local dependency instructions are complete and CSP-compatible', () => {
  const mobile = readFileSync(join(ROOT, 'dev-toolkit/skills/mobile-debugging/SKILL.md'), 'utf8');
  const secureAuth = readFileSync(join(ROOT, 'security-toolkit/skills/secure-auth/SKILL.md'), 'utf8');
  const zeroBuild = readFileSync(join(ROOT, 'dev-toolkit/skills/zero-build-frontend/SKILL.md'), 'utf8');

  assert.match(mobile, /find public\/debug -type f ! -name SHA256SUMS/);

  assert.match(secureAuth, /script-src 'self' 'nonce-/);
  assert.equal(
    [...secureAuth.matchAll(/<script type="module" nonce="\{\{CSP_NONCE\}\}">/g)].length,
    2,
  );

  assert.match(zeroBuild, /@alpinejs\/csp@3\.15\.12/);
  assert.match(zeroBuild, /alpine-csp-3\.15\.12\.min\.js/);
  assert.doesNotMatch(zeroBuild, /node_modules\/alpinejs\/dist\/cdn\.min\.js/);
  assert.match(zeroBuild, /papaparse@5\.5\.4/);
  assert.match(zeroBuild, /papaparse-5\.5\.4\.min\.js/);
});

test('checksum-manifest classifier catches the bug class without flagging narrower globs', () => {
  assert.deepEqual(
    selfIncludingChecksumGlobs('sha256sum public/assets/* > public/assets/SHA256SUMS'),
    ['public/assets/* > public/assets/SHA256SUMS'],
  );
  assert.deepEqual(
    selfIncludingChecksumGlobs('sha256sum public/assets/SHA* > public/assets/SHA256SUMS'),
    ['public/assets/SHA* > public/assets/SHA256SUMS'],
  );
  assert.deepEqual(
    selfIncludingChecksumGlobs('sha256sum public/assets/*.js > public/assets/SHA256SUMS'),
    [],
  );
  assert.deepEqual(
    selfIncludingChecksumGlobs('sha256sum "public/assets"/* > public/assets/SHA256SUMS'),
    ['"public/assets"/* > public/assets/SHA256SUMS'],
  );
  assert.deepEqual(
    selfIncludingChecksumGlobs('sha256sum public/assets/**/* > public/assets/SHA256SUMS'),
    ['public/assets/**/* > public/assets/SHA256SUMS'],
  );
  assert.deepEqual(
    selfIncludingChecksumGlobs('sha256sum public/assets/**/SUMS > public/assets/SHA256SUMS'),
    [],
  );
  assert.deepEqual(
    selfIncludingChecksumGlobs('sha256sum public/assets/* >> public/assets/SHA256SUMS'),
    ['public/assets/* >> public/assets/SHA256SUMS'],
  );
  assert.deepEqual(
    selfIncludingChecksumGlobs('sha256sum public/assets/{*,.*} > public/assets/SHA256SUMS'),
    ['public/assets/{*,.*} > public/assets/SHA256SUMS'],
  );
  assert.deepEqual(
    selfIncludingChecksumGlobs('sha256sum "public/assets/*" > public/assets/SHA256SUMS'),
    [],
  );
  assert.deepEqual(
    selfIncludingChecksumGlobs('sha256sum public/assets/\\* > public/assets/SHA256SUMS'),
    [],
  );
  assert.deepEqual(
    selfIncludingChecksumGlobs('sha256sum public/assets/{*.js,*.css} > public/assets/SHA256SUMS'),
    [],
  );
  assert.deepEqual(
    selfIncludingChecksumGlobs(
      'find public/assets -type f ! -name SHA256SUMS -print0 | xargs -0 sha256sum > public/assets/SHA256SUMS',
    ),
    [],
  );
});

test('checksum manifests are not generated from globs that include themselves', () => {
  const violations = [];
  for (const path of sourceFiles()) {
    for (const command of selfIncludingChecksumGlobs(executableSource(path))) {
      violations.push(`${relative(ROOT, path)}: ${command}`);
    }
  }
  assert.deepEqual(violations, []);
});

test('visual-explainer templates ship the Mermaid module they import', () => {
  const bundle = join(ROOT, 'visual-explainer/templates/vendor/mermaid-11.16.0.mjs');
  const legal = bundle + '.LEGAL.txt';
  const mermaidLicense = join(ROOT, 'visual-explainer/templates/vendor/MERMAID-LICENSE');
  assert.equal(existsSync(bundle), true);
  assert.equal(existsSync(legal), true);
  assert.equal(existsSync(mermaidLicense), true);
  assert.ok(statSync(bundle).size > 100_000);
});

test('CDN version parser distinguishes exact versions from mutable tags', () => {
  assert.equal(packageVersion('https://unpkg.com/pkg@1.2.3/dist/x.js'), '1.2.3');
  assert.equal(packageVersion('https://esm.sh/@scope/pkg@2.3.4'), '2.3.4');
  assert.equal(packageVersion('https://cdnjs.cloudflare.com/ajax/libs/pkg/4.5.6/x.js'), '4.5.6');
  assert.equal(packageVersion('https://cdn.jsdelivr.net/npm/pkg@latest/x.js'), null);
  assert.equal(packageVersion('https://cdn.jsdelivr.net/npm/pkg@4/x.js'), null);
  assert.equal(packageVersion('https://unpkg.com/@scope/pkg/dist/x.js'), null);
});
