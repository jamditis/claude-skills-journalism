---
name: claude-md-updater
description: Scans the session for lessons and workflows, then proposes scoped CLAUDE.md edits. Use for save this lesson or add to context.
---

# CLAUDE.md auto-updater

Analyze the current conversation to identify information worth persisting in CLAUDE.md for future sessions, then propose the edits for approval before writing anything.

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

2. **Categorize findings.** Only durable facts belong in CLAUDE.md:
   - Hard-won lessons go to the "Hard-won lessons" section
   - Infrastructure changes update the relevant section
   - New workflows go to the appropriate section
   - Transient, session-specific notes do **not** go in CLAUDE.md (see "What not to persist")

3. **Build the exact diff.** Produce a unified diff against the current CLAUDE.md showing the precise lines and sections to be added or changed. This diff is what the user approves, not a summary of it.

4. **Present the diff for approval** and write nothing until the user approves.

## Output format

Show the exact patch first, then a short summary grouped by category:

````
## Proposed CLAUDE.md updates

```diff
--- a/CLAUDE.md
+++ b/CLAUDE.md
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

CLAUDE.md is team-shared (checked into git) and advisory: it loads into every session, so it is for durable, infrequently-changing facts, not a running log. Per the project-memory skill, keep these **out** of CLAUDE.md:

- Transient "what we did today" session summaries
- Anything that changes frequently
- Things Claude learns over time through corrections

Route those to **auto memory** (`~/.claude/projects/<project>/memory/`, which Claude maintains on its own) or to a gitignored `CLAUDE.local.md` for personal notes. Putting them in CLAUDE.md bloats shared context and loads stale per-session facts into future sessions.

## Rules

1. **Never add sensitive values.** Reference where a credential is stored; never include the actual token.
2. **Keep it concise.** CLAUDE.md should stay scannable; target under 200 lines.
3. **Avoid duplication.** Check whether the information already exists before adding it.
4. **Match the existing style.** Follow the tone and format of the current file.
5. **Durable facts only.** Persist hard-won lessons, infrastructure facts, and workflows. Session-specific notes belong in auto memory or a gitignored `CLAUDE.local.md`, never the committed CLAUDE.md.
