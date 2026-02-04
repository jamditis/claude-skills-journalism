# PDF Playground

A Claude Code plugin for creating professional, print-ready HTML documents that export to PDF. Designed for newsrooms, nonprofits, and organizations that need to create proposals, reports, one-pagers, newsletters, slides, and event materials.

**Fully customizable** — configure your organization's colors, fonts, and branding once, then generate on-brand documents every time.

## Features

- **6 document types**: Proposals, reports, one-pagers, newsletters, slides, event materials
- **Customizable branding**: Set your colors, fonts, and organization info in one config file
- **Print-ready output**: Proper @page CSS for 8.5" × 11" letter size
- **Interactive preview**: Live browser preview with Playwright for iterative design
- **Pre-built templates**: Start from polished templates, customize content

## Quick start

### 1. Install the plugin

```bash
# Add the marketplace
claude plugin marketplace add https://github.com/jamditis/claude-skills-journalism

# Install the plugin
claude plugin install pdf-playground@claude-skills-journalism

# Restart Claude Code to load the plugin
```

### 2. Configure your brand

Create a brand configuration file at `.claude/pdf-playground.local.md`:

```yaml
---
brand:
  name: "Your Organization"
  tagline: "Your tagline or mission"
  website: "https://yourorg.com"
  email: "contact@yourorg.com"

colors:
  primary: "#CA3553"      # Main accent color
  secondary: "#000000"    # Secondary color (usually black)
  background: "#FFFFFF"   # Page background
  text: "#2d2a28"        # Body text color
  muted: "#666666"       # Secondary text color

fonts:
  heading: "Playfair Display"  # Google Font name for headings
  body: "Source Sans 3"        # Google Font name for body text

style:
  headingCase: "sentence"      # "sentence" or "title"
  useOxfordComma: true
---

# Additional brand notes

Add any specific brand guidelines or notes here that Claude should follow when creating documents.
```

### 3. Create documents

| Command | Description |
|---------|-------------|
| `/pdf-playground:proposal` | Multi-page funding proposals with budgets |
| `/pdf-playground:report` | Program reports and annual reports |
| `/pdf-playground:onepager` | Single-page fact sheets |
| `/pdf-playground:newsletter` | HTML email newsletters |
| `/pdf-playground:slides` | HTML presentation slides |
| `/pdf-playground:event` | Flyers, posters, event materials |
| `/pdf-playground:preview` | Interactive browser preview |

### 4. Export to PDF

1. Open the HTML file in Chrome
2. Press Ctrl+P (or Cmd+P on Mac)
3. Set "Destination" to "Save as PDF"
4. Set "Margins" to "None"
5. Enable "Background graphics"
6. Save

## Example brand configurations

### Minimal config

```yaml
---
brand:
  name: "My Newsroom"
colors:
  primary: "#0066CC"
---
```

### Full config with custom fonts

```yaml
---
brand:
  name: "Local News Co"
  tagline: "Covering our community since 1952"
  website: "https://localnews.co"
  email: "editor@localnews.co"

colors:
  primary: "#1a5f7a"
  secondary: "#002b36"
  accent: "#cb4b16"
  background: "#fdf6e3"
  text: "#073642"
  muted: "#586e75"

fonts:
  heading: "Merriweather"
  body: "Open Sans"

style:
  headingCase: "sentence"
  useOxfordComma: true
---

## Brand notes

- Always use our tagline on cover pages
- Include our founding year (1952) when space allows
- Prefer action verbs in headlines
```

## Document types

### Proposals (`/pdf-playground:proposal`)

Multi-page funding proposals with:
- Cover page with organization branding
- Background/context sections
- Proposed work with numbered priorities
- Case studies and evidence
- Budget tables with totals
- Contact information

### Reports (`/pdf-playground:report`)

Program reports and annual reports with:
- Branded cover page
- Executive summary with key metrics
- Detailed findings sections
- Pull quotes and testimonials
- Data visualizations

### One-pagers (`/pdf-playground:onepager`)

Single-page fact sheets with:
- Header with organization branding
- Two-column layout (main content + sidebar)
- Key highlights as bullet points
- Quick facts and statistics
- Contact information and CTA

### Newsletters (`/pdf-playground:newsletter`)

HTML email newsletters with:
- Email-safe table-based layout
- Featured article section
- News item listings
- Upcoming events
- Social links and footer

### Slides (`/pdf-playground:slides`)

HTML presentation slides with:
- Title slides
- Section dividers
- Content slides with bullets
- Two-column layouts
- Quote slides
- Big stat slides
- End slide with contact info

### Event materials (`/pdf-playground:event`)

Flyers and posters with:
- Bold event title
- Date, time, location details
- Event description
- Highlights/features
- Registration CTA
- QR code placeholder

## Templates

Templates are stored in `${CLAUDE_PLUGIN_ROOT}/templates/`:

- `proposal-template.html`
- `report-template.html`
- `onepager-template.html`
- `newsletter-template.html`
- `slides-template.html`
- `event-template.html`

## Requirements

- **Claude Code** with plugin support
- **Playwright plugin** (optional, for browser preview)
- **Google Fonts access** for custom typography

## Credits

Created by [Joe Amditis](https://github.com/jamditis) at the [Center for Cooperative Media](https://centerforcooperativemedia.org), Montclair State University.

Based on real-world document production workflows used for grant proposals, program reports, and newsroom communications.

## License

MIT License - Use freely, attribution appreciated.
