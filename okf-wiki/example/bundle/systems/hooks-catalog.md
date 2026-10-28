---
type: Reference
title: "the hooks catalog"
description: "Seventeen standalone workflow hooks under hooks/, grouped by purpose, including a Stop guard for prose questions."
source: ["hooks/", "AGENTS.md"]
verified: 2026-10-28
timestamp: 2026-10-28
tags: [hooks, catalog]
---
# the hooks catalog

The `hooks/` directory holds 17 optional workflow hooks. Each has a Markdown
reference with frontmatter naming its `event` and, for tool hooks, its `tools`.
Command hooks also have executable implementations. After installation, they run
at events such as writing, editing, submitting a prompt, stopping, or session start.

Most are **non-blocking warnings**: they surface guidance without stopping the
action. Two block until resolved: `one-way-door-check` (a shell hook that exits 2
on an irreversible-decision file until confirmed) and `no-ai-attribution` (denies a
commit, PR, or comment that carries AI authorship credit). `pre-commit-review`
surfaces the staged diff before a commit. `prose-question-guard` blocks a stop
once to move a possible prose question into `AskUserQuestion`. Its Python 3
implementation supports Windows, macOS, and Linux.

They group into six purposes: writing quality, verification, editorial workflow,
preservation, interaction, and development. Browse every hook in the [hooks section](../hooks/index.md).
These standalone hooks are separate from the OKF
[session-start hooks](session-hooks.md) the okf-wiki scaffolder writes.
