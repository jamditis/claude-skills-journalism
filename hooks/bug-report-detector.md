---
name: bug-report-detector
event: UserPromptSubmit
description: Detects bug reports and reminds Claude to establish the failure before fixing it
match_patterns:
  - "bug"
  - "broken"
  - "not working"
  - "doesn't work"
  - "failed"
  - "failing"
  - "error"
  - "crash"
  - "fix"
  - "issue"
  - "problem"
  - "wrong"
  - "unexpected"
---

# Bug report detection

When the user's message suggests they are reporting a bug or asking for a fix, remind Claude to establish the failure with evidence before it changes code.

## Detection criteria

The user message likely describes a bug if it contains:
- Direct bug language: "bug", "broken", "not working", "crash", "error"
- Fix requests: "fix", "repair", "solve", "resolve"
- Problem descriptions: "issue", "problem", "wrong", "unexpected behavior"
- Failure indicators: "fails", "failing", "failed", "doesn't work"

## Response

When a bug report is detected, prepend this reminder to Claude's context:

---

**Bug report detected. Establish the failure first:**

1. Reproduce the bug with the cheapest faithful evidence: an existing test, a focused command, a log, or a new failing test.
2. Confirm that it fails for the reported reason.
3. Fix the cause, not the symptom.
4. Prove the fix with the same evidence.
5. Keep a new regression test only when the bug is likely to recur or affects an important contract, non-obvious logic, or high-impact behavior.

---

## Non-blocking

This hook provides guidance but does not block any tools.
