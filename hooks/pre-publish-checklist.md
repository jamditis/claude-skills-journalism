---
name: pre-publish-checklist
description: Remind about verification, legal review, and publication checks before completing journalism tasks
event: Stop
---

# Pre-publish checklist hook

When completing a task that appears to involve journalism content ready for publication, display a reminder checklist.

## When this hook fires

- At the `Stop` event (when Claude completes a task)
- Only when the task involved creating or editing journalism content
- Content indicators: articles, stories, press releases, fact-checks, news briefs

## Detection criteria

Trigger this checklist when the session included:
- Writing/editing .md or .html files with journalism content
- References to "publish," "post," "release," "file" in task context
- Content that looks like news articles (ledes, quotes, attribution)
- Fact-check articles or verification work

## Checklist to display

```
📋 Pre-publish checklist

Before publication, verify:

### Accuracy
- [ ] All facts independently verified
- [ ] Statistics sourced and double-checked
- [ ] Quotes accurate (check against recording/transcript)
- [ ] Names and titles correct
- [ ] Dates and numbers accurate

### Fairness
- [ ] All relevant parties contacted for comment
- [ ] Response deadline was reasonable
- [ ] Opposing viewpoints fairly represented
- [ ] No cherry-picked quotes or data

### Legal
- [ ] No defamation risk (statements supported by evidence)
- [ ] No privacy violations
- [ ] Copyright/fair use reviewed for images
- [ ] Confidential sources properly protected

### Style
- [ ] AP Style applied
- [ ] No AI-generated patterns ("delve," "landscape," etc.)
- [ ] Headline is accurate (not clickbait)
- [ ] Appropriate length for format

### Metadata
- [ ] SEO elements filled
- [ ] Categories/tags applied
- [ ] Author byline correct
- [ ] Publication date set

### Final
- [ ] Editor has reviewed
- [ ] Copy edit complete
- [ ] One more read-through for typos

This is a reminder, not a blocker. Use your judgment.
```

## Output format

Display the checklist as a callout at the end of the response:

```
---
📋 **Pre-publish reminder**

[Checklist above]

Ready to publish? Make sure you've checked these items.
---
```

## Skip conditions

Skip this checklist when:
- Task was clearly not journalism (code, config, data processing)
- Task was research/exploration only, not content creation
- Content is clearly internal (notes, plans, outlines)
- User explicitly said this is a draft/not for publication

## Non-blocking

This hook is purely informational. It reminds the user but does not prevent task completion or require confirmation.

## Purpose

Journalists working with AI assistance may move faster than traditional workflows. This hook serves as a "pause and verify" moment before publication, encouraging the verification habits that maintain credibility.

The goal is not to slow down or annoy—it's to build in a systematic reminder of professional standards.
