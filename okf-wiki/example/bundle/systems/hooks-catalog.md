---
type: Reference
title: "the hooks catalog"
description: "Sixteen standalone workflow hooks under hooks/, grouped by purpose; two block intentionally."
source: ["hooks/", "CLAUDE.md"]
verified: 2026-06-26
timestamp: 2026-06-26
tags: [hooks, catalog]
---
# the hooks catalog

The `hooks/` directory holds 16 single-file workflow hooks, each a markdown
instruction set with frontmatter naming its `event` and (for tool hooks) its
`tools`. They run automatically at workflow events — writing, editing, submitting
a prompt, stopping, or session start.

Most are **non-blocking warnings**: they surface guidance without stopping the
action. Two block intentionally — `one-way-door-check` (a shell hook that exits 2
on an irreversible-decision file until confirmed) and `enforce-test-first` (gates
source edits until a failing test exists). `pre-commit-review` surfaces the staged
diff before a commit.

They group into five purposes: writing quality, verification, editorial workflow,
preservation, and development. Browse every hook in the [hooks section](../hooks/index.md).
These standalone hooks are separate from the OKF
[session-start hooks](session-hooks.md) the okf-wiki scaffolder writes.
