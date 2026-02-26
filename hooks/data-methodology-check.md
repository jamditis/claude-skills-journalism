---
name: data-methodology-check
description: Ensure data journalism content includes methodology documentation
event: PostToolUse
tools: [Write, Edit]
---

# Data methodology check hook

After writing data-driven content, check that methodology is documented for transparency and reproducibility.

## When this hook fires

- After `Write` tool creates content with data analysis
- After `Edit` tool adds statistics or data findings
- When content includes charts, calculations, or data-driven claims

## What to check

### Data source documentation

```
⚠️ Methodology: Data source not specified
   Add: Where did this data come from? When was it collected?
```

### Sample size and scope

```
⚠️ Methodology: Sample size not mentioned
   Add: How many records? What time period? Geographic scope?
```

### Calculation transparency

```
⚠️ Methodology: Calculation method unclear
   Add: How was this percentage/rate/average calculated?
```

### Limitations acknowledgment

```
⚠️ Methodology: No limitations mentioned
   Add: What are the caveats? What can't this data tell us?
```

### Data cleaning notes

```
⚠️ Methodology: Data cleaning not documented
   Add: Were records excluded? How were duplicates handled?
```

## Methodology checklist

For data stories, ensure documentation covers:

```
📋 Data methodology checklist:

Source:
- [ ] Data source named (agency, organization, etc.)
- [ ] Date of data collection/release
- [ ] How data was obtained (FOIA, API, download, etc.)

Scope:
- [ ] Time period covered
- [ ] Geographic scope
- [ ] Universe (all records or sample?)
- [ ] Sample size stated

Analysis:
- [ ] Calculations explained
- [ ] Tools/software mentioned (if relevant)
- [ ] Statistical methods named (if used)

Limitations:
- [ ] Known gaps in data
- [ ] Caveats about interpretation
- [ ] What the data cannot show

Reproducibility:
- [ ] Data available for download (if possible)
- [ ] Code/queries available (if applicable)
```

## Output format

```
⚠️ Data methodology check:

This content includes data analysis. Verify methodology is documented:

Missing elements:
- [ ] Data source not specified
- [ ] Time period unclear
- [ ] Calculation method not explained

Readers and other journalists should be able to understand and verify your analysis.
```

## Methodology box template

If methodology is missing, suggest adding:

```markdown
## Methodology

**Data source:** [Name of source]
**Time period:** [Date range]
**Records analyzed:** [Number]

**Analysis:** [Brief description of methods]

**Limitations:** [What the data doesn't show]

**Download:** [Link to data if available]
```

## Non-blocking

This hook reminds about transparency. Not all data mentions need full methodology boxes—use judgment about what level of documentation fits the content.

## Skip conditions

Skip for:
- Casual mentions of commonly known statistics
- Citing other publications' data work (cite them instead)
- Opinion pieces using data for illustration
