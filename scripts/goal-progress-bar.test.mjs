import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const SCRIPT = join(
  ROOT,
  'project-templates-toolkit',
  'skills',
  'goal-progress-bar',
  'scripts',
  'progress.py',
);
const PYTHON = spawnSync('python3', ['--version'], { encoding: 'utf8' });
const SKIP = PYTHON.error || PYTHON.status !== 0 ? 'python3 is not available' : false;

function withTracker(items, run) {
  const dir = mkdtempSync(join(tmpdir(), 'goal-progress-bar-'));
  const tracker = join(dir, 'tracker.json');
  try {
    writeFileSync(tracker, JSON.stringify(items));
    return run(tracker);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

function render(args) {
  return spawnSync('python3', [SCRIPT, ...args], { encoding: 'utf8' });
}

test('renders a normal weighted tracker', { skip: SKIP }, () => {
  withTracker(
    [
      ['Research', 1, 1],
      ['Build', 1, 0.5],
      ['Release proof', 2, 0],
    ],
    (tracker) => {
      const result = render([tracker, 'Site release']);
      assert.equal(result.status, 0, result.stderr);
      assert.match(result.stdout, /^Site release: \[#{11}-{19}\] 37%/u);
      assert.match(result.stdout, /- Research: done/u);
      assert.match(result.stdout, /- Build: in progress \(50%\)/u);
      assert.match(result.stdout, /- Release proof: not started/u);
    },
  );
});

test('renders an empty tracker as zero percent', { skip: SKIP }, () => {
  withTracker([], (tracker) => {
    const result = render([tracker, 'Empty tracker']);
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /^Empty tracker: \[-{30}\] 0%/u);
    assert.match(result.stdout, /No progress rows\./u);
    assert.doesNotMatch(result.stderr, /ZeroDivisionError/u);
  });
});

test('prints usage and exits 2 for a wrong argument count', { skip: SKIP }, () => {
  const result = render([]);
  assert.equal(result.status, 2);
  assert.equal(result.stdout, '');
  assert.match(result.stderr, /^usage: progress\.py /u);
  assert.doesNotMatch(result.stderr, /IndexError/u);
});

test('weights rows and rounds down until completion', { skip: SKIP }, () => {
  withTracker(
    [
      ['Small task', 1, 1],
      ['Large task', 2, 0.5],
    ],
    (tracker) => {
      const result = render([tracker, 'Weighted goal']);
      assert.equal(result.status, 0, result.stderr);
      assert.match(result.stdout, /^Weighted goal: \[#{20}-{10}\] 66%/u);
    },
  );
});

test('does not undercount an exact decimal boundary', { skip: SKIP }, () => {
  withTracker([['Task', 1, 0.58]], (tracker) => {
    const result = render([tracker, 'Decimal goal']);
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /^Decimal goal: \[#{17}-{13}\] 58%/u);
    assert.match(result.stdout, /- Task: in progress \(58%\)/u);
  });
});
