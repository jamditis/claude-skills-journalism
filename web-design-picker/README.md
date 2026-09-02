# web-design-picker

A reusable Agent Skill and static-site factory for presenting two to five genuinely distinct website directions, three by default, in one switchable review site.

The package creates:

- standalone responsive concept pages;
- a neutral iframe-based direction picker;
- hash-addressable toggles and keyboard navigation;
- class-based and browser full-screen presentation modes;
- a searchable asset catalog;
- individual asset downloads;
- browser-generated per-family and all-assets ZIPs;
- complete favicon families;
- media, palette, and raster/vector export helpers;
- static validation, anti-slop review, distinctness scoring, browser QA, screenshots, and deterministic delivery ZIPs;
- a Cloudflare Drop archive with `index.html` at its root and no nested ZIP.

## Install as a skill

Install the plugin from this repository's Claude Code marketplace:

```text
/plugin marketplace add jamditis/claude-skills-journalism
/plugin install web-design-picker@claude-skills-journalism
```

For a standalone Agent Skills install, copy or link this directory into the agent's skills directory. The root `SKILL.md` contains the operating instructions.

## Command-line use

```bash
python scripts/web_design_picker.py init ./my-project --name "Client name" --directions 3
```

Complete the brief and build the actual concepts, then run:

```bash
python scripts/web_design_picker.py run ./my-project --test-downloads
```

The Cloudflare-ready file appears in `my-project/deliverables/`.

## Unified command map

```bash
python scripts/web_design_picker.py init PROJECT_DIR --name "Client name"
python scripts/web_design_picker.py build PROJECT_DIR
python scripts/web_design_picker.py validate PROJECT_DIR --strict
python scripts/web_design_picker.py preview PROJECT_DIR --test-downloads
python scripts/web_design_picker.py package PROJECT_DIR
python scripts/web_design_picker.py run PROJECT_DIR --strict --test-downloads
```

The `preview` command requires Playwright and a Chromium environment permitted to open a local HTTP server. Static validation and packaging do not require browser automation.

## Tool dependencies

Project scaffolding and favicon exports require Pillow and resvg-cli. Browser previews require Playwright and Chromium. Install the declared tools in an isolated environment:

```bash
python -m pip install -r requirements-optional.txt
playwright install chromium
```

Install `ffmpeg` and `ffprobe` through the operating system when video optimization is needed. Existing projects can use the build, static validation, and packaging commands without these media and browser tools.

## Self-test

Install Pillow and resvg-cli before running the default self-test because it scaffolds a fresh project and exports its favicon families.

```bash
python scripts/web_design_picker.py self-test
```

Add `--browser` where local Chromium navigation is permitted.
