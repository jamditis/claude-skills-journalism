---
name: supply-chain-hardening
description: Configure install-time cooldowns for npm/bun (minimum release age) and run a sandboxed pre-install scan when the cooldown has to be bypassed. Use when the user asks about supply-chain attacks, npm/bun security, "minimum release age", a "cooldown" for installs, hardening against Shai-Hulud-class worms, or how to safely install a package that was just published. Also use after any recent supply-chain incident in the npm ecosystem.
---

# Supply-chain hardening

Defends a journalism toolchain against the dominant npm/bun supply-chain attack pattern: a maintainer account or CI pipeline is compromised, a malicious version ships, and machines install it before anyone notices. Recent example: the **Mini Shai-Hulud TanStack attack (2026-05-11)** compromised 84 versions across 42 `@tanstack/*` packages and exfiltrated AWS / GCP / Vault / GitHub / SSH credentials via a postinstall script.

The defense is **layered** and intentionally simple:

1. **Install-time cooldown** — only install package versions older than N days (default 7). This is the primary defense. By the time the cooldown expires, the security community has almost always flagged a compromised version and the registry has yanked it.
2. **Sandboxed pre-install scan** — when the cooldown has to be bypassed (CVE patch, fresh dep, urgent install), run the candidate tarball through a static-analysis scan that looks for the diagnostic signatures of supply-chain malware. The scan runs inside `bwrap`/`firejail`/`unshare` so a malicious package can't escape the inspection.
3. **`--ignore-scripts` at install** — postinstall is the #1 attack vector. Skip lifecycle scripts on every cooldown-bypass install.

These three together would have blocked the Mini Shai-Hulud TanStack attack on a stock laptop with no human in the loop.

## Configure the cooldown

Verified config keys (npm v11+ and bun 1.3+):

| Manager | File | Key | Units | Exclusion key |
|---|---|---|---|---|
| npm | `~/.npmrc` (or project `.npmrc`) | `min-release-age` | days | none yet — proposed in [npm/cli#8994](https://github.com/npm/cli/issues/8994) |
| bun | `~/.bunfig.toml` (or project `bunfig.toml`) | `[install] minimumReleaseAge` | seconds | `[install] minimumReleaseAgeExcludes = []` (exact names, no globs) |

Minimal config:

```ini
# ~/.npmrc
min-release-age=7
```

```toml
# ~/.bunfig.toml
[install]
minimumReleaseAge = 604800  # 7 days
minimumReleaseAgeExcludes = []
```

**Requires npm 11+.** Older npm silently ignores unknown keys, so the config looks correct but does nothing. Check with `npm --version` and `npm config get min-release-age` (should echo `7`, not `null`).

## Per-command bypass

When the cooldown blocks an install you actually want:

```bash
npm install <pkg>@<version> --min-release-age=0 --ignore-scripts
bun add     <pkg>@<version> --minimum-release-age=0 --ignore-scripts
```

The `bun add --minimum-release-age=0` CLI flag works in 1.3+ even though the docs don't list it — it follows bun's `bunfig key → kebab-case flag` convention.

**Always pair the bypass with `--ignore-scripts`.** Postinstall is the most common payload-execution path in supply-chain malware (Mini Shai-Hulud, event-stream, ua-parser-js, coa, all used it). Native modules that legitimately need postinstall can have the script run manually after a human-readable review:

```bash
(cd node_modules/<pkg> && cat package.json | jq .scripts) # eyeball it
(cd node_modules/<pkg> && npm run postinstall)            # run if it checks out
```

## When to scan before bypassing

The scan is for the dangerous moment: you've decided to bypass the cooldown and need a sanity check. The skill ships a reference script (`scripts/hotpatch.example.sh`) implementing the heuristics. Adapt it to your machine — Bash assumes `bwrap` (Linux); macOS users substitute `sandbox-exec` or skip the sandbox layer with the trade-off documented.

Static checks the scan should perform (each backed by a real attack):

| Check | Diagnostic of | Severity |
|---|---|---|
| `optionalDependencies` / `dependencies` containing `github:` or `git+` URLs | Mini Shai-Hulud (delivered payload via `github:tanstack/router#<sha>` ref) | RED |
| Large JS file at package root not referenced by `main`/`module`/`exports`/`bin`/`files` | Planted payload pattern (`router_init.js` in Mini Shai-Hulud) | RED |
| Unpacked size >3x the prior stable version | Bulk payload smuggling | RED |
| `fileCount` delta of 1–4 paired with >2x size jump | Single planted file | RED |
| `preinstall`/`install`/`postinstall`/`prepare` scripts present | Lifecycle-script attack vector (event-stream, ua-parser-js, etc.) | YELLOW |
| JS files referencing `.ssh/`, `.aws/`, `.npmrc`, `GITHUB_TOKEN`, `AWS_SECRET`, kube config | Credential exfiltration | YELLOW |
| Version flagged `deprecated` in npm registry with "security"/"compromised"/"malicious" wording | Maintainer/registry yank | RED |
| OSV.dev returns known vulnerabilities for `<pkg>@<version>` | Disclosed CVE | RED (severity-dependent) |

**Why prerelease versions are skipped from the size-delta baseline:** dev/beta/rc versions have wildly different sizes than stable releases and produce false positives.

## What the cooldown does *not* catch

Be honest about the limits with whoever you're configuring this for:

- **Old packages with new malicious versions still in the cooldown window are blocked**, but if the bad version *also* passes the cooldown (rare but possible — a compromise that goes >7 days undetected), the cooldown alone won't help. The scan catches most of those.
- **Transitive deps**. A clean `<pkg>` you install can pull in a compromised transitive. Defenses: scan against the *resolved* tree (`npm audit`, `osv-scanner`), and keep the cooldown active globally so transitive resolution also waits.
- **`npm ci`** against an existing lockfile. The cooldown applies during *resolution*, not installation of already-pinned versions. If your lockfile pins a compromised version, `npm ci` will install it. Mitigation: scan lockfiles in CI with `osv-scanner --lockfile=package-lock.json`.
- **Pre-existing compromised packages in `node_modules`**. Hardening protects future installs, not past ones. Audit existing deps separately (`npm audit`, `osv-scanner`, manual review of recently-published deps in your tree).

## Quick-start workflow for a new machine

1. Verify npm >= 11: `npm --version`. If older, upgrade (`sudo npm i -g npm@latest` or tarball-swap if self-upgrade races).
2. Write `~/.npmrc` and `~/.bunfig.toml` with the config above.
3. Verify: `npm config get min-release-age` returns `7`. `cat ~/.bunfig.toml` shows the `[install]` block.
4. Copy `scripts/hotpatch.example.sh` to `~/.claude/hotpatch.sh` (or wherever fits). Make executable. Run `./hotpatch.sh --self-test` against the synthetic Mini Shai-Hulud fixture (also shipped) to confirm the heuristics fire.
5. Document the bypass workflow somewhere your team will find it. The whole skill assumes the bypass is *rare* and *reviewed*, not the default.

## Threat model: what this defends and what it doesn't

| Defends against | Doesn't defend against |
|---|---|
| Maintainer account compromise (npm token theft) | Targeted attack tailored to wait through the cooldown |
| CI/CD pipeline hijack (Mini Shai-Hulud, valid OIDC tokens, SLSA-attested malice) | Compromise of a transitive dep already pinned in a lockfile |
| Typosquatting (lookalike package names) — when paired with `npm pkg fix` and lockfile review | Malicious code in your own dev dependencies that you authored |
| Postinstall payload execution (cooldown + `--ignore-scripts` = belt and suspenders) | Runtime supply-chain attacks (e.g., dynamic loading of bad code from a CDN) |
| Drive-by `npm install` of a brand-new transitive | Compromise of the registry itself (very rare; out of scope) |

## Further reading

- Original Mini Shai-Hulud StepSecurity analysis (TanStack attack, 2026-05-11): <https://www.stepsecurity.io/blog/mini-shai-hulud-is-back-a-self-spreading-supply-chain-attack-hits-the-npm-ecosystem>
- npm `min-release-age` config: <https://docs.npmjs.com/cli/v11/using-npm/config>
- bun `minimumReleaseAge` config: <https://bun.com/docs/runtime/bunfig>
- OSV.dev API (free, unauth): <https://osv.dev/docs/#tag/api>
- Earlier Shai-Hulud worm context: <https://github.com/advisories?query=shai-hulud>
