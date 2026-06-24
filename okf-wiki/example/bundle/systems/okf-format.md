---
type: Reference
title: "the OKF format"
description: "Open Knowledge Format: one concept per file, provenance in frontmatter, a validator."
source: ["okf-wiki/spec/SPEC.md", "okf-wiki/scripts/validate.py"]
verified: 2026-06-23
timestamp: 2026-06-23
tags: [okf, format]
---
# the OKF format

OKF stores knowledge as small markdown files, one concept each, with provenance in
YAML frontmatter (`type, title, description, source, verified, timestamp, tags`).
Directory `index.md` files navigate; the bundle-root `index.md` carries
`okf_version` only. A validator enforces the contract and scans for leaked secrets.
The [okf-wiki plugin](../plugins/okf-wiki.md) scaffolds a conforming bundle.
