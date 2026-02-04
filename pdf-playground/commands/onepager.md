---
description: Create a single-page fact sheet or program overview
argument-hint: [topic]
allowed-tools: Read, Write, Edit, Glob, mcp__plugin_playwright_playwright__*
---

Create a print-ready single-page HTML fact sheet.

## Setup

1. Check for brand configuration at `.claude/pdf-playground.local.md`
2. If found, parse the YAML frontmatter for brand settings
3. If not found, ask the user for their organization name and primary brand color
4. Load the one-pager template from `${CLAUDE_PLUGIN_ROOT}/templates/onepager-template.html`

## Brand application

Apply brand settings throughout:
- Organization name in header
- CSS variables for colors
- Font families from config

## Document structure

Create a single 8.5" × 11" page with:

**Header:**
- Organization name/logo
- Document title
- Category eyebrow

**Content area:**
- Key points (3-5 bullet points)
- Brief description (2-3 paragraphs max)
- Sidebar with quick facts or stats
- Call to action

**Footer:**
- Organization website
- Contact information

## Layout options

- Two-column (main + sidebar)
- Full-width with callout boxes
- Grid for multiple equal sections

## Topic

The topic is: $ARGUMENTS

If no topic provided, ask for:
- Main topic or program name
- 3-5 key points
- Any statistics
- Call to action

## Output

Save HTML file in current working directory.
All content MUST fit on one page - no overflow.
