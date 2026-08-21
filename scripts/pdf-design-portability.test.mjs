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
// portable skill must satisfy (#235 AC1).
const PORTABLE_FIXTURE = `
Copy the bundled template from the skill's own directory:
    cp "$SKILL_DIR/templates/democracy-day-proposal.html" ./new-report.html

Render it with a disposable working directory:
    WORK_DIR="$(mktemp -d)"
    cp new-report.html "$WORK_DIR/"
    chromium --headless --disable-gpu \\
      --print-to-pdf="$WORK_DIR/output.pdf" \\
      "file://$WORK_DIR/new-report.html"
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

test('inventories the current skill from the repository, not a hard-coded list (#235 AC2)', () => {
  const findings = detectPathAssumptions(readSkillBody());
  // The skill as committed carries exactly the two known couplings.
  assert.deepEqual(findings.map((f) => f.kind).sort(), [...PATH_ASSUMPTION_KINDS].sort());
});

// The portable end state (#235 AC3): once the default instructions resolve the
// template relative to the skill and stage the browser in a disposable dir, the
// live skill carries no path assumptions. It does today, so this is a todo --
// it documents the failing fixture against the current skill without reddening
// CI. Drop the `todo` when the SKILL.md rewrite lands.
test(
  'the committed pdf-design default resolves paths portably (#235 AC3)',
  { todo: '#235: SKILL.md default still hardcodes ~/.claude/plugins and ~/snap/chromium' },
  () => {
    assert.deepEqual(detectPathAssumptions(readSkillBody()), []);
  },
);
