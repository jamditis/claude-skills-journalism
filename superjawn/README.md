# superjawn

Claude Code skills derived from [obra/superpowers](https://github.com/obra/superpowers) v5.0.7. Research belongs at entry-point stages where work originates without an upstream artifact (`brainstorming`, `systematic-debugging`, `writing-skills`); stale-artifact-consumer skills get a narrow default-skip freshness check (`executing-plans`, `subagent-driven-development`); the rest port as pure consumers that trust the artifact handoff. See [`../specs/2026-05-05-superjawn-research-phases-design.md`](../specs/2026-05-05-superjawn-research-phases-design.md) for the full architecture.

## Skills

| Skill | Category | Status |
|---|---|---|
| `brainstorming` | Research | Ported (Batch 1) |
| `writing-plans` | Consumer | Ported (Batch 1, research stripped in v0.2.0) |
| `executing-plans` | Freshness check | Ported (Batch 1, freshness check in v0.2.0) |
| `systematic-debugging` | Research | Pending (Batch 2) |
| `test-driven-development` | Consumer | Pending (Batch 2) |
| `verification-before-completion` | Consumer | Pending (Batch 2) |
| `receiving-code-review` | Consumer | Pending (Batch 3) |
| `requesting-code-review` | Consumer | Pending (Batch 3) |
| `subagent-driven-development` | Freshness check | Pending (Batch 4) |
| `dispatching-parallel-agents` | Consumer | Pending (Batch 4) |
| `using-git-worktrees` | Consumer | Pending (Batch 4) |
| `finishing-a-development-branch` | Consumer | Pending (Batch 5) |
| `using-superjawn` | Consumer | Pending (Batch 5) |
| `writing-skills` | Research | Pending (Batch 5) |

## Coexistence with upstream

During the rollout (v0.1.0 through v0.6.0), keep both `superpowers` and `superjawn` plugins installed. Skills not yet ported still resolve via `superpowers:<skill>`. At v1.0.0, after at least 2 weeks of real use of the full set, disable the upstream `superpowers` plugin in your Claude Code config.

## Phase shapes

**Research phase (3 entry-point skills).** Default-on. Subagent dispatch by default (`Explore` for codebase, `general-purpose` for web/discourse). Findings land in the skill's existing artifact. Skip requires an explicit, justified line per the locked skip protocol.

**Freshness check (2 stale-artifact consumer skills).** Default-skip. Fires only when a trigger indicates real drift risk: cross-session execution, external API/service touched, or working on `main`/`master`. Findings land in `.superpowers/exec-journal-<plan-slug>.md`.

**Consumer (9 skills).** No phase. Pure port from upstream with attribution comment + dual-namespace cross-reference rewrites. Trusts the upstream-artifact handoff.

## Credits

See `CREDITS.md`.
