# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **dev-toolkit context-engineering-fundamentals:** published the context
  engineering skill from the tools repo standouts (group 4 of #115). Teaches the
  attention budget, the lost-in-middle effect, five context degradation patterns
  with mitigations, and practical size thresholds. Stripped the project-bound
  "Amditis Resource Kit" section, the dangling related-skill references, and the
  dated version footer before publishing (#220).

## [2.4.0] - 2026-07-25

This release advances photo provenance and OKF secret detection, records a
no-Claude runtime boundary for okf-wiki, and finishes the attribution-hook
parser hardening with required CI coverage.

### Added

- **okf-wiki provider detectors:** added default high-signal checks for
  Anthropic, GitLab, npm, OpenAI, SendGrid, and Stripe secrets. Prefix-based
  formats use provider-specific shape, boundary, and entropy checks so
  human-readable vault paths remain valid (#248).
- **okf-wiki runtime evidence:** added a repeatable isolated Codex pilot that
  verifies skill and spec reads, exact generated output, an immutable install,
  and the boundary between the portable OKF bundle and its inert Claude adapter
  files (#251).

### Changed

- **photo-metadata:** modernized for current provenance practice using IPTC,
  C2PA, Google, and exiftool primary sources. Adds AI/synthetic
  labeling via IPTC `DigitalSourceType` (full controlled vocabulary, with the
  `trainedAlgorithmicMedia` / `compositeWithTrainedAlgorithmicMedia` /
  `compositeSynthetic` distinctions and the IPTC 2025.1 AI-system/prompt fields);
  a C2PA / Content Credentials section (exiftool reads but cannot sign — use
  `c2patool` / `verify.contentauthenticity.org` — with cautions that a credential
  proves a signature, not truth); GPS-stripping guidance and an `embed.py
  --strip-gps` flag for source protection; Google Images "Licensable" fields
  (`xmpRights:WebStatement` + PLUS `Licensor*`); an XMP-first framing with a
  HEIC/AVIF/WebP format table; and a corrected caption vs. alt-text vs. extended-
  description distinction. `embed.py` gains `digital_source_type` (shorthand→URI,
  per-image override), licensing, and `ext_description` manifest fields, with
  black-box round-trip coverage (#255).
- **Published versions:** marketplace `2.3.3 → 2.4.0`; journalism-core
  `1.2.0 → 1.3.0`; and okf-wiki `0.6.1 → 0.7.0`.

### Fixed

- **Document design updates:** added a fail-closed migration, verifier, fixture,
  and live canary for the historical project-lock key that blocked updates in
  Skills CLI 1.5.20 (#252).
- **Attribution hook:** catches an inherited Git identity and models measured
  Bash `cd`, `pushd`, `popd`, ANSI-C quoting, and directory-stack behavior when
  resolving commit message files. A required hook-test workflow now gates
  changes to the executable parser (#253, #258).

## [2.3.3] - 2026-07-23

This release catches the public GitHub history up to marketplace `2.3.3`. It adds
the video toolkit, hardens executable and remote-content boundaries, and records
the first verified Codex installation and package-runtime evidence. The Codex
work is a phase-one baseline, not a repository-wide support declaration; commands,
agents, hooks, and packages without completed runtime gates remain outside the
claim.

### Added

- **video-toolkit 1.0.3:** added `video-dashboard`, `video-download`,
  `video-frames`, and `video-transcribe`, with a docs page and marketplace
  registration. The transcription workflow records source, model, build, and
  decode provenance; CPU `whisper.cpp` remains the reproducible transcript of
  record while GPU paths are optional accelerators (#189, #213, #218, #222).
- **Codex phase-one baseline:** added a checked-in 12-package compatibility
  matrix, a pinned official Agent Skills validator, install canaries for Claude
  and the tested Codex paths, and client-specific installation guidance. The
  canaries verify the exact installed file set and hashes without adding a
  native Codex manifest (#225, #246).
- **Paired runtime pilots:** recorded successful Claude and standards-based
  Codex runs for all 14 `journalism-core` skills, plus a standards-based Codex
  run for the `visual-explainer` root skill and its relative resources. The
  legacy package route, generated wrappers, source commands, and broader
  package claims retain their documented limits (#247, #249).
- **Compatibility drift gates:** added current-client scheduled checks, bounded
  canary runtimes, catalog-to-child metadata checks, native-manifest path
  guards, and Windows line-ending and path portability coverage (#225).
- **Editorial hooks:** added `copywriting-preflight`, `pre-commit-review`, and
  an executable `no-ai-attribution` hook with tests for common Git and GitHub
  CLI invocation paths (#135, #160, #176, #193).
- **Last-updated stamps:** every skill and plugin card now shows its last source
  change from Git history. A scheduled writer keeps the README and docs
  surfaces synchronized, and the docs finder excludes the stamp text from
  search results (#202).

### Changed

- **okf-wiki 0.2.0 → 0.6.1:** added an author-from-existing-sources
  workflow, an onboarding interview, format version 0.2 with backward reading
  support, domain-neutral concept types, documented upstream divergences, and
  opt-in entropy checks for URL-safe secrets. Validator and scaffold fixes cover
  provenance quoting, dead wikilinks, aliases and merges, ISO 8601 timestamps,
  PyYAML requirements, canonical/example drift, and safe `--force` behavior
  (#136, #147-#149, #159, #163-#168, #174, #184, #186, #190, #192, #204,
  #243).
- **Agent Skills metadata:** restored official CLI discovery, normalized
  `document-design`, removed its duplicate version field, and removed
  Claude-only `argument-hint` keys from the four video skills. Claude invocation
  and argument delivery remain tested (#224, #225).
- **Security boundaries:** high-risk skills now state trust boundaries for
  untrusted content and remote input. Runtime CDN execution, the Tailwind Play
  CDN, and runtime Whisper source fetching were removed; checksum and video
  dependency checks were tightened (#201, #206, #207, #209, #212, #215, #217,
  #222).
- **Published versions:** marketplace `2.2.0 → 2.3.3`; dev-toolkit
  `1.1.0 → 1.1.1`; okf-wiki `0.2.0 → 0.6.1`; pdf-playground
  `1.3.1 → 1.3.2`; and the new video-toolkit at `1.0.3`.

### Fixed

- **FOIA deadlines:** the federal deadline helper now counts 20 business days
  and excludes federal holidays as documented (#180).
- **Autonomy kit:** corrected subscription estimates when review is disabled,
  fixed the launchd template, and added Python and template checks to CI (#134,
  #178, #191).
- **Docs and examples:** fixed okf-wiki contrast and mobile table clipping,
  replaced runtime Tailwind compilation with committed CSS, and hardened scraper
  redirects and webhook failure handling (#133, #183, #206, #212).

## [2.2.0] - 2026-06-24

### Added

- **claude-md-updater skill:** added a dev-toolkit workflow that extracts
  durable lessons from a session and proposes a scoped `CLAUDE.md` edit as an
  exact diff before writing. Transient notes stay in auto memory or a local,
  ignored file. The release also added the skill's docs page and synchronized
  the catalog to 56 skills and 11 plugins (#127).

## [2.1.0] - 2026-06-24

The marketplace rollup added okf-wiki and the work shipped between the bundling
release and its June catalog cut.

### Added

- **okf-wiki 0.2.0:** added an Open Knowledge Format scaffolder,
  validator, example bundle, docs page, optional GitHub-wiki bootstrap, and
  session-orientation hooks that merge safely into existing Claude settings
  (#129-#131).
- **photo-metadata:** added a fourteenth journalism-core skill for writing and
  verifying wire-ready IPTC, EXIF, and XMP captions, credits, alt text, location,
  keywords, and licensing fields (#119).
- **Guides and workflows:** added the autonomy issue-workhorse kit and cost
  estimator, a multi-agent workflows guide, and a vendor-neutral X/Twitter
  evidence-packet workflow (#91, #97-#100, #103, #108, #117).
- **supply-chain-hardening:** added the security-toolkit skill, hotpatch
  command, sandboxed package scanner, docs page, and CI self-test (#77, #80,
  #84).

### Changed

- **one-way-door:** made approval stateful, narrowed false-positive matching, and
  added behavior-matched PowerShell hooks for Windows (#114).
- **Supply-chain scanner:** added Linux `bwrap`, macOS `sandbox-exec`, and
  PowerShell paths with explicit fallback behavior when a sandbox backend is
  unavailable (#77, #84).
- **Docs:** synchronized catalog counts and sitemap coverage, tightened page
  copy, hardened external links, and fixed mobile diagrams and contrast across
  the autonomy, workflows, and skill pages (#81-#83, #92, #95, #100-#101,
  #122-#124).

### Fixed

- **Autonomy schedules:** corrected named-weekday cron estimates and native
  Windows scheduling guidance (#109, #113).
- **Docs verification:** fixed an intermittent undici failure in the
  accessibility gate and restored accurate hook and install claims (#94, #123).

## [2.0.0] - 2026-05-11

The bundling milestone: every skill in the repo now lives inside a registered plugin, so the marketplace install path is the only first-class install path. Headline numbers: 10 plugins registered (was 4 at v1.9.0), zero bare skill directories at the repo root, marketplace manifest version bumped 1.8.0 → 2.0.0 to signal the breaking layout change.

### Breaking

- **Bare-path skill installs no longer work.** Every skill moved from `<repo>/<skill>/` to `<repo>/<plugin>/skills/<skill>/` across Phases 1-6 (PRs #60-#69). Anyone scripting `cp -r ~/projects/claude-skills-journalism/<skill> ~/.claude/skills/` against the old paths will get "no such file." Updated install paths are documented on each `docs/<skill>/index.html` landing page (PR #71) and in the top-level README. Recommended fix: switch to `/plugin install <plugin>@claude-skills-journalism`.
- **Two skills removed (#65)**: `animated-sprite-gen` and `nano-banana-image-gen`. Off-theme for a journalism-skills repo; never bundled into a plugin. No replacement.

### Added

- **journalism-core plugin v1.1.0 (#60, #61)**: 13 skills — `ai-writing-detox`, `crisis-communications`, `data-journalism`, `editorial-workflow`, `fact-check-workflow`, `foia-requests`, `interview-prep`, `interview-transcription`, `newsletter-publishing`, `newsroom-style`, `social-media-intelligence`, `source-verification`, `story-pitch`. Phase 2 (#61) absorbed `data-journalism` and `social-media-intelligence` from the bare-skill set.
- **research-toolkit plugin v1.1.0 (#62, #69)**: 6 skills — `academic-writing`, `content-access`, `digital-archive`, `free-apis-catalog`, `page-monitoring`, `web-archiving`. v1.1.0 (#69) absorbed `free-apis-catalog` from the bare-skill set.
- **dev-toolkit plugin v1.0.0 (#63)**: 10 skills — `accessibility-compliance`, `electron-dev`, `mobile-debugging`, `one-way-door`, `python-pipeline`, `test-first-bugs`, `vibe-coding`, `web-scraping`, `web-ui-best-practices`, `zero-build-frontend`.
- **security-toolkit plugin v1.0.0 (#64)**: 3 skills — `api-hardening`, `secure-auth`, `security-checklist`. Includes 2026 currency sweep aligned to OWASP Top 10:2025, NIST SP 800-63B-4, OAuth 2.1, WebAuthn L3.
- **project-templates-toolkit plugin v1.0.0 (#68)**: 3 skills — `project-memory`, `project-retrospective`, `template-selector`.
- **visual-explainer plugin (#68 registration)**: registered in marketplace.json alongside the v0.7.1 backport (#66) that pulled in the upstream nicobailon/visual-explainer fork while preserving journalism overlays.

### Changed

- **Currency sweeps across multiple skills** (Phase 3 #62, Phase 5 #64, Phase 6c #67): updated `data-journalism`, `social-media-intelligence`, `source-verification`, `web-archiving`, `page-monitoring`, `api-hardening`, `secure-auth`, `security-checklist`, `project-memory`, `project-retrospective`, `free-apis-catalog` against authoritative 2026 sources (NIST, IETF, W3C, OWASP, vendor docs, CVE DBs).
- **visual-explainer backported v0.1.0 → upstream v0.7.1 (#66)**: pulled in the upstream nicobailon/visual-explainer fork at v0.7.1, preserved the journalism-specific palette and design sensibilities as overlays.
- **Docs site sweep (#71)**: 36 landing pages updated for the bundling reorg — install snippets switched from `cp -r <skill>` to the plugin-install pattern with the new plugin-nested bare path as a fallback. 41 GitHub tree links rewritten to the new paths. 28 pages got real `<meta name="description">` tags sourced from each SKILL.md frontmatter (previously many had placeholder OG descriptions like "A Claude Code skill for X"). 5 pages had lead-paragraph drift fixed against their SKILL.md.
- **project-memory language drift fix (this release)**: SKILL.md body lines 8 and 140, plus `docs/project-memory/index.html` lines 237 and 381, now consistently use "institutional knowledge" — matching the canonical phrasing from the SKILL.md frontmatter description (which already used that phrasing after Phase 6c). Closes the last drift loose-thread from PR #71.

### Fixed

- **Indentation drift on 2 docs pages (#71)**: install-snippet bulk fixer hardcoded a 16-space leading indent, which broke on `web-ui-best-practices/index.html` and `one-way-door/index.html` where the install block sits inside an Option-1/Option-2 wrapper at 24-space context. Surgically re-indented both before PR #71 merged.

## [1.9.0] - 2026-05-08

### Changed

- **superjawn v1.0.0 — standalone (#58)**: decouples superjawn's runtime dispatch from the upstream `superpowers` plugin. The four `superpowers:code-reviewer` agent dispatches that v0.6.0 left in place (three in `requesting-code-review/SKILL.md`, one in `subagent-driven-development/code-quality-reviewer-prompt.md`) now target `pr-review-toolkit:code-reviewer`, an Anthropic-maintained agent in `@claude-code-plugins`. After this release, no skill in `superjawn` requires the upstream `superpowers` plugin to be installed. The original "≥2 weeks of real use" readiness gate is waived ahead of ship; reinstall path for the upstream plugin is `/plugin install superpowers@claude-plugins-official`. Manifest: `requesting-code-review` drops `skill_md_parity` from `true` to `false` (the rewrite breaks byte-identity); `subagent-driven-development` adds a `supporting_file_overrides` entry for `code-quality-reviewer-prompt.md`. Three documentation example mentions of `superpowers:code-reviewer` in `using-superjawn/references/{codex,copilot}-tools.md` are intentionally preserved as references to upstream's canonical agent name.
- **persistent-sessions guide expanded (#57)**: promotes the SSH path to first-class alongside Cockpit in the auto-attach step, marks the Cockpit `IdleTimeout` step as Cockpit-only with an anchor link, adds an "Installing tmux" table covering Debian/Ubuntu, Fedora/RHEL, Arch, openSUSE, Alpine, macOS, FreeBSD, and WSL2 (plus notes on Windows-as-server and macOS-as-server), and adds a "Connecting from different devices" section covering macOS, Windows, Linux, iOS/iPadOS, Android, ChromeOS, Cockpit, and mosh. Notes the Ctrl-prefix alternative for mobile keyboards and updates the CTA so it no longer claims the skill requires Cockpit.
- **Marketplace landing page: superjawn card refreshed**. The featured-plugin card on `docs/index.html` previously read "v0.6.0 ships all 14 skills; v1.0.0 (disabling the upstream plugin) gates on 2 weeks of real use." Now reads as the v1.0.0 standalone description, matching `docs/superjawn/index.html` (which was updated in PR #58).

### Fixed

- **README skill-status table for `superjawn` (#58 fold-in)**: eight rows still read "Pending (Batch 3/4/5)" for skills that had already shipped, one category was wrong (`subagent-driven-development` listed as freshness check instead of consumer), and the phase-shape counts were off by one (1 freshness + 10 consumer, was written as 2 + 9). All corrected as part of the v1.0.0 cut.
- **`superjawn:debugging` typo in top-level `README.md` plugin catalog (#58 round 1 Copilot)**: the row's "fires before brainstorming, debugging, and writing-skills" copy and the example invocation `superjawn:debugging` referenced a skill that does not exist; the actual skill is `systematic-debugging`. Updated both occurrences so the example invocation resolves to a real skill.

## [1.8.0] - 2026-05-07

### Added

- **superjawn v0.6.0 — feature-complete (#46, #48)**: all 14 skills now ported across five batches. Final batch (Batch 5) brings `finishing-a-development-branch`, `using-superjawn` (the bootstrap skill, ported from upstream `using-superpowers` so the directory + frontmatter `name:` field match the local plugin's identity), and the writing-skills triad. Earlier in the window: Batch 3 added the `code-review` pair plus the validator script (`#36` series), Batch 4 added parallel execution and `using-git-worktrees` (`#46`).
- **Validator support for renamed ports (#48)**: `superjawn/scripts/validate-skill.sh` now reads an optional `upstream_name:` field from `superjawn/skills-manifest.json` so renamed ports (`using-superjawn` ← `using-superpowers`) pass parity checks against the upstream skill of record.

### Fixed

- **CVE chain cleared by removing `puppeteer-core` (#41, #50)**: the dependency was never imported anywhere in the repo. Removing it eliminated GHSA-5rq4-664w-9x2c (path traversal) and GHSA-6v7q-wjvx-w8wg (CRLF injection) and shrank the install footprint substantially. `playwright` remains for the small number of scripts that actually use a browser.
- **`single-file-cli` removed (#51, #53)**: same pattern — declared but unused. Its removal dropped the dependency tree from ~80 packages to 5 and cleared GHSA-rp42-5vxx-qpwr, GHSA-rpmf-866q-6p89 (DoS), and GHSA-v2v4-37r5-5v8g (XSS). `npm audit` now reports zero vulnerabilities.

### Changed

- **CI: `actions/checkout` v4 → v6 (#27, #54)**: aligns with GitHub Actions runner deprecations around Node.js 20 (warnings 2026-06-02, hard fail 2026-09-16). Both `lint-skills` and `check-readme` jobs run under v6. The workflow's `paths:` filter includes itself, so the bump verified itself on the PR under the new pin — no separate dispatch needed.
- **Featured plugin on the landing page: autocontext → superjawn (#52)**: the hero slot now showcases superjawn v0.6.0 with a "New in v0.6.0" pill, headline "Skills that do their homework first.", and a copy block pitching the research-augmented fork plus the default-on research phase. autocontext stays in the plugin grid below — only the hero rotates.
- **README: plugin table expanded** to list all four marketplace plugins (`autocontext`, `pdf-design`, `pdf-playground`, `superjawn`). Previously listed only `pdf-playground`.
- **Docs: skill and hook counts corrected.** Landing page hero badge, OG/Twitter descriptions, and JSON-LD schema now report 39 skills + 14 hooks (was a mix of 31/37 skills and 11/14 hooks across stale fields). `CLAUDE.md` directory tree now reads "14 hooks" instead of "13."

## [1.7.0] - 2026-05-05

### Added

- **superjawn plugin (#34, #35, #36, #37)** — new plugin at v0.3.0. Research-augmented fork of [obra/superpowers](https://github.com/obra/superpowers) v5.0.7 (MIT, dual-copyright Vincent 2025 / Amditis 2026) with a default-on research phase at entry-point stages: web search, codebase prior-bugs (`git log --grep`), authoritative docs, and memory check before Claude commits to a direction. Three categories:
  - **Research** (entry points where work originates without an upstream artifact): `brainstorming`, `systematic-debugging`. Research phase fires by default.
  - **Freshness check** (stale-artifact consumers): `executing-plans`. Default-skip; fires only when a trigger indicates real drift risk (cross-session execution, external API touched, working on master/main).
  - **Consumer** (trust the upstream-artifact handoff): `writing-plans`, `test-driven-development`, `verification-before-completion`.

  v0.3.0 ships 6 of 14 ported skills (foundation + debugging triads). Eight more pending across batches 3–5.

  Landing page: https://skills.amditis.tech/superjawn/

### Fixed

- **autocontext slash commands (#26)**: Claude Code's plugin-namespaced commands use colons (`/autocontext:review`), not hyphens. INSTALL.md, CLAUDE.md, and the docs site updated to match actual invocation.
- **WCAG 2.2 AA pass across all 45 docs/ pages (#40)**: 86 violations to 0 — alt text, heading order, color contrast, focus-visible, link purpose. Validated with axe-core via Playwright.
- **Plugin grid layout (#38)**: docs landing page plugin grid bumped from 3 columns to 4 so the fourth card (superjawn) doesn't strand on its own row.
- **Marketplace version sync (#33, #39)**: `marketplace.json` plugin entries are now kept in sync with each plugin's individual `plugin.json` version. Closes the drift surfaced by issue #33.

### Changed

- **Global instructions cleanup (#28, #30, #31, #32)**: slimmed `.github/copilot-instructions.md` from 47 lines to 13 (Copilot's 4k char cap was being burned on prose conventions Copilot doesn't enforce); narrowed `CLAUDE.md` to the bot-enforceable subset; corrected hook-mechanism wording so the "blocking hooks" claim accurately reflects which hooks block (`one-way-door-check` shell hook + `enforce-test-first` prompt-based) versus which are advisory.

## [1.6.2] - 2026-04-22

### Fixed
- **Install instructions** (reported by Marjorie Roswell on the Knight Center MOOC forum): `git clone ... ~/.claude/skills/journalism-skills` nested every `SKILL.md` two levels deep, so Claude Code's skill discovery (which scans `~/.claude/skills/<name>/SKILL.md` one level deep) loaded nothing from the clone. Updated `README.md`, `CLAUDE.md`, `autocontext/README.md`, and `docs/index.html` (skills.amditis.tech) to clone outside `~/.claude/skills/` and copy or symlink individual skills into place.
- Install commands are now idempotent: added `mkdir -p ~/.claude/skills` and switched symlink examples to `ln -sfn`, so re-running the instructions replaces an existing link instead of erroring.

## [1.6.1] - 2026-04-14

### Added
- **pdf-playground v1.3.1**: `session-start.sh` hook that checks GitHub for a newer plugin version and prints a one-line warning if the installed copy is behind
  - Fetches `.claude-plugin/plugin.json` from the repo's `master` branch (raw.githubusercontent.com) and compares with `sort -V` for correct semver ordering
  - Rate-limited to once per 24 hours via `$XDG_CACHE_HOME/pdf-playground/last-version-check` when set, or `~/.cache/pdf-playground/last-version-check` otherwise. Applies to failed checks too — an offline host gets rate-limited the same way a successful one does
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

[Unreleased]: https://github.com/jamditis/claude-skills-journalism/compare/v2.4.0...HEAD
[2.4.0]: https://github.com/jamditis/claude-skills-journalism/compare/v2.3.3...v2.4.0
[2.3.3]: https://github.com/jamditis/claude-skills-journalism/compare/v2.2.0...v2.3.3
[2.2.0]: https://github.com/jamditis/claude-skills-journalism/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/jamditis/claude-skills-journalism/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/jamditis/claude-skills-journalism/compare/v1.9.0...v2.0.0
[1.9.0]: https://github.com/jamditis/claude-skills-journalism/compare/v1.8.0...v1.9.0
[1.8.0]: https://github.com/jamditis/claude-skills-journalism/compare/v1.7.0...v1.8.0
[1.7.0]: https://github.com/jamditis/claude-skills-journalism/compare/v1.6.2...v1.7.0
[1.6.2]: https://github.com/jamditis/claude-skills-journalism/compare/v1.6.1...v1.6.2
[1.6.1]: https://github.com/jamditis/claude-skills-journalism/compare/v1.6.0...v1.6.1
[1.6.0]: https://github.com/jamditis/claude-skills-journalism/compare/v1.5.1...v1.6.0
[1.5.1]: https://github.com/jamditis/claude-skills-journalism/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/jamditis/claude-skills-journalism/compare/v1.4.1...v1.5.0
[1.4.1]: https://github.com/jamditis/claude-skills-journalism/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/jamditis/claude-skills-journalism/compare/v1.3.0...v1.4.0
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
