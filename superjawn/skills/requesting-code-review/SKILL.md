---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements
---
<!--
Adapted from obra/superpowers requesting-code-review skill (v5.0.7),
MIT-licensed, copyright 2025 Jesse Vincent. Modifications copyright 2026 Joe Amditis. v0.4.0 ports as a consumer category, no research
phase per the v0.2.0 architecture, since dispatch mechanic; reviewer
preferences live in the project instruction file and memory rather than a research phase.
See CREDITS.md.
-->

# Requesting Code Review

Dispatch a code-review subagent or parallel worker, if your client supports one, to catch issues before they cascade. In Claude Code, dispatch `pr-review-toolkit:code-reviewer`. Give the reviewer precise context instead of the full session history. This keeps the reviewer focused on the work product, not your thought process, and preserves your own context for continued work. If the client has no worker capability, perform the same review in sequence in a fresh review pass.

**Core principle:** Review early, review often.

**Independence rule:** Before merge, the independent review comes from a model provider other than the one that wrote the code. Scale the reviewer's effort to risk: low for a trivial change, high for behavior, security, data, or broad changes. A same-provider review can still catch issues during a task, but it does not count as the independent review.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Dispatch code-reviewer subagent:**

Use the client's worker capability and fill the template at `code-reviewer.md`. In Claude Code, use the Task tool with `pr-review-toolkit:code-reviewer`.

**Placeholders:**
- `{WHAT_WAS_IMPLEMENTED}` - What you just built
- `{PLAN_OR_REQUIREMENTS}` - What it should do
- `{BASE_SHA}` - Starting commit
- `{HEAD_SHA}` - Ending commit
- `{DESCRIPTION}` - Brief summary

**3. Pin the snapshot:**

Record the base, head, changed paths, and a diff digest. Ask the reviewer to repeat them. Discard a result that covers a different snapshot. If you change the code after review, the old result no longer covers the head.

**4. Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with reasoning)
- After fixes, run a focused verify-fixes pass on the new snapshot with the same reviewer

Do not switch reviewers because the first one found problems or returned malformed output. Switch only when the reviewer's provider is unavailable. There is no cap on review rounds; stop when the reviewer finds no actionable defect in the exact head.

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch a code-review worker from a different provider]
  WHAT_WAS_IMPLEMENTED: Verification and repair functions for conversation index
  PLAN_OR_REQUIREMENTS: Task 2 from docs/superpowers/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types

[Subagent returns]:
  Strengths: Clean architecture, real tests
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Assessment: Ready to proceed

You: [Fix progress indicators]
[Continue to Task 3]
```

## Integration with Workflows

**Subagent-Driven Development:**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to next task

**Executing Plans:**
- Review after each batch (3 tasks)
- Get feedback, apply, continue

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

See template at: requesting-code-review/code-reviewer.md

## Reference files

Read [Cross-provider code review](references/cross-provider-review.md) when an independent reviewer must verify a completed change.
