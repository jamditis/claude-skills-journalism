# superjawn

Research-augmented Claude Code skills derived from [obra/superpowers](https://github.com/obra/superpowers) v5.0.7. Each skill grows a default-on research phase tailored to its stage of the workflow — gather trends, pitfalls, patterns, and discourse before building or proposing.

## Skills

| Skill | Status |
|---|---|
| `brainstorming` | Ported (Batch 1) |
| `writing-plans` | Ported (Batch 1) |
| `executing-plans` | Ported (Batch 1) |
| `systematic-debugging` | Pending (Batch 2) |
| `test-driven-development` | Pending (Batch 2) |
| `verification-before-completion` | Pending (Batch 2) |
| `receiving-code-review` | Pending (Batch 3) |
| `requesting-code-review` | Pending (Batch 3) |
| `subagent-driven-development` | Pending (Batch 4) |
| `dispatching-parallel-agents` | Pending (Batch 4) |
| `using-git-worktrees` | Pending (Batch 4) |
| `finishing-a-development-branch` | Pending (Batch 5) |
| `using-superjawn` | Pending (Batch 5) |
| `writing-skills` | Pending (Batch 5) |

## Coexistence with upstream

During the rollout (v0.1.0 through v0.5.0), keep both `superpowers` and `superjawn` plugins installed. Skills not yet ported still resolve via `superpowers:<skill>`. At v1.0.0, after at least 2 weeks of real use of the full set, disable the upstream `superpowers` plugin in your Claude Code config.

## Research phase

Every ported skill includes a `## Research phase` section. By default, the research runs via subagent dispatch (`Explore` for codebase questions, `general-purpose` for web/discourse). Findings are written into the skill's existing artifact (spec, plan, debug log). Skipping research requires an explicit, justified line in the artifact — see each skill's Skip protocol.

## Credits

See `CREDITS.md`.
