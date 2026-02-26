---
description: Create HTML presentation slides with your organization's branding
argument-hint: [presentation-name]
allowed-tools: Read, Write, Edit, Glob, mcp__plugin_playwright_playwright__*
---

Create HTML presentation slides.

## Version check

Read the plugin version from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and note it. If the file doesn't exist or the read fails, warn the user that the plugin may not be properly installed.

## Setup

1. Check for brand configuration at `.claude/pdf-playground.local.md`
2. If found, parse the YAML frontmatter for brand settings
3. Load the slides template from `${CLAUDE_PLUGIN_ROOT}/templates/slides-template.html`

## Slide format

Each slide: 10" × 7.5" (4:3) or 13.33" × 7.5" (16:9)

## Slide types

**Title slide:**
- Large centered title
- Subtitle or presenter name
- Date
- Organization branding

**Content slide:**
- Slide title at top
- Bullet points (max 5-6)
- Slide number

**Section divider:**
- Large section title
- Primary color background

**Two-column:**
- Title at top
- Left: text/bullets
- Right: image or data area

**Quote slide:**
- Large pull quote
- Attribution
- Accent styling

**Stat slide:**
- Large number
- Description

**End slide:**
- Thank you
- Contact info

## Design rules

- Large fonts (title: 36-48pt, body: 24-28pt)
- Minimal text (6×6 rule: max 6 bullets, 6 words each)
- High contrast
- Brand colors throughout

## Presentation name

The name is: $ARGUMENTS

If not provided, ask for:
- Presentation title
- Number of slides
- Key topics
- Aspect ratio preference

## Output

Save HTML file in current working directory.
To present: Open in browser, use print to PDF, or Decktape.
