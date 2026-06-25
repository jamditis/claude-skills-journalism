# claude-skills-journalism wiki

An Open Knowledge Format (OKF) knowledge base: small markdown files, one concept each,
with provenance in YAML frontmatter. See `SPEC.md` for the full contract.

## Requirements

The validator parses YAML frontmatter with PyYAML:

```bash
pip install -r requirements.txt    # or: pip install pyyaml
```

## Validate

```bash
python3 scripts/validate.py --bundle bundle
```

It must exit 0. Run it before every commit.

## Add a concept

1. Create `bundle/<section>/<concept>.md` with the required frontmatter
   (`type, title, description, source, verified, timestamp, tags`).
2. Add a bullet for it in that section's `index.md`.
3. Validate.

## Session hooks

`.claude/` ships two hooks that orient Claude on this knowledge base before it works:

- `okf-anchor.py` (SessionStart) loads the bundle index into the session context.
- `okf-orient.py` (PreToolUse) blocks the first action once per session until Claude
  confirms it has read the index, then unblocks for the rest of the session.

They are one cross-platform python3 script each. No single interpreter name works on
every OS, so `settings.json` names the one for the OS this bundle was scaffolded on
(`python3` on macOS/Linux, `python` on Windows). If you move the bundle to a different
OS, change that one token in `settings.json` (or re-run the scaffolder there). Claude
Code treats a checked-in `.claude/settings.json` as untrusted, so the first time you
open this project it asks you to approve the hooks. They run automatically after that.
Delete `.claude/` (or set `disableAllHooks`) to turn them off.

## Security

Never put secret values in a concept. A credential concept documents the key name and
where it is retrieved, not the value. The validator scans for leaked secrets and fails on a hit.
