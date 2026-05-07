# superjawn batch 4 — parallel execution + worktrees

**Status:** draft, 2026-05-07
**Target version:** v0.5.0
**Master design:** [`2026-05-05-superjawn-research-phases-design.md`](./2026-05-05-superjawn-research-phases-design.md)
**Branch:** `feat/superjawn-batch-4-parallel-execution-skills`

## Scope

Port three skills from upstream `obra/superpowers` v5.0.7:

1. `subagent-driven-development` — in-session execution mode (sub-skill of executing-plans)
2. `dispatching-parallel-agents` — fan-out utility, called by debugging / executing / subagent-driven flows
3. `using-git-worktrees` — workspace setup utility, called before plan execution

All three are **consumer category** per the master spec section 2 — no research phase, no freshness check. They are utilities and execution modes; the research conclusions they act on were already crystallised upstream by `brainstorming` and `writing-plans`.

After this batch, 11 of 14 skills will be ported. Remaining for Batch 5: `finishing-a-development-branch`, `using-superpowers` (rename to `using-superjawn` at port time), `writing-skills`.

## Per-skill plan

### 1. dispatching-parallel-agents

| Property | Value |
|---|---|
| Category | consumer |
| `skill_md_parity` | `true` |
| Supporting files | none |
| Cross-refs in upstream | none |
| Difficulty | trivial — easiest of the three |

The cleanest port of the entire 14-skill set so far. Upstream `SKILL.md` has zero `superpowers:` or `superjawn:` cross-references — verified with `grep -oE '(superjawn|superpowers):[a-z][a-z0-9_-]*'`. Pure attribution insertion.

**Required edits:**
- Insert MIT attribution comment block immediately after frontmatter (strict-parity layout from PR #42).
- Body: byte-identical to upstream.

### 2. using-git-worktrees

| Property | Value |
|---|---|
| Category | consumer |
| `skill_md_parity` | `true` |
| Supporting files | none |
| Cross-refs in upstream | none of the `superpowers:<x>` form |
| Difficulty | trivial |

Upstream `SKILL.md` has bare-name "Related skills" mentions of `brainstorming` and `executing-plans` (lines 212 and 214) but they are NOT prefixed with `superpowers:` — they appear in plain prose. The validator's `extract_crossrefs` only matches the `(superjawn|superpowers):<name>` token form, so these don't trigger cross-ref enforcement and don't need rewriting. Parity stays clean.

**Required edits:**
- Insert MIT attribution comment block immediately after frontmatter.
- Body: byte-identical to upstream.

### 3. subagent-driven-development

| Property | Value |
|---|---|
| Category | consumer |
| `skill_md_parity` | **`false`** (constraint surfaces here) |
| Supporting files | 3 (all byte-identical to upstream — no overrides needed) |
| Cross-refs in upstream | 7 (5 to skills ported by end of Batch 3, 2 to skills ported in this batch, 1 to a Batch 5 skill) |
| Difficulty | medium — namespace migration breaks parity |

**Strict-parity / dual-namespace tension hits here.** The validator's parity check is `cmp -s <stripped-local-SKILL.md> <upstream-SKILL.md>` — strict byte-identity. The cross-ref check requires that `superpowers:<x>` becomes `superjawn:<x>` whenever `<x>` has been ported. Migrating the prefix breaks parity by definition.

Resolution: drop `skill_md_parity` for this skill (set to `false` in the manifest), log the namespace-migration divergences in `CREDITS.md`. Precedent: `writing-plans` (v0.2.0) is `parity: false` for a different reason (research-phase strip), but the manifest mechanism is the same.

**Cross-ref migrations** (after this batch the ported set is 11 skills):

| Upstream reference | Line | After Batch 4 | Action |
|---|---|---|---|
| `superpowers:using-git-worktrees` | 268 | ported (this batch) | rewrite `superjawn:using-git-worktrees` |
| `superpowers:writing-plans` | 269 | ported (v0.2.0) | rewrite `superjawn:writing-plans` |
| `superpowers:requesting-code-review` | 270 | ported (v0.4.0) | rewrite `superjawn:requesting-code-review` |
| `superpowers:finishing-a-development-branch` | 64, 83, 271 | NOT yet ported (Batch 5) | leave as `superpowers:` |
| `superpowers:test-driven-development` | 274 | ported (v0.3.0) | rewrite `superjawn:test-driven-development` |
| `superpowers:executing-plans` | 277 | ported (v0.2.0) | rewrite `superjawn:executing-plans` |

All other content stays byte-identical to upstream.

**Supporting files** (3 — all directly under `subagent-driven-development/`):

| File | Cross-refs | Overrides needed? |
|---|---|---|
| `implementer-prompt.md` | none | no — byte-identical port |
| `spec-reviewer-prompt.md` | none | no — byte-identical port |
| `code-quality-reviewer-prompt.md` | `superpowers:code-reviewer` (agent — keep), `requesting-code-review/code-reviewer.md` (relative path — keep) | no — byte-identical port |

The supporting-file walk in the validator passes naturally for all three since they remain byte-identical to upstream.

## Cross-ref enforcement summary

Per the dual-namespace rule (locked memory): ported-this-batch-or-prior → `superjawn:`, not-yet-ported → `superpowers:`. After Batch 4 the ported set will be:

```
brainstorming, writing-plans, executing-plans, systematic-debugging,
test-driven-development, verification-before-completion,
receiving-code-review, requesting-code-review,
subagent-driven-development, dispatching-parallel-agents, using-git-worktrees
```

Six remain on `superpowers:` until Batch 5 ships: `finishing-a-development-branch`, `using-superpowers` (will rename to `using-superjawn`), `writing-skills`. Plus the `code-reviewer` AGENT, which stays `superpowers:` indefinitely until the agents port plan exists (post-v1.0.0).

## Files to create

```
superjawn/skills/dispatching-parallel-agents/SKILL.md
superjawn/skills/using-git-worktrees/SKILL.md
superjawn/skills/subagent-driven-development/SKILL.md
superjawn/skills/subagent-driven-development/implementer-prompt.md
superjawn/skills/subagent-driven-development/spec-reviewer-prompt.md
superjawn/skills/subagent-driven-development/code-quality-reviewer-prompt.md
```

## Files to modify

```
superjawn/.claude-plugin/plugin.json    # version 0.4.0 -> 0.5.0; description "8 of 14" -> "11 of 14"; "batches 4-5" -> "batch 5"
superjawn/CREDITS.md                    # add v0.5.0 batch 4 section with namespace-migration divergence log for subagent-driven-development
superjawn/scripts/skills-manifest.json  # add 3 new skill entries
.claude-plugin/marketplace.json         # superjawn version 0.4.0 -> 0.5.0 with bumped description
docs/superjawn/index.html               # bump v0.4.0 -> v0.5.0; "8 of 14" -> "11 of 14"; ported skills section
docs/index.html                         # main landing card description bump
```

## Manifest entries

```json
"subagent-driven-development": {
  "category": "consumer",
  "skill_md_parity": false,
  "supporting_file_overrides": {}
},
"dispatching-parallel-agents": {
  "category": "consumer",
  "skill_md_parity": true,
  "supporting_file_overrides": {}
},
"using-git-worktrees": {
  "category": "consumer",
  "skill_md_parity": true,
  "supporting_file_overrides": {}
}
```

Note: `skill_md_parity: false` for `subagent-driven-development` skips the parity check (the cross-ref migrations are the divergence). Supporting files are still walked — all three are byte-identical to upstream so no overrides are required.

## MIT attribution comment block

Each new `SKILL.md` gets the same opening pattern as the v0.4.0 consumer ports — flush against the frontmatter close (no blank line above):

```markdown
---
name: <skill-name>
description: <unchanged from upstream>
---
<!--
Adapted from obra/superpowers <skill-name> skill (v5.0.7),
MIT-licensed, copyright 2025 Jesse Vincent. Modifications copyright 2026 Joe Amditis.
v0.5.0 ports as a consumer category — no research phase per the v0.2.0 architecture,
since this skill is a [utility / execution mode] called by upstream skills that already
encode their research conclusions.
See CREDITS.md.
-->

<rest of upstream content; for subagent-driven-development with cross-ref migrations applied>
```

## CREDITS.md addendum (v0.5.0 section)

```markdown
**v0.5.0 Batch 4.** Three skills ported under the v0.2.0 architecture:
- `dispatching-parallel-agents` — consumer category. Pure port (no cross-refs in upstream; SKILL.md byte-identical to upstream after stripping the MIT block).
- `using-git-worktrees` — consumer category. Pure port (cross-refs in upstream are bare-name, not `superpowers:` prefixed, so no migration needed; SKILL.md byte-identical).
- `subagent-driven-development` — consumer category, but `skill_md_parity: false` because upstream contains five `superpowers:<ported-skill>` cross-references (writing-plans, executing-plans, test-driven-development, requesting-code-review, using-git-worktrees) that the validator's dual-namespace check requires migrating to `superjawn:<x>`. The migration breaks byte-parity with upstream. The two `superpowers:finishing-a-development-branch` references stay as `superpowers:` (not yet ported, Batch 5). The one `superpowers:code-reviewer` reference inside `code-quality-reviewer-prompt.md` stays as `superpowers:` (agent, not skill — agents are not in the 5-batch port plan). All three supporting files are byte-identical to upstream and need no overrides.
```

## Validation expectations

`bash superjawn/scripts/validate-skill.sh` should report all 11 ported skills passing all enforced checks:

- 11 skills declared in manifest, 11 frontmatter shapes ok, 11 attribution blocks ok, 11 cross-ref ok
- Parity check: 6 enforced + 5 skipped (research/freshness/post-Batch-4 false-parity)
  - Enforced and passing: test-driven-development, verification-before-completion, receiving-code-review, requesting-code-review, dispatching-parallel-agents, using-git-worktrees
  - Skipped: brainstorming (research), executing-plans (freshness), systematic-debugging (research), writing-plans (consumer but research-strip), subagent-driven-development (consumer but cross-ref migration)
- Supporting files: brainstorming 5 overrides, systematic-debugging 6 overrides, all others empty; subagent-driven-development walks 3 byte-identical files

## Smoke test plan

After implementation lands but before opening the PR:

1. `bash superjawn/scripts/validate-skill.sh` exits 0.
2. `claude plugin validate ./superjawn` exits 0.
3. Live-test in a fresh session: invoke `superjawn:dispatching-parallel-agents` and confirm it loads (vs. falling through to `superpowers:`).
4. Live-test: invoke `superjawn:subagent-driven-development` and confirm cross-ref invocations inside the skill point at `superjawn:` for the migrated targets and at `superpowers:` for `finishing-a-development-branch`.
5. `git diff master..HEAD --stat` matches the "files to create / modify" list — no surprise changes.

## Open questions for review before porting

1. Should the marketplace.json bump + landing-page bump be in the SAME PR as the skill ports (precedent: PR #42), or split into a release PR (precedent: PR #37)? PR #42 bundled them and was clean — recommendation: bundle.
2. Anything else to fold in alongside Batch 4 (e.g., another validator hardening pass)? Not aware of any outstanding items.

## Relationship to the rest of the plan

Batch 5 (`finishing-a-development-branch`, `using-superjawn`, `writing-skills`) is the last batch. After it ships:

- The `superpowers:finishing-a-development-branch` references in `subagent-driven-development/SKILL.md` (lines 64, 83, 271) need migrating to `superjawn:finishing-a-development-branch`. Batch 5's plan should include this back-reference cleanup.
- v1.0.0 readiness work begins (disable upstream `superpowers` plugin after ≥2 weeks of real use).
