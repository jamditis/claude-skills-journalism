---
description: Create HTML presentation slides with your organization's branding
argument-hint: [presentation-name]
allowed-tools: Read, Write, Edit, Glob, mcp__plugin_playwright_playwright__*
---

Create HTML presentation slides.

## Version check

Read the plugin version from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and note it. If the file doesn't exist or the read fails, warn the user that the plugin may not be properly installed.

## Setup

1. Check for brand configuration at `.claude/pdf-playground.local.md`
2. If found, parse the YAML frontmatter for brand settings
3. Load the slides template from `${CLAUDE_PLUGIN_ROOT}/templates/slides-template.html`

## Slide format

Default: 16:9 widescreen (13.333" × 7.5"). Switch the `@page` rule to `10in 7.5in` for 4:3.

## Slide types

The template ships with layouts for most pitch- and walkthrough-style decks. Use the right one for each slide rather than forcing everything through a generic content layout.

### Cover and hero

**`.slide-title`** — Gradient title slide with centered headline, subtitle, presenter line. Use when no cover photo is available.

**`.slide-hero`** — Full-bleed photo background with right-aligned headline and subtitle, plus a red branded footer bar. Best for opening pitch decks. Set the background image on the `.hero-bg` child via inline style.

**`.slide-hero.slide-closing`** — Same hero with left-aligned headline for closing "Ready on [date]" slides. The subtitle sits tight to the headline on purpose — the close reads as one unit, not two floating lines.

### Section dividers

**`.slide-section`** — Solid red background with a large outlined section number and title. Use for clean typographic chapter breaks.

**`.slide-section.with-photo`** — Photo background with a red section chip ("Section 8.1") and a large section title. Use when the deck mirrors a numbered document (RFP response, report) and reviewers need to cross-reference.

### Content layouts

**`.slide-content`** — Headline with red accent rule, optional `.lede` intro paragraph, and bullet list or prose. The workhorse layout. The accent rule is a tight 0.95in × 0.08in red bar under the headline, not a heavy border across the whole body.

**`.slide-content.slide-two-col`** — Headline, optional lede, then two text columns with a dashed divider. Use for paired or compared topics.

**`.three-col`** — Three text columns with dashed dividers. Use inside a `.slide-body` for breaking one topic into three facets (e.g., partners / programming / operations).

**`.four-col-tiles`** — Four numbered tile cards with a red top rule, each containing a label ("Pillar 01"), short title, and 2–3 line description. Use for parallel capabilities or themes where each item deserves equal weight.

**`.stats-strip`** — Row of big numbers with small captions, each with a red left rule. Default 4 columns — override with `style="--stat-cols: 3"` on the container. Use to summarize the top-line numbers from a longer section.

**`.slide-table`** — Comparison or budget table with a red header row, gray-shaded label column, and grid rules. Use for scenario comparisons, budget tiers, or before/after data.

**`.partner-grid`** — 4-column grid of label tiles with a red left accent bar. Use for letters of support, sponsor lists, or organizations.

### Set pieces

**`.slide-quote`** — Pull quote on a tinted background with a red left rule.

**`.slide-stat`** — Single huge number centered on white. Use when one statistic carries the slide.

**`.slide-end`** — Dark "thank you" closing slide with contact info.

## Design rules

- **Sentence case everywhere.** Never Title Case. Use `text-transform: uppercase` in CSS if you want visual caps on a section chip or hero title, but keep the source text in sentence case.
- **Large fonts.** Title: 52–68pt. Headline: 32–36pt. Lede: 19pt bold. Body: 16pt. Footer: 10–11pt.
- **Tight vertical rhythm.** Headline → accent rule → lede → body should feel connected, not spaced out. The template's default paddings are already tuned; don't add extra `margin-top` to children.
- **Minimal text.** Max 5–6 bullets per slide, max 2 lines per bullet. If you need more, split the slide.
- **Contrast.** Dark text on white, white text on red or dark photo overlays. No gray-on-gray.
- **Brand colors.** Set `--red` on `:root` to your primary. Use `--font-heading` and `--font-body` to swap font pairs (Playfair/Source Sans for reports, Montserrat for modern decks).
- **Photos earn their place.** Hero slides and section dividers with photos have more impact than gradient or solid-color versions. Use photos when you have good ones; fall back to gradients otherwise.
- **Accent rule, not border-bottom.** The headline's red accent rule is tight to the title. Don't convert it to a full-width border unless you want a different visual system.

## Content discipline

- The lede should be one or two sentences max, sitting right below the headline.
- Bold inline phrases in bullets anchor the most important words. Use sparingly — bolding everything bolds nothing.
- Section chips should use the RFP/report section number ("Section 8.1") if the deck is a walkthrough, or a simple eyebrow label ("Chapter 2") otherwise.

## Presentation name

The name is: $ARGUMENTS

If not provided, ask for:
- Presentation title
- Target audience (investors, selection committee, internal briefing, etc.)
- Number of slides
- Key topics or RFP sections to walk through
- Aspect ratio preference (default 16:9)
- Whether photos are available for hero and divider slides

## Footer clearance (critical)

Content MUST NOT touch or overlap the slide footer.

- The `.slide` element MUST use `display: grid; grid-template-rows: auto 1fr auto`
- Content slides MUST have exactly 3 direct children: `<div class="slide-header">`, `<div class="slide-body">`, `<div class="slide-footer">` (or `.slide-footer-red` for the branded bar)
- The `.slide-body` MUST have `overflow: hidden` to prevent text bleeding
- Never use `position: absolute` for footers — keep them in normal document flow as the third grid row
- Title and section slides that don't have footers can use flex layout instead
- After generating, always take a screenshot and visually verify the bottom of each slide
- If content is too long, **reduce content** rather than shrinking the footer gap

## Output

Save HTML file in current working directory alongside a `photos/` folder for any hero/divider images.

To export:
- **PDF**: `chromium --headless=new --disable-gpu --no-sandbox --no-pdf-header-footer --print-to-pdf=out.pdf "file://$(pwd)/slides.html"`
- **Google Slides / PowerPoint**: Screenshot each slide to PNG via `pdftoppm`, then assemble with python-pptx as full-bleed images. Upload the resulting `.pptx` to Google Drive with `mimeType: application/vnd.google-apps.presentation` to convert. This gives pixel-perfect fidelity across all three formats from a single HTML source.
- **Text-editable PowerPoint**: Build a parallel python-pptx file with native text shapes. Use the same palette and structure but accept minor spacing differences — the trade-off is editability.

## Multi-format delivery pattern

When a deck needs to ship as PDF, PowerPoint, and Google Slides:

1. Build the HTML deck (authoritative source)
2. Render to PDF via Chromium headless
3. Screenshot each slide to PNG via `pdftoppm -r 144 -png`
4. Assemble PNGs into a `.pptx` with python-pptx (one full-bleed image per slide)
5. Upload the `.pptx` to Google Drive with conversion to Google Slides
6. Export the Google Slides as PDF for cross-verification

All three formats share the same source pixels, so they're visually identical. Text isn't individually editable in the pptx/Slides — if editability is a requirement, build a parallel python-pptx version with native text shapes.
