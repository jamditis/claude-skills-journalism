---
type: Reference
title: "the marketplace"
description: "How plugins are registered and installed via the marketplace manifest."
source: [".claude-plugin/marketplace.json", "README.md"]
verified: 2026-06-23
timestamp: 2026-06-23
tags: [marketplace, install]
---
# the marketplace

`.claude-plugin/marketplace.json` registers every plugin with its name, version,
and source path. Add the marketplace once, then install a plugin:

```
/plugin marketplace add jamditis/claude-skills-journalism
/plugin install okf-wiki@claude-skills-journalism
```

Each plugin also carries its own `.claude-plugin/plugin.json`. Browse the
[plugins](../plugins/index.md).
