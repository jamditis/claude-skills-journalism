# superjawn — research-phase additions to superpowers skills

**Status:** design approved, awaiting implementation plan
**Date:** 2026-05-05
**Author:** Joe Amditis (with brainstorming session)
**Repo:** `claude-skills-journalism`
**New plugin:** `superjawn/`

## Goal

Add a default-on research phase to all 14 skills currently shipped by the upstream `superpowers` plugin (obra/superpowers, MIT, currently v5.0.7), recreated as a new plugin `superjawn` inside the existing `claude-skills-journalism` marketplace.

The research phase realizes the "research-first approach" already documented in `~/.claude/CLAUDE.md` — "let me check the latest trends, possible pitfalls, patterns, and discourse surrounding this topic before we start actually building or proposing solutions." Each skill gets a tailored research step at the right stage of its existing flow, dispatched via subagent by default, with findings written into the skill's existing artifact.

## Decision log

Locked during brainstorming on 2026-05-05:

| Question | Decision |
|---|---|
| Kind of research | All four — web/best-practices, codebase/prior-art, authoritative verification, user-context — situational and skill-dependent |
| Scope | All 14 superpowers skills |
| Rigidity | Default-on with explicit skip (justified, surfaced) |
| Mechanism | Subagent dispatch by default; inline only for light-touch |
| Output destination | Findings written into the skill's existing artifact (spec, plan, debug log) |
| Delivery approach | Approach D — new plugin `superjawn/` inside `claude-skills-journalism`; copy upstream MIT-licensed skills with attribution; rewrite cross-references; disable upstream `superpowers` once migration complete |
| Plugin name | `superjawn` |

## Section 1 — Plugin architecture

**Location:** New plugin directory at `~/projects/claude-skills-journalism/superjawn/`, registered in `marketplace.json` alongside `autocontext`, `pdf-design`, `pdf-playground`.

**Layout:** Standard plugin shape — `.claude-plugin/plugin.json`, `skills/<skill-name>/SKILL.md` × 14, plus top-level `LICENSE` and `CREDITS.md` attributing Jesse Vincent / `obra/superpowers` (MIT preserved).

**Cross-references:** Every `superpowers:<skill>` reference inside the skill text gets rewritten to `superjawn:<skill>`. One-time pass during port.

**Coexistence:** During build, both `superpowers` and `superjawn` plugins installed; manually invoke `superjawn:<skill>` for testing. After all 14 skills ship (v0.5.0), live with both enabled for at least 2 weeks of real use. Disable upstream `superpowers` only at v1.0.0, once superjawn has proven itself in practice. (See Section 5 for the version-by-version breakdown.)

**Versioning:** Track upstream-source version in `CREDITS.md` (currently 5.0.7). Manual diff-and-port pass when upstream ships changes worth pulling in. No automatic rebase.

## Section 2 — Per-skill research taxonomy

| Skill | Research stage | Default kinds | Subagent | Findings land in |
|---|---|---|---|---|
| `brainstorming` | After clarifying questions, before approaches | Web (trends + discourse), codebase (prior art) | general-purpose + Explore (parallel) | Spec doc, new `## Research notes` section |
| `writing-plans` | Before drafting plan steps | Web (pitfalls in chosen approach), codebase (similar features), authoritative (live API smoke) | general-purpose + Explore | Plan doc, top section |
| `executing-plans` | Before each step's implementation | Authoritative re-verification (drift check) | general-purpose, scoped to current step | Execution journal entry |
| `subagent-driven-development` | Per-subagent, before each task starts | Codebase (independence verification), authoritative (per-task) | Each subagent does its own | Subagent's report |
| `systematic-debugging` | At hypothesis formation | Web (error-string search, GitHub issues), codebase (prior bugs in this area) | general-purpose + Explore | Debug log, hypothesis section |
| `test-driven-development` | Before writing the red test | Web (testing patterns for this code shape), codebase (existing test conventions) | general-purpose + Explore | Test file header comment + draft notes |
| `using-git-worktrees` | Before creating worktree | User-context (existing worktrees? unfinished branches?) | Inline | Inline log line |
| `dispatching-parallel-agents` | Before fan-out | Codebase (verify task independence — no hidden shared state) | Explore | Dispatch plan |
| `finishing-a-development-branch` | Before integration choice | Codebase (competing PRs on adjacent code), user-context (recent decisions) | Inline | Inline summary |
| `receiving-code-review` | Per comment, before responding | Authoritative (verify reviewer's claim), codebase (current behavior) | general-purpose | Comment-response draft |
| `requesting-code-review` | Before requesting | User-context (review-scope conventions, reviewer preferences) | Inline | Inline |
| `using-superjawn` | Before invoking another skill | User-context (recent feedback memory about this skill) | Inline (memory check) | Inline |
| `verification-before-completion` | At verification step | Authoritative (what command actually proves this?) | general-purpose | Verification evidence block |
| `writing-skills` | Before drafting skill | Codebase (overlapping skills in plugin), user-context (description conventions) | Explore | Skill draft metadata |

**Light-touch flags:** `using-superjawn`, `finishing-a-development-branch`, `requesting-code-review`, `using-git-worktrees`, `dispatching-parallel-agents` have thin research fits — research is a brief inline check, not a subagent dispatch. Skill text says so explicitly rather than padding cargo-cult research into the flow.

**Cross-cutting principles:**
- All research is default-on with explicit skip
- Research output is always written into the skill's existing artifact, never to a separate file
- Subagent-by-default uses existing `Explore` / `general-purpose` agent types only

## Section 3 — Common research-step shape

Reusable template inserted into each skill's `## Research phase` section, with skill-specific substitutions (stage trigger, default kinds, subagent recommendation, artifact name).

```
## Research phase

[Skill-specific stage: e.g. "After clarifying questions, before proposing approaches"]

This is default-on. Skip only with explicit justification.

### 1. Pick research kinds
From the menu — trends + discourse, patterns, pitfalls, authoritative verification, user-context.
For this skill, defaults are: <kinds from Section 2>. Add others if the topic warrants.

### 2. Dispatch
Subagent by default:
  - Explore for codebase / prior-art
  - general-purpose for web / discourse / verification
  - Parallel when kinds are independent
Inline only for light-touch research (memory check, single grep).

### 3. Record findings
Write 3-5 tight bullets into <skill-specific artifact>. Include load-bearing
links/refs and anything considered-but-ruled-out so future-you knows it was checked.

### 4. Skip protocol
If skipping, write one line: "Skipped research because <reason>."
Valid reasons: trivial scope, fresh prior research in memory, user said skip.
Invalid reasons: "I think I know", "seems straightforward", "moving fast" —
if those are tempting, do the research.
```

**Integration with existing skill flow:** The `## Research phase` section gets inserted into each skill's existing `## Checklist` or `## Process` block as a new numbered step at the right stage. Existing process flow diagrams (the dot graphs in brainstorming, debugging, etc.) get one new node added — `"Research phase"` — with edges into and out of the right neighbors.

## Section 4 — Skip-justification protocol

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

**Build batches (5 batches, ~3 skills each, one PR per batch):**

1. **Foundation:** `brainstorming`, `writing-plans`, `executing-plans`
2. **Debugging + testing:** `systematic-debugging`, `test-driven-development`, `verification-before-completion`
3. **Code review:** `receiving-code-review`, `requesting-code-review`
4. **Parallelism + isolation:** `subagent-driven-development`, `dispatching-parallel-agents`, `using-git-worktrees`
5. **Meta + integration:** `finishing-a-development-branch`, `using-superjawn`, `writing-skills`

**Per-skill build steps:**

1. Copy upstream `SKILL.md` into `superjawn/skills/<name>/SKILL.md`
2. Add MIT attribution comment at top with original source URL
3. Insert `## Research phase` section at the stage from Section 2
4. Rewrite cross-references (`superpowers:` → `superjawn:`)
5. Update process flow diagram (dot graph) to include the new node
6. Self-test on a small real task; confirm research phase fires and findings record correctly

**Plugin install during build:** Local plugin path for fast iteration. Both upstream and superjawn installed; manually invoke `superjawn:<skill>` to test. After batch 5, disable upstream `superpowers`.

**Versioning:**

- `v0.1.0` — batch 1 shipped
- `v0.2.0`–`v0.4.0` — batches 2–4
- `v0.5.0` — batch 5 (all 14 in place, upstream still enabled)
- `v1.0.0` — upstream disabled, 2+ weeks of real use, no critical issues

**Per-batch testing:**

- Cross-ref resolution: every `superjawn:` reference must resolve
- Research phase fires: pick one small real task per skill, verify findings or skip line appear in the artifact
- Skip protocol works: deliberately invoke on a trivial task, verify skip line is correct and audit-visible

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
