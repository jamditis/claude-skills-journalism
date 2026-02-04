---
name: playground
description: Interactive PDF design playground - create and refine reports with live preview
user_invocable: true
---

# PDF Playground

An interactive environment for creating and testing PDF reports and proposals. Describe what you want, see previews, and iterate until it's perfect.

## Getting started

Tell me what kind of document you want to create:

- **"Create a funding proposal for [program]"**
- **"Make a 2-page impact report"**
- **"Design a budget summary with 3 tiers"**
- **"Build a cover page for [project]"**

I'll generate the HTML, show you a preview, and we'll refine it together.

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

Claude: [Generates HTML template]
        [Shows cover page preview]

        Here's the initial design. The cover has:
        - Program title and tagline
        - 3 key stats
        - Date and logo

        What would you like to adjust?

You: Make the title bigger and change the stats to show
     newsrooms, states, and stories

Claude: [Updates HTML]
        [Shows new preview]

        Done! Title is now 48pt. Stats updated.
        Ready to see page 2?

You: Yes, show page 2

Claude: [Shows page 2 preview]
        ...
```

## Design options

### Document types
- Cover page only
- 2-page brief
- 4-6 page proposal
- Full report with appendix

### Style presets
- **CCM Standard** — Red (#CA3553), black, Montserrat/Source Sans
- **Civic** — Navy (#1a2b4a), gold (#c9a227), Inter/Fraunces
- **Minimal** — Black and white, clean typography
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

### PDF generation
Uses Chromium headless on this machine. Due to snap confinement:
- HTML copied to `~/snap/chromium/common/pdf-work/`
- PDF generated there
- Result copied to your working directory

### Working directory
Files are created in the scratchpad:
```
/tmp/claude-1000/.../scratchpad/
├── report.html      # Current HTML
├── report.pdf       # Generated PDF
└── preview-*.png    # Page previews
```

### Upload destinations
- **Shared with Joe**: Google Drive folder for review
- **Claude Workspace**: For Claude's own projects

## Tips

1. **Be specific** — "Make the title 36pt bold" works better than "make it bigger"
2. **Reference elements** — "The cover stats" or "the budget table footer"
3. **Preview often** — Check after each change
4. **Iterate** — Good design takes rounds of refinement

## Quick start templates

Say one of these to begin immediately:

- `"Start a funding proposal"` — 4-page template with budget
- `"Start an impact report"` — 2-page metrics and testimonials
- `"Start a budget summary"` — Single page with table
- `"Start a cover page"` — Just the cover, perfect for presentations
