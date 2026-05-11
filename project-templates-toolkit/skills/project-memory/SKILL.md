---
name: project-memory
description: Generate CLAUDE.md project memory files that transfer institutional knowledge, not obvious information. Use when setting up new journalism projects, onboarding collaborators, or documenting project-specific quirks. Includes templates for editorial tools, event websites, publications, research projects, content pipelines, and digital archives.
---

# Project memory generator

Create CLAUDE.md files that transfer institutional knowledge, not obvious information. Think like a senior journalist onboarding a competent colleague — you don't explain how journalism works, you explain YOUR project's quirks.

## CLAUDE.md is advisory, not enforced

Anthropic is explicit on this point: CLAUDE.md content is delivered as a user message after the system prompt. Claude reads it and tries to follow it, but there's no guarantee of strict compliance — especially with vague or conflicting instructions. Source: https://code.claude.com/docs/en/memory

This affects how you write a CLAUDE.md and what you put elsewhere:

| Mechanism | Use for | Source-of-truth |
|---|---|---|
| **CLAUDE.md** | Standing facts, conventions, "always do X" rules | Advisory |
| **Skills** | Multi-step procedures, on-demand workflows | Loaded when invoked |
| **Hooks** | Actions that must happen every time, no exceptions | Deterministic — runs as a shell command (e.g., `hooks/one-way-door-check.md`) or as a prompt the harness enforces (e.g., `hooks/enforce-test-first.md`) |

If an instruction is "block writes to `published/`" or "run accessibility check before commit," that belongs in a hook, not CLAUDE.md. If it's "fact-check workflow" or "FOIA-letter drafting," that's a skill. CLAUDE.md is the place for things Claude must hold in every session.

## What belongs in CLAUDE.md

Anthropic publishes an explicit include/exclude table for what makes an effective CLAUDE.md. Source: https://code.claude.com/docs/en/best-practices

| ✅ Include | ❌ Exclude |
|---|---|
| Bash commands Claude can't guess | Anything Claude can figure out by reading code |
| Code style rules that differ from defaults | Standard language conventions Claude already knows |
| Testing instructions and preferred test runners | Detailed API documentation (link to docs instead) |
| Repository etiquette (branch naming, PR conventions) | Information that changes frequently |
| Architectural decisions specific to your project | Long explanations or tutorials |
| Developer environment quirks (required env vars) | File-by-file descriptions of the codebase |
| Common gotchas or non-obvious behaviors | Self-evident practices like "write clean code" |

For journalism projects, translate to:

- **Include:** AP-style preferences that override defaults, "always cite source URLs," byline policy, embargo handling, source-protection invariants, CMS quirks (e.g., "story slugs must be unique across ALL desks, not just metro").
- **Exclude:** "We verify facts before publishing" (every journalist knows this), "use AP Style" without specifics (every journalism stack does this), framework documentation, generic git commands.

## The deletion test

For every line you write, ask: "Would removing this cause Claude to make mistakes?" If not, cut it.

## Size guidance: target under 200 lines

Anthropic's explicit guidance as of 2026: target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence. Bloated CLAUDE.md files cause Claude to ignore the actual rules. Source: https://code.claude.com/docs/en/best-practices

Going over 200 lines is a signal to use one of these instead:

- **`.claude/rules/` with `paths:` frontmatter** — file-pattern-scoped rules that load only when Claude works with matching files. Replaces `@import` chains as the size-management mechanism. (Note: `@imports` no longer help with context size — Anthropic explicitly notes that imports load fully at launch.)
- **Skills** — for multi-step procedures that don't need to be in every session.
- **Hooks** — for deterministic enforcement.

## Where to put CLAUDE.md files

CLAUDE.md location precedence (more specific wins). Source: https://code.claude.com/docs/en/memory

| Scope | Location | Use case |
|---|---|---|
| **Managed policy** | Linux/WSL: `/etc/claude-code/CLAUDE.md`<br/>macOS: `/Library/Application Support/ClaudeCode/CLAUDE.md`<br/>Windows: `C:\Program Files\ClaudeCode\CLAUDE.md` | Org-wide standards (IT/DevOps managed; cannot be excluded by individual settings) |
| **Project** | `./CLAUDE.md` OR `./.claude/CLAUDE.md` | Team-shared instructions (check into git) |
| **User** | `~/.claude/CLAUDE.md` | Personal preferences across all projects |
| **Local** | `./CLAUDE.local.md` | Personal project-specific notes (add to `.gitignore`) |

The `./.claude/CLAUDE.md` location and managed-policy tier are 2026 additions to Anthropic's documented locations. Templates that say "put this at project root" should mention `./.claude/CLAUDE.md` as an equally valid location.

## AGENTS.md interop

If your repo already has `AGENTS.md` for other coding agents (Cursor, Codex, etc.), don't duplicate the content. Anthropic's recommended pattern is `@AGENTS.md` import (or symlink) with Claude-specific overrides appended:

```markdown
@AGENTS.md

## Claude Code
- Use plan mode for changes under `src/billing/`.
```

For journalism teams using multiple agents, this matters — shared editorial standards (AP-style preferences, source-handling invariants, fact-check protocols) belong to the org, not one agent.

## Anti-patterns to warn about

Anthropic now names these explicitly. Source: https://code.claude.com/docs/en/best-practices and https://code.claude.com/docs/en/memory

1. **The over-specified CLAUDE.md.** Bloat causes Claude to ignore real rules. If Claude keeps doing something despite a CLAUDE.md rule, the file is probably too long and the rule is getting lost.
2. **Conflicting instructions across nested CLAUDE.md files.** Claude picks one arbitrarily. Review periodically to remove outdated rules.
3. **Hand-coded standard conventions Claude already knows.** "Use proper indentation," "write clean code" — delete.
4. **Detailed API docs / file-by-file descriptions / info that changes frequently.** Link to the canonical source instead.
5. **Secrets in CLAUDE.md.** It's checked into git. Use `CLAUDE.local.md` (gitignored) for sandbox URLs, test credentials, personal overrides.

## Minimum-viable CLAUDE.md (~6 lines)

Anthropic ships this as the canonical starter. Templates should default to something this short and grow only as needed:

```markdown
# Code style
- Use ES modules (import/export) syntax, not CommonJS (require)
- Destructure imports when possible

# Workflow
- Be sure to typecheck when you're done making a series of code changes
- Prefer running single tests, and not the whole test suite, for performance
```

Each of the 6 journalism templates ships a sub-30-line "starter" variant alongside the fuller version. Adopt incrementally.

## Auto memory is separate from CLAUDE.md

As of Claude Code v2.1.59+, there's a second memory mechanism alongside CLAUDE.md: **auto memory**, where Claude writes notes to itself in `~/.claude/projects/<project>/memory/` based on your corrections. The first 200 lines of that directory's `MEMORY.md` are loaded into every session. Source: https://code.claude.com/docs/en/memory

Practical implication for templates: don't ask the user to manually write down "things Claude learns over time" — that's auto memory's job now. CLAUDE.md is for facts you write up front; auto memory is for things Claude notices.

## Voice guidelines

- Direct and terse
- Like notes you'd leave for yourself
- No marketing language
- No "Welcome to..." introductions
- No "This project is..." padding

## Example: good vs bad

**Bad (too verbose, obvious):**
```markdown
# CLAUDE.md

## Overview
Welcome to our newsroom's story tracking system! This is a
web application built with React and Node.js that helps
editors and reporters collaborate on stories.

## Getting started
First, make sure you have Node.js installed. Then:
npm install
npm start
```

**Good (institutional knowledge only):**
```markdown
# CLAUDE.md

## Overview
Story tracker for metro desk. React + Supabase.

## Gotchas
- Story slugs must be unique across ALL desks, not just metro
- "Hold" status doesn't stop the autopublish cron — use "Kill"
- Reporter dropdown caches for 1 hour; new hires won't appear

## Commands
npm run sync-ap  # Pull latest from AP, runs automatically at :15

## Credentials
Supabase key in 1Password "Metro Desk" vault, not .env
```

## Journalism-specific templates

Templates are in the `templates/` directory:

| Template | Use for |
|----------|---------|
| `editorial-tool.md` | Newsroom tools, fact-checkers, AI assistants |
| `event-website.md` | Conferences, workshops, campaign sites |
| `publication.md` | Newsletters, podcasts, ongoing content series |
| `research-project.md` | Investigations, data journalism with defined scope |
| `content-pipeline.md` | CMS workflows, publishing automation |
| `digital-archive.md` | Historical collections, document repositories |

### Template selection guide

```
What are you building?
├── Tool for the newsroom → editorial-tool.md
├── Site for an event → event-website.md
├── Recurring content series → publication.md
├── One-time investigation → research-project.md
├── Publishing automation → content-pipeline.md
└── Archive/preservation → digital-archive.md
```

## How to use templates

1. Copy the appropriate template to `./CLAUDE.md` OR `./.claude/CLAUDE.md` at your project root
2. Fill in the bracketed placeholders with YOUR specifics
3. Delete any sections that don't apply
4. If your project uses other agents (Cursor, Codex), add `@AGENTS.md` at the top instead of duplicating shared content
5. Add project-specific gotchas as you discover them — but stay under 200 lines
6. Move multi-step procedures to skills, deterministic enforcement to hooks

## Last currency sweep

2026-05-09. Sources verified: code.claude.com/docs/en/memory, code.claude.com/docs/en/best-practices.

---

*The best CLAUDE.md files are written by people who've been burned by the quirks they're documenting.*
