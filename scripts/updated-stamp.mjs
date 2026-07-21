// Stamps a "last updated" date onto every skill and plugin surface: the cards
// on docs/index.html, each docs/<slug>/index.html page, and the README tables.
//
// Git history is the source of truth. Nothing here reads a hand-maintained
// date field, so a stamp cannot drift from the thing it describes.
//
// Two rules hold the design together:
//
//   1. Dates come only from source paths (journalism-core/skills/foia-requests,
//      okf-wiki, ...) and never from docs/. If a date were derived from the
//      page it is stamped into, the CI commit that writes the stamp would bump
//      the date, which would trigger another stamp, forever.
//   2. Only the absolute date is written into HTML. "3 days ago" is computed in
//      the browser by docs/updated.js, because a stamped relative age is wrong
//      the day after the build.
//
// Usage:
//   node scripts/updated-stamp.mjs           write stamps
//   node scripts/updated-stamp.mjs --check   exit 1 if any file would change
//   node scripts/updated-stamp.mjs --quiet   only report problems

import { execFileSync } from 'node:child_process';
import { readdirSync, readFileSync, statSync, realpathSync, writeFileSync } from 'node:fs';
import { join, dirname, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
export const REPO_ROOT = join(__dirname, '..');

// Never walked, at any depth.
const SKIP_ANYWHERE = new Set(['.git', 'node_modules', '.pytest_cache']);
// Never walked at the repo root. Anchored there so a nested directory that
// happens to share one of these names is still searched.
const SKIP_AT_ROOT = new Set(['docs', 'plans', 'specs', 'research']);

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// The two shapes every entry has to satisfy. Both are checked once, where an
// entry is built, so no consumer downstream has to defend itself: a slug is
// safe in an HTML attribute, a CSS selector, a URL path, and a README link
// because it cannot be anything else by the time it gets there.
//
// A slug outside this shape is not a case to escape and carry on with. It is
// already broken: it cannot match a card href, cannot be a docs/<slug>/ page
// GitHub Pages serves, and cannot be a plugin name `/plugin install` accepts.
// Escaping it would hide that behind a stamp that quietly matches nothing.
const SLUG_RE = /^[a-z0-9][a-z0-9-]*$/;
// A cell this tool wrote: an absolute date, or blank for an untracked row.
const STAMP_CELL = /^(?:[A-Z][a-z]{2} \d{1,2}, \d{4})?$/;
// git --format=%cI always writes an offset; Z is accepted for hand-built dates.
const ISO_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2}|Z)$/;

/**
 * Absolute date shown in the HTML and README: "Jul 7, 2026".
 *
 * Reads the calendar date straight off the ISO string rather than converting
 * to the local or UTC day. The commit already carries its own offset, so this
 * is both machine-independent and the date the author saw when they committed.
 */
export function formatAbsolute(iso) {
  if (!ISO_RE.test(iso)) throw new Error(`not an ISO timestamp: ${iso}`);
  const [, y, mo, d] = /^(\d{4})-(\d{2})-(\d{2})T/.exec(iso);
  return `${MONTHS[Number(mo) - 1]} ${Number(d)}, ${y}`;
}

/**
 * ISO date of the last commit touching a path, or null if it has no history.
 *
 * --literal-pathspecs because `--` ends option parsing but does not turn off
 * pathspec magic. A committed directory named ":(exclude)x" would otherwise be
 * read as a pathspec matching everything else, so that skill would take the
 * repo's newest date and change on every run. The slug check cannot catch it:
 * in ":(exclude)x/evil/SKILL.md" the slug is the clean last segment.
 */
export function lastCommitISO(path, { repoRoot = REPO_ROOT } = {}) {
  const out = execFileSync('git', ['--literal-pathspecs', 'log', '-1', '--format=%cI', '--', path], {
    cwd: repoRoot, encoding: 'utf8',
  }).trim();
  return out || null;
}

function walk(dir, repoRoot, out = []) {
  const atRoot = dir === repoRoot;
  for (const name of readdirSync(dir)) {
    if (SKIP_ANYWHERE.has(name) || (atRoot && SKIP_AT_ROOT.has(name))) continue;
    const full = join(dir, name);
    let st;
    try { st = statSync(full); } catch { continue; }
    if (st.isDirectory()) walk(full, repoRoot, out);
    else out.push(relative(repoRoot, full));
  }
  return out;
}

/**
 * Every skill and plugin in the repo, keyed by slug.
 *
 * A plugin whose root is also a skill (okf-wiki, pdf-design, visual-explainer)
 * is one entry, not two: same directory, same date.
 *
 * Throws on a duplicate slug. Two skills with one name would silently stamp
 * each other's dates, so the collision has to stop the run rather than pick.
 */
export function collectEntries({ repoRoot = REPO_ROOT, dates = lastCommitISO } = {}) {
  const files = walk(repoRoot, repoRoot);
  const bySlug = new Map();

  const add = (slug, entry) => {
    if (!SLUG_RE.test(slug)) {
      throw new Error(
        `unusable slug "${slug}" from ${entry.path}. ` +
        'A slug addresses a stamp in an HTML attribute, a docs/ path, and a ' +
        'README link, so it has to be lowercase letters, digits, and hyphens.'
      );
    }
    const existing = bySlug.get(slug);
    if (existing) {
      if (existing.path === entry.path) {
        // Plugin root that is also a skill directory. Keep the plugin framing.
        existing.type = 'plugin';
        if (entry.version) existing.version = entry.version;
        return;
      }
      throw new Error(
        `duplicate slug "${slug}": ${existing.path} and ${entry.path}. ` +
        'Slugs address stamps across the site, so they have to be unique.'
      );
    }
    bySlug.set(slug, { slug, ...entry });
  };

  for (const file of files) {
    const parts = file.split(sep);
    const base = parts[parts.length - 1];

    if (base === 'plugin.json' && parts[parts.length - 2] === '.claude-plugin') {
      const manifest = JSON.parse(readFileSync(join(repoRoot, file), 'utf8'));
      const path = parts.slice(0, -2).join('/');
      if (!manifest.name) throw new Error(`${file} has no name`);
      add(manifest.name, { type: 'plugin', path, version: manifest.version || null });
    } else if (base === 'SKILL.md') {
      const path = parts.slice(0, -1).join('/');
      add(parts[parts.length - 2], { type: 'skill', path });
    }
  }

  const entries = [...bySlug.values()].sort((a, b) => a.slug.localeCompare(b.slug));
  for (const entry of entries) {
    if (entry.path.startsWith('docs/')) {
      // See rule 1 at the top of the file.
      throw new Error(`${entry.slug} resolves to ${entry.path}; dates must not come from docs/`);
    }
    const updated = dates(entry.path, { repoRoot });
    if (updated !== null && !ISO_RE.test(updated)) {
      throw new Error(`unusable date "${updated}" for ${entry.path}; expected an ISO timestamp`);
    }
    entry.updated = updated;
  }
  return entries;
}

/** Slug a docs/index.html card link points at, or null if it is not a skill card. */
export function slugFromHref(href) {
  const tree = href.match(/\/tree\/[^/]+\/([^/?#]+)\/?$/);
  if (tree) return decodeURIComponent(tree[1]);
  if (/^[a-z0-9][a-z0-9-]*\/$/i.test(href)) return href.slice(0, -1);
  return null;
}

// Layout only. The tape itself is drawn by docs/updated.css.
const TAPE_CLASS = {
  card: 'updated-tape updated-tape-card mt-4',
  hero: 'updated-tape updated-tape-hero mt-5',
};

function tape(entry, variant) {
  const absolute = formatAbsolute(entry.updated);
  return `<p class="${TAPE_CLASS[variant]}" data-updated-at="${entry.updated}" data-updated-slug="${entry.slug}">`
    + `Updated <time datetime="${entry.updated}">${absolute}</time></p>`;
}

// One attribute, consumed whole: either a run of plain characters, or a
// complete quoted value. Scanning with [^>]* instead reads the inside of a
// quoted value as if it were markup, so an unrelated attribute that merely
// quotes the text `class="skill-card"` is mistaken for the real thing. Every
// tag pattern in this file is built from it for that reason.
const ATTRS = '(?:[^>"\']|"[^"]*"|\'[^\']*\')*';

// Anchored on (?:^|\s) rather than \b, which sits between the "-" and the "s"
// of data-src and so never excluded a prefixed attribute. An attribute can only
// begin at the start of the run or after whitespace.
const attr = (name, value) => `(?:^|\\s)${name}=(?:"${value}"|'${value}')`;

/** Value of `name` within a tag's attribute text, or '' if it has none. */
function attrValue(attrs, name) {
  const m = attrs.match(new RegExp(`(?:^|\\s)${name}=(?:"([^"]*)"|'([^']*)')`, 'i'));
  return m ? (m[1] ?? m[2]) : '';
}

// Matches a stamp this tool owns, so a rewrite replaces rather than stacks.
// Global: if a page somehow carried two stamps, clearing only the first would
// leave a duplicate behind and quietly break idempotence.
//
// Keyed on the data attribute this tool owns, not on the exact serialization it
// writes. Attribute order and quote style carry no meaning in HTML, so matching
// the literal output would miss a tape a formatter had touched and append a
// second one beside it, leaving a stale date with nothing reporting it.
const TAPE_RE = new RegExp(
  `[ \\t]*<p\\b${ATTRS}?${attr('data-updated-slug', '[^"\']*')}${ATTRS}>.*?</p>\\n?`,
  'gs',
);

/**
 * Leading whitespace of the line `index` sits on.
 *
 * Searches from index - 1 because lastIndexOf includes its start position, and
 * an index that lands on the newline ending a line would otherwise report the
 * next line's indent (which is none of it).
 */
function indent(html, index) {
  const lineStart = html.lastIndexOf('\n', Math.max(0, index - 1)) + 1;
  return (html.slice(lineStart, index).match(/^[ \t]*/) || [''])[0];
}

/**
 * Stamps the plugin and skill cards on docs/index.html.
 *
 * Cards are <a class="skill-card"> whose href already names the thing they
 * link to, so identity comes from markup that is already there. A card
 * pointing somewhere that is not a skill or plugin (about/, workflows/) is
 * left alone.
 */
export function stampIndex(html, entries, { onSkip } = {}) {
  const bySlug = new Map(entries.map((e) => [e.slug, e]));
  // Attribute-aware, like every other tag pattern here: an <a> carrying
  // title="class='skill-card'" is not a card, and reading its class list as a
  // list rather than a substring is what tells the two apart. Nested cards are
  // not handled, because an <a> inside an <a> is invalid HTML no parser keeps.
  const anchor = new RegExp(`<a\\b(${ATTRS})>`, 'g');
  let out = '';
  let cursor = 0;
  let match;

  while ((match = anchor.exec(html)) !== null) {
    const attrs = match[1];
    if (!attrValue(attrs, 'class').split(/\s+/).includes('skill-card')) continue;
    const close = html.indexOf('</a>', match.index);
    if (close === -1) continue;
    const href = attrValue(attrs, 'href');
    const slug = slugFromHref(href);
    const entry = slug ? bySlug.get(slug) : null;

    let block = html.slice(match.index, close);
    if (entry && entry.updated) {
      block = block.replace(TAPE_RE, '');
      const pad = indent(html, match.index);
      block = `${block.replace(/\s*$/, '')}\n${pad}    ${tape(entry, 'card')}\n${pad}`;
    } else if (slug && !entry && onSkip) {
      onSkip({ href, slug });
    }
    out += html.slice(cursor, match.index) + block;
    cursor = close;
    anchor.lastIndex = close;
  }
  return out + html.slice(cursor);
}

/**
 * Stamps one docs/<slug>/index.html hero, under its <h1>.
 *
 * The 49 skill pages use two different hero layouts, so the <h1> is the one
 * landmark every page shares.
 */
export function stampSkillPage(html, entry) {
  const cleaned = html.replace(TAPE_RE, '');
  const close = cleaned.indexOf('</h1>');
  if (close === -1) return null;
  const at = close + '</h1>'.length;
  const pad = indent(cleaned, at);
  const rest = cleaned.slice(at);
  // The tape always ends its own line, whatever the page looked like going in.
  // Without this, a page whose </h1> does not already end a line gains a
  // newline on the first pass and another on the second, so CI commits a churn
  // diff instead of converging. Same normalize-then-insert shape as stampIndex.
  const tail = rest.startsWith('\n') ? rest : `\n${rest}`;
  return `${cleaned.slice(0, at)}\n${pad}${tape(entry, 'hero')}${tail}`;
}

/** The attribute text of every <name ...> tag in the page. */
function tags(html, name) {
  const re = new RegExp(`<${name}\\b(${ATTRS})>`, 'gi');
  return [...html.matchAll(re)].map((m) => m[1]);
}

/** Escapes a literal string for use inside a RegExp. */
const reEscape = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/**
 * Whether a page already loads this script.
 *
 * Looks for a real script element rather than the bare path, so a page that
 * merely mentions updated.js in prose does not read as one that loads it. A
 * tag written inside an HTML comment would still count; ruling that out needs
 * a parser, and these pages are generated, so the substring case is the one
 * worth closing. The insert and the later verify share this, so they cannot
 * disagree about whether the asset landed.
 */
export const hasScriptTag = (html, src) =>
  tags(html, 'script').some((a) => new RegExp(attr('src', reEscape(src)), 'i').test(a));

/** Adds <script src="../updated.js"> once, right before </body>. */
export function ensureScriptTag(html, src) {
  if (hasScriptTag(html, src)) return html;
  const tag = `<script defer src="${src}"></script>`;
  if (!html.includes('</body>')) return html;
  return html.replace(/([ \t]*)<\/body>/, (_m, pad) => `${pad}${tag}\n${pad}</body>`);
}

/** Whether a page already links this stylesheet. See hasScriptTag. */
export const hasStyleLink = (html, href) => tags(html, 'link').some((a) =>
  new RegExp(attr('href', reEscape(href)), 'i').test(a)
  && new RegExp(attr('rel', '[^"\']*\\bstylesheet\\b[^"\']*'), 'i').test(a));

/**
 * Adds <link rel="stylesheet" href="../updated.css"> once, before </head>.
 *
 * The tape is styled by a real stylesheet rather than by injected CSS so it is
 * drawn on first paint; updated.js only rewrites the words and the age tier.
 */
export function ensureStyleLink(html, href) {
  if (hasStyleLink(html, href)) return html;
  const tag = `<link rel="stylesheet" href="${href}">`;
  if (!html.includes('</head>')) return html;
  return html.replace(/([ \t]*)<\/head>/, (_m, pad) => `${pad}${tag}\n${pad}</head>`);
}

/**
 * Adds and maintains an "Updated" column in the README tables.
 *
 * A row is stamped when its first cell links to a known skill or plugin
 * directory, so hand-written prose tables are untouched.
 */
export function stampReadme(md, entries, { onUnstamped } = {}) {
  const byPath = new Map(entries.map((e) => [e.path, e]));
  // Split on either ending and write back whatever the file used. Splitting on
  // "\n" alone leaves a "\r" on each line, which stops cells() from seeing the
  // closing pipe and turns the carriage return into an extra cell, so every
  // rebuilt row grows a phantom column.
  const eol = md.includes('\r\n') ? '\r\n' : '\n';
  const lines = md.split(/\r?\n/);
  const out = [];
  let i = 0;

  const cells = (line) => line.replace(/^\||\|$/g, '').split(/(?<!\\)\|/);
  const rebuild = (parts) => `| ${parts.map((p) => p.trim()).join(' | ')} |`;
  // Separator rows keep the repo's unpadded style, so adding a column shows up
  // as one changed cell rather than a reformatted line.
  const rebuildSeparator = (parts) => `|${parts.map((p) => p.trim()).join('|')}|`;

  while (i < lines.length) {
    const header = lines[i];
    const sep = lines[i + 1] || '';
    const isTable = /^\|.*\|$/.test(header.trim()) && /^\|[\s:|-]+\|$/.test(sep.trim());
    if (!isTable) { out.push(lines[i++]); continue; }

    const body = [];
    let j = i + 2;
    while (j < lines.length && /^\|.*\|$/.test(lines[j].trim())) body.push(lines[j++]);

    const entryFor = (row) => {
      const first = cells(row)[0] || '';
      const link = first.match(/\]\(\.\/([^)]+?)\/?\)/);
      return link ? byPath.get(link[1]) : null;
    };
    const stampable = body.some(entryFor);
    if (!stampable) {
      out.push(...lines.slice(i, j));
      i = j;
      continue;
    }

    const headerCells = cells(header).map((c) => c.trim());
    const hasColumn = headerCells[headerCells.length - 1] === 'Updated';
    const width = headerCells.length;

    // A table is reshaped whole or not at all. A row that does not match the
    // header width has an unescaped pipe in it, and adding a column would make
    // it exactly as wide as a well-formed row: the next run could no longer
    // tell its last cell from a stamp, and would overwrite real text. Refusing
    // the table keeps that ambiguity from ever being created. It also skips
    // rows that are fine, which is the point: the header is shared, so there is
    // no way to widen it for some rows and not others.
    const ragged = [sep, ...body].filter((row) => cells(row).length !== width);
    if (ragged.length) {
      out.push(...lines.slice(i, j));
      if (onUnstamped) ragged.forEach((row) => onUnstamped(row));
      i = j;
      continue;
    }

    out.push(hasColumn ? header : rebuild([...headerCells, 'Updated']));
    out.push(hasColumn ? sep : rebuildSeparator([...cells(sep).map((c) => c.trim()), '--------']));

    for (const row of body) {
      const parts = cells(row).map((c) => c.trim());
      // Every row is header-width by now, so when the column exists the last
      // cell is the one this run wrote last time. A cell holding anything else
      // was typed by hand: report it and leave the row alone rather than
      // discard someone's note.
      if (hasColumn) {
        if (!STAMP_CELL.test(parts[parts.length - 1])) {
          out.push(row);
          if (onUnstamped) onUnstamped(row);
          continue;
        }
        parts.pop();
      }
      const entry = entryFor(row);
      // A row this tool does not track gets an empty cell, not a typed
      // placeholder glyph: blank reads as "no date" and adds no character.
      out.push(rebuild([...parts, entry && entry.updated ? formatAbsolute(entry.updated) : '']));
    }
    i = j;
  }
  return out.join(eol);
}

/**
 * The docs pages that exist for these entries.
 *
 * A missing docs/<slug>/index.html is normal, not a problem: 20 of the 64
 * entries are sub-skills inside a plugin bundle (superjawn/skills/*,
 * dev-toolkit/skills/*) that the site covers through the README tables rather
 * than a page of their own, and the five bundle cards link to GitHub instead
 * of a local page. Treating absence as an error would fail every run.
 */
function docsPagesFor(entries, repoRoot) {
  const pages = [];
  const notFiles = [];
  // Resolved once, so the comparison below is against real locations. An
  // lstat of the leaf alone would miss a symlinked docs/<slug>/, which reaches
  // another page just as effectively as a symlinked index.html does.
  let docsRoot;
  try { docsRoot = realpathSync(join(repoRoot, 'docs')); } catch { return { pages, notFiles }; }

  for (const entry of entries) {
    const page = join(repoRoot, 'docs', entry.slug, 'index.html');
    if (!entry.updated) continue;
    // A stamp destination must be a regular file that really lives where its
    // path says. Writing through a link, at any segment, would restamp another
    // page under this slug's date, and the workflow would commit an edit that
    // appeared nowhere in the diff.
    let real;
    try { real = realpathSync(page); } catch { continue; }
    if (real !== join(docsRoot, entry.slug, 'index.html') || !statSync(real).isFile()) {
      notFiles.push(relative(repoRoot, page));
      continue;
    }
    pages.push({ entry, page });
  }
  return { pages, notFiles };
}

export function run({ repoRoot = REPO_ROOT, check = false, quiet = false, log = console.log } = {}) {
  const entries = collectEntries({ repoRoot });
  const undated = entries.filter((e) => !e.updated);
  const changed = [];
  const write = (file, next) => {
    const path = join(repoRoot, file);
    const before = readFileSync(path, 'utf8');
    if (before === next) return;
    changed.push(file);
    if (!check) writeFileSync(path, next);
  };

  const indexPath = 'docs/index.html';
  const indexHtml = readFileSync(join(repoRoot, indexPath), 'utf8');
  const skipped = [];
  const missingAssets = [];
  // A page with no </head> or </body> would silently come back without the
  // stylesheet or script, leaving a stamp that never ages. Check rather than
  // trust the insertion.
  const withAssets = (html, prefix, file) => {
    const next = ensureStyleLink(ensureScriptTag(html, `${prefix}updated.js`), `${prefix}updated.css`);
    if (!hasScriptTag(next, `${prefix}updated.js`) || !hasStyleLink(next, `${prefix}updated.css`)) {
      missingAssets.push(file);
    }
    return next;
  };

  write(indexPath, withAssets(
    stampIndex(indexHtml, entries, { onSkip: (s) => skipped.push(s.slug) }),
    '',
    indexPath,
  ));

  const missingH1 = [];
  const { pages: docsPages, notFiles } = docsPagesFor(entries, repoRoot);
  for (const { entry, page } of docsPages) {
    const file = relative(repoRoot, page);
    const stamped = stampSkillPage(readFileSync(page, 'utf8'), entry);
    if (stamped === null) { missingH1.push(file); continue; }
    write(file, withAssets(stamped, '../', file));
  }

  const unstampedRows = [];
  write('README.md', stampReadme(
    readFileSync(join(repoRoot, 'README.md'), 'utf8'),
    entries,
    { onUnstamped: (row) => unstampedRows.push(row.trim()) },
  ));

  if (!quiet) {
    log(`${entries.length} entries (${entries.filter((e) => e.type === 'plugin').length} plugins)`);
    log(changed.length ? `${check ? 'would change' : 'updated'}: ${changed.join(', ')}` : 'no changes');
  }
  // Everything that leaves a surface unstamped or unable to age, in one list.
  // Three arrays a caller has to remember to check is how an unstamped page
  // rides along inside the CI commit that was supposed to stamp it. A card
  // pointing at a non-skill (workflows/, about/) is not in here: that is
  // expected, and an error nobody can act on is an error nobody reads.
  const problems = [
    ...missingH1.map((f) => `${f} has no <h1>, not stamped`),
    ...undated.map((e) => `${e.path} has no commit history, not stamped`),
    ...missingAssets.map((f) => `${f} is missing updated.css or updated.js`),
    ...notFiles.map((f) => `${f} does not resolve to a regular file at that path, not stamped`),
    ...unstampedRows.map((r) => `README row not stamped, its cells are not this tool's to rewrite: ${r}`),
  ];

  for (const slug of skipped) log(`note: card links to ${slug}/ which is not a skill or plugin`);
  for (const problem of problems) log(`problem: ${problem}`);

  return { entries, changed, skipped, missingH1, undated, missingAssets, notFiles, unstampedRows, problems };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const check = process.argv.includes('--check');
  const result = run({ check, quiet: process.argv.includes('--quiet') });
  // Exits before the --check comparison: a page that could not be stamped is
  // wrong whether or not anything else changed, and CI commits what it finds.
  if (result.problems.length) {
    console.error(`${result.problems.length} surface(s) could not be stamped; see problems above`);
    process.exit(1);
  }
  if (check && result.changed.length) {
    console.error('stamps are out of date: run node scripts/updated-stamp.mjs');
    process.exit(1);
  }
}
