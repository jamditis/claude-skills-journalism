---
name: enforce-test-first
event: PreToolUse
tools:
  - Edit
  - Write
description: Blocks code edits during bug fixing until a test has been written
---

# Enforce test-first bug fixing

This hook checks whether Claude is attempting to fix a bug by editing source code before writing a test.

## Detection logic

Analyze the current conversation to determine:

1. **Is this a bug fix context?** — Has the user reported a bug, error, or requested a fix?
2. **Is this editing source code?** — Is the target file a source file (not a test file)?
3. **Has a test been written?** — Has Claude already created or modified a test file in this session?

## File classification

**Test files** (allowed during bug fix):
- `**/test_*.py`, `**/*_test.py`, `**/tests/**/*.py`
- `**/*.test.js`, `**/*.test.ts`, `**/*.test.jsx`, `**/*.test.tsx`
- `**/*.spec.js`, `**/*.spec.ts`, `**/*.spec.jsx`, `**/*.spec.tsx`
- `**/__tests__/**/*`
- `**/spec/**/*`
- `**/*_test.go`

**Source files** (blocked until test written):
- All other `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.go`, `.rs`, `.java`, etc.

## Hook behavior

### When to BLOCK (return error message)

Block Edit/Write to source files when ALL of these are true:
1. Conversation contains bug-related keywords (bug, broken, fix, error, crash, not working)
2. Target file is a source file (not a test file)
3. No test file has been modified yet in this session

**Block message:**
```
⚠️ TEST-FIRST WORKFLOW REQUIRED

Cannot edit source code before writing a failing test.

Per project guidelines, bug fixes must follow this order:
1. Write a failing test that reproduces the bug
2. Launch subagents to fix the bug
3. Verify with passing test

Please write a test first in one of these locations:
- tests/test_<module>.py
- __tests__/<module>.test.js
- <module>_test.go

Once a test file is modified, source edits will be allowed.
```

### When to ALLOW (return empty/success)

Allow the edit when ANY of these are true:
1. Target file is a test file
2. A test file has already been modified in this session
3. Conversation does NOT appear to be about bug fixing
4. User explicitly overrides with "skip test" or "no test needed"

## Session state tracking

Track in conversation context:
- `bug_fix_mode`: boolean — Is this session in bug-fix mode?
- `test_file_modified`: boolean — Has a test file been touched?
- `bug_keywords_detected`: list — Which bug indicators were found?

## Override phrases

Allow users to bypass when appropriate:
- "skip test", "no test", "skip the test"
- "just fix it", "quick fix"
- "refactoring" (not a bug fix)
- "typo" (trivial fix)

When override detected, allow edit but warn:
```
⚠️ Proceeding without test (user override). Consider adding a test later to prevent regression.
```

## Examples

### Example 1: Block source edit before test

**Conversation:**
> User: "The login function crashes when email has spaces"
> Claude: [attempts Edit on auth.py]

**Hook response:** BLOCK with test-first message

### Example 2: Allow test file edit

**Conversation:**
> User: "The login function crashes when email has spaces"
> Claude: [attempts Write on tests/test_auth.py]

**Hook response:** ALLOW (test file)

### Example 3: Allow source edit after test

**Conversation:**
> User: "The login function crashes when email has spaces"
> Claude: [wrote test to tests/test_auth.py] ✓
> Claude: [attempts Edit on auth.py]

**Hook response:** ALLOW (test already written)

### Example 4: Allow non-bug edit

**Conversation:**
> User: "Add a new endpoint for user profiles"
> Claude: [attempts Edit on routes.py]

**Hook response:** ALLOW (not a bug fix)

## Implementation notes

This is a **prompt-based hook** — Claude evaluates the conditions and decides whether to proceed or block. The hook content provides the decision criteria.

For reliable enforcement, this hook should:
1. Scan conversation history for bug indicators
2. Check if any test file paths appear in recent tool uses
3. Classify the target file as test or source
4. Apply the decision logic above
