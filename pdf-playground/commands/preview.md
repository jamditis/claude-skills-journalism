---
description: Launch interactive preview for document editing
argument-hint: [file-path]
allowed-tools: Read, Edit(./**/*.html), Glob, AskUserQuestion, Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/playground.py *), Bash(python ${CLAUDE_PLUGIN_ROOT}/scripts/playground.py *), mcp__plugin_playwright_playwright__*
---

Launch an interactive preview session for iterating on a document design.

## Setup

1. Read the document-design skill for guidance
2. Resolve the HTML file path (see "File path" below)
3. Copy the playground wrapper and controls next to the file
4. Start a local HTTP server to serve the file
5. Open the wrapper in the Playwright browser

## Helper script

Every shell step runs through one plugin script. This command pre-approves only
that script, so use the exact form below. If `python3` is not found (common on
Windows), use `python` in its place.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/playground.py <setup|serve|clean> ...
```

## Preview workflow

**Step 1: Set up the playground wrapper**

The playground uses an iframe-based architecture: the document lives in an iframe, and the control panel sits alongside it as a sidebar. This keeps the document HTML clean for PDF export while providing interactive design controls.

Detect which template is being previewed (see "Template detection" below), then copy the control files and wrapper next to the HTML file:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/playground.py setup <html-file> --template <template-name>
```

This creates `playground-controls/` and `playground-wrapper.html` in the same directory as the HTML file and prints the wrapper path to open.

If the command prints that the control panel is missing, tell the user to run this command and restart Claude Code, then STOP:

```
claude plugin update pdf-playground@claude-skills-journalism
```

**Step 2: Start local server**

The Playwright browser cannot open `file://` URLs. Start a local HTTP server instead, with `run_in_background: true`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/playground.py serve <directory-containing-html>
```

The script picks the first free port from 8787 upward, binds to `127.0.0.1` only, and prints `Serving http://localhost:<port>/`. Read the port from that line.

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
2. Stop the HTTP server (the background process from step 2)
3. Optionally remove the temporary playground files:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/playground.py clean <html-file>
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
- `proposal.js`, Funding proposals, grant applications

## Common adjustments

- Text content changes
- Spacing and margin adjustments
- Font size tweaks
- Color modifications
- Layout restructuring
- Adding or removing sections
- Fixing overlap issues

## Browser commands

- `browser_navigate`, Open the wrapper page via HTTP URL
- `browser_snapshot`, Get accessibility tree
- `browser_take_screenshot`, Capture visual state
- `browser_close`, End preview session

## Tips

- Always use HTTP URLs (`http://localhost:<port>/`), never `file://`
- Take screenshots after each change
- The control panel reloads with each page navigation (no manual re-injection needed)
- For multi-page docs, scroll or use page-specific screenshots
- Remind user: Ctrl+P in Chrome -> Save as PDF -> Margins: None -> Background graphics: checked
- The wrapper uses `display: flex` and `clamp()` so it scales with the browser window
