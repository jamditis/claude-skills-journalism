---
description: Create a multi-page funding proposal with your organization's branding
argument-hint: [project-name]
allowed-tools: Read, Write, Edit, Glob, Bash, AskUserQuestion, mcp__plugin_playwright_playwright__*
---

Create a print-ready HTML funding proposal document using a guided wizard.

## Version check

Read the plugin version from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and note it. If the file doesn't exist or the read fails, warn the user that the plugin may not be properly installed.

## Setup

1. Check for brand configuration at `.claude/pdf-playground.local.md`
2. If found, parse the YAML frontmatter for brand settings
3. If not found, ask the user for their organization name and primary brand color
4. Load the proposal template from `${CLAUDE_PLUGIN_ROOT}/templates/proposal-template.html`
5. Read the document-design skill for CSS patterns

## Project name

The project name is: $ARGUMENTS

If no project name provided, ask the user in Phase 1 below.

---

## Phase 1 — Content setup

Gather requirements using AskUserQuestion before generating anything.

**Q1: Proposal type**

```
AskUserQuestion:
  question: "What type of proposal is this?"
  header: "Type"
  options:
    - label: "Funding proposal"
      description: "Request for grant funding or financial support from a foundation or government agency"
    - label: "Partnership pitch"
      description: "Pitch to a potential partner organization for a collaborative project"
    - label: "Program overview"
      description: "Summary of an existing program for stakeholders or board members"
```

**Q2: Sections to include**

```
AskUserQuestion:
  question: "Which sections should be included?"
  header: "Sections"
  multiSelect: true
  options:
    - label: "Background"
      description: "Context, history, and research supporting the need"
    - label: "Proposed work"
      description: "Priorities, deliverables, and what the funding supports"
    - label: "Case studies"
      description: "Evidence of past success with named examples"
    - label: "Budget"
      description: "Itemized budget table with totals"
```

**Q3: Page count**

```
AskUserQuestion:
  question: "How many pages should the proposal be?"
  header: "Pages"
  options:
    - label: "3 pages (compact)"
      description: "Cover + 2 content pages. Good for quick briefs."
    - label: "4 pages (standard)"
      description: "Cover + background + proposed work + budget"
    - label: "5 pages (full)"
      description: "Cover + background + proposed work + case studies + budget"
    - label: "6+ pages (detailed)"
      description: "Full proposal with extra room for evidence and appendices"
```

**Q4: Budget line items (only if budget was selected in Q2)**

```
AskUserQuestion:
  question: "How many budget line items?"
  header: "Budget"
  options:
    - label: "3 items"
      description: "Simple budget with 3 expense categories"
    - label: "4 items"
      description: "Standard budget with 4 expense categories"
    - label: "5-6 items"
      description: "Detailed budget with 5-6 expense categories"
    - label: "7+ items"
      description: "Full budget — may need a second budget page"
```

If no project name was provided via $ARGUMENTS, also ask:
- Project name
- Brief description (1-2 sentences)

---

## Phase 2 — Design choices

**Q5: Color scheme**

```
AskUserQuestion:
  question: "What color scheme should the proposal use?"
  header: "Colors"
  options:
    - label: "Brand colors (Recommended)"
      description: "Use colors from your pdf-playground.local.md config, or the template defaults"
    - label: "Professional blue"
      description: "Navy and steel blue — formal and institutional"
    - label: "Bold red and black"
      description: "High contrast with red accents — CCM style"
    - label: "Custom"
      description: "You'll specify the exact hex colors"
```

If "Custom" selected: ask for primary color, dark variant, and text color.

If "Professional blue" selected: use `--red: #1a5f7a; --red-dark: #134a5e; --black: #0a1628;`

If "Bold red and black" selected: use template defaults (`--red: #CA3553`).

**Q6: Typography style**

```
AskUserQuestion:
  question: "What typography style?"
  header: "Fonts"
  options:
    - label: "Classic (Recommended)"
      description: "Playfair Display headings + Source Sans body — elegant and readable"
    - label: "Modern"
      description: "Inter for both headings and body — clean and contemporary"
    - label: "Mixed"
      description: "Merriweather headings + Open Sans body — warm and approachable"
    - label: "Custom"
      description: "You'll specify the exact Google Font names"
```

If "Custom" selected: ask for heading font name and body font name (must be valid Google Fonts).

**Q7: Visual style**

```
AskUserQuestion:
  question: "What visual style?"
  header: "Style"
  options:
    - label: "Clean and minimal (Recommended)"
      description: "Generous whitespace, subtle accents, professional tone"
    - label: "Bold and impactful"
      description: "Larger headings, stronger colors, prominent stats"
    - label: "Traditional and formal"
      description: "Conservative layout, smaller decorative elements, classic feel"
```

Apply style adjustments:
- **Clean and minimal**: Default template sizing. Body 11pt, heading scale 1.0x, padding 0.75in.
- **Bold and impactful**: Body 11pt, heading scale 1.15x, padding 0.65in. Stat numbers 20% larger.
- **Traditional and formal**: Body 10.5pt, heading scale 0.9x, padding 0.85in. Remove decorative gradients from highlight boxes (use solid background instead).

---

## Phase 3 — Generation and review

**Step 1: Generate the HTML**

Using the answers from Phases 1 and 2:
1. Copy the proposal template
2. Apply brand settings (org name, colors, fonts)
3. Include only the sections selected in Q2
4. Match the page count from Q3
5. Set budget line items per Q4
6. Apply color scheme from Q5
7. Apply typography from Q6
8. Apply visual style from Q7
9. Fill placeholder text with `[bracketed instructions]` for the user to fill in later
10. Save the HTML file in the current working directory

**Step 2: Launch preview with control panel**

1. Start a local HTTP server (see preview command for details):
   ```bash
   python -c "import socket; s=socket.socket(); s.settimeout(1); result=s.connect_ex(('127.0.0.1',8787)); s.close(); print('free' if result!=0 else 'busy')"
   ```
   Then start the server in the background on an available port.

2. Open in Playwright browser: `browser_navigate` to `http://localhost:<port>/<filename>.html`

3. Inject the control panel:
   - Read `${CLAUDE_PLUGIN_ROOT}/controls/control-panel.css`
   - Read `${CLAUDE_PLUGIN_ROOT}/controls/template-maps/proposal.js`
   - Read `${CLAUDE_PLUGIN_ROOT}/controls/prompt-generator.js`
   - Read `${CLAUDE_PLUGIN_ROOT}/controls/control-panel.js`
   - Inject all four via `browser_run_code` (CSS first, then template map, then prompt generator, then control panel last)

4. Take a screenshot and show it to the user

5. Explain the control panel:
   > The interactive control panel is loaded on the right side. You can tweak colors, fonts, spacing, and toggle sections live. When you're happy with changes, click "Copy all changes" in the panel — it puts a prompt on your clipboard that you can paste back here and I'll apply the changes to the source HTML.

**Step 3: Iterate with user**

Wait for user feedback. They may:
- Describe changes in words ("make the title bigger")
- Paste a prompt from the control panel's "Copy all changes" button
- Ask for specific adjustments

For each round:
1. Apply changes to the HTML source file
2. Refresh the browser: `browser_navigate` to the same URL
3. Re-inject the control panel (it's lost on page refresh)
4. Take a new screenshot

**Q8: Satisfaction check**

After applying changes:
```
AskUserQuestion:
  question: "How does this look?"
  header: "Review"
  options:
    - label: "Looks good"
      description: "Move on to finalization"
    - label: "Make more changes"
      description: "Keep tweaking — describe what to change or use the control panel"
    - label: "Start over"
      description: "Scrap this and begin the wizard again from the top"
```

If "Make more changes": loop back to Step 3.
If "Start over": go back to Phase 1.

---

## Phase 4 — Finalization

**Q9: What next?**

```
AskUserQuestion:
  question: "What would you like to do with the proposal?"
  header: "Next"
  options:
    - label: "Finalize and save"
      description: "Save the HTML file and clean up the preview server"
    - label: "Export to PDF"
      description: "Get instructions for printing to PDF from Chrome"
    - label: "Make more changes"
      description: "Go back to the review phase"
```

**If "Finalize and save":**
1. Close the browser: `browser_close`
2. Kill the HTTP server background process
3. Report the saved file path

**If "Export to PDF":**
Tell the user:
> To export as PDF:
> 1. Open the HTML file in Chrome
> 2. Press **Ctrl+P** (Windows/Linux) or **Cmd+P** (Mac)
> 3. Set "Destination" to **Save as PDF**
> 4. Set "Margins" to **None**
> 5. Check **Background graphics**
> 6. Click **Save**

Then ask Q9 again.

**If "Make more changes":**
Go back to Phase 3, Step 3.

---

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

## Output

Save the HTML file in the current working directory with a descriptive filename like `proposal-[project-name].html`.
