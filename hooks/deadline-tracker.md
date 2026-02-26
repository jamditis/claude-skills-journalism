---
name: deadline-tracker
description: Surface upcoming deadlines from editorial workflow at session start
event: SessionStart
---

# Deadline tracker hook

At the start of a session, check for and surface upcoming deadlines from editorial workflow files.

## When this hook fires

- At `SessionStart` event
- When working in a project with editorial workflow files
- When deadline tracking files exist in the project

## What to look for

### Editorial workflow files

Check for files that might contain deadlines:

```
editorial-calendar.md
deadlines.md
assignments.md
story-tracker.md
.claude/deadlines.json
```

### Deadline patterns in content

Look for patterns like:

```markdown
**Deadline:** January 30, 2026
**Due:** 5pm Friday
**Publish date:** Feb 1
- [ ] Due: [date]
```

### Time-sensitive items

```markdown
- FOIA response due: [date]
- Embargo lifts: [date/time]
- Event date: [date]
- Source callback by: [date]
```

## Output format

At session start, if deadlines found:

```
📅 Upcoming deadlines:

TODAY:
- [Story slug]: Draft due 5pm

THIS WEEK:
- [Story slug]: Publish Wednesday
- [FOIA request]: Response deadline Friday

UPCOMING:
- [Event]: Feb 15
- [Embargo]: Lifts Feb 10 at 12:01am ET

Would you like to focus on any of these?
```

## Deadline file format

If project uses a dedicated deadline file, suggested format:

```yaml
# deadlines.yaml
deadlines:
  - slug: city-budget-story
    type: draft
    due: 2026-01-30T17:00:00
    assignee: reporter-name

  - slug: council-meeting
    type: publish
    due: 2026-02-01T06:00:00

  - slug: foia-police-records
    type: response-due
    due: 2026-02-05
    notes: "20-day deadline from Jan 16 request"
```

## Integration with editorial-workflow skill

This hook complements the editorial-workflow skill by:

1. Reading deadline data the skill helps create
2. Surfacing time-sensitive items proactively
3. Helping journalists prioritize session work

## Silence conditions

Don't show deadline reminder if:

- No deadline files found in project
- All deadlines are more than 2 weeks out
- User is clearly working on something else

## Customization

Projects can configure deadline tracking in CLAUDE.md:

```markdown
## Deadline tracking

Deadline file: `editorial/deadlines.yaml`
Alert window: 7 days
Exclude types: [meeting, call]
```

## Non-blocking

This is informational. The hook surfaces deadlines but doesn't prevent any actions. Journalists manage their own time.

## Privacy note

Deadline information may be sensitive (story slugs, source names). This hook only reads local files—no external transmission.
