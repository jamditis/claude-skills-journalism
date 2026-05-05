# superjawn Batch 1 implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap the `superjawn` plugin inside `claude-skills-journalism` and port the foundation triad of skills (`brainstorming`, `writing-plans`, `executing-plans`) with a default-on research phase wired into each.

**Architecture:** New plugin directory `superjawn/` registered in the existing marketplace. Upstream MIT-licensed skill files copied into `superjawn/skills/<name>/`, modified to add a `## Research phase` section per the design spec's Section 2 taxonomy, with cross-references to ported skills rewritten to `superjawn:` namespace and references to not-yet-ported skills temporarily kept at `superpowers:` (dual-namespace mode). Both upstream `superpowers` and `superjawn` plugins stay enabled during the migration; upstream gets disabled only at v1.0.0.

**Tech Stack:** Markdown (skill files), JSON (plugin manifest + marketplace), bash (smoke tests).

**Source spec:** `specs/2026-05-05-superjawn-research-phases-design.md` (commit `ef80468` on branch `docs/superjawn-research-phases-spec`).

**Scope:** Plugin scaffold + Batch 1 only. Batches 2–5 each get their own plan generated after Batch 1 lands and is validated.

---

## File structure

**Created in this plan:**

```
superjawn/
├── .claude-plugin/
│   └── plugin.json                                    # Plugin manifest
├── LICENSE                                            # MIT, dual copyright Jesse Vincent + Joe Amditis
├── CREDITS.md                                         # Upstream attribution + baseline tracking
├── README.md                                          # Description, install, disable-upstream notes
└── skills/
    ├── brainstorming/
    │   ├── SKILL.md                                   # Modified copy of upstream
    │   ├── visual-companion.md                        # Verbatim copy of upstream
    │   ├── spec-document-reviewer-prompt.md           # Verbatim copy of upstream
    │   └── scripts/
    │       ├── frame-template.html                    # Verbatim
    │       ├── helper.js                              # Verbatim
    │       ├── server.cjs                             # Verbatim
    │       ├── start-server.sh                        # Verbatim
    │       └── stop-server.sh                         # Verbatim
    ├── writing-plans/
    │   ├── SKILL.md                                   # Modified copy of upstream
    │   └── plan-document-reviewer-prompt.md           # Verbatim copy
    └── executing-plans/
        └── SKILL.md                                   # Modified copy of upstream
```

**Modified in this plan:**

```
.claude-plugin/marketplace.json                        # Add superjawn entry
```

**Responsibility split:**
- `plugin.json` declares the plugin to Claude Code's plugin loader
- `LICENSE` + `CREDITS.md` carry the MIT obligations
- `README.md` is human documentation
- Each `SKILL.md` is the agent-facing skill text Claude reads at invocation
- The non-SKILL files inside each skill directory are reference material the SKILL.md links to (visual companion, reviewer prompts, browser-companion server scripts) — copied verbatim because they don't need research-phase additions

---

## Task 1: Scaffold plugin directory + manifest

**Files:**
- Create: `superjawn/.claude-plugin/plugin.json`

- [ ] **Step 1: Create directory structure**

```bash
cd ~/projects/claude-skills-journalism
mkdir -p superjawn/.claude-plugin superjawn/skills
```

- [ ] **Step 2: Create plugin manifest**

Write `superjawn/.claude-plugin/plugin.json`:

```json
{
  "name": "superjawn",
  "version": "0.1.0",
  "description": "Research-augmented skills derived from obra/superpowers — adds default-on research phases to each skill in the workflow",
  "author": {
    "name": "Joe Amditis",
    "email": "jamditis@gmail.com"
  }
}
```

- [ ] **Step 3: Verify file is valid JSON**

```bash
python3 -c "import json; json.load(open('superjawn/.claude-plugin/plugin.json'))"
```

Expected: no output (success). Any output = parse error.

- [ ] **Step 4: Commit**

```bash
git add superjawn/.claude-plugin/plugin.json
git commit -m "feat(superjawn): scaffold plugin manifest"
```

---

## Task 2: Add LICENSE and CREDITS.md

**Files:**
- Create: `superjawn/LICENSE`
- Create: `superjawn/CREDITS.md`

- [ ] **Step 1: Write LICENSE (MIT, dual copyright)**

Write `superjawn/LICENSE`:

```
MIT License

Copyright (c) 2025 Jesse Vincent (original superpowers skills)
Copyright (c) 2026 Joe Amditis (superjawn modifications)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Write CREDITS.md**

Write `superjawn/CREDITS.md`:

```markdown
# Credits

`superjawn` is a research-augmented variant of the [superpowers](https://github.com/obra/superpowers) plugin by Jesse Vincent. Original work is MIT-licensed; modifications carry the same license.

## Upstream baseline

Synced against upstream `obra/superpowers` v5.0.7 (commit: <fill in upstream commit SHA at first port>) on 2026-05-05.

## Upstream changes ported since baseline

(none yet — list each port as it lands, with link to upstream commit)

## Modifications from upstream

Each skill in this plugin adds a `## Research phase` section relative to the upstream version. See `specs/2026-05-05-superjawn-research-phases-design.md` for the design rationale.
```

- [ ] **Step 3: Commit**

```bash
git add superjawn/LICENSE superjawn/CREDITS.md
git commit -m "feat(superjawn): add LICENSE and upstream attribution"
```

---

## Task 3: Add README.md

**Files:**
- Create: `superjawn/README.md`

- [ ] **Step 1: Write README**

Write `superjawn/README.md`:

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add superjawn/README.md
git commit -m "docs(superjawn): add README with skill status table and coexistence notes"
```

---

## Task 4: Register superjawn in marketplace.json

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Read current marketplace.json**

```bash
cat .claude-plugin/marketplace.json | python3 -m json.tool | head -40
```

Note the existing plugin entries (autocontext, pdf-design, pdf-playground) — superjawn entry will follow the same shape.

- [ ] **Step 2: Add superjawn entry**

Edit `.claude-plugin/marketplace.json`. Inside the `"plugins"` array, add a new object after the existing entries:

```json
    {
      "name": "superjawn",
      "description": "Research-augmented skills derived from obra/superpowers — default-on research phase per skill",
      "version": "0.1.0",
      "author": {
        "name": "Joe Amditis",
        "email": "jamditis@gmail.com"
      },
      "source": "./superjawn",
      "category": "Productivity"
    }
```

Insert with a leading comma after the previous entry's closing brace.

- [ ] **Step 3: Verify JSON parses**

```bash
python3 -c "import json; m = json.load(open('.claude-plugin/marketplace.json')); names = [p['name'] for p in m['plugins']]; print(names)"
```

Expected output: `['autocontext', 'pdf-design', 'pdf-playground', 'superjawn']`

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat(marketplace): register superjawn plugin"
```

---

## Task 5: Validate manifest (live install deferred to post-merge)

**Files:** None (validation step)

**Discovery during execution (2026-05-05):** The `claude-skills-journalism` marketplace pulls from the GitHub remote (`https://github.com/jamditis/claude-skills-journalism.git`), cached at `~/.claude/plugins/marketplaces/claude-skills-journalism/`. `claude plugin install` reads only from that cache — it cannot see local feature-branch edits before they're pushed and merged. Live install verification therefore can't run until this PR merges to master and the marketplace cache refreshes.

The substitute is `claude plugin validate <plugin-dir>`, which confirms the manifest would install correctly without actually pulling it through the marketplace.

- [ ] **Step 1: Validate the plugin manifest**

```bash
cd /home/jamditis/projects/claude-skills-journalism
claude plugin validate ./superjawn
```

Expected: `✔ Validation passed`. Any failure means the manifest has a problem — fix before continuing.

- [ ] **Step 2: Verify the marketplace entry agrees with `plugin.json`**

```bash
claude plugin tag --dry-run ./superjawn
```

Expected: success, with no version-mismatch warnings for superjawn (other plugins in the marketplace may have pre-existing drift — see issue #33; ignore those for this task).

- [ ] **Step 3: Defer live install verification until post-merge**

Once this PR merges to master, run on a fresh machine or after a marketplace update:

```bash
claude plugin marketplace update claude-skills-journalism
claude plugin install superjawn@claude-skills-journalism
claude plugin list | grep superjawn      # should show: superjawn 0.1.0
```

Then in a fresh `claude` session, confirm `superjawn:` skill triggers DO appear after Tasks 6–17 ship (since skills are populated then). Document the result in the post-merge follow-up.

---

## Task 6: Port `brainstorming` — copy upstream files

**Files:**
- Create: `superjawn/skills/brainstorming/` (full upstream tree)

- [ ] **Step 1: Copy upstream brainstorming directory**

```bash
cp -r ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/brainstorming \
      ~/projects/claude-skills-journalism/superjawn/skills/brainstorming
```

- [ ] **Step 2: Verify all 8 files copied**

```bash
find superjawn/skills/brainstorming -type f | sort
```

Expected (8 files):

```
superjawn/skills/brainstorming/SKILL.md
superjawn/skills/brainstorming/scripts/frame-template.html
superjawn/skills/brainstorming/scripts/helper.js
superjawn/skills/brainstorming/scripts/server.cjs
superjawn/skills/brainstorming/scripts/start-server.sh
superjawn/skills/brainstorming/scripts/stop-server.sh
superjawn/skills/brainstorming/spec-document-reviewer-prompt.md
superjawn/skills/brainstorming/visual-companion.md
```

If any are missing, re-run Step 1 and check for cp errors.

- [ ] **Step 3: Verify SKILL.md is unchanged from upstream**

```bash
diff superjawn/skills/brainstorming/SKILL.md \
     ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/brainstorming/SKILL.md
```

Expected: no output (files identical at this point — modifications come in next task).

---

## Task 7: Port `brainstorming` — add MIT attribution + research phase + visual companion branding

**Files:**
- Modify: `superjawn/skills/brainstorming/SKILL.md`
- Modify: `superjawn/skills/brainstorming/scripts/frame-template.html`

The existing brainstorming SKILL.md has a checklist with 9 items at "## Checklist". The research phase fits BETWEEN item 3 ("Ask clarifying questions") and item 4 ("Propose 2-3 approaches"). The skill's process flow `digraph` also needs a new `Research phase` node added between those two.

- [ ] **Step 1: Add MIT attribution comment to SKILL.md**

Edit `superjawn/skills/brainstorming/SKILL.md`. Add this HTML comment immediately AFTER the YAML frontmatter (after the closing `---`) and BEFORE the `# Brainstorming Ideas Into Designs` heading:

```html
<!--
Adapted from obra/superpowers brainstorming skill (v5.0.7), MIT-licensed,
copyright 2025 Jesse Vincent. Modifications copyright 2026 Joe Amditis.
Modifications add a default-on research phase between clarifying questions
and approach proposal, plus updates to cross-references and process flow.
See CREDITS.md.
-->
```

- [ ] **Step 2: Insert research phase as checklist item 4 (renumber subsequent)**

Find the `## Checklist` section. Item 3 currently reads `3. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria`. Item 4 currently reads `4. **Propose 2-3 approaches** — with trade-offs and your recommendation`.

Insert a new item 4 between them, and renumber existing items 4–9 to become 5–10:

```markdown
4. **Research phase** — gather outside context (default-on; skip only with explicit justification). See "Research phase" section below.
```

- [ ] **Step 3: Add the Research phase section body**

Find the section break that comes BEFORE `## Process Flow` in the existing SKILL.md. Insert the following new section there:

````markdown
## Research phase

After clarifying questions, before proposing approaches, gather outside context. This is **default-on**: skip only with explicit, justified statement.

### 1. Pick research kinds

From the menu — trends + discourse, patterns, pitfalls, authoritative verification, user-context.

For brainstorming, the **defaults are: web (trends + discourse) and codebase (prior art)**. Add others if the topic warrants — e.g. authoritative verification when an external API is in scope, or user-context when prior decisions in memory are relevant.

### 2. Dispatch

Subagent by default:
- `Explore` for codebase / prior-art questions ("does this repo already have something like X?", "what's the convention for Y here?")
- `general-purpose` for web / discourse / verification ("what's the current best practice for Z?", "what pitfalls do people hit with W?")
- Run multiple in parallel when the kinds are independent

Inline only for light-touch research (single grep, memory check).

### 3. Record findings

Write 3–5 tight bullets into the spec doc under a new `## Research notes` section. Include load-bearing links/refs and anything considered-but-ruled-out so future-you knows it was checked.

### 4. Skip protocol

If skipping, write one line into the spec doc: `Skipped research because <reason>. <Verifiable pointer if applicable>.`

**Valid reasons:**
- Trivial scope (typo, comment edit, single-line config)
- Fresh prior research — same topic in current session OR within last 7 days with verifiable spec/plan pointer
- User explicit (quote the phrase)
- Repeat of identical task (with pointer to prior instance)

**Invalid reasons:** "I think I know", "seems straightforward", "moving fast", "user wants this done quickly", "already familiar with this codebase". If those are tempting, do the research.
````

- [ ] **Step 4: Update the process flow `digraph` to include Research phase node**

Find the `digraph brainstorming { ... }` block in the SKILL.md. Currently it has edges: `"Ask clarifying questions" -> "Propose 2-3 approaches"`. Replace that edge with two edges via a new `Research phase` node, and add visual companion's existing flow connections.

Old edge:

```
"Ask clarifying questions" -> "Propose 2-3 approaches";
```

New edges (replacing the old one):

```
"Research phase" [shape=box];
"Ask clarifying questions" -> "Research phase";
"Research phase" -> "Propose 2-3 approaches";
```

Insert the node declaration `"Research phase" [shape=box];` near the other shape declarations at the top of the digraph.

- [ ] **Step 5: Update spec self-review section to check research-findings/skip-line presence**

Find the "**Spec Self-Review:**" subsection. Add a fifth item to the numbered list (after the "Ambiguity check" item):

```markdown
5. **Research phase check:** Does the spec contain either a `## Research notes` section with findings, or a one-line `Skipped research because <reason>` declaration? If neither, the brainstorming flow didn't run correctly — go back to the research phase before continuing.
```

- [ ] **Step 6: Update visual companion header to dual-link**

Edit `superjawn/skills/brainstorming/scripts/frame-template.html`. Around line 199 the upstream header reads:

```html
<h1><a href="https://github.com/obra/superpowers" target="_blank" rel="noopener">Superpowers Brainstorming</a></h1>
```

Replace with the dual-link form (superjawn-primary, parenthetical upstream attribution):

```html
<h1><a href="https://github.com/jamditis/claude-skills-journalism/tree/master/superjawn" target="_blank" rel="noopener">superjawn Brainstorming</a> <span style="font-size: 0.7em; opacity: 0.7;">(forked from <a href="https://github.com/obra/superpowers" target="_blank" rel="noopener">superpowers</a>)</span></h1>
```

This shows "superjawn Brainstorming" linked to your repo as the primary identity, with a smaller parenthetical "forked from superpowers" link pointing at upstream. Best-of-both attribution.

- [ ] **Step 7: Verify edits parse as valid markdown**

```bash
# Quick sanity check — confirm SKILL.md still has the expected sections
grep -c "^## " superjawn/skills/brainstorming/SKILL.md
```

Expected: count is 1 higher than the upstream count (we added `## Research phase`).

```bash
grep -c "^## " ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/brainstorming/SKILL.md
```

Compare the two — superjawn should be exactly +1.

Also verify the HTML edit didn't break the file:

```bash
grep -c "<h1>" superjawn/skills/brainstorming/scripts/frame-template.html
grep "github.com" superjawn/skills/brainstorming/scripts/frame-template.html
```

Expected: one `<h1>` tag, two GitHub URLs visible (jamditis/claude-skills-journalism and obra/superpowers).

- [ ] **Step 8: Commit**

```bash
git add superjawn/skills/brainstorming/
git commit -m "feat(superjawn): port brainstorming with research phase

Adds default-on research phase between clarifying questions and approach
proposal. Subagent dispatch (Explore + general-purpose). Findings recorded
in spec doc; skip protocol with valid/invalid reason whitelist.

Process flow digraph updated. Spec self-review check added.

Visual companion header rebranded to dual-link form: superjawn primary,
parenthetical 'forked from superpowers' attribution."
```

---

## Task 8: Port `brainstorming` — rewrite cross-references (with explicit non-renames)

**Files:**
- Modify: `superjawn/skills/brainstorming/SKILL.md`

Cross-refs from brainstorming go to `writing-plans` (which IS being ported in this batch — rewrite to `superjawn:writing-plans`) and possibly other skills (which are NOT yet ported — keep at `superpowers:` for now per dual-namespace mode).

**EXPLICIT NON-RENAMES** — DO NOT mechanically grep-replace `superpowers` → `superjawn`. The following strings refer to user-data layouts and project conventions that are SHARED across forks, not to skill identifiers, and must remain unchanged:

- `.superpowers/` (runtime directory, e.g. `<project>/.superpowers/brainstorm/<session-id>/`) — referenced in `start-server.sh`, `stop-server.sh`, `visual-companion.md`. Renaming would break any user with existing brainstorm sessions.
- `docs/superpowers/specs/` (project spec directory) — referenced in `SKILL.md` and `spec-document-reviewer-prompt.md`. Renaming would force every superjawn user to choose a different spec home and break continuity with prior work.
- `https://github.com/obra/superpowers` (upstream attribution link) — Task 7 already handled the visual-companion header rebranding to dual-link form. Any other occurrences of this URL are pure attribution and stay as-is.

Only the `superpowers:<skill-name>` namespaced references inside SKILL.md get rewritten. Bare-name references to `writing-plans` (skill name, not directory path) also get rewritten. Everything else stays.

- [ ] **Step 1: Inventory existing cross-refs**

```bash
grep -nE "(superpowers:|writing-plans|frontend-design|mcp-builder)" \
  superjawn/skills/brainstorming/SKILL.md
```

Note each line. Expected refs to update: `writing-plans` mentions (with or without prefix). Refs to `frontend-design` / `mcp-builder` should stay as written (those skills are out of scope for superjawn; they live in upstream or other plugins).

- [ ] **Step 2: Rewrite refs to ported skills**

For each line found that references `writing-plans`, rewrite to `superjawn:writing-plans`. Specifically:

- "invoke writing-plans skill" → "invoke superjawn:writing-plans skill"
- "the writing-plans skill" → "the superjawn:writing-plans skill"
- Any `superpowers:writing-plans` → `superjawn:writing-plans`

**Do NOT add a namespace prefix to `frontend-design` or `mcp-builder` mentions.** These appear in the upstream brainstorming SKILL.md as generic illustrative examples of "implementation skills not to invoke after brainstorming," not as references to specific plugin skills. Verification against upstream `superpowers` v5.0.7 confirms neither name exists in that plugin (`frontend-design` is a separate top-level plugin `frontend-design:frontend-design`; `mcp-builder` doesn't resolve in the current plugin marketplace at all). Leave them bare so the sentence reads as "any of these *kinds* of skills" rather than as fully-qualified references that don't exist.

- [ ] **Step 3: Verify the rewrite**

```bash
grep -n "writing-plans" superjawn/skills/brainstorming/SKILL.md
```

Every line should now show `superjawn:writing-plans` (no bare `writing-plans` and no `superpowers:writing-plans`).

- [ ] **Step 4: Commit**

```bash
git add superjawn/skills/brainstorming/SKILL.md
git commit -m "refactor(superjawn): rewrite brainstorming cross-refs to superjawn namespace"
```

---

## Task 9: Smoke-test `superjawn:brainstorming`

**Files:** None (validation step)

- [ ] **Step 1: Restart the Claude session so the plugin reload picks up the new skill**

Open a fresh `claude` session in `~/projects/claude-skills-journalism`. The available-skills list should now include `superjawn:brainstorming`.

- [ ] **Step 2: Invoke on a tiny real task**

Pick something trivial — e.g. "I want to add a one-line ASCII art header to a script." Invoke `superjawn:brainstorming` on it.

- [ ] **Step 3: Verify the research phase fires**

The skill should:
1. Check project context
2. Ask clarifying questions
3. **Reach the research phase** (this is the new behavior)
4. EITHER dispatch subagents and record findings, OR write a skip line because the task is trivial

Expected outcome: visible evidence that step 3 happened. If the skill jumped from clarifying questions to approach proposal without a research-phase or skip line, the additions didn't take effect — debug before continuing.

- [ ] **Step 4: If skip path — verify skip line format**

The skip line should be exactly: `Skipped research because trivial scope. <Verifiable pointer if applicable>.` Recorded in the spec doc.

If wrong format, the skip protocol section needs revision.

- [ ] **Step 5: Document the smoke test**

Append to `CREDITS.md` under a new `## Smoke tests` heading:

```markdown
## Smoke tests

- 2026-05-XX: `superjawn:brainstorming` invoked on trivial task; research phase fired correctly; skip line recorded with valid format.
```

(Use the actual date of the test.)

- [ ] **Step 6: Commit smoke-test note**

```bash
git add superjawn/CREDITS.md
git commit -m "docs(superjawn): record brainstorming smoke test pass"
```

---

## Task 10: Port `writing-plans` — copy upstream files

**Files:**
- Create: `superjawn/skills/writing-plans/` (full upstream tree)

- [ ] **Step 1: Copy upstream writing-plans directory**

```bash
cp -r ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/writing-plans \
      ~/projects/claude-skills-journalism/superjawn/skills/writing-plans
```

- [ ] **Step 2: Verify both files copied**

```bash
find superjawn/skills/writing-plans -type f | sort
```

Expected (2 files):

```
superjawn/skills/writing-plans/SKILL.md
superjawn/skills/writing-plans/plan-document-reviewer-prompt.md
```

- [ ] **Step 3: Verify SKILL.md matches upstream**

```bash
diff superjawn/skills/writing-plans/SKILL.md \
     ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/writing-plans/SKILL.md
```

Expected: no output.

---

## Task 11: Port `writing-plans` — add MIT attribution + research phase

**Files:**
- Modify: `superjawn/skills/writing-plans/SKILL.md`

writing-plans research stage is "Before drafting plan steps". Default kinds are web (pitfalls in chosen approach), codebase (similar features), and authoritative verification (live API smoke if external systems are in scope).

- [ ] **Step 1: Add MIT attribution comment**

Edit `superjawn/skills/writing-plans/SKILL.md`. Add this HTML comment immediately after the YAML frontmatter and before the `# Writing Plans` heading:

```html
<!--
Adapted from obra/superpowers writing-plans skill (v5.0.7), MIT-licensed,
copyright 2025 Jesse Vincent. Modifications copyright 2026 Joe Amditis.
Modifications add a default-on research phase before plan drafting, plus
updates to cross-references and self-review.
See CREDITS.md.
-->
```

- [ ] **Step 2: Insert Research phase section**

Find the `## Scope Check` section near the top of the SKILL.md. Insert a new `## Research phase` section AFTER `## Scope Check` and BEFORE `## File Structure`:

````markdown
## Research phase

Before drafting plan steps, gather outside context. **Default-on**: skip only with explicit justification.

### 1. Pick research kinds

For writing-plans, defaults are:
- **Web (pitfalls in chosen approach):** What's gone wrong for others doing this kind of plan? Recent post-mortems, GitHub issues, conference talks?
- **Codebase (similar features):** Has this codebase done something similar before? What patterns can be reused?
- **Authoritative verification:** If the plan involves external APIs/services/standards, hit the real source — current docs, live curl, current spec — to confirm the plan's assumptions.

Add user-context if a prior plan or session is relevant.

### 2. Dispatch

Subagent by default:
- `Explore` for codebase / similar-feature search
- `general-purpose` for web research and live API verification
- Run in parallel when independent

Inline for trivial plans (single-file edits, mechanical changes).

### 3. Record findings

Write 3–5 tight bullets into a new `## Research notes` section AT THE TOP of the plan doc, immediately after the plan header. Include load-bearing references and anything considered-but-ruled-out.

### 4. Skip protocol

Same as brainstorming. If skipping, write one line into the plan doc:

`Skipped research because <reason>. <Verifiable pointer if applicable>.`

Valid reasons: trivial scope, fresh prior research within 7 days, user explicit, repeat of identical task. Invalid reasons: "I think I know", "seems straightforward", "moving fast".
````

- [ ] **Step 3: Update Self-Review to check research-findings/skip-line presence**

Find the `## Self-Review` section. Add a fourth check after the "Type consistency" check:

```markdown
**4. Research phase check:** Does the plan contain either a `## Research notes` section with findings, or a `Skipped research because <reason>` declaration? If neither, the plan was drafted without the research step — return to the research phase.
```

- [ ] **Step 4: Verify section count**

```bash
grep -c "^## " superjawn/skills/writing-plans/SKILL.md
grep -c "^## " ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/writing-plans/SKILL.md
```

superjawn count should be +1 (we added `## Research phase`).

- [ ] **Step 5: Commit**

```bash
git add superjawn/skills/writing-plans/
git commit -m "feat(superjawn): port writing-plans with research phase

Adds default-on research phase between scope check and file structure.
Subagent dispatch with web/codebase/authoritative defaults. Findings
recorded at top of plan doc. Self-review check added."
```

---

## Task 12: Port `writing-plans` — rewrite cross-references

**Files:**
- Modify: `superjawn/skills/writing-plans/SKILL.md`

writing-plans references `superpowers:subagent-driven-development` and `superpowers:executing-plans`. executing-plans IS being ported in this batch — rewrite. subagent-driven-development is NOT (Batch 4) — keep at `superpowers:` for now.

- [ ] **Step 1: Inventory existing cross-refs**

```bash
grep -nE "superpowers:|subagent-driven-development|executing-plans" \
  superjawn/skills/writing-plans/SKILL.md
```

- [ ] **Step 2: Rewrite refs to ported skills**

- `superpowers:executing-plans` → `superjawn:executing-plans` (executing-plans is in this batch)
- `superpowers:subagent-driven-development` → leave as-is (Batch 4 — not yet ported)
- Bare `executing-plans` mentions → `superjawn:executing-plans` only when context makes the namespace clear

- [ ] **Step 3: Verify**

```bash
grep -n "executing-plans" superjawn/skills/writing-plans/SKILL.md
```

Every reference should now be `superjawn:executing-plans` (no bare or `superpowers:` form).

```bash
grep -n "subagent-driven-development" superjawn/skills/writing-plans/SKILL.md
```

References should still be `superpowers:subagent-driven-development` (kept until Batch 4 ships).

- [ ] **Step 4: Commit**

```bash
git add superjawn/skills/writing-plans/SKILL.md
git commit -m "refactor(superjawn): rewrite writing-plans cross-refs (executing-plans → superjawn)"
```

---

## Task 13: Smoke-test `superjawn:writing-plans`

**Files:** None (validation step)

- [ ] **Step 1: Fresh Claude session**

Restart `claude` so the new skill is registered.

- [ ] **Step 2: Invoke on a tiny real task**

Pick a small spec — e.g. the 2-line README change above. Invoke `superjawn:writing-plans` referencing that spec. (You can use any small spec doc as input.)

- [ ] **Step 3: Verify research phase fires**

The skill should reach the research phase before file-structure mapping. EITHER dispatch subagents (web/codebase) OR write a skip line into the plan doc.

- [ ] **Step 4: Verify findings location**

If research happened: findings are in `## Research notes` at the top of the plan doc.
If skipped: skip line is in the plan doc, not buried elsewhere.

- [ ] **Step 5: Document the smoke test**

Append to `CREDITS.md`:

```markdown
- 2026-05-XX: `superjawn:writing-plans` invoked on trivial spec; research phase fired correctly; findings recorded in plan doc.
```

- [ ] **Step 6: Commit**

```bash
git add superjawn/CREDITS.md
git commit -m "docs(superjawn): record writing-plans smoke test pass"
```

---

## Task 14: Port `executing-plans` — copy upstream file

**Files:**
- Create: `superjawn/skills/executing-plans/SKILL.md`

- [ ] **Step 1: Copy upstream executing-plans directory**

```bash
cp -r ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/executing-plans \
      ~/projects/claude-skills-journalism/superjawn/skills/executing-plans
```

- [ ] **Step 2: Verify file copied**

```bash
find superjawn/skills/executing-plans -type f | sort
```

Expected (1 file):

```
superjawn/skills/executing-plans/SKILL.md
```

- [ ] **Step 3: Verify content matches upstream**

```bash
diff superjawn/skills/executing-plans/SKILL.md \
     ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/executing-plans/SKILL.md
```

Expected: no output.

---

## Task 15: Port `executing-plans` — add MIT attribution + research phase

**Files:**
- Modify: `superjawn/skills/executing-plans/SKILL.md`

executing-plans research stage is "Before each step's implementation". Default kind is **authoritative re-verification** (drift check) — has the API/file/state changed since the plan was written?

- [ ] **Step 1: Add MIT attribution comment**

Edit `superjawn/skills/executing-plans/SKILL.md`. Add HTML comment after frontmatter, before `# Executing Plans` heading:

```html
<!--
Adapted from obra/superpowers executing-plans skill (v5.0.7), MIT-licensed,
copyright 2025 Jesse Vincent. Modifications copyright 2026 Joe Amditis.
Modifications add a per-step research phase (drift check before execution).
See CREDITS.md.
-->
```

- [ ] **Step 2: Insert per-step Research phase section**

Find a logical insertion point in the existing executing-plans flow — typically after a section describing how to begin a task and before actual implementation steps. Insert:

````markdown
## Research phase (per task)

Before implementing each task in the plan, run a quick drift check. **Default-on**: skip only with explicit justification per task.

### 1. What to verify

The plan was written at a point in time. Before each task, verify:
- **Authoritative state:** If the task touches an external API or file the plan references, confirm the API contract or file content hasn't changed. Live curl, file read, version check.
- **Codebase drift:** If the task assumes a function/module exists at a specific path, grep to confirm it still does.
- **Repo state:** Has anyone landed conflicting work on the branch since the plan was drafted?

### 2. Dispatch

Inline for single-file or single-API checks. `general-purpose` subagent only when the verification spans multiple sources.

### 3. Record findings

Append a short note to the execution journal (or PR description) for each task:

```
Task N drift check: <PASS / FAIL> — <one-line summary>
```

If FAIL, escalate before implementing — the plan may need revision.

### 4. Skip protocol

Skip per-task research is allowed when:
- Task is purely additive within a file the previous task just created (no external state to verify)
- Plan was drafted within the current session and nothing has changed
- Task is a pure mechanical commit/rebase step

If skipping, write one line in the journal: `Task N research skipped because <reason>.`
````

- [ ] **Step 3: Verify section count**

```bash
grep -c "^## " superjawn/skills/executing-plans/SKILL.md
grep -c "^## " ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/executing-plans/SKILL.md
```

superjawn count should be +1.

- [ ] **Step 4: Commit**

```bash
git add superjawn/skills/executing-plans/
git commit -m "feat(superjawn): port executing-plans with per-task drift-check research

Adds per-task research phase (authoritative re-verification of external
state) before implementation. Inline by default; subagent for multi-source
checks. Findings recorded in execution journal."
```

---

## Task 16: Port `executing-plans` — rewrite cross-references

**Files:**
- Modify: `superjawn/skills/executing-plans/SKILL.md`

- [ ] **Step 1: Inventory existing cross-refs**

```bash
grep -nE "superpowers:|writing-plans|subagent-driven-development|verification-before-completion" \
  superjawn/skills/executing-plans/SKILL.md
```

- [ ] **Step 2: Rewrite refs to ported skills**

- Refs to `writing-plans` → `superjawn:writing-plans` (Batch 1, ported)
- Refs to `subagent-driven-development` → leave as `superpowers:` (Batch 4, not yet ported)
- Refs to `verification-before-completion` → leave as `superpowers:` (Batch 2, not yet ported)

- [ ] **Step 3: Verify**

```bash
grep -nE "(superpowers:|superjawn:)(writing-plans|subagent|verification)" \
  superjawn/skills/executing-plans/SKILL.md
```

Every match should be on the right side of the dual-namespace rule above.

- [ ] **Step 4: Commit**

```bash
git add superjawn/skills/executing-plans/SKILL.md
git commit -m "refactor(superjawn): rewrite executing-plans cross-refs (writing-plans → superjawn)"
```

---

## Task 17: Smoke-test `superjawn:executing-plans`

**Files:** None (validation step)

- [ ] **Step 1: Fresh Claude session**

- [ ] **Step 2: Invoke on a tiny real plan**

Pick a single-task plan — e.g. "Add one line to README.md saying 'See CREDITS.md.'" Invoke `superjawn:executing-plans` against it.

- [ ] **Step 3: Verify per-task drift check fires**

Before implementing, the skill should verify:
- The README.md file exists at the expected path
- No conflicting changes on the branch

- [ ] **Step 4: Verify journal entry**

After the task is implemented (or skipped), confirm the journal has a `Task 1 drift check: PASS — <summary>` line or a skip declaration.

- [ ] **Step 5: Document the smoke test**

Append to `CREDITS.md`:

```markdown
- 2026-05-XX: `superjawn:executing-plans` invoked on trivial plan; per-task drift check fired correctly.
```

- [ ] **Step 6: Commit**

```bash
git add superjawn/CREDITS.md
git commit -m "docs(superjawn): record executing-plans smoke test pass"
```

---

## Task 18: End-of-batch verification

**Files:** None (verification step)

- [ ] **Step 1: All three skills register**

In a fresh `claude` session, verify the available-skills list shows all three:

- `superjawn:brainstorming`
- `superjawn:writing-plans`
- `superjawn:executing-plans`

- [ ] **Step 2: Cross-references all resolve**

For each ported skill, every `superjawn:<skill>` reference inside the SKILL.md must resolve to a real ported skill, AND every `superpowers:<skill>` reference must resolve to a real upstream skill.

```bash
# Find all superjawn: refs across batch 1
grep -rEh "superjawn:[a-z-]+" superjawn/skills/ | grep -oE "superjawn:[a-z-]+" | sort -u

# Find all superpowers: refs across batch 1
grep -rEh "superpowers:[a-z-]+" superjawn/skills/ | grep -oE "superpowers:[a-z-]+" | sort -u
```

Manually verify each `superjawn:` ref appears in the Batch 1 ported set, and each `superpowers:` ref exists in the upstream `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/` directory.

- [ ] **Step 3: Both plugins still function side-by-side**

In a fresh session, invoke `superpowers:brainstorming` (the upstream version) and verify it still works as before. Then invoke `superjawn:brainstorming` and verify it reaches the research phase. They should not interfere with each other.

- [ ] **Step 4: Bump plugin version**

Edit `superjawn/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` — bump the superjawn version from `0.1.0` to `0.1.0` (it stays — this is the v0.1.0 cut). If you've made enough changes that you want a v0.1.1, bump now.

(Decision deferred to engineer at this point: hold at 0.1.0 if Batch 1 is the v0.1.0 release, or bump if there's been iteration since last tag.)

- [ ] **Step 5: Push branch and open PR**

```bash
git push -u origin docs/superjawn-research-phases-spec
gh pr create --title "superjawn Batch 1: scaffold plugin + foundation skills with research phase" \
             --body "$(cat <<'EOF'
## Summary

Bootstraps the `superjawn` plugin and ports the foundation triad of superpowers skills (`brainstorming`, `writing-plans`, `executing-plans`) with a default-on research phase per the design spec.

Spec: `specs/2026-05-05-superjawn-research-phases-design.md`
Plan: `plans/2026-05-05-superjawn-batch-1.md`

## What's in this PR

- Plugin scaffold: `plugin.json`, `LICENSE`, `CREDITS.md`, `README.md`
- Marketplace registration: `superjawn` entry in `marketplace.json`
- Three skills ported with research phase additions:
  - `brainstorming`: research between clarifying questions and approach proposal
  - `writing-plans`: research before plan drafting
  - `executing-plans`: per-task drift check before implementation
- Cross-references in dual-namespace mode: ported skills use `superjawn:`, not-yet-ported skills keep `superpowers:`
- Smoke tests passed for all three skills

## Test plan

- [x] Plugin loads in fresh Claude session
- [x] All three skills appear in available-skills list under `superjawn:`
- [x] Cross-references resolve correctly (manually verified per skill)
- [x] Both plugins coexist without interference
- [x] Smoke test per skill confirmed research phase fires

## Out of scope

- Batches 2–5 each get their own implementation plan after this PR merges and proves the pattern.
- v1.0.0 (disable upstream `superpowers`) is gated on at least 2 weeks of real use after Batch 5 ships.
EOF
)"
```

Note: PR title and body intentionally have zero AI attribution per global rules.

---

## Self-review

### Spec coverage check

| Spec section | Plan task(s) covering it |
|---|---|
| §1 Plugin architecture (location, layout, cross-refs, coexistence, versioning) | Tasks 1–5 (scaffold, manifest, license, README, marketplace registration, install verification) |
| §2 Per-skill research taxonomy (3 of 14 skills covered in Batch 1) | Tasks 7, 11, 15 (research-phase insertion per skill, kinds and stage from §2 table) |
| §3 Common research-step shape | Tasks 7, 11, 15 (template substituted per skill: stage, kinds, subagent, artifact) |
| §4 Skip-justification protocol | Tasks 7, 11, 15 (skip rules baked into each skill's research-phase section) |
| §5 Rollout sequence (this is plan #1 of 5) | Plan covers Batch 1; Batches 2–5 explicitly deferred to subsequent plans (Task 18 PR body says so) |
| §6 Upstream drift management | `CREDITS.md` baseline tracking established in Task 2; quarterly check cadence is operational, not part of this plan |

### Placeholder scan

- "fill in upstream commit SHA at first port" in `CREDITS.md` — intentional placeholder, surfaced as a clear instruction. Engineer fills it during Task 2 by running `cd ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7 && git rev-parse HEAD 2>/dev/null` (or noting "tagged release v5.0.7" if the cache isn't a git checkout).
- "the actual date of the test" in Tasks 9/13/17 — intentional, instructs engineer to substitute current date.
- No "TBD", "TODO", "implement later", or "similar to Task N" patterns.

### Type consistency check

- "Skipped research because" phrase used identically across Tasks 7, 11, 15.
- "Research notes" section name used consistently (brainstorming and writing-plans both use this; executing-plans uses "execution journal" which is its skill-specific artifact per spec §2).
- Cross-ref rule consistent: ported-in-this-batch → `superjawn:`, not-yet-ported → `superpowers:`.
- "Drift check" phrasing used consistently for executing-plans.

No type/naming drift found.

### Engineer-readability check

Each task has explicit file paths, exact commands, expected outputs. The HTML attribution comment is repeated verbatim in Tasks 7/11/15 rather than referenced ("similar to Task N") so an engineer reading tasks out of order has the full text.

---

## Execution handoff

**Plan complete and saved to `plans/2026-05-05-superjawn-batch-1.md`.**

Two execution options for this plan (per the writing-plans skill):

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration. Best when iterating on the research-phase wording is likely.
2. **Inline Execution** — execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints. Faster when the wording is settled.

Which approach?
