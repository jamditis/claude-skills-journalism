// Detect maintainer-specific path assumptions in the pdf-design skill, so the
// portability work in #235 has a guard to fix against rather than a prose
// inventory that drifts. The skill body is read from the repository, not
// hard-coded, and each finding names the adapter that makes it portable.
// Explicit `### Adapter:` sections may document client-specific paths without
// turning them into shared defaults. This mirrors the
// { kind, mappable, detail } signal shape that dev-toolkit-portability.mjs uses.
//
// This detector and its failing fixture landed before the shared SKILL.md
// rewrite. It now guards the portable default and explicit adapter boundary.

import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import MarkdownIt from 'markdown-it';

export const ROOT = fileURLToPath(new URL('..', import.meta.url));
export const SKILL_SUBDIR = 'pdf-design';

// Read every bundled text file under the skill directory. Path assumptions live
// in SKILL.md today, but a template, reference, or helper added later can carry
// the same coupling, so the detector reads the whole bundle rather than one
// file. Binary files (an og-image, a font) are skipped.
export function readSkillBodies(root = ROOT) {
  const dir = join(root, SKILL_SUBDIR);
  const bodies = [];
  const walk = (current) => {
    for (const entry of readdirSync(current, { withFileTypes: true })) {
      const path = join(current, entry.name);
      if (entry.isDirectory()) {
        walk(path);
        continue;
      }
      if (!entry.isFile()) continue;
      const bytes = readFileSync(path);
      if (!bytes.includes(0)) bodies.push({ path, body: bytes.toString('utf8') });
    }
  };
  walk(dir);
  return bodies;
}

// Each assumption is a concrete, greppable pattern paired with the adapter that
// makes it portable. `mappable: true` means an adapter exists; nothing here is
// Claude-only, because both couplings are about where files live, not about a
// Claude mechanic.
// A home-anchored path can be written tilde-style (~/x) or through the HOME
// variable ($HOME/x or ${HOME}/x). The detector recognizes all three spellings
// so a later edit cannot slip a coupling past the guard by swapping ~ for $HOME.
const HOME = '(?:~|\\$HOME|\\$\\{HOME\\})';
const markdown = new MarkdownIt({ html: true });

function withoutExplicitAdapters(body) {
  const lines = body.split('\n');
  const tokens = markdown.parse(body, {});
  const headings = [];

  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (token.type !== 'heading_open' || token.level !== 0 || !token.map) continue;

    const inline = tokens[index + 1];
    headings.push({
      level: Number(token.tag.slice(1)),
      start: token.map[0],
      text: inline?.type === 'inline' ? inline.content : '',
    });
  }

  const excludedLines = new Set();
  for (let index = 0; index < headings.length; index += 1) {
    const heading = headings[index];
    if (heading.level !== 3 || !/^Adapter:[ \t]+/u.test(heading.text)) continue;

    let end = lines.length;
    for (let next = index + 1; next < headings.length; next += 1) {
      if (headings[next].level <= heading.level) {
        end = headings[next].start;
        break;
      }
    }
    for (let line = heading.start; line < end; line += 1) excludedLines.add(line);
  }

  return lines.filter((_, index) => !excludedLines.has(index)).join('\n');
}

export function detectPathAssumptions(input) {
  const bodies = typeof input === 'string' ? [{ path: null, body: input }] : input;
  const defaultInstructions = bodies
    .map(({ path, body }) =>
      path === null || path.endsWith('.md') ? withoutExplicitAdapters(body) : body,
    )
    .join('\n');
  const findings = [];

  // The template ships beside SKILL.md at pdf-design/templates/. A path below
  // ~/.claude outside an explicit adapter couples the shared default to a Claude
  // install and fails for Codex or another standards-based client.
  if (new RegExp(`${HOME}/\\.claude/(?:plugins|skills)/`, 'u').test(defaultInstructions)) {
    findings.push({
      kind: 'claude-install-path',
      mappable: true,
      detail:
        'reads the bundled template from ~/.claude/plugins|skills/; resolve it relative to the installed skill directory and keep the Claude and Codex install locations as explicit adapters',
    });
  }

  // A snap-specific staging path outside an explicit adapter couples the shared
  // default to one browser package. That directory does not exist for a
  // non-snap Chrome, on macOS, or in a disposable CI working directory.
  if (new RegExp(`${HOME}/snap/chromium/`, 'u').test(defaultInstructions)) {
    findings.push({
      kind: 'snap-confined-browser',
      mappable: true,
      detail:
        'stages files in ~/snap/chromium/common/ for snap-confined Chromium; default to a disposable working directory for unconfined Chrome and keep the snap path in an explicit adapter',
    });
  }

  return findings;
}

// The kinds this detector can emit, for a test to assert against without
// repeating the strings.
export const PATH_ASSUMPTION_KINDS = ['claude-install-path', 'snap-confined-browser'];
