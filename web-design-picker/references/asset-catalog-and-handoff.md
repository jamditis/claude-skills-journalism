# Asset catalog and handoff specification

## Asset taxonomy

Organize assets by direction and function:

```text
site/assets/
├── brand/                         # neutral review-shell identity
├── direction-a/
│   ├── logos/
│   ├── favicons/
│   ├── palettes/
│   ├── graphics/
│   └── previews/
├── direction-b/
├── direction-c/
└── shared/
    ├── media/
    └── documents/
```

The handoff may use a more descriptive hierarchy, but manifest paths must remain valid relative to `site/`.

## Naming

Use lowercase kebab-case filenames. Include meaning before format or size:

- `primary-mark.svg`
- `primary-mark-512.png`
- `horizontal-lockup-outlined.svg`
- `favicon-180.png`
- `palette.css`
- `palette.json`
- `clash-detection-workflow.svg`
- `software-demo-poster-overview.jpg`

Do not name deliverables `final-final`, `new-logo`, `asset-1`, or `image-copy-2`.

## Required favicon family

For each direction:

- `favicon.svg`
- `favicon.ico`
- `favicon-32.png`
- `favicon-180.png`
- `favicon-192.png`
- `favicon-512.png`

The standalone page should reference the SVG, ICO fallback, and touch icon.

## Logo exports

When a direction includes a proposed mark, export:

- editable SVG;
- outlined SVG when text is present and outlines can be produced safely;
- transparent PNG at 512 px for a mark;
- PNG at 1600–2400 px wide for a horizontal lockup;
- monochrome variant;
- light/dark variants only when the system actually requires them.

Label concept marks as concept work and do not imply trademark clearance.

## Palette and token exports

Export:

- visual palette sheet in SVG and PNG;
- CSS custom properties;
- JSON token file;
- notes on semantic use, not only hex values.

Example:

```css
:root {
  --color-ink: #111315;
  --color-surface: #f4f3ed;
  --color-accent: #e45535;
  --color-line: #8b8f90;
}
```

## Manifest schema

`config/assets.json` is the source for the generated catalog. Paths are relative to the built site root:

```json
{
  "shared": [
    {
      "title": "Shared software demonstration",
      "description": "Media used across directions.",
      "preview": "assets/design-package/media/web/demo-poster.jpg",
      "poster": "assets/design-package/media/web/demo-poster.jpg",
      "files": [
        {"label": "MP4", "href": "assets/design-package/media/web/demo.mp4", "format": "MP4"},
        {"label": "Poster", "href": "assets/design-package/media/web/demo-poster.jpg", "format": "JPG"}
      ]
    }
  ],
  "directions": [
    {
      "key": "direction-a",
      "label": "Direction A: Evidence ledger",
      "accent": "#d84a32",
      "groups": [
        {
          "title": "Primary mark",
          "description": "Working identity mark for the concept.",
          "preview": "assets/design-package/logos/direction-a/primary-mark.svg",
          "preview_alt": "Primary mark for Direction A",
          "files": [
            {"href": "assets/design-package/logos/direction-a/primary-mark.svg", "label": "SVG"},
            {"href": "assets/design-package/logos/direction-a/primary-mark-512.png", "label": "PNG 512", "dimensions": "512×512"}
          ]
        }
      ]
    }
  ]
}
```

Every `files[].href`, `preview`, and `poster` path must exist after the build. Keep provenance and licensing notes in `design-package/notes/`.

## Catalog interaction

The generated catalog:

- renders groups as sections and assets as full-width rows;
- previews images and video;
- exposes every file variant as a normal download link;
- generates family and all-assets ZIPs in the browser;
- reports download progress and failure;
- preserves relative paths within the generated ZIP;
- does not require a nested ZIP in the deployed site.

For very large collections, still provide a separate prebuilt handoff ZIP in the release folder. The browser-generated download is a convenience, not the archival source of truth.

## Handoff README

Include:

- project and direction names;
- concept status;
- how to use logos and favicons;
- color and typography notes;
- source and license notes;
- trademark or independence language;
- media provenance;
- known omissions;
- which ZIP is for deployment and which is for design handoff.
