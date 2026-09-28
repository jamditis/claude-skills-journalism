#!/usr/bin/env bash
# secret-scan.sh - deterministic Gitleaks scans for private and shared repos.
#
# Usage:
#   secret-scan.sh install [--dir DIR]      download the pinned Gitleaks and verify its checksum
#   secret-scan.sh staged [--report FILE]   scan staged changes (pre-commit)
#   secret-scan.sh push [RANGE] [--remote NAME] [--report FILE]
#                                           scan commits about to be pushed; with no RANGE,
#                                           read pre-push hook lines from stdin
#   secret-scan.sh history [--report FILE]  scan every commit reachable from any ref
#   secret-scan.sh install-hooks            add pre-commit and pre-push hooks to this repo
#   secret-scan.sh self-test                prove leaks fail and clean repos pass
#
# Exit codes: 0 clean, 1 leaks found, 2 scanner or configuration error.
# Every error path exits non-zero, so a missing scanner never reads as clean.
#
# Reports and terminal output hold rule, file, line, commit, and fingerprint.
# They never hold the secret, the match, or the source line.

set -euo pipefail

GITLEAKS_VERSION="8.30.1"
# Leaks exit with this code. Gitleaks exits 1 on fatal errors (a bad config,
# for one) whatever --exit-code says, so 1 must never mean "leaks".
LEAK_EXIT=10
INSTALL_DIR="${SECRET_SCAN_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/private-secret-scanning}/bin"
HOOK_MARKER="managed by private-secret-scanning"
# Bash 3.2 (macOS) treats "${empty[@]}" as unbound under set -u, hence the
# ${arr[@]+...} guards on arrays that can be empty.
CLEANUP=()
trap 'rm -rf ${CLEANUP[@]+"${CLEANUP[@]}"}' EXIT
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

die() { echo "secret-scan: $*" >&2; exit 2; }

platform() {
  local os arch
  case "$(uname -s)" in
    Linux) os=linux ;;
    Darwin) os=darwin ;;
    *) die "unsupported OS $(uname -s); install Gitleaks $GITLEAKS_VERSION yourself and set GITLEAKS_BIN" ;;
  esac
  case "$(uname -m)" in
    x86_64|amd64) arch=x64 ;;
    aarch64|arm64) arch=arm64 ;;
    *) die "unsupported CPU $(uname -m); install Gitleaks $GITLEAKS_VERSION yourself and set GITLEAKS_BIN" ;;
  esac
  echo "${os}_${arch}"
}

# From gitleaks_8.30.1_checksums.txt on the v8.30.1 GitHub release.
expected_sha256() {
  case "$1" in
    linux_x64) echo "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb" ;;
    linux_arm64) echo "e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080" ;;
    darwin_x64) echo "dfe101a4db2255fc85120ac7f3d25e4342c3c20cf749f2c20a18081af1952709" ;;
    darwin_arm64) echo "b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5" ;;
  esac
}

sha256_of() {
  if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1
  elif command -v shasum >/dev/null; then shasum -a 256 "$1" | cut -d' ' -f1
  else die "need sha256sum or shasum to verify the download"
  fi
}

cmd_install() {
  local dir="$INSTALL_DIR"
  [[ "${1:-}" == "--dir" ]] && dir="${2:?--dir needs a path}"
  local plat tarball url tmp
  plat="$(platform)"
  tarball="gitleaks_${GITLEAKS_VERSION}_${plat}.tar.gz"
  url="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/${tarball}"
  command -v curl >/dev/null || die "need curl to download Gitleaks"
  tmp="$(mktemp -d)"
  CLEANUP+=("$tmp")
  curl -fsSL --retry 3 -o "$tmp/$tarball" "$url" || die "download failed: $url"
  local got
  got="$(sha256_of "$tmp/$tarball")"
  [[ "$got" == "$(expected_sha256 "$plat")" ]] \
    || die "checksum mismatch for $tarball (got $got); refusing to install"
  tar -xzf "$tmp/$tarball" -C "$tmp" gitleaks
  mkdir -p "$dir"
  install -m 0755 "$tmp/gitleaks" "$dir/gitleaks"
  echo "installed Gitleaks $GITLEAKS_VERSION to $dir/gitleaks"
}

# Find the pinned scanner. Anything else is a configuration error.
gitleaks_bin() {
  local bin="${GITLEAKS_BIN:-}"
  if [[ -z "$bin" ]]; then
    if [[ -x "$INSTALL_DIR/gitleaks" ]]; then bin="$INSTALL_DIR/gitleaks"
    elif command -v gitleaks >/dev/null; then bin="$(command -v gitleaks)"
    else die "Gitleaks not found; run: $SCRIPT_PATH install"
    fi
  fi
  [[ -x "$bin" ]] || die "GITLEAKS_BIN is not executable: $bin"
  local ver
  ver="$("$bin" version 2>/dev/null)" || die "could not run $bin"
  [[ "${ver#v}" == "$GITLEAKS_VERSION" ]] \
    || die "Gitleaks $ver found, $GITLEAKS_VERSION required; run: $SCRIPT_PATH install"
  echo "$bin"
}

repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || die "not inside a git repository"
}

# Optional repository config: .gitleaks.toml (rules and allowlists). Gitleaks
# reads .gitleaksignore (accepted fingerprints) from its working directory,
# so scans run from the repo root.
# SECRET_SCAN_CONFIG overrides the config path; if it is set, the file must exist.
set_config_args() {
  local root="$1"
  CONFIG_ARGS=()
  if [[ -n "${SECRET_SCAN_CONFIG:-}" ]]; then
    [[ -f "$SECRET_SCAN_CONFIG" ]] || die "SECRET_SCAN_CONFIG does not exist: $SECRET_SCAN_CONFIG"
    CONFIG_ARGS+=(--config "$SECRET_SCAN_CONFIG")
  elif [[ -f "$root/.gitleaks.toml" ]]; then
    CONFIG_ARGS+=(--config "$root/.gitleaks.toml")
  fi
}

# Run Gitleaks with a private raw report, then keep only safe fields.
# $1 = optional sanitized report path; remaining args go to `gitleaks git`.
run_scan() {
  local report_out="$1"; shift
  local bin root raw status
  bin="$(gitleaks_bin)"
  root="$(repo_root)"
  command -v python3 >/dev/null || die "need python3 to sanitize the report"
  set_config_args "$root"
  raw="$(umask 077; mktemp)"
  CLEANUP+=("$raw")
  local scan_status=0
  (cd "$root" && "$bin" git . ${CONFIG_ARGS[@]+"${CONFIG_ARGS[@]}"} "$@" --redact --no-banner \
    --log-level error --report-format json --report-path "$raw" --exit-code "$LEAK_EXIT" \
    >/dev/null) || scan_status=$?
  if [[ "$scan_status" -ne 0 && "$scan_status" -ne "$LEAK_EXIT" ]]; then
    die "Gitleaks failed (exit $scan_status); fix the error above before committing"
  fi
  status=0
  python3 - "$raw" "${report_out:-}" <<'PY' || status=$?
import json, os, sys
raw_path, out_path = sys.argv[1], sys.argv[2]
with open(raw_path) as f:
    text = f.read().strip()
findings = json.loads(text) if text else []
keep = ("RuleID", "File", "StartLine", "Commit", "Fingerprint")
safe = [{k: item.get(k) for k in keep} for item in findings]
for item in safe:
    commit = (item["Commit"] or "staged")[:12]
    print(f"leak: {item['RuleID']} in {item['File']}:{item['StartLine']} "
          f"(commit {commit}, fingerprint {item['Fingerprint']})", file=sys.stderr)
if out_path:
    fd = os.open(out_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)  # O_CREAT mode does not apply to an existing file
    with os.fdopen(fd, "w") as f:
        json.dump(safe, f, indent=2)
        f.write("\n")
# 10, not 1: an uncaught Python error also exits 1 and must not read as leaks.
sys.exit(10 if safe else 0)
PY
  # The exit code and the report must agree; if they don't, trust neither.
  case "$status:$scan_status" in
    "0:0") return 0 ;;
    "10:$LEAK_EXIT") return 1 ;;
    0:*|10:*) die "Gitleaks exit $scan_status does not match its report" ;;
    *) die "could not read the Gitleaks report" ;;
  esac
}

parse_report() {
  # Sets REPORT, REMOTE, and REST from the argument list.
  REPORT=""; REMOTE=""; REST=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --report) REPORT="${2:?--report needs a path}"; shift 2 ;;
      --remote) REMOTE="${2:?--remote needs a name}"; shift 2 ;;
      *) REST+=("$1"); shift ;;
    esac
  done
}

cmd_staged() {
  parse_report "$@"
  run_scan "$REPORT" --staged && echo "secret-scan: staged changes clean"
}

cmd_push() {
  parse_report "$@"
  local -a ranges=()
  if [[ ${#REST[@]} -gt 0 ]]; then
    ranges=("${REST[0]}")
  else
    # pre-push stdin: <local ref> <local sha> <remote ref> <remote sha>.
    # Git sends an all-zero id (40 or 64 digits) for a missing side.
    local lsha rsha
    while read -r _ lsha _ rsha; do
      [[ -z "${lsha:-}" || "$lsha" =~ ^0+$ ]] && continue  # branch deletion
      if [[ "$rsha" =~ ^0+$ ]]; then
        # New branch: skip only commits the destination already has. Other
        # remotes do not count; a commit on a private remote can still leak
        # to a public one. With no remote name, scan all of its ancestry.
        if [[ -n "$REMOTE" ]]; then
          ranges+=("$lsha --not --remotes=$REMOTE")
        else
          ranges+=("$lsha")
        fi
      else
        ranges+=("$rsha..$lsha")
      fi
    done
  fi
  [[ ${#ranges[@]} -gt 0 ]] || { echo "secret-scan: nothing to push"; return 0; }
  local r status=0
  for r in "${ranges[@]}"; do
    run_scan "$REPORT" --log-opts="$r" || status=$?
    [[ "$status" -ne 0 ]] && return "$status"
  done
  echo "secret-scan: outgoing commits clean"
}

cmd_history() {
  parse_report "$@"
  run_scan "$REPORT" --log-opts="--all" && echo "secret-scan: full history clean"
}

cmd_install_hooks() {
  local root hooks hook
  root="$(repo_root)"
  hooks="$(git -C "$root" rev-parse --git-path hooks)"
  [[ "$hooks" = /* ]] || hooks="$root/$hooks"
  mkdir -p "$hooks"
  for hook in pre-commit pre-push; do
    if [[ -e "$hooks/$hook" ]] && ! grep -q "$HOOK_MARKER" "$hooks/$hook"; then
      die "$hooks/$hook already exists; add a call to $SCRIPT_PATH ${hook#pre-} there instead"
    fi
  done
  printf '#!/usr/bin/env bash\n# %s\nexec "%s" staged\n' "$HOOK_MARKER" "$SCRIPT_PATH" > "$hooks/pre-commit"
  # Git passes the destination remote's name as $1.
  printf '#!/usr/bin/env bash\n# %s\nexec "%s" push --remote "$1"\n' "$HOOK_MARKER" "$SCRIPT_PATH" > "$hooks/pre-push"
  chmod 0755 "$hooks/pre-commit" "$hooks/pre-push"
  echo "installed pre-commit and pre-push hooks in $hooks"
}

cmd_self_test() {
  gitleaks_bin >/dev/null
  local work fails=0
  work="$(mktemp -d)"
  CLEANUP+=("$work")
  # Build a synthetic AWS-style key at run time so no literal secret is
  # stored in this repository.
  local fake="AKIA" alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" _
  for _ in {1..16}; do fake+="${alphabet:RANDOM%32:1}"; done

  new_repo() {
    git init -q "$1"
    git -C "$1" config user.email test@example.invalid
    git -C "$1" config user.name "secret-scan self-test"
    git -C "$1" config commit.gpgsign false
    echo "clean" > "$1/README.md"
    git -C "$1" add README.md
    git -C "$1" commit -qm "initial"
  }
  expect() {  # expect <want-exit> <label> <cmd...>
    local want="$1" label="$2"; shift 2
    local got=0
    "$@" >/dev/null 2>&1 || got=$?
    if [[ "$got" == "$want" ]]; then echo "ok   $label"
    else echo "FAIL $label (exit $got, want $want)"; fails=$((fails + 1)); fi
  }

  new_repo "$work/clean"
  expect 0 "clean repo passes staged scan" bash -c "cd '$work/clean' && '$SCRIPT_PATH' staged"
  expect 0 "clean repo passes history scan" bash -c "cd '$work/clean' && '$SCRIPT_PATH' history"

  new_repo "$work/staged"
  printf 'aws_access_key_id = %s\n' "$fake" > "$work/staged/config.ini"
  git -C "$work/staged" add config.ini
  expect 1 "staged leak fails" bash -c "cd '$work/staged' && '$SCRIPT_PATH' staged"
  # Gitleaks exits 1 on a fatal config error, the old "leaks" code.
  printf '[[rules]\nbroken\n' > "$work/staged/bad.toml"
  expect 2 "malformed config fails closed, even with a staged leak" \
    bash -c "cd '$work/staged' && SECRET_SCAN_CONFIG='$work/staged/bad.toml' '$SCRIPT_PATH' staged"

  new_repo "$work/push"
  local base
  base="$(git -C "$work/push" rev-parse HEAD)"
  printf 'aws_access_key_id = %s\n' "$fake" > "$work/push/config.ini"
  git -C "$work/push" add config.ini
  git -C "$work/push" commit -qm "add config"
  expect 1 "push-range leak fails" bash -c "cd '$work/push' && '$SCRIPT_PATH' push '$base..HEAD'"
  local head zero="0000000000000000000000000000000000000000"
  head="$(git -C "$work/push" rev-parse HEAD)"
  expect 1 "pre-push stdin with a leak fails" bash -c \
    "cd '$work/push' && echo 'refs/heads/main $head refs/heads/main $base' | '$SCRIPT_PATH' push"
  expect 1 "pre-push stdin for a new branch fails" bash -c \
    "cd '$work/push' && echo 'refs/heads/new $head refs/heads/new $zero' | '$SCRIPT_PATH' push"
  local zero64="${zero}000000000000000000000000"  # SHA-256 repos use 64 zeros
  expect 1 "pre-push new branch with a 64-zero id fails" bash -c \
    "cd '$work/push' && echo 'refs/heads/new $head refs/heads/new $zero64' | '$SCRIPT_PATH' push"
  expect 0 "pre-push deletion with a 64-zero id is skipped" bash -c \
    "cd '$work/push' && echo '(delete) $zero64 refs/heads/old $head' | '$SCRIPT_PATH' push"
  # The leak is already on a private remote. A first push to another remote
  # must still scan it; only the destination's own commits are skipped.
  git init -q --bare "$work/private.git"
  git -C "$work/push" remote add private "$work/private.git"
  git -C "$work/push" push -q private HEAD:refs/heads/main
  git -C "$work/push" fetch -q private
  expect 1 "new branch to another remote still scans commits on a private remote" bash -c \
    "cd '$work/push' && echo 'refs/heads/new $head refs/heads/new $zero' | '$SCRIPT_PATH' push --remote public"
  expect 0 "new branch skips commits the destination already has" bash -c \
    "cd '$work/push' && echo 'refs/heads/new $head refs/heads/new $zero' | '$SCRIPT_PATH' push --remote private"
  expect 0 "push range before the leak passes" bash -c "cd '$work/push' && '$SCRIPT_PATH' push '$base~0..$base'"

  # Leak added then deleted: invisible in the tree, still in history.
  new_repo "$work/history"
  printf 'aws_access_key_id = %s\n' "$fake" > "$work/history/config.ini"
  git -C "$work/history" add config.ini
  git -C "$work/history" commit -qm "add config"
  git -C "$work/history" rm -q config.ini
  git -C "$work/history" commit -qm "remove config"
  expect 1 "deleted leak fails history scan" bash -c "cd '$work/history' && '$SCRIPT_PATH' history --report '$work/report.json'"

  if [[ -f "$work/report.json" ]] && grep -q '"Fingerprint"' "$work/report.json" \
      && ! grep -qF "$fake" "$work/report.json"; then
    echo "ok   report has fingerprints and no secret value"
  else
    echo "FAIL report missing, or it contains the secret"; fails=$((fails + 1))
  fi
  local mode
  mode="$(stat -c %a "$work/report.json" 2>/dev/null || stat -f %Lp "$work/report.json")"
  if [[ "$mode" == "600" ]]; then echo "ok   report is private (mode 600)"
  else echo "FAIL report mode is $mode, want 600"; fails=$((fails + 1)); fi
  python3 -c 'import json,sys; print("\n".join(f["Fingerprint"] for f in json.load(open(sys.argv[1]))))' \
    "$work/report.json" > "$work/history/.gitleaksignore"
  expect 0 "fingerprints in .gitleaksignore accept known findings" \
    bash -c "cd '$work/history' && '$SCRIPT_PATH' history"
  mkdir -p "$work/history/sub/dir"
  expect 0 ".gitleaksignore at the root applies from a subdirectory" \
    bash -c "cd '$work/history/sub/dir' && '$SCRIPT_PATH' history"
  rm "$work/history/.gitleaksignore"
  local out
  out="$(cd "$work/history" && "$SCRIPT_PATH" history 2>&1 || true)"
  if grep -q "leak:" <<<"$out" && ! grep -qF "$fake" <<<"$out"; then
    echo "ok   terminal output names the leak without the value"
  else
    echo "FAIL terminal output missing the leak, or it prints the secret"; fails=$((fails + 1))
  fi

  expect 2 "missing scanner fails closed" \
    bash -c "cd '$work/clean' && GITLEAKS_BIN='$work/no-such-gitleaks' '$SCRIPT_PATH' staged"
  expect 2 "missing config fails closed" \
    bash -c "cd '$work/clean' && SECRET_SCAN_CONFIG='$work/none.toml' '$SCRIPT_PATH' staged"

  # A scanner that reports the pinned version but writes a broken report.
  printf '#!/usr/bin/env bash\n[[ "$1" == version ]] && { echo %s; exit 0; }\nwhile [[ $# -gt 0 ]]; do [[ "$1" == --report-path ]] && echo "not json" > "$2"; shift; done\n' \
    "$GITLEAKS_VERSION" > "$work/broken-gitleaks"
  chmod +x "$work/broken-gitleaks"
  expect 2 "unreadable report fails closed" \
    bash -c "cd '$work/clean' && GITLEAKS_BIN='$work/broken-gitleaks' '$SCRIPT_PATH' staged"

  new_repo "$work/hooks"
  (cd "$work/hooks" && "$SCRIPT_PATH" install-hooks >/dev/null)
  printf 'aws_access_key_id = %s\n' "$fake" > "$work/hooks/config.ini"
  git -C "$work/hooks" add config.ini
  expect 1 "installed pre-commit hook blocks the commit" git -C "$work/hooks" commit -qm "leak"
  # --no-verify skips pre-commit; pre-push must catch the commit on the way
  # out, even though a private remote already tracks it.
  git -C "$work/hooks" commit -qm "leak" --no-verify
  git init -q --bare "$work/hooks-private.git"
  git init -q --bare "$work/hooks-public.git"
  git -C "$work/hooks" remote add private "$work/hooks-private.git"
  git -C "$work/hooks" remote add public "$work/hooks-public.git"
  git -C "$work/hooks" push -q --no-verify private HEAD:refs/heads/main
  expect 1 "installed pre-push hook blocks the first push to another remote" \
    git -C "$work/hooks" push -q public HEAD:refs/heads/main

  if [[ "$fails" -eq 0 ]]; then echo "self-test passed"; return 0; fi
  echo "self-test failed: $fails check(s)"; return 1
}

main() {
  local cmd="${1:-}"; shift || true
  case "$cmd" in
    install) cmd_install "$@" ;;
    staged) cmd_staged "$@" ;;
    push) cmd_push "$@" ;;
    history) cmd_history "$@" ;;
    install-hooks) cmd_install_hooks ;;
    self-test) cmd_self_test ;;
    *) sed -n '2,17p' "$SCRIPT_PATH" | sed 's/^# \{0,1\}//'; [[ -z "$cmd" ]] && exit 0; exit 2 ;;
  esac
}

main "$@"
