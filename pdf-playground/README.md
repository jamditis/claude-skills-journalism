# PDF Playground

A Claude Code plugin for creating professional, print-ready documents. Designed for newsrooms, nonprofits, and organizations that need proposals, reports, one-pagers, newsletters, slides, and event materials.

Configure your organization's colors, fonts, and branding once, then generate on-brand documents every time.

## Before you start

You need **Claude Code** installed and working on your computer. Claude Code is a command-line tool made by Anthropic — it runs inside your terminal (the black window where you type commands).

**Not sure if you have it?** Open your terminal and type:

```
claude --version
```

If you see a version number, you're good. If you get an error like "command not found," you need to install Claude Code first: [Install Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview)

## Setup (one time)

### Step 1: Add the plugin source

Open your terminal and run this command exactly as shown:

```
claude plugin marketplace add https://github.com/jamditis/claude-skills-journalism
```

**What this does:** It tells Claude Code where to find this plugin. You only need to do this once. Think of it like adding a new app store to your phone.

**If you get an error:**
- Make sure you're connected to the internet
- Make sure you typed the URL exactly — no extra spaces, no missing letters
- Try running `claude --version` to confirm Claude Code is installed

### Step 2: Install the plugin

```
claude plugin install pdf-playground@claude-skills-journalism
```

**What this does:** It downloads and installs the PDF Playground plugin.

**If you get an error:**
- Make sure step 1 completed without errors first
- The part before the `@` is the plugin name (`pdf-playground`), and the part after is the source (`claude-skills-journalism`). Type the whole thing as one word with no spaces.

### Step 3: Restart Claude Code

Close your Claude Code session and open a new one. The plugin loads when Claude Code starts, so you need a fresh session for it to appear.

That's it — you can start creating documents now. Brand customization (below) is optional.

---

## Updating

To get the latest features and fixes:

```
claude plugin update pdf-playground@claude-skills-journalism
```

Then restart Claude Code (close and reopen).

You can also run `/pdf-playground:update` inside Claude Code to check your version and update automatically.

### How to tell if you need an update

If you see any of these, you probably need to update:
- The preview opens without a control panel sidebar
- Commands reference features that don't seem to work
- Claude mentions your plugin version is outdated

---

## Creating documents

Once the plugin is installed, open Claude Code and type any of these commands:

| Command | What it creates |
|---------|-----------------|
| `/pdf-playground:proposal` | Multi-page funding proposal with budget tables |
| `/pdf-playground:report` | Program report or annual report |
| `/pdf-playground:onepager` | Single-page fact sheet or program overview |
| `/pdf-playground:newsletter` | HTML email newsletter |
| `/pdf-playground:slides` | Presentation slides |
| `/pdf-playground:event` | Event flyer, poster, or signage |
| `/pdf-playground:preview` | Open a live preview in your browser to make changes interactively |

After Claude generates your document, it saves an HTML file in your current folder. To turn it into a PDF:

1. Open the HTML file in Chrome (or any Chromium-based browser)
2. Press **Ctrl+P** (Windows/Linux) or **Cmd+P** (Mac)
3. Set "Destination" to **Save as PDF**
4. Set "Margins" to **None**
5. Check the **Background graphics** box
6. Click **Save**

---

## Guided wizard (proposals)

The proposal command (`/pdf-playground:proposal`) includes a step-by-step wizard that walks you through setup:

**Phase 1 — Content:** Choose the proposal type, sections to include, page count, and budget line items. Each question appears as a multiple-choice prompt you can click through.

**Phase 2 — Design:** Pick a color scheme, typography style, and visual style. Presets are available (brand colors, professional blue, bold red/black) or go fully custom.

**Phase 3 — Review:** The proposal generates and opens in a live preview with an interactive control panel on the right side. You can tweak colors, fonts, spacing, and toggle sections on or off in real time. Click "Copy all changes" in the panel, paste the prompt back into the conversation, and the changes get applied to the HTML source.

**Phase 4 — Finalization:** Save the file, get PDF export instructions, or go back for more tweaks.

The wizard is currently available for proposals. Other templates will get wizard support in future updates.

---

## Interactive control panel

When you use `/pdf-playground:preview` to open a document, a wrapper page opens with your document in an iframe on the left and a control panel sidebar on the right. The panel includes:

- **Presets** — One-click theme buttons (CCM brand, Professional blue, Modern green, Warm earth, Elegant purple) that apply coordinated colors and fonts
- **Colors** — Color pickers for all CSS variables (primary, dark, text, background, accent)
- **Typography** — Font dropdowns (heading and body) with Google Fonts, plus sliders for body size, heading scale, and line height
- **Spacing** — Slider for page padding
- **Sections** — Toggles to show or hide individual content blocks (stat grid, case studies, budget table, etc.)
- **Layout** — Button groups for stat columns, dropdown for heading case
- **Undo/Redo** — Step backward and forward through your changes

Every change you make applies instantly in the preview. A "Pending changes" list at the bottom tracks your adjustments. When you're ready, click **Copy changes** — it puts a formatted prompt on your clipboard that you can paste back into the conversation. Claude applies those changes to the actual HTML source file.

The panel collapses to a thin sidebar tab when you don't need it. It's hidden during print, so it won't appear if you print to PDF. Your document HTML stays completely unchanged — the controls live in the wrapper page, separate from your document.

### Adding control panel support for other templates

The control panel is driven by template maps — data files that describe which CSS variables, selectors, and sections exist in each template. Currently only the proposal template has a map. To add support for another template, create a new map file in `controls/template-maps/`. See the README in that directory for the format.

---

## Customizing your brand (optional)

By default, PDF Playground uses generic styling. To use your organization's colors, fonts, and name, you create a small config file.

### Where the config file goes

The file goes inside a hidden folder called `.claude` in your **home directory**. Your home directory is:

- **Mac/Linux:** `/Users/yourname/` (or `~/`)
- **Windows:** `C:\Users\yourname\`

The full path for the config file is:

```
~/.claude/pdf-playground.local.md
```

### How to create the config file

**Option A — Let Claude do it:** Inside Claude Code, just say:

> "Create a brand config for PDF Playground. My organization is called [your org name] and our main color is [your color]."

Claude will create the file in the right place.

**Option B — Create it yourself:** Open a text editor (VS Code, Notepad, TextEdit, nano — any editor works) and create a new file at `~/.claude/pdf-playground.local.md` with this content:

```yaml
---
brand:
  name: "Your Organization Name Here"
colors:
  primary: "#0066CC"
---
```

Replace `Your Organization Name Here` with your actual organization name. Replace `#0066CC` with your brand's main color (any hex color code works — google "hex color picker" if you're not sure what yours is).

**That's the minimum config. Everything else is optional.** The two lines above (`name` and `primary` color) are enough to get branded documents.

### Full config (all options)

If you want more control, here's every option available. Only include the lines you want to customize — you can leave out anything you don't need:

```yaml
---
brand:
  name: "Your Organization Name Here"
  tagline: "Your tagline or mission statement"
  website: "https://your-website.com"
  email: "contact@your-website.com"

colors:
  primary: "#1a5f7a"       # Your main brand color (buttons, headings, accents)
  secondary: "#002b36"     # A second color if you have one (usually darker)
  accent: "#cb4b16"        # An accent color for highlights (optional)
  background: "#FFFFFF"    # Page background (usually white)
  text: "#2d2a28"          # Body text color (usually near-black)
  muted: "#666666"         # Color for less important text (usually gray)

fonts:
  heading: "Merriweather"  # Font for headings (any Google Font name)
  body: "Open Sans"        # Font for body text (any Google Font name)

style:
  headingCase: "sentence"  # "sentence" (only first word capitalized) or "title" (Each Word Capitalized)
  useOxfordComma: true     # true or false
---

## Brand notes

Add any specific guidelines here, like:
- Always include our tagline on cover pages
- Use action verbs in headlines
- Our fiscal year runs July–June
```

**What to customize vs. what to leave alone:**

| Part | Customize it? | How |
|------|---------------|-----|
| `brand: name:` | **Yes** — put your org's name | Replace the text in quotes |
| `colors: primary:` | **Yes** — put your brand color | Replace the hex code (e.g., `"#FF5733"`) |
| Everything else | **Only if you want to** | Replace the example values with your own, or delete lines you don't need |
| The `---` lines | **No — don't change these** | They mark the beginning and end of the config section |
| The words before the colons (`brand:`, `colors:`, `fonts:`, etc.) | **No — don't change these** | They're field names that the plugin looks for |

---

## What each document type includes

### Proposals (`/pdf-playground:proposal`)

- Cover page with your branding
- Background and context sections
- Proposed work with numbered priorities
- Case studies and evidence
- Budget tables with totals
- Contact information

### Reports (`/pdf-playground:report`)

- Branded cover page
- Executive summary with key metrics
- Detailed findings
- Pull quotes and testimonials
- Data visualizations

### One-pagers (`/pdf-playground:onepager`)

- Header with your branding
- Two-column layout (main content + sidebar)
- Key highlights as bullet points
- Quick facts and statistics
- Contact info and call to action

### Newsletters (`/pdf-playground:newsletter`)

- Email-safe table-based layout
- Featured article section
- News item listings
- Upcoming events
- Social links and footer

### Slides (`/pdf-playground:slides`)

- Title slides
- Section dividers
- Content slides with bullets
- Two-column layouts
- Quote slides and big stat slides
- End slide with contact info

### Event materials (`/pdf-playground:event`)

- Bold event title
- Date, time, and location
- Event description and highlights
- Registration call to action
- QR code placeholder

---

## Troubleshooting

### "command not found" when running `claude`

Claude Code isn't installed. Follow the [installation guide](https://docs.anthropic.com/en/docs/claude-code/overview).

### Plugin install command fails

Try each step in order:
1. Run `claude --version` to confirm Claude Code is working
2. Run the marketplace add command from Step 1 again
3. Run the install command from Step 2 again
4. If it still fails, check that you have internet access and that the URL is typed correctly

### Plugin installed but commands don't work

Did you restart Claude Code after installing? Close your session and open a new one. The plugin loads at startup.

### Documents look unstyled or generic

The brand config file might be in the wrong place or have a formatting error. The easiest fix: inside Claude Code, say "Create a brand config for PDF Playground for [your org name]" and let Claude create it for you.

### "Playwright" errors when using preview

The preview feature (`/pdf-playground:preview`) requires the Playwright plugin for Claude Code. If you don't have it, skip the preview and just open the HTML file directly in your browser.

---

## Credits

Created by [Joe Amditis](https://github.com/jamditis) at the [Center for Cooperative Media](https://centerforcooperativemedia.org), Montclair State University.

## License

MIT License — use freely, attribution appreciated.
