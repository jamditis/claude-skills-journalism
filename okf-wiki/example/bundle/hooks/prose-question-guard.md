---
type: Reference
title: "prose-question-guard hook"
description: "Nudge prose questions into AskUserQuestion at the end of a Claude Code turn"
source: ["hooks/prose-question-guard.md", "hooks/prose-question-guard.py", "AGENTS.md"]
verified: 2026-10-28
timestamp: 2026-10-28
tags: ["hook", "interaction"]
---
# prose-question-guard hook

Checks the final reply for possible questions and asks Claude to use
`AskUserQuestion`. Blocks a stop once, then allows a stop with
`stop_hook_active` to prevent a loop.

**Event:** `Stop` | **Runtime:** Python 3 on Windows, macOS, and Linux | **Category:** Interaction

One of the repository's standalone [hooks](index.md). Install manually from
`hooks/prose-question-guard.md`. The [public guide](https://skills.amditis.tech/prose-question-guard/)
includes platform-specific setup and an example of false-positive recovery.
