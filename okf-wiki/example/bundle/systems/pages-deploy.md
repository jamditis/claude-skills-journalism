---
type: Process
title: "the docs site and deploy"
description: "The docs/ directory publishes to skills.amditis.tech via GitHub Pages on merge."
source: ["docs/index.html", "docs/okf-wiki/index.html"]
verified: 2026-06-23
timestamp: 2026-06-23
tags: [docs, deploy]
---
# the docs site and deploy

The `docs/` directory is the source for the GitHub Pages site at
skills.amditis.tech. The landing page lists the plugins; each plugin gets a page
under its own slug (for example `docs/okf-wiki/`). Merging to the default branch
rebuilds and publishes the site. Plugins are listed in
[the marketplace](marketplace.md).
