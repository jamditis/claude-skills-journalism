# Claude skills collection

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
├── hooks/                       # Automated workflow checks
│   ├── ap-style-check.md        # PostToolUse: Flag AP Style violations
│   ├── ai-slop-detector.md      # PostToolUse: Warn about AI patterns
│   └── pre-publish-checklist.md # Stop: Pre-publication reminder
│
├── # Core journalism skills
├── source-verification/         # SIFT method, verification trails
├── foia-requests/               # Public records requests
├── data-journalism/             # Data analysis and storytelling
├── newsroom-style/              # AP Style enforcement
├── interview-prep/              # Interview preparation
├── story-pitch/                 # Pitch templates
├── fact-check-workflow/         # Claim verification
├── editorial-workflow/          # Assignment tracking, calendars
│
├── # Writing quality
├── ai-writing-detox/            # Eliminate AI writing patterns
│
├── # Project documentation
├── project-memory/              # CLAUDE.md generation
│   └── templates/               # 6 project type templates
├── project-retrospective/       # LESSONS.md generation
│   └── templates/               # 4 project type templates
├── template-selector/           # Choose the right template
│
├── # Academic
├── academic-writing/            # Research and academic writing
├── digital-archive/             # Archive building
│
├── # Development
├── vibe-coding/                 # AI-assisted development
├── electron-dev/                # Electron patterns
├── python-pipeline/             # Data pipelines
├── web-scraping/                # Content extraction
├── zero-build-frontend/         # No-build web apps
│
└── # Security
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

Hooks run automatically at specific workflow events:

| Hook | Event | Purpose |
|------|-------|---------|
| ap-style-check | PostToolUse(Write,Edit) | Flag AP Style violations |
| ai-slop-detector | PostToolUse(Write,Edit) | Warn about AI patterns |
| pre-publish-checklist | Stop | Remind about verification |

All hooks are **non-blocking warnings**. They provide guidance but don't prevent actions.

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
