---
name: source-attribution-check
description: Flag unattributed quotes, claims, and statistics in journalism content
event: PostToolUse
tools: [Write, Edit]
---

# Source attribution check hook

After writing or editing journalism content, scan for unattributed information that requires sources.

## When this hook fires

- After `Write` tool creates or overwrites a file
- After `Edit` tool modifies a file
- Only for text files containing journalism content (.md, .txt, .html)

## What to detect

### Unattributed quotes

Look for quotation marks without attribution:

```
❌ "This policy will help thousands of families."
✅ "This policy will help thousands of families," Smith said.
```

### Unattributed statistics

Numbers and percentages without sources:

```
❌ Crime dropped 15% last year.
✅ Crime dropped 15% last year, according to FBI data.

❌ Most Americans support the policy.
✅ 67% of Americans support the policy, according to a Gallup poll.
```

### Unattributed claims

Factual assertions that need sourcing:

```
❌ The company has been losing money for years.
✅ The company has lost money for five consecutive quarters, SEC filings show.
```

### Patterns to flag

- Quotes without "said," "according to," or similar attribution
- Statistics without source citation
- "Studies show..." without naming the study
- "Experts say..." without naming experts
- "Critics argue..." without naming critics
- Definitive claims about what someone thinks/feels without quotes

## Output format

If issues found, add a note:

```
⚠️ Attribution check:
- Line [X]: Quote needs attribution - who said this?
- Line [X]: Statistic "15%" needs source
- Line [X]: "Experts say" - which experts?

Unattributed claims can damage credibility. Add sources.
```

## Non-blocking

This hook provides warnings only. The journalist decides whether attribution is needed in context (some facts are common knowledge).

## Skip conditions

Skip this check for:
- Opinion/editorial pieces (first-person commentary)
- Code files
- Configuration files
- Content clearly marked as analysis/opinion

## Context awareness

Some claims don't need attribution:
- Commonly known facts ("The sun rises in the east")
- Observable facts ("The building is on Main Street")
- Direct observations by the reporter ("The crowd cheered")

Focus on claims that readers would reasonably ask "says who?"
