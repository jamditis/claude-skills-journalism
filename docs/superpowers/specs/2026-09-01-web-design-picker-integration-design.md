# Web design picker integration design

## Decision

Add `web-design-picker` as a standalone, top-level Claude Code plugin with one
root `SKILL.md`. It will use the existing root-skill pattern rather than a
`skills/web-design-picker/` wrapper.

```text
web-design-picker/
├── .claude-plugin/plugin.json
├── SKILL.md
├── agents/openai.yaml
├── assets/
├── examples/
├── references/
├── scripts/
├── README.md
└── requirements-optional.txt
```

The plugin manifest and marketplace entry will both declare version `1.0.0`.
The repository release-version decision is deferred to implementation, after
the current release policy is inspected.

## Package contents

Copy from the reviewed ZIP: `SKILL.md`, `assets/`, `examples/`, `references/`,
`scripts/`, and `requirements-optional.txt`. Keep `assets/manifest.webmanifest`
because it is a functional static-site asset.

Add a repository-specific `README.md` that documents marketplace installation,
copy-installation, optional Python dependencies, Playwright, and ffmpeg. Do
not retain the ZIP instruction to upload the archive directly to an unspecified
skill host.

Do not copy `CHANGELOG.md`, `VERIFICATION.md`, or `manifest.txt`. The root
changelog records repository releases; the verification record is specific to
the source build environment; and the static file inventory would drift.
Omit the ZIP-local `LICENSE` to match current plugin layout. The repository
license and `license: MIT` frontmatter remain the license record.

## Repository surfaces

Implementation will add:

- `.claude-plugin/plugin.json` for the new plugin;
- a `web-design-picker` entry in `.claude-plugin/marketplace.json`, with
  `source: "./web-design-picker"` and the Design category;
- package and stable skill entries in `skills-catalog.yaml`;
- `agents/openai.yaml` with the catalog-required `interface.display_name` and
  `interface.short_description` fields;
- a root README plugin-table entry and design-and-production skill-table entry;
- the plugin in `CLAUDE.md`'s directory map and available-plugin list; and
- a documentation card plus `docs/web-design-picker/index.html` so the
  updated-stamp surfaces remain complete.

## Validation

Before release, run:

```text
npm run validate:catalog
npm run validate:agent-skills
node scripts/updated-stamp.mjs --check
claude plugin validate --strict ./web-design-picker
claude --plugin-dir ./web-design-picker
```

Review the imported Python scripts before execution. If their self-test is
used, run it in a disposable project directory. Browser QA starts a local
server and needs a Chromium environment that permits local navigation.

No deployment, marketplace publication, or push is part of this work.

## Research notes

- The [Agent Skills specification](https://agentskills.io/specification)
  requires a directory with `SKILL.md`, YAML frontmatter, a lowercase
  hyphenated name that matches its directory, and permits `scripts/`,
  `references/`, and `assets/`.
- The [Claude Code plugin guide](https://code.claude.com/docs/en/plugins)
  permits a one-skill plugin to keep `SKILL.md` at the plugin root. It places
  only `plugin.json` inside `.claude-plugin/`.
- The [Claude Code marketplace guide](https://code.claude.com/docs/en/plugin-marketplaces)
  requires marketplace plugin entries to provide a kebab-case name and source.
- The [Claude Code plugin reference](https://code.claude.com/docs/en/plugins-reference)
  defines explicit manifest versioning and recommends semantic versioning for
  published plugins.
- Closest local examples are `visual-explainer/`, `pdf-design/`, and
  `okf-wiki/`: each is a top-level plugin with root `SKILL.md`, a plugin
  manifest, and `agents/openai.yaml`.
- `scripts/repository-catalog.mjs` requires every marketplace package and
  `SKILL.md` to appear in `skills-catalog.yaml`; stable skills need
  `agents/openai.yaml`. `scripts/updated-stamp.mjs` requires matching README
  and documentation surfaces.

## Scope boundary

This document records the approved design only. It does not add the plugin,
copy archive files, change catalog or documentation surfaces, run imported
scripts, publish a marketplace release, deploy, or push.
