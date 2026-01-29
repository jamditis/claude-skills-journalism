---
name: accessibility-check
description: Check for alt text, heading structure, and accessibility in content
event: PostToolUse
tools: [Write, Edit]
---

# Accessibility check hook

After writing content, check for accessibility issues that would exclude readers with disabilities.

## When this hook fires

- After `Write` tool creates content with images or complex structure
- After `Edit` tool adds media or formatting
- When content includes HTML, Markdown with images, or data visualizations

## What to check

### Images without alt text

```markdown
❌ ![](image.jpg)
❌ <img src="photo.jpg">

✅ ![Mayor Smith speaks at podium during press conference](image.jpg)
✅ <img src="photo.jpg" alt="Chart showing crime rates declining 15% from 2020 to 2024">
```

### Decorative images not marked

```markdown
✅ ![](decorative-border.png){aria-hidden="true"}
✅ <img src="icon.svg" alt="" role="presentation">
```

### Heading hierarchy

```markdown
❌ # Title
    ### Skipped to h3
    ## Then h2

✅ # Title
    ## Section
    ### Subsection
```

### Link text

```markdown
❌ Click [here](url) to read more
❌ [Read more](url)

✅ Read the [full report on housing costs](url)
✅ [Housing cost report (PDF, 2.3MB)](url)
```

### Color-only information

```
⚠️ Chart uses only color to distinguish categories
   Add: Pattern, label, or shape differentiation
```

### Data tables

```markdown
❌ | | Column A | Column B |
   |---|---|---|

✅ | Category | 2023 | 2024 |
   |---|---|---|
   With proper headers and scope
```

## Accessibility checklist

```
📋 Accessibility checklist:

Images:
- [ ] All images have descriptive alt text
- [ ] Alt text describes content, not just "image of..."
- [ ] Decorative images marked as such
- [ ] Complex images (charts) have detailed descriptions

Structure:
- [ ] Headings follow logical hierarchy (h1 → h2 → h3)
- [ ] No heading levels skipped
- [ ] Content readable without styles

Links:
- [ ] Link text describes destination
- [ ] No "click here" or "read more" alone
- [ ] File type/size noted for downloads

Media:
- [ ] Videos have captions
- [ ] Audio has transcript
- [ ] Auto-play disabled or controllable

Data:
- [ ] Tables have proper headers
- [ ] Charts don't rely only on color
- [ ] Data available in text form
```

## Output format

```
⚠️ Accessibility check:

Issues found:
- Line [X]: Image missing alt text
- Line [X]: Heading jumps from h1 to h3
- Line [X]: Link text "click here" is not descriptive

Accessibility ensures all readers can access your journalism.
```

## Alt text guidance

Good alt text for journalism:

| Image type | Alt text approach |
|------------|-------------------|
| News photo | Describe key action, people, context |
| Headshot | "Name, title" or "Name speaking at event" |
| Chart | Summarize the main finding |
| Map | Describe what it shows and key locations |
| Document | "Screenshot of [document] showing [key info]" |

**Example:**
```markdown
![Protesters march down Main Street holding signs that read "Save Our Schools" as police officers watch from the sidewalk](protest.jpg)
```

## Non-blocking

This hook flags issues but doesn't prevent publication. Prioritize fixes based on impact—missing alt text on key images is more critical than minor heading issues.

## Skip conditions

Skip for:
- Plain text files without markup
- Code files
- Internal notes/drafts
