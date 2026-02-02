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
├── hooks/                       # Automated workflow checks (13 hooks)
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
│   ├── bug-report-detector.md   # Bug fixing: Detect bug reports
│   └── enforce-test-first.md    # Bug fixing: Enforce test-first workflow
│
├── # Core journalism skills (11)
├── source-verification/         # SIFT method, verification trails
├── foia-requests/               # Public records requests
├── data-journalism/             # Data analysis and storytelling
├── newsroom-style/              # AP Style enforcement
├── interview-prep/              # Interview preparation
├── interview-transcription/     # Recording, transcription, quotes
├── story-pitch/                 # Pitch templates
├── fact-check-workflow/         # Claim verification
├── editorial-workflow/          # Assignment tracking, calendars
├── crisis-communications/       # Breaking news, rapid verification
├── social-media-intelligence/   # OSINT, account analysis
│
├── # Communications and publishing (1)
├── newsletter-publishing/       # Email newsletters, subscribers
│
├── # Writing quality (1)
├── ai-writing-detox/            # Eliminate AI writing patterns
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
├── # Development (8)
├── test-first-bugs/             # Test-driven bug fixing workflow
├── vibe-coding/                 # AI-assisted development
├── electron-dev/                # Electron patterns
├── python-pipeline/             # Data pipelines
├── web-scraping/                # Content extraction
├── zero-build-frontend/         # No-build web apps
├── mobile-debugging/            # Eruda, vConsole, remote debug
├── accessibility-compliance/    # WCAG, alt text, a11y
│
└── # Security (3)
    ├── security-checklist/      # Pre-deployment audit
    ├── secure-auth/             # Authentication patterns
    └── api-hardening/           # API security
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

Hooks run automatically at specific workflow events. All are **non-blocking warnings**.

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

## Installation

Clone to `~/.claude/skills/` for automatic loading:

```bash
git clone https://github.com/jamditis/claude-skills-journalism.git ~/.claude/skills/journalism-skills
```

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
