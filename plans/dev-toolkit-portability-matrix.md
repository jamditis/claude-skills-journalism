# dev-toolkit per-skill portability

How far each dev-toolkit skill is from running under Codex instead of
Claude Code. Generated from the repository by the classifier; do not edit by
hand. Regenerate with `node scripts/dev-toolkit-portability.mjs`.

Classes: **shared** runs as written; **adapter-required** needs a documented
Codex mapping (instruction file, tool vocabulary, or hook); **Claude-only**
depends on a Claude runtime mechanic with no Codex equivalent.

Inventory: 12 skills discovered from `dev-toolkit/skills` (9 shared, 3 adapter-required, 0 Claude-only).

| Skill | Class | Auto-activation | Reason |
| --- | --- | --- | --- |
| `accessibility-compliance` | shared | no | No Claude-specific mechanic; runs under Codex as written. |
| `claude-md-updater` | adapter-required | no | Targets CLAUDE.md; map the instruction file to AGENTS.md for Codex. |
| `context-engineering-fundamentals` | shared | no | No Claude-specific mechanic; runs under Codex as written. |
| `electron-dev` | shared | no | No Claude-specific mechanic; runs under Codex as written. |
| `mobile-debugging` | shared | no | No Claude-specific mechanic; runs under Codex as written. |
| `one-way-door` | adapter-required | yes (one-way-door-check.md) | Targets CLAUDE.md; map the instruction file to AGENTS.md for Codex; uses the AskUserQuestion tool; map to a Codex prompt or approval step; wires Claude PreToolUse/PostToolUse hooks; reproduce the failure and approval semantics before mapping, do not drop them. |
| `python-pipeline` | shared | no | No Claude-specific mechanic; runs under Codex as written. |
| `test-first-bugs` | adapter-required | yes (bug-report-detector.md) | Invokes the Task tool with subagent_type; map to a Codex multi-attempt run; names Claude auto-activation hooks (bug-report-detector.md); reproduce their trigger and failure semantics before mapping. |
| `vibe-coding` | shared | no | No Claude-specific mechanic; runs under Codex as written. |
| `web-scraping` | shared | no | No Claude-specific mechanic; runs under Codex as written. |
| `web-ui-best-practices` | shared | no | No Claude-specific mechanic; runs under Codex as written. |
| `zero-build-frontend` | shared | no | No Claude-specific mechanic; runs under Codex as written. |

Adapter and Claude-only skills stay behind the one-installation-path rule in
`plans/codex-compatibility-matrix.md` until each has a tested Codex mapping.
