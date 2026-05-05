# superjawn Batch 2 — debugging triad port

**Status:** implemented in PR #36 (v0.3.0). Plan at [`../plans/2026-05-05-superjawn-batch-2.md`](../plans/2026-05-05-superjawn-batch-2.md).
**Date:** 2026-05-05
**Author:** Joe Amditis (with brainstorming session)
**Repo:** `claude-skills-journalism`
**Plugin:** `superjawn/`
**Parent spec:** [`2026-05-05-superjawn-research-phases-design.md`](2026-05-05-superjawn-research-phases-design.md) (v0.2.0 architecture)

## Goal

Port the second batch of three superpowers skills into `superjawn` per the v0.2.0 architecture: research at entry-point stages, freshness check on stale-artifact consumers, pure consumer ports for the rest. Batch 2 covers the debugging-and-testing triad, where one skill is research-category (systematic-debugging) and two are consumer-category (test-driven-development, verification-before-completion).

After this PR ships as v0.3.0, six of the fourteen upstream skills will be ported.

## Decision log

Locked during brainstorming on 2026-05-05:

| Question | Decision |
|---|---|
| Stage placement (`systematic-debugging`) | Phase 1 → Phase 2 boundary — research fires after Root Cause Investigation, before Pattern Analysis |
| Default research kinds | All four — web (error-string + framework GitHub issues), codebase prior-bugs (`git log --grep` for related fixes), authoritative (live current docs), user-context (memory check) |
| Dispatch pattern | 3 parallel subagents (web, codebase, authoritative) + 1 inline memory check |
| Findings location | `.superpowers/debug-log-<slug>.md` where `<slug>` = `YYYY-MM-DD-<short-bug-description>`. Created on first run; appended chronologically. `.superpowers/` is git-ignored by upstream convention. |
| Skip protocol | Identical byte-for-byte to Batch 1's locked text. Skill text adds a clarifying note that research fires only when entering Phase 2; Phase 1 → Phase 4 paths don't reach it. |
| Scope (PR shape) | All three skills in one PR (no split between research-skill and consumer-skills) |
| Build order | systematic-debugging first (design-heavy), then test-driven-development, then verification-before-completion |

## Section 1 — Per-skill plan

### `systematic-debugging` (research category)

**Insertion point.** New `### Research phase` section placed between upstream's `### Phase 1: Root Cause Investigation` and `### Phase 2: Pattern Analysis`, at the same heading level as the existing phase sections so it reads as a discrete step in the four-phase flow rather than a Phase 1 sub-step.

**Default research kinds:** all four.

| Kind | Purpose | Dispatch | Tool |
|---|---|---|---|
| Web | Search the literal error string and the framework/library's open GitHub issues for prior reports | `general-purpose` subagent | WebSearch + WebFetch |
| Codebase prior-bugs | `git log --grep` for related historical fixes; spots regressions and prior work in the same file/area | `Explore` subagent | Bash (`git log`) + Grep |
| Authoritative | Fetch current live docs/spec for the API or library involved; catches "am I using this wrong" cases | `general-purpose` subagent | WebFetch |
| User-context | Check `MEMORY.md` for related debugging history | Inline (single Read of MEMORY.md + targeted file reads) | Read |

The three subagent kinds dispatch in parallel. The inline memory check runs concurrently in the main thread.

**Findings location.** A per-bug log file at `.superpowers/debug-log-<slug>.md`, where `<slug>` follows the pattern `YYYY-MM-DD-<short-bug-description>`:

```
.superpowers/debug-log-2026-05-05-test-failure-auth-handler.md
.superpowers/debug-log-2026-05-12-build-fails-on-arm64.md
.superpowers/debug-log-2026-06-03-flaky-redis-pubsub.md
```

The skill creates the file on first invocation if it doesn't exist; subsequent invocations on the same bug append. Each entry includes:

- Date/time
- Which research kinds fired (or were skipped, with the locked skip-justification line)
- Findings: 3-5 bullets per kind that fired, including load-bearing links/references
- "Considered but ruled out" notes so future-you knows what was checked

**Skip protocol.** Identical byte-for-byte to Batch 1's locked text:

> **Valid reasons:**
> - Trivial scope (typo, comment edit, single-line config)
> - Fresh prior research — same topic in current session OR within last 7 days with verifiable spec/plan pointer. **If the pointer doesn't resolve, the skip is invalid.** (Beyond 7 days, repeat the research even if you remember the prior findings — the landscape drifts.)
> - User explicit — **must quote the phrase** that authorized the skip.
> - Repeat of identical task — **must include a pointer** to the prior successful run.
>
> **Invalid reasons:** "I think I know", "seems straightforward", "moving fast", "user wants this done quickly", "already familiar with this codebase". If those are tempting, do the research.

**Phase-2-entry clarification.** The skill text includes one new note: research fires only when you've decided to enter Phase 2 (Pattern Analysis). If Phase 1 yielded the root cause and you're going Phase 1 → Phase 4 (Implementation) directly, you don't reach the research phase at all. The skip protocol governs the case where you've decided pattern analysis is needed but want to skip the research that would inform it.

**Cross-refs in this skill (from upstream → rewritten in port):**
- `superpowers:test-driven-development` → `superjawn:test-driven-development`
- `superpowers:verification-before-completion` → `superjawn:verification-before-completion`

### `test-driven-development` (consumer)

**No research or freshness phase.** Pure port:

1. Copy upstream `SKILL.md` byte-for-byte
2. Insert MIT attribution comment at top with v0.2.0 architecture note ("ported as a consumer category — no research phase per the v0.2.0 architecture; the artifact handoff carries the design conclusions")
3. Cross-refs: grep upstream for `superpowers:` references, rewrite per the dual-namespace rule. Most TDD invocations come FROM other skills (debugging, executing-plans, etc.), not the other way around, so this skill likely has few or no outbound cross-refs.

### `verification-before-completion` (consumer)

**No research or freshness phase.** Pure port — same shape as `test-driven-development`:

1. Copy upstream `SKILL.md` byte-for-byte
2. Insert MIT attribution comment at top with v0.2.0 architecture note
3. Cross-refs: grep upstream and rewrite per dual-namespace rule

## Section 2 — Cross-reference handling rules

**Locked from Batch 1, applied across all batches.**

- **Ported-this-batch-or-prior → `superjawn:`.** After this PR merges, the ported set is: `brainstorming`, `writing-plans`, `executing-plans` (Batch 1), `systematic-debugging`, `test-driven-development`, `verification-before-completion` (Batch 2). Six of fourteen.
- **Not-yet-ported → `superpowers:`.** The remaining eight: `subagent-driven-development`, `dispatching-parallel-agents`, `using-git-worktrees`, `finishing-a-development-branch`, `using-superpowers` (will rename to `using-superjawn` at port time), `writing-skills`, `receiving-code-review`, `requesting-code-review`.
- **Verify upstream existence before adding `superpowers:` prefix.** The Batch 1 fictional-namespace lesson (Task 8 caught `superpowers:frontend-design` and `superpowers:mcp-builder` — neither exists upstream; both rolled back to bare names). Always grep `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/` before adding a `superpowers:X` reference.

## Section 3 — Build sequence

1. Branch off master: `feat/superjawn-batch-2-debugging-triad`
2. **Port `systematic-debugging`** (design-heavy):
   - Copy upstream SKILL.md to `superjawn/skills/systematic-debugging/SKILL.md`
   - Insert MIT attribution comment with v0.2.0 architecture note
   - Insert `## Research phase` section between Phase 1 and Phase 2 (per Section 1's specifics)
   - Rewrite cross-refs (`test-driven-development` and `verification-before-completion` both become `superjawn:`)
   - Self-test: confirm the research-phase block reads end-to-end without contradicting Phase 1 or Phase 2
3. **Port `test-driven-development`** (consumer):
   - Copy upstream SKILL.md to `superjawn/skills/test-driven-development/SKILL.md`
   - Insert MIT attribution comment
   - Grep for `superpowers:` cross-refs; rewrite per Section 2 rule
4. **Port `verification-before-completion`** (consumer):
   - Copy upstream SKILL.md to `superjawn/skills/verification-before-completion/SKILL.md`
   - Insert MIT attribution comment
   - Grep for `superpowers:` cross-refs; rewrite per Section 2 rule
5. **Bump `superjawn/.claude-plugin/plugin.json`** 0.2.0 → 0.3.0; update description if useful
6. **Update `superjawn/README.md`** skill status table — mark Batch 2 entries as Ported
7. **Update `superjawn/CREDITS.md`** "Modifications from upstream" with a v0.3.0 entry summarizing the Batch 2 additions
8. **Spec self-review pass** on the SKILL.md files: cross-ref resolution check, attribution comment present, no leftover `superpowers:` references that should have been rewritten
9. **Commit (multiple logical commits, one per skill plus a bump commit), push, create PR**

## Section 4 — Testing approach

| Test | What it verifies | When |
|---|---|---|
| Cross-ref resolution | Every `superjawn:` reference in the three new SKILL.md files resolves to a real ported skill | Pre-commit, by `grep -rn "superjawn:" superjawn/skills/{systematic-debugging,test-driven-development,verification-before-completion}/` |
| Upstream-existence check | Every `superpowers:` reference left in the new SKILL.md files exists at `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/<name>/` | Pre-commit |
| Attribution comment | Each ported file has the MIT attribution comment at the top | Pre-commit |
| Research-phase smoke (systematic-debugging only) | Real-use exercise post-merge: pick a small bug, invoke `superjawn:systematic-debugging`, verify the research phase fires correctly, findings land at `.superpowers/debug-log-<slug>.md`, and the skip protocol works | Post-merge, fresh session |
| Pure-consumer smoke (TDD, VBC) | No skill text was modified beyond attribution + cross-refs. Static review only. | Pre-commit |

**Subagent loadability caveat.** A known limitation surfaced during Batch 1 smoke testing: sessions that started before a plugin install/reinstall can't load `superjawn:*` skills via the `Skill` tool. This means smoke testing in the SAME session as the marketplace operation is unreliable. The research-phase smoke for systematic-debugging must happen in a fresh session opened post-merge.

## Section 5 — Versioning

- **v0.3.0** ships this PR (Batch 2 — three skills)
- v0.4.0 → Batch 3 (`receiving-code-review`, `requesting-code-review`)
- v0.5.0 → Batch 4 (`subagent-driven-development`, `dispatching-parallel-agents`, `using-git-worktrees`)
- v0.6.0 → Batch 5 (`finishing-a-development-branch`, `using-superjawn`, `writing-skills`)
- v1.0.0 → upstream `superpowers` plugin disabled, after at least 2 weeks of real use of the full set with no critical issues

## Open questions / deferred decisions

- **`subagent-driven-development` freshness check (Batch 4).** This skill is in the freshness category but the spec hasn't enumerated trigger conditions yet — defer until Batch 4 brainstorming.
- **`using-superpowers` → `using-superjawn` rename (Batch 5).** The skill's name itself changes, not just cross-refs. Defer details until Batch 5 brainstorming.
- **`writing-skills` research-phase specifics (Batch 5).** Third research-category skill; specifics for stage placement, kinds, and findings location defer until Batch 5 brainstorming.

## Next steps

1. User reviews this spec
2. On approval, invoke `superjawn:writing-plans` (with `superpowers:writing-plans` fallback if the loadability issue blocks; the skills are byte-equivalent for plan-drafting purposes after the v0.2.0 strip) to produce the implementation plan
3. Execute the plan via `superjawn:subagent-driven-development` (with `superpowers:subagent-driven-development` fallback) once written
