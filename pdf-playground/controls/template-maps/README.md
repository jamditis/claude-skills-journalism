# Template maps

Each file in this directory defines the control panel layout for one document template. The control-panel.js reads the active map to build the correct set of controls.

## How it works

A template map is a JS file that assigns `window.PDFPlaygroundTemplateMap` with the following sections:

**colors** — Array of CSS custom property mappings. Each entry has `variable` (the CSS variable name in `:root`), `label` (displayed in the panel), and `default` (the starting hex value).

**fonts** — Object with `heading` and `body` keys. Each has `targets` (CSS selectors to update), `default` (initial font name), and `options` (array of Google Font names to offer).

**sliders** — Array of range controls. Each entry has `id`, `label`, `property` (CSS property to set), `targets` (selectors), `unit`, `min`, `max`, `step`, and `default`. Special cases: `isScale: true` multiplies base sizes for heading scaling. `mirrorProperty` copies the value to a second property.

**toggles** — Array of show/hide switches. Each has `id`, `label`, `selector` (elements to toggle), and `default` (true = visible).

**layout** — Array of layout controls. Each has `id`, `label`, `type` ("buttonGroup" or "select"), `target` (selector), `property` (CSS property), `options` (value/label pairs), and `default`.

## Creating a new map

1. Copy `proposal.js` as a starting point
2. Rename it to match your template (e.g., `report.js`)
3. Update `window.PDFPlaygroundTemplateMap.name` to match
4. Map the CSS variables and selectors from your template
5. The control panel auto-detects which template is loaded based on the map name

## Example: adding a color

```js
{ variable: "--accent", label: "Accent color", default: "#c9a227" }
```

## Example: adding a toggle

```js
{ id: "testimonials", label: "Testimonials", selector: ".testimonial-block", default: true }
```

## Supported templates

- `proposal.js` — Funding proposal template
