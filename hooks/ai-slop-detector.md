---
name: ai-slop-detector
description: Warn about AI-generated writing patterns that erode reader trust
event: PostToolUse
tools: [Write, Edit]
---

# AI slop detector hook

After writing or editing content, scan for phrases and patterns that signal AI-generated text and flag them.

## When this hook fires

- After `Write` tool creates or overwrites a file
- After `Edit` tool modifies a file
- Only for text files containing prose (.md, .txt, .html)

## What to detect

### Banned words (high confidence AI markers)

| Word | Severity |
|------|----------|
| delve | High |
| realm | High |
| tapestry | High |
| landscape (metaphorical) | Medium |
| leverage (as verb) | Medium |
| utilize | Medium |
| robust | Medium |
| seamless | Medium |
| comprehensive | Low |
| cutting-edge | Low |
| holistic | Low |
| synergy | High |
| paradigm | Medium |

### Banned phrases

**Throat-clearing:**
- "It's important to note that..."
- "In today's [X] landscape..."
- "Let's dive/delve into..."
- "Without further ado..."

**Empty hedges:**
- "At the end of the day..."
- "When it comes to..."
- "In terms of..."

**AI enthusiasm:**
- "This is a game-changer"
- "...and that's a good thing!"
- "Here's the thing:"

### Banned structures

**Sentence starters:**
- "So," (when not answering a question)
- "Now," (when not about time)
- "Basically,"
- "Essentially,"

### Patterns

- Lists of near-synonyms: "comprehensive, sophisticated, and robust"
- The "Not just X—it's Y" construction
- "Fundamentally transforms" or "fundamental shift"
- Title Case In Headlines When Sentence Case Expected

## Output format

If patterns found, add a note:

```
⚠️ AI writing patterns detected:
- Line [X]: "delve" → consider: examine, explore, look at
- Line [X]: "In today's landscape" → delete throat-clearing
- Line [X]: Title Case heading → use sentence case

These patterns can erode reader trust. Consider revising.
```

## Non-blocking

This hook provides warnings only. It does not prevent the write/edit from completing. The purpose is awareness—the writer decides whether to revise.

## Skip conditions

Skip this check for:
- Code files
- Configuration files
- Data files (JSON, YAML, CSV)
- Files in node_modules, .git, venv, etc.
- Content quoted from external sources (check for quotation marks)

## Severity levels

- **High:** Almost certainly AI-generated; strong signal
- **Medium:** Commonly AI-generated but has legitimate uses
- **Low:** Often overused by AI but may be appropriate in context

Only flag high and medium severity items. Low severity items can be mentioned if there are multiple.

## Examples

**Flagged:**
```
In today's rapidly evolving digital landscape, it's crucial to
delve into how these robust tools can help journalists leverage
cutting-edge technology.
```
→ Multiple issues: "In today's...landscape," "delve," "robust," "leverage," "cutting-edge"

**Flagged:**
```
## Getting Started With Your Project
```
→ Title Case heading; should be "Getting started with your project"

**Clean:**
```
AI tools do three things well: drafting, research, and analysis.
Here's when to use each.
```
