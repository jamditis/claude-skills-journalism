---
name: claude-md-updater
description: Use this skill when the user asks to update CLAUDE.md, save a lesson, or persist something from the current session — phrases like "update claude.md", "what should we remember", "save this lesson", "add to context", or "/remember". Scans the conversation for hard-won lessons, new file paths, infrastructure changes, and new workflows, then proposes scoped edits to the project's CLAUDE.md for approval before writing.
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

2. **Categorize findings**:
   - Hard-won lessons go to the "Hard-won lessons" section
   - Session-specific work goes to the "Session notes" section
   - Infrastructure changes update the relevant section
   - New workflows go to the appropriate section

3. **Generate a diff** showing the proposed changes.

4. **Present for approval** before making any change.

## Output format

Present findings as:

```
## Proposed CLAUDE.md updates

### Hard-won lessons (if any)
[new lesson to add]

### Session notes
[summary of today's work]

### Infrastructure updates (if any)
[changes to services, endpoints, and the like]

---
Apply these changes? (the exact edits are shown first)
```

## Rules

1. **Never add sensitive values.** Reference where a credential is stored; never include the actual token.
2. **Keep it concise.** CLAUDE.md should stay scannable.
3. **Avoid duplication.** Check whether the information already exists before adding it.
4. **Match the existing style.** Follow the tone and format of the current file.
5. **Session notes expire.** Keep only recent session notes (the last ~5 sessions).
