---
name: project-memory
description: Generates project instruction files that transfer institutional knowledge. Use when setting up projects or onboarding.
---

# Project memory generator

Create a project instruction file that transfers institutional knowledge, not
obvious information. Write for a capable colleague who needs this project's
specific commands, constraints, and failure modes.

## Choose the canonical instruction file

Resolve the target before writing:

1. If `AGENTS.md` exists, update it.
2. If only `CLAUDE.md` exists, update it.
3. If both exist and one imports the other, edit the imported canonical file.
4. If neither exists, create `AGENTS.md`. In Claude Code, also create a
   one-line `CLAUDE.md` that imports it with `@AGENTS.md`.

Do not create competing copies of the same guidance. Keep nested instruction
files only when a subdirectory needs narrower rules than its parent.

## Project instructions are advisory

A project instruction file gives standing context to the active client. It does
not enforce a rule by itself.

| Mechanism | Use for | Behavior |
|---|---|---|
| Project instruction file | Standing facts, commands, conventions, and boundaries | Advisory context |
| Skills | Multi-step procedures and on-demand workflows | Loaded when relevant |
| Client enforcement | Actions that must block or run every time | Client-specific and not portable unless mapped and tested |

Do not use a client hook as load-bearing shared behavior. If a rule must work in
both Claude Code and Codex, state the rule in the project instruction file and
document any optional client enforcement separately.

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

## Anti-patterns

1. **Over-specified instructions.** Important rules disappear inside generic
   advice.
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

## Templates

Templates are in the `templates/` directory:

| Template | Use for |
|---|---|
| `editorial-tool.md` | Newsroom tools, fact-checkers, and research assistants |
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
