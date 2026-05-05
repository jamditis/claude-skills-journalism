# superjawn — research and freshness phases on superpowers skills

**Status:** v0.1.0 shipped (foundation triad), v0.2.0 in flight (architecture rework)
**Date:** 2026-05-05 (v0.1.0 design), revised 2026-05-05 (v0.2.0 architecture)
**Author:** Joe Amditis (with brainstorming session)
**Repo:** `claude-skills-journalism`
**Plugin:** `superjawn/`

## Goal

Recreate the 14 skills shipped by upstream `superpowers` (obra/superpowers, MIT, currently v5.0.7) as `superjawn` inside the existing `claude-skills-journalism` marketplace, with research phases added only at entry-point stages and a narrow freshness check on stale-artifact-consumer skills.

The research phase realizes the "research-first approach" already documented in `~/.claude/CLAUDE.md` — "let me check the latest trends, possible pitfalls, patterns, and discourse surrounding this topic before we start actually building or proposing solutions." But research belongs only where work originates without an upstream artifact. Skills that consume an artifact from a research-baked-in upstream stage trust the handoff and don't re-research.

## Architecture revision (v0.2.0)

v0.1.0 shipped with research phases on all three foundation skills (`brainstorming`, `writing-plans`, `executing-plans`). Real-use feedback identified the issue: when these skills run in succession (the canonical flow), the research duplicates conclusions already encoded in the upstream artifact. Research at every stage:
- Costs time (especially with subagent dispatch)
- Risks conflicting findings (brainstorming concluded X, writing-plans research finds Y, plan is now ambiguous)
- Bloats skill text and skip-protocol overhead
- Creates a discipline-skip excuse in rigid skills like `test-driven-development`

The v0.2.0 architecture concentrates research at entry-point stages, adds a narrow freshness check on stale-artifact-consumer skills, and ports the remaining skills as pure consumers (no research insertion).

## Decision log

Locked during brainstorming on 2026-05-05 (v0.1.0):

| Question | Decision |
|---|---|
| Kind of research | All four — web/best-practices, codebase/prior-art, authoritative verification, user-context — situational and skill-dependent |
| Scope | All 14 superpowers skills (revised in v0.2.0 — see below) |
| Rigidity | Default-on with explicit skip (justified, surfaced) |
| Mechanism | Subagent dispatch by default; inline only for light-touch |
| Output destination | Findings written into the skill's existing artifact (spec, plan, debug log) |
| Delivery approach | Approach D — new plugin `superjawn/` inside `claude-skills-journalism`; copy upstream MIT-licensed skills with attribution; rewrite cross-references; disable upstream `superpowers` once migration complete |
| Plugin name | `superjawn` |

Revised 2026-05-05 (v0.2.0):

| Question | Decision |
|---|---|
| Where does research belong | Only at entry-point stages where work originates without an upstream artifact (3 skills) |
| Stale-artifact consumers | Get a narrow freshness check (default-skip with explicit triggers) instead of research (2 skills) |
| Pure consumers | Port without any research/freshness insertion — trust the upstream-artifact handoff (9 skills) |
| Trigger for the architecture revision | Real-use feedback that research in writing-plans/executing-plans duplicated brainstorming conclusions when the three skills ran in succession |

## Section 1 — Plugin architecture

**Location:** New plugin directory at `~/projects/claude-skills-journalism/superjawn/`, registered in `marketplace.json` alongside `autocontext`, `pdf-design`, `pdf-playground`.

**Layout:** Standard plugin shape — `.claude-plugin/plugin.json`, `skills/<skill-name>/SKILL.md` × 14, plus top-level `LICENSE` and `CREDITS.md` attributing Jesse Vincent / `obra/superpowers` (MIT preserved).

**Cross-references:** Every `superpowers:<skill>` reference inside the skill text gets rewritten to `superjawn:<skill>`. One-time pass during port.

**Coexistence:** During build, both `superpowers` and `superjawn` plugins installed; manually invoke `superjawn:<skill>` for testing. After all 14 skills ship (v0.5.0), live with both enabled for at least 2 weeks of real use. Disable upstream `superpowers` only at v1.0.0, once superjawn has proven itself in practice. (See Section 5 for the version-by-version breakdown.)

**Versioning:** Track upstream-source version in `CREDITS.md` (currently 5.0.7). Manual diff-and-port pass when upstream ships changes worth pulling in. No automatic rebase.

## Section 2 — Per-skill categorization (14 skills, three categories)

The categorization rule: research belongs at **entry-point stages where work originates without an upstream artifact**. Skills that consume an artifact from a research-baked-in upstream stage are consumers and trust the handoff. The narrow exception is **stale-artifact consumers** — skills that consume an artifact that may have aged across a session boundary or external API drift, which get a default-skip freshness check.

### Research (entry points) — 3 skills

These skills begin work from scratch (an idea, a bug report, a behavior to teach). The research phase fires by default with the locked skip protocol from Section 4.

| Skill | Research stage | Default kinds | Subagent | Findings land in |
|---|---|---|---|---|
| `brainstorming` | After clarifying questions, before approaches | Web (trends + discourse), codebase (prior art) | general-purpose + Explore (parallel) | Spec doc, new `## Research notes` section |
| `systematic-debugging` | At hypothesis formation (Phase 1 → Phase 2 boundary) | Web (error-string search, GitHub issues), codebase (prior bugs in this area), user-context (recent regressions in memory) | general-purpose + Explore | Debug log, hypothesis section |
| `writing-skills` | Before drafting the skill's first version | Codebase (overlapping skills in plugin), user-context (description conventions, naming patterns), web (recent skill-format changes upstream) | Explore | Skill draft notes / RED-phase scenarios |

### Freshness check (stale-artifact consumers) — 2 skills

These skills consume a plan that may have aged. Default-skip with explicit triggers.

| Skill | Trigger conditions | Verification kinds | Findings land in |
|---|---|---|---|
| `executing-plans` | (a) plan drafted in a prior session, OR (b) any task touches an external API/service/file outside the repo, OR (c) current branch is `main`/`master` | Authoritative state (live curl / file read / version check), codebase drift (grep that referenced functions/modules still exist), repo state (no conflicting commits since plan written) | Execution journal at `.superpowers/exec-journal-<plan-name>.md` (defined; see Section 3) |
| `subagent-driven-development` | Same triggers as executing-plans | Same as executing-plans, but each subagent's dispatched prompt includes the relevant freshness pointer | Subagent dispatch prompt + journal note |

### Consumer (pure port, no research/freshness insertion) — 9 skills

These skills port from upstream with attribution comment + dual-namespace cross-reference rewrites only. No research or freshness phase. The artifact handoff carries the conclusions.

| Skill | Why no research | Notes |
|---|---|---|
| `writing-plans` | Consumes spec from brainstorming. Spec encodes research conclusions. | v0.2.0 strips the research phase that v0.1.0 added |
| `test-driven-development` | Sub-skill called within other workflows. Pure red-green-refactor discipline. Adding research creates a discipline-skip excuse. | |
| `verification-before-completion` | Gate function. Verification command is determined by what was just built; no external research adds value. | |
| `receiving-code-review` | "Verify against codebase reality" is already step 3 of the existing skill. No separate research duplicates internal work. | |
| `requesting-code-review` | Pure dispatch mechanic. Reviewer preferences live in CLAUDE.md/memory. | |
| `dispatching-parallel-agents` | "Identify independent domains" is step 1 of the existing skill — already inline. | |
| `using-git-worktrees` | Pure mechanical (directory pick + gitignore + baseline tests). | |
| `finishing-a-development-branch` | Mechanical 4-option choice (merge/PR/keep/discard). | |
| `using-superjawn` | Meta-skill about skill discovery itself. | |

**Cross-cutting principles:**
- Research findings always land in the skill's existing artifact, never a separate file
- Subagent dispatch uses existing `Explore` / `general-purpose` agent types only
- Freshness check defaults to skip with explicit triggers (inverse of research's default-on)

## Section 3 — Phase shapes

Two shapes, one per phase type.

### 3a. Research phase (used by entry-point skills only)

```
## Research phase

[Skill-specific stage: e.g. "After clarifying questions, before proposing approaches"]

**Default-on.** Skip only with explicit justification per the locked skip protocol (Section 4).

### 1. Pick research kinds
From the menu — trends + discourse, patterns, pitfalls, authoritative verification, user-context.
For this skill, defaults are: <kinds from Section 2>. Add others if the topic warrants.

### 2. Dispatch
Subagent by default:
  - Explore for codebase / prior-art
  - general-purpose for web / discourse / verification
  - Parallel when kinds are independent

### 3. Record findings
Write 3-5 tight bullets into <skill-specific artifact>. Include load-bearing
links/refs and anything considered-but-ruled-out so future-you knows it was checked.

### 4. Skip protocol
[Insert the locked Section 4 skip protocol verbatim — bolded enforcement clauses preserved]
```

### 3b. Freshness check (used by stale-artifact consumer skills only)

```
## Freshness check (when artifact is stale)

**Default-skip.** Run only when one of these triggers fires:

- **Cross-session execution.** The plan was drafted in a prior session (different cwd, different transcript), not the current one.
- **External API/service touched.** Any task in the plan calls an API, service, or file outside the repo (e.g., live HTTP, third-party SDK call, OS-managed config).
- **Working on main/master.** Current branch is `main` or `master` — heightened drift risk because integration work assumes the branch is in sync.

If none of the triggers fire, write one line in the journal: "Freshness check skipped — none of the triggers fired (current session, no external APIs, on feature branch <name>)."

### When the check fires

Verify, in order:
1. **Authoritative state.** For each external API/file the plan references, hit the real source (live curl / file read / version check). Confirm the contract still matches what the plan assumed.
2. **Codebase drift.** Grep that any function/module/path the plan names still exists at the same path with the same shape.
3. **Repo state.** `git log <plan-write-sha>..HEAD` — has anyone landed conflicting work?

### Findings location

Write to the execution journal at `.superpowers/exec-journal-<plan-slug>.md` (created on first run if it doesn't exist). One line per check:

```
[YYYY-MM-DD HH:MM] Task N freshness check: <PASS / FAIL> — <one-line summary>
```

If FAIL on any check, escalate before implementing — the plan needs revision.
```

**Integration with existing skill flow:** The `## Research phase` section gets inserted into entry-point skills at the stage from Section 2 (after clarifying questions in brainstorming, between Phase 1 and Phase 2 in systematic-debugging, before drafting in writing-skills). Existing process flow diagrams (the dot graphs) get one new node added with edges into and out of the right neighbors.

The `## Freshness check (when artifact is stale)` section goes into executing-plans and subagent-driven-development between the plan-load step and the per-task implementation step. Default-skip means the check itself is one decision and one line in the journal — not a forcing function.

## Section 4 — Skip-justification protocol (research skills only)

This protocol applies to the three research-phase skills (`brainstorming`, `systematic-debugging`, `writing-skills`). Freshness-check skills (Section 3b) have their own inverse pattern (default-skip with explicit triggers); the protocol below does not apply there.

**Skip line format:**

```
Skipped research because <reason>. <Verifiable pointer if applicable>.
```

One line, written into the same artifact where findings would have gone. Audit-trail by design.

**Valid skip reasons (whitelist — these four, nothing else):**

1. **Trivial scope.** Typo fix, log-message wording, comment edit, single-character config change, removing a debug print.
2. **Fresh prior research.** Same topic researched in a recent session, findings still apply. "Recent" = either (a) the current session, or (b) within the last 7 calendar days with a verifiable spec/plan/log pointer. **Must include the pointer** — if it doesn't resolve, the skip is invalid. Beyond 7 days, repeat the research even if you remember the prior findings, because the landscape (codebase, libraries, docs) drifts.
3. **User explicit.** User said "skip research" or equivalent. **Must quote the phrase.**
4. **Repeat of identical task.** Same operation as a previous successful run, with a pointer to the prior instance.

**Invalid skip reasons (called out explicitly in skill text):**

- "I think I know" / "I have prior knowledge"
- "Seems straightforward" / "obvious fix"
- "Moving fast" / "tight timeline"
- "User wants this done quickly"
- "Already familiar with this codebase"

**Audit:** Each skill's existing self-review step gains a check: "Is there a research-findings section or a valid skip line? If neither, the skill didn't run correctly."

**Override:** If the user objects to a skip, the skill reverts to step 1 of the research phase.

**Drift visibility:** Skip lines written into artifacts make patterns visible during spec/plan review.

## Section 5 — Rollout sequence

**Build batches (5 batches, one PR per batch):**

1. **Foundation (shipped v0.1.0; rearchitected v0.2.0):** `brainstorming` (research), `writing-plans` (consumer — strip research), `executing-plans` (freshness check — replace research)
2. **Debugging + testing:** `systematic-debugging` (research), `test-driven-development` (consumer), `verification-before-completion` (consumer)
3. **Code review:** `receiving-code-review` (consumer), `requesting-code-review` (consumer)
4. **Parallelism + isolation:** `subagent-driven-development` (freshness check), `dispatching-parallel-agents` (consumer), `using-git-worktrees` (consumer)
5. **Meta + integration:** `finishing-a-development-branch` (consumer), `using-superjawn` (consumer), `writing-skills` (research)

**Per-skill build steps depend on the category:**

**Research skill:** Copy upstream `SKILL.md` → add MIT attribution comment → insert `## Research phase` section per Section 3a at the stage from Section 2 → rewrite `superpowers:` cross-references → update process flow diagram to include the research node → self-test that research phase fires and skip protocol works.

**Freshness-check skill:** Copy upstream `SKILL.md` → add MIT attribution comment → insert `## Freshness check (when artifact is stale)` section per Section 3b → rewrite `superpowers:` cross-references → ensure execution journal path is defined and reachable → self-test the trigger conditions (cross-session, external API, main/master) and the default-skip path.

**Consumer skill:** Copy upstream `SKILL.md` → add MIT attribution comment → rewrite `superpowers:` cross-references → done. No research/freshness phase, no flow-diagram edits beyond cross-ref text.

**Plugin install during build:** Marketplace cleanup completed 2026-05-05 post-merge of v0.1.0 — local-path registration removed, GitHub-sourced marketplace re-registered. For feature-branch live testing, register the local path under a parallel marketplace name (e.g., `claude-skills-journalism-local`) instead of replacing the canonical GitHub-sourced one.

**Versioning:**

- `v0.1.0` — batch 1 shipped (foundation triad with research on all three; rearchitected in v0.2.0)
- `v0.2.0` — batch 1 architecture rework: strip research from writing-plans, replace executing-plans research with freshness check, fold in smoke-test bug fixes
- `v0.3.0`–`v0.5.0` — batches 2-4 per the new categorization
- `v0.6.0` — batch 5 (all 14 in place, upstream still enabled)
- `v1.0.0` — upstream disabled, 2+ weeks of real use, no critical issues

**Per-batch testing:**

- Cross-ref resolution: every `superjawn:` reference must resolve to a real upstream or already-ported skill
- Research phase fires (entry-point skills only): pick one small real task per skill, verify findings or skip line appear in the artifact
- Freshness check (executing-plans, subagent-driven-development): deliberately exercise the trigger conditions (cross-session plan, external-API task, main-branch invocation) and the default-skip path on a feature-branch run
- Pure-port consumers: cross-ref resolution + announce-string namespace correctness only (no phase to test)

## Section 6 — Upstream drift management

**Cadence:** Quarterly check (4×/year). Faster only on major upstream releases.

**Diff mechanism:** `diff -ru` between upstream cache and `superjawn/skills/`, or compare upstream's `CHANGELOG.md` since the version recorded in `CREDITS.md`.

**Baseline tracking in `CREDITS.md`:**

```
Synced against upstream obra/superpowers v5.0.7 (commit <fill in commit SHA at port time>) on 2026-05-05.
Upstream changes since baseline: <list each port as it lands>
```

**Triage — what's worth porting:**

- New skills upstream adds → port if relevant
- Bug fixes to existing skills → port
- Process improvements that don't conflict with research-phase additions → port
- Re-flows of skill checklists that conflict → manually merge research phase back in

**Skip:**

- Pure copy edits (typos, formatting)
- New visual-companion features etc. unless they'll be used
- Anything that contradicts the research-phase design

**Process when porting:**

- One PR per upstream change
- PR title: `port: <upstream commit summary>`
- PR body links to upstream commit
- Run per-skill test from Section 5 after porting

**Drift-detection signal:** If a quarterly check finds upstream has diverged a lot (e.g. >1k LOC of skill changes in 90 days), escalate to a re-evaluation of approach.

## Open questions / deferred decisions

- Specific phrasing of the `## Research phase` text per skill — settled during implementation plan
- Whether to add a parallel `superjawn-hooks/` plugin that enforces research-phase compliance via PreToolUse/PostToolUse hooks — out of scope for v1, revisit if drift becomes visible
- Distribution beyond the marketplace (e.g. announcing to other CCM/journalism users) — deferred until v1.0.0

## Next steps

1. User reviews this spec
2. On approval, invoke `superjawn:writing-plans` (once it exists) — or until then, `superpowers:writing-plans` — to produce the implementation plan
3. Execute batch 1 first as a validation slice; pause after each batch for real-use feedback before next
