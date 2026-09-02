# End-to-end workflow

Use this sequence for every website picker project. The goal is not merely to generate three HTML pages. The goal is to create a fair, credible, client-usable design decision environment.

## Phase A: intake and evidence

1. Read the existing site, brief, attachments, and prior decisions.
2. Inventory factual content and source assets.
3. Identify the primary audience, decision, and conversion action.
4. Identify the most defensible differentiator or proof point.
5. Record uncertainties. Do not convert uncertainties into claims.
6. Confirm whether the final output is a local package, Cloudflare Drop ZIP, another static host, or a live deployment.

Recommended working notes:

```text
Audience:
Problem the site solves:
Primary promise:
Strongest evidence:
Required pages/sections:
Primary conversion:
Secondary conversion:
Provided assets:
Restrictions:
Unverified claims:
Hosting target:
```

## Phase B: content model

Build one canonical content outline before visual exploration. The three directions should use the same content facts, though order and emphasis can differ.

Minimum content model:

- identity and positioning
- audience-specific needs
- concrete services or offers
- inputs, process, and outputs
- proof, differentiator, product, or case study
- trust and risk reduction
- conversion path
- footer and contact information

Create concise copy. A design picker becomes less useful when one direction is visibly stronger only because it received better writing.

## Phase C: direction briefs

Write three one-page direction briefs. Each must answer:

- What strategic idea does this direction embody?
- What should a visitor feel within five seconds?
- What is the visual grammar?
- Where does the proof live?
- How is navigation handled?
- What is the interaction ceiling?
- What conventions does it reject?
- What kind of client would choose it?

Complete `DIRECTION-BRIEFS.md` and score every pair in `config/distinctness.json` before final packaging.

## Phase D: asset preparation

1. Preserve originals in a source directory.
2. Rename working copies with predictable lowercase names.
3. Optimize supplied video and create posters.
4. Extract or redraw only graphics that can be represented accurately.
5. Create favicon sets for the review shell and each direction.
6. Prepare an asset manifest before the asset page is built.

Never overwrite the only copy of an original asset.

## Phase E: standalone directions

Build each direction as its own HTML document and its own design system. Shared factual media may be referenced from a common assets directory, but direction styling must not leak through the parent picker.

A direction is ready only when it has enough sections to judge hierarchy, rhythm, proof, conversion, and responsive behavior.

## Phase F: picker and asset page

1. Generate the review shell from `config/directions.json`.
2. Load each direction in an iframe.
3. Add hash-based direct links and keyboard switching.
4. Add presentation mode and restore controls.
5. Generate the asset page from `config/assets.json`.
6. Expose every variant as a normal download and generate family/all-assets ZIPs in the browser.
7. Package a separate archival design-assets ZIP while keeping the Cloudflare Drop ZIP free of nested archives.

## Phase G: QA

Run both machine and visual checks:

- broken references and missing downloads
- HTML metadata and favicon declarations
- labels and alternative text
- desktop, tablet, and mobile overflow
- tab switching and URL hashes
- full-screen/presentation restore behavior
- video playback and inactive pausing
- asset downloads
- static hosting under a local HTTP server
- ZIP extraction and root structure
- anti-slop review
- factual claim review

Fix issues and repeat. Screenshots are evidence, not decoration.

## Phase H: delivery

Return clearly labeled files:

- combined review site or its ZIP
- Cloudflare Drop ZIP
- design-assets ZIP
- source-project ZIP
- website-design-handoff ZIP
- optional standalone HTML files
- optional screenshots and QA report

Do not call a local file a published site. Do not call an upload package a deployment.
