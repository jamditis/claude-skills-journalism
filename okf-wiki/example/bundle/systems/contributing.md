---
type: Process
title: "contributing a skill"
description: "How to add a skill, hook, or plugin: directory layout, SKILL.md frontmatter, and the house style."
source: ["CONTRIBUTING.md", "CLAUDE.md"]
verified: 2026-06-26
timestamp: 2026-06-26
tags: [contributing, authoring]
---
# contributing a skill

A skill is a directory with a `SKILL.md` carrying `name` and `description`
frontmatter, plus optional `templates/`, `examples/`, and `scripts/`. The
`description` is what Claude matches on to activate the skill, so it should name
specific trigger conditions. Skills now live inside a plugin at
`<plugin>/skills/<skill-name>/SKILL.md`; single-skill plugins keep `SKILL.md` at
the plugin root.

A hook is a single markdown file in `hooks/` with `event` (and `tools` for
Pre/PostToolUse hooks) frontmatter, see [the hooks catalog](hooks-catalog.md).

House style, enforced by review and the writing hooks: sentence-case headings,
terse and actionable descriptions, cited sources, and no AI writing patterns (the
`ai-writing-detox` skill lists the banned words). After adding a skill, register
its plugin in [the marketplace](marketplace.md) and update the docs site. Validate
any OKF wiki changes with [the OKF format](okf-format.md) validator and the
[tests](testing.md).
