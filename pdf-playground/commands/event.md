---
description: Create event materials (flyers, posters, signage) with your organization's branding
argument-hint: [event-name]
allowed-tools: Read, Write, Edit, Glob, mcp__plugin_playwright_playwright__*
---

Create print-ready event materials.

## Setup

1. Check for brand configuration at `.claude/pdf-playground.local.md`
2. If found, parse the YAML frontmatter for brand settings
3. Load the event template from `${CLAUDE_PLUGIN_ROOT}/templates/event-template.html`

## Material types

**Flyer (8.5" × 11"):**
- Event title (large, eye-catching)
- Date, time, location
- Brief description
- Registration info or QR code placeholder
- Organization branding

**Poster (11" × 17"):**
- Bold headline
- Key details at a glance
- Visual hierarchy for scanning
- Prominent logo

**Signage:**
- Directional signs
- Welcome banners
- Table tents

## Design principles

- High visual impact
- Easy to read from distance (for posters)
- Clear hierarchy: What → When → Where → How
- Bold use of brand primary color
- Minimal text, maximum clarity

## Brand application

- Primary color for header/accent areas
- Secondary color for text
- Brand fonts
- Organization name in footer

## Event name

The event name is: $ARGUMENTS

If not provided, ask for:
- Event name
- Date and time
- Location
- Brief description
- Registration URL
- Material type needed

## Output

Save HTML file in current working directory.
For professional printing, export to PDF with "Background graphics" enabled.
