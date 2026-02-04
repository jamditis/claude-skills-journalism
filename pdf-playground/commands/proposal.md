---
description: Create a multi-page funding proposal with your organization's branding
argument-hint: [project-name]
allowed-tools: Read, Write, Edit, Glob, mcp__plugin_playwright_playwright__*
---

Create a print-ready HTML funding proposal document.

## Setup

1. Check for brand configuration at `.claude/pdf-playground.local.md`
2. If found, parse the YAML frontmatter for brand settings
3. If not found, ask the user for their organization name and primary brand color
4. Load the proposal template from `${CLAUDE_PLUGIN_ROOT}/templates/proposal-template.html`
5. Read the document-design skill for CSS patterns

## Brand application

Apply brand settings to the template:
- Replace organization name throughout
- Update CSS variables with brand colors
- Set font families from brand config
- Apply heading case style (sentence or title)

## Document structure

Create a multi-page HTML document with:

**Page 1 - Cover page:**
- Organization logo/name in header
- Document type eyebrow
- Main title in configured heading case
- Subtitle or tagline
- Key statistics (if provided)
- Footer with organization and date

**Page 2+ - Content pages:**
- Section headings
- Body text with proper margins
- Fixed footer with document title and page number
- Proper page breaks between sections

**Budget page (if included):**
- Budget tables with brand-colored headers
- Total row with primary color background
- Two-year or custom period totals

## Project name

The project name is: $ARGUMENTS

If no project name provided, ask the user for:
- Project name
- Brief description
- Key sections to include
- Whether to include a budget

## Output

Save the HTML file in the current working directory with a descriptive filename.

After creating the file, offer to preview it with the Playwright browser tools.
