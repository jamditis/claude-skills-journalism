# Handoff note: Skill pages creation

## Current status

**Completed:** 7 flagship skill pages with rich design matching the pdf-playground template exactly:
1. `docs/pdf-playground/index.html` - Original template (red accent)
2. `docs/foia-requests/index.html` - Purple accent (#7c3aed)
3. `docs/vibe-coding/index.html` - Indigo accent (#4f46e5)
4. `docs/project-retrospective/index.html` - Orange accent (#d97706)
5. `docs/ai-writing-detox/index.html` - Slate accent (#475569)
6. `docs/accessibility-compliance/index.html` - Cyan accent (#0891b2)
7. `docs/source-verification/index.html` - May need review (noted as having simpler issues)
8. `docs/data-journalism/index.html` - May need review (noted as having simpler issues)

**Pending:** Create pages for remaining ~25 non-featured skills

---

## What needs to be done

Create individual GitHub Pages for each remaining skill. These can be **simpler template pages** (not the full flagship treatment) but should still look professional and consistent.

### Skills needing pages

Check the skill directories in the repo root to find all skills. Featured skills (already done) are listed in the main site's "Featured skills" section. Everything else needs a simpler page.

Skill directories are at: `C:\Users\Joe Amditis\Desktop\Crimes\sandbox\claude-skills-journalism\`

Each skill has a `SKILL.md` file with the content to use.

---

## Template details (for reference)

### Flagship template key elements

- **Fonts:** Fraunces (display) + Plus Jakarta Sans (body)
- **Background:** Canvas #ede6d4
- **Paper overlay:** Natural paper texture + radial gradient, opacity 0.5
- **Hero:** SVG grid pattern (40x40) + linear-gradient with accent colors
- **Cards:** White bg, subtle border, hover lift effect
- **Dark sections:** bg-ink #121212
- **Nav:** Fixed, backdrop-blur-md, bg-canvas/90

### Simpler template suggestion

For non-featured skills, consider a lighter version:
- Same fonts and canvas background
- Paper overlay
- Simpler hero (just gradient, no SVG grid)
- Basic content sections without all the fancy cards
- Footer with link back to main site

---

## File structure

```
docs/
├── index.html                    # Main site
├── pdf-playground/index.html     # Template reference
├── foia-requests/index.html      # ✅ Complete
├── vibe-coding/index.html        # ✅ Complete
├── project-retrospective/        # ✅ Complete
├── ai-writing-detox/             # ✅ Complete
├── accessibility-compliance/     # ✅ Complete
├── source-verification/          # May need review
├── data-journalism/              # May need review
└── [remaining-skills]/           # TO CREATE
```

---

## Key files to read

1. `docs/pdf-playground/index.html` - The canonical template
2. Any skill's `SKILL.md` - Content source for each page
3. `docs/index.html` - Main site, shows which skills are featured

---

## Git info

- Repo: `claude-skills-journalism`
- Branch: `master`
- Last commit: 03ac2b2 "Rewrite 5 flagship skill pages to match pdf-playground template"
- Remote is up to date

---

## Suggested next steps

1. List all skill directories in the repo
2. Compare against `docs/` to find which skills don't have pages yet
3. Create a simpler template for non-featured skills
4. Generate pages for all remaining skills
5. Push changes

---

*Created: 2026-02-04*
