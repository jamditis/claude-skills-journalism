---
type: Reference
title: "one-way-door-check hook"
description: "Blocks creation of files that represent irreversible architectural decisions until the user confirms."
source: ["hooks/one-way-door-check.md", "CLAUDE.md"]
verified: 2026-06-26
timestamp: 2026-06-26
tags: ["hook", "development"]
---
# one-way-door-check hook

Blocks creation of files that represent irreversible architectural decisions until the
user confirms. Requires the companion PostToolUse:AskUserQuestion hook (one-way-door-
approve), which promotes the session's pending files to approved so the retry passes —
install both, not just this check.

**Event:** `PreToolUse`  |  **Tools:** Write  |  **Category:** Development

One of the repository's standalone [hooks](index.md). Source: `hooks/one-way-door-check.md`.
