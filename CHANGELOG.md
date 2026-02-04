# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-04

### Added

**34 skills across 8 categories:**

#### Core journalism (11 skills)
- `source-verification` - SIFT method, digital verification, reverse image search
- `foia-requests` - Public records request drafting, tracking, appeals
- `data-journalism` - Data acquisition, cleaning, analysis, visualization
- `newsroom-style` - AP Style enforcement, attribution rules, formatting
- `interview-prep` - Pre-interview research, question frameworks, consent
- `interview-transcription` - Recording workflows, transcription, quotes
- `story-pitch` - Pitch templates for news, features, investigations
- `fact-check-workflow` - Claim extraction, evidence gathering, ratings
- `editorial-workflow` - Assignment tracking, deadlines, calendars
- `crisis-communications` - Breaking news protocol, rapid verification
- `social-media-intelligence` - OSINT, account analysis, coordination detection

#### Communications (1 skill)
- `newsletter-publishing` - Email newsletters, subscriber management

#### Design and production (2 skills)
- `pdf-playground` - Full Claude Code plugin with 6 document types
- `pdf-design` - PDF reports and proposals with print-ready CSS

#### Writing quality (1 skill)
- `ai-writing-detox` - Eliminate AI-generated writing patterns

#### Project documentation (3 skills)
- `project-memory` - Generate CLAUDE.md files with 6 templates
- `project-retrospective` - Generate LESSONS.md files with 4 templates
- `template-selector` - Decision tree for choosing templates

#### Academic and research (5 skills)
- `academic-writing` - Research design, literature reviews, grants
- `digital-archive` - Archive building with AI enrichment
- `web-archiving` - Wayback Machine, Archive.today, preservation
- `content-access` - Unpaywall, CORE, Semantic Scholar access
- `page-monitoring` - Change detection, RSS generation, alerts

#### Development (8 skills)
- `vibe-coding` - AI-assisted software development methodology
- `electron-dev` - Electron + React desktop application patterns
- `python-pipeline` - Data processing pipelines
- `web-scraping` - Content extraction with anti-bot handling
- `zero-build-frontend` - Static web apps without build tools
- `mobile-debugging` - Eruda, vConsole, remote debugging
- `accessibility-compliance` - WCAG compliance, accessible design
- `test-first-bugs` - Test-driven bug fixing workflow

#### Security (3 skills)
- `security-checklist` - Pre-deployment security audit
- `secure-auth` - Authentication patterns (sessions, JWT, OAuth)
- `api-hardening` - Rate limiting, input validation, CORS

**13 automated hooks:**
- `ap-style-check` - Flag AP Style violations
- `ai-slop-detector` - Warn about AI patterns
- `accessibility-check` - Check alt text, headings, links
- `source-attribution-check` - Flag unattributed quotes
- `verification-reminder` - Prompt fact verification
- `data-methodology-check` - Ensure methodology documented
- `source-diversity-check` - Note sourcing diversity
- `legal-review-flag` - Flag defamation risk
- `pre-publish-checklist` - Pre-publication reminder
- `deadline-tracker` - Surface upcoming deadlines
- `archive-reminder` - Remind to archive URLs
- `bug-report-detector` - Detect bug reports
- `enforce-test-first` - Enforce test-first workflow

**GitHub Pages site:**
- Main site at jamditis.github.io/claude-skills-journalism
- Individual pages for all 34 skills
- About page with author info

**Claude Code plugin support:**
- Can be installed as a Claude Code plugin
- Plugin manifest at `plugin.json`

[1.0.0]: https://github.com/jamditis/claude-skills-journalism/releases/tag/v1.0.0
