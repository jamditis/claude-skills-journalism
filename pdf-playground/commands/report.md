---
description: Create a program report or annual report with your organization's branding
argument-hint: [report-name]
allowed-tools: Read, Write, Edit, Glob, mcp__plugin_playwright_playwright__*
---

Create a print-ready HTML program report document.

## Setup

1. Check for brand configuration at `.claude/pdf-playground.local.md`
2. If found, parse the YAML frontmatter for brand settings
3. If not found, ask the user for their organization name and primary brand color
4. Load the report template from `${CLAUDE_PLUGIN_ROOT}/templates/report-template.html`
5. Read the document-design skill for CSS patterns

## Brand application

Apply brand settings to the template:
- Replace organization name throughout
- Update CSS variables with brand colors
- Set font families from brand config
- Apply heading case style

## Document structure

**Page 1 - Cover page:**
- Organization branding
- Report title in configured case
- Subtitle (e.g., "Annual report 2025")
- Date range or publication date

**Page 2+ - Content sections:**
- Executive summary
- Key metrics or highlights (use callout boxes)
- Detailed sections with headings
- Data visualizations or tables
- Quotes and testimonials

**Final page:**
- Contact information
- Acknowledgments
- Organization info

## Report name

The report name is: $ARGUMENTS

If no report name provided, ask the user for:
- Report title
- Time period covered
- Key sections to include
- Any metrics or data to highlight

## Output

Save the HTML file in the current working directory.
After creating, offer to preview with Playwright browser tools.
