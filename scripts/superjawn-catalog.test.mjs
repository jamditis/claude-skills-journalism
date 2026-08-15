import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const GUARDED_PATHS = [
  'README.md',
  'docs/index.html',
  'docs/superjawn/index.html',
  'superjawn/README.md',
  'superjawn/CREDITS.md',
];

function read(path) {
  return readFileSync(join(ROOT, path), 'utf8');
}

test('current Superjawn catalog copy does not present 1.0.0 as the current release', () => {
  for (const path of GUARDED_PATHS.slice(0, -1)) {
    assert.doesNotMatch(read(path), /v1\.0\.0 ships(?: all 14| with)/u, path);
  }
  assert.doesNotMatch(read('superjawn/CREDITS.md'), /\*\*v1\.0\.0 \(current/u);
  assert.doesNotMatch(read('superjawn/README.md'), /^## Coexistence with upstream$/mu);
  assert.doesNotMatch(
    read('docs/superjawn/index.html'),
    /Keep both .* installed during rollout|Skills not yet ported|Upstream disabled at v1\.0\.0 after/u,
  );
});

test('skill-lint CI runs when any guarded Superjawn catalog file changes', () => {
  const workflow = read('.github/workflows/skill-lint.yml');
  for (const path of GUARDED_PATHS) {
    assert.match(workflow, new RegExp(`      - '${path.replaceAll('.', '\\.')}'`, 'u'), path);
  }
});
