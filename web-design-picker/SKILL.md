---
name: web-design-picker
description: Use when creating distinct website directions, a client review picker, asset catalog, previews, and Cloudflare-ready handoffs.
license: MIT
compatibility: Python 3.10+. Build, validation, and packaging use the standard library. Scaffolding and favicon exports require Pillow and resvg-cli; screenshots require Playwright plus Chromium; video exports require ffmpeg. Generated sites are framework-free static files.
metadata:
  author: Joe Amditis
  version: "1.0.0"
  category: web-design
---

# Web design picker

Build a complete website-concept review package rather than isolated mockups. The default deliverable is three materially different, responsive website directions; a review shell that switches among them without losing the presentation context; a full-screen presentation mode; a searchable asset catalog with per-format, per-family, and download-all controls; two primary release archives; and supporting review, source, and full-handoff archives.

When invoked for an actual website project, perform the work. Do not stop at a strategy document unless the user asks only for strategy.

## Default output contract

Create:

1. Three standalone direction source pages in `src/concepts/`, built into `dist/concepts/`.
2. One generated review picker at `dist/index.html`.
3. One generated asset catalog at `dist/design-assets.html`.
4. Direction-specific logos, favicons, palettes, design tokens, and supporting graphic elements.
5. Optimized client media when source video or animation is supplied.
6. Desktop and mobile preview images when browser automation is available.
7. A lean static deployment ZIP with `index.html` at its root.
8. A separate complete design-assets handoff ZIP.
9. A machine-readable and human-readable QA report.

Use `scripts/web_design_picker.py` as the unified command-line entry point for scaffolding, building, validating, browser-testing, and packaging. Read [the workflow reference](references/workflow.md) before beginning a full project.

## Non-negotiable rules

- Build three distinct design theses, not one template with three palettes.
- Each direction must differ in information architecture, typography, spacing, geometry, media treatment, interaction, and emotional register.
- Keep each concept independently usable as a static page with its own title, viewport metadata, favicon, accessible navigation, and responsive layout.
- Use real supplied content and media as evidence. Do not invent capabilities, clients, metrics, certifications, software compatibility, or testimonials.
- Treat trademarks and product names accurately. Never imply an affiliation that does not exist.
- Do not use stock imagery merely to fill a composition. Prefer client assets, purposeful diagrams, custom vector elements, crops of real work, or restrained typography.
- Avoid generic AI-site styling. Apply [the anti-slop guardrails](references/anti-slop-guardrails.md) and run `scripts/slop_lint.py` before packaging.
- Do not make a fake contact flow. A prototype form may download a structured brief or clearly state that submission is not connected. Production submission requires a real endpoint.
- Do not bundle font files for handoff unless the user owns redistribution rights. Prefer system fonts, licensed web delivery, or outlined logo artwork.
- Every direction and the review shell must include a favicon set.
- Preserve reduced-motion preferences and keyboard operation.
- Do not place a wrapper folder inside the Cloudflare Drop ZIP. The first archive entry must be `index.html`.
- Keep the deployment ZIP lean. Do not place the complete handoff ZIP inside it. The asset page should assemble ZIP downloads client-side from individual static files.

## Workflow

### 1. Ingest and establish truth

Inspect the current site, supplied files, brand material, screenshots, source copy, and media. Extract:

- audiences and jobs-to-be-done;
- actual services or products;
- strongest proof and differentiators;
- current conversion path;
- factual constraints and unknowns;
- required legal, trademark, privacy, accessibility, or geographic language;
- reusable and missing assets.

Create a concise source-of-truth brief. Mark every assumption that needs confirmation, but continue with a defensible prototype when the answer is not necessary to build it.

### 2. Define three orthogonal directions

For each direction, write a short thesis containing:

- the perception it should create;
- the primary audience or buying concern it prioritizes;
- its information architecture;
- its typographic and spatial system;
- its media strategy;
- its interaction idea;
- the deliberate tradeoff it makes.

Use [the direction strategy rubric](references/direction-strategy.md). Reject a set when two directions could be made equivalent by changing only colors, fonts, or border radius.

### 3. Design content before decoration

Write a shared factual content model, then decide how each direction edits, sequences, and frames it. A design direction may emphasize different content, but factual claims must stay consistent.

Prefer concrete language: inputs, outputs, process, deliverables, evidence, constraints, next action. Remove boilerplate such as “bringing visions to life,” “innovative solutions,” or “trusted partner” unless the organization has specific evidence supporting it.

### 4. Build the standalone concepts

Create complete responsive HTML pages. Inline CSS and lightweight JavaScript are acceptable; local assets should use relative paths. Each page must:

- have a recognizable opening composition rather than a generic hero-card stack;
- include real sections with meaningful transitions and hierarchy;
- make the differentiator prominent rather than burying it in a service grid;
- use interaction sparingly and purposefully;
- include labeled form controls when a form is shown;
- provide an honest prototype behavior;
- work at approximately 390 px, 768 px, 1280 px, and 1440 px widths;
- include a direction-specific favicon.

Do at least three passes: content accuracy, visual distinctiveness, and responsive/alignment polish. Then run the anti-slop review.

### 5. Build the asset system

For every direction, export the useful design ingredients, not just screenshots:

- primary mark and monochrome mark;
- horizontal lockup when applicable;
- editable SVG and transparent PNG versions;
- favicon SVG, ICO, 32 px, 180 px, 192 px, and 512 px exports;
- palette sheet plus CSS and JSON tokens;
- reusable diagrams, patterns, frames, rules, arrows, icons, or interface graphics;
- poster images and web media derivatives;
- notes identifying concept-only marks, licensing limits, or trademark constraints.

Record assets in `config/assets.json`. Follow [the asset catalog and handoff specification](references/asset-catalog-and-handoff.md).

### 6. Optimize media

When video is supplied, inspect representative frames and preserve the content that proves the claim. Create an H.264 MP4 with `faststart`, a WebM when useful, at least one poster frame, and only a short GIF fallback when it has a real presentation use.

Run:

```bash
python scripts/optimize_video.py INPUT.mp4 OUTPUT_DIR --name demo --width 1280 --fps 24 --poster-times 1.5 --gif
```

Read [the media and favicon reference](references/media-and-favicons.md) for defaults and exceptions.

### 7. Generate the picker and asset page

Initialize or adapt a project:

```bash
python scripts/web_design_picker.py init PROJECT_DIR --name "Client website directions" --slug client-site
```

Replace the starter concepts and assets, update `config/project.json`, `config/directions.json`, and `config/assets.json`, then run:

```bash
python scripts/web_design_picker.py build PROJECT_DIR
```

The generated picker must provide:

- persistent direction tabs;
- accessible tab semantics and live status text;
- URL hash state;
- left/right arrow and number-key switching;
- a full-screen presentation mode with a visible restoration control;
- a current-direction standalone link;
- a direct path to the asset catalog;
- iframe isolation so each design can have an independent CSS system.

The asset catalog must provide:

- grouped, full-width asset rows rather than a bento dashboard;
- a usable preview for visual assets;
- direct downloads for every listed variant;
- a client-side ZIP for each multi-file asset family;
- a client-side ZIP containing all cataloged assets;
- search and format/group filters when the asset count warrants them;
- production, licensing, trademark, and concept-status notes.

### 8. Validate and render

Run:

```bash
python scripts/web_design_picker.py validate PROJECT_DIR --strict
python scripts/web_design_picker.py preview PROJECT_DIR --test-downloads
```

Treat missing files, missing root `index.html`, broken local references, missing favicons, unlabeled controls, unsafe archive paths, nested archives, and oversized deployment assets as release blockers. Treat heuristic slop findings as design-review prompts, not automatic proof of a defect.

### 9. Package the release and handoff archives

Run:

```bash
python scripts/web_design_picker.py package PROJECT_DIR
```

Produce:

- `PROJECT_SLUG-cloudflare-drop.zip`: only deployable static files, with `index.html` at the archive root and no enclosing folder or nested ZIP.
- `PROJECT_SLUG-design-assets.zip`: the full editable/raster asset handoff, manifest, tokens, notes, and source derivatives.
- `PROJECT_SLUG-review-site.zip`: the review site with its downloadable assets.
- `PROJECT_SLUG-source-project.zip`: the editable source project and configuration.
- `PROJECT_SLUG-website-design-handoff.zip`: the full review, source, QA, and delivery bundle.

Follow [the QA and Cloudflare Drop checklist](references/qa-and-cloudflare-drop.md). Never tell the user a site has been deployed when only a ZIP was created.

### 10. Deliver clearly

Give the user direct links to:

- the Cloudflare Drop ZIP;
- the separate design-assets ZIP;
- the QA report;
- the review `index.html` when local artifact linking is available;
- optional preview screenshots.

State what is functional, what is prototype-only, and what still requires a production backend or owner confirmation.

## Tool map

- `scripts/web_design_picker.py`: unified entry point for `init`, `build`, `validate`, `preview`, `package`, `run`, and `self-test`.
- `scripts/new_project.py`: scaffold a two-to-five-direction project, three by default.
- `scripts/build_picker.py`: build the review picker, standalone concepts, and asset catalog.
- `scripts/run_factory.py`: run the end-to-end build, validation, browser QA, and packaging pipeline.
- `scripts/optimize_video.py`: produce MP4, WebM, poster, and optional GIF derivatives.
- `scripts/make_favicons.py`: generate a complete favicon set from an SVG or PNG.
- `scripts/make_asset_variants.py`: export raster variants while preserving the editable vector.
- `scripts/make_palette.py`: create palette sheets plus CSS and JSON tokens.
- `scripts/browser_qa.py`: serve the build locally, test interactions and downloads, and capture desktop/mobile screenshots.
- `scripts/check_distinctness.py`: enforce material separation among design directions.
- `scripts/validate_site.py`: inspect static references, metadata, accessibility basics, and Drop constraints.
- `scripts/package_delivery.py`: create deterministic Cloudflare Drop, review, source, asset, and full-handoff archives.
- `scripts/slop_lint.py`: flag common generic AI-site patterns for human review.
- `scripts/validate_skill.py`: validate this skill’s directory and `SKILL.md` metadata.

## Reference loading guide

Read only what the project needs:

- Full project process: [workflow](references/workflow.md)
- Making the three concepts genuinely different: [direction strategy](references/direction-strategy.md)
- Avoiding generic AI design tells: [anti-slop guardrails](references/anti-slop-guardrails.md)
- Catalog structure and export naming: [asset catalog and handoff](references/asset-catalog-and-handoff.md)
- Video and favicon production: [media and favicons](references/media-and-favicons.md)
- Release validation and Drop packaging: [QA and Cloudflare Drop](references/qa-and-cloudflare-drop.md)
- Example prompts and invocation patterns: [examples](examples/prompts.md)
