---
name: autocontext-pre-tool-use
description: Inject relevant project lessons before Edit/Write/Bash tool calls
hooks:
  - event: PreToolUse
    type: prompt
    matcher: "Edit|Write|Bash"
---

First, check the injection mode. Read `.autocontext/config.json` and look at the `pretooluse_hook` field:
- If `"disabled"` or `false`: do nothing, return no warnings.
- If `"errors_only"`: only inject warnings for lessons whose category is `"codebase"` or whose tags contain `"bug"`, `"error"`, `"breaking"`, or `"regression"`.
- If `"enabled"` or `true` or missing: inject all relevant warnings (default behavior).

Check if any lessons from `.autocontext/cache/session-lessons.json` are relevant to this tool call. If the file being edited or the command being run matches a lesson's tags or context, inject a brief warning.

For test files (files in `tests/` or `__tests__/` directories, or files ending in `_test.py`, `.test.ts`, `.test.js`, `.spec.ts`, `.spec.js`, or named `test_*.py`), also check:
- Are assertions based on desired behavior (from the task/spec), not current implementation output?
- Is there at least one error/edge case, not just the happy path?
- Would this test fail if the feature broke?
- Are mocked return values being used as the expected assertions?

Only inject warnings when genuinely relevant. Do not warn on every tool call. Cap at 3 warnings.
