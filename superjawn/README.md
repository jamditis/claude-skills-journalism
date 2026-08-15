# superjawn

Claude Code skills derived from [obra/superpowers](https://github.com/obra/superpowers) v5.0.7. Research belongs at entry-point stages where work originates without an upstream artifact (`brainstorming`, `systematic-debugging`, `writing-skills`); stale-artifact-consumer skills get a narrow default-skip freshness check (`executing-plans`, `subagent-driven-development`); the rest port as pure consumers that trust the artifact handoff. See [`../specs/2026-05-05-superjawn-research-phases-design.md`](../specs/2026-05-05-superjawn-research-phases-design.md) for the full architecture.

## Skills

| Skill | Category | Status |
|---|---|---|
| `brainstorming` | Research | Ported (Batch 1) |
| `writing-plans` | Consumer | Ported (Batch 1, research stripped in v0.2.0) |
| `executing-plans` | Freshness check | Ported (Batch 1, freshness check in v0.2.0) |
| `systematic-debugging` | Research | Ported (Batch 2) |
| `test-driven-development` | Consumer | Ported (Batch 2) |
| `verification-before-completion` | Consumer | Ported (Batch 2) |
| `receiving-code-review` | Consumer | Ported (Batch 3) |
| `requesting-code-review` | Consumer | Ported (Batch 3, parity dropped in v1.0.0 for code-reviewer agent rewrite) |
| `subagent-driven-development` | Consumer | Ported (Batch 4) |
| `dispatching-parallel-agents` | Consumer | Ported (Batch 4) |
| `using-git-worktrees` | Consumer | Ported (Batch 4) |
| `finishing-a-development-branch` | Consumer | Ported (Batch 5) |
| `using-superjawn` | Consumer | Ported (Batch 5, renamed from upstream `using-superpowers`) |
| `writing-skills` | Research | Ported (Batch 5) |

## Standalone by default

Superjawn has no soft dependencies on the upstream `superpowers` plugin. The v1.0.0 release rewrote the four `superpowers:code-reviewer` agent dispatches from v0.6.0 to target `pr-review-toolkit:code-reviewer` (Anthropic-maintained, in `@claude-code-plugins`). You can run `superjawn` as a standalone replacement for `superpowers`. If you want to revert to the upstream plugin for any reason, install with `/plugin install superpowers@claude-plugins-official`.

## Phase shapes

**Research phase (3 entry-point skills).** Default-on. Subagent dispatch by default (`Explore` for codebase, `general-purpose` for web/discourse). Findings land in the skill's existing artifact. Skip requires an explicit, justified line per the locked skip protocol.

**Freshness check (1 stale-artifact consumer skill).** Default-skip. Fires only when a trigger indicates real drift risk: cross-session execution, external API/service touched, or working on `main`/`master`. Findings land in `.superpowers/exec-journal-<plan-slug>.md`.

**Consumer (10 skills).** No phase. Pure port from upstream with attribution comment + dual-namespace cross-reference rewrites. Trusts the upstream-artifact handoff.

## Credits

See `CREDITS.md`.
