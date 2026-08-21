## Picking a stack

Three current zero-build approaches, each with different trade-offs:

| Stack | When | Bundle size impact |
|---|---|---|
| **Vendored React + htm** | Component-heavy SPAs, existing React mental model, Tailwind styling | ~50 KB gzipped (React + ReactDOM + htm) |
| **htmx 2.x + server-rendered HTML** | CRUD apps, traditional MPA flow, want server-side state of truth | ~14 KB gzipped (htmx alone) |
| **Alpine.js 3.x + plain HTML** | Light interactivity sprinkled into mostly-static pages, no full SPA | ~15 KB gzipped (Alpine alone) |

You can mix htmx and Alpine.js in the same page, htmx handles server interactions, Alpine handles client-side UI state. Many production sites converge on this combo.

## Dependency policy

Zero-build means the deployed site does not compile code at request time. It
does not require fetching executable code from a third-party CDN on every page
load. Install exact packages, commit the lockfile, create local browser assets
once, commit those assets with checksums, and serve them under a CSP such as
`script-src 'self'`.

```bash
npm install --save-exact react@19.2.8 react-dom@19.2.8 htm@3.1.1 \
  lodash-es@4.18.1 htmx.org@2.0.10 @alpinejs/csp@3.15.12 \
  papaparse@5.5.4 \
  leaflet@1.9.4 leaflet.markercluster@1.5.3
npm install --save-dev --save-exact esbuild@0.28.1 \
  tailwindcss@4.3.3 @tailwindcss/cli@4.3.3
npm ci
npx @tailwindcss/cli -i ./src/input.css -o ./public/index.css --minify
```

Create one React entry so React and ReactDOM share the same bundled runtime:

```javascript
// src/vendor-entry.js
export { default as React } from 'react';
export { createRoot } from 'react-dom/client';
export { default as htm } from 'htm';
```

Build or copy the reviewed packages into the static directory, then record and
verify their hashes:

```bash
mkdir -p public/vendor
npx esbuild src/vendor-entry.js --bundle --format=esm --platform=browser \
  --outfile=public/vendor/react-runtime-19.2.8.mjs
npx esbuild lodash-es --bundle --format=esm --platform=browser \
  --outfile=public/vendor/lodash-es-4.18.1.mjs
cp node_modules/htmx.org/dist/htmx.min.js public/vendor/htmx-2.0.10.min.js
cp node_modules/@alpinejs/csp/dist/cdn.min.js public/vendor/alpine-csp-3.15.12.min.js
cp node_modules/papaparse/papaparse.min.js public/vendor/papaparse-5.5.4.min.js
cp node_modules/leaflet/dist/leaflet.js public/vendor/leaflet-1.9.4.js
cp node_modules/leaflet/dist/leaflet.css public/vendor/leaflet-1.9.4.css
cp -R node_modules/leaflet/dist/images public/vendor/images
cp node_modules/leaflet.markercluster/dist/leaflet.markercluster.js \
  public/vendor/leaflet.markercluster-1.5.3.js
cp node_modules/leaflet.markercluster/dist/MarkerCluster.css \
  public/vendor/MarkerCluster-1.5.3.css
cp node_modules/leaflet.markercluster/dist/MarkerCluster.Default.css \
  public/vendor/MarkerCluster.Default-1.5.3.css
find public/vendor -type f ! -name SHA256SUMS -print0 | sort -z | \
  xargs -0 sha256sum > public/vendor/SHA256SUMS
sha256sum -c public/vendor/SHA256SUMS
```
