# Claude skills collection

## Bug-fixing workflow

When a bug is reported, don't immediately attempt to fix it. Instead:

1. **Write a failing test first** that reproduces the bug
2. **Launch subagents** to work on fixing the bug
3. **Verify the fix** by running the test — a passing test proves the bug is fixed

---

Collection of Claude Code skills for journalism, media, academia, and technical workflows.

## Project overview

This repo contains modular instruction sets (skills) that extend Claude's capabilities for specialized tasks. Each skill directory contains domain-specific knowledge, workflows, templates, and best practices.

## Directory structure

```
claude-skills-journalism/
├── CLAUDE.md                    # This file
├── README.md                    # User documentation
├── LICENSE
│
├── hooks/                       # Automated workflow checks (14 hooks)
│   ├── ap-style-check.md        # Writing: AP Style violations
│   ├── ai-slop-detector.md      # Writing: AI patterns
│   ├── accessibility-check.md   # Writing: Alt text, headings
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
│   └── enforce-test-first.md    # Development: Enforce test-first workflow
│
├── # Plugin: journalism-core (13 skills) — registered in marketplace.json
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
│       ├── social-media-intelligence/  # OSINT, account analysis, platform-API currency
│       ├── source-verification/        # SIFT method, verification, deepfakes/C2PA
│       └── story-pitch/                # Pitch templates
│
├── # Plugin: research-toolkit (6 skills, v1.1.0) — registered in marketplace.json
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
├── # Plugin: dev-toolkit (10 skills) — registered in marketplace.json
├── dev-toolkit/
│   ├── .claude-plugin/plugin.json
│   ├── README.md
│   └── skills/
│       ├── accessibility-compliance/   # WCAG 2.2, alt text, focus management
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
├── # Plugin: pdf-design (1 skill) — registered in marketplace.json
├── pdf-design/                  # PDF reports, proposals, brand system
│   └── templates/               # HTML templates (Democracy Day, etc.)
│
├── # Plugin: visual-explainer (1 skill) — registered in marketplace.json
├── visual-explainer/            # HTML diagrams, data tables, architecture views
│   ├── references/              # CSS patterns, library guides, nav patterns
│   ├── templates/               # Architecture, flowchart, data table templates
│   └── commands/                # Slash command templates
│
├── # Plugin: project-templates-toolkit (3 skills) — registered in marketplace.json
├── project-templates-toolkit/
│   ├── .claude-plugin/plugin.json
│   ├── README.md
│   └── skills/
│       ├── project-memory/             # CLAUDE.md generation, 6 project type templates
│       ├── project-retrospective/      # LESSONS.md generation, 4 project type templates
│       └── template-selector/          # Decision tree for picking the right template
│
└── # Plugin: security-toolkit (4 skills, /hotpatch command) — registered in marketplace.json
    ├── .claude-plugin/plugin.json
    ├── README.md
    ├── commands/hotpatch.md            # Slash command: sandboxed pre-install scan + cooldown bypass
    ├── scripts/hotpatch.example.sh     # Reference Linux/bwrap implementation
    ├── test-fixtures/                  # Synthetic malicious tarballs for self-test
    └── skills/
        ├── api-hardening/              # Rate limiting, CORS, request throttling, defense-in-depth
        ├── secure-auth/                # Password hashing, sessions, JWT, OAuth, passkeys
        ├── security-checklist/         # Pre-deployment OWASP audit
        └── supply-chain-hardening/     # npm/bun install-time cooldown + sandboxed bypass scan
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

Hooks run automatically at specific workflow events. Most are **non-blocking warnings**, but `one-way-door-check` (shell hook, exits 2) and `enforce-test-first` (prompt-based) block intentionally — see each hook's "Hook behavior" section for details.

### Writing quality
| Hook | Event | Purpose |
|------|-------|---------|
| ap-style-check | PostToolUse(Write,Edit) | Flag AP Style violations |
| ai-slop-detector | PostToolUse(Write,Edit) | Warn about AI patterns |
| accessibility-check | PostToolUse(Write,Edit) | Check alt text, headings, links |

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

## Installation

This repo distributes its skills in two ways: **as Marketplace plugins** (registered in `.claude-plugin/marketplace.json`) and **as bare skill directories** (top-level dirs that haven't been bundled into a plugin yet).

### Recommended: install via Marketplace plugin

```
/plugin marketplace add jamditis/claude-skills-journalism
/plugin install journalism-core@claude-skills-journalism
```

Available plugins: `autocontext`, `dev-toolkit`, `journalism-core`, `pdf-design`, `pdf-playground`, `project-templates-toolkit`, `research-toolkit`, `security-toolkit`, `superjawn`, `visual-explainer`. See `.claude-plugin/marketplace.json` for the full list.

### Alternate: copy a single skill into `~/.claude/skills/`

Every skill in this repo now lives inside a plugin's `skills/` directory. To install just one without taking the whole plugin, clone the repo and copy the nested skill folder. Claude Code discovers skills at `~/.claude/skills/<skill-name>/SKILL.md` — one level deep:

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

## Style guidelines

- Use sentence case for headings, not title case
- Keep descriptions terse and actionable
- Include examples and templates
- Avoid AI writing patterns (see ai-writing-detox)
