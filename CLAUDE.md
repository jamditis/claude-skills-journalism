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
├── # Plugin: journalism-core (11 skills) — registered in marketplace.json
├── journalism-core/
│   ├── .claude-plugin/plugin.json
│   ├── README.md
│   └── skills/
│       ├── ai-writing-detox/        # Eliminate AI writing patterns
│       ├── crisis-communications/   # Breaking news, rapid verification
│       ├── editorial-workflow/      # Assignment tracking, calendars
│       ├── fact-check-workflow/     # Claim verification
│       ├── foia-requests/           # Public records requests
│       ├── interview-prep/          # Interview preparation
│       ├── interview-transcription/ # Recording, transcription, quotes
│       ├── newsletter-publishing/   # Email newsletters, subscribers
│       ├── newsroom-style/          # AP Style enforcement
│       ├── source-verification/     # SIFT method, verification, deepfakes/C2PA
│       └── story-pitch/             # Pitch templates
│
├── # Bare journalism skills (candidates for future bundles)
├── data-journalism/             # Data analysis and storytelling
├── social-media-intelligence/   # OSINT, account analysis
│
├── # Design and production (2)
├── pdf-design/                  # PDF reports, proposals, brand system
│   └── templates/               # HTML templates (Democracy Day, etc.)
├── visual-explainer/            # HTML diagrams, data tables, architecture views
│   ├── references/              # CSS patterns, library guides, nav patterns
│   ├── templates/               # Architecture, flowchart, data table templates
│   └── prompts/                 # Slash command templates
│
├── # Project documentation (3)
├── project-memory/              # CLAUDE.md generation
│   └── templates/               # 6 project type templates
├── project-retrospective/       # LESSONS.md generation
│   └── templates/               # 4 project type templates
├── template-selector/           # Choose the right template
│
├── # Academic and research (5)
├── academic-writing/            # Research and academic writing
├── digital-archive/             # Archive building
├── web-archiving/               # Wayback, Archive.today, evidence
├── content-access/              # Unpaywall, CORE, library access
├── page-monitoring/             # Change detection, alerts
│
├── # Development (10)
├── test-first-bugs/             # Test-driven bug fixing workflow
├── vibe-coding/                 # AI-assisted development
├── one-way-door/                # Flag irreversible architectural decisions
├── electron-dev/                # Electron patterns
├── python-pipeline/             # Data pipelines
├── web-scraping/                # Content extraction
├── zero-build-frontend/         # No-build web apps
├── mobile-debugging/            # Eruda, vConsole, remote debug
├── accessibility-compliance/    # WCAG, alt text, a11y
├── web-ui-best-practices/       # Signs of taste in web UI
│
├── # Security (3)
├── security-checklist/          # Pre-deployment audit
├── secure-auth/                 # Authentication patterns
├── api-hardening/               # API security
│
├── # AI and creative tools (1)
├── nano-banana-image-gen/       # Gemini image gen model selection and prompting
├── animated-sprite-gen/         # AI-generated animated sprite sheets
│
└── # Reference (1)
    └── free-apis-catalog/       # 1000+ free public APIs by category
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

Available plugins: `autocontext`, `journalism-core`, `pdf-design`, `pdf-playground`, `superjawn`. See `.claude-plugin/marketplace.json` for the full list.

### Alternate: copy a bare skill into `~/.claude/skills/`

For skills that haven't been packaged into a plugin yet (e.g., `data-journalism`, `social-media-intelligence`), Claude Code discovers skills at `~/.claude/skills/<skill-name>/SKILL.md` — one level deep:

```bash
git clone https://github.com/jamditis/claude-skills-journalism.git ~/projects/claude-skills-journalism
cd ~/projects/claude-skills-journalism
mkdir -p ~/.claude/skills
cp -r data-journalism ~/.claude/skills/
# or: ln -sfn "$PWD/data-journalism" ~/.claude/skills/data-journalism
```

For skills inside a plugin directory (e.g., `journalism-core/skills/source-verification`), point at the nested path:

```bash
cp -r journalism-core/skills/source-verification ~/.claude/skills/
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
