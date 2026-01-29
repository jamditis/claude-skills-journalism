---
name: legal-review-flag
description: Flag potentially defamatory or legally risky content for review
event: PostToolUse
tools: [Write, Edit]
---

# Legal review flag hook

After writing content, flag statements that may carry legal risk and should be reviewed before publication.

## When this hook fires

- After `Write` tool creates content with potentially risky claims
- After `Edit` tool adds allegations or accusations
- When content discusses legal matters, accusations, or private information

## What to flag

### Defamation risk

Statements that could be defamatory if false:

```
⚠️ Legal flag: "Smith embezzled funds" - Is this proven? Source?
```

**High-risk patterns:**
- Accusations of crimes
- Allegations of dishonesty, fraud, corruption
- Claims about professional incompetence
- Statements damaging to reputation

### Privacy concerns

```
⚠️ Legal flag: Medical information disclosed - Is this newsworthy? Consent?
```

**Sensitive areas:**
- Medical/health information
- Sexual history or orientation
- Financial details of private individuals
- Minor children's identities
- Home addresses (safety concern)

### Confidential sources

```
⚠️ Legal flag: Source could be identified from details provided
```

**Check for:**
- Details that narrow down who the source could be
- Information only a few people would know
- Job titles or departments with few employees

### Pre-trial publicity

```
⚠️ Legal flag: Detailed crime allegations before trial - Fair trial concerns?
```

### Copyright

```
⚠️ Legal flag: Extended quote from copyrighted work - Fair use applies?
```

## Risk levels

| Level | Description | Action |
|-------|-------------|--------|
| **High** | Accusations of crime, fraud | Must have documentation |
| **Medium** | Negative characterizations | Should have multiple sources |
| **Low** | Potentially embarrassing facts | Consider newsworthiness |

## Output format

```
⚠️ Legal review flags:

HIGH RISK:
- Line [X]: Accusation of [crime/misconduct] - Ensure documentation exists

MEDIUM RISK:
- Line [X]: Characterization of [person] - Verify with multiple sources

PRIVACY:
- Line [X]: [Type of information] - Confirm newsworthiness justifies disclosure

Consider legal review before publication for flagged items.
```

## Defense reminders

When flagging, remind of defamation defenses:

- **Truth**: The statement is provably true
- **Privilege**: Fair report of official proceedings
- **Opinion**: Clearly labeled as opinion, not fact
- **Public figure**: Higher bar for public officials/figures

## Non-blocking

This hook flags for review but doesn't prevent publication. Journalists and editors make the final call, ideally with legal counsel for high-risk items.

## Skip conditions

Skip for:
- Clearly fictional content
- Historical figures (deceased, generally)
- Content about the writer themselves
- Quotes from official court documents (privileged)
