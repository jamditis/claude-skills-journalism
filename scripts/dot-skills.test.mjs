import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { calculateProgress, createState, transition } = require('../docs/dot-skills/workshop.js');
const root = path.resolve('docs/dot-skills');
const slugs = ['', 'status-cards', 'incident-updates', 'visual-audits', 'source-evidence', 'rough-edges'];
// A connector-only checkout can test the changed files without fabricating old assets.
// Normal repository/CI runs must leave this unset and validate every local link.
const partial = process.env.DOT_SKILLS_PARTIAL_SNAPSHOT === '1';
const legacyPaths = new Set([
  path.join(root, 'downloads/verify-source-evidence-1.0.0-preview.zip'),
  path.join(root, 'downloads/verify-source-evidence/README.md'),
  path.join(root, 'downloads/index.json')
]);

test('pages retain accessible static content, unique anchors, and real local links', () => {
  for (const slug of slugs) {
    const filename = path.join(root, slug, 'index.html');
    const html = fs.readFileSync(filename, 'utf8');
    assert.equal((html.match(/<h1>/g) || []).length, 1, filename);
    assert.match(html, /id="main"/);
    assert.match(html, /class="skip"/);
    assert.match(html, /<html lang="en">/);
    assert.match(html, /<meta name="description" content="[^"]+"/);
    const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
    assert.equal(new Set(ids).size, ids.length, `Duplicate ID in ${filename}`);
    for (const [, value] of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
      if (/^(https?:|\/)/.test(value)) continue;
      const [href, anchor] = value.split('#');
      let target = href ? path.resolve(path.dirname(filename), href) : filename;
      if (partial && (legacyPaths.has(target) || target === path.dirname(root))) continue;
      assert.ok(fs.existsSync(target), `${filename}: missing ${value}`);
      if (fs.statSync(target).isDirectory()) target = path.join(target, 'index.html');
      assert.ok(fs.existsSync(target), `${filename}: missing index for ${value}`);
      if (anchor && target.endsWith('.html')) assert.ok(fs.readFileSync(target, 'utf8').includes(`id="${anchor}"`), `${filename}: missing #${anchor}`);
    }
  }
});

test('all four guides expose readable prompts and complete downloadable playbooks', () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'playbooks/index.json'), 'utf8'));
  assert.equal(manifest.workflows.length, 4);
  assert.equal(manifest.format, 'markdown-workflow-preview');
  for (const entry of manifest.workflows) {
    const bytes = fs.readFileSync(path.join(root, 'playbooks', entry.file));
    assert.equal(bytes.length, entry.bytes, `${entry.name}: byte count`);
    assert.equal(createHash('sha256').update(bytes).digest('hex'), entry.sha256, `${entry.name}: integrity`);
    const text = bytes.toString('utf8');
    assert.match(text, /Version: 0\.2\.0/);
    assert.match(text, /## Requirements and limits/);
    assert.ok(text.length > 2000, `${entry.name}: missing procedure`);
    const html = fs.readFileSync(path.join(root, entry.name, 'index.html'), 'utf8');
    assert.ok(html.includes(`href="../playbooks/${entry.file}" download`));
    assert.match(html, /<textarea[^>]+readonly/);
    assert.match(html, /data-copy="[^"]+" data-js-only hidden/);
    assert.doesNotMatch(html, /<div class="downloads"[^>]*><\/div>/);
  }
});

test('scenario progress reflects six equal milestones, not release optimism', () => {
  assert.equal(calculateProgress(createState('starting').rows), 25);
  assert.equal(calculateProgress(createState('merged').rows), 50);
  assert.equal(calculateProgress(createState('blocked').rows), 67);
  assert.equal(calculateProgress(createState('verified').rows), 100);
  assert.equal(createState('blocked').rows[4].blocked, true);
  assert.equal(createState('blocked').rows[1].fraction, 1);
});

test('the bar reserves 100 percent for complete scope and rejects invalid inputs', () => {
  assert.equal(calculateProgress([]), 0);
  assert.equal(calculateProgress([{ weight: 1000, fraction: 1 }, { weight: 1, fraction: 0 }]), 99);
  for (const row of [{ weight: 0, fraction: 0 }, { weight: -1, fraction: 0 }, { weight: Infinity, fraction: 0 }, { weight: 1, fraction: NaN }, { weight: 1, fraction: 1.1 }, { weight: 1, fraction: -.1 }, { weight: 1, fraction: 1, blocked: true }]) assert.throws(() => calculateProgress([row]));
  assert.throws(() => createState('not-a-scenario'));
  assert.throws(() => transition(createState(), { type: 'not-an-action' }));
});

test('unchanged checks advance only successful-check time; failures advance neither clock', () => {
  const initial = createState('blocked');
  const checked = transition(initial, { type: 'check' });
  assert.notEqual(checked.checked, initial.checked);
  assert.equal(checked.changed, initial.changed);
  assert.deepEqual(checked.rows, initial.rows);
  assert.equal(initial.checked, '09:40', 'The previous state must not be mutated');
  const failed = transition(checked, { type: 'failure' });
  assert.equal(failed.checked, checked.checked);
  assert.equal(failed.changed, checked.changed);
  assert.equal(calculateProgress(failed.rows), 67);
  const repeated = transition(failed, { type: 'check' });
  assert.equal(repeated.checked, '09:42');
  assert.equal(repeated.changed, initial.changed);
  assert.equal(calculateProgress(transition(repeated, { type: 'reset' }).rows), 25);
});

function motionHarness(storage, reduced = false) {
  const handlers = {}, classes = new Set(), attributes = {};
  const preference = { matches: reduced, addEventListener: (_, fn) => { handlers.preference = fn; } };
  const motion = { setAttribute: (name, value) => { attributes[name] = value; }, addEventListener: (_, fn) => { handlers.click = fn; } };
  const context = {
    document: { documentElement: { classList: { toggle: (name, on) => on ? classes.add(name) : classes.delete(name) } }, querySelector: selector => selector === '#motion' ? motion : null, querySelectorAll: () => [] },
    window: { matchMedia: () => preference }, localStorage: storage
  };
  vm.runInNewContext(fs.readFileSync(path.join(root, 'workshop.js'), 'utf8'), context);
  return { handlers, classes, attributes, preference, motion };
}

test('motion pause persists; OS reduced motion takes precedence without storage dependency', () => {
  const data = new Map();
  const storage = { getItem: key => data.get(key), setItem: (key, value) => data.set(key, value) };
  const first = motionHarness(storage);
  first.handlers.click();
  assert.ok(first.classes.has('paused'));
  assert.equal(data.get('dot-skills-motion'), 'paused');
  assert.ok(motionHarness(storage).classes.has('paused'));
  const reduced = motionHarness(storage, true);
  assert.equal(reduced.motion.disabled, true);
  assert.equal(reduced.attributes['aria-pressed'], 'true');
  reduced.preference.matches = false;
  reduced.handlers.preference();
  assert.ok(reduced.classes.has('paused'), 'Manual pause survives an OS setting change');
  reduced.handlers.click();
  assert.ok(!reduced.classes.has('paused'));
  reduced.preference.matches = true;
  reduced.handlers.preference();
  assert.ok(reduced.classes.has('paused'));
  const blockedStorage = { getItem() { throw Error('denied'); }, setItem() { throw Error('denied'); } };
  const fallback = motionHarness(blockedStorage);
  fallback.handlers.click();
  assert.ok(fallback.classes.has('paused'));
});

test('demos disclose their boundary and do not perform network actions', () => {
  const js = fs.readFileSync(path.join(root, 'workshop.js'), 'utf8');
  assert.doesNotMatch(js, /\b(?:fetch|XMLHttpRequest|WebSocket|setInterval)\s*\(/);
  for (const slug of ['', 'status-cards']) {
    const html = fs.readFileSync(path.join(root, slug, 'index.html'), 'utf8');
    assert.match(html, /Fictional project · local demo/);
    assert.match(html, /does not connect to Slack/);
    assert.match(html, /aria-valuenow="25"/);
  }
  assert.match(fs.readFileSync(path.join(root, 'style.css'), 'utf8'), /@media\(prefers-reduced-motion:reduce\)/);
});

test('main docs feature still precedes the Codex feature', { skip: partial ? 'Main docs unchanged and unavailable in connector-only snapshot' : false }, () => {
  const home = fs.readFileSync('docs/index.html', 'utf8');
  const dots = home.indexOf('href="dot-skills/"');
  const codex = home.indexOf('The Codex review setup I run.');
  assert.ok(dots >= 0 && codex >= 0 && dots < codex);
});

test('legacy preview assets remain present', { skip: partial ? 'Unchanged binary archive and original documentation not materialized' : false }, () => {
  for (const filename of legacyPaths) assert.ok(fs.statSync(filename).isFile(), filename);
});
