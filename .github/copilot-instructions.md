# Copilot review instructions — claude-skills-journalism

Project context, skill format, hook conventions, and style rules live in [CLAUDE.md](../CLAUDE.md). Read that for everything Copilot needs to understand the repo. This file lists the *journalism-domain* guardrails that benefit from explicit reviewer attention.

## What to flag in reviews

1. **No hardcoded credentials in skill content.** API keys, tokens, OAuth secrets, or any credential value must never appear in skill markdown, templates, or example code. Reference paths (e.g., `pass show claude/services/X`) and env-var names are fine; values are not.

2. **Web scraping skills must respect robots.txt and rate limits.** Any skill in `web-scraping/`, `digital-archive/`, `web-archiving/`, or `page-monitoring/` that fetches third-party content must document robots.txt compliance and apply rate limiting. Flag scraping examples that don't.

3. **FOIA/records skills must include privacy considerations.** Skills under `foia-requests/` or that handle personally-identifying information from public records must call out PII redaction, victim/witness identifier protection, and the distinction between *public records* and *public-interest publication*.

4. **Hooks must be non-blocking warnings, not silent failures.** All hooks in `hooks/` follow the "warn but don't block" pattern. Flag any hook that silently suppresses errors, exits with a blocking status without explanation, or modifies behavior without surfacing what it did.
