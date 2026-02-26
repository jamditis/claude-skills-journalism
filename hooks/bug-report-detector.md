---
name: bug-report-detector
event: UserPromptSubmit
description: Detects bug reports and reminds Claude to follow test-first workflow
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

When the user's message suggests they are reporting a bug or asking for a fix, remind Claude to follow the test-first bug fixing workflow.

## Detection criteria

The user message likely describes a bug if it contains:
- Direct bug language: "bug", "broken", "not working", "crash", "error"
- Fix requests: "fix", "repair", "solve", "resolve"
- Problem descriptions: "issue", "problem", "wrong", "unexpected behavior"
- Failure indicators: "fails", "failing", "failed", "doesn't work"

## Response

When a bug report is detected, prepend this reminder to Claude's context:

---

**🐛 Bug report detected — Follow test-first workflow:**

1. **DO NOT** immediately edit code to fix the bug
2. **FIRST** write a failing test that reproduces the bug
3. **THEN** launch subagents via Task tool to attempt fixes
4. **VERIFY** by running the test — passing test proves the fix works

This workflow is required per project CLAUDE.md guidelines.

---

## Non-blocking

This hook provides guidance but does not block any tools. The `enforce-test-first` hook handles enforcement.
