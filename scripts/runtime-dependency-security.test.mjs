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

  function posixClassMatches(name, character) {
    if (character === undefined) return false;
    const code = character.codePointAt(0);
    const classes = {
      alnum: /[A-Za-z0-9]/u,
      alpha: /[A-Za-z]/u,
      blank: /[\t ]/u,
      digit: /[0-9]/u,
      lower: /[a-z]/u,
      space: /\s/u,
      upper: /[A-Z]/u,
      xdigit: /[A-Fa-f0-9]/u,
    };
    if (classes[name]) return classes[name].test(character);
    if (name === 'cntrl') return code < 32 || code === 127;
    if (name === 'graph') return code >= 33 && code <= 126;
    if (name === 'print') return code >= 32 && code <= 126;
    if (name === 'punct') return code >= 33 && code <= 126 && !/[A-Za-z0-9]/u.test(character);
    return false;
  }

  function bracketMatch(start, character) {
    let cursor = start + 1;
    let negated = false;
    if (pattern[cursor] === '!' || pattern[cursor] === '^') {
      negated = true;
      cursor += 1;
    }
    const bodyStart = cursor;
    if (pattern[cursor] === ']') cursor += 1;

    let end = -1;
    while (cursor < pattern.length) {
      if (pattern.startsWith('[:', cursor)) {
        const posixEnd = pattern.indexOf(':]', cursor + 2);
        if (posixEnd !== -1) {
          cursor = posixEnd + 2;
          continue;
        }
      }
      if (pattern[cursor] === ']') {
        end = cursor;
        break;
      }
      cursor += 1;
    }
    if (end === -1) return null;

    let included = false;
    for (let index = bodyStart; index < end;) {
      if (pattern.startsWith('[:', index)) {
        const posixEnd = pattern.indexOf(':]', index + 2);
        if (posixEnd !== -1 && posixEnd < end) {
          included ||= posixClassMatches(pattern.slice(index + 2, posixEnd), character);
          index = posixEnd + 2;
          continue;
        }
      }
      if (index + 2 < end && pattern[index + 1] === '-') {
        included ||= character >= pattern[index] && character <= pattern[index + 2];
        index += 3;
      } else {
        included ||= character === pattern[index];
        index += 1;
      }
    }
    return { end, matches: negated ? !included : included };
  }

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
      const bracket = bracketMatch(patternIndex, value[valueIndex]);
      if (!bracket) {
        result = value[valueIndex] === '[' && match(patternIndex + 1, valueIndex + 1);
      } else {
        result = valueIndex < value.length
          && value[valueIndex] !== '/'
          && bracket.matches
          && match(bracket.end + 1, valueIndex + 1);
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

function shellTokens(input) {
  const tokens = [];
  let text = '';
  let pattern = '';
  let raw = '';
  let quote = null;
  let started = false;

  function append(character, active, source = character) {
    text += character;
    pattern += !active && GLOB_META.has(character) ? `\\${character}` : character;
    raw += source;
    started = true;
  }

  function reset() {
    text = '';
    pattern = '';
    raw = '';
    started = false;
  }

  function finish() {
    if (started) tokens.push({ type: 'word', text, pattern, raw });
    reset();
  }

  for (let index = 0; index < input.length; index += 1) {
    const character = input[index];
    if (quote) {
      if (character === quote) {
        raw += character;
        quote = null;
        started = true;
      } else if (character === '\\' && quote === '"' && index + 1 < input.length) {
        append(input[index + 1], false, character + input[index + 1]);
        index += 1;
      } else {
        append(character, false);
      }
    } else if (character === '"' || character === "'") {
      quote = character;
      raw += character;
      started = true;
    } else if (character === '\\' && index + 1 < input.length) {
      append(input[index + 1], false, character + input[index + 1]);
      index += 1;
    } else if (/\s/u.test(character)) {
      finish();
    } else if (character === '>') {
      let fileDescriptor = '';
      if (started && /^\d+$/u.test(text)) {
        fileDescriptor = text;
        reset();
      } else {
        finish();
      }
      let operator = '>';
      if (input[index + 1] === '>') {
        operator = '>>';
        index += 1;
      }
      tokens.push({ type: 'operator', text: fileDescriptor + operator, raw: fileDescriptor + operator });
    } else if (character === '|' || character === ';' || character === '&') {
      finish();
      let operator = character;
      if (input[index + 1] === character && character !== ';') {
        operator += character;
        index += 1;
      }
      tokens.push({ type: 'operator', text: operator, raw: operator });
    } else {
      append(character, true);
    }
  }
  finish();
  return tokens;
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
  for (const line of flattened.split(/\r?\n/u)) {
    const tokens = shellTokens(line);
    for (let start = 0; start < tokens.length; start += 1) {
      if (tokens[start].type !== 'word' || posix.basename(tokens[start].text) !== 'sha256sum') {
        continue;
      }

      const inputs = [];
      const outputs = [];
      let index = start + 1;

      while (index < tokens.length) {
        const token = tokens[index];
        if (token.type === 'operator' && ['|', ';', '&&', '||'].includes(token.text)) break;
        if (token.type === 'operator' && />/u.test(token.text)) {
          const target = tokens[index + 1];
          if (/^(?:1)?>>?$/u.test(token.text) && target?.type === 'word') {
            outputs.push({ label: `${token.text.replace(/^1/u, '')} ${target.raw}`, target });
          }
          index += 2;
          continue;
        }
        if (token.type === 'word') inputs.push(token);
        index += 1;
      }

      if (tokens[index]?.text === '|') {
        const tee = tokens[index + 1];
        if (tee?.type === 'word' && posix.basename(tee.text) === 'tee') {
          for (let cursor = index + 2; cursor < tokens.length; cursor += 1) {
            const target = tokens[cursor];
            if (target.type === 'operator') break;
            if (!target.text.startsWith('-')) {
              outputs.push({ label: `| tee ${target.raw}`, target });
            }
          }
        }
      }

      const inputLabel = inputs.map((word) => word.raw).join(' ');
      for (const { label, target } of outputs) {
        const output = posix.normalize(target.text);
        if (posix.basename(output) !== 'SHA256SUMS') continue;
        const includesOutput = inputs.some((word) => {
          if (word.text.startsWith('-')) return false;
          return expandBraces(posix.normalize(word.pattern)).some((pattern) =>
            hasActiveGlob(pattern) && globMatches(pattern, output));
        });
        if (includesOutput) violations.push(`${inputLabel} ${label}`);
      }
    }
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
  const zeroBuildReferences = readdirSync(
    join(ROOT, 'dev-toolkit/skills/zero-build-frontend/references'),
    { withFileTypes: true },
  )
    .filter((entry) => entry.isFile() && extname(entry.name) === '.md')
    .map((entry) => `dev-toolkit/skills/zero-build-frontend/references/${entry.name}`)
    .sort();
  const audited = [
    'dev-toolkit/skills/accessibility-compliance/SKILL.md',
    'dev-toolkit/skills/mobile-debugging/SKILL.md',
    'dev-toolkit/skills/zero-build-frontend/SKILL.md',
    ...zeroBuildReferences,
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
  const zeroBuild = [
    'dev-toolkit/skills/zero-build-frontend/SKILL.md',
    'dev-toolkit/skills/zero-build-frontend/references/dependency-assets.md',
  ].map((file) => readFileSync(join(ROOT, file), 'utf8')).join('\n');

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
    selfIncludingChecksumGlobs('sha256sum "$dir"/* > "$dir"/SHA256SUMS'),
    ['"$dir"/* > "$dir"/SHA256SUMS'],
  );
  assert.deepEqual(
    selfIncludingChecksumGlobs(
      'sha256sum public/assets/* 2>/dev/null > public/assets/SHA256SUMS',
    ),
    ['public/assets/* > public/assets/SHA256SUMS'],
  );
  assert.deepEqual(
    selfIncludingChecksumGlobs(
      'sha256sum public/assets/[[:upper:]]* > public/assets/SHA256SUMS',
    ),
    ['public/assets/[[:upper:]]* > public/assets/SHA256SUMS'],
  );
  assert.deepEqual(
    selfIncludingChecksumGlobs(
      'sha256sum public/assets/* | tee public/assets/SHA256SUMS',
    ),
    ['public/assets/* | tee public/assets/SHA256SUMS'],
  );
  assert.deepEqual(
    selfIncludingChecksumGlobs(
      'sha256sum public/assets/*.js > public/assets/JS-SHA; sha256sum public/assets/* > public/assets/SHA256SUMS',
    ),
    ['public/assets/* > public/assets/SHA256SUMS'],
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
