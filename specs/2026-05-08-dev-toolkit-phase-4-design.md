# Phase 4 — dev-toolkit plugin (10 skills)

**Status:** draft, 2026-05-08
**Branch:** `package/dev-toolkit-phase4`
**Mirrors:** [Phase 3 research-toolkit, PR #62](https://github.com/jamditis/claude-skills-journalism/pull/62) (merged `b7de6a2`)

## Goal

Bundle 10 development-themed bare skills into a new `dev-toolkit` Marketplace plugin with a full Phase 3-style currency sweep and codex/Copilot review-loop quality gating.

## Scope

The 10 skills bundled in this phase:

| Skill | Theme | High-likelihood drift |
|---|---|---|
| accessibility-compliance | a11y | WCAG 2.2 baseline, `prefers-reduced-motion`, ARIA Authoring Practices |
| electron-dev | platform | Electron 30+ contextIsolation/sandbox, BrowserView → WebContentsView |
| mobile-debugging | debugging | Eruda 3.x, Chrome DevTools Protocol on Android, iOS Safari Inspector |
| one-way-door | discipline | mostly stable, light touch |
| python-pipeline | data | Python 3.13+, pandas vs polars, DuckDB, asyncio TaskGroup |
| test-first-bugs | discipline | pytest-watcher, mostly stable |
| vibe-coding | AI workflow | Claude Code / Cursor / Aider / Continue landscape (high-drift) |
| web-scraping | data | Playwright 1.50+, Cloudflare bot defense, anti-bot ethics |
| web-ui-best-practices | UI | container queries stable, `:has()`, view transitions, scroll-driven animations |
| zero-build-frontend | UI | ESM import maps, htmx 2.0, Alpine.js current |

## Out of scope

- Creating new skills.
- Refactoring beyond currency (no rewriting working content for style alone).
- Changes to other plugins (autocontext, journalism-core, pdf-design, pdf-playground, research-toolkit, superjawn).

## Architecture

Mirrors `research-toolkit/` exactly. New top-level dir + git mv:

```
dev-toolkit/
├── .claude-plugin/plugin.json   # v1.0.0
├── README.md                     # skill table + install notes
└── skills/
    ├── accessibility-compliance/SKILL.md
    ├── electron-dev/SKILL.md
    ├── mobile-debugging/SKILL.md
    ├── one-way-door/SKILL.md
    ├── python-pipeline/SKILL.md
    ├── test-first-bugs/SKILL.md
    ├── vibe-coding/SKILL.md
    ├── web-scraping/SKILL.md
    ├── web-ui-best-practices/SKILL.md
    └── zero-build-frontend/SKILL.md
```

Updated files:
- `.claude-plugin/marketplace.json` → bump to v1.5.0, add `dev-toolkit` entry alphabetically (between `autocontext` and `journalism-core`), category `Development`.
- `CLAUDE.md` → add `# Plugin: dev-toolkit (10 skills)` section after research-toolkit; remove the "# Development (10)" bare section; update install examples.
- `README.md` (top-level) → add row to plugins table; replace "Bare development skills" section with "Development skills (in dev-toolkit plugin)" pointing to nested paths.

## Branch + commit shape

- Branch: `package/dev-toolkit-phase4`
- Sequence:
  1. Structural commit: scaffold + 10x git mv + marketplace bump + doc updates.
  2. 10 per-skill currency sweep commits in alphabetical order (one per skill).
  3. Codex review #1 fix commit(s) addressing the cross-skill review of the full sweep.
  4. PR opened. Copilot review fires once.
  5. Copilot fix commit(s).
  6. Codex review #2/#3/... loop until convergence (no new findings).
- Squash merge after Joe's explicit "merge".
- Estimated 16-22 commits on branch before squash. Phase 3 produced 11 commits for 5 skills; Phase 4 scales linearly.

## Quality gates

| Gate | Mechanism |
|---|---|
| Plugin structure validity | GitHub Actions `check-readme` and `lint-skills` (existing) |
| Pre-PR cross-skill review | `codex exec` against the full branch after sweep commits land |
| External code review | Copilot PR-bot review (one-shot per PR — no re-trigger) |
| Post-Copilot review | `codex exec` against the Copilot-fix commit |
| Convergence | Recursive codex reviews until a round returns NO ISSUES FOUND |
| Final | Squash merge after Joe's explicit "merge" instruction |

## Risks + mitigations

- **vibe-coding currency drift.** The AI-coding tool landscape changes monthly. Mitigation: scope the sweep to "what's accurate as of 2026-05" with explicit dated language so the next phase knows when to re-sweep.
- **electron-dev relevance.** Smaller audience than other dev skills. Mitigation: keep currency-only; do not over-invest if the skill's content is already accurate.
- **10 skills × codex/Copilot recursion.** Phase 3's 5-skill sweep produced 4 review rounds and 13 distinct bugs. Phase 4 may exceed that. Mitigation: cap at 5 codex review rounds; if a 6th round still surfaces real bugs, pause and re-scope rather than push through.
- **bare-skill consumers.** Users who installed bare skills via `cp -r web-scraping ~/.claude/skills/` will need to re-install from the nested path. Mitigation: top-level README's install examples updated; CLAUDE.md install examples updated; no symlink shim (Phase 3 didn't ship one either).

## Acceptance criteria

- `dev-toolkit` plugin appears in `.claude-plugin/marketplace.json` with v1.0.0 and category `Development`.
- All 10 skills moved under `dev-toolkit/skills/<skill>/SKILL.md` with git rename history preserved (similarity ≥50%).
- Each skill's content sweep documented in commit message.
- CI green on the merge commit.
- Final codex review round returns NO ISSUES FOUND.
- PR squash-merged after Joe's "merge".

## Skipped research

Skipped formal brainstorming research phase because Phase 4 is structurally identical to Phase 3 (research-toolkit), which merged today as `b7de6a2`. Pointer: PR #62. The pattern (single PR, structural + per-skill sweeps, codex/Copilot review loop, squash merge) is fresh muscle memory.
