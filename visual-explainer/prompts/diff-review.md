---
name: diff-review
description: Generate a visual diff review with architecture comparison, code review, and decision log
---

Generate a visual HTML diff review following the visual-explainer skill.

## Scope

Determine the diff scope from `$ARGUMENTS`:
- No arguments: current branch vs `main`
- Branch name: that branch vs `main`
- Commit hash: that single commit
- Range (`main..HEAD`): committed changes only
- PR number (`#42`): that pull request

## Data gathering

1. Run `git diff --stat` for file-level statistics
2. Categorize files: new / modified / deleted
3. Read changed files for full context
4. Identify new public APIs, changed interfaces
5. Check if CHANGELOG and README reflect changes

## HTML sections (10 required)

1. **Executive summary** — why these changes exist, factual scope (hero typography, 20-24px)
2. **KPI dashboard** — files changed, lines added/removed, test coverage status
3. **Module architecture** — before/after dependency graphs (Mermaid with zoom controls)
4. **Feature comparisons** — side-by-side before/after panels
5. **Flow diagrams** — Mermaid visualizations of new patterns
6. **File map** — color-coded file tree showing change types
7. **Test coverage** — test file analysis, coverage gaps
8. **Code review** — structured Good/Bad/Ugly assessment
9. **Decision log** — design choices with rationale and confidence levels
10. **Re-entry context** — invariants, coupling notes, gotchas for future readers

## Visual treatment

- Sections 1-4: hero depth, dominant viewport
- Sections 5-7: elevated, standard
- Sections 8-10: flat/recessed, collapsible, reference material
- Choose a distinctive aesthetic — read reference templates before generating

Write to `~/.agent/diagrams/` and open in browser.
