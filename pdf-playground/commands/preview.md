---
description: Launch interactive preview for document editing
argument-hint: [file-path]
allowed-tools: Read, Write, Edit, Glob, mcp__plugin_playwright_playwright__*
---

Launch an interactive preview session for iterating on a document design.

## Setup

1. Read the document-design skill for guidance
2. Open the specified HTML file in the Playwright browser

## Preview workflow

**Step 1: Open the document**
- Navigate to the HTML file using `browser_navigate` with a file:// URL
- Take an initial screenshot to show current state

**Step 2: Gather feedback**
- Ask user what changes they'd like
- Options:
  - Describe changes in words
  - Point out specific areas to adjust
  - Request screenshots of specific pages

**Step 3: Implement changes**
- Edit the HTML file based on feedback
- Refresh the browser to show updates
- Take new screenshots to confirm

**Step 4: Iterate**
- Repeat until satisfied
- Offer to take final screenshots

## Common adjustments

- Text content changes
- Spacing and margin adjustments
- Font size tweaks
- Color modifications
- Layout restructuring
- Adding or removing sections
- Fixing overlap issues

## File path

The file to preview is: $ARGUMENTS

If no file path provided:
1. Look for HTML files in current directory
2. If found, list them and ask which to preview
3. If none found, ask for the file path

## Browser commands

- `browser_navigate` - Open the HTML file
- `browser_snapshot` - Get accessibility tree
- `browser_take_screenshot` - Capture visual state
- `browser_close` - End preview session

## Tips

- Use file:// URLs for local files
- Take screenshots after each change
- For multi-page docs, scroll or use page-specific screenshots
- Remind user: Ctrl+P → Save as PDF → Margins: None
