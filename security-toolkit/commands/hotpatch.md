---
description: Sandboxed pre-install scan + cooldown bypass for an urgent npm/bun install. Use when a recent package version must be installed despite the global supply-chain cooldown — for example a published CVE patch, a dependency that just shipped, or any case where waiting the full cooldown is not acceptable.
---

# /hotpatch

`/hotpatch <pkg>[@<version>] [--manager npm|bun]`

This command runs the supply-chain pre-install scan defined in the `supply-chain-hardening` skill, then performs an `--ignore-scripts` install with the cooldown bypassed if the scan is clean.

The command is the gate. The trigger phrase "hotpatch" should not bypass the cooldown without the scan; if no scan tooling is available on the machine, perform the equivalent checks in-conversation before installing.

## Execution path

1. **Look for a local scan script.** Check `~/.claude/hotpatch.sh` (officejawn convention), `./hotpatch.sh`, `./scripts/hotpatch.sh`, and any path stored in `$HOTPATCH_SCRIPT`. If found:

   ```bash
   <script> <pkg>[@<version>] [--manager npm|bun]
   ```

   Pass through `--yes` only if the user has explicitly authorized non-interactive execution. Pass through `--force` only if the user has reviewed red flags from a prior run and approved.

2. **If no local script exists**, perform the scan in-conversation using the supply-chain-hardening skill's heuristics. Briefly:
   - `curl -fsSL "https://registry.npmjs.org/<encoded-name>"` — get metadata
   - Resolve the requested version, extract `unpackedSize`, `fileCount`, `dist.tarball`, `time[version]`, and any `deprecated` flag
   - Download the tarball to a `mktemp -d` directory
   - Extract under `bwrap --ro-bind /usr /usr --unshare-all --die-with-parent --bind ...` (Linux) or `sandbox-exec` (macOS) — never extract into the cwd, never extract without sandboxing
   - Parse `package.json` for risky patterns (see SKILL.md "Static checks" table)
   - Diff size + fileCount against the most recent **stable** prior version (skip prereleases — `-dev`, `-rc`, `-beta`)
   - Hit OSV.dev: `POST https://api.osv.dev/v1/query` with `{"package":{"name":"<name>","ecosystem":"npm"},"version":"<version>"}` — no auth required
   - Render a report with `RED` (block install) and `YELLOW` (warn) flags

3. **If any RED flags fire**, do NOT install. Surface the flags, recommend either picking a different version, waiting out the cooldown, or — if the user has confirmed they understand the risk — passing `--force` on a re-run. Do not auto-`--force` without explicit user confirmation.

4. **If clean (or user approved despite flags)**, install with the cooldown bypassed AND scripts disabled:

   ```bash
   # npm path
   npm install <pkg>@<version> --min-release-age=0 --ignore-scripts

   # bun path
   bun add <pkg>@<version> --minimum-release-age=0 --ignore-scripts
   ```

5. **Report what was skipped.** Tell the user the postinstall script was not executed. If the package legitimately needs postinstall (native module compilation, binary download), surface the script contents and let the user choose to run it manually after review.

## Manager autodetect

If `--manager` is not given, autodetect from cwd:

- `bun.lock` or `bun.lockb` present → bun
- `package-lock.json` or `package.json` present → npm
- Neither → ask the user; do not guess

## Argument parsing

- `<pkg>` may be unscoped (`typescript`) or scoped (`@types/node`)
- `@<version>` is optional; default is `latest`
- `--manager npm|bun` overrides autodetect
- `--force` is **never** to be passed unless the user has explicitly authorized after seeing the RED flags from a prior dry-run
- `--yes` skips the interactive `[y/N]` prompt; only pass through if the user is operating non-interactively

## What this command is NOT for

- Routine package installs — let the cooldown do its job; no scan needed
- Bulk dependency upgrades — use `npm update` / `bun update` normally
- Auditing already-installed packages — that's `npm audit` / `osv-scanner --lockfile=...`
- Scanning a tarball without installing — call the scan script directly with `--scan-local <tarball>` if it supports that mode

## Cross-reference

For threat model and the design rationale behind each check, read `supply-chain-hardening` (SKILL.md). For the reference Bash implementation that powers the officejawn workflow, see `scripts/hotpatch.example.sh` in this plugin.
