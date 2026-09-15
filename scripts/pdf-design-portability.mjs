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

export const ROOT = fileURLToPath(new URL('..', import.meta.url));
export const SKILL_SUBDIR = 'pdf-design';

// Read every bundled text file under the skill directory. Path assumptions live
// in SKILL.md today, but a template, reference, or helper added later can carry
// the same coupling, so the detector reads the whole bundle rather than one
// file. Binary files (an og-image, a font) are skipped.
function readSkillBodies(root) {
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
      if (!bytes.includes(0)) bodies.push(bytes.toString('utf8'));
    }
  };
  walk(dir);
  return bodies;
}

// Filter every file on its own so an adapter at one file's end cannot exempt
// default instructions at the start of the next file.
export function readSkillBody(root = ROOT) {
  return readSkillBodies(root).map(withoutExplicitAdapters).join('\n');
}

// Each assumption is a concrete, greppable pattern paired with the adapter that
// makes it portable. `mappable: true` means an adapter exists; nothing here is
// Claude-only, because both couplings are about where files live, not about a
// Claude mechanic.
// A home-anchored path can be written tilde-style (~/x) or through the HOME
// variable ($HOME/x or ${HOME}/x). The detector recognizes all three spellings
// so a later edit cannot slip a coupling past the guard by swapping ~ for $HOME.
const HOME = '(?:~|\\$HOME|\\$\\{HOME\\})';

function withoutExplicitAdapters(body) {
  const keptLines = [];
  let inAdapter = false;
  let openFence = null;
  let previousLine = '';

  for (const line of body.split('\n')) {
    const fence = /^ {0,3}(`{3,}|~{3,})/u.exec(line)?.[1];
    const wasInFence = openFence !== null;

    if (!openFence && fence) {
      openFence = { character: fence[0], length: fence.length };
    } else if (openFence && fence?.[0] === openFence.character) {
      const closingFence = new RegExp(
        `^ {0,3}${openFence.character}{${openFence.length},}\\s*$`,
        'u',
      );
      if (closingFence.test(line)) openFence = null;
    }

    const outsideFence = !wasInFence && !fence;
    if (outsideFence) {
      const atxHeading = /^ {0,3}(#{1,3})(?:[ \t]+|$)/u.exec(line);
      const setextHeading =
        previousLine.trim() !== '' && /^ {0,3}(?:=+|-+)[ \t]*$/u.test(line);

      if (atxHeading) {
        inAdapter = /^ {0,3}###[ \t]+Adapter:[ \t]+/u.test(line);
      } else if (setextHeading) {
        inAdapter = false;
      }
    }
    if (!inAdapter) keptLines.push(line);
    previousLine = outsideFence ? line : '';
  }

  return keptLines.join('\n');
}

export function detectPathAssumptions(body) {
  const defaultInstructions = withoutExplicitAdapters(body);
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
