# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.1] - 2026-04-14

### Added
- **pdf-playground v1.3.1**: `session-start.sh` hook that checks GitHub for a newer plugin version and prints a one-line warning if the installed copy is behind
  - Fetches `.claude-plugin/plugin.json` from the repo's `master` branch (raw.githubusercontent.com) and compares with `sort -V` for correct semver ordering
  - Rate-limited to once per 24 hours via `~/.cache/pdf-playground/last-version-check` so sessions never hit GitHub more than daily
  - 3-second network timeout and silent failure on any error — a missing curl/jq, offline host, or GitHub outage never delays or pollutes session start
  - Points users at `/pdf-playground:update` to pull the new version
  - First proactive update nudge for the plugin — previously users had to remember to run the update command themselves

## [1.6.0] - 2026-04-14

### Added
- **pdf-playground v1.3.0**: Major slide template overhaul based on real presentation feedback from the Montclair State / NJPBA RFP walkthrough deck
  - New `.slide-hero` layout: full-bleed photo background with right-aligned headline and red branded footer bar. Includes a `.slide-closing` variant with left-aligned headline and tightened subtitle for "Ready on [date]" close slides
  - New `.slide-section.with-photo` layout: photo-background section divider with a red section chip ("Section 8.1") for decks that mirror numbered documents like RFP responses
  - New `.three-col` layout: three text columns with dashed dividers for breaking a topic into parallel facets
  - New `.four-col-tiles` layout: four numbered pillar cards with red top rule and short descriptions — for parallel capabilities or themes
  - New `.stats-strip` layout: row of big numbers with small captions, each with a red left rule. Column count configurable via `--stat-cols` custom property
  - New `.slide-table` layout: comparison/budget table with red header row, gray label column, grid rules
  - New `.partner-grid` layout: 4-column grid of labeled tiles with red left accent bar for sponsor lists and letters of support
  - New `.slide-footer-red` variant: filled red footer bar with wordmark image for branded decks (alternative to the muted text footer)
  - Montserrat added to the font stack alongside Playfair Display + Source Sans 3. Switch via `--font-heading` and `--font-body` CSS variables
- **pdf-design v1.1.0**: Reusable content blocks section added to SKILL.md
  - Stats strip, three-column, four-tile pillars, and partner grid patterns documented as drop-in blocks for report and proposal pages
  - Vertical rhythm guidelines added — tighter spacing is a feature, not a bug

### Changed
- **pdf-playground v1.3.0**: Tighter vertical rhythm throughout content slides
  - Slide headline padding: 0.75in → 0.55in top
  - Slide body padding: 0.3in → 0.22in top
  - Red accent rule under headlines replaces full-width border-bottom for a cleaner visual relationship between title and body
  - Default aspect ratio: 10×7.5 (4:3) → 13.333×7.5 (16:9). Flip via the `@page` rule if 4:3 is needed
  - `commands/slides.md` rewritten with layout docs, design rules, content discipline guidance, and the multi-format delivery pattern (HTML → PDF → pptx → Google Slides)

## [1.5.1] - 2026-03-17

### Changed
- **pdf-playground v1.2.0**: Footer clearance overhaul across all templates
  - All document templates (one-pager, report, proposal, slides, event) now use CSS Grid `grid-template-rows: auto 1fr auto` instead of absolute-positioned footers
  - Footers are in normal document flow as the third grid row — no more fragile `calc()` with hardcoded header/footer heights
  - Content areas have `overflow: hidden` to prevent text bleeding into the footer zone
  - All 5 document commands updated with footer clearance verification rules
  - Document-design skill updated with the grid layout pattern and safeguards
  - Newsletter template unchanged (email table layout, not affected)
- Updated GitHub Pages docs with v1.2.0 changelog section

## [1.5.0] - 2026-03-14

### Added
- Skill evolution: skills can now self-improve based on accumulated lessons
- `post-tool-use.sh` tracks which skills are active during a session
- `user-prompt-submit.sh` tags corrections with active skill names
- Global skill lesson store at `~/.claude/skill-lessons/`
- New `/autocontext-evolve` command: scan, evolve, rollback, export, import
- `skill-lesson-injector.md` hook injects global lessons when skills load
- "Promote to global" action in `/autocontext-review`
- Steps 11-12 in `/autocontext-setup` for skill learning configuration
- Shared `config-utils.sh` for consistent config resolution
- Export/import sync with union merge for cross-machine sharing

## [1.4.1] - 2026-03-14

### Fixed
- **autocontext seed script**: filter out 5 noise patterns from CLAUDE.md bullet extraction that caused ~30% of seeded items to be headings, metadata labels, command docs, cross-references, or decontextualized fragments instead of actual lessons
- Bumped autocontext plugin to v1.0.1

## [1.3.2] - 2026-03-13

### Fixed
- Added `user_invocable: true` to all autocontext skill frontmatter so slash commands are discoverable
- Bumped autocontext plugin to v0.1.1

## [1.3.1] - 2026-03-13

### Fixed
- Moved `autocontext` and `pdf-design` plugin manifests to `.claude-plugin/plugin.json` for marketplace discovery
- Added both plugins to `.claude-plugin/marketplace.json` index so `claude plugin install` finds them
- Stripped `skills` and `hooks` arrays from manifests (auto-discovered from directory structure)
- Normalized author format to object style across all plugin manifests

## [1.3.0] - 2026-03-13

New skills, new plugin, and new docs pages added since v1.2.0.

### Added
- **`autocontext` plugin** — cross-session knowledge persistence for Claude Code
  - 5 hooks: SessionStart (load + curate), PreToolUse (warn on mistakes), UserPromptSubmit (detect corrections), PostToolUse (performance + test quality), SessionEnd (persist)
  - 4 slash commands: `/autocontext-setup`, `/autocontext-init`, `/autocontext-review`, `/autocontext-status`
  - Curator agent for lesson validation
  - Three Python scripts: `generate-playbook.py`, `merge-driver.py`, `seed-from-claude-md.py`
  - 16 unit tests
  - Cross-developer sharing via git with custom merge driver
  - Built-in test quality rules (tautological tests, bare assertions, happy-path-only, mock-as-assertion)
  - Landing page at `skills.amditis.tech/autocontext/` with interactive lesson lifecycle demo
- `visual-explainer` skill — HTML diagrams, data tables, architecture views (adapted from nicobailon/visual-explainer)
- `web-ui-best-practices` skill — signs of taste in web UI design
- `nano-banana-image-gen` skill — Gemini image generation model selection, visual grounding, cost optimization
- `free-apis-catalog` skill — 1000+ categorized free public APIs
- `animated-sprite-gen` skill — AI-generated animated sprite sheets for 2D games
- `persistent-sessions` guide — tmux configuration for long-running Claude Code sessions
- Docs pages for visual-explainer, web-ui-best-practices, animated-sprite-gen
- Support/sponsor buttons in site footer

### Fixed
- Removed debugging scripts with hardcoded paths and disabled security checks
- Fixed nested anchor tags breaking skill card layout on docs site

### Changed
- Updated skill counts on homepage (development section: 10 → 11)

---

## [1.2.0] - 2026-02-14

Added the one-way door check skill and hook, plus a flagship documentation page. Set up custom domain `skills.amditis.tech`.

### Added
- `one-way-door` skill — flag irreversible architectural decisions (data models, infra, auth, APIs, events, CI/CD, dependencies, cloud configs) before committing
- `one-way-door-check` hook — PreToolUse hook that blocks Write calls for one-way-door file patterns and forces a trade-off discussion
- Flagship page at `skills.amditis.tech/one-way-door/` with amber/gold design, SVG grid hero, 8-category grid, workflow phases, and hook code
- Custom domain `skills.amditis.tech` via Cloudflare CNAME
- Development hooks category on the homepage (one-way-door-check, bug-report-detector, enforce-test-first)

### Changed
- Updated skill and hook counts on homepage
- Reorganized hooks section on homepage to include development category

---

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

[1.3.0]: https://github.com/jamditis/claude-skills-journalism/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/jamditis/claude-skills-journalism/compare/v1.1.1...v1.2.0
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
