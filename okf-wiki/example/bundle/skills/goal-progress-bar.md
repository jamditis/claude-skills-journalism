---
type: Reference
title: "goal-progress-bar skill"
description: "Weighted progress with evidence, scope guidance, and completion safeguards."
source: ["project-templates-toolkit/skills/goal-progress-bar/SKILL.md", ".claude-plugin/marketplace.json"]
verified: 2026-10-28
timestamp: 2026-10-28
tags: ["skill", "project-templates-toolkit"]
---
# goal-progress-bar skill

Render weighted progress for multi-step work from a JSON tracker. A script computes the
percentage and bar from weighted rows and updates them from recorded evidence, so nobody
hand-types a number. Rows that prove the work in real use come last, and blocked rows are
marked rather than removed. The renderer rejects invalid or contradictory inputs and prevents rounding from displaying unfinished work as 100%. A linked reference explains evidence, scope changes, and revalidation.

Part of the [project-templates-toolkit plugin](../plugins/project-templates-toolkit.md). Source: `project-templates-toolkit/skills/goal-progress-bar/SKILL.md`.
