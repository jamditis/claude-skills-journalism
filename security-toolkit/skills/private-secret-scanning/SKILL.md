---
name: private-secret-scanning
description: Local Gitleaks scans for staged changes, push ranges, and full history in private repos, with redacted reports. Use to block committed secrets without GitHub Secret Protection.
---

# Private secret scanning

GitHub push protection and secret scanning are free on public repositories. Private repositories need a paid GitHub Secret Protection license. This skill gives private and shared repositories a deterministic local replacement: a pinned [Gitleaks](https://github.com/gitleaks/gitleaks) binary, three scan scopes, and git hooks that stop a leak before it leaves the machine.

Everything runs through one script that ships with this skill: `scripts/secret-scan.sh`. It needs only Bash (3.2 or later, so the macOS default works), git, curl, and python3.

## Quick start

```bash
SCAN=path/to/private-secret-scanning/scripts/secret-scan.sh

"$SCAN" install          # pinned Gitleaks 8.30.1, SHA-256 checked before install
"$SCAN" self-test        # proves leaks fail and clean repos pass on this machine
cd your-repo
"$SCAN" history --report /tmp/secret-report.json   # one-time audit of every commit
"$SCAN" install-hooks    # pre-commit and pre-push protection from now on
```

## Scan scopes

| Command | Scans | Use it |
|---|---|---|
| `staged` | the staged diff only | pre-commit hook; fastest |
| `push [RANGE] [--remote NAME]` | commits in `RANGE`, or the commits a `git push` is about to send (read from pre-push stdin). For a new branch, only commits the destination remote already has are skipped | pre-push hook; catches commits made with `--no-verify` |
| `history` | every commit reachable from any ref, including files deleted later | first adoption, and before a private repo goes public |

A secret that was committed and then deleted is still in history. Only `history` finds it, and only rotating the credential fixes it. Rewriting history does not undo a clone that already happened.

## Exit codes and failure behavior

| Exit | Meaning |
|---|---|
| 0 | no leaks |
| 1 | leaks found; each is listed on stderr |
| 2 | scanner or configuration error |

The script fails closed. It exits 2, never 0, when:

- Gitleaks is missing, cannot run, or is not the pinned version.
- `SECRET_SCAN_CONFIG` names a file that does not exist.
- Gitleaks exits with anything other than 0 or the script's own leak code. Gitleaks also exits 1 on fatal errors, such as a malformed `.gitleaks.toml`, so 1 from Gitleaks is treated as an error.
- The Gitleaks exit code and its report disagree.
- The report cannot be read.

A hook that exits non-zero blocks the commit or push, so a broken scanner blocks work. It does not let a leak through.

## What reports contain

Terminal output and `--report` files hold five fields per finding: `RuleID`, `File`, `StartLine`, `Commit`, and `Fingerprint`. They never hold the secret, the match, or the source line. Gitleaks runs with `--redact`, its raw report goes to a private temp file that is deleted on exit, and the script copies only those five fields out. The report is written with mode `0600`.

The fingerprint (`commit:file:rule:line`) is enough to find and fix the leak. It is also the line you add to `.gitleaksignore` to accept a finding.

## Baselines and allowlists

Adopting scanning on an old repo usually turns up findings you have already rotated. Record them instead of turning the scanner off:

1. Rotate every live credential first. Accepting a finding does not make it safe.
2. Run `history --report /tmp/secret-report.json`, then write its fingerprints to `.gitleaksignore` at the repo root:

   ```bash
   python3 -c 'import json,sys; print("\n".join(f["Fingerprint"] for f in json.load(open(sys.argv[1]))))' \
     /tmp/secret-report.json >> .gitleaksignore
   ```

3. Commit `.gitleaksignore`. Later scans report only new findings. Each line names one commit, file, rule, and line, so a new leak of the same secret in another commit still fails.

Keep allowlists narrow. In `.gitleaks.toml`, allow a specific path and rule, such as a test fixture, instead of a whole directory or a broad regex. Never allowlist a rule wholesale because it is noisy. A config that silences a rule also silences the next real leak of that type. Review a `.gitleaksignore` or allowlist change the way you would review an access-control change.

The script picks up `.gitleaks.toml` and `.gitleaksignore` from the repo root automatically. Set `SECRET_SCAN_CONFIG` to use a shared config from elsewhere.

## Hooks

`install-hooks` writes `pre-commit` (runs `staged`) and `pre-push` (runs `push --remote <destination>`) into the repository's hooks directory. It refuses to overwrite a hook it did not write; add a call to the script inside that hook instead. `git commit --no-verify` skips pre-commit, which is why pre-push scans the outgoing range again. A commit that is already on one remote is still scanned when it goes to a different remote for the first time. This matters when a branch moves from a private remote to a public one.

## Keep this public, keep your data private

This skill is generic on purpose. Do not add repository inventories, fleet or host paths, credentials, or real findings to a public copy of it. Keep those in a private repository or local config. Reports belong outside the repository you scanned, or in a gitignored path.

## CI

Run the same script in CI for a second check that local `--no-verify` cannot skip:

```yaml
- uses: actions/checkout@v6
  with:
    fetch-depth: 0     # history scans need every commit
- run: path/to/secret-scan.sh install
- run: path/to/secret-scan.sh history
```

Run this only on hosted runners, or on `push` events from trusted branches. Never run untrusted pull-request code on a self-hosted runner. A fork's PR can rewrite the scan script itself and then read whatever that runner can reach.

## Pinned version

The script pins Gitleaks 8.30.1 and the SHA-256 of each platform build from the release's `checksums.txt`. To upgrade, change `GITLEAKS_VERSION` and all four hashes together, then run `self-test`. Set `GITLEAKS_BIN` to use a binary you installed another way. It must still report the pinned version.
