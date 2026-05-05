# superjawn Batch 2 implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Use `superpowers:` namespace for the meta-skills here because the session executing this plan likely cannot load `superjawn:*` skills due to the loadability caveat in the spec — the two are byte-equivalent for plan-execution purposes after the v0.2.0 strip.

**Goal:** Port the second batch of three superpowers skills into superjawn under the v0.2.0 architecture: `systematic-debugging` (research category — design-heavy), `test-driven-development` (consumer — pure port), `verification-before-completion` (consumer — pure port). Ship as v0.3.0.

**Architecture:** Three skill ports inside the existing `superjawn/skills/` tree. systematic-debugging gets a research-phase section inserted between its existing Phase 1 (Root Cause Investigation) and Phase 2 (Pattern Analysis) per the spec's locked design (4 research kinds, 3 parallel subagents + inline memory, findings at `.superpowers/debug-log-<slug>.md`, locked Batch 1 skip protocol). The two consumers receive only an MIT attribution comment and dual-namespace cross-reference rewrites — no research/freshness phase.

**Tech Stack:** Markdown (skill files), JSON (plugin manifest + marketplace), bash (verification commands).

**Source spec:** `specs/2026-05-05-superjawn-batch-2-design.md` (commit `b078c40` on branch `feat/superjawn-batch-2-debugging-triad`).

**Parent architecture spec:** `specs/2026-05-05-superjawn-research-phases-design.md` (master, last revised in PR #35 squash `0c5c8e7`).

**Scope:** Batch 2 only. Batches 3–5 each get their own plan generated after this batch lands.

---

## File structure

**Created in this plan:**

```
superjawn/skills/systematic-debugging/
├── SKILL.md                              # Modified copy of upstream (research phase inserted)
├── root-cause-tracing.md                 # Verbatim copy of upstream supporting reference
├── defense-in-depth.md                   # Verbatim copy of upstream supporting reference
└── condition-based-waiting.md            # Verbatim copy of upstream supporting reference

superjawn/skills/test-driven-development/
├── SKILL.md                              # Modified copy of upstream (attribution + cross-refs only)
└── testing-anti-patterns.md              # Verbatim copy of upstream supporting reference

superjawn/skills/verification-before-completion/
└── SKILL.md                              # Modified copy of upstream (attribution + cross-refs only)
```

**Modified in this plan:**

```
superjawn/.claude-plugin/plugin.json      # Version bump 0.2.0 → 0.3.0, description update
superjawn/README.md                       # Skill status table — mark Batch 2 entries Ported
superjawn/CREDITS.md                      # Add v0.3.0 entry under Modifications from upstream
```

**Responsibility split:**
- `systematic-debugging/SKILL.md` carries the research-phase design from the spec
- The two consumer SKILL.md files port byte-for-byte except for attribution + cross-refs
- The supporting files inside each skill directory are reference material the SKILL.md links to (root-cause-tracing, defense-in-depth, condition-based-waiting for systematic-debugging; testing-anti-patterns for TDD) — copied verbatim because they don't have research phases or cross-refs to rewrite
- `plugin.json`, `README.md`, `CREDITS.md` carry the version/status/attribution metadata

---

## Task 1: Port `systematic-debugging` — copy upstream files

**Files:**
- Create: `superjawn/skills/systematic-debugging/` (full upstream tree)

- [ ] **Step 1: Verify on the right branch**

```bash
cd ~/projects/claude-skills-journalism
git branch --show-current
```

Expected: `feat/superjawn-batch-2-debugging-triad`. The branch was created at brainstorming time when the spec was committed. If the output is `master`, run `git checkout feat/superjawn-batch-2-debugging-triad`.

- [ ] **Step 2: Copy upstream systematic-debugging directory**

```bash
cp -r ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/systematic-debugging \
      ~/projects/claude-skills-journalism/superjawn/skills/systematic-debugging
```

- [ ] **Step 3: Verify all files copied**

```bash
find superjawn/skills/systematic-debugging -type f | sort
```

Expected (4 files):

```
superjawn/skills/systematic-debugging/SKILL.md
superjawn/skills/systematic-debugging/condition-based-waiting.md
superjawn/skills/systematic-debugging/defense-in-depth.md
superjawn/skills/systematic-debugging/root-cause-tracing.md
```

If the upstream directory has additional files not listed here, copy them too — the upstream tree is the source of truth.

- [ ] **Step 4: Verify SKILL.md is unchanged from upstream**

```bash
diff superjawn/skills/systematic-debugging/SKILL.md \
     ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/systematic-debugging/SKILL.md
```

Expected: no output (files identical at this point — modifications come in next task).

---

## Task 2: Port `systematic-debugging` — add MIT attribution + research phase

**Files:**
- Modify: `superjawn/skills/systematic-debugging/SKILL.md`

The research phase from the spec inserts between Phase 1 (Root Cause Investigation) and Phase 2 (Pattern Analysis), at the same heading level as the existing phases (`###`). The skill already has `## The Four Phases` as the parent heading; the research phase becomes a fifth `###` section nested under it. The skill text in the parent heading's intro paragraph also needs a sentence noting research fires between Phase 1 and Phase 2.

- [ ] **Step 1: Add MIT attribution comment**

Edit `superjawn/skills/systematic-debugging/SKILL.md`. Add this HTML comment immediately after the YAML frontmatter (after the closing `---`) and before the `# Systematic Debugging` heading:

```html
<!--
Adapted from obra/superpowers systematic-debugging skill (v5.0.7), MIT-licensed,
copyright 2025 Jesse Vincent. Modifications copyright 2026 Joe Amditis.
v0.3.0 adds a research phase between Phase 1 (Root Cause Investigation)
and Phase 2 (Pattern Analysis) per the v0.2.0 architecture's
research-at-entry-point rule (debugging is an entry-point stage —
the work begins from a bug report, not an upstream artifact).
See CREDITS.md.
-->
```

- [ ] **Step 2: Update the parent heading's intro paragraph**

Find the existing line beneath `## The Four Phases` that reads `You MUST complete each phase before proceeding to the next.` Replace with:

```markdown
You MUST complete each phase before proceeding to the next. Between Phase 1 and Phase 2, run the research phase (default-on, see below) to gather external context that pattern analysis can build on.
```

- [ ] **Step 3: Insert the `### Research phase` section between Phase 1 and Phase 2**

Find the end of `### Phase 1: Root Cause Investigation` (which ends with the last item of its sub-step "5. Trace Data Flow"). The next heading is `### Phase 2: Pattern Analysis`.

Insert the following new `### Research phase` section after Phase 1 ends and before Phase 2 begins:

````markdown
### Research phase

After Phase 1 (Root Cause Investigation) and before Phase 2 (Pattern Analysis), gather outside context. Phase 1 produced internal evidence (error messages, repro steps, recent diffs); the research phase adds external information that pattern analysis can build on.

**Default-on.** Skip only with explicit, justified statement per the skip protocol below.

**This phase only fires when entering Phase 2.** If Phase 1 yielded the root cause directly and you're going Phase 1 → Phase 4 (Implementation), you don't reach the research phase. The skip protocol governs the case where you've decided pattern analysis is needed but want to skip the research that would inform it.

#### 1. Default research kinds (all four)

| Kind | Purpose | Tool |
|---|---|---|
| Web | Search the literal error string and the framework/library's open GitHub issues for prior reports | WebSearch + WebFetch (via subagent) |
| Codebase prior-bugs | `git log --grep` for related historical fixes; spots regressions and prior work in the same area | Bash + Grep (via subagent) |
| Authoritative | Fetch current live docs/spec for the API or library involved; catches "am I using this wrong" cases | WebFetch (via subagent) |
| User-context | Check `MEMORY.md` for related debugging history | Read (inline, no subagent) |

#### 2. Dispatch

Three subagents in parallel (web via `general-purpose`, codebase prior-bugs via `Explore`, authoritative via `general-purpose`) plus the inline memory check running concurrently in the main thread. The subagent prompts each carry the bug context from Phase 1 (error message, repro, current diff) so they don't have to rediscover it.

#### 3. Findings location

Findings land in `.superpowers/debug-log-<slug>.md` where `<slug>` is `YYYY-MM-DD-<short-bug-description>`. Examples:

```
.superpowers/debug-log-2026-05-05-test-failure-auth-handler.md
.superpowers/debug-log-2026-05-12-build-fails-on-arm64.md
.superpowers/debug-log-2026-06-03-flaky-redis-pubsub.md
```

The skill creates the file on first invocation if it doesn't exist; subsequent invocations on the same bug append. Each entry includes:

- Date/time of the research run
- Which research kinds fired (or were skipped, with the locked skip-justification line)
- Findings: 3-5 bullets per kind that fired, including load-bearing links/refs
- "Considered but ruled out" notes so future-you knows what was checked

The directory `.superpowers/` is git-ignored by upstream convention.

#### 4. Skip protocol

If skipping, write one line to `.superpowers/debug-log-<slug>.md`: `Skipped research because <reason>. <Verifiable pointer if applicable>.`

**Valid reasons:**
- Trivial scope (typo, comment edit, single-line config)
- Fresh prior research — same topic in current session OR within last 7 days with verifiable spec/plan pointer. **If the pointer doesn't resolve, the skip is invalid.** (Beyond 7 days, repeat the research even if you remember the prior findings — the landscape drifts.)
- User explicit — **must quote the phrase** that authorized the skip.
- Repeat of identical task — **must include a pointer** to the prior successful run.

**Invalid reasons:** "I think I know", "seems straightforward", "moving fast", "user wants this done quickly", "already familiar with this codebase". If those are tempting, do the research.

````

- [ ] **Step 4: Verify section count and structure**

```bash
grep -c "^## " superjawn/skills/systematic-debugging/SKILL.md
grep -c "^## " ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/systematic-debugging/SKILL.md
```

The two counts should be identical — we added a `###` section, not a `##`.

```bash
grep -c "^### " superjawn/skills/systematic-debugging/SKILL.md
grep -c "^### " ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/systematic-debugging/SKILL.md
```

The superjawn count should be exactly +1 from upstream (the new `### Research phase` section).

```bash
grep -n "^### " superjawn/skills/systematic-debugging/SKILL.md | head -10
```

Expected to see, in order: Phase 1, Research phase, Phase 2, Phase 3, Phase 4. The Research phase line should appear between Phase 1 and Phase 2.

- [ ] **Step 5: Verify the locked skip-protocol text is byte-identical to Batch 1**

The valid/invalid skip reasons in Step 3's inserted text are LOCKED — they must match the text in Batch 1's ported skills (`superjawn/skills/brainstorming/SKILL.md` and the v0.2.0-stripped `superjawn/skills/writing-plans/SKILL.md` had it before strip; brainstorming still does).

```bash
# Extract just the locked block from brainstorming
grep -A 6 "^\*\*Valid reasons:\*\*" superjawn/skills/brainstorming/SKILL.md | head -7

# Extract from systematic-debugging
grep -A 6 "^\*\*Valid reasons:\*\*" superjawn/skills/systematic-debugging/SKILL.md | head -7
```

The two blocks should be identical text. If they diverge, fix systematic-debugging's text to match brainstorming's.

- [ ] **Step 6: Commit**

```bash
# Use directory form so the supporting files copied in Task 1
# (root-cause-tracing.md, defense-in-depth.md, condition-based-waiting.md)
# get tracked along with the modified SKILL.md
git add superjawn/skills/systematic-debugging/
git commit -m "feat(superjawn): port systematic-debugging with research phase

Adds research phase between Phase 1 (Root Cause Investigation) and
Phase 2 (Pattern Analysis) per the v0.2.0 architecture. Four default
research kinds: web, codebase prior-bugs, authoritative, user-context.
Three parallel subagents (web, codebase, authoritative) plus inline
memory check. Findings land at .superpowers/debug-log-<slug>.md.

Skip protocol byte-identical to Batch 1's locked text. Skill text
includes a Phase-2-entry clarification: research fires only when
entering Phase 2; Phase 1 → Phase 4 paths don't reach it.

Supporting reference files (root-cause-tracing, defense-in-depth,
condition-based-waiting) ported verbatim alongside the modified SKILL.md."
```

---

## Task 3: Port `systematic-debugging` — rewrite cross-references

**Files:**
- Modify: `superjawn/skills/systematic-debugging/SKILL.md`

Per the spec's Section 2 cross-ref handling rules, references to ported-this-batch-or-prior skills become `superjawn:`. The two cross-refs to handle in systematic-debugging are `superpowers:test-driven-development` and `superpowers:verification-before-completion` — both ported in this batch.

**EXPLICIT NON-RENAMES** — same as Batch 1's locked rule:
- `.superpowers/` (runtime directory, including the new `.superpowers/debug-log-*.md` paths) — keeps the upstream convention
- `docs/superpowers/` (project doc directory paths) if they appear — keeps the convention
- `obra/superpowers` (upstream attribution links) — pure attribution, stays as-is

Only `superpowers:<skill-name>` namespaced skill references get rewritten, and only when the skill is in the ported set.

- [ ] **Step 1: Inventory existing `superpowers:` references**

```bash
grep -nE "superpowers:[a-z-]+" superjawn/skills/systematic-debugging/SKILL.md
```

Expected hits: at least `superpowers:test-driven-development` and `superpowers:verification-before-completion`. Note the line numbers.

- [ ] **Step 2: Rewrite refs to ported skills**

For each line that references `superpowers:test-driven-development` or `superpowers:verification-before-completion`, rewrite to the `superjawn:` form. Use Edit tool with the exact line context to ensure uniqueness.

- `superpowers:test-driven-development` → `superjawn:test-driven-development`
- `superpowers:verification-before-completion` → `superjawn:verification-before-completion`

- [ ] **Step 3: Verify the rewrite**

```bash
grep -n "test-driven-development" superjawn/skills/systematic-debugging/SKILL.md
grep -n "verification-before-completion" superjawn/skills/systematic-debugging/SKILL.md
```

Every match should now show `superjawn:test-driven-development` or `superjawn:verification-before-completion` — no `superpowers:` prefix on those two skills, and no bare names without a namespace.

- [ ] **Step 4: Verify no fictional namespaces**

```bash
grep -oE "superpowers:[a-z-]+" superjawn/skills/systematic-debugging/SKILL.md | sort -u | while read ref; do
  skill="${ref#superpowers:}"
  if [ -d "$HOME/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/$skill" ]; then
    echo "OK: $ref"
  else
    echo "MISSING UPSTREAM: $ref"
  fi
done
```

Expected: every `superpowers:` reference left in the file resolves to a real upstream skill directory. Any "MISSING UPSTREAM" output means a fictional reference exists — track it down and either rewrite it or remove the namespace prefix per the Batch 1 fictional-namespace lesson (Task 8 of Batch 1 caught `superpowers:frontend-design` and `superpowers:mcp-builder`; both rolled back to bare names).

- [ ] **Step 5: Commit**

```bash
git add superjawn/skills/systematic-debugging/SKILL.md
git commit -m "refactor(superjawn): rewrite systematic-debugging cross-refs

test-driven-development and verification-before-completion are both
ported in this batch, so their cross-references become superjawn:.
All remaining superpowers: references verified to exist upstream."
```

---

## Task 4: Port `test-driven-development` — copy upstream files

**Files:**
- Create: `superjawn/skills/test-driven-development/` (full upstream tree)

- [ ] **Step 1: Copy upstream test-driven-development directory**

```bash
cp -r ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/test-driven-development \
      ~/projects/claude-skills-journalism/superjawn/skills/test-driven-development
```

- [ ] **Step 2: Verify files copied**

```bash
find superjawn/skills/test-driven-development -type f | sort
```

Expected (2 files):

```
superjawn/skills/test-driven-development/SKILL.md
superjawn/skills/test-driven-development/testing-anti-patterns.md
```

If the upstream tree has additional files (e.g., a `references/` subdirectory), they should also have copied — verify the count matches the upstream:

```bash
find ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/test-driven-development -type f | wc -l
find superjawn/skills/test-driven-development -type f | wc -l
```

The two counts should be identical.

- [ ] **Step 3: Verify SKILL.md matches upstream**

```bash
diff superjawn/skills/test-driven-development/SKILL.md \
     ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/test-driven-development/SKILL.md
```

Expected: no output.

---

## Task 5: Port `test-driven-development` — add MIT attribution + rewrite cross-references

**Files:**
- Modify: `superjawn/skills/test-driven-development/SKILL.md`

This is a consumer-category port: no research/freshness phase, just attribution + cross-refs.

- [ ] **Step 1: Add MIT attribution comment**

Edit `superjawn/skills/test-driven-development/SKILL.md`. Add this HTML comment immediately after the YAML frontmatter and before the `# Test-Driven Development (TDD)` heading:

```html
<!--
Adapted from obra/superpowers test-driven-development skill (v5.0.7),
MIT-licensed, copyright 2025 Jesse Vincent. Modifications copyright
2026 Joe Amditis. v0.3.0 ports as a consumer category — no research
phase per the v0.2.0 architecture, since TDD is a sub-skill called
within other workflows whose specs/plans already encode the research
conclusions. The artifact handoff carries those conclusions.
See CREDITS.md.
-->
```

- [ ] **Step 2: Inventory existing `superpowers:` references**

```bash
grep -nE "superpowers:[a-z-]+" superjawn/skills/test-driven-development/SKILL.md
```

Note the line numbers and target skills. Most of TDD's outbound references are to systematic-debugging and verification-before-completion (both in this batch).

- [ ] **Step 3: Rewrite refs to ported skills**

For each line referencing a skill that has been ported in Batch 1 or Batch 2, rewrite to `superjawn:`. The full ported set after Batch 2 is:

- brainstorming, writing-plans, executing-plans (Batch 1)
- systematic-debugging, test-driven-development, verification-before-completion (Batch 2)

So any `superpowers:<one-of-those-six>` becomes `superjawn:<same-name>`. Anything else (subagent-driven-development, dispatching-parallel-agents, using-git-worktrees, finishing-a-development-branch, using-superpowers, writing-skills, receiving-code-review, requesting-code-review) stays at `superpowers:`.

- [ ] **Step 4: Verify the rewrite**

```bash
grep -nE "superjawn:[a-z-]+" superjawn/skills/test-driven-development/SKILL.md
grep -nE "superpowers:[a-z-]+" superjawn/skills/test-driven-development/SKILL.md
```

Sanity check: every `superjawn:` reference is to one of the six ported skills above, and every remaining `superpowers:` reference is to one of the eight not-yet-ported skills.

- [ ] **Step 5: Verify no fictional namespaces**

```bash
grep -oE "superpowers:[a-z-]+" superjawn/skills/test-driven-development/SKILL.md | sort -u | while read ref; do
  skill="${ref#superpowers:}"
  if [ -d "$HOME/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/$skill" ]; then
    echo "OK: $ref"
  else
    echo "MISSING UPSTREAM: $ref"
  fi
done
```

Expected: every entry "OK". Any "MISSING UPSTREAM" means a fictional reference — fix per Batch 1's lesson.

- [ ] **Step 6: Commit**

```bash
git add superjawn/skills/test-driven-development/
git commit -m "feat(superjawn): port test-driven-development as consumer

Pure port: MIT attribution comment + dual-namespace cross-reference
rewrites only. No research phase per the v0.2.0 architecture — TDD
is a sub-skill called within other workflows whose specs/plans already
encode the research conclusions."
```

---

## Task 6: Port `verification-before-completion` — copy upstream files

**Files:**
- Create: `superjawn/skills/verification-before-completion/` (full upstream tree)

- [ ] **Step 1: Copy upstream verification-before-completion directory**

```bash
cp -r ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/verification-before-completion \
      ~/projects/claude-skills-journalism/superjawn/skills/verification-before-completion
```

- [ ] **Step 2: Verify files copied**

```bash
find superjawn/skills/verification-before-completion -type f | sort
find ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/verification-before-completion -type f | sort
```

The two outputs should mirror each other. Expected to be a single SKILL.md, but if upstream has supporting files, they should all have copied.

- [ ] **Step 3: Verify SKILL.md matches upstream**

```bash
diff superjawn/skills/verification-before-completion/SKILL.md \
     ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/verification-before-completion/SKILL.md
```

Expected: no output.

---

## Task 7: Port `verification-before-completion` — add MIT attribution + rewrite cross-references

**Files:**
- Modify: `superjawn/skills/verification-before-completion/SKILL.md`

Same shape as Task 5 (consumer-category pure port).

- [ ] **Step 1: Add MIT attribution comment**

Edit `superjawn/skills/verification-before-completion/SKILL.md`. Add this HTML comment immediately after the YAML frontmatter and before the `# Verification Before Completion` heading:

```html
<!--
Adapted from obra/superpowers verification-before-completion skill
(v5.0.7), MIT-licensed, copyright 2025 Jesse Vincent. Modifications
copyright 2026 Joe Amditis. v0.3.0 ports as a consumer category — no
research phase per the v0.2.0 architecture. Verification is a gate
function: the verification command is determined by what was just
built, so external research adds no value here.
See CREDITS.md.
-->
```

- [ ] **Step 2: Inventory existing `superpowers:` references**

```bash
grep -nE "superpowers:[a-z-]+" superjawn/skills/verification-before-completion/SKILL.md
```

Note the line numbers and target skills.

- [ ] **Step 3: Rewrite refs to ported skills**

For each line referencing a skill in the six-skill ported set, rewrite to `superjawn:`. Anything else stays at `superpowers:`. Same rule as Task 5 Step 3.

- [ ] **Step 4: Verify the rewrite**

```bash
grep -nE "superjawn:[a-z-]+" superjawn/skills/verification-before-completion/SKILL.md
grep -nE "superpowers:[a-z-]+" superjawn/skills/verification-before-completion/SKILL.md
```

Sanity-check the dual-namespace rule held.

- [ ] **Step 5: Verify no fictional namespaces**

```bash
grep -oE "superpowers:[a-z-]+" superjawn/skills/verification-before-completion/SKILL.md | sort -u | while read ref; do
  skill="${ref#superpowers:}"
  if [ -d "$HOME/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/$skill" ]; then
    echo "OK: $ref"
  else
    echo "MISSING UPSTREAM: $ref"
  fi
done
```

Expected: every entry "OK".

- [ ] **Step 6: Commit**

```bash
git add superjawn/skills/verification-before-completion/
git commit -m "feat(superjawn): port verification-before-completion as consumer

Pure port: MIT attribution comment + dual-namespace cross-reference
rewrites only. No research phase per the v0.2.0 architecture —
verification is a gate function whose command is determined by what
was just built; external research adds no value."
```

---

## Task 8: Bump plugin version + update README + update CREDITS

**Files:**
- Modify: `superjawn/.claude-plugin/plugin.json`
- Modify: `superjawn/README.md`
- Modify: `superjawn/CREDITS.md`

- [ ] **Step 1: Bump plugin.json from 0.2.0 to 0.3.0**

Edit `superjawn/.claude-plugin/plugin.json`. Change the `version` field:

```diff
-  "version": "0.2.0",
+  "version": "0.3.0",
```

The `description` field can stay as-is (it already names systematic-debugging in the entry-point list, which becomes accurate at this batch).

- [ ] **Step 2: Verify plugin.json parses**

```bash
python3 -c "import json; m = json.load(open('superjawn/.claude-plugin/plugin.json')); print(m['version'])"
```

Expected: `0.3.0`.

- [ ] **Step 3: Update README skill status table**

Edit `superjawn/README.md`. In the Skills table, change three rows from `Pending (Batch 2)` to `Ported (Batch 2)`:

- `systematic-debugging` row → status becomes `Ported (Batch 2)`
- `test-driven-development` row → status becomes `Ported (Batch 2)`
- `verification-before-completion` row → status becomes `Ported (Batch 2)`

- [ ] **Step 4: Update CREDITS.md with v0.3.0 modifications entry**

Edit `superjawn/CREDITS.md`. Find the `## Modifications from upstream` section. Insert a new bullet block at the TOP of that section (so v0.3.0 reads above v0.2.0):

```markdown
**v0.3.0 Batch 2 (current).** Three skills ported under the v0.2.0 architecture:
- `systematic-debugging` — research category. Research phase inserted between Phase 1 (Root Cause Investigation) and Phase 2 (Pattern Analysis), default-on. Four research kinds (web, codebase prior-bugs, authoritative, user-context) dispatched as 3 parallel subagents + inline memory. Findings at `.superpowers/debug-log-<slug>.md`. Skip protocol byte-identical to Batch 1's locked text.
- `test-driven-development` — consumer category. Pure port (attribution + cross-refs only). No research phase: TDD is a sub-skill whose triggering spec/plan already encodes research conclusions.
- `verification-before-completion` — consumer category. Pure port. No research phase: verification is a gate function determined by what was just built.

```

The blank line at the end is intentional — it separates the v0.3.0 block from the existing v0.2.0 block beneath it.

- [ ] **Step 5: Commit**

```bash
git add superjawn/.claude-plugin/plugin.json superjawn/README.md superjawn/CREDITS.md
git commit -m "chore(superjawn): bump 0.2.0 → 0.3.0 for Batch 2 ports

Skill status table marks systematic-debugging, test-driven-development,
and verification-before-completion as Ported. CREDITS.md grows a v0.3.0
modifications entry above the v0.2.0 entry, summarizing the three ports."
```

---

## Task 9: End-of-batch verification + push + open PR

**Files:** None (verification + delivery step)

- [ ] **Step 1: Verify all three skills' files are present**

```bash
find superjawn/skills/{systematic-debugging,test-driven-development,verification-before-completion} -type f | sort
```

Expected: all the files mapped in the `File structure` section near the top of this plan. Specifically systematic-debugging has 4 files (SKILL.md + 3 supporting), TDD has 2 files (SKILL.md + testing-anti-patterns), verification has at least SKILL.md.

- [ ] **Step 2: Cross-ref resolution sweep across the three new skills**

```bash
# Find every superjawn: reference
grep -rEh "superjawn:[a-z-]+" \
  superjawn/skills/systematic-debugging/ \
  superjawn/skills/test-driven-development/ \
  superjawn/skills/verification-before-completion/ \
  | grep -oE "superjawn:[a-z-]+" | sort -u
```

Expected output is a subset of the six-skill ported set: `superjawn:brainstorming`, `superjawn:writing-plans`, `superjawn:executing-plans`, `superjawn:systematic-debugging`, `superjawn:test-driven-development`, `superjawn:verification-before-completion`. Any other name in the output indicates a typo or fictional reference — fix it.

- [ ] **Step 3: Upstream-existence sweep on remaining `superpowers:` references**

```bash
grep -rh "superpowers:[a-z-]\+" \
  superjawn/skills/systematic-debugging/ \
  superjawn/skills/test-driven-development/ \
  superjawn/skills/verification-before-completion/ \
  | grep -oE "superpowers:[a-z-]+" | sort -u | while read ref; do
  skill="${ref#superpowers:}"
  if [ -d "$HOME/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/$skill" ]; then
    echo "OK: $ref"
  else
    echo "MISSING UPSTREAM: $ref"
  fi
done
```

Expected: every line "OK". Any "MISSING UPSTREAM" means a fictional reference snuck in.

- [ ] **Step 4: Attribution-comment sweep**

```bash
for f in superjawn/skills/systematic-debugging/SKILL.md \
         superjawn/skills/test-driven-development/SKILL.md \
         superjawn/skills/verification-before-completion/SKILL.md; do
  if grep -q "Adapted from obra/superpowers" "$f"; then
    echo "OK: $f has attribution"
  else
    echo "MISSING ATTRIBUTION: $f"
  fi
done
```

Expected: three "OK" lines.

- [ ] **Step 5: Plugin manifest validates**

```bash
claude plugin validate ./superjawn
```

Expected: `✔ Validation passed`.

- [ ] **Step 6: Commit summary check**

```bash
git log master..HEAD --oneline
```

Expected: 8 commits in this batch — three for systematic-debugging (copy implicit, modify, cross-refs), one for TDD (copy implicit + modify combined under the consumer pattern), one for verification-before-completion (same), one for the version/README/CREDITS bump, and the spec doc commit from brainstorming. Plus this verification commit if you choose to make one. Commit count being slightly off is fine; the commits should be logically distinct.

- [ ] **Step 7: Push branch**

```bash
git push -u origin feat/superjawn-batch-2-debugging-triad
```

- [ ] **Step 8: Open PR**

```bash
gh pr create --title "superjawn v0.3.0: Batch 2 ports (debugging triad)" \
             --body "$(cat <<'EOF'
## Summary

Ports the second batch of three superpowers skills into superjawn under the v0.2.0 architecture. Ships as v0.3.0. After this PR, 6 of 14 upstream skills are ported.

- `systematic-debugging` (research category) — research phase inserted between Phase 1 (Root Cause Investigation) and Phase 2 (Pattern Analysis). Four default research kinds dispatched as 3 parallel subagents + inline memory check. Findings at `.superpowers/debug-log-<slug>.md`. Skip protocol byte-identical to Batch 1's locked text.
- `test-driven-development` (consumer) — pure port: MIT attribution + cross-refs only.
- `verification-before-completion` (consumer) — pure port: MIT attribution + cross-refs only.

## Spec and plan

- Spec: `specs/2026-05-05-superjawn-batch-2-design.md`
- Plan: `plans/2026-05-05-superjawn-batch-2.md`
- Parent architecture: `specs/2026-05-05-superjawn-research-phases-design.md` (v0.2.0)

## Test plan

- [x] Cross-ref resolution: every `superjawn:` reference in the three new SKILL.md files is in the six-skill ported set
- [x] Upstream-existence: every remaining `superpowers:` reference resolves to a real upstream skill
- [x] Attribution comment present in all three SKILL.md files
- [x] `claude plugin validate ./superjawn` passes
- [ ] Post-merge smoke test in a fresh session: invoke `superjawn:systematic-debugging` on a small contrived bug, confirm research phase fires correctly, findings land at `.superpowers/debug-log-<slug>.md`, skip protocol works (deferred per the loadability caveat — sessions started before plugin install/reinstall can't load `superjawn:*`).

## Out of scope

- Smoke testing must happen in a fresh session post-merge — the same session as the marketplace operation can't load the new skill.
- Batches 3-5 each get their own brainstorm/spec/plan cycle after this PR lands.
EOF
)"
```

The PR title and body have zero AI attribution per global rules.

---

## Self-review

### Spec coverage check

| Spec section | Plan task(s) covering it |
|---|---|
| §1 Per-skill plan — systematic-debugging research phase | Tasks 1-3 (copy, attribution + research phase insertion, cross-refs) |
| §1 Per-skill plan — test-driven-development consumer port | Tasks 4-5 (copy, attribution + cross-refs) |
| §1 Per-skill plan — verification-before-completion consumer port | Tasks 6-7 (copy, attribution + cross-refs) |
| §2 Cross-ref handling rules (six-skill ported set, fictional-namespace verification) | Tasks 3, 5, 7 each include the upstream-existence verification grep |
| §3 Build sequence (systematic-debugging first, then consumers, then version bump, then verification) | Tasks 1-9 follow that order exactly |
| §4 Testing approach — cross-ref resolution, upstream-existence, attribution presence | Task 9 sweep covers all three |
| §4 Testing approach — research-phase smoke test (post-merge, fresh session) | Task 9 PR test plan flags this as deferred per the loadability caveat |
| §5 Versioning — v0.3.0 ships this PR | Task 8 |

### Placeholder scan

- "YYYY-MM-DD-<short-bug-description>" in Task 2 Step 3's slug examples — intentional, this is the format users substitute when invoking the skill, not a placeholder for the engineer to fill.
- "v0.3.0 Batch 2 (current)" in Task 8 Step 4 — intentional copy text, not a placeholder.
- No "TBD", "TODO", "implement later", "fill in details", or "similar to Task N" patterns in any task.

### Type consistency check

- "Skipped research because" phrase used identically in Task 2 Step 3's locked block and verifiable against Batch 1's brainstorming SKILL.md (Task 2 Step 5 is the verification).
- "`.superpowers/debug-log-<slug>.md`" path used consistently across the spec excerpt in Task 2 and the PR body in Task 9.
- Cross-ref rule consistent: "the six-skill ported set" referenced identically in Tasks 3, 5, 7, 9.
- Attribution-comment opening line ("Adapted from obra/superpowers") used identically in Tasks 2, 5, 7, and verified by the Task 9 attribution sweep.
- Slug format `YYYY-MM-DD-<short-bug-description>` used consistently (no drift to `YYYY_MM_DD` or other variants).

No type/naming drift found.

### Engineer-readability check

Each task has explicit file paths, exact bash commands, and expected outputs. The locked skip-protocol text in Task 2 Step 3 is reproduced in full rather than referenced via "see Batch 1" so an engineer reading tasks out of order has the complete text. The cross-ref handling rules are repeated in the prose intros of Tasks 3, 5, 7 (six-skill ported set + the eight not-yet-ported skills explicitly listed in Task 5 Step 3) so each task is self-contained.

---

## Execution handoff

**Plan complete and saved to `plans/2026-05-05-superjawn-batch-2.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, two-stage review (spec compliance + code quality), fast iteration. The locked skip-protocol text in Task 2 Step 3 and the Phase-2-entry clarification language are the most likely places for drift, so per-task review catches them early.
2. **Inline Execution** — execute tasks in this session using `superpowers:executing-plans`. Faster wall-clock but no automatic review checkpoints.

Which approach?
