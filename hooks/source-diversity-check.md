---
name: source-diversity-check
description: Note when sources in an article may lack diversity of perspective
event: PostToolUse
tools: [Write, Edit]
---

# Source diversity check hook

After writing content with multiple sources, check whether the sourcing reflects diverse perspectives.

## When this hook fires

- After `Write` tool creates content with quoted sources
- After `Edit` tool adds sources to existing content
- When content includes multiple named sources

## What to check

### Single-perspective sourcing

```
⚠️ All sources appear to share same viewpoint
   Consider: Are opposing/different perspectives represented?
```

### Authority imbalance

```
⚠️ Sources are all officials/institutions
   Consider: Are affected community members included?
```

### Gender balance

```
⚠️ All quoted sources appear to be same gender
   Consider: Does the topic warrant diverse gender perspectives?
```

### Expertise diversity

```
⚠️ All experts from same institution/background
   Consider: Would different expertise add value?
```

## Source diversity checklist

```
📋 Source diversity considerations:

Perspective:
- [ ] Multiple viewpoints on contentious issues
- [ ] Critics and supporters both represented
- [ ] Affected parties have voice, not just officials

Demographics:
- [ ] Gender diversity in expert sources
- [ ] Geographic diversity where relevant
- [ ] Age diversity where relevant

Authority levels:
- [ ] Official sources (government, institutions)
- [ ] Expert sources (academics, specialists)
- [ ] Community sources (affected individuals)
- [ ] Advocacy sources (organizations, activists)

Context:
- [ ] Historical context sources
- [ ] Data/research sources
- [ ] On-the-ground observers
```

## Output format

```
⚠️ Source diversity note:

This piece includes [X] quoted sources. Consider:

- All sources appear to be [observation]
- Missing perspective: [suggestion]

Diverse sourcing strengthens journalism and serves readers better.
```

## When diversity matters most

| Story type | Key diversity considerations |
|------------|------------------------------|
| Policy stories | Affected communities, not just officials |
| Expert roundups | Different institutions, methodologies |
| Conflict coverage | All parties to the dispute |
| Community stories | Range of community members |
| Business stories | Workers, not just executives |

## When it matters less

- Breaking news (get what you can, expand later)
- Single-source profiles (by design)
- Direct quotes from documents/statements
- Historical pieces with limited living sources

## Important caveats

This hook raises awareness but:

- **Not a quota system** - Quality matters more than counting
- **Context matters** - Some stories legitimately focus on one perspective
- **Not about false balance** - Don't platform bad-faith actors for "diversity"
- **Time pressure is real** - Do what you can, note limitations

## Non-blocking

This hook prompts reflection, not requirements. Journalists make editorial decisions about sourcing based on the story's needs.

## Skip conditions

Skip for:
- Single-source stories (profiles, interviews)
- Breaking news with limited sourcing time
- Opinion/commentary pieces
- Aggregation of other reporting
