---
type: Reference
title: "director skill"
description: "Direct one request through the lower-tier agents configured in the applicable policy."
source: ["dev-toolkit/skills/director/SKILL.md", ".claude-plugin/marketplace.json"]
verified: 2026-08-21
timestamp: 2026-08-21
tags: ["skill", "dev-toolkit"]
---
# director skill

Activate an explicit top-tier director role for one request. The director reads
the applicable `CLAUDE.md` policy, delegates execution to the lower-tier agents
configured there, reviews their results, and stays within the user's authority.

Part of the [dev-toolkit plugin](../plugins/dev-toolkit.md). Source: `dev-toolkit/skills/director/SKILL.md`.
