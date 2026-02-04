---
description: Create an HTML email newsletter with your organization's branding
argument-hint: [newsletter-name]
allowed-tools: Read, Write, Edit, Glob, mcp__plugin_playwright_playwright__*
---

Create an HTML email newsletter.

## Setup

1. Check for brand configuration at `.claude/pdf-playground.local.md`
2. If found, parse the YAML frontmatter for brand settings
3. Load the newsletter template from `${CLAUDE_PLUGIN_ROOT}/templates/newsletter-template.html`

## Email constraints

HTML emails have special requirements:
- Use tables for layout (not CSS grid/flexbox)
- Inline CSS styles
- Max width: 600px
- Web-safe fonts with fallbacks
- Alt text for all images

## Document structure

**Header:**
- Organization logo centered
- Newsletter title/date
- View in browser link (placeholder)

**Content:**
- Featured story with image placeholder
- News items (headline + excerpt + link)
- Upcoming events
- Quick links
- CTA button

**Footer:**
- Social media links
- Unsubscribe link (placeholder)
- Organization address
- Copyright

## Brand application

- Use brand primary color for headers and buttons
- Apply brand secondary color for text
- Use brand fonts with web-safe fallbacks

## Newsletter name

The newsletter name is: $ARGUMENTS

If not provided, ask for:
- Newsletter title or edition
- Featured content
- Number of news items
- Any events to highlight

## Output

Save HTML file in current working directory.
Note: Test in email clients before sending.
