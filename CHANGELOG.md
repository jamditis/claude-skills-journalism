# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2026-02-05

Update awareness and version checking for PDF Playground.

### Added
- **`/pdf-playground:update` command** — checks the installed version and runs the update
- **Pre-flight check in preview** — verifies control panel files exist before starting; warns if the plugin is outdated
- **Version check in all document commands** — reads `plugin.json` at startup to detect installation problems
- **Updating section in README** — instructions for updating the plugin and signs you need an update

### Changed
- Bumped `plugin.json` version from 1.0.0 to 1.1.1
- Bumped `marketplace.json` version from 1.0.0 to 1.1.1
- Added version info to `playground.md` skill

---

## [1.1.0] - 2026-02-05

Interactive control panel and guided wizard for PDF Playground.

### Added
- **Interactive control panel** — a sidebar that sits alongside your document for live design editing
  - 5 color theme presets (CCM brand, Professional blue, Modern green, Warm earth, Elegant purple)
  - 7 color pickers for CSS variables (primary, dark, text, heading, background, accent, gray)
  - Font dropdowns for heading and body (any Google Font, loaded dynamically)
  - Sliders for body font size, heading scale, line height, and page padding
  - Toggles to show/hide sections (stat grid, highlight boxes, case studies, budget table, mission block)
  - Layout controls (stat columns 2/3/4, heading case)
  - Undo/redo for all changes
  - "Copy changes" button generates a prompt you can paste back into Claude Code
  - Collapsible sidebar with vertical tab when minimized
- **Iframe-based preview architecture** — document lives in an iframe, controls in a wrapper page
  - Scales with browser window via CSS `clamp()` and flexbox
  - No script injection needed — the wrapper handles everything
  - Document HTML stays completely unchanged for clean PDF export
  - No re-injection after page refresh
- **Guided proposal wizard** — AskUserQuestion-driven setup with 4 phases
  - Phase 1 (Content): proposal type, sections, page count, budget items
  - Phase 2 (Design): color scheme, typography, visual style
  - Phase 3 (Review): live preview with control panel, screenshot, iterate
  - Phase 4 (Finalization): save, export, or continue editing
- **Prompt generator** — tracks changes and generates copyable prompts
  - Deduplicates by type+label (same slider moved twice = one change)
  - Skips no-op changes (e.g. background #ffffff to #ffffff)
  - Generates numbered lists for multiple changes
- **Template map system** — data-driven control panel configuration
  - `proposal.js` maps all CSS variables and selectors for the proposal template
  - New templates just need a map file (see `controls/template-maps/README.md`)
- New files: `controls/control-panel.js`, `controls/control-panel.css`, `controls/playground-wrapper.html`, `controls/prompt-generator.js`, `controls/template-maps/proposal.js`, `controls/template-maps/README.md`

### Changed
- Rewrote `commands/preview.md` for the wrapper approach (no more script injection)
- Updated `commands/proposal.md` with the full AskUserQuestion wizard
- Updated `skills/playground.md` with new architecture docs and preset list
- Updated `pdf-playground/README.md` with control panel and wrapper docs

---

## [1.0.1] - 2026-02-05

Rewrote installation docs based on user feedback. The GitHub Pages site had a broken install command (`cc --plugin-dir`) that never worked, and the instructions assumed too much prior knowledge of Claude Code and the terminal.

### Fixed
- Replaced broken `cc --plugin-dir /path/to/...` command on the PDF Playground page with the correct `claude plugin marketplace add` workflow
- Synced installation instructions across all four documentation surfaces (pdf-playground README, pdf-playground page, main site, tools repo)

### Changed
- Rewrote `pdf-playground/README.md` for beginners: added prerequisites, step-by-step explanations, and a troubleshooting section
- Rewrote the "Get started" section on the PDF Playground GitHub Pages site with correct commands, plain-language explanations, and a collapsible troubleshooting FAQ
- Updated the main site install section to show the plugin approach (recommended) alongside manual skills installation
- Made brand configuration clearly optional with an "ask Claude to create it" shortcut
- Reduced minimum brand config from 20+ lines to 3 lines (name + color)

---

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

[1.1.1]: https://github.com/jamditis/claude-skills-journalism/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/jamditis/claude-skills-journalism/compare/v1.0.0...v1.1.0
[1.0.1]: https://github.com/jamditis/claude-skills-journalism/compare/v1.0.0...v1.0.1
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
