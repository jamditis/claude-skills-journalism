# dev-toolkit

Thirteen development-focused skills for journalists, researchers, and small newsroom dev teams.

## Skills in this plugin

| Skill | What it covers |
|---|---|
| accessibility-compliance | WCAG 2.2 baseline, alt text, focus management, motion preferences |
| claude-md-updater | Detect session lessons, new paths, infra changes, and workflows and propose scoped CLAUDE.md edits |
| context-engineering-fundamentals | Attention budget, lost-in-middle recall, context degradation patterns, and mitigations for long sessions |
| director | Explicit top-tier direction through the lower-tier agents and models configured in CLAUDE.md |
| electron-dev | Electron security model (contextIsolation, sandbox), IPC patterns, packaging |
| mobile-debugging | Eruda, vConsole, Chrome DevTools on Android, Safari Web Inspector for iOS |
| one-way-door | Block irreversible architectural decisions during planning |
| python-pipeline | Data pipeline patterns (pandas, polars, DuckDB, asyncio) |
| test-first-bugs | TDD workflow for bug fixes, failing test before fix |
| vibe-coding | AI-assisted development workflow (Claude Code, Cursor, Aider, Continue) |
| web-scraping | Ethical scraping patterns (Playwright, robots.txt, anti-bot, terms-of-service) |
| web-ui-best-practices | Container queries, `:has()`, view transitions, scroll-driven animations |
| zero-build-frontend | ESM import maps, htmx, Alpine.js, no-build deployment |

## Installation

```
/plugin marketplace add jamditis/claude-skills-journalism
/plugin install dev-toolkit@claude-skills-journalism
```

The plugin form invokes the skill as `/dev-toolkit:director`. For the literal
`/director` command, copy or symlink the standalone skill into the personal
Claude Code skills directory:

```sh
mkdir -p ~/.claude/skills
cp -r dev-toolkit/skills/director ~/.claude/skills/
```

## See also

- [`journalism-core`](../journalism-core/README.md), 15 skills for reporting, verification, publishing
- [`research-toolkit`](../research-toolkit/README.md), 6 skills for research, archives, academic workflows
