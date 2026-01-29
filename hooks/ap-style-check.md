---
name: ap-style-check
description: Flag common AP Style violations in written content
event: PostToolUse
tools: [Write, Edit]
---

# AP Style check hook

After writing or editing content, scan for common AP Style violations and flag them.

## When this hook fires

- After `Write` tool creates or overwrites a file
- After `Edit` tool modifies a file
- Only for text files likely to contain journalism content (.md, .txt, .html, prose sections)

## What to check

### Numbers
- Numbers one through nine should be spelled out
- Exception: ages, percentages, addresses, money always use numerals
- "Percent" should be spelled out, not "%"

### Dates and times
- Months with dates should be abbreviated: Jan., Feb., Aug., Sept., Oct., Nov., Dec.
- March, April, May, June, July are never abbreviated
- Times should use a.m./p.m. format: "9 a.m." not "9:00 AM"
- "Noon" and "midnight" not "12 p.m." or "12 a.m."

### Titles
- Formal titles before names should be capitalized: "Mayor Jane Smith"
- Titles after names or alone should be lowercase: "Jane Smith, the mayor"

### Common word choices
- "More than" for quantities, not "over"
- "Fewer" for countable items, "less" for mass nouns
- "Said" for attribution, not "stated," "remarked," "noted"

### Formatting
- Headlines should use sentence case, not title case
- No exclamation points in hard news
- Paragraphs should be short (1-3 sentences for news)

## Output format

If violations found, add a note:

```
⚠️ AP Style check:
- Line [X]: [issue] → [suggestion]
- Line [X]: [issue] → [suggestion]

These are non-blocking suggestions. Review before publication.
```

## Non-blocking

This hook provides suggestions only. It does not prevent the write/edit from completing. The goal is awareness, not enforcement.

## Skip conditions

Skip this check for:
- Code files
- Configuration files
- Data files (JSON, YAML, CSV)
- Files in node_modules, .git, venv, etc.

## Examples

**Flagged:**
```
"The mayor stated that over 15 percent of residents..."
```
→ "stated" should be "said"; "over" should be "more than"; "percent" is fine

**Flagged:**
```
"The meeting starts at 9:00 AM on October 15th."
```
→ "9:00 AM" should be "9 a.m."; "October" shouldn't be abbreviated with date; ordinal "15th" should be "15"

**Clean:**
```
"The meeting starts at 9 a.m. Oct. 15."
```
