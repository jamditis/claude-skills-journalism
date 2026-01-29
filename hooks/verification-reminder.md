---
name: verification-reminder
description: Prompt to verify facts before including them in journalism content
event: PostToolUse
tools: [Write, Edit]
---

# Verification reminder hook

After writing content that includes factual claims, remind about verification before publication.

## When this hook fires

- After `Write` tool creates journalism content
- After `Edit` tool adds new factual claims
- When content includes verifiable assertions

## What to flag for verification

### Names and titles

```
⚠️ Verify: "Mayor John Smith" - Is spelling correct? Is title current?
```

### Dates and times

```
⚠️ Verify: "Tuesday, January 15" - Does the day match the date?
```

### Numbers and statistics

```
⚠️ Verify: "$5 million budget" - Source? Recent figure?
```

### Quotes

```
⚠️ Verify: Direct quote - Matches recording/transcript?
```

### Historical claims

```
⚠️ Verify: "Founded in 1985" - Primary source confirms?
```

### Contact information

```
⚠️ Verify: Phone number, email, address - Still current?
```

## Verification checklist

When flagging content, suggest verification steps:

```
📋 Verification checklist for this content:

Names/Titles:
- [ ] Spelling confirmed with source or official records
- [ ] Title is current (not former)

Numbers:
- [ ] Source document reviewed
- [ ] Calculations double-checked
- [ ] Context appropriate (per capita, adjusted, etc.)

Quotes:
- [ ] Matches recording or transcript
- [ ] Context preserved
- [ ] Speaker confirmed accuracy (if read-back promised)

Dates:
- [ ] Day of week matches calendar date
- [ ] Timezone considered if relevant

Claims:
- [ ] Primary source consulted
- [ ] Corroborating source found
- [ ] Subject given chance to respond
```

## Output format

```
⚠️ Verification reminder:

This content includes claims that should be verified:
- [Claim 1]: [suggested verification]
- [Claim 2]: [suggested verification]

Have you checked these against primary sources?
```

## Non-blocking

This is a reminder, not a gate. Experienced journalists may have already verified; this catches items that might be missed under deadline pressure.

## Skip conditions

Skip for:
- Clearly labeled drafts/notes
- Opinion pieces (though facts within opinions still need verification)
- Content quoting other published sources (cite the source instead)
