# Claude Skills Collection

Collection of Claude Code skills for journalism, media, academia, and technical workflows.

## Project overview

This repo contains modular instruction sets (skills) that extend Claude's capabilities for specialized tasks. Each skill directory contains domain-specific knowledge, workflows, templates, and best practices.

## Directory structure

```
claude-skills-collection/
├── academic-writing/       # Academic writing assistance
├── data-journalism/        # Data journalism workflows
├── digital-archive/        # Digital archiving patterns
├── electron-dev/           # Electron development patterns
├── foia-requests/          # FOIA request workflows
├── python-pipeline/        # Python data pipeline patterns
├── source-verification/    # Source verification workflows
├── vibe-coding/            # AI-assisted coding methodology
├── web-scraping/           # Web scraping techniques
└── zero-build-frontend/    # Zero-build frontend development
```

## Installation

Skills can be installed to `~/.claude/skills/` for Claude Code to load automatically.

---

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
