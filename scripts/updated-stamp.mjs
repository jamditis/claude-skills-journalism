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

function repoRelativePath(repoRoot, file) {
  return relative(repoRoot, file).split(sep).join('/');
}

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
  const local = href.match(/^(?:\.\/)?([a-z0-9][a-z0-9-]*)\/$/i);
  if (local) return local[1];
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

const RAW_TEXT_ELEMENTS = new Set(['script', 'style']);
const VOID_ELEMENTS = new Set([
  'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
  'link', 'meta', 'param', 'source', 'track', 'wbr',
]);

/** Parse one tag's attributes without scanning inside quoted values. */
function parseAttributes(source) {
  const attrs = new Map();
  let i = 0;

  while (i < source.length) {
    while (/\s/.test(source[i] || '')) i += 1;
    if (i >= source.length || source[i] === '/') break;

    const start = i;
    while (i < source.length && !/[\s=/>]/.test(source[i])) i += 1;
    if (i === start) { i += 1; continue; }
    const name = source.slice(start, i).toLowerCase();

    while (/\s/.test(source[i] || '')) i += 1;
    let value = '';
    if (source[i] === '=') {
      i += 1;
      while (/\s/.test(source[i] || '')) i += 1;
      if (source[i] === '"' || source[i] === "'") {
        const quote = source[i++];
        const valueStart = i;
        while (i < source.length && source[i] !== quote) i += 1;
        value = source.slice(valueStart, i);
        if (source[i] === quote) i += 1;
      } else {
        const valueStart = i;
        while (i < source.length && !/[\s>]/.test(source[i])) i += 1;
        value = source.slice(valueStart, i);
      }
    }

    // Browsers keep the first duplicate attribute. Matching that behavior
    // prevents a later decoy from changing what this tool thinks the DOM sees.
    if (!attrs.has(name)) attrs.set(name, value);
  }
  return attrs;
}

/** Find the closing angle bracket for a tag, respecting quoted values. */
function tagEnd(html, from) {
  let quote = null;
  for (let i = from; i < html.length; i += 1) {
    const char = html[i];
    if (quote) {
      if (char === quote) quote = null;
    } else if (char === '"' || char === "'") {
      quote = char;
    } else if (char === '>') {
      return i;
    }
  }
  return -1;
}

/** Find an exact raw-text closing tag without treating script text as markup. */
function rawTextClose(html, name, from) {
  const lower = html.toLowerCase();
  const needle = `</${name}`;
  let at = lower.indexOf(needle, from);
  while (at !== -1) {
    if (/[\s/>]/.test(lower[at + needle.length] || '')) return at;
    at = lower.indexOf(needle, at + needle.length);
  }
  return -1;
}

/**
 * Tokenize the HTML surfaces this repository owns.
 *
 * This is deliberately small rather than a browser-grade parser: it recognizes
 * real tag and attribute boundaries, skips comments and raw script/style text,
 * pairs elements, and marks inert template content. Every stamper lookup uses
 * these tokens so quoting, casing, and custom-element boundaries agree.
 */
function tokenizeHTML(html) {
  const tags = [];
  const pairs = new Map();
  const stacks = new Map();
  let templateDepth = 0;
  let rawText = null;
  let cursor = 0;

  while (cursor < html.length) {
    const start = rawText
      ? rawTextClose(html, rawText, cursor)
      : html.indexOf('<', cursor);
    if (start === -1) break;

    if (!rawText && html.startsWith('<!--', start)) {
      const end = html.indexOf('-->', start + 4);
      cursor = end === -1 ? html.length : end + 3;
      continue;
    }

    let at = start + 1;
    let closing = false;
    if (html[at] === '/') { closing = true; at += 1; }
    const nameStart = at;
    while (/[A-Za-z0-9:-]/.test(html[at] || '')) at += 1;
    if (at === nameStart || !/[\s/>]/.test(html[at] || '')) {
      cursor = start + 1;
      continue;
    }

    const name = html.slice(nameStart, at).toLowerCase();
    const end = tagEnd(html, at);
    if (end === -1) break;
    const selfClosing = /\/\s*$/.test(html.slice(at, end)) || VOID_ELEMENTS.has(name);

    if (closing && name === 'template') templateDepth = Math.max(0, templateDepth - 1);
    const tag = {
      name,
      start,
      end: end + 1,
      closing,
      selfClosing,
      templateDepth,
      attrs: closing ? new Map() : parseAttributes(html.slice(at, end)),
    };
    const index = tags.push(tag) - 1;

    if (closing) {
      const stack = stacks.get(name);
      if (stack?.length) pairs.set(stack.pop(), index);
      if (rawText === name) rawText = null;
    } else if (!selfClosing) {
      if (!stacks.has(name)) stacks.set(name, []);
      stacks.get(name).push(index);
      if (name === 'template') templateDepth += 1;
      if (RAW_TEXT_ELEMENTS.has(name)) rawText = name;
    }
    cursor = end + 1;
  }

  return { tags, pairs };
}

/** Remove every stale stamp owned by this tool, regardless of tag casing. */
function removeOwnedTapes(html) {
  const { tags, pairs } = tokenizeHTML(html);
  const ranges = [];
  for (let i = 0; i < tags.length; i += 1) {
    const tag = tags[i];
    if (tag.closing || tag.name !== 'p' || !tag.attrs.has('data-updated-slug')) continue;
    const closeIndex = pairs.get(i);
    if (closeIndex === undefined) continue;

    let start = tag.start;
    const lineStart = html.lastIndexOf('\n', Math.max(0, start - 1)) + 1;
    if (/^[ \t]*$/.test(html.slice(lineStart, start))) start = lineStart;
    let end = tags[closeIndex].end;
    if (html.startsWith('\r\n', end)) end += 2;
    else if (html[end] === '\n') end += 1;
    ranges.push([start, end]);
  }

  for (const [start, end] of ranges.sort((a, b) => b[0] - a[0])) {
    html = html.slice(0, start) + html.slice(end);
  }
  return html;
}

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
export function stampIndex(html, entries, { onSkip, onStamp } = {}) {
  const bySlug = new Map(entries.map((e) => [e.slug, e]));
  const { tags, pairs } = tokenizeHTML(html);
  let out = '';
  let cursor = 0;

  for (let i = 0; i < tags.length; i += 1) {
    const anchor = tags[i];
    if (anchor.closing || anchor.name !== 'a' || anchor.templateDepth > 0) continue;
    if (!(anchor.attrs.get('class') || '').split(/\s+/).includes('skill-card')) continue;
    const closeIndex = pairs.get(i);
    if (closeIndex === undefined) continue;
    const close = tags[closeIndex];
    const href = anchor.attrs.get('href') || '';
    const slug = slugFromHref(href);
    const entry = slug ? bySlug.get(slug) : null;

    let block = html.slice(anchor.start, close.start);
    if (entry && entry.updated) {
      block = removeOwnedTapes(block);
      const pad = indent(html, anchor.start);
      block = `${block.replace(/\s*$/, '')}\n${pad}    ${tape(entry, 'card')}\n${pad}`;
      if (onStamp) onStamp(entry);
    } else if (slug && !entry && onSkip) {
      onSkip({ href, slug });
    }
    out += html.slice(cursor, anchor.start) + block;
    cursor = close.start;
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
  const cleaned = removeOwnedTapes(html);
  const { tags, pairs } = tokenizeHTML(cleaned);
  let close;
  for (let i = 0; i < tags.length; i += 1) {
    const heading = tags[i];
    if (heading.closing || heading.name !== 'h1' || heading.templateDepth > 0) continue;
    const closeIndex = pairs.get(i);
    if (closeIndex !== undefined) close = tags[closeIndex];
    break;
  }
  if (!close) return null;
  const at = close.end;
  const pad = indent(cleaned, at);
  const rest = cleaned.slice(at);
  // The tape always ends its own line, whatever the page looked like going in.
  // Without this, a page whose </h1> does not already end a line gains a
  // newline on the first pass and another on the second, so CI commits a churn
  // diff instead of converging. Same normalize-then-insert shape as stampIndex.
  const tail = rest.startsWith('\n') ? rest : `\n${rest}`;
  return `${cleaned.slice(0, at)}\n${pad}${tape(entry, 'hero')}${tail}`;
}

/**
 * Whether a page already loads this script.
 *
 * Looks for a real script element rather than the bare path, so a page that
 * merely mentions updated.js in prose, a comment, raw script text, or inert
 * template content does not read as one that loads it. The insert and later
 * verify share the tokenizer, so they cannot disagree about whether it landed.
 */
export const hasScriptTag = (html, src) => tokenizeHTML(html).tags.some((tag) =>
  !tag.closing && tag.templateDepth === 0
  && tag.name === 'script' && tag.attrs.get('src') === src);

function insertBeforeClosingTag(html, name, markup) {
  const tags = tokenizeHTML(html).tags;
  let closing;
  for (let i = tags.length - 1; i >= 0; i -= 1) {
    if (tags[i].closing && tags[i].name === name && tags[i].templateDepth === 0) {
      closing = tags[i];
      break;
    }
  }
  if (!closing) return html;
  const pad = indent(html, closing.start);
  return `${html.slice(0, closing.start)}${markup}\n${pad}${html.slice(closing.start)}`;
}

/** Adds <script src="../updated.js"> once, right before </body>. */
export function ensureScriptTag(html, src) {
  if (hasScriptTag(html, src)) return html;
  const tag = `<script defer src="${src}"></script>`;
  return insertBeforeClosingTag(html, 'body', tag);
}

/** Whether a page already links this stylesheet. See hasScriptTag. */
export const hasStyleLink = (html, href) => tokenizeHTML(html).tags.some((tag) => {
  if (tag.closing || tag.templateDepth > 0
    || tag.name !== 'link' || tag.attrs.get('href') !== href) return false;
  return (tag.attrs.get('rel') || '').toLowerCase().split(/\s+/).includes('stylesheet');
});

/**
 * Adds <link rel="stylesheet" href="../updated.css"> once, before </head>.
 *
 * The tape is styled by a real stylesheet rather than by injected CSS so it is
 * drawn on first paint; updated.js only rewrites the words and the age tier.
 */
export function ensureStyleLink(html, href) {
  if (hasStyleLink(html, href)) return html;
  const tag = `<link rel="stylesheet" href="${href}">`;
  return insertBeforeClosingTag(html, 'head', tag);
}

/**
 * Adds and maintains an "Updated" column in the README tables.
 *
 * A row is stamped when its first cell links to a known skill or plugin
 * directory, so hand-written prose tables are untouched.
 */
export function stampReadme(md, entries, { onUnstamped, onStamp } = {}) {
  const byPath = new Map(entries.map((e) => [e.path, e]));
  // Split on either ending and write back whatever the file used. Splitting on
  // "\n" alone leaves a "\r" on each line, which stops cells() from seeing the
  // closing pipe and turns the carriage return into an extra cell, so every
  // rebuilt row grows a phantom column.
  const eol = md.includes('\r\n') ? '\r\n' : '\n';
  const lines = md.split(/\r?\n/);
  const out = [];
  let i = 0;

  const parseRow = (line) => {
    const trimmed = line.trim();
    if (!trimmed.includes('|')) return null;
    const leading = trimmed.startsWith('|');
    const trailing = /(?<!\\)\|$/.test(trimmed);
    let content = trimmed;
    if (leading) content = content.slice(1);
    if (trailing) content = content.slice(0, -1);
    return { cells: content.split(/(?<!\\)\|/), leading, trailing };
  };
  const cells = (line) => parseRow(line)?.cells || [];
  const rebuild = (parts, shape) => {
    const content = parts.map((part) => part.trim()).join(' | ');
    return `${shape.leading ? '| ' : ''}${content}${shape.trailing ? ' |' : ''}`;
  };
  // Separator rows keep the repo's unpadded style, so adding a column shows up
  // as one changed cell rather than a reformatted line.
  const rebuildSeparator = (parts, shape) => {
    const content = parts.map((part) => part.trim()).join('|');
    return `${shape.leading ? '|' : ''}${content}${shape.trailing ? '|' : ''}`;
  };
  const separator = (parsed) => parsed && parsed.cells.length > 1
    && parsed.cells.every((cell) => /^\s*:?-{3,}:?\s*$/.test(cell));

  while (i < lines.length) {
    const header = lines[i];
    const sep = lines[i + 1] || '';
    const headerRow = parseRow(header);
    const sepRow = parseRow(sep);
    const isTable = headerRow && headerRow.cells.length > 1 && separator(sepRow);
    if (!isTable) { out.push(lines[i++]); continue; }

    const body = [];
    let j = i + 2;
    while (j < lines.length && (parseRow(lines[j])?.cells.length || 0) > 1) body.push(lines[j++]);

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

    out.push(hasColumn ? header : rebuild([...headerCells, 'Updated'], headerRow));
    out.push(hasColumn ? sep : rebuildSeparator(
      [...cells(sep).map((c) => c.trim()), '--------'], sepRow,
    ));

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
      out.push(rebuild(
        [...parts, entry && entry.updated ? formatAbsolute(entry.updated) : ''], parseRow(row),
      ));
      if (entry?.updated && onStamp) onStamp(entry);
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
      notFiles.push(repoRelativePath(repoRoot, page));
      continue;
    }
    pages.push({ entry, page });
  }
  return { pages, notFiles };
}

/** Whether a top-level output is the regular file named by its repository path. */
function isRegularDestination(repoRoot, file) {
  let root;
  let real;
  try {
    root = realpathSync(repoRoot);
    real = realpathSync(join(repoRoot, file));
  } catch {
    return false;
  }
  return real === join(root, file) && statSync(real).isFile();
}

export function run({ repoRoot = REPO_ROOT, check = false, quiet = false, log = console.log } = {}) {
  const entries = collectEntries({ repoRoot });
  const undated = entries.filter((e) => !e.updated);
  const covered = new Set();
  const changed = [];
  const write = (file, next) => {
    const path = join(repoRoot, file);
    const before = readFileSync(path, 'utf8');
    if (before === next) return;
    changed.push(file);
    if (!check) writeFileSync(path, next);
  };

  const indexPath = 'docs/index.html';
  const skipped = [];
  const missingAssets = [];
  const notFiles = [];
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

  if (isRegularDestination(repoRoot, indexPath)) {
    const indexHtml = readFileSync(join(repoRoot, indexPath), 'utf8');
    write(indexPath, withAssets(
      stampIndex(indexHtml, entries, {
        onSkip: (s) => skipped.push(s.slug),
        onStamp: (entry) => covered.add(entry.slug),
      }),
      '',
      indexPath,
    ));
  } else {
    notFiles.push(indexPath);
  }

  const missingH1 = [];
  const { pages: docsPages, notFiles: unsafeDocsPages } = docsPagesFor(entries, repoRoot);
  notFiles.push(...unsafeDocsPages);
  for (const { entry, page } of docsPages) {
    const file = repoRelativePath(repoRoot, page);
    const stamped = stampSkillPage(readFileSync(page, 'utf8'), entry);
    if (stamped === null) { missingH1.push(file); continue; }
    covered.add(entry.slug);
    write(file, withAssets(stamped, '../', file));
  }

  const unstampedRows = [];
  const readmePath = 'README.md';
  if (isRegularDestination(repoRoot, readmePath)) {
    write(readmePath, stampReadme(
      readFileSync(join(repoRoot, readmePath), 'utf8'),
      entries,
      {
        onUnstamped: (row) => unstampedRows.push(row.trim()),
        onStamp: (entry) => covered.add(entry.slug),
      },
    ));
  } else {
    notFiles.push(readmePath);
  }

  if (!quiet) {
    log(`${entries.length} entries (${entries.filter((e) => e.type === 'plugin').length} plugins)`);
    log(changed.length ? `${check ? 'would change' : 'updated'}: ${changed.join(', ')}` : 'no changes');
  }
  // Everything that leaves a surface unstamped or unable to age, in one list.
  // Three arrays a caller has to remember to check is how an unstamped page
  // rides along inside the CI commit that was supposed to stamp it. A card
  // pointing at a non-skill (workflows/, about/) is not in here: that is
  // expected, and an error nobody can act on is an error nobody reads.
  const uncovered = entries.filter((entry) => entry.updated && !covered.has(entry.slug));
  const problems = [
    ...missingH1.map((f) => `${f} has no <h1>, not stamped`),
    ...undated.map((e) => `${e.path} has no commit history, not stamped`),
    ...missingAssets.map((f) => `${f} is missing updated.css or updated.js`),
    ...notFiles.map((f) => `${f} does not resolve to a regular file at that path, not stamped`),
    ...unstampedRows.map((r) => `README row not stamped, its cells are not this tool's to rewrite: ${r}`),
    ...uncovered.map((e) => `${e.path} (${e.slug}) reaches no public stamp surface`),
  ];

  for (const slug of skipped) log(`note: card links to ${slug}/ which is not a skill or plugin`);
  for (const problem of problems) log(`problem: ${problem}`);

  return {
    entries, changed, skipped, missingH1, undated, missingAssets,
    notFiles, unstampedRows, uncovered, problems,
  };
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
