# Vendored template runtime

`mermaid-11.16.0.mjs` is the browser bundle imported by the two HTML templates in the parent directory. It is committed so a copied or directly opened template does not depend on a runtime CDN or a missing generated file.

Rebuild from exact packages:

```bash
npm install --save-exact mermaid@11.16.0
npm install --save-dev --save-exact esbuild@0.28.1
npx esbuild node_modules/mermaid/dist/mermaid.esm.min.mjs --bundle \
  --format=esm --platform=browser --minify --legal-comments=external \
  --outfile=visual-explainer/templates/vendor/mermaid-11.16.0.mjs
(cd visual-explainer/templates/vendor && sha256sum -c SHA256SUMS)
```

Mermaid's MIT license is retained in `MERMAID-LICENSE`. Bundled third-party notices are retained in `mermaid-11.16.0.mjs.LEGAL.txt`.
