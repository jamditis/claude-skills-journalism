---
type: Reference
title: "the hooks catalog"
description: "Seventeen standalone workflow hooks under hooks/, grouped by purpose; three block intentionally."
source: ["hooks/", "CLAUDE.md"]
verified: 2026-06-30
timestamp: 2026-06-30
tags: [hooks, catalog]
---
# the hooks catalog

The `hooks/` directory holds 17 single-file workflow hooks, each a markdown
instruction set with frontmatter naming its `event` and (for tool hooks) its
`tools`. They run automatically at workflow events, writing, editing, submitting
a prompt, stopping, or session start.

Most are **non-blocking warnings**: they surface guidance without stopping the
action. Three block intentionally, `one-way-door-check` (a shell hook that exits 2
on an irreversible-decision file until confirmed), `enforce-test-first` (gates
source edits until a failing test exists), and `no-ai-attribution` (denies a
commit, PR, or comment that carries AI authorship credit). `pre-commit-review`
surfaces the staged diff before a commit.

They group into five purposes: writing quality, verification, editorial workflow,
preservation, and development. Browse every hook in the [hooks section](../hooks/index.md).
These standalone hooks are separate from the OKF
[session-start hooks](session-hooks.md) the okf-wiki scaffolder writes.
