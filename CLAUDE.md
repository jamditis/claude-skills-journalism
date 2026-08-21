# Agent skills collection

## Bug-fixing workflow

When a bug is reported, don't immediately attempt to fix it. Instead:

1. **Write a failing test first** that reproduces the bug
2. **Launch subagents** to work on fixing the bug
3. **Verify the fix** by running the test, a passing test proves the bug is fixed

---

Collection of Claude Code and Codex skills for journalism, media, academia, and technical workflows.

## Project overview

This repo contains modular instruction sets that extend supported coding agents for specialized tasks. Each skill directory contains domain knowledge, workflows, templates, and best practices.

## Directory structure

Packages use `.claude-plugin/plugin.json`. Codex supports standards-based skill
installs and a verified legacy-compatible journalism-core package route. Each
stable skill has Codex UI metadata. The repository does not ship native Codex
plugin manifests.

```
claude-skills-journalism/
├── CLAUDE.md                    # This file
├── README.md                    # User documentation
├── LICENSE
│
├── hooks/                       # Automated workflow checks (17 hooks)
│   ├── ap-style-check.md        # Writing: AP Style violations
│   ├── ai-slop-detector.md      # Writing: AI patterns
│   ├── accessibility-check.md   # Writing: Alt text, headings
│   ├── copywriting-preflight.md # Writing: Intent interview before drafting
│   ├── source-attribution-check.md  # Verification: Unattributed claims
│   ├── verification-reminder.md # Verification: Fact-check prompt
│   ├── data-methodology-check.md    # Verification: Methodology docs
│   ├── source-diversity-check.md    # Editorial: Source diversity
│   ├── legal-review-flag.md     # Editorial: Defamation risk
│   ├── pre-publish-checklist.md # Editorial: Pre-publish reminder
│   ├── deadline-tracker.md      # Editorial: Deadline surfacing
│   ├── archive-reminder.md      # Preservation: Archive URLs
│   ├── one-way-door-check.md    # Development: Block irreversible decisions
│   ├── bug-report-detector.md   # Development: Detect bug reports
│   ├── enforce-test-first.md    # Development: Enforce test-first workflow
│   ├── pre-commit-review.md     # Development: Review staged diff before commit
│   └── no-ai-attribution.md     # Development: Block AI attribution in commits, PRs, and comments
│
├── # Plugin: journalism-core (15 skills, v1.4.1), registered in marketplace.json
├── journalism-core/
│   ├── .claude-plugin/plugin.json
│   ├── README.md
│   └── skills/
│       ├── ai-writing-detox/           # Eliminate AI writing patterns
│       ├── crisis-communications/      # Breaking news, rapid verification
│       ├── data-journalism/            # Data analysis, federal-data currency, AI-assisted-analysis cautions
│       ├── editorial-workflow/         # Assignment tracking, calendars
│       ├── fact-check-workflow/        # Claim verification
│       ├── foia-requests/              # Public records requests
│       ├── interview-prep/             # Interview preparation
│       ├── interview-transcription/    # Recording, transcription, quotes
│       ├── newsletter-publishing/      # Email newsletters, subscribers
│       ├── newsroom-style/             # AP Style enforcement
│       ├── photo-metadata/             # Embed caption, credit, alt text, license in IPTC/EXIF/XMP
│       ├── brazil-records-requests/     # Brazilian LAI requests and appeals
│       ├── social-media-intelligence/  # OSINT, account analysis, platform-API currency
│       ├── source-verification/        # SIFT method, verification, deepfakes/C2PA
│       └── story-pitch/                # Pitch templates
│
├── # Plugin: research-toolkit (6 skills, v1.1.2), registered in marketplace.json
├── research-toolkit/
│   ├── .claude-plugin/plugin.json
│   ├── README.md
│   └── skills/
│       ├── academic-writing/           # Research and scholarly communication
│       ├── content-access/             # Unpaywall, library databases, paywall bypass
│       ├── digital-archive/            # AI-enriched archives, entity extraction
│       ├── free-apis-catalog/          # Curated free-API catalog with sunset currency notes
│       ├── page-monitoring/            # Change detection, availability tracking
│       └── web-archiving/              # Wayback, Archive.today, evidence preservation
│
├── # Plugin: dev-toolkit (13 skills), registered in marketplace.json
├── dev-toolkit/
│   ├── .claude-plugin/plugin.json
│   ├── README.md
│   └── skills/
│       ├── accessibility-compliance/   # WCAG 2.2, alt text, focus management
│       ├── claude-md-updater/          # Propose scoped CLAUDE.md updates
│       ├── context-engineering-fundamentals/ # Preserve instructions, evidence, and state
│       ├── director/                   # Explicit top-tier direction and delegation
│       ├── electron-dev/               # Electron security model, packaging
│       ├── mobile-debugging/           # Eruda, vConsole, remote debug
│       ├── one-way-door/               # Block irreversible decisions
│       ├── python-pipeline/            # Data pipelines (pandas, polars, DuckDB)
│       ├── test-first-bugs/            # TDD bug-fixing workflow
│       ├── vibe-coding/                # AI-assisted development
│       ├── web-scraping/               # Ethical content extraction
│       ├── web-ui-best-practices/      # Container queries, :has(), view transitions
│       └── zero-build-frontend/        # ESM import maps, htmx, Alpine.js
│
├── # Plugin: okf-wiki (1 skill), registered in marketplace.json
├── okf-wiki/                    # Scaffold an Open Knowledge Format knowledge base
│   ├── .claude-plugin/plugin.json
│   ├── SKILL.md
│   ├── spec/SPEC.md             # generic OKF spec v1
│   ├── scripts/                 # scaffold.py, validate.py, gh-wiki-bootstrap.py
│   ├── templates/              # .claude/ hooks copied into each scaffolded project
│   ├── example/                # a scaffolded OKF wiki of this repo (dogfood + live example)
│   └── tests/                   # pytest: scaffold output, hooks, validator rejections
│
├── # Plugin: pdf-design (1 skill), registered in marketplace.json
├── pdf-design/                  # PDF reports, proposals, brand system
│   └── templates/               # HTML templates (Democracy Day, etc.)
│
├── # Plugin: video-toolkit (4 skills, v1.0.5), registered in marketplace.json
├── video-toolkit/
│   ├── .claude-plugin/plugin.json
│   ├── README.md
│   └── skills/
│       ├── video-dashboard/     # Interactive transcript and frame analysis
│       ├── video-download/      # Public social-video collection
│       ├── video-frames/        # Frame extraction and vision analysis
│       └── video-transcribe/    # Reproducible Whisper transcription
│
├── # Plugin: visual-explainer (1 skill), registered in marketplace.json
├── visual-explainer/            # HTML diagrams, data tables, architecture views
│   ├── references/              # CSS patterns, library guides, nav patterns
│   ├── templates/               # Architecture, flowchart, data table templates
│   └── commands/                # Slash command templates
│
├── # Plugin: project-templates-toolkit (3 skills), registered in marketplace.json
├── project-templates-toolkit/
│   ├── .claude-plugin/plugin.json
│   ├── README.md
│   └── skills/
│       ├── project-memory/             # CLAUDE.md generation, 6 project type templates
│       ├── project-retrospective/      # LESSONS.md generation, 4 project type templates
│       └── template-selector/          # Decision tree for picking the right template
│
├── # Plugin: security-toolkit (4 skills, /security-toolkit:hotpatch command), registered in marketplace.json
├── security-toolkit/
│   ├── .claude-plugin/plugin.json
│   ├── README.md
│   ├── commands/hotpatch.md            # Slash command: sandboxed pre-install scan + cooldown bypass
│   ├── scripts/hotpatch.example.sh     # Reference Linux/bwrap implementation
│   ├── test-fixtures/                  # Synthetic malicious tarballs for self-test
│   └── skills/
│       ├── api-hardening/              # Rate limiting, CORS, request throttling, defense-in-depth
│       ├── secure-auth/                # Password hashing, sessions, JWT, OAuth, passkeys
│       ├── security-checklist/         # Pre-deployment OWASP audit
│       └── supply-chain-hardening/     # npm/bun install-time cooldown + sandboxed bypass scan
│
├── # Plugin: autocontext (no skills, hooks/commands/agents), registered in marketplace.json
├── autocontext/                 # Cross-session knowledge persistence with skill evolution
│   ├── .claude-plugin/plugin.json
│   ├── agents/                  # Lesson-review and evolution agents
│   ├── commands/                # /autocontext:setup, :init, :review, :status, :evolve
│   ├── hooks/                   # Capture, validate, and surface lessons across sessions
│   ├── scripts/skill-evolution/ # Fold accumulated lessons back into skill files
│   ├── templates/              # Lesson and archive templates
│   └── tests/
│
├── # Plugin: pdf-playground (8 commands, v1.3.4), registered in marketplace.json
├── pdf-playground/              # Interactive proposal/report/slide builder with live control panel
│   ├── .claude-plugin/plugin.json
│   ├── brands/                  # Brand presets
│   ├── commands/                # /proposal, /report, /onepager, /newsletter, /slides, /event, /preview, /update
│   ├── controls/template-maps/  # Live design-editing control wiring
│   ├── hooks/
│   ├── templates/               # Document templates
│   └── skills/                  # document-design/ + playground.md (user-invocable entry skill)
│
└── # Plugin: superjawn (14 skills, v1.0.2), registered in marketplace.json
    ├── # Research-augmented fork of obra/superpowers; standalone, no upstream dependency
    ├── .claude-plugin/plugin.json
    ├── README.md
    └── skills/
        ├── brainstorming/                 # Research phase: ideation before creative work
        ├── dispatching-parallel-agents/   # Independent tasks across 2+ agents
        ├── executing-plans/               # Run a written implementation plan
        ├── finishing-a-development-branch/ # Decide how to land completed work
        ├── receiving-code-review/         # Handle review feedback
        ├── requesting-code-review/        # Verify completed work before merging
        ├── subagent-driven-development/   # Parallel task execution in one session
        ├── systematic-debugging/          # Research phase: triage before proposing fixes
        ├── test-driven-development/        # TDD before implementation code
        ├── using-git-worktrees/           # Isolate feature work
        ├── using-superjawn/               # How to find and use skills
        ├── verification-before-completion/ # Confirm work is complete before committing
        ├── writing-plans/                 # Multi-step planning before touching code
        └── writing-skills/                # Research phase: creating or editing skills
```

## Skill format

Each skill follows the Agent Skills Standard:

```yaml
---
name: skill-name
description: When this skill activates and what it does
---

# Skill content

Instructions, templates, and workflows.
```

## Hooks

Hooks run automatically at specific workflow events. Most are **non-blocking warnings**, but `one-way-door-check` (shell hook, exits 2), `enforce-test-first` (prompt-based), and `no-ai-attribution` (PreToolUse deny) block intentionally. See each hook's "Hook behavior" section for details.

### Writing quality
| Hook | Event | Purpose |
|------|-------|---------|
| ap-style-check | PostToolUse(Write,Edit) | Flag AP Style violations |
| ai-slop-detector | PostToolUse(Write,Edit) | Warn about AI patterns |
| accessibility-check | PostToolUse(Write,Edit) | Check alt text, headings, links |
| copywriting-preflight | UserPromptSubmit | Interview for intent before drafting |

### Verification
| Hook | Event | Purpose |
|------|-------|---------|
| source-attribution-check | PostToolUse(Write,Edit) | Flag unattributed quotes/claims |
| verification-reminder | PostToolUse(Write,Edit) | Prompt fact verification |
| data-methodology-check | PostToolUse(Write,Edit) | Ensure methodology documented |

### Editorial workflow
| Hook | Event | Purpose |
|------|-------|---------|
| source-diversity-check | PostToolUse(Write,Edit) | Note sourcing diversity |
| legal-review-flag | PostToolUse(Write,Edit) | Flag defamation risk |
| pre-publish-checklist | Stop | Pre-publication reminder |
| deadline-tracker | SessionStart | Surface upcoming deadlines |

### Preservation
| Hook | Event | Purpose |
|------|-------|---------|
| archive-reminder | PostToolUse(Write,Edit) | Remind to archive URLs |

### Development
| Hook | Event | Purpose |
|------|-------|---------|
| one-way-door-check | PreToolUse(Write) | Block irreversible architectural decisions |
| bug-report-detector | UserPromptSubmit | Detect bug reports |
| enforce-test-first | PreToolUse(Edit,Write) | Block source edits until test written |
| pre-commit-review | PreToolUse(Bash) | Surface staged diff for review; flag guardrail deletions |
| no-ai-attribution | PreToolUse(Bash) | Block AI authorship credit in commits, PR bodies, and comments |

## Installation

This repo distributes shared skills as Claude and Codex packages and as standards-based skill directories.

### Recommended: install via Marketplace plugin

```
/plugin marketplace add jamditis/claude-skills-journalism
/plugin install journalism-core@claude-skills-journalism
```

Available plugins: `autocontext`, `dev-toolkit`, `journalism-core`, `okf-wiki`, `pdf-design`, `pdf-playground`, `project-templates-toolkit`, `research-toolkit`, `security-toolkit`, `superjawn`, `video-toolkit`, `visual-explainer`. See `.claude-plugin/marketplace.json` for the full list.

### Alternate: copy a single skill into `~/.claude/skills/`

Most skills live inside a package's `skills/` directory. The `okf-wiki`, `pdf-design`, and `visual-explainer` packages keep `SKILL.md` at the package root. Clone the repo and copy the directory that directly contains the required `SKILL.md`. Claude Code discovers skills at `~/.claude/skills/<skill-name>/SKILL.md`, one level deep:

```bash
git clone https://github.com/jamditis/claude-skills-journalism.git ~/projects/claude-skills-journalism
cd ~/projects/claude-skills-journalism
mkdir -p ~/.claude/skills

cp -r journalism-core/skills/source-verification ~/.claude/skills/
cp -r research-toolkit/skills/free-apis-catalog ~/.claude/skills/
cp -r research-toolkit/skills/web-archiving ~/.claude/skills/
cp -r dev-toolkit/skills/web-scraping ~/.claude/skills/
cp -r security-toolkit/skills/secure-auth ~/.claude/skills/
cp -r project-templates-toolkit/skills/project-memory ~/.claude/skills/
cp -r okf-wiki ~/.claude/skills/

# Or symlink so git pull updates them in place (ln -sfn replaces an existing link):
ln -sfn "$PWD/research-toolkit/skills/free-apis-catalog" ~/.claude/skills/free-apis-catalog
```

Cloning the whole repo into `~/.claude/skills/journalism-skills/` nests each `SKILL.md` too deep and will not load.

## Multi-machine workflow

This repo is developed across multiple machines. GitHub is the source of truth.

**Before switching machines:**
```bash
git add . && git commit -m "WIP" && git push
```

**After switching machines:**
```bash
git pull
```

## Adding new skills

1. Create directory: `skill-name/`
2. Add `SKILL.md` with frontmatter
3. Include templates in `templates/` if applicable
4. Update README.md skills table
5. Test with Claude Code

A new skill picks up its last-updated stamp automatically once it is on master
(see below). Slugs have to stay unique across the repo: the stamper refuses to
run on a duplicate rather than guessing which skill a stamp belongs to.

## Last-updated stamps

Every skill and plugin shows when it last changed: a strip of tape on its card
and page at skills.amditis.tech, and an `Updated` column in the README tables.
Readers use it to judge whether an installed copy has gone stale.

- `scripts/updated-stamp.mjs` writes the stamps. Git history is the source of
  truth (`git log -1 --format=%cI -- <path>`), so no date is ever hand-typed.
  Run it with no arguments to write, `--check` to see if anything is out of date.
- `docs/updated.css` draws the tape; `docs/updated.js` turns the absolute date
  into "3 days ago" and ages the tape (fresh under 90 days, yellowed under 270,
  browned past that). Relative time is computed in the browser because a
  stamped "3 days ago" would be wrong the day after the build.
- `.github/workflows/updated-stamp.yml` re-runs the stamper on pushes to master
  and commits the result. It synchronizes with the latest master and regenerates
  before each push attempt, so a concurrent update cannot strand stale stamps.

Seven rules keep it honest, all covered by tests in
`scripts/updated-stamp.test.mjs`:

1. **Dates come only from source paths, never from `docs/`.** A date derived
   from the page it is stamped into would make the CI commit bump the date,
   which would stamp again, forever.
2. **Only the absolute date goes in the HTML.** The relative age belongs to the
   reader's clock, not the build's.
3. **A surface that could not be stamped exits 1.** A page with no `<h1>`, a
   page missing the stylesheet or script, or a path with no commit history is
   reported as a problem and stops the run, because the workflow commits
   whatever the stamper leaves behind. A card pointing at something that is not
   a skill (`workflows/`, `about/`) is a note instead: that one is expected.
4. **A slug is lowercase letters, digits, and hyphens, checked when the entry
   is built.** The same string addresses an HTML attribute, a `docs/<slug>/`
   path, and a README link, so anything else is rejected rather than escaped.
5. **A stamp destination has to resolve to the regular file that names it.**
   This includes `docs/index.html`, `README.md`, and every
   `docs/<slug>/index.html`. A symlink at any path segment could write through
   to an unrelated file while CI commits an edit that appears nowhere in the
   diff.
6. **A README table is reshaped whole or not at all.** Adding a column to a
   table holding a row with an unescaped pipe makes that row exactly as wide as
   a good one, and the next run could no longer tell its last cell from a
   stamp. Such a table is skipped and every ragged row reported, so the cost is
   a missing stamp rather than deleted text.
7. **Every dated entry reaches a public surface.** A skill or plugin with no
   card, page, or root README row is reported as a problem. Bundled skills still
   need their own README rows so a change to one is visible under its own date.

## Style guidelines

- Use sentence case for headings, not title case
- Keep descriptions terse and actionable
- Include examples and templates
- Avoid AI writing patterns (see ai-writing-detox)

## Commits and attribution

No AI attribution in commits, PR bodies, issues, docs, or code. `.claude/settings.json` sets `attribution.sessionUrl` to false and blanks `attribution.commit` and `attribution.pr`, which stops Claude Code from appending a `Claude-Session:` trailer to commits, adding the session link to PR bodies, and emitting the "Generated with Claude Code" strings. Web and Remote Control sessions both emit these by default. The setting lives in the repo rather than `~/.claude/settings.json` because cloud sessions clone the repo and never read user-level config. Don't reintroduce any of it by hand.

No `Co-authored-by` trailers of any kind, including Joe's own aliases.

Git identity, set before committing, in every worktree and every agent session:

```sh
git config user.name "Joe Amditis"
git config user.email "6799804+jamditis@users.noreply.github.com"
```

Any other author email either trips GitHub's email-privacy push block (GH007) or makes a squash merge inject a `Co-authored-by` line into the merge body.
