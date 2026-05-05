# Credits

`superjawn` is a research-augmented variant of the [superpowers](https://github.com/obra/superpowers) plugin by Jesse Vincent. Original work is MIT-licensed; modifications carry the same license.

## Upstream baseline

Synced against upstream `obra/superpowers` v5.0.7 (release tag) on 2026-05-05. The cached snapshot at `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/` is a release tarball, not a git checkout, so no commit SHA is available. Future syncs should pin to whichever upstream tag is current.

## Upstream changes ported since baseline

(none yet — list each port as it lands, with link to upstream commit)

## Modifications from upstream

**v0.3.0 Batch 2 (current).** Three skills ported under the v0.2.0 architecture:
- `systematic-debugging` — research category. Research phase inserted between Phase 1 (Root Cause Investigation) and Phase 2 (Pattern Analysis), default-on. Four research kinds (web, codebase prior-bugs, authoritative, user-context) dispatched as 3 parallel subagents + inline memory. Findings at `.superpowers/debug-log-<slug>.md`. Skip protocol byte-identical to Batch 1's locked text.
- `test-driven-development` — consumer category. Pure port (attribution + cross-refs only). No research phase: TDD is a sub-skill whose triggering spec/plan already encodes research conclusions.
- `verification-before-completion` — consumer category. Pure port. No research phase: verification is a gate function determined by what was just built.
- Inherited supporting files in `systematic-debugging/` diverge from upstream v5.0.7 with PR #36 review fixes: test-pressure-1/2/3.md and test-academic.md path references rewritten from `skills/debugging/systematic-debugging` to `superjawn:systematic-debugging` (matches actual plugin path + Claude Code skill-name invocation); CREATION-LOG.md path reference + Jesse's local `CLAUDE.md` path genericized; SKILL.md phase intro clarifies the Phase 1→4 fast path; SKILL.md `.superpowers/` git-ignore note reframed as user instruction; find-polluter.sh `find -path` pattern handling fixed (normalizes leading `./`, collapses `**` to `*`, uses mapfile array so 0 matches exit cleanly instead of silently reporting TOTAL=1); find-polluter.sh header relabeled "sequential test scanner" to match implementation.

**v0.2.0 architecture revision.** Research belongs only at entry-point stages where work originates without an upstream artifact. The three foundation skills shipped in v0.1.0 are now categorized:
- `brainstorming` — research phase preserved (entry-point skill)
- `writing-plans` — research phase stripped (consumer of brainstorming spec; trusts the handoff)
- `executing-plans` — per-task drift check replaced with a one-time default-skip freshness check at execution start, gated on three triggers (cross-session plan, external API/service, main/master branch). Two smoke-test bugs from PR #34 review folded in: the execution-journal location is now defined (`.superpowers/exec-journal-<plan-slug>.md`), and the master-branch guardrail is wired into the freshness check itself (was previously only in Remember).

See [`../specs/2026-05-05-superjawn-research-phases-design.md`](../specs/2026-05-05-superjawn-research-phases-design.md) for the full architecture and the categorization across all 14 skills.

**v0.1.0 (foundation triad).** Each ported skill added a `## Research phase` section. Reverted/replaced in v0.2.0 for `writing-plans` and `executing-plans`.

**Visual companion scripts.** `skills/brainstorming/scripts/{helper.js,server.cjs,start-server.sh,stop-server.sh}` diverge from upstream v5.0.7 with security and correctness fixes flagged during PR #34 review: XSS-safe DOM construction in `helper.js` (replaces `innerHTML` with `createElement`+`textContent`+`replaceChildren`), an inbound WebSocket frame size cap in `server.cjs` (rejects payloads above 1 MiB before allocating), `exec`-based PID preservation in `start-server.sh` foreground mode (so `server.pid` matches the node process), and SESSION_DIR validation in `stop-server.sh` (rejects paths outside `/tmp/brainstorm-*` or `*/.superpowers/brainstorm/*`). Carry these forward when syncing future upstream releases.
