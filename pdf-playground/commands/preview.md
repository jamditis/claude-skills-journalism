---
description: Launch interactive preview for document editing
argument-hint: [file-path]
allowed-tools: Read, Write, Edit, Glob, Bash, AskUserQuestion, mcp__plugin_playwright_playwright__*
---

Launch an interactive preview session for iterating on a document design.

## Setup

1. Read the document-design skill for guidance
2. Resolve the HTML file path (see "File path" below)
3. Start a local HTTP server to serve the file
4. Set up the playground wrapper and controls
5. Open the wrapper in the Playwright browser

## Pre-flight check

Before proceeding, verify the control panel files exist:

1. Check if the controls directory exists:
   ```bash
   ls "${CLAUDE_PLUGIN_ROOT}/controls/control-panel.js" 2>/dev/null && echo "OK" || echo "MISSING"
   ```
2. If MISSING, tell the user:
   > Your PDF Playground plugin is outdated and missing the interactive control panel.
   > Run this command to update, then restart Claude Code:
   > ```
   > claude plugin update pdf-playground@claude-skills-journalism
   > ```
   Then STOP — do not continue with the preview workflow.

## Preview workflow

**Step 1: Start local server**

The Playwright browser cannot open `file://` URLs. Start a local HTTP server instead:

1. Determine the directory containing the HTML file
2. Check if port 8787 is available:
   ```bash
   python -c "import socket; s=socket.socket(); s.settimeout(1); result=s.connect_ex(('127.0.0.1',8787)); s.close(); print('free' if result!=0 else 'busy')"
   ```
3. If port 8787 is busy, try 8788, 8789, etc. until one is free
4. Start the server in the background:
   ```bash
   cd <directory-containing-html> && python -m http.server <port>
   ```
   Run this with `run_in_background: true`
5. Wait 1 second for the server to start

**Step 2: Set up the playground wrapper**

The playground uses an iframe-based architecture: the document lives in an iframe, and the control panel sits alongside it as a sidebar. This keeps the document HTML clean for PDF export while providing interactive design controls.

1. Create a `playground-controls/` directory in the same directory as the HTML file
2. Copy the control files from the plugin:
   ```bash
   mkdir -p <html-dir>/playground-controls/template-maps
   cp ${CLAUDE_PLUGIN_ROOT}/controls/control-panel.css <html-dir>/playground-controls/
   cp ${CLAUDE_PLUGIN_ROOT}/controls/control-panel.js <html-dir>/playground-controls/
   cp ${CLAUDE_PLUGIN_ROOT}/controls/prompt-generator.js <html-dir>/playground-controls/
   ```
3. Detect which template is being previewed and copy the matching template map:
   ```bash
   cp ${CLAUDE_PLUGIN_ROOT}/controls/template-maps/<template-name>.js <html-dir>/playground-controls/template-maps/
   ```
4. Copy the wrapper HTML to the same directory as the HTML file:
   ```bash
   cp ${CLAUDE_PLUGIN_ROOT}/controls/playground-wrapper.html <html-dir>/
   ```

**Step 3: Open the wrapper**

Navigate to the wrapper page with the document and template as URL parameters:
```
http://localhost:<port>/playground-wrapper.html?doc=<filename>.html&template=<template-name>
```

The `template` parameter defaults to `proposal` if omitted.

The wrapper page will:
- Display the document in a full-height iframe (left side)
- Show the control panel as a sidebar (right side)
- Handle all iframe-to-control communication automatically

Take an initial screenshot to show current state.

Tell the user:
> The interactive control panel is now loaded on the right side of the preview. You can:
> - Adjust colors, fonts, spacing, and layout live
> - Toggle sections on and off
> - Try different presets for quick theme changes
> - Click "Copy changes" to get a prompt you can paste back here
> - I'll apply the changes to the HTML source file

**Step 4: Gather feedback**

- Ask user what changes they'd like
- Options:
  - Describe changes in words
  - Point out specific areas to adjust
  - Paste a prompt from the control panel's "Copy changes" button
  - Request screenshots of specific pages

**Step 5: Implement changes**

- Edit the HTML file based on feedback
- Refresh the browser to show updates: `browser_navigate` to the same wrapper URL
- The control panel reloads automatically with the wrapper (no re-injection needed)
- Take new screenshots to confirm

**Step 6: Iterate**

- Repeat steps 4-5 until satisfied
- Offer to take final screenshots

**Step 7: Clean up**

When the user is done:
1. Close the browser: `browser_close`
2. Kill the HTTP server (the background Bash process)
3. Optionally remove the temporary playground files:
   ```bash
   rm -rf <html-dir>/playground-controls <html-dir>/playground-wrapper.html
   ```

## File path

The file to preview is: $ARGUMENTS

If no file path provided:
1. Look for HTML files in current directory
2. If found, list them and ask which to preview
3. If none found, ask for the file path

## Template detection

To determine which template map to use, check the HTML file for clues:
- Look for CSS class names that match known templates (e.g. `.cover-title`, `.stat-grid` for proposal)
- Check the document structure and layout
- If uncertain, default to the proposal template map

Currently available template maps:
- `proposal.js` — Funding proposals, grant applications

## Common adjustments

- Text content changes
- Spacing and margin adjustments
- Font size tweaks
- Color modifications
- Layout restructuring
- Adding or removing sections
- Fixing overlap issues

## Browser commands

- `browser_navigate` — Open the wrapper page via HTTP URL
- `browser_snapshot` — Get accessibility tree
- `browser_take_screenshot` — Capture visual state
- `browser_close` — End preview session

## Tips

- Always use HTTP URLs (`http://localhost:<port>/`) — never `file://`
- Take screenshots after each change
- The control panel reloads with each page navigation (no manual re-injection needed)
- For multi-page docs, scroll or use page-specific screenshots
- Remind user: Ctrl+P in Chrome -> Save as PDF -> Margins: None -> Background graphics: checked
- The wrapper uses `display: flex` and `clamp()` so it scales with the browser window
