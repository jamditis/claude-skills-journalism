---
type: Reference
title: "pre-commit-review hook"
description: "Surface the staged diff for line-by-line review before a commit, and flag deletions of safety-critical guardrails"
source: ["hooks/pre-commit-review.md", "CLAUDE.md"]
verified: 2026-06-26
timestamp: 2026-06-26
tags: ["hook", "development"]
---
# pre-commit-review hook

Surface the staged diff for line-by-line review before a commit, and flag deletions of
safety-critical guardrails

**Event:** `PreToolUse`  |  **Tools:** Bash  |  **Category:** Development

One of the repository's standalone [hooks](index.md). Source: `hooks/pre-commit-review.md`.
