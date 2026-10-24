---
name: project-memory
description: Generates project instruction files (AGENTS.md or CLAUDE.md) that transfer institutional knowledge. Use when setting up projects or onboarding. For lessons from a finished project or investigation, use project-retrospective.
---

# Project memory generator

Create a project instruction file that transfers institutional knowledge, not
obvious information. Think like a senior journalist onboarding a competent
colleague. Do not explain how journalism works; explain this project's quirks.

## Choose the canonical instruction file

Resolve the target before writing:

1. If `AGENTS.md` exists, update it. If no `CLAUDE.md` exists, then
   in Claude Code, also create a one-line
   `CLAUDE.md` that imports it with `@AGENTS.md`. Claude Code loads
   `CLAUDE.md`, not `AGENTS.md`.
2. If only `CLAUDE.md` exists, update it.
3. If both exist and one imports the other, edit the imported canonical file.
4. If neither exists, create `AGENTS.md`. In Claude Code, also create the
   same one-line `CLAUDE.md` import.

Do not create competing copies of the same guidance. Keep nested instruction
files only when a subdirectory needs narrower rules than its parent.

## Project instructions are advisory

A project instruction file gives standing context to the active client. It does
not enforce a rule by itself.

In Claude Code, `CLAUDE.md` content is delivered as user context after the
system prompt. Claude reads it and tries to follow it, but the file does not
guarantee strict compliance with vague or conflicting instructions. Source:
https://code.claude.com/docs/en/memory

| Mechanism | Use for | Behavior |
|---|---|---|
| Project instruction file | Standing facts, commands, conventions, and boundaries | Advisory context |
| Skills | Multi-step procedures and on-demand workflows | Loaded when relevant |
| Client enforcement | Actions that must block or run every time | Deterministic only when the client blocks, for example, a Claude Code hook that exits 2 or returns a PreToolUse deny. A prompt hook only adds a reminder |

Do not use a client hook as load-bearing shared behavior. If a rule must work in
both Claude Code and Codex, state the rule in the project instruction file and
document any optional client enforcement separately.

If an instruction is "block writes to `published/`" or "run an accessibility
check before commit," use client enforcement. If it is a "fact-check workflow"
or "FOIA-letter drafting," use a skill. Keep standing project facts and rules
in the project instruction file.

Claude Code guidance for effective instruction files includes an explicit
include/exclude list. Source: https://code.claude.com/docs/en/best-practices

## What belongs in the file

Include information an agent cannot infer reliably from the repository:

- Project-specific build, test, lint, and validation commands.
- Code or editorial rules that differ from common defaults.
- Repository etiquette, branch conventions, and approval boundaries.
- Architecture decisions and non-obvious dependencies.
- Environment requirements, named variables, and credential pointers without
  secret values.
- Common failure modes and the smallest known recovery steps.
- Source-handling, publication, privacy, or legal constraints specific to the
  project.

Exclude information the agent can discover cheaply:

- Standard language conventions and generic advice.
- Detailed API documentation that has a canonical source.
- File-by-file repository descriptions.
- Session logs, status updates, and facts that change often.
- Long tutorials or narrative history.
- Credentials, tokens, private values, or personal data.

For journalism projects:

- Include AP-style preferences that override defaults, source-citation rules,
  byline policy, embargo handling, source-protection invariants, and CMS quirks
  (for example, "story slugs must be unique across all desks, not just metro").
- Exclude "verify facts before publishing" and "use AP Style" without
  specifics. Every newsroom already knows both.

For every line, ask: Would removing this make a capable agent more likely to
make a project-specific mistake? If not, remove it.

## Keep the file small and scoped

Use short sections and direct instructions. Treat 200 lines as a review
threshold, not a target. When the file grows:

- Move multi-step procedures into skills.
- Link to canonical reference documentation.
- Put narrow directory rules in a nested instruction file.
- Move transient notes into the client's memory feature or a gitignored local
  notes file.
- Remove duplicated and superseded rules.

If both supported clients are used, keep shared guidance in `AGENTS.md` and
let `CLAUDE.md` import it. Add client-specific guidance only when the behavior
cannot be expressed portably, and label the client.

Client-specific scoping options:

- Claude Code: `.claude/rules/` files with `paths:` frontmatter load only when
  the agent works on matching files. An `@import` loads in full at launch, so
  it does not reduce context size.
- Codex: a nested `AGENTS.md` applies to its directory and below.

### Client-specific locations

In Claude Code, more specific locations take precedence. Source:
https://code.claude.com/docs/en/memory

| Scope | Claude Code location | Use case |
|---|---|---|
| Managed policy | Linux/WSL: `/etc/claude-code/CLAUDE.md`<br>macOS: `/Library/Application Support/ClaudeCode/CLAUDE.md`<br>Windows: `C:\Program Files\ClaudeCode\CLAUDE.md` | Organization standards that individual settings cannot exclude |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team-shared instructions checked into version control |
| User | `~/.claude/CLAUDE.md` | Personal preferences across projects |
| Local | `./CLAUDE.local.md` | Gitignored personal project notes |

In Codex, instructions load from global scope through the current working
directory. Later directories override earlier ones, and `AGENTS.override.md`
takes precedence over `AGENTS.md` in the same directory. Source:
https://developers.openai.com/codex/guides/agents-md

| Scope | Codex location | Use case |
|---|---|---|
| User | `~/.codex/AGENTS.md` | Personal instructions across projects |
| Project and nested directories | `AGENTS.md` from the repository root through the current working directory | Shared rules with narrower directory scope |
| Override | `AGENTS.override.md` | Replace `AGENTS.md` for the same directory when a temporary or stronger override is required |

For journalism teams that use multiple agents, keep shared editorial standards,
source-handling invariants, and fact-check protocols in the canonical shared
file. Those rules belong to the organization, not one client.

## Anti-patterns

1. **Over-specified instructions.** Important rules disappear inside generic
   advice. In Claude Code, if Claude keeps ignoring a rule, the file is probably
   too long and the rule is getting lost.
2. **Conflicting nested files.** A broad rule and a narrow rule disagree without
   stating which scope wins.
3. **Duplicated client files.** Two copies drift and give different guidance.
4. **Stale operational state.** Ports, owners, or current status remain after
   reality changes.
5. **Secrets in instructions.** The file is checked into version control.

## Voice

- Use short, direct sentences.
- Name exact commands and paths only when the project requires them.
- State who can authorize consequential work.
- Remove welcome text, marketing language, and generic reminders.
- Use sentence-case headings.

## Auto memory is separate from project instructions

In Claude Code v2.1.59 and later, auto memory stores notes under
`~/.claude/projects/<project>/memory/`. The first 200 lines of `MEMORY.md` load
into each session. Source: https://code.claude.com/docs/en/memory

Do not ask the user to write down things Claude learns through corrections.
Auto memory handles those notes. Project instructions hold durable facts that
the team writes and reviews.

## Example: good vs. bad

Bad, because it explains obvious setup and gives no institutional knowledge:

```markdown
# Project instructions

## Overview

Welcome to our newsroom's story tracking system. This React and Node.js app
helps editors and reporters collaborate on stories.

## Getting started

npm install
npm start
```

Good, because it records only project-specific behavior:

```markdown
# Project instructions

## Overview

Story tracker for the metro desk. React + Supabase.

## Gotchas

- Story slugs must be unique across all desks, not only metro.
- "Hold" does not stop the autopublish cron. Use "Kill."
- The reporter dropdown caches for one hour. New hires do not appear sooner.

## Commands

npm run sync-ap  # Pull latest from AP. Runs automatically at :15.

## Credentials

The Supabase key is in the 1Password "Metro Desk" vault, not `.env`.
```

## Templates

Templates are in the `templates/` directory:

| Template | Use for |
|---|---|
| `editorial-tool.md` | Newsroom tools, fact-checkers, and AI assistants |
| `event-website.md` | Conferences, workshops, and campaign sites |
| `publication.md` | Newsletters, podcasts, and continuing publications |
| `research-project.md` | Investigations and scoped data research |
| `content-pipeline.md` | CMS workflows and publishing automation |
| `digital-archive.md` | Historical collections and document repositories |

## Workflow

1. Resolve the canonical instruction file with the rules above.
2. Read the existing file and every parent or nested instruction file that
   applies to the target scope.
3. Select the closest template. Copy only the sections the project needs.
4. Preserve existing guidance and ordering unless the user asks for a rewrite.
5. Replace placeholders with verified project facts. Do not invent commands,
   owners, paths, or service state.
6. Keep separately scoped rules in their applicable directories.
7. Review the final file for duplicates, conflicts, stale facts, and secrets.
8. If this created `AGENTS.md` in Claude Code, create the one-line import file
   described above.

## Minimum starter

```markdown
# Project instructions

## Commands

- Test: [exact command]
- Lint: [exact command]

## Project rules

- [Non-obvious rule that changes how work is done.]
- [Approval or safety boundary.]

## Known failure modes

- [Symptom]: [Cause and verified recovery.]
```

Start small. Add a rule only after the project demonstrates that agents need it.

## Reference files

Read [Pinned repository ledger](references/repo-ledger.md) when several agents, runtimes, or people coordinate in one repository.

## Last currency sweep

2026-05-09. Sources verified: https://code.claude.com/docs/en/memory and
https://code.claude.com/docs/en/best-practices. Codex instruction scoping was
checked against official OpenAI documentation on 2026-10-23.
