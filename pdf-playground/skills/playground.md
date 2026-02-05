---
name: pdf-playground
description: Interactive PDF design playground - create and refine reports with live preview
user_invocable: true
---

# PDF Playground

An interactive environment for creating and testing PDF reports and proposals. Describe what you want, see previews, tweak the design with live controls, and iterate until it's perfect.

## Getting started

Tell me what kind of document you want to create:

- **"Create a funding proposal for [program]"**
- **"Make a 2-page impact report"**
- **"Design a budget summary with 3 tiers"**
- **"Build a cover page for [project]"**

I'll walk you through a guided setup, generate the HTML, show you a live preview with interactive design controls, and we'll refine it together.

## How the wizard works

For proposals (and eventually other templates), the process has four phases:

**Phase 1 — Content:** I'll ask what type of document you want, which sections to include, and how many pages. This happens through a series of quick multiple-choice questions.

**Phase 2 — Design:** I'll ask about color scheme, typography, and visual style. Pick from presets or go custom.

**Phase 3 — Review:** I generate the HTML, open a live preview in the browser, and inject an interactive control panel. You can tweak colors, fonts, spacing, and sections in real time. When you're satisfied with a set of changes, click "Copy all changes" in the panel — it puts a prompt on your clipboard. Paste it back here and I'll apply those changes to the HTML source.

**Phase 4 — Finalization:** Save the file, get PDF export instructions, or go back for more changes.

## Interactive control panel

When previewing a document, a wrapper page opens with your document in an iframe on the left and a control panel sidebar on the right. The panel includes:

- **Presets** — One-click theme buttons (CCM brand, Professional blue, Modern green, Warm earth, Elegant purple) that change colors and fonts together
- **Colors** — Color pickers for primary, dark, text, background, and accent colors
- **Typography** — Font dropdowns for headings and body, plus sliders for size, scale, and line height
- **Spacing** — Slider for page padding
- **Sections** — Toggles to show/hide stat grid, highlight boxes, case studies, budget table, and mission block
- **Layout** — Button groups for stat columns, select for heading case
- **Undo/Redo** — Step backward and forward through your changes

Changes apply instantly to the preview. A "Pending changes" list at the bottom tracks everything you've adjusted. Click "Copy changes" to get a prompt you can paste back into the conversation. The panel collapses to a thin sidebar tab when you don't need it.

## Interactive commands

During a session, use these:

| Command | What it does |
|---------|--------------|
| `preview` | Show current document as screenshot |
| `preview page 2` | Show specific page |
| `regenerate` | Rebuild PDF from HTML |
| `save` | Save to working directory |
| `upload` | Upload to Google Drive |
| `export` | Copy HTML to clipboard/file |
| `start over` | Reset and begin fresh |

## Example workflow

```
You: Create a 3-page funding proposal for Democracy Day

Claude: [Asks: What type of proposal?]
        [Asks: Which sections to include?]
        [Asks: How many pages?]
        [Asks: Color scheme?]
        [Asks: Typography style?]
        [Asks: Visual style?]

Claude: [Generates HTML based on your choices]
        [Opens live preview with control panel]
        [Shows screenshot]

        The proposal is ready with the interactive control panel
        loaded. Adjust anything you'd like in the panel, then click
        "Copy all changes" and paste the prompt here.

You: [Pastes prompt from control panel]
     Apply the following changes to the proposal:
     1. Change the primary color from #CA3553 to #2563EB
     2. Set the body font size to 12pt

Claude: [Applies changes to HTML source]
        [Refreshes preview]
        [Shows new screenshot]

        Done. How does this look?

You: Looks good — finalize it

Claude: [Saves file, cleans up server]
        Saved to proposal-democracy-day.html
```

## Design options

### Document types
- Cover page only
- 2-page brief
- 4-6 page proposal
- Full report with appendix

### Style presets
- **CCM brand** — Red (#CA3553), Playfair Display/Source Sans 3
- **Professional blue** — Teal (#1a5f7a), Merriweather/Open Sans
- **Modern green** — Green (#2d8659), Inter/Work Sans
- **Warm earth** — Amber (#b5651d), Lora/Nunito
- **Elegant purple** — Purple (#6b3fa0), DM Serif Display/IBM Plex Sans
- **Custom** — You specify colors and fonts

### Components available
- Cover pages with stats
- Section headers
- Body text with callouts
- Budget tables (single or multi-tier)
- Case study cards
- Testimonial blocks
- Appendix pages
- Institution footers

## Technical details

### Preview system
- Uses a local HTTP server (Python) to serve HTML files
- A wrapper page (`playground-wrapper.html`) loads your document in an iframe alongside the control panel sidebar
- Your document HTML stays completely unchanged — the controls live in the wrapper page
- The panel scales with the browser window using CSS `clamp()` and flexbox
- All controls are hidden during print (they won't appear in your PDF)
- No re-injection needed after page refresh — the wrapper handles everything

### Working directory
Files are created in your current working directory.

### How the control panel works
The control panel is built from three modules:
1. **Template map** (`controls/template-maps/proposal.js`) — defines which CSS variables, selectors, and sections exist in the template
2. **Prompt generator** (`controls/prompt-generator.js`) — tracks changes and generates copyable prompts
3. **Control panel** (`controls/control-panel.js`) — builds the UI from the template map, targets the iframe document for live changes

The wrapper page loads the template map dynamically via a URL parameter (`?template=proposal`), so the same wrapper works with any template.

To add control panel support for a new template, create a new template map file. See `controls/template-maps/README.md` for the format.

## Tips

1. **Be specific** — "Make the title 36pt bold" works better than "make it bigger"
2. **Use the control panel** — It's faster than describing changes in words for visual tweaks
3. **Preview often** — Check after each change
4. **Iterate** — Good design takes rounds of refinement
5. **Copy and paste** — The control panel's "Copy all changes" button is the fastest way to communicate design changes

## Quick start templates

Say one of these to begin immediately:

- `"Start a funding proposal"` — 4-page template with budget
- `"Start an impact report"` — 2-page metrics and testimonials
- `"Start a budget summary"` — Single page with table
- `"Start a cover page"` — Just the cover, perfect for presentations
