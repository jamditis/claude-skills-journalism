# Web design picker integration implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superjawn:subagent-driven-development (recommended) or superjawn:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the supplied `web-design-picker` package as an installable, cataloged, and documented standalone plugin.

**Architecture:** Keep the package as a root-skill plugin, matching `visual-explainer` and `okf-wiki`. Import the functional skill files unchanged, then add only the repository metadata and public documentation required by current validators.

**Tech stack:** Agent Skills Markdown, Claude plugin JSON, Codex UI YAML, Python 3.10+, static HTML, Node.js repository validators.

---

## Execution note

Joe approved the design and then directed the primary session to implement locally after delegated workers stalled without changing files. Work proceeds on `feat/web-design-picker`; nothing is pushed or deployed.

### Task 1: Import the approved package

**Files:**
- Create: `web-design-picker/SKILL.md`
- Create: `web-design-picker/README.md`
- Create: `web-design-picker/requirements-optional.txt`
- Create: `web-design-picker/assets/*`
- Create: `web-design-picker/examples/*`
- Create: `web-design-picker/references/*`
- Create: `web-design-picker/scripts/*`

- [ ] Inspect the ZIP for duplicate, absolute, or parent-traversal paths.
- [ ] Extract it to a disposable directory and scan the text files for credentials and generated dependency trees.
- [ ] Copy only the approved functional files. Omit the package-level `CHANGELOG.md`, `LICENSE`, `VERIFICATION.md`, and `manifest.txt`.
- [ ] Compile all imported Python scripts and run `python web-design-picker/scripts/web_design_picker.py self-test`.
- [ ] Inspect the imported tree and checkpoint the result.

### Task 2: Register the plugin and skill

**Files:**
- Create: `web-design-picker/.claude-plugin/plugin.json`
- Create: `web-design-picker/agents/openai.yaml`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `skills-catalog.yaml`

- [ ] Add plugin metadata at version `1.0.0` using the existing author and design-category conventions.
- [ ] Add stable model-invoked Codex UI metadata with only `display_name` and `short_description`.
- [ ] Register the package and skill in the marketplace and repository catalog.
- [ ] Run `npm run validate:catalog` and `npm run validate:agent-skills`.

### Task 3: Add repository and public documentation

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/index.html`
- Create: `docs/web-design-picker/index.html`

- [ ] Add the plugin to the installation table, manual-install examples, and design-and-production skill table.
- [ ] Add the package to the repository map and available-plugin list.
- [ ] Add one concise Unreleased changelog entry without changing the repository release version.
- [ ] Add a docs index card and a focused detail page using the existing site design, favicon, accessibility, and updated-stamp hooks.
- [ ] Run the docs accessibility and updated-stamp checks, then checkpoint the integration diff.

### Task 4: Verify the complete change

- [ ] Run the package self-test again in a disposable directory.
- [ ] Run Python compilation for all imported scripts.
- [ ] Run `npm run validate:catalog`, `npm run validate:agent-skills`, `npm test`, `npm run a11y`, and `node scripts/updated-stamp.mjs --check`.
- [ ] Run `claude plugin validate --strict ./web-design-picker` when the installed CLI supports that command; record an unavailable command as a tooling limitation, not a pass.
- [ ] Inspect `git diff --check`, the complete diff, paths, line endings, and credential-like strings.
- [ ] Commit the implementation locally with the configured Joe Amditis noreply identity.

### Task 5: Run the local review gate

- [ ] Run Kimi K3 at low reasoning against the committed local diff and address every finding.
- [ ] Run Kimi K3 at high reasoning against the post-fix diff and address every finding.
- [ ] Use Qwen, then Claude Opus 4.8, only if Kimi is unavailable or quota-blocked.
- [ ] Re-run affected verification after review fixes and leave the branch unpushed for Joe.

