# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Codex phase-one installation baseline:** added a checked-in 12-package compatibility matrix, a pinned Agent Skills validator, clean `journalism-core` canaries for Claude, Codex's legacy package reader, the project `.agents/skills` path, and the user `~/.agents/skills` path, plus client-specific installation guidance. The canaries require the exact 14-skill and 17-file package, compare installed file hashes with the source, and add no native Codex manifest.
- **Compatibility drift gates:** added a scheduled check against the current upstream Agent Skills validator while keeping pull-request validation pinned, bounded client canary runtimes, linked package evidence records, native Codex manifest path guards, and catalog-to-child metadata equality checks.
- **Windows verification portability:** normalized repository-relative result paths and line endings in cross-platform checks, preserved the one NTFS-impossible path fixture as a Windows-only skip, and added CRLF regression coverage for the docs CSS freshness gate.
- **Last-updated stamps on every skill and plugin (this PR)**: each card and skill page at skills.amditis.tech now carries the date that skill or plugin last changed, and the README tables gained an `Updated` column. Readers installing a skill can see whether their copy is likely to have drifted from its sources. Dates come from git history (`git log -1 --format=%cI -- <path>`), never from a hand-maintained field, so a stamp cannot silently rot. `scripts/updated-stamp.mjs` writes all three surfaces and is idempotent; `docs/updated.css` draws the date as a strip of tape that yellows with age (fresh under 90 days, yellowed under 270, browned past that) and `docs/updated.js` converts the stamped absolute date to a relative one in the reader's browser, because a relative age baked into a static file is wrong the day after the build. `.github/workflows/updated-stamp.yml` re-runs the stamper on pushes to master that touch a date source and commits the result. Six invariants are covered by tests in `scripts/updated-stamp.test.mjs`: dates are never derived from `docs/` (a date read from the page it is stamped into would make the CI commit bump the date and stamp again, forever); a duplicate skill slug stops the run rather than letting two skills stamp each other; a slug is checked to be lowercase letters, digits, and hyphens where the entry is built, because the same string addresses an HTML attribute, a `docs/<slug>/` path, and a README link; any surface that could not be stamped exits 1 rather than logging a warning the CI commit would ride past; a stamp destination has to resolve to the path that names it, so a symlink at any segment cannot write through to another page; and a README table holding a row with an unescaped pipe is skipped whole and reported, because widening it would make that row indistinguishable from a stamped one on the next pass. The index finder excludes tape text from its search corpus so a card cannot match on its own date. Every tier clears WCAG AA contrast on all card and hero backgrounds, and the age is stated in words as well as color.
- **`photo-metadata` skill (journalism-core, this PR)**: new `journalism-core/skills/photo-metadata/` skill for embedding wire- and archive-ready metadata into image files — caption, byline, credit, alt text, keywords, location, and copyright or Creative Commons license written across the IPTC, EXIF, and XMP layers with exiftool. Leads with the newsroom discipline a capable model otherwise skips: caption only what is visible, label people from visible evidence, always write a screen-reader `AltTextAccessibility` field, keep editorial framing in `Headline` rather than the structured location or caption fields, and verify the round-trip by reading the metadata back from the file. Ships `SKILL.md`, a `reference.md` field map (IPTC-IIM byte limits, the Creative Commons field set, the AP caption recipe, and the alt-text-versus-caption distinction), and a generic `embed.py` that batch-tags a local folder from a JSON manifest and reads each file back to confirm. journalism-core `1.1.0 → 1.2.0`; the plugin and marketplace descriptions move Thirteen → Fourteen skills. Built test-first per `writing-skills`: the RED baseline without the skill omitted alt text, wrote caption detail not visible in the frame, and set an incomplete license; GREEN with the skill closed all three and refused an unverifiable bystander claim. The marketplace rollup version stays `2.1.0` until the next release cut.
- **`one-way-door` Windows (PowerShell) port** (this PR): `dev-toolkit/skills/one-way-door/one-way-door-check.ps1` and `one-way-door-approve.ps1`, behavior-matched to the shell hooks for Windows, where Claude Code runs hooks through PowerShell and `tool_input.file_path` can arrive with backslashes (which `basename` does not split on, so the shell safelist would misfire). The ports share the same session ledger (`%USERPROFILE%\.claude\hooks\state\one-way-door\`), early-exit safelist, and one-way-door categories; filename and directory splitting goes through `[System.IO.Path]` and directory patterns are matched after normalizing `\` to `/`, so the check is correct for backslash and forward-slash paths alike. Verified against a block / safelist / stateful-approve test matrix. Documented with the PowerShell `settings.json` wiring in `SKILL.md`, `hooks/one-way-door-check.md`, and `docs/one-way-door/index.html`.

### Changed

- **Shared frontmatter now passes the Agent Skills specification:** normalized `document-design`, removed its stale duplicate version field, and removed Claude-only `argument-hint` fields from the four video skills. Claude invocation and argument delivery remain tested. `pdf-playground` advanced to 1.3.2, `video-toolkit` to 1.0.3, and the Claude marketplace to 2.3.3 so existing installs can receive the repaired files.
- **`one-way-door` hook is now stateful** (this PR): the check (`PreToolUse:Write`) gained a session-scoped approval ledger, and a companion `one-way-door-approve.sh` (`PostToolUse:AskUserQuestion`) promotes pending files to approved once the user answers an `AskUserQuestion`. The old stateless check re-blocked the same file on the retry, so its own "ask, then retry" instruction never terminated. The retried write now passes; every other unapproved one-way-door file still blocks. The ledger lives in `~/.claude/hooks/state/one-way-door/` (`<session_id>.pending` / `.approved`), and a new session starts clean.
- **`one-way-door` check gained a false-positive safelist and tighter auth matching** (this PR): the documented script is now the best-of-both version running locally — it early-exits an explicit safelist (test files by convention, `tests/`/`__tests__/`/`fixtures/`/`mocks/` directories, all Markdown, and `*.txt`/`*.rst` under `plans`/`docs`/`notes`/`superpowers`) before any pattern check, and the auth/security patterns are extension-qualified (`security.{ts,js,py,json,rules,yaml,yml}`, `rbac.{ts,js,py,json}`, `permissions.{ts,js,py,json}`) so a file that merely contains a keyword no longer trips. Updated `dev-toolkit/skills/one-way-door/SKILL.md`, `hooks/one-way-door-check.md`, and `docs/one-way-door/index.html` to document both hooks, the safelist, and the new `settings.json` wiring.

## [2.1.0] - 2026-05-12

The security-toolkit supply-chain release. Marketplace bumped 2.0.0 → 2.1.0 to roll up PR #77 (security-toolkit 1.1.0) and the docs-surface follow-up.

### Added

- **security-toolkit plugin v1.2.0 (#77, #80, this PR)**: new `supply-chain-hardening` skill plus a `/security-toolkit:hotpatch` slash command that runs a sandboxed pre-install scan of npm/bun packages (bwrap on Linux, sandbox-exec on macOS). The skill ships install-time cooldown configuration (npm `min-release-age`, bun `[install] minimumReleaseAge`) plus a reference shell script (`scripts/hotpatch.example.sh`) with a `--self-test` mode that verifies against synthetic malicious tarballs in `test-fixtures/`. Defends against the Mini Shai-Hulud-class TanStack supply-chain worm pattern.
- **Docs landing page** at `docs/supply-chain-hardening/index.html` (#80) mirroring the security-checklist template with a red gradient hero, threat-model two-column grid, scan-heuristics table, and `aria-labelledby` / `scope="col"` accessibility additions beyond the cohort baseline.
- **`docs/supply-chain-hardening/og-image.png`** (#80) — 1200×630 OG image matching the security cohort palette.
- **CI hotpatch self-test workflow** (this PR): `.github/workflows/security-toolkit-hotpatch-selftest.yml` runs `bash security-toolkit/scripts/hotpatch.example.sh --self-test` on every PR that touches `security-toolkit/scripts/` or `security-toolkit/test-fixtures/`.

### Changed

- **`security-toolkit/scripts/hotpatch.example.sh` is now cross-platform** (this PR): detects host OS via `uname` and selects a sandbox backend per platform — `bwrap` on Linux, `sandbox-exec` on macOS with a deny-default profile that restricts reads to system dirs + the tarball file, restricts writes to the scan-dir, allows `process-exec` of `/usr/bin/tar` only, and denies network. The Linux path also probes `bwrap` with a no-op `--bind / / -- true` before use; if AppArmor/seccomp policy on the host blocks unprivileged user namespaces (common on GitHub Actions runners and inside Docker containers), the script falls back to an unsandboxed `tar` extract with a loud warning. The static scan still runs identically either way. Falls back to a clearly-flagged unsandboxed extract on platforms with neither backend.
- **`docs/index.html`** (#80): `09 / Security` cluster header `3 Skills` → `4 Skills`; new `supply-chain-hardening` card with the `package-check` lucide icon.
- **`docs/llms.txt`** (this PR): rebuilt from the filesystem — `31 → 53` skills, added "Project templates", "Documents and explainers", and "Workflow patterns (superjawn)" sections that were missing entirely. Closes the count drift noted in #83.
- **`docs/sitemap.xml`** (this PR): regenerated from the filesystem — 6 → 43 URLs, every page under `docs/<slug>/index.html` now listed with current `<lastmod>`. Closes the staleness noted in #82.

### Fixed

- **a11y color-contrast on `docs/persistent-sessions/index.html`** (this PR): three nodes using `text-clay/50` and `text-clay/60` fell below WCAG AA 4.5:1 against the white card background; bumped to the cohort-standard `text-clay/70`. axe-core 4.x scan now reports zero severe and zero minor violations across all 43 docs pages. Closes #81.

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
