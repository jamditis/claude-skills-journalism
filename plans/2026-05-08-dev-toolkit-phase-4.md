# Phase 4 dev-toolkit implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superjawn:subagent-driven-development (recommended) or superjawn:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bundle 10 development-themed bare skills into a new `dev-toolkit` Marketplace plugin with a full Phase 3-style currency sweep and codex/Copilot review-loop quality gating.

**Architecture:** Mirror `research-toolkit/` exactly. New plugin directory at top level; the 10 bare skill directories move under `dev-toolkit/skills/` via `git mv` to preserve rename history. Marketplace bumps to v1.5.0; CLAUDE.md and top-level README.md updated to reflect the new plugin. Currency sweep applied per-skill in alphabetical order, one commit per skill. Review loop: codex #1 → push → Copilot → codex #2+ until convergence.

**Tech Stack:** Markdown (skill files), JSON (marketplace + plugin manifest), Bash (git, gh CLI, codex exec), GitHub Actions CI.

**Source spec:** `specs/2026-05-08-dev-toolkit-phase-4-design.md` (commit `ef213b9` on master).

**Branch:** `package/dev-toolkit-phase4` (cut from current master HEAD).

**Scope:** Phase 4 only. Plan terminates at squash merge of the resulting PR.

---

## File structure

**Created in this plan:**

```
dev-toolkit/
├── .claude-plugin/
│   └── plugin.json                                  # Plugin manifest, v1.0.0
├── README.md                                        # Skill table + install notes
└── skills/
    ├── accessibility-compliance/SKILL.md            # git mv from top-level
    ├── electron-dev/SKILL.md                        # git mv from top-level
    ├── mobile-debugging/SKILL.md                    # git mv from top-level
    ├── one-way-door/SKILL.md                        # git mv from top-level
    ├── python-pipeline/SKILL.md                     # git mv from top-level
    ├── test-first-bugs/SKILL.md                     # git mv from top-level
    ├── vibe-coding/SKILL.md                         # git mv from top-level
    ├── web-scraping/SKILL.md                        # git mv from top-level
    ├── web-ui-best-practices/SKILL.md               # git mv from top-level
    └── zero-build-frontend/SKILL.md                 # git mv from top-level
```

**Modified in this plan:**

```
.claude-plugin/marketplace.json                      # bump to v1.5.0, add dev-toolkit entry
CLAUDE.md                                            # add Plugin: dev-toolkit section
README.md                                            # add row to plugins table
```

**Responsibility split:**
- `dev-toolkit/.claude-plugin/plugin.json` declares the plugin to Claude Code's loader (one-time, structural).
- `dev-toolkit/README.md` is the per-plugin landing doc.
- The 10 SKILL.md files are agent-facing content; each gets a per-skill currency sweep commit after the structural mv.
- Top-level `marketplace.json`, `CLAUDE.md`, `README.md` are repo-wide indexes that need refreshing whenever a new plugin appears.

---

## Task 1: Cut the feature branch

**Files:** none (git operation).

- [ ] **Step 1: Sync master**

```bash
cd /home/jamditis/projects/claude-skills-journalism
git checkout master
git pull --ff-only
```

Expected output: `Already up to date.` or fast-forward to `ef213b9` (the spec commit).

- [ ] **Step 2: Cut and switch to the feature branch**

```bash
git checkout -b package/dev-toolkit-phase4
git status
```

Expected output: `On branch package/dev-toolkit-phase4` with clean tree.

---

## Task 2: Create plugin manifest

**Files:**
- Create: `dev-toolkit/.claude-plugin/plugin.json`

- [ ] **Step 1: Create directory**

```bash
mkdir -p dev-toolkit/.claude-plugin dev-toolkit/skills
```

- [ ] **Step 2: Write the manifest**

Write `dev-toolkit/.claude-plugin/plugin.json`:

```json
{
  "name": "dev-toolkit",
  "version": "1.0.0",
  "description": "Ten development-focused skills for journalists, researchers, and small newsroom dev teams. Covers accessibility (WCAG 2.2), Electron app patterns, mobile/remote debugging, irreversible-decision discipline, Python data pipelines, test-first bug fixing, AI-assisted development workflows, ethical web scraping, no-build frontend patterns, and signs-of-taste guidance for web UI.",
  "author": {
    "name": "Joe Amditis",
    "url": "https://amditis.com"
  },
  "homepage": "https://github.com/jamditis/claude-skills-journalism",
  "repository": "https://github.com/jamditis/claude-skills-journalism"
}
```

The description is the value users will see in the Marketplace; it must accurately reflect the 10-skill scope as of 2026-05.

---

## Task 3: Create plugin README

**Files:**
- Create: `dev-toolkit/README.md`

- [ ] **Step 1: Write the README**

Write `dev-toolkit/README.md`:

```markdown
# dev-toolkit

Ten development-focused skills for journalists, researchers, and small newsroom dev teams.

## Skills in this plugin

| Skill | What it covers |
|---|---|
| accessibility-compliance | WCAG 2.2 baseline, alt text, focus management, motion preferences |
| electron-dev | Electron security model (contextIsolation, sandbox), IPC patterns, packaging |
| mobile-debugging | Eruda, vConsole, Chrome DevTools on Android, Safari Web Inspector for iOS |
| one-way-door | Block irreversible architectural decisions during planning |
| python-pipeline | Data pipeline patterns (pandas, polars, DuckDB, asyncio) |
| test-first-bugs | TDD workflow for bug fixes, failing test before fix |
| vibe-coding | AI-assisted development workflow (Claude Code, Cursor, Aider, Continue) |
| web-scraping | Ethical scraping patterns (Playwright, robots.txt, anti-bot, terms-of-service) |
| web-ui-best-practices | Container queries, `:has()`, view transitions, scroll-driven animations |
| zero-build-frontend | ESM import maps, htmx, Alpine.js, no-build deployment |

## Installation

```
/plugin marketplace add jamditis/claude-skills-journalism
/plugin install dev-toolkit@claude-skills-journalism
```

## See also

- [`journalism-core`](../journalism-core/README.md), 13 skills for reporting, verification, publishing
- [`research-toolkit`](../research-toolkit/README.md), 5 skills for research, archives, academic workflows
```

---

## Task 4: Move the 10 skills under dev-toolkit/skills/

**Files:**
- 10 directory renames via `git mv` (preserves history)

- [ ] **Step 1: Run all 10 git mv commands**

```bash
git mv accessibility-compliance dev-toolkit/skills/accessibility-compliance
git mv electron-dev              dev-toolkit/skills/electron-dev
git mv mobile-debugging          dev-toolkit/skills/mobile-debugging
git mv one-way-door              dev-toolkit/skills/one-way-door
git mv python-pipeline           dev-toolkit/skills/python-pipeline
git mv test-first-bugs           dev-toolkit/skills/test-first-bugs
git mv vibe-coding               dev-toolkit/skills/vibe-coding
git mv web-scraping              dev-toolkit/skills/web-scraping
git mv web-ui-best-practices     dev-toolkit/skills/web-ui-best-practices
git mv zero-build-frontend       dev-toolkit/skills/zero-build-frontend
```

- [ ] **Step 2: Verify the renames**

```bash
git status --short
```

Expected output: 10 lines starting with `R` (rename), each pointing from the old path to `dev-toolkit/skills/<name>/`. No `D`/`A` pairs (those would mean git didn't detect the rename, bad).

- [ ] **Step 3: Confirm rename similarity**

```bash
git diff --staged --stat -M50
```

Expected: each rename shows up as `dev-toolkit/skills/<name>/SKILL.md` (renamed) with `0 insertions(+), 0 deletions(-)` (since file content didn't change in this step).

---

## Task 5: Update marketplace.json

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Read current marketplace.json**

```bash
jq '.version, (.plugins | length)' .claude-plugin/marketplace.json
```

Expected: `"1.4.0"` and `6`.

- [ ] **Step 2: Bump version and add dev-toolkit entry**

Edit `.claude-plugin/marketplace.json`:
- Change `"version": "1.4.0"` to `"version": "1.5.0"`.
- Insert a new plugin object alphabetically between `autocontext` and `journalism-core`:

```json
{
  "name": "dev-toolkit",
  "source": "./dev-toolkit",
  "description": "Ten development-focused skills for journalists, researchers, and small newsroom dev teams. Covers accessibility (WCAG 2.2), Electron app patterns, mobile/remote debugging, irreversible-decision discipline, Python data pipelines, test-first bug fixing, AI-assisted development workflows, ethical web scraping, no-build frontend patterns, and signs-of-taste guidance for web UI.",
  "category": "Development",
  "version": "1.0.0",
  "author": {
    "name": "Joe Amditis",
    "url": "https://amditis.com"
  }
}
```

(Use the same description as `dev-toolkit/.claude-plugin/plugin.json`, keep them in sync.)

- [ ] **Step 3: Validate JSON**

```bash
jq '.plugins[] | .name' .claude-plugin/marketplace.json
```

Expected output (one per line, in this order): `"autocontext"`, `"dev-toolkit"`, `"journalism-core"`, `"pdf-design"`, `"pdf-playground"`, `"research-toolkit"`, `"superjawn"`.

---

## Task 6: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add the dev-toolkit section in the directory tree**

Locate the section starting with `# Plugin: research-toolkit (5 skills)`. Add a new section immediately after research-toolkit's tree:

```markdown
├── # Plugin: dev-toolkit (10 skills), registered in marketplace.json
├── dev-toolkit/
│   ├── .claude-plugin/plugin.json
│   ├── README.md
│   └── skills/
│       ├── accessibility-compliance/    # WCAG 2.2, alt text, focus management
│       ├── electron-dev/                # Electron security model, packaging
│       ├── mobile-debugging/            # Eruda, vConsole, remote debug
│       ├── one-way-door/                # Block irreversible decisions
│       ├── python-pipeline/             # Data pipelines (pandas, polars, DuckDB)
│       ├── test-first-bugs/             # TDD bug-fixing workflow
│       ├── vibe-coding/                 # AI-assisted development
│       ├── web-scraping/                # Ethical content extraction
│       ├── web-ui-best-practices/       # Container queries, :has(), view transitions
│       └── zero-build-frontend/         # ESM import maps, htmx, Alpine.js
```

- [ ] **Step 2: Remove the bare "Development (10)" section**

Locate and delete the block starting with `├── # Development (10)` and ending before `├── # Security (3)`. The 10 skills now live under `dev-toolkit/skills/`.

- [ ] **Step 3: Update the "Available plugins" line**

Find: `Available plugins: \`autocontext\`, \`journalism-core\`, \`pdf-design\`, \`pdf-playground\`, \`research-toolkit\`, \`superjawn\`. See \`.claude-plugin/marketplace.json\` for the full list.`

Replace with: `Available plugins: \`autocontext\`, \`dev-toolkit\`, \`journalism-core\`, \`pdf-design\`, \`pdf-playground\`, \`research-toolkit\`, \`superjawn\`. See \`.claude-plugin/marketplace.json\` for the full list.`

- [ ] **Step 4: Update bare-skill copy examples**

Replace any example referencing `web-scraping` or `python-pipeline` as bare skills with examples that point to nested paths (mirroring research-toolkit's section pattern):

```bash
cp -r dev-toolkit/skills/web-scraping ~/.claude/skills/
cp -r dev-toolkit/skills/python-pipeline ~/.claude/skills/
```

---

## Task 7: Update top-level README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add dev-toolkit row to plugins table**

Locate the plugins table; add a row alphabetically between autocontext and journalism-core:

```markdown
| dev-toolkit | 10 development skills | `/plugin install dev-toolkit@claude-skills-journalism` |
```

- [ ] **Step 2: Replace bare "Development skills" section**

Replace the existing "Bare development skills" section (or whatever Phase 3 renamed it to) with:

```markdown
### Development skills (in dev-toolkit plugin)

10 skills for journalists, researchers, and small newsroom dev teams: accessibility-compliance, electron-dev, mobile-debugging, one-way-door, python-pipeline, test-first-bugs, vibe-coding, web-scraping, web-ui-best-practices, zero-build-frontend. Install via `/plugin install dev-toolkit@claude-skills-journalism` or copy individual skills from `dev-toolkit/skills/`:

\`\`\`bash
cp -r dev-toolkit/skills/web-scraping ~/.claude/skills/
\`\`\`
```

- [ ] **Step 3: Remove any other "Development" bare-skill list elsewhere in the file**

Grep for `python-pipeline` and `web-scraping` and ensure no remaining references treat them as top-level bare skills.

```bash
grep -n -E "python-pipeline|web-scraping|electron-dev|mobile-debugging|test-first-bugs|vibe-coding|one-way-door|accessibility-compliance|web-ui-best-practices|zero-build-frontend" README.md
```

Verify each hit either points to `dev-toolkit/skills/<name>/` or is in the plugins table.

---

## Task 8: Structural commit

**Files:** all of the above.

- [ ] **Step 1: Stage and commit**

```bash
git add .claude-plugin/marketplace.json CLAUDE.md README.md \
        dev-toolkit/.claude-plugin/plugin.json dev-toolkit/README.md \
        dev-toolkit/skills/
git status --short
```

Expected: 13 lines (10 renames `R` + 3 modifications `M` + 2 new files `A`).

```bash
git commit -m "Phase 4: scaffold dev-toolkit plugin and bundle 10 skills"
```

- [ ] **Step 2: Verify rename detection on the commit**

```bash
git show HEAD --stat -M50 | head -30
```

Expected: each of the 10 SKILL.md moves shows as `=>` rename with `0 insertions(+), 0 deletions(-)` or close to it.

---

## Tasks 9-18: Per-skill currency sweep (alphabetical)

Each task follows the same shape: audit, apply edits, commit. The audit is informed by the spec's "high-likelihood drift" table for each skill, plus a focused web search for current state of relevant tools.

**Task template (reuse for each skill):**

- [ ] **Step 1: Read the skill content**

```bash
SKILL=<skill-name>
wc -l dev-toolkit/skills/$SKILL/SKILL.md
```

Read the file in full. Note any references to versions, URLs, tool names, dates, or workflows that might have drifted.

- [ ] **Step 2: Run focused currency check**

For each candidate drift point, web-search for current state. Use `WebSearch` for 2026 facts. Skip obviously stable content (general principles, methodology).

The spec's drift table is the starting point but not a complete list, also flag anything that looks dated.

- [ ] **Step 3: Apply edits**

Use the `Edit` tool. Keep changes minimal and surgical:
- Update version numbers, URLs, tool lists.
- Remove retired tools / services with date stamps.
- Add 2026-specific caveats where the landscape changed.
- Do NOT rewrite working content for style.

- [ ] **Step 4: Commit with descriptive message**

```bash
git add dev-toolkit/skills/$SKILL/SKILL.md
git commit -m "Currency sweep: $SKILL"
```

The commit body should list the substantive currency changes (one bullet per fix).

---

### Task 9: accessibility-compliance currency sweep

**Files:** `dev-toolkit/skills/accessibility-compliance/SKILL.md`.

Apply the per-skill template above. Drift focus per spec: WCAG 2.2 baseline (now AA-required for federal contractors per 2025 DOJ rule), `prefers-reduced-motion`, `:focus-visible`, ARIA Authoring Practices Guide updates, alt-text patterns for AI-generated images.

Commit message prefix: `Currency sweep: accessibility-compliance`.

### Task 10: electron-dev currency sweep

**Files:** `dev-toolkit/skills/electron-dev/SKILL.md`.

Drift focus: Electron 30+ default `contextIsolation: true` and `sandbox: true`, `BrowserView` deprecation in favor of `WebContentsView`, ASAR integrity checks, recent CVE classes (preload script confusion, IPC over file://), notarization on macOS.

Commit prefix: `Currency sweep: electron-dev`.

### Task 11: mobile-debugging currency sweep

**Files:** `dev-toolkit/skills/mobile-debugging/SKILL.md`.

Drift focus: Eruda 3.x (current major), vConsole status, Chrome DevTools Protocol on Android (`chrome://inspect`), iOS Web Inspector via Safari (still requires macOS), USB debugging permissions evolution on Android 13+, weinre status (deprecated).

Commit prefix: `Currency sweep: mobile-debugging`.

### Task 12: one-way-door currency sweep

**Files:** `dev-toolkit/skills/one-way-door/SKILL.md`.

Drift focus: relatively stable methodology. Light-touch sweep, verify the heuristics still hold and any cited examples are reasonable. May produce zero changes (acceptable; commit only if real edits).

Commit prefix: `Currency sweep: one-way-door` (skip commit if no edits warranted; note in execution log).

### Task 13: python-pipeline currency sweep

**Files:** `dev-toolkit/skills/python-pipeline/SKILL.md`.

Drift focus: Python 3.13+ features (free-threaded build status, JIT preview), `asyncio.TaskGroup`, pandas vs polars maturity (polars 1.0+ stable), DuckDB Python integration, modern packaging (`uv` adoption, `pyproject.toml` standards), `datetime.UTC` (3.11+) vs `timezone.utc`.

Commit prefix: `Currency sweep: python-pipeline`.

### Task 14: test-first-bugs currency sweep

**Files:** `dev-toolkit/skills/test-first-bugs/SKILL.md`.

Drift focus: pytest 8.x, `pytest-watcher` (replacement for unmaintained `pytest-watch`), `pytest.fixture` patterns. Mostly stable methodology, sweep should focus on tooling references not principles.

Commit prefix: `Currency sweep: test-first-bugs`.

### Task 15: vibe-coding currency sweep

**Files:** `dev-toolkit/skills/vibe-coding/SKILL.md`.

Drift focus (high-drift skill): current AI coding tool landscape, Claude Code, Cursor, GitHub Copilot, Aider, Continue, Codeium, Gemini Code Assist. Verify pricing/capability claims with explicit "as of 2026-05" date stamps. Note any tools that have shut down or pivoted.

Commit prefix: `Currency sweep: vibe-coding`.

### Task 16: web-scraping currency sweep

**Files:** `dev-toolkit/skills/web-scraping/SKILL.md`.

Drift focus: Playwright 1.50+ vs Puppeteer, Cloudflare bot defense (Turnstile, IUAM), undetected-chromedriver maintenance status, `httpx` vs `requests`, rate-limit ethics, robots.txt enforcement, terms-of-service caveats post-Reddit/Twitter API changes.

Commit prefix: `Currency sweep: web-scraping`.

### Task 17: web-ui-best-practices currency sweep

**Files:** `dev-toolkit/skills/web-ui-best-practices/SKILL.md`.

Drift focus: container queries (Baseline 2023, now stable), `:has()` selector (Baseline 2024), View Transitions API (cross-document support landing 2025-2026), scroll-driven animations (Chromium-only, Safari/Firefox status), `subgrid`, `text-wrap: balance`, `prefers-reduced-motion`.

Commit prefix: `Currency sweep: web-ui-best-practices`.

### Task 18: zero-build-frontend currency sweep

**Files:** `dev-toolkit/skills/zero-build-frontend/SKILL.md`.

Drift focus: ESM import maps (Baseline 2023), htmx 2.0 (released 2024), Alpine.js current, Petite Vue, native CSS nesting, `@import` with media queries, deno_std deprecation in favor of JSR, esm.sh and unpkg current state.

Commit prefix: `Currency sweep: zero-build-frontend`.

---

## Task 19: Codex review #1

**Files:** none (review against branch state).

- [ ] **Step 1: Verify codex auth**

```bash
jq -r '"auth_mode=" + .auth_mode + " api_key=" + (.OPENAI_API_KEY|tostring|.[0:5])' ~/.codex/auth.json
echo "OPENAI_API_KEY=${OPENAI_API_KEY:-unset}"
```

Expected: `auth_mode=chatgpt api_key=null` and `OPENAI_API_KEY=unset`. If either is wrong, fix per `feedback_codex_must_use_oauth_not_api_key` memory before continuing.

- [ ] **Step 2: Write review prompt**

Write `/tmp/codex-review-1-dev-toolkit.txt` using this template (fill in the `<...>` placeholders):

```text
Review the work on branch package/dev-toolkit-phase4 (HEAD: <branch-head-sha>) against master.

This branch ships a new `dev-toolkit` plugin bundling 10 skills + a 2026 currency sweep
across all 10. There are 11 commits:

- <structural-sha>, Structural: scaffold dev-toolkit/.claude-plugin/plugin.json + README.md,
  git mv 10 skills, update marketplace.json (v1.5.0) and CLAUDE.md / README.md.
- <accessibility-sha>, accessibility-compliance currency sweep
- <electron-sha>, electron-dev currency sweep
... (repeat for each skill)

Repo context:
- Skills are markdown files containing instructional Python / JS / shell snippets meant
  to be copied into developer notebooks. Code samples are NOT runtime-tested; the value
  bar is "common-case correctness, no copy/paste hazards, factual currency."
- Date is 2026-05-08.

Your task: find HIGH-confidence bugs, regressions, or correctness issues introduced by
THIS BRANCH (since master). Focus on:

1. CONSISTENCY, same patterns appearing across multiple skills should be consistent.
2. CODE THAT WON'T RUN, missing imports, undefined variables, syntax mismatches.
3. FACTUAL CLAIMS, anything asserted as fact that could be wrong (version numbers,
   API endpoints, retired services, library status).
4. URL CORRECTNESS, every URL added should be reachable and correctly formatted.
5. INSTRUCTIONS THAT WOULD BREAK COPY/PASTE, broken bash, malformed Python.
6. LOW-VALUE FINDINGS, skip "could be improved" / stylistic preferences. Focus on
   what's WRONG.

Output format, terse, no preamble:
- [HIGH/MED/LOW] <file:line>, <issue>, <suggested fix>
- One line per finding. NO summary. NO "overall good" wrap-up.

If no issues: NO ISSUES FOUND.
```

- [ ] **Step 3: Run codex**

```bash
timeout --foreground 600 codex exec \
  -C /home/jamditis/projects/claude-skills-journalism \
  -s read-only --skip-git-repo-check \
  "$(cat /tmp/codex-review-1-dev-toolkit.txt)" </dev/null > /tmp/codex-1-output.txt 2>&1
echo "exit: $?"
tail -100 /tmp/codex-1-output.txt
```

Expected: codex returns a list of findings (or `NO ISSUES FOUND`).

- [ ] **Step 4: Address findings**

For each HIGH or MED finding, apply the suggested fix via `Edit`. Group related fixes into one commit per skill (or per logical fix cluster). Commit message: `Address codex review #1 findings on the currency sweep`.

---

## Task 20: Push branch and open PR

**Files:** none (git + gh operations).

- [ ] **Step 1: Push branch**

```bash
git push -u origin package/dev-toolkit-phase4
```

Expected: branch created on origin.

- [ ] **Step 2: Open PR**

```bash
gh pr create --title "Phase 4: dev-toolkit plugin (10 skills) + currency sweep" \
  --body "$(cat <<'BODY'
## Summary

Phase 4 of the bundling effort: 10 development-themed bare skills become the new \`dev-toolkit\` plugin (v1.0.0), with a Phase 3-style currency sweep applied across all 10.

Mirrors the research-toolkit structure introduced in PR #62.

**The 10 skills:**
- accessibility-compliance, WCAG 2.2 baseline, alt text, focus management, motion preferences
- electron-dev, Electron 30+ security model, IPC, packaging
- mobile-debugging, Eruda 3.x, Chrome DevTools Protocol, Safari Web Inspector
- one-way-door, block irreversible architectural decisions
- python-pipeline, pandas, polars, DuckDB, asyncio TaskGroup, Python 3.13+
- test-first-bugs, TDD bug-fixing workflow, pytest 8.x
- vibe-coding, AI-assisted development (Claude Code, Cursor, Aider, Continue), 2026-05 snapshot
- web-scraping, Playwright 1.50+, Cloudflare bot defense, scraping ethics
- web-ui-best-practices, container queries, :has(), view transitions, scroll-driven animations
- zero-build-frontend, ESM import maps, htmx 2.0, Alpine.js

## Quality gates

- Local codex review #1 ran before push; findings addressed in fix commit(s).
- CI: \`check-readme\`, \`lint-skills\` (existing).
- Awaiting Copilot PR review.
- Codex review #2+ will run on Copilot-fix commits until convergence.

## Test plan

- [ ] CI green (\`check-readme\`, \`lint-skills\`).
- [ ] Marketplace.json validates as JSON and lists 7 plugins including dev-toolkit alphabetically between autocontext and journalism-core.
- [ ] All 10 skill SKILL.md files moved with rename history preserved (similarity ≥50%).
- [ ] CLAUDE.md and top-level README.md no longer reference the 10 skills as bare top-level dirs.
- [ ] Codex review converges (final round returns NO ISSUES FOUND).
- [ ] Squash merge after Joe's explicit "merge".
BODY
)"
```

Expected output: PR URL.

- [ ] **Step 3: Confirm CI status**

```bash
gh pr checks <pr-number>
```

Expected: `check-readme` pass, `lint-skills` pass.

---

## Task 21: Address Copilot review

**Files:** as flagged by Copilot's review.

- [ ] **Step 1: Wait for Copilot review (one-shot)**

Use Monitor to poll for the review without burning cache. The bot fires once per PR open; pushing fixes does NOT re-trigger.

```bash
prev=""
while true; do
  cur=$(gh api repos/jamditis/claude-skills-journalism/pulls/<pr-number>/reviews \
    --jq '[.[] | select(.user.login == "copilot-pull-request-reviewer[bot]")] | length' 2>/dev/null || echo "0")
  if [ "$cur" != "0" ] && [ "$cur" != "$prev" ]; then
    echo "copilot review arrived"
    break
  fi
  sleep 60
done
```

- [ ] **Step 2: Read review body**

```bash
gh api repos/jamditis/claude-skills-journalism/pulls/<pr-number>/reviews \
  --jq '.[] | select(.user.login == "copilot-pull-request-reviewer[bot]") | {state, body}'
```

- [ ] **Step 3: Apply fixes**

For each finding (including suppressed-low-confidence ones, they're often real bugs per Phase 3 experience), apply the suggested fix via `Edit`. Group related fixes into one commit. Commit message: `address Copilot review findings`.

- [ ] **Step 4: Push the fix commit**

```bash
git push
```

CI will re-run; Copilot will NOT re-review (one-shot bot).

---

## Task 22: Codex review #2+ until convergence

**Files:** as needed per round.

- [ ] **Step 1: Write a prompt focused on the latest fix commit**

Write `/tmp/codex-review-N-dev-toolkit.txt` using this template (fill in `<...>` and replace `N` with the round number):

```text
Review fix commit <fix-sha> on branch package/dev-toolkit-phase4 (PR #<pr-number>).

This commit addresses N findings from <previous review> (Copilot or codex #N-1).

Files changed: <list of files>

The N fixes:
1. <file:line>: <fix description>
2. ... (one per fix)

Your task: find HIGH-confidence bugs, regressions, or correctness issues introduced by
THIS COMMIT. Specifically:

A. Did the fix accidentally introduce a regression?
B. Are there sibling bugs of the same class elsewhere in the changed files that the
   fix didn't reach?
C. Any new factual / URL / import / type errors?
D. Any non-encoding bugs introduced (typos, broken markdown, removed lines that
   shouldn't have been removed)?

Output format, terse:
- [HIGH/MED/LOW] <file:line>, <issue>, <suggested fix>
- One line per finding. NO summary.

If no issues: NO ISSUES FOUND.
```

- [ ] **Step 2: Run codex**

```bash
timeout --foreground 600 codex exec \
  -C /home/jamditis/projects/claude-skills-journalism \
  -s read-only --skip-git-repo-check \
  "$(cat /tmp/codex-review-N-dev-toolkit.txt)" </dev/null > /tmp/codex-N-output.txt 2>&1
tail -100 /tmp/codex-N-output.txt
```

- [ ] **Step 3: Address findings or stop**

If findings: apply fixes, commit, push, run another round (Step 1 of Task 22 again).

If `NO ISSUES FOUND`: stop the recursion. Convergence reached. The spec caps recursion at 5 rounds; if a 6th round still produces real bugs, pause and re-scope rather than push through.

---

## Task 23: Final ready-for-merge state

**Files:** none.

- [ ] **Step 1: Confirm PR state**

```bash
gh pr view <pr-number> --json state,mergeable,mergeStateStatus,headRefOid
gh pr checks <pr-number>
```

Expected: `state=OPEN`, `mergeable=MERGEABLE`, `mergeStateStatus=CLEAN`, all checks pass.

- [ ] **Step 2: Tell Joe ready for merge**

Send a status message:
- HEAD commit SHA
- mergeStateStatus / mergeable / state
- CI status
- Number of codex review rounds run, last round result
- Number of Copilot findings addressed

- [ ] **Step 3: WAIT for Joe's explicit "merge"**

Do NOT run `gh pr merge` until Joe sends the literal word "merge". This is a hard rule from `~/.claude/CLAUDE.md` PR workflow.

- [ ] **Step 4: Squash merge after authorization**

```bash
gh pr merge <pr-number> --repo jamditis/claude-skills-journalism --squash --delete-branch
gh pr view <pr-number> --json state,mergedAt,mergeCommit \
  --jq '"state=\(.state) merged_at=\(.mergedAt) merge_sha=\(.mergeCommit.oid)"'
```

Expected: `state=MERGED`.

- [ ] **Step 5: Sync local master**

```bash
git checkout master
git pull --ff-only
git log --oneline -3
```

Expected: master fast-forwards to the new merge commit.

---

## Risks and mitigations (from spec, restated)

- **vibe-coding currency drift.** Tag claims with explicit "as of 2026-05" so the next phase knows when to re-sweep.
- **electron-dev relevance.** Keep currency-only; do not over-invest.
- **10 skills × codex/Copilot recursion.** Cap at 5 codex rounds; pause and re-scope if a 6th round still surfaces bugs.
- **bare-skill consumers.** No symlink shim; rely on updated install instructions in CLAUDE.md and README.md.
