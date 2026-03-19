# Copilot review instructions

## Project

Claude skills for journalism — a collection of Claude Code skills for journalists, researchers, and media professionals. Static site at skills.amditis.tech via GitHub Pages from `docs/`.

## Style rules

- Always use sentence case. Never Title Case.
- No emojis in source code or skill content.
- Flag banned words: "comprehensive", "robust", "leveraging", "seamlessly", "innovative", "cutting-edge", "holistic", "synergy", "ecosystem", "paradigm", "empower", "transformative", "sophisticated", "state-of-the-art".
- Skill descriptions should be terse and actionable, not padded with filler.
- Never include AI attribution ("Generated with Claude Code", etc.) in PRs, commits, code, or docs.

## Skill format

Each skill must have YAML frontmatter:
```yaml
---
name: skill-name
description: When this skill activates and what it does
---
```

Flag skills missing frontmatter or with vague descriptions.

## Website (docs/)

- Zero-build static HTML with Tailwind CDN, Lucide icons, Google Fonts.
- Uses the Amditis V2 light editorial theme (canvas #ede6d4, ink #121212, accent #3d4b40).
- Every HTML page needs an SVG favicon and full OG/Twitter meta tags.
- External links need `rel="noopener noreferrer"`.

## Hooks

All hooks are non-blocking warnings. They follow the pattern:
- Event-based triggers (PreToolUse, PostToolUse, Stop, SessionStart, UserPromptSubmit)
- Clear, specific detection criteria
- Actionable output (not just "be careful")

Flag hooks that silently suppress errors or block without explanation.

## Security

- Skill content should not include hardcoded credentials, API keys, or tokens.
- Web scraping skills must respect robots.txt and rate limits.
- FOIA/records skills must include privacy considerations.
