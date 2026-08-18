# superjawn batch 3, code review skills

**Status:** draft, 2026-05-06
**Target version:** v0.4.0
**Master design:** [`2026-05-05-superjawn-research-phases-design.md`](./2026-05-05-superjawn-research-phases-design.md)
**Branch:** `feat/superjawn-batch-3-code-review-skills`

## Scope

Port two consumer-category skills from upstream `obra/superpowers` v5.0.7:

1. `receiving-code-review`, verifying-feedback skill, called when handling code review comments
2. `requesting-code-review`, dispatch skill, called to fan out code review work to a subagent

Both are **consumer category** per the master spec section 2, no research phase, no freshness check. Per master spec section 4, the per-skill build is: copy upstream `SKILL.md` → add MIT attribution comment → rewrite `superpowers:` cross-references → done.

## Cross-reference rewrites

Run `grep -oE '(superjawn|superpowers):[a-z][a-z0-9_-]*'` on each upstream `SKILL.md` and apply the dual-namespace rule (master spec, locked memory):

- ported-this-batch-or-prior → `superjawn:`
- not-yet-ported → `superpowers:`

After v0.3.0 the ported set is: `brainstorming`, `writing-plans`, `executing-plans`, `systematic-debugging`, `test-driven-development`, `verification-before-completion`. Add to that the two skills landing in this batch.

### receiving-code-review/SKILL.md

Upstream content has **zero** cross-references to other skills or agents. Only references "your human partner" (a phrasing convention, not a cross-ref). No rewrites required.

### requesting-code-review/SKILL.md

Upstream cross-references:

| Reference | Type | Action |
|---|---|---|
| `superpowers:code-reviewer` (line 8) | agent (`agents/code-reviewer.md` upstream) | **stays `superpowers:`**, agents are not in the 5-batch port plan; v1.0.0 readiness will revisit |
| `Use Task tool with superpowers:code-reviewer type` (line 34) | agent | same, stays `superpowers:` |

The `code-reviewer` is an agent, not a skill, and isn't in any of the 5 batches in the master spec. It stays `superpowers:` for now. CREDITS.md gets a note so the v1.0.0 plan picks it up.

### requesting-code-review/code-reviewer.md (template)

Supporting file referenced from `SKILL.md` line 105 ("See template at: requesting-code-review/code-reviewer.md"). Copy alongside SKILL.md, no edits unless it contains additional cross-refs (verify before commit).

## Files to create

```
superjawn/skills/receiving-code-review/SKILL.md
superjawn/skills/requesting-code-review/SKILL.md
superjawn/skills/requesting-code-review/code-reviewer.md
```

## Files to modify

```
superjawn/.claude-plugin/plugin.json    # version 0.3.0 -> 0.4.0; description bumps "6 of 14" -> "8 of 14"
superjawn/CREDITS.md                    # add v0.4.0 batch 3 section with divergence log
.claude-plugin/marketplace.json         # superjawn version 0.3.0 -> 0.4.0 (matches plugin.json per PR #39 sync rule)
docs/superjawn/index.html               # if it exists with a version badge, bump
```

## MIT attribution comment block

Each new `SKILL.md` gets the same opening pattern as the v0.3.0 consumer ports (`test-driven-development/SKILL.md`, `verification-before-completion/SKILL.md`):

```markdown
---
name: <skill-name>
description: <unchanged from upstream>
---

<!--
Adapted from obra/superpowers <skill-name> skill (v5.0.7),
MIT-licensed, copyright 2025 Jesse Vincent. Modifications copyright
2026 Joe Amditis. v0.4.0 ports as a consumer category, no research
phase per the v0.2.0 architecture, since [skill-specific rationale].
See CREDITS.md.
-->

<rest of upstream content unchanged>
```

Per-skill rationale clause for the comment:

- **receiving-code-review:** "verification-against-codebase is already step 3 of the existing flow; review-evaluation is per-comment, not entry-point work"
- **requesting-code-review:** "dispatch mechanic; reviewer preferences live in CLAUDE.md and memory rather than a research phase"

## Verification

### Structural validator (must pass)

```bash
superjawn/scripts/validate-skill.sh receiving-code-review requesting-code-review
# expected: pass on both, exit 0
```

The validator script (added in this branch alongside the ports) asserts: SKILL.md present, frontmatter `name` matches dirname, non-empty `description`, MIT attribution block referencing CREDITS.md, all `superjawn:` and `superpowers:` cross-refs resolve in their respective trees.

A pass on the full skill set (no args) must also remain green:

```bash
superjawn/scripts/validate-skill.sh
# expected: 8 skills pass, exit 0
```

### Live load smoke test (parallel local marketplace)

Per master spec section 4 ("Plugin install during build"):

1. Register feature branch as a parallel marketplace under a different name:
   ```bash
   claude plugin marketplace add /home/jamditis/projects/claude-skills-journalism --name claude-skills-journalism-local --scope user
   claude plugin install superjawn@claude-skills-journalism-local
   ```
2. In a fresh session, invoke each new skill once via the Skill tool and confirm it loads cleanly with the expected frontmatter `name`/`description`.
3. Unregister the local marketplace before opening the PR:
   ```bash
   claude plugin marketplace remove claude-skills-journalism-local
   ```

### External reviewer

Run `codex exec -m gpt-5.4 --reasoning-effort low` on the diff before opening the PR. Codex's job is architectural sanity check (cross-ref correctness, dual-namespace adherence, attribution comment shape). Codex should not rewrite content, it confirms or flags.

## Out of scope

- **The `code-reviewer` agent itself**, referenced by `requesting-code-review` but not in any port batch. Stays `superpowers:code-reviewer`. v1.0.0 readiness will decide whether to port it, rewrite the reference, or keep `superpowers:` (which requires upstream to remain installed).
- **Any content edits** to either skill beyond attribution and cross-refs. These are pure consumer ports.
- **Marketplace updates outside this repo.** Post-merge marketplace bump runs in master via PRs #37/#39's pattern.
- **Batches 4 and 5.** Locked rule: each batch gets its own plan after the prior validates.

## Versioning

- `v0.3.0`, Batch 2 shipped, 6 of 14 skills (current)
- `v0.4.0`, **this batch**, 8 of 14 skills
- `v0.5.0`, Batch 4 (3 skills), 11 of 14
- `v0.6.0`, Batch 5 (3 skills), 14 of 14
- `v1.0.0`, gated on 2+ weeks of post-B5 real use; revisits the `code-reviewer` agent reference noted above

## Risk

- **Low**, pure consumer ports, both files small (214 lines + 107 lines + 3.4 KB template). Highest-risk item is the dangling `superpowers:code-reviewer` agent reference, which is intentional and logged.
- Copilot review historically flags: stale paths, namespace inconsistencies, internal contradictions, attribution drift. The validator catches those mechanically before PR open.

## CREDITS.md addition

Append under "## Modifications from upstream":

```markdown
**v0.4.0 Batch 3.** Two skills ported under the v0.2.0 architecture:
- `receiving-code-review`, consumer category. Pure port (attribution only; zero cross-references in upstream content).
- `requesting-code-review`, consumer category. Pure port (attribution only; supporting `code-reviewer.md` template copied verbatim). The `superpowers:code-reviewer` agent reference at lines 8 and 34 is intentionally preserved, agents are not in the 5-batch skills port plan. v1.0.0 readiness will decide whether to port the agent into superjawn, rewrite the reference, or accept the soft dependency on the upstream `superpowers` plugin.
- Validator added at `superjawn/scripts/validate-skill.sh` (structural assertions for any consumer port, frontmatter shape, MIT attribution, cross-reference resolution). Passes on all 8 ported skills.
```
