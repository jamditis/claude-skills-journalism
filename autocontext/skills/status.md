---
name: autocontext-status
description: Show knowledge stats for the current project
---

Display stats and status for the autocontext in the current project.

## Precondition

Before displaying stats, the script checks if `.autocontext/` exists. If it doesn't, you'll see:

```
Autocontext not initialized for this project.
Run '/autocontext-init' to set up knowledge tracking.
```

Otherwise, the script reads:
- `.autocontext/lessons.json` — active and archived lessons
- `.autocontext/config.json` — project configuration
- `.autocontext/cache/` — any pending lessons

## Status report

The script displays a clean, organized report with the following sections:

### 1. Lessons by category

Breakdown of all lessons (active and tombstoned) by category:

```
Lessons by category:
  bug-fix:          12 active, 3 tombstoned
  architecture:     8 active, 1 tombstoned
  workflow:         15 active, 2 tombstoned
  pattern:          6 active, 0 tombstoned
  gotcha:           9 active, 1 tombstoned
  integration:      4 active, 0 tombstoned
  test-strategy:    5 active, 0 tombstoned

Total: 59 active lessons | 7 tombstoned
```

### 2. Confidence metrics

Average confidence across all active lessons:

```
Confidence metrics:
  Average confidence: 0.72
  High confidence (>= 0.8):  28 lessons
  Medium confidence (0.5-0.8):  26 lessons
  Low confidence (< 0.5):  5 lessons
```

### 3. Most-validated lessons

Top 5 lessons with the highest `validated_count` (most confirmed across sessions):

```
Most-validated lessons (by developer/session confirmations):
  1. [Architecture] "Split domain logic from infrastructure" — validated 34 times
  2. [Workflow] "Always run tests before commit" — validated 28 times
  3. [Bug-fix] "Regex patterns need raw strings" — validated 22 times
  4. [Pattern] "Use dependency injection for testing" — validated 18 times
  5. [Test-strategy] "Write integration tests for API changes" — validated 16 times
```

### 4. Stalest lessons

Top 5 lessons with lowest confidence or oldest `last_validated` timestamp (need attention):

```
Stalest lessons (lowest confidence or oldest validation):
  1. [Workflow] "Use Docker for local dev" — confidence 0.3, last validated 120 days ago
  2. [Integration] "Slack API batch operations" — confidence 0.4, last validated 89 days ago
  3. [Gotcha] "Python timezone handling edge case" — confidence 0.5, last validated 73 days ago
  4. [Architecture] "Consider microservices for X" — confidence 0.4, last validated 95 days ago
  5. [Pattern] "SQL query optimization with indexes" — confidence 0.5, last validated 67 days ago
```

### 5. Lessons by developer

Breakdown showing which developers discovered/contributed lessons:

```
Lessons by creator:
  alice:     18 lessons
  bob:       14 lessons
  claude:    22 lessons
  dave:      5 lessons
```

### 6. Recent lessons

Lessons added in the last 7 days:

```
Added in the last 7 days: 3 lessons
  • [Bug-fix] "Array slice doesn't mutate original" — 2 days ago
  • [Gotcha] "Event listener cleanup in unmount" — 4 days ago
  • [Pattern] "Memoize expensive computations" — 6 days ago
```

If no lessons were added in the last 7 days, that's noted: `No lessons added in the last 7 days.`

### 7. Merge driver status

Shows whether cross-developer sharing is configured:

```
Merge driver status:
  ✓ Configured (git config merge.autocontext-union.driver found)
```

Or if not configured:

```
Merge driver status:
  ✗ Not configured (single-developer mode)
  To enable, run: /autocontext-init
```

### 8. Pending lessons

Shows if there are lessons awaiting curation:

```
Pending lessons:
  3 lessons in .autocontext/cache/pending-lessons.json (from ask_before_persist mode)
  Run '/autocontext-review' to approve or reject.
```

Or if none:

```
Pending lessons:
  None
```

## Display format

The report uses:
- Clear section headers
- Indented, aligned data
- Counts and percentages where relevant
- Plain language (no technical jargon)
- Readable line breaks between sections

## No interaction required

This skill is read-only. No AskUserQuestion is used. The report is informational, designed to help you understand the current state of your project's knowledge base.

## Next steps

Based on the status output, you might:
- Run `/autocontext-review` if there are lessons with low confidence or pending approval
- Check stalest lessons to see if they're still valid or should be updated
- Share the status report with team members if using cross-developer sharing
