---
name: plan-review
description: Compare an implementation plan against the codebase with risk assessment
---

Generate a visual HTML plan review following the visual-explainer skill.

## Inputs

- Plan file: `$1` (required)
- Codebase: `$2` (defaults to current directory)

## Data gathering

1. Read the plan file completely — problem statement, proposed changes, alternatives, scope
2. Read every file referenced in the plan
3. Map blast radius: imports, tests, configs, public APIs affected
4. Cross-reference plan claims against actual code

## Verification checkpoint

Before generating HTML, create a fact sheet:
- Quantitative figures (file counts, line estimates) with sources
- Function/type/module names — plan vs actual code
- Current vs proposed behavior descriptions
- Citations for every claim

## HTML sections (9 required)

1. **Plan summary** — problem statement, core insight, scope overview (hero typography)
2. **Impact dashboard** — files modified/created/deleted, line estimates, test/dependency status
3. **Current architecture** — Mermaid diagram of affected subsystem today (zoom controls required)
4. **Planned architecture** — Mermaid diagram post-implementation (matching layout, highlight changes)
5. **Change-by-change breakdown** — side-by-side panels (current left, planned right, rationale below)
6. **Dependency and ripple analysis** — callers/importers, collapsible details, color-coded coverage
7. **Risk assessment** — cards for edge cases, assumptions, rollback complexity, mitigation suggestions
8. **Plan review** — Good/Bad/Ugly/Questions with colored left-border cards
9. **Understanding gaps** — changes without rationale, complexity flags, pre-implementation recommendations

## Visual treatment

- Sections 1-4: hero/elevated depth, dominate initial viewport
- Sections 5+: flat/recessed, compact, collapsible
- Colors: blue/neutral (current), green/purple (planned), amber (concerns), red (gaps)

Write to `~/.agent/diagrams/` and open in browser.
