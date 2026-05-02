# Copilot review instructions — claude-skills-journalism

Project context, skill format, and hook conventions live in [CLAUDE.md](../CLAUDE.md). Both this file and CLAUDE.md are read by Copilot code review (cap ~4,000 chars each). This file lists the rules worth named attention on every PR.

## Global rules to flag

These are Joe's user-level conventions. They live in `~/.claude/CLAUDE.md`, which Copilot's PR review bot does *not* read — so they're restated here so the bot enforces them on this repo's PRs.

- **Sentence case** in headings, UI text, and identifiers. Title Case is a regression.
- **No emojis** in source code, log messages, comments, commits, PR bodies, skill content, or any output. Plain text only.
- **No AI attribution.** Never include "Generated with Claude Code", `Co-Authored-By: Claude` trailers, or any AI/model/company attribution in PRs, commits, code, skill markdown, or any committed file.
- **Banned words** (delete or replace): *comprehensive, sophisticated, robust, transformative, leveraging, seamlessly, innovative, cutting-edge, state-of-the-art, holistic, synergy, ecosystem, paradigm, empower*. Suggest alternatives that say what's actually meant. Skill descriptions should be terse and actionable, not padded.
- **Every HTML page must have an SVG favicon and full OG/Twitter meta tags.** (This repo's `docs/` is a static site at skills.amditis.tech.)

## Project-specific bug classes to flag

1. **No hardcoded credentials in skill content.** API keys, tokens, OAuth secrets, or any credential value must never appear in skill markdown, templates, or example code. Reference paths (e.g., `pass show claude/services/X`) and env-var names are fine; values are not.

2. **Web scraping skills must respect robots.txt and rate limits.** Any skill in `web-scraping/`, `digital-archive/`, `web-archiving/`, or `page-monitoring/` that fetches third-party content must document robots.txt compliance and apply rate limiting. Flag scraping examples that don't.

3. **FOIA/records skills must include privacy considerations.** Skills under `foia-requests/` or that handle personally-identifying information from public records must call out PII redaction, victim/witness identifier protection, and the distinction between *public records* and *public-interest publication*.

4. **Hooks must be non-blocking warnings, not silent failures.** All hooks in `hooks/` follow the "warn but don't block" pattern. Flag any hook that silently suppresses errors, exits with a blocking status without explanation, or modifies behavior without surfacing what it did.
