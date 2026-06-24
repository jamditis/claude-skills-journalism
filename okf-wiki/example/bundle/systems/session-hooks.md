---
type: Reference
title: "session-start hooks"
description: "Two hooks that orient Claude on an OKF bundle before it works."
source: ["okf-wiki/templates/hooks/okf-anchor.py", "okf-wiki/templates/hooks/okf-orient.py"]
verified: 2026-06-23
timestamp: 2026-06-23
tags: [okf, hooks]
---
# session-start hooks

A scaffolded bundle ships two hooks. `okf-anchor.py` (SessionStart) loads the
bundle index into the session context. `okf-orient.py` (PreToolUse) blocks the
first action once per session until Claude confirms it has read the index, then
unblocks. Both are one cross-platform python3 script; only the launch command in
`.claude/settings.json` differs per OS. They belong to the
[okf-wiki plugin](../plugins/okf-wiki.md).
