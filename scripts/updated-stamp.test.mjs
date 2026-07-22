import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import {
  REPO_ROOT, formatAbsolute, collectEntries, slugFromHref,
  stampIndex, stampSkillPage, hasScriptTag, hasStyleLink,
  ensureScriptTag, ensureStyleLink, stampReadme, run,
} from './updated-stamp.mjs';

const ISO = '2026-07-07T09:17:25-04:00';

function fixtureRepo(files) {
  const root = mkdtempSync(join(tmpdir(), 'updated-stamp-'));
  for (const [path, body] of Object.entries(files)) {
    mkdirSync(join(root, path, '..'), { recursive: true });
    writeFileSync(join(root, path), body);
  }
  return root;
}

const skill = '---\nname: x\n---\n';
const plugin = (name) => JSON.stringify({ name, version: '1.0.0' });
const dates = (iso) => () => iso;

/** A fixture with real git history, so run() can date paths the way CI does. */
function committedRepo(files) {
  const root = fixtureRepo(files);
  const git = (...args) => execFileSync('git', args, { cwd: root, stdio: 'ignore' });
  git('init', '-q');
  git('config', 'user.email', 'test@example.com');
  git('config', 'user.name', 'test');
  git('add', '-A');
  git('commit', '-qm', 'fixture');
  return root;
}

const page = (body) => `<html><head></head><body>${body}</body></html>`;
const siteFiles = (skillPage) => ({
  'journalism-core/skills/foia-requests/SKILL.md': skill,
  'docs/index.html': page('<a class="skill-card" href="foia-requests/"><h3>FOIA</h3></a>'),
  'docs/foia-requests/index.html': page(skillPage),
  'README.md': '| Skill | Description |\n|-------|-------------|\n',
});

test('formatAbsolute reads the commit\'s own calendar day, not the runner\'s', () => {
  assert.equal(formatAbsolute(ISO), 'Jul 7, 2026');
  // Late evening in -04:00 is already the next day in UTC. The stamp should
  // still read as the day the author committed, on any machine.
  assert.equal(formatAbsolute('2026-07-15T22:09:17-04:00'), 'Jul 15, 2026');
  assert.equal(formatAbsolute('2026-01-02T00:00:00Z'), 'Jan 2, 2026');
  assert.throws(() => formatAbsolute('last tuesday'), /not an ISO timestamp/);
});

test('collectEntries finds skills and plugins and dates them from their own path', () => {
  const root = fixtureRepo({
    'journalism-core/.claude-plugin/plugin.json': plugin('journalism-core'),
    'journalism-core/skills/foia-requests/SKILL.md': skill,
  });
  const seen = [];
  const entries = collectEntries({
    repoRoot: root,
    dates: (path) => { seen.push(path); return ISO; },
  });
  rmSync(root, { recursive: true, force: true });

  assert.deepEqual(entries.map((e) => e.slug), ['foia-requests', 'journalism-core']);
  assert.equal(entries.find((e) => e.slug === 'journalism-core').type, 'plugin');
  assert.equal(entries.find((e) => e.slug === 'foia-requests').type, 'skill');
  assert.deepEqual(seen.sort(), ['journalism-core', 'journalism-core/skills/foia-requests']);
});

test('a plugin whose root is also a skill is one entry, not two', () => {
  const root = fixtureRepo({
    'okf-wiki/.claude-plugin/plugin.json': plugin('okf-wiki'),
    'okf-wiki/SKILL.md': skill,
  });
  const entries = collectEntries({ repoRoot: root, dates: dates(ISO) });
  rmSync(root, { recursive: true, force: true });

  assert.equal(entries.length, 1);
  assert.equal(entries[0].type, 'plugin');
  assert.equal(entries[0].version, '1.0.0');
});

test('two skills with the same name stop the run instead of stamping each other', () => {
  const root = fixtureRepo({
    'a/skills/web-scraping/SKILL.md': skill,
    'b/skills/web-scraping/SKILL.md': skill,
  });
  assert.throws(
    () => collectEntries({ repoRoot: root, dates: dates(ISO) }),
    /duplicate slug "web-scraping"/,
  );
  rmSync(root, { recursive: true, force: true });
});

test('a slug that cannot address a stamp stops the run', () => {
  const root = fixtureRepo({ 'weird/.claude-plugin/plugin.json': plugin('bad"name') });
  assert.throws(
    () => collectEntries({ repoRoot: root, dates: dates(ISO) }),
    /unusable slug "bad"name"/,
  );
  rmSync(root, { recursive: true, force: true });
});

test('a slug from a directory name is held to the same shape', () => {
  const root = fixtureRepo({ 'a/skills/Not Kebab/SKILL.md': skill });
  assert.throws(
    () => collectEntries({ repoRoot: root, dates: dates(ISO) }),
    /unusable slug "Not Kebab"/,
  );
  rmSync(root, { recursive: true, force: true });
});

test('a date git could not have produced stops the run', () => {
  const root = fixtureRepo({ 'a/skills/foia-requests/SKILL.md': skill });
  assert.throws(
    () => collectEntries({ repoRoot: root, dates: dates('2026-07-07T09:17:25-04:00"><script>') }),
    /unusable date/,
  );
  rmSync(root, { recursive: true, force: true });
});

test('a path with no git history is dateless, not a failure', () => {
  const root = fixtureRepo({ 'a/skills/foia-requests/SKILL.md': skill });
  const entries = collectEntries({ repoRoot: root, dates: () => null });
  rmSync(root, { recursive: true, force: true });
  assert.equal(entries[0].updated, null);
});

test('docs/ is never a date source, because stamping it would loop forever', () => {
  const root = fixtureRepo({ 'docs/foia-requests/SKILL.md': skill });
  const entries = collectEntries({ repoRoot: root, dates: dates(ISO) });
  rmSync(root, { recursive: true, force: true });
  assert.deepEqual(entries, []);
});

test('slugFromHref reads identity off the link a card already has', () => {
  assert.equal(slugFromHref('foia-requests/'), 'foia-requests');
  assert.equal(
    slugFromHref('https://github.com/jamditis/claude-skills-journalism/tree/master/journalism-core'),
    'journalism-core',
  );
  assert.equal(slugFromHref('#skills'), null);
  assert.equal(slugFromHref('https://example.com/'), null);
});

const entryFor = (slug) => ({ slug, path: `p/${slug}`, type: 'skill', updated: ISO });

test('stampIndex adds one tape per card and stamping twice changes nothing', () => {
  const html = [
    '<div>',
    '    <a href="foia-requests/" class="skill-card p-6">',
    '        <h3>FOIA</h3>',
    '    </a>',
    '</div>',
  ].join('\n');

  const once = stampIndex(html, [entryFor('foia-requests')]);
  assert.match(once, /data-updated-at="2026-07-07T09:17:25-04:00"/);
  assert.match(once, /<time datetime="[^"]+">Jul 7, 2026<\/time>/);
  assert.equal((once.match(/data-updated-at=/g) || []).length, 1);
  assert.ok(once.indexOf('updated-tape') < once.indexOf('</a>'), 'tape belongs inside the card');

  const twice = stampIndex(once, [entryFor('foia-requests')]);
  assert.equal(twice, once);
});

test('stampIndex refreshes a stale tape rather than stacking a second one', () => {
  const html = '<a href="foia-requests/" class="skill-card">\n    <h3>FOIA</h3>\n</a>';
  const old = stampIndex(html, [{ ...entryFor('foia-requests'), updated: '2020-01-02T00:00:00Z' }]);
  const fresh = stampIndex(old, [entryFor('foia-requests')]);

  assert.equal((fresh.match(/data-updated-at=/g) || []).length, 1);
  assert.ok(!fresh.includes('2020'));
  assert.match(fresh, /Jul 7, 2026/);
});

test('stampIndex leaves cards that are not skills alone and reports them', () => {
  const html = '<a href="workflows/" class="skill-card">\n    <h3>Guide</h3>\n</a>';
  const skipped = [];
  const out = stampIndex(html, [entryFor('foia-requests')], { onSkip: (s) => skipped.push(s.slug) });

  assert.equal(out, html);
  assert.deepEqual(skipped, ['workflows']);
});

test('stampSkillPage converges on a page whose </h1> does not end a line', () => {
  // Not hypothetical: a page saved without that line break used to gain one
  // newline per pass, so CI committed a fresh diff on the next push.
  const html = '<body><h1>FOIA</h1></body>';
  const once = stampSkillPage(html, entryFor('foia-requests'));
  assert.equal(stampSkillPage(once, entryFor('foia-requests')), once);
});

test('stampIndex converges on a card that sits on one line', () => {
  const html = '<a class="skill-card" href="foia-requests/"><h3>FOIA</h3></a>';
  const once = stampIndex(html, [entryFor('foia-requests')]);
  assert.equal(stampIndex(once, [entryFor('foia-requests')]), once);
});

test('a directory carrying pathspec magic does not hijack the date', {
  skip: process.platform === 'win32' && 'NTFS does not allow colons in file names',
}, () => {
  // ":(exclude)x/evil/SKILL.md" has a clean slug, so the slug check cannot see
  // it. Without --literal-pathspecs git reads the parent as "everything else"
  // and the skill takes the repo's newest date.
  const root = committedRepo({
    ':(exclude)x/evil/SKILL.md': skill,
    'a/skills/plain/SKILL.md': skill,
  });
  execFileSync('git', ['commit', '-q', '--allow-empty', '-m', 'later, unrelated'], { cwd: root, stdio: 'ignore' });
  const entries = collectEntries({ repoRoot: root });
  rmSync(root, { recursive: true, force: true });

  const evil = entries.find((e) => e.slug === 'evil');
  const plain = entries.find((e) => e.slug === 'plain');
  assert.equal(evil.updated, plain.updated, 'both date from the one commit that added them');
});

test('a symlinked parent directory is refused too, not just a symlinked page', () => {
  // The half-fix this replaces checked only the leaf. docs/zzz -> foia-requests
  // reaches the same victim page without docs/zzz/index.html being a link.
  const root = committedRepo(siteFiles('<h1>FOIA</h1>'));
  symlinkSync('foia-requests', join(root, 'docs/zzz'));
  mkdirSync(join(root, 'zzz'), { recursive: true });
  writeFileSync(join(root, 'zzz/SKILL.md'), skill);
  execFileSync('git', ['add', '-A'], { cwd: root, stdio: 'ignore' });
  execFileSync('git', ['commit', '-qm', 'add zzz'], { cwd: root, stdio: 'ignore' });

  const result = run({ repoRoot: root, quiet: true, log: () => {} });
  const victim = readFileSync(join(root, 'docs/foia-requests/index.html'), 'utf8');
  rmSync(root, { recursive: true, force: true });

  assert.deepEqual(result.notFiles, ['docs/zzz/index.html']);
  assert.ok(!victim.includes('data-updated-slug="zzz"'), 'zzz did not write through the link');
});

test('a symlinked stamp destination is refused, not written through', () => {
  const root = committedRepo(siteFiles('<h1>FOIA</h1>'));
  mkdirSync(join(root, 'docs/zzz'), { recursive: true });
  symlinkSync('../foia-requests/index.html', join(root, 'docs/zzz/index.html'));
  mkdirSync(join(root, 'zzz'), { recursive: true });
  writeFileSync(join(root, 'zzz/SKILL.md'), skill);
  execFileSync('git', ['add', '-A'], { cwd: root, stdio: 'ignore' });
  execFileSync('git', ['commit', '-qm', 'add zzz'], { cwd: root, stdio: 'ignore' });

  const result = run({ repoRoot: root, quiet: true, log: () => {} });
  const victim = readFileSync(join(root, 'docs/foia-requests/index.html'), 'utf8');
  rmSync(root, { recursive: true, force: true });

  assert.deepEqual(result.notFiles, ['docs/zzz/index.html']);
  assert.match(result.problems.join('\n'), /docs\/zzz\/index\.html does not resolve to a regular file/);
  assert.match(victim, /data-updated-slug="foia-requests"/, 'the victim page kept its own slug');
  assert.ok(!victim.includes('data-updated-slug="zzz"'), 'zzz did not write through the link');
});

test('a row the tool declines to reshape is reported, not silently left', () => {
  // Refusing to pop a cell that is not ours is what protects the text, but a
  // refusal nobody hears is the same silent failure in a different place.
  const md = [
    '| Skill | Description | Updated |',
    '|---|---|---|',
    '| [foia-requests](./p/foia-requests/) | Records | TBD |',
  ].join('\n');
  const seen = [];
  const out = stampReadme(md, [entryFor('foia-requests')], { onUnstamped: (r) => seen.push(r) });

  assert.equal(out, md, 'the hand-typed cell is left exactly as written');
  assert.equal(seen.length, 1);
  assert.match(seen[0], /TBD/);
});

test('stampReadme keeps a stray-pipe row intact on the second pass', () => {
  // A table holding a stray-pipe row never gets the column, so there is no
  // second-pass state in which that row could be mistaken for a stamped one.
  const md = [
    '| Skill | Description |',
    '|-------|-------------|',
    '| [foia-requests](./p/foia-requests/) | Records |',
    '| [web-scraping](./p/web-scraping/) | Uses a | pipe |',
  ].join('\n');
  const entries = [entryFor('foia-requests'), entryFor('web-scraping')];

  const once = stampReadme(md, entries);
  const twice = stampReadme(once, entries);
  assert.equal(twice, once, 'second pass changes nothing');
  assert.ok(twice.includes('| Uses a | pipe |'), 'the row kept its text');
});

test('a tape survives having its attributes reordered', () => {
  // Attribute order is not meaningful in HTML. Matching only the exact string
  // this tool emits would leave the old tape in place and append a second one.
  const reordered = '<h1>x</h1>\n<p data-updated-slug="foia-requests" '
    + 'data-updated-at="2020-01-01T00:00:00Z" class="mt-5 updated-tape">Updated old</p>\n';
  const out = stampSkillPage(reordered, entryFor('foia-requests'));

  assert.equal((out.match(/data-updated-at=/g) || []).length, 1, 'one tape, not two');
  assert.ok(!out.includes('2020-01-01'), 'the stale date is gone');
});

test('stampIndex does not read data-href as the card link', () => {
  // \bhref= matches inside data-href, because \b sits between "-" and "h".
  // The card would take its slug from an attribute that is not its link.
  const html = '<a class="skill-card" data-href="foia-requests/" href="about/">x</a>';
  const out = stampIndex(html, [entryFor('foia-requests')], { onSkip: () => {} });

  assert.ok(!out.includes('data-updated-slug'), 'no stamp from the decoy attribute');
});

test('stampIndex does not treat a quoted class= in another attribute as a card', () => {
  // A class list is a list, not a substring of the tag text. Scanning the whole
  // tag with [^>]* reads the inside of a quoted value as though it were markup.
  const html = '<a title="class=\'skill-card\'" href="foia-requests/">not a card</a>';
  const out = stampIndex(html, [entryFor('foia-requests')], { onSkip: () => {} });

  assert.equal(out, html, 'the decoy is left exactly as it was');
});

test('stampIndex reads a card written with single quotes', () => {
  const html = "<a class='skill-card' href='foia-requests/'><h3>FOIA</h3></a>";
  const out = stampIndex(html, [entryFor('foia-requests')]);
  assert.match(out, /data-updated-slug="foia-requests"/);
});

test('a page that only mentions the asset path still gets a real tag', () => {
  // The old check matched the bare src= substring, so a page showing the tag as
  // an example read as a page that loads it, and the tape never aged.
  const html = '<html><head></head><body><code>src="../updated.js"</code></body></html>';
  const out = ensureScriptTag(html, '../updated.js');
  assert.match(out, /<script defer src="\.\.\/updated\.js"><\/script>/);
  assert.equal(ensureScriptTag(out, '../updated.js'), out, 'still added only once');
});

test('stampIndex ignores anchors that are not cards', () => {
  const html = '<a href="foia-requests/" class="nav-link">FOIA</a>';
  assert.equal(stampIndex(html, [entryFor('foia-requests')]), html);
});

test('stampSkillPage puts the tape under the h1 and is idempotent', () => {
  const html = [
    '<header>',
    '    <h1 class="font-display">Web',
    '        scraping</h1>',
    '    <p>Body</p>',
    '</header>',
  ].join('\n');

  const once = stampSkillPage(html, entryFor('web-scraping'));
  const lines = once.split('\n');
  const tapeLine = lines.findIndex((l) => l.includes('updated-tape'));
  assert.ok(tapeLine > 0);
  assert.ok(lines[tapeLine - 1].includes('</h1>'), 'tape follows the heading');
  assert.match(lines[tapeLine], /^ {8}</, 'tape matches the heading indent');
  assert.equal(stampSkillPage(once, entryFor('web-scraping')), once);
});

test('stampSkillPage reports a page with no h1 instead of guessing a spot', () => {
  assert.equal(stampSkillPage('<header><p>No heading</p></header>', entryFor('x')), null);
});

test('ensureStyleLink adds the tape stylesheet once, in the head', () => {
  const html = '<head>\n    <title>x</title>\n</head>\n<body></body>';
  const once = ensureStyleLink(html, '../updated.css');
  assert.match(once, /<link rel="stylesheet" href="\.\.\/updated\.css">/);
  assert.ok(once.indexOf('updated.css') < once.indexOf('</head>'));
  assert.equal(ensureStyleLink(once, '../updated.css'), once);
});

test('ensureScriptTag adds the upgrade script once', () => {
  const html = '<body>\n    <p>Hi</p>\n</body>';
  const once = ensureScriptTag(html, '../updated.js');
  assert.match(once, /<script defer src="\.\.\/updated\.js"><\/script>/);
  assert.ok(once.indexOf('script') < once.indexOf('</body>'));
  assert.equal(ensureScriptTag(once, '../updated.js'), once);
});

test('stampReadme adds an Updated column and keeps it current', () => {
  const md = [
    '| Skill | Description |',
    '|-------|-------------|',
    '| [foia-requests](./p/foia-requests/) | Records |',
    '',
  ].join('\n');
  const entries = [entryFor('foia-requests')];

  const once = stampReadme(md, entries);
  assert.match(once.split('\n')[0], /\| Updated \|$/);
  assert.match(once.split('\n')[2], /\| Jul 7, 2026 \|$/);

  const twice = stampReadme(once, entries);
  assert.equal(twice, once);

  const moved = stampReadme(once, [{ ...entries[0], updated: '2026-01-02T00:00:00Z' }]);
  assert.match(moved.split('\n')[2], /\| Jan 2, 2026 \|$/);
  assert.equal(moved.split('\n')[2].split('|').length, once.split('\n')[2].split('|').length);
});

test('stampReadme leaves an untracked row blank rather than typing a placeholder', () => {
  const md = [
    '| Skill | Description |',
    '|-------|-------------|',
    '| [foia-requests](./p/foia-requests/) | Records |',
    '| [coming-soon](./p/coming-soon/) | Not built yet |',
  ].join('\n');

  const out = stampReadme(md, [entryFor('foia-requests')]).split('\n');
  assert.match(out[2], /\| Jul 7, 2026 \|$/);
  assert.match(out[3], /\|\s*\|$/);
  assert.ok(!out[3].includes('\u2014'), 'no em dash in a generated cell');
});

test('a healthy site stamps clean and reports no problems', () => {
  const root = committedRepo(siteFiles('<h1>FOIA requests</h1>'));
  const result = run({ repoRoot: root, quiet: true, log: () => {} });

  assert.deepEqual(result.problems, []);
  assert.equal(result.entries.length, 1);
  // Second pass writes nothing, which is what makes the CI commit terminate.
  assert.deepEqual(run({ repoRoot: root, quiet: true, log: () => {} }).changed, []);
  rmSync(root, { recursive: true, force: true });
});

test('a page that could not be stamped is a problem, not a warning', () => {
  const root = committedRepo(siteFiles('<p>No heading here</p>'));
  const result = run({ repoRoot: root, quiet: true, log: () => {} });
  rmSync(root, { recursive: true, force: true });

  // CI commits whatever the stamper leaves behind. A page that silently came
  // back unstamped has to stop that commit, not ride along inside it.
  assert.deepEqual(result.missingH1, ['docs/foia-requests/index.html']);
  assert.equal(result.problems.length, 1);
  assert.match(result.problems[0], /docs\/foia-requests\/index\.html/);
});

test('a card pointing at a non-skill is a note, not a problem', () => {
  const files = siteFiles('<h1>FOIA requests</h1>');
  files['docs/index.html'] = page(
    '<a class="skill-card" href="foia-requests/"><h3>FOIA</h3></a>'
    + '<a class="skill-card" href="workflows/"><h3>Workflows</h3></a>',
  );
  const root = committedRepo(files);
  const result = run({ repoRoot: root, quiet: true, log: () => {} });
  rmSync(root, { recursive: true, force: true });

  assert.deepEqual(result.skipped, ['workflows']);
  assert.deepEqual(result.problems, []);
});

test('stampReadme handles a CRLF file without growing a phantom column', () => {
  // A retained \r used to ride along inside the last cell, so the row split one
  // cell wide and the rebuilt separator came out as |---|---||--------|, which
  // GitHub renders as a broken table.
  const md = '| Skill | Description |\r\n|---|---|\r\n| [foia-requests](./p/foia-requests/) | Records |\r\n';
  const out = stampReadme(md, [entryFor('foia-requests')]);

  assert.equal(out, '| Skill | Description | Updated |\r\n|---|---|--------|\r\n'
    + '| [foia-requests](./p/foia-requests/) | Records | Jul 7, 2026 |\r\n');
  assert.equal(stampReadme(out, [entryFor('foia-requests')]), out);
});

test('stampReadme leaves tables that do not list skills untouched', () => {
  const md = [
    '| Guide | Description |',
    '|-------|-------------|',
    '| [Autonomy](https://skills.amditis.tech/autonomy/) | A guide |',
  ].join('\n');
  assert.equal(stampReadme(md, [entryFor('foia-requests')]), md);
});

test('stampReadme refuses a whole table when any row is ragged, and reports it', () => {
  // The header is shared, so a column cannot be widened for some rows and not
  // others. Skipping the table costs a stamp; reshaping it would cost text.
  const md = [
    '| Skill | Description |',
    '|-------|-------------|',
    '| [foia-requests](./p/foia-requests/) | Records |',
    '| [web-scraping](./p/web-scraping/) | Uses a | pipe |',
  ].join('\n');

  const reported = [];
  const out = stampReadme(md, [entryFor('foia-requests'), entryFor('web-scraping')], {
    onUnstamped: (row) => reported.push(row),
  });

  assert.equal(out, md, 'the table is untouched');
  assert.deepEqual(reported, ['| [web-scraping](./p/web-scraping/) | Uses a | pipe |']);
});

test('stampReadme does not eat a date-like cell in a ragged row on the second pass', () => {
  // The cell that made this necessary: text in a stray-pipe row that happens to
  // look exactly like a stamp. Nothing may distinguish the two by shape, so the
  // table has to be refused before a column is ever added.
  const md = [
    '| Skill | Description |',
    '|-------|-------------|',
    '| [foia-requests](./p/foia-requests/) | Records |',
    '| [web-scraping](./p/web-scraping/) | Released | Jan 2, 2020 |',
  ].join('\n');
  const entries = [entryFor('foia-requests'), entryFor('web-scraping')];

  const once = stampReadme(md, entries);
  const twice = stampReadme(once, entries);
  assert.equal(once, md, 'first pass leaves it alone');
  assert.equal(twice, once, 'and so does the second');
  assert.ok(twice.includes('| Released | Jan 2, 2020 |'), 'the date-like text survives');
});

test('attribute lookup ignores attribute-shaped text inside quoted values', () => {
  assert.equal(
    hasScriptTag(`<script title='example src="../updated.js"'></script>`, '../updated.js'),
    false,
  );

  const html = `<a title="x class='skill-card' href='foia-requests/'">not a card</a>`;
  assert.equal(stampIndex(html, [entryFor('foia-requests')]), html);
});

test('top-level stamp destinations are refused when they are symlinks', () => {
  const root = committedRepo(siteFiles('<h1>FOIA requests</h1>'));
  const outside = mkdtempSync(join(tmpdir(), 'updated-stamp-victim-'));
  const victimIndex = join(outside, 'index.html');
  const victimReadme = join(outside, 'README.md');
  const indexBefore = page('<h1>Unrelated index</h1>');
  const readmeBefore = '# Unrelated README\n';
  writeFileSync(victimIndex, indexBefore);
  writeFileSync(victimReadme, readmeBefore);
  rmSync(join(root, 'docs/index.html'));
  rmSync(join(root, 'README.md'));
  symlinkSync(victimIndex, join(root, 'docs/index.html'));
  symlinkSync(victimReadme, join(root, 'README.md'));

  const result = run({ repoRoot: root, quiet: true, log: () => {} });

  assert.deepEqual(readFileSync(victimIndex, 'utf8'), indexBefore);
  assert.deepEqual(readFileSync(victimReadme, 'utf8'), readmeBefore);
  assert.ok(result.notFiles.includes('docs/index.html'));
  assert.ok(result.notFiles.includes('README.md'));
  assert.match(result.problems.join('\n'), /docs\/index\.html/);
  assert.match(result.problems.join('\n'), /README\.md/);
  rmSync(root, { recursive: true, force: true });
  rmSync(outside, { recursive: true, force: true });
});

test('stylesheet detection treats rel as a whitespace-separated token list', () => {
  assert.equal(hasStyleLink('<link rel="not-stylesheet" href="u.css">', 'u.css'), false);
  assert.equal(hasStyleLink('<link rel="alternate-stylesheet" href="u.css">', 'u.css'), false);
  assert.equal(hasStyleLink('<link rel="alternate stylesheet" href="u.css">', 'u.css'), true);
});

test('stampSkillPage replaces an uppercase owned tape instead of stacking it', () => {
  const html = '<h1>x</h1>\n<P DATA-UPDATED-SLUG="foia-requests">Updated Jan 1, 2020</P>\n';
  const out = stampSkillPage(html, entryFor('foia-requests'));

  assert.equal((out.match(/data-updated-slug=/gi) || []).length, 1);
  assert.ok(!out.includes('Jan 1, 2020'));
  assert.match(out, /Jul 7, 2026/);
});

test('stampReadme supports GFM tables without outer pipes', () => {
  const md = [
    'Skill | Description',
    '--- | ---',
    '[foia-requests](./p/foia-requests/) | Records',
  ].join('\n');
  const once = stampReadme(md, [entryFor('foia-requests')]);

  assert.equal(once, [
    'Skill | Description | Updated',
    '---|---|--------',
    '[foia-requests](./p/foia-requests/) | Records | Jul 7, 2026',
  ].join('\n'));
  assert.equal(stampReadme(once, [entryFor('foia-requests')]), once);
});

test('stampReadme ignores whitespace after a closing table pipe', () => {
  const md = [
    '| Skill | Description |   ',
    '|---|---|   ',
    '| [foia-requests](./p/foia-requests/) | Records |   ',
  ].join('\n');
  const once = stampReadme(md, [entryFor('foia-requests')]);

  assert.equal(once, [
    '| Skill | Description | Updated |',
    '|---|---|--------|',
    '| [foia-requests](./p/foia-requests/) | Records | Jul 7, 2026 |',
  ].join('\n'));
  assert.equal(stampReadme(once, [entryFor('foia-requests')]), once);
});

test('run reports a dated entry that reaches no public stamp surface', () => {
  const files = siteFiles('<h1>FOIA requests</h1>');
  files['hidden/skills/unadvertised/SKILL.md'] = skill;
  const root = committedRepo(files);
  const result = run({ repoRoot: root, quiet: true, log: () => {} });
  rmSync(root, { recursive: true, force: true });

  assert.deepEqual(result.uncovered.map((entry) => entry.slug), ['unadvertised']);
  assert.match(result.problems.join('\n'), /\(unadvertised\) reaches no public stamp surface/);
});

test('stamp workflow regenerates from latest master before each push attempt', () => {
  const workflow = readFileSync(join(REPO_ROOT, '.github/workflows/updated-stamp.yml'), 'utf8');
  const retry = workflow.indexOf('for attempt in 1 2 3');
  const reset = workflow.indexOf('git reset --hard origin/master', retry);
  const regenerate = workflow.indexOf('node scripts/updated-stamp.mjs', reset);
  const push = workflow.indexOf('git push origin HEAD:master', regenerate);

  assert.ok(retry >= 0, 'workflow retries a raced push');
  assert.ok(reset > retry, 'each attempt starts from the latest remote master');
  assert.ok(regenerate > reset, 'stamps are regenerated after synchronizing');
  assert.ok(push > regenerate, 'only regenerated stamps are pushed');
});

test('slugFromHref resolves a dot-relative local card link', () => {
  assert.equal(slugFromHref('./foia-requests/'), 'foia-requests');
});

test('script detection requires the exact script tag name', () => {
  assert.equal(
    hasScriptTag('<script-loader src="../updated.js"></script-loader>', '../updated.js'),
    false,
  );
});

test('stampIndex handles uppercase anchor tags and closing tags', () => {
  const html = '<A class="skill-card" href="foia-requests/"><h3>FOIA</h3></A>';
  const out = stampIndex(html, [entryFor('foia-requests')]);
  assert.match(out, /data-updated-slug="foia-requests"/);
  assert.ok(out.indexOf('updated-tape') < out.indexOf('</A>'));
});

test('stampSkillPage ignores headings inside inert template content', () => {
  const html = '<template><h1>example</h1></template><header><h1>FOIA</h1></header>';
  const out = stampSkillPage(html, entryFor('foia-requests'));

  assert.ok(out.indexOf('updated-tape') > out.indexOf('<h1>FOIA</h1>'));
  assert.ok(out.indexOf('updated-tape') > out.indexOf('</template>'));
});

test('asset detection ignores tags inside inert template content', () => {
  const html = '<template><link rel="stylesheet" href="updated.css">'
    + '<script src="updated.js"></script></template>';
  assert.equal(hasStyleLink(html, 'updated.css'), false);
  assert.equal(hasScriptTag(html, 'updated.js'), false);
});

test('tokenization ignores comments and raw script text', () => {
  const comment = '<!-- <script src="updated.js"></script> -->';
  const raw = '<script>const example = `<script src="updated.js"></script>`;</script>';
  assert.equal(hasScriptTag(comment, 'updated.js'), false);
  assert.equal(hasScriptTag(raw, 'updated.js'), false);

  const pageWithExamples = `${comment}${raw}<main><h1>Real heading</h1></main>`;
  const out = stampSkillPage(pageWithExamples, entryFor('foia-requests'));
  assert.ok(out.indexOf('updated-tape') > out.indexOf('<h1>Real heading</h1>'));
});
