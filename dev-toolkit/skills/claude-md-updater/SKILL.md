---
name: claude-md-updater
description: Scans the session for durable lessons and workflows, then proposes scoped project instruction updates. Use for save this lesson or add to context.
---

# Project instruction updater

Analyze the current conversation to identify information worth persisting in the project's instruction file, then propose the edits for approval before writing anything.

Resolve the target before drafting:

1. If `AGENTS.md` exists, update it. In Claude Code, if there is no `CLAUDE.md`, also propose a one-line `CLAUDE.md` import of `@AGENTS.md`. Claude Code loads `CLAUDE.md`, not `AGENTS.md`.
2. If only `CLAUDE.md` exists, update it.
3. If both exist and either imports the other, update the imported canonical file.
4. If neither exists, create `AGENTS.md`. In Claude Code, also propose the one-line `CLAUDE.md` import.

## What to look for

### 1. Hard-won lessons
- Debugging sessions that revealed non-obvious causes
- Workarounds for platform or tool limitations
- Anti-patterns discovered through failure
- "The real problem was..." moments

### 2. New infrastructure
- New services deployed
- New endpoints or URLs
- New file paths or directories
- New credentials or tokens (reference only, never the values)

### 3. New workflows
- Commands that solve recurring problems
- Multi-step processes that work well
- Integration patterns between systems

### 4. Updated information
- Changed ports, IPs, or URLs
- New capabilities added to existing systems
- Deprecated or removed features

## Analysis process

1. **Scan the conversation** for keywords:
   - "fixed", "solved", "the issue was", "turns out"
   - "deployed", "set up", "configured", "installed"
   - "new endpoint", "new service", "new path"
   - "doesn't work", "limitation", "workaround"

2. **Categorize findings.** Only durable facts belong in the project instruction file:
   - Hard-won lessons go to the "Hard-won lessons" section
   - Infrastructure changes update the relevant section
   - New workflows go to the appropriate section
   - Transient, session-specific notes do **not** go in the project instruction file (see "What not to persist")

3. **Build the exact diff.** Produce a unified diff against the resolved instruction file showing the precise lines and sections to add or change. This diff is what the user approves, not a summary of it.

4. **Present the diff for approval** and write nothing until the user approves.

## Output format

Show the exact patch first, then a short summary grouped by category:

````
## Proposed project instruction updates

```diff
--- a/AGENTS.md
+++ b/AGENTS.md
@@ section being changed @@
 existing context line
+new durable lesson, infra fact, or workflow
```

Summary of the diff above:
- Hard-won lessons: [one line, if any]
- Infrastructure updates: [one line, if any]
- New workflows: [one line, if any]

Apply this diff? Nothing is written until you approve.
````

## What not to persist

The project instruction file is team-shared, checked into git, and loaded into agent sessions. Use it for durable, infrequently changing facts, not a running log. Per the project-memory skill, keep these items out:

- Transient "what we did today" session summaries
- Anything that changes frequently
- Things the client learns over time through corrections

Route those to the client's memory feature (in Claude Code, auto memory at
`~/.claude/projects/<project>/memory/`) or to a gitignored local notes file (in
Claude Code, `CLAUDE.local.md`). Putting them in shared project instructions
bloats context and loads stale session facts into future sessions.

## Rules

1. **Never add sensitive values.** Reference where a credential is stored; never include the actual token.
2. **Keep it concise.** The project instruction file should stay scannable; target under 200 lines.
3. **Avoid duplication.** Check whether the information already exists before adding it.
4. **Match the existing style.** Follow the tone and format of the current file.
5. **Durable facts only.** Persist hard-won lessons, infrastructure facts, and workflows. Session-specific notes belong in client memory or a gitignored local notes file, never the committed project instruction file.
