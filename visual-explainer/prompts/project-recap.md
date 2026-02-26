---
name: project-recap
description: Generate a visual project recap for context-switching back to a project
---

Generate a visual HTML project recap following the visual-explainer skill.

## Time window

Parse `$ARGUMENTS` for time range shorthand: `2w` (2 weeks), `30d`, `3m`. Default: `2w`.
Convert to git's `--since` format.

## Data gathering

1. Harvest project identity from README, package.json, CLAUDE.md, or similar manifests
2. Extract recent activity via `git log --since=<window>` — commits, authors, changed files
3. Assess current state: uncommitted changes, stale branches, open TODOs
4. Document decision rationale from commit messages, comments, and planning docs

## Verification checkpoint

Before generating HTML, produce a fact sheet citing sources for every quantitative claim and architectural reference. Cross-verify against actual code.

## HTML sections (8 required)

1. **Project identity** — name, purpose, tech stack, team (hero card)
2. **Architecture diagram** — current system overview (Mermaid with zoom/pan controls)
3. **Activity narrative** — themed summary of recent work, not just a commit log
4. **Decision log** — key choices made during the time window with rationale
5. **Status dashboard** — KPI cards: commits, files changed, open issues, test status
6. **Mental model essentials** — the 3-5 things you need to remember to work on this project
7. **Cognitive debt hotspots** — areas of accumulated complexity, with severity indicators
8. **Inferred next steps** — what logically follows from recent activity

## Visual treatment

- Warm, muted palette with blues/greens, amber callouts for debt hotspots
- Architecture diagram as visual anchor
- Responsive navigation, overflow protection, accessibility throughout

Write to `~/.agent/diagrams/` and open in browser.
