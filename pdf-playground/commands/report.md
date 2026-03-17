---
description: Create a program report or annual report with your organization's branding
argument-hint: [report-name]
allowed-tools: Read, Write, Edit, Glob, mcp__plugin_playwright_playwright__*
---

Create a print-ready HTML program report document.

## Version check

Read the plugin version from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and note it. If the file doesn't exist or the read fails, warn the user that the plugin may not be properly installed.

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

## Footer clearance (critical)

Content MUST NOT touch or overlap the page footer. This is a common issue.

- The `.page` element MUST use `display: grid; grid-template-rows: auto 1fr auto` so the footer takes its natural height and content fills the rest
- The content area MUST have `overflow: hidden` to prevent text bleeding past its bounds
- Never use `position: absolute` for footers — keep them in normal document flow as the third grid row
- After generating, always take a screenshot and visually verify the bottom of each page
- If content is too long, **reduce content** rather than shrinking the footer gap

## Output

Save the HTML file in the current working directory.
After creating, offer to preview with Playwright browser tools.
