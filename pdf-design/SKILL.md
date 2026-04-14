---
name: pdf-design
description: Design and edit professional PDF reports and proposals with live preview
user_invocable: true
trigger_patterns:
  - "create.*report"
  - "create.*proposal"
  - "pdf.*report"
  - "funding.*proposal"
  - "design.*pdf"
  - "make.*proposal"
  - "edit.*report"
  - "preview.*report"
---

# PDF Design System

Create and edit professional PDF reports and funding proposals with live preview and iterative design.

## Interactive editing mode

During a design session, use these commands:

| Command | Action |
|---------|--------|
| `preview` | Screenshot current state |
| `preview page N` | Screenshot specific page |
| `show cover` | Preview cover page |
| `show budget` | Preview budget section |
| `regenerate` | Create new PDF |
| `upload` | Upload to Google Drive |
| `done` | Finish session |

**Workflow:**
1. You say "preview" → I show current state
2. You describe changes → I implement them
3. Repeat until done → Generate final PDF

---

## Quick start

```bash
# Copy template to start new report
cp ~/.claude/plugins/pdf-design/templates/democracy-day-proposal.html ./new-report.html

# Generate PDF (must use snap-accessible path)
mkdir -p ~/snap/chromium/common/pdf-work
cp new-report.html ~/snap/chromium/common/pdf-work/
chromium-browser --headless --disable-gpu \
  --print-to-pdf="$HOME/snap/chromium/common/pdf-work/output.pdf" \
  --no-pdf-header-footer \
  "file://$HOME/snap/chromium/common/pdf-work/new-report.html"
```

## Document types

- **Funding proposals** — Grant requests with budgets
- **Program reports** — Initiative updates
- **Impact reports** — Metrics and outcomes
- **Budget summaries** — Financial breakdowns

## Key principles

1. **Sentence case** — Never Title Case
2. **Left-aligned** — Never justified text
3. **Print-ready** — 8.5" × 11" letter size
4. **Brand consistent** — CCM red or program palettes

---

## Brand guidelines

### CCM standard colors
```css
:root {
    --ccm-red: #CA3553;
    --ccm-black: #000000;
    --ccm-gray: #666666;
    --ccm-light: #e2e8f0;
}
```

### Program-specific (Democracy Day)
```css
:root {
    --civic-navy: #1a2b4a;
    --civic-blue: #2d4a7c;
    --civic-gold: #c9a227;
    --civic-red: #b31942;
}
```

### Typography
```html
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&family=Source+Sans+Pro:wght@300;400;600&display=swap" rel="stylesheet">
```

```css
body {
    font-family: 'Source Sans Pro', sans-serif;
    font-size: 0.875rem;
    line-height: 1.6;
}

h1, h2, h3 {
    font-family: 'Montserrat', sans-serif;
}
```

---

## HTML structure

### Page setup
```css
@page { size: letter; margin: 0; }

.page {
    width: 8.5in;
    height: 11in;
    display: grid;
    grid-template-rows: auto 1fr auto;
    overflow: hidden;
    page-break-after: always;
}
```

### Cover page
```html
<div class="page cover">
    <div class="cover-header">
        <div class="cover-org">Center for Cooperative Media</div>
        <h1 class="cover-title">Report title</h1>
        <p class="cover-intro">Brief description.</p>
    </div>
    <div class="cover-footer">
        <div class="cover-stats"><!-- Stats --></div>
        <div class="cover-footer-right">
            <div class="cover-date">February 2026</div>
            <div class="cover-logo"><img src="..." alt="Logo"></div>
        </div>
    </div>
</div>
```

### Content page
```html
<div class="page content-page">
    <div class="page-header">
        <div class="page-header-title">Document title</div>
        <div class="page-number">2</div>
    </div>
    <div class="page-body">
        <!-- Content goes here -->
    </div>
    <footer class="page-footer">
        <!-- Footer -->
    </footer>
</div>
```

### Budget table
```html
<table class="budget-table">
    <thead>
        <tr><th>Expense</th><th>Per year</th><th>Total</th></tr>
    </thead>
    <tbody>
        <tr>
            <td>Item<span class="item-desc">Details</span></td>
            <td>$10,000</td>
            <td>$20,000</td>
        </tr>
    </tbody>
    <tfoot>
        <tr><td>Total</td><td>$50,000</td><td>$100,000</td></tr>
    </tfoot>
</table>
```

### Page footer
```css
.page-body {
    padding: 0.2in 0.65in 0.3in;
    overflow: hidden;
}

.page-footer {
    padding: 0 0.65in 0.5in;
    border-top: 1px solid #e2e8f0;
    font-size: 0.8rem;
}
```

---

## Footer clearance

Content must not touch or overlap the page footer. These rules apply to **content pages** — cover pages and special layouts may use different structures.

- Content pages must use `display: grid; grid-template-rows: auto 1fr auto` on `.page`
- Content pages must have exactly 3 direct children: header, content wrapper (`.page-body`), footer
- The content wrapper must have `overflow: hidden` to prevent text bleeding
- Never use `position: absolute` for footers — keep them in normal document flow as the third grid row
- Use `.page-footer:empty { display: none; }` so pages without footer content don't render a blank border
- If content is too long, reduce content rather than shrinking the footer gap

---

## PDF generation

### Chromium (snap-confined)
```bash
# Must use ~/snap/chromium/common/ path
mkdir -p ~/snap/chromium/common/pdf-work
cp template.html ~/snap/chromium/common/pdf-work/
chromium-browser --headless --disable-gpu \
  --print-to-pdf="$HOME/snap/chromium/common/pdf-work/output.pdf" \
  --no-pdf-header-footer \
  "file://$HOME/snap/chromium/common/pdf-work/template.html"
cp ~/snap/chromium/common/pdf-work/output.pdf ./
```

### Preview pages
```bash
# PDF to PNG
pdftoppm -png -f 1 -l 1 output.pdf preview

# Page count
pdfinfo output.pdf | grep Pages
```

### Legion browser preview
```bash
~/.claude/scripts/legion-browser.py screenshot "file:///path/to/template.html" -o preview.png
```

---

## Google Drive upload

```python
cd ~/.claude/workstation/mcp-servers/gmail && source .venv/bin/activate
python3 << 'PYEOF'
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import json

with open('/home/jamditis/.claude/google/drive-token.json') as f:
    token_data = json.load(f)

creds = Credentials(
    token=token_data['access_token'],
    refresh_token=token_data.get('refresh_token'),
    token_uri='https://oauth2.googleapis.com/token',
    client_id=token_data.get('client_id'),
    client_secret=token_data.get('client_secret')
)

service = build('drive', 'v3', credentials=creds)

# Upload new file
file_metadata = {
    'name': 'Report.pdf',
    'parents': ['1lKTdwq4_5uErj-tBN112WCdJGD2YtetO']  # Shared with Joe
}
media = MediaFileUpload('/path/to/output.pdf', mimetype='application/pdf')
file = service.files().create(body=file_metadata, media_body=media, fields='id,webViewLink').execute()
print(f"Uploaded: {file.get('webViewLink')}")
PYEOF
```

### Drive folders
- **Shared with Joe:** `1lKTdwq4_5uErj-tBN112WCdJGD2YtetO`
- **Claude Workspace:** `1e5dtKOiuvk0PPrFq3UyNI2UAa6RFiom3`

---

## Reusable content blocks

These patterns were proven out in the NJ Public TV walkthrough deck (pdf-playground 1.3.0) and work just as well inside report and proposal pages. Drop them into any `.page-body` or `.cover-footer`.

### Headline with red accent rule

A tight 0.95in × 0.08in red bar under the headline reads cleaner than a full-width border. Use for section headers inside content pages.

```css
.section-header h2 {
    font-family: 'Montserrat', sans-serif;
    font-size: 22pt;
    font-weight: 800;
    color: var(--ccm-black);
    line-height: 1.08;
}

.section-header h2::after {
    content: '';
    display: block;
    width: 0.95in;
    height: 0.08in;
    background: var(--ccm-red);
    margin-top: 0.14in;
}
```

### Stats strip (big-number row)

Row of 3–4 big numbers with a short caption and a red left rule. Great for executive-summary numbers on a cover or intro page.

```html
<div class="stats-strip">
    <div class="stat"><div class="big">23,000+</div><div class="label">Students enrolled</div></div>
    <div class="stat"><div class="big">$660M</div><div class="label">Annual operating budget</div></div>
    <div class="stat"><div class="big">$2.3B</div><div class="label">Economic impact</div></div>
    <div class="stat"><div class="big">252</div><div class="label">Acre main campus</div></div>
</div>
```

```css
.stats-strip {
    display: grid;
    grid-template-columns: repeat(var(--stat-cols, 4), 1fr);
    gap: 0.3in;
}
.stats-strip .stat {
    padding: 0.05in 0 0.1in 0.24in;
    border-left: 4px solid var(--ccm-red);
}
.stats-strip .big {
    font-family: 'Montserrat', sans-serif;
    font-size: 28pt;
    font-weight: 800;
    line-height: 1;
    color: var(--ccm-black);
    letter-spacing: -0.015em;
}
.stats-strip .label {
    font-size: 9pt;
    font-weight: 600;
    margin-top: 0.1in;
    color: var(--ccm-gray);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
```

### Three-column content

For breaking one topic into three parallel facets with a dashed divider between columns.

```css
.three-col {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 0.3in;
}
.three-col > div + div {
    padding-left: 0.3in;
    border-left: 2px dashed #d9d9d9;
}
.three-col h3 {
    font-size: 10pt;
    font-weight: 800;
    color: var(--ccm-red);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.12in;
}
```

### Four-tile pillars

Numbered cards with a red top rule — for parallel capabilities, themes, or commitments. Common on proposal executive summary pages.

```html
<div class="four-col-tiles">
    <div class="tile">
        <div class="tile-num">Pillar 01</div>
        <h3>Proven facilities and expertise</h3>
        <p>Short 2–3 line description.</p>
    </div>
    <!-- 3 more tiles -->
</div>
```

```css
.four-col-tiles {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.15in;
}
.four-col-tiles .tile {
    border-top: 4px solid var(--ccm-red);
    padding: 0.18in 0.15in 0.15in;
    background: #f7f6f5;
}
.four-col-tiles .tile-num {
    font-size: 8pt;
    font-weight: 800;
    color: var(--ccm-red);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.08in;
}
.four-col-tiles .tile h3 {
    font-size: 12pt;
    font-weight: 800;
    color: var(--ccm-black);
    margin-bottom: 0.08in;
}
.four-col-tiles .tile p {
    font-size: 9pt;
    line-height: 1.38;
    color: var(--ccm-gray);
    margin: 0;
}
```

### Partner / label grid

4-column grid of labeled tiles with a red left accent bar. Use for sponsor lists, letters of support, or advisory board rosters.

```css
.partner-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.12in 0.18in;
}
.partner-grid .partner {
    position: relative;
    padding: 0.14in 0.15in 0.14in 0.22in;
    background: #f7f6f5;
    font-size: 9pt;
    font-weight: 600;
    line-height: 1.25;
    color: var(--ccm-black);
}
.partner-grid .partner::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 0.06in;
    background: var(--ccm-red);
}
```

### Vertical rhythm

Every block above was tightened based on real presentation feedback. Key principles:

- Accent rule sits ~0.14in below the headline, not further
- Lede paragraph sits ~0.18in below the headline or rule
- Body content sits ~0.22in below the lede
- Between body sections, 0.25–0.3in gap is enough — don't add more
- Between grid cards, use 0.15–0.2in gaps
- The instinct to "add breathing room" almost always makes pages feel emptier rather than cleaner

If a page feels too crowded, *reduce content*, don't expand spacing.

---

## Known issues

1. **Base64 images** — Don't read HTML with large base64 using Read tool (API error). Use sed/grep/Python.
2. **Snap confinement** — Chromium can only write to `~/snap/chromium/common/`
3. **Fonts** — Google Fonts via CDN; for offline, embed as base64

## Logo locations

- CCM logo: `~/.claude/plugins/pdf-design/templates/` (embedded in template)
- Brand assets: `/home/jamditis/projects/cjs2026/public/internal/brand_web_assets/`

## Template

Reference: `~/.claude/plugins/pdf-design/templates/democracy-day-proposal.html`
