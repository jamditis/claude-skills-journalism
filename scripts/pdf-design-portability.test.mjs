import assert from 'node:assert/strict';
import test from 'node:test';

import {
  detectPathAssumptions,
  readSkillBody,
  PATH_ASSUMPTION_KINDS,
} from './pdf-design-portability.mjs';

// A portable pdf-design body: the template is resolved relative to the installed
// skill and the browser stages files in a disposable working directory. No
// ~/.claude and no snap path, so it runs on a Codex or standards-based install
// with no Claude present. This is the no-Claude path-resolution fixture the
// portable skill must satisfy (#235 AC1). SKILL_DIR is provided by the skill
// runtime; the fallback derivation keeps the example runnable on its own so it
// models a working portable strategy, not a broken one.
const PORTABLE_FIXTURE = `
Resolve the skill's own directory (the runtime sets SKILL_DIR; derive it if not):
    SKILL_DIR="\${SKILL_DIR:-$(cd "$(dirname "$0")" && pwd)}"

Copy the bundled template from that directory:
    cp "$SKILL_DIR/templates/democracy-day-proposal.html" ./new-report.html

Render it with a disposable working directory:
    WORK_DIR="$(mktemp -d)"
    cp new-report.html "$WORK_DIR/"
    chromium --headless --disable-gpu \\
      --print-to-pdf="$WORK_DIR/output.pdf" \\
      "file://$WORK_DIR/new-report.html"
`;

// A frozen snapshot of the pdf-design default as it couples to the maintainer's
// machine today: the template read from a Claude plugin path and the browser
// staged under snap confinement. AC2 pins the detector's inventory against this
// legacy body rather than the live skill, so the inventory assertion stays true
// after the #235 rewrite makes the live skill portable (when AC3 flips green).
const LEGACY_COUPLED_FIXTURE = `
    cp ~/.claude/plugins/pdf-design/templates/democracy-day-proposal.html ./new-report.html
    mkdir -p ~/snap/chromium/common/pdf-work
    cp new-report.html ~/snap/chromium/common/pdf-work/
    chromium --headless --print-to-pdf=~/snap/chromium/common/pdf-work/output.pdf \\
      "file://$HOME/snap/chromium/common/pdf-work/new-report.html"
`;

test('detects nothing in a portable, no-Claude skill body (#235 AC1)', () => {
  assert.deepEqual(detectPathAssumptions(PORTABLE_FIXTURE), []);
});

test('flags each maintainer-specific path assumption independently', () => {
  const claudeOnly = detectPathAssumptions(
    'cp ~/.claude/plugins/pdf-design/templates/democracy-day-proposal.html ./new-report.html',
  );
  assert.deepEqual(
    claudeOnly.map((f) => f.kind),
    ['claude-install-path'],
  );

  const snapOnly = detectPathAssumptions(
    'mkdir -p ~/snap/chromium/common/pdf-work && cp template.html "$HOME/snap/chromium/common/pdf-work/"',
  );
  assert.deepEqual(
    snapOnly.map((f) => f.kind),
    ['snap-confined-browser'],
  );

  // Every finding names an adapter, so none is a dead end.
  for (const finding of [...claudeOnly, ...snapOnly]) {
    assert.equal(finding.mappable, true);
    assert.ok(finding.detail.length > 0);
  }
});

test('recognizes $HOME and ${HOME} spellings, not only the tilde', () => {
  // A coupling written through the HOME variable is still a coupling; the guard
  // must not be evadable by swapping ~ for $HOME (or ${HOME}).
  for (const home of ['$HOME', '${HOME}']) {
    assert.deepEqual(
      detectPathAssumptions(`cp ${home}/.claude/plugins/pdf-design/templates/x.html .`).map(
        (f) => f.kind,
      ),
      ['claude-install-path'],
      `claude path via ${home}`,
    );
    assert.deepEqual(
      detectPathAssumptions(`mkdir -p ${home}/snap/chromium/common/pdf-work`).map((f) => f.kind),
      ['snap-confined-browser'],
      `snap path via ${home}`,
    );
  }
});

test('inventories a coupled skill body, not a hard-coded list (#235 AC2)', () => {
  const findings = detectPathAssumptions(LEGACY_COUPLED_FIXTURE);
  // The detector reports exactly the two known couplings, and it derives them
  // from the body it is handed rather than a hard-coded list.
  assert.deepEqual(findings.map((f) => f.kind).sort(), [...PATH_ASSUMPTION_KINDS].sort());
});

// The portable end state (#235 AC3): once the default instructions resolve the
// template relative to the skill and stage the browser in a disposable dir, the
// live skill carries no path assumptions. It does today, so this is a todo --
// it reads the real committed skill and documents the failing fixture against it
// without reddening CI. Drop the `todo` when the SKILL.md rewrite lands, and the
// AC2 inventory above stays green because it pins the frozen legacy body.
test(
  'the committed pdf-design default resolves paths portably (#235 AC3)',
  { todo: '#235: SKILL.md default still hardcodes ~/.claude/plugins and ~/snap/chromium' },
  () => {
    assert.deepEqual(detectPathAssumptions(readSkillBody()), []);
  },
);
