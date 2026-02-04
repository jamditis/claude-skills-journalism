# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-04

First stable release with 34 skills, 13 hooks, and full GitHub Pages documentation.

### Added
- Individual GitHub Pages for all 34 skills
- About page with author bio and contact info
- Claude Code plugin support with `plugin.json`
- PDF playground interactive demo with typing animation

### Changed
- Redesigned flagship skill pages to match pdf-playground template
- Fixed all skill card links to use local docs pages instead of GitHub

---

## [0.9.0] - 2026-02-04

### Added
- `pdf-playground` - Full Claude Code plugin with 6 document types, live preview, and brand customization
- `pdf-design` - Standalone skill for PDF reports and proposals

---

## [0.8.0] - 2026-02-01

### Added
- `test-first-bugs` - Test-driven bug fixing workflow
- `bug-report-detector` hook - Detect when users report bugs
- `enforce-test-first` hook - Enforce test-first workflow

---

## [0.7.0] - 2026-01-29

### Added
- GitHub Pages site with Amditis V2 design
- 8 new journalism workflow hooks:
  - `ap-style-check`
  - `ai-slop-detector`
  - `accessibility-check`
  - `source-attribution-check`
  - `verification-reminder`
  - `data-methodology-check`
  - `source-diversity-check`
  - `legal-review-flag`
  - `pre-publish-checklist`
  - `deadline-tracker`
  - `archive-reminder`
- 9 new skills merged from feature branches
- Project documentation templates

### Changed
- Major expansion of journalism skills and hooks

---

## [0.6.0] - 2026-01-28

### Changed
- Updated `web-scraping` skill with improved patterns
- Updated `data-journalism` skill with new workflows
- Updated `foia-requests` skill with additional templates

---

## [0.5.0] - 2026-01-16

### Added
- `CLAUDE.md` with project overview and multi-machine workflow instructions

---

## [0.4.0] - 2026-01-08

### Added
- Security skills for AI-assisted development:
  - `security-checklist`
  - `secure-auth`
  - `api-hardening`
- Google Translate proxy capture script
- Playwright console capture script
- Research on web access and console debugging tools

---

## [0.3.0] - 2026-01-08

### Added
- `mobile-debugging` - Eruda, vConsole, remote debugging patterns
- `content-access` - Unpaywall, CORE, Semantic Scholar APIs
- npm dependencies for page debugging tools

---

## [0.2.0] - 2026-01-07

### Added
- Comprehensive research on web access tools
- `page-monitoring` - Change detection and alerts
- `web-archiving` - Wayback Machine and Archive.today patterns

---

## [0.1.0] - 2025-12-25

Initial commit with foundational skills.

### Added
- Core journalism skills:
  - `source-verification` - SIFT method, digital verification
  - `foia-requests` - Public records request drafting
  - `data-journalism` - Data analysis and storytelling
  - `newsroom-style` - AP Style enforcement
  - `interview-prep` - Pre-interview research
  - `interview-transcription` - Recording and transcription
  - `story-pitch` - Pitch templates
  - `fact-check-workflow` - Claim verification
  - `editorial-workflow` - Assignment tracking
  - `crisis-communications` - Breaking news protocol
  - `social-media-intelligence` - OSINT and account analysis
- Communications skills:
  - `newsletter-publishing` - Email newsletter workflows
- Writing quality:
  - `ai-writing-detox` - Eliminate AI writing patterns
- Project documentation:
  - `project-memory` - CLAUDE.md generation
  - `project-retrospective` - LESSONS.md generation
  - `template-selector` - Template decision tree
- Academic and research:
  - `academic-writing` - Research and scholarly writing
  - `digital-archive` - Archive building with AI
- Development skills:
  - `vibe-coding` - AI-assisted development methodology
  - `electron-dev` - Electron application patterns
  - `python-pipeline` - Data processing pipelines
  - `web-scraping` - Content extraction
  - `zero-build-frontend` - No-build web apps
  - `accessibility-compliance` - WCAG compliance

---

[1.0.0]: https://github.com/jamditis/claude-skills-journalism/releases/tag/v1.0.0
[0.9.0]: https://github.com/jamditis/claude-skills-journalism/compare/a8dc4ff...4a9ed8d
[0.8.0]: https://github.com/jamditis/claude-skills-journalism/compare/43a5558...a8dc4ff
[0.7.0]: https://github.com/jamditis/claude-skills-journalism/compare/ba040ce...43a5558
[0.6.0]: https://github.com/jamditis/claude-skills-journalism/compare/485c4f2...ba040ce
[0.5.0]: https://github.com/jamditis/claude-skills-journalism/compare/7a5838a...485c4f2
[0.4.0]: https://github.com/jamditis/claude-skills-journalism/compare/32ef4c9...7a5838a
[0.3.0]: https://github.com/jamditis/claude-skills-journalism/compare/dc7792f...32ef4c9
[0.2.0]: https://github.com/jamditis/claude-skills-journalism/compare/8b81977...dc7792f
[0.1.0]: https://github.com/jamditis/claude-skills-journalism/releases/tag/v0.1.0
