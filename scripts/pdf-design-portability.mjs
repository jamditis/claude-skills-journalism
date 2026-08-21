// Detect maintainer-specific path assumptions in the pdf-design skill, so the
// portability work in #235 has a guard to fix against rather than a prose
// inventory that drifts. The skill body is read from the repository, not
// hard-coded, and each finding names the adapter that makes it portable --
// mirroring the { kind, mappable, detail } signal shape that
// dev-toolkit-portability.mjs already uses.
//
// The intent (issue #235) is to land this detector and its test BEFORE
// rewriting the shared SKILL.md instructions, so the rewrite can be checked
// rather than trusted.

import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = fileURLToPath(new URL('..', import.meta.url));
export const SKILL_SUBDIR = 'pdf-design';

// Read every bundled text file under the skill directory. Path assumptions live
// in SKILL.md today, but a template, reference, or helper added later can carry
// the same coupling, so the detector reads the whole bundle rather than one
// file. Binary files (an og-image, a font) are skipped.
export function readSkillBody(root = ROOT) {
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
  return bodies.join('\n');
}

// Each assumption is a concrete, greppable pattern paired with the adapter that
// makes it portable. `mappable: true` means an adapter exists; nothing here is
// Claude-only, because both couplings are about where files live, not about a
// Claude mechanic.
// A home-anchored path can be written tilde-style (~/x) or through the HOME
// variable ($HOME/x or ${HOME}/x). The detector recognizes all three spellings
// so a later edit cannot slip a coupling past the guard by swapping ~ for $HOME.
const HOME = '(?:~|\\$HOME|\\$\\{HOME\\})';

export function detectPathAssumptions(body) {
  const findings = [];

  // The template ships beside SKILL.md at pdf-design/templates/, but the default
  // copy step reads it from ~/.claude/plugins/pdf-design/templates/, a path that
  // only exists on a Claude plugin install. A Codex or standards-based install
  // puts the skill somewhere else and has no ~/.claude at all, so the copy fails
  // before the skill does any work.
  if (new RegExp(`${HOME}/\\.claude/(?:plugins|skills)/`, 'u').test(body)) {
    findings.push({
      kind: 'claude-install-path',
      mappable: true,
      detail:
        'reads the bundled template from ~/.claude/plugins|skills/; resolve it relative to the installed skill directory and keep the Claude and Codex install locations as explicit adapters',
    });
  }

  // Chromium under snap confinement can only read and write
  // ~/snap/chromium/common/, so the default PDF and preview steps stage files
  // there. That directory does not exist for a non-snap Chrome, on macOS, or in
  // a disposable CI working directory.
  if (new RegExp(`${HOME}/snap/chromium/`, 'u').test(body)) {
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
