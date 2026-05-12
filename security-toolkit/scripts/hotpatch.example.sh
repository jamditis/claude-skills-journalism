#!/usr/bin/env bash
# hotpatch — bypass the supply-chain cooldown for one install, after a
# sandboxed pre-install scan. Defends against attacks that ship within the
# 7-day cooldown window (e.g. Mini Shai-Hulud, TanStack 2026-05-11).
#
# Usage:
#   hotpatch <pkg>[@<version>] [--manager npm|bun] [--force] [--yes]
#   hotpatch --scan-local <tarball-path>            # offline test mode
#   hotpatch --self-test                            # run unit fixtures
#
# Defaults:
#   --manager autodetected from cwd (bun.lock → bun, package.json → npm)
#   --version "latest"
#   Install runs with --ignore-scripts (postinstall is the #1 attack vector)
#
# Exit 0 on success, 1 on user-visible error, 2 on red-flag abort.
set -euo pipefail

VERSION="0.1.0"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
SCAN_DIR=""
trap 'cleanup' EXIT

cleanup() { [ -n "${SCAN_DIR:-}" ] && [ -d "$SCAN_DIR" ] && rm -rf "$SCAN_DIR"; }
die() { echo "hotpatch: $*" >&2; exit 1; }
warn() { echo "WARN: $*" >&2; }

declare -a FLAGS_RED=()
declare -a FLAGS_YELLOW=()
flag_red() { FLAGS_RED+=("$*"); echo "  RED  $*"; }
flag_yellow() { FLAGS_YELLOW+=("$*"); echo "  YEL  $*"; }

print_usage() {
  cat <<EOF
hotpatch v$VERSION — sandboxed bypass for npm/bun cooldown

  hotpatch <pkg>[@<version>] [--manager npm|bun] [--force] [--yes]
  hotpatch --scan-local <tarball-path>
  hotpatch --self-test

Flags:
  --manager npm|bun   Force package manager (default: autodetect from cwd)
  --force             Install even if red flags raised
  --yes, -y           Skip interactive confirm
  --scan-local PATH   Scan a local .tgz/.tar.gz without registry/network
  --self-test         Run unit-test fixtures and exit
EOF
}

# ---- Parse args ----
PKG=""
MANAGER=""
FORCE=0
ASSUME_YES=0
SCAN_LOCAL=""
SELF_TEST=0
while [ $# -gt 0 ]; do
  case "$1" in
    --manager)     MANAGER="$2"; shift 2 ;;
    --force)       FORCE=1; shift ;;
    --yes|-y)      ASSUME_YES=1; shift ;;
    --scan-local)  SCAN_LOCAL="$2"; shift 2 ;;
    --self-test)   SELF_TEST=1; shift ;;
    -h|--help)     print_usage; exit 0 ;;
    -*)            die "unknown flag: $1" ;;
    *)             PKG="$1"; shift ;;
  esac
done

# ---- Static-check functions ----
# Each takes the extracted package root and updates FLAGS_RED/FLAGS_YELLOW.

check_install_hooks() {
  local pkg_root="$1" pkg_json="$1/package.json"
  [ -f "$pkg_json" ] || { flag_red "missing package.json"; return; }
  local hooks
  hooks=$(python3 - "$pkg_json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
scripts = p.get('scripts', {})
risky = {k: v for k, v in scripts.items()
         if k in ('preinstall', 'install', 'postinstall', 'prepare', 'prepublish')}
for k, v in risky.items():
    print(f'{k}={v}')
PY
)
  if [ -n "$hooks" ]; then
    flag_yellow "install/prepare hooks present (will be skipped via --ignore-scripts):"
    echo "$hooks" | sed 's/^/         /'
  fi
}

check_git_deps() {
  local pkg_root="$1" pkg_json="$1/package.json"
  [ -f "$pkg_json" ] || return
  local sus
  sus=$(python3 - "$pkg_json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
out = []
for field in ('dependencies', 'optionalDependencies', 'peerDependencies'):
    for k, v in (p.get(field) or {}).items():
        if isinstance(v, str) and ('github:' in v or v.startswith('git+') or v.startswith('git@')):
            out.append(f'{field}.{k} = {v}')
print('\n'.join(out))
PY
)
  if [ -n "$sus" ]; then
    flag_red "git URLs in dependency fields (Mini Shai-Hulud pattern):"
    echo "$sus" | sed 's/^/         /'
  fi
}

check_large_root_js() {
  # Flag large JS at the package root that ISN'T declared in package.json.
  # Mini Shai-Hulud planted router_init.js at root, undeclared. Legitimate
  # bundle files (lodash.js, react.production.min.js) are always referenced
  # by main/module/exports/bin/files.
  local pkg_root="$1" pkg_json="$1/package.json"
  local unref
  unref=$(python3 - "$pkg_root" "$pkg_json" <<'PY'
import json, os, sys
root, manifest = sys.argv[1], sys.argv[2]
declared = set()
try:
    p = json.load(open(manifest))
except Exception:
    p = {}

def add(v):
    if isinstance(v, str):
        declared.add(os.path.normpath(v.lstrip('./')))
    elif isinstance(v, dict):
        for x in v.values():
            add(x)
    elif isinstance(v, list):
        for x in v:
            add(x)

for k in ('main', 'module', 'browser', 'types', 'typings'):
    add(p.get(k))
add(p.get('exports'))
add(p.get('bin'))
add(p.get('files'))

flagged = []
for entry in os.listdir(root):
    path = os.path.join(root, entry)
    if not os.path.isfile(path):
        continue
    if not entry.endswith(('.js', '.mjs', '.cjs')):
        continue
    if os.path.getsize(path) < 500 * 1024:
        continue
    # Match against any declared path that references this entry
    if any(entry == d or entry == os.path.basename(d) for d in declared):
        continue
    flagged.append(f'{entry} ({os.path.getsize(path)//1024}KB)')
print('\n'.join(flagged))
PY
)
  if [ -n "$unref" ]; then
    flag_red "large unreferenced JS at package root (Mini Shai-Hulud planted router_init.js this way):"
    echo "$unref" | sed 's/^/         /'
  fi
}

check_credential_paths() {
  # Look for string references to sensitive paths in *.js files near the root.
  local pkg_root="$1"
  local matches
  matches=$(grep -rEo --include='*.js' --include='*.mjs' --include='*.cjs' \
    -l '\.ssh/|\.aws/|\.npmrc|\.gnupg|GITHUB_TOKEN|AWS_SECRET|VAULT_TOKEN|/etc/shadow|kube/config' \
    "$pkg_root" 2>/dev/null | head -5 || true)
  if [ -n "$matches" ]; then
    flag_yellow "files reference credential/secret paths:"
    echo "$matches" | sed "s|$pkg_root/||; s/^/         /"
  fi
}

# ---- Sandboxed extract ----
sandboxed_extract() {
  local tarball="$1" dest="$2"
  mkdir -p "$dest"
  # bwrap: no network, ro system, only the scan dir is writable.
  # /bin and /lib are symlinks into /usr on Debian unified-/usr layout, so
  # binding /usr alone is sufficient. Add symlinks back inside the sandbox so
  # tools that hardcode /bin/sh still work.
  bwrap \
    --ro-bind /usr /usr \
    --symlink usr/bin /bin \
    --symlink usr/lib /lib \
    --symlink usr/lib /lib64 \
    --ro-bind-try /etc/alternatives /etc/alternatives \
    --bind "$(dirname "$tarball")" "$(dirname "$tarball")" \
    --bind "$dest" "$dest" \
    --proc /proc --dev /dev \
    --setenv PATH /usr/bin:/usr/local/bin \
    --unshare-all --die-with-parent \
    -- \
    /usr/bin/tar -xzf "$tarball" -C "$dest"
}

# ---- Run the scan against an extracted package ----
run_static_checks() {
  local pkg_root="$1"
  echo "==> static checks"
  check_install_hooks  "$pkg_root"
  check_git_deps       "$pkg_root"
  check_large_root_js  "$pkg_root"
  check_credential_paths "$pkg_root"
}

# ---- Registry helpers ----
fetch_meta() {
  local name="$1"
  curl -fsSL "https://registry.npmjs.org/${name//\//%2F}" 2>/dev/null
}

resolve_version() {
  local meta="$1" req="$2"
  python3 - "$req" <<PY
import json, sys
d = json.loads('''$meta''') if False else None
PY
}

# ---- OSV.dev (free, no auth) + npm deprecation check ----
check_external() {
  local name="$1" version="$2" meta_file="$3"
  echo "==> external feeds"

  # 1. npm registry deprecation flag (TanStack used this to mark compromised versions)
  local deprecated
  deprecated=$(python3 - "$meta_file" "$version" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
v = sys.argv[2]
info = d['versions'].get(v, {})
print(info.get('deprecated', ''))
PY
)
  if [ -n "$deprecated" ]; then
    if echo "$deprecated" | grep -qiE 'security|compromise|malicious|do not|vulnerab'; then
      flag_red "registry marks this version deprecated for security:"
      echo "         $deprecated" | head -2 | sed 's/^/         /'
    else
      flag_yellow "registry marks this version deprecated:"
      echo "         $deprecated" | head -2 | sed 's/^/         /'
    fi
  fi

  # 2. OSV.dev — free public vulnerability database
  local osv_resp
  osv_resp=$(curl -fsSL --max-time 10 -X POST "https://api.osv.dev/v1/query" \
    -d "{\"package\":{\"name\":\"$name\",\"ecosystem\":\"npm\"},\"version\":\"$version\"}" 2>/dev/null) \
    || { echo "         osv api unavailable (skipped)"; return; }
  local osv_count
  osv_count=$(echo "$osv_resp" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    vulns = d.get('vulns', [])
    print(len(vulns))
    for v in vulns[:5]:
        sev = v.get('database_specific', {}).get('severity', '?')
        print(f\"  {v.get('id','?')} ({sev}): {v.get('summary','')[:80]}\", file=sys.stderr)
except Exception as e:
    print(0)
" 2>&1)
  # python wrote count to stdout and per-vuln lines to stderr; capture both
  local count_line=$(echo "$osv_resp" | python3 -c "
import json,sys
try: d=json.load(sys.stdin); print(len(d.get('vulns',[])))
except: print(0)
")
  if [ "$count_line" -gt 0 ]; then
    flag_red "OSV.dev reports $count_line known vulnerability/vulnerabilities for this version"
    echo "$osv_resp" | python3 -c "
import json, sys
d = json.load(sys.stdin)
for v in d.get('vulns', [])[:5]:
    sev = v.get('database_specific', {}).get('severity', '?')
    print(f\"         {v.get('id','?')} ({sev}): {v.get('summary','')[:90]}\")
"
  else
    echo "         OSV: no known vulnerabilities for $name@$version"
  fi
}

# ---- Main flows ----
do_self_test() {
  # Look for the fixture in (1) the plugin's test-fixtures dir relative to this
  # script, (2) ~/.claude/hotpatch-fixtures/ (officejawn convention).
  local fixture
  for candidate in \
      "$SCRIPT_DIR/../test-fixtures/fake-mini-shai.tgz" \
      "$HOME/.claude/hotpatch-fixtures/fake-mini-shai.tgz"; do
    if [ -f "$candidate" ]; then fixture="$candidate"; break; fi
  done
  [ -n "${fixture:-}" ] || die "self-test fixture not found (looked in ../test-fixtures/ and ~/.claude/hotpatch-fixtures/)"
  echo "==> self-test: scanning $fixture"
  SCAN_DIR=$(mktemp -d /tmp/hotpatch.XXXXXX)
  sandboxed_extract "$fixture" "$SCAN_DIR/extracted"
  run_static_checks "$SCAN_DIR/extracted/package"
  echo
  echo "expected: 1+ RED (git URL in deps, large root JS), 1+ YEL (postinstall hook)"
  echo "got:      ${#FLAGS_RED[@]} red, ${#FLAGS_YELLOW[@]} yellow"
  if [ "${#FLAGS_RED[@]}" -ge 2 ] && [ "${#FLAGS_YELLOW[@]}" -ge 1 ]; then
    echo "SELF-TEST PASSED"
    exit 0
  else
    echo "SELF-TEST FAILED — scan did not flag the synthetic Mini Shai-Hulud fixture"
    exit 1
  fi
}

do_scan_local() {
  local tarball="$1"
  [ -f "$tarball" ] || die "tarball not found: $tarball"
  SCAN_DIR=$(mktemp -d /tmp/hotpatch.XXXXXX)
  sandboxed_extract "$tarball" "$SCAN_DIR/extracted"
  local pkg_root="$SCAN_DIR/extracted/package"
  [ -d "$pkg_root" ] || die "tarball did not extract a 'package/' directory"
  run_static_checks "$pkg_root"
  echo
  echo "==> summary: ${#FLAGS_RED[@]} red, ${#FLAGS_YELLOW[@]} yellow (scan-local: no install attempted)"
  [ "${#FLAGS_RED[@]}" -gt 0 ] && exit 2 || exit 0
}

do_hotpatch() {
  [ -n "$PKG" ] || { print_usage; die "missing package name"; }

  # Manager autodetect
  if [ -z "$MANAGER" ]; then
    if [ -f bun.lock ] || [ -f bun.lockb ]; then MANAGER=bun
    elif [ -f package.json ] || [ -f package-lock.json ]; then MANAGER=npm
    else die "no package.json in cwd; specify --manager npm|bun"; fi
  fi

  # Parse name@version
  local name version_req
  case "$PKG" in
    @*/*@*)  name="${PKG%@*}"; version_req="${PKG##*@}" ;;
    @*/*)    name="$PKG";      version_req="latest" ;;
    *@*)     name="${PKG%@*}"; version_req="${PKG##*@}" ;;
    *)       name="$PKG";      version_req="latest" ;;
  esac

  echo "==> hotpatch: $name@$version_req via $MANAGER"

  # Set up scan dir first so we can spool metadata
  SCAN_DIR=$(mktemp -d /tmp/hotpatch.XXXXXX)
  local meta_file="$SCAN_DIR/meta.json"

  # Fetch metadata to disk (big JSON breaks heredoc interpolation)
  curl -fsSL "https://registry.npmjs.org/${name//\//%2F}" -o "$meta_file" \
    || die "package not found on registry: $name"

  local tarball_url version pub_date age_days
  read -r version tarball_url pub_date age_days < <(python3 - "$meta_file" "$version_req" <<'PY'
import json, sys
from datetime import datetime, timezone
d = json.load(open(sys.argv[1]))
v = sys.argv[2]
if v == 'latest':
    v = d['dist-tags']['latest']
if v not in d['versions']:
    sys.exit(f"version {v} not found on registry")
tb = d['versions'][v]['dist']['tarball']
pub = d['time'].get(v, '')
if pub:
    age = int((datetime.now(timezone.utc) - datetime.fromisoformat(pub.replace('Z','+00:00'))).total_seconds() / 86400)
else:
    age = -1
print(v, tb, pub or '?', age)
PY
) || die "version resolution failed"

  echo "         resolved: $name@$version  (published $pub_date, age ${age_days}d)"

  # Download tarball
  local tarball="$SCAN_DIR/pkg.tgz"
  curl -fsSL -o "$tarball" "$tarball_url" || die "tarball download failed"
  local size_kb=$(( $(stat -c%s "$tarball") / 1024 ))
  echo "         tarball:  ${size_kb}KB"

  # Size + fileCount delta vs prior version, using registry metadata (no
  # second HEAD request — Cloudflare HEAD responses sometimes drop Content-Length).
  local prior this_size this_files prior_size prior_files
  read -r prior this_size this_files prior_size prior_files < <(python3 - "$meta_file" "$version" <<'PY'
import json, sys
from datetime import datetime
d = json.load(open(sys.argv[1]))
this_v = sys.argv[2]
times = d['time']
if this_v not in times or this_v not in d['versions']:
    print('', 0, 0, 0, 0); sys.exit()
this_dist = d['versions'][this_v]['dist']
this_size = this_dist.get('unpackedSize') or 0
this_files = this_dist.get('fileCount') or 0
this = datetime.fromisoformat(times[this_v].replace('Z','+00:00'))
def is_stable(v):
    # Skip prereleases (5.7.0-dev.x, 1.0.0-rc.1, etc.) so baseline is meaningful.
    return '-' not in v
older = [(v, times[v]) for v in d['versions']
         if v != this_v and v in times and is_stable(v)
         and datetime.fromisoformat(times[v].replace('Z','+00:00')) < this]
older.sort(key=lambda x: x[1], reverse=True)
if older:
    prev = older[0][0]
    pd = d['versions'][prev]['dist']
    print(prev, this_size, this_files,
          pd.get('unpackedSize') or 0, pd.get('fileCount') or 0)
else:
    print('', this_size, this_files, 0, 0)
PY
)

  if [ -n "$prior" ] && [ "$prior_size" -gt 0 ]; then
    local size_ratio file_delta
    size_ratio=$(( this_size * 100 / prior_size ))
    file_delta=$(( this_files - prior_files ))
    echo "         vs $prior:  unpackedSize ${prior_size}B (this is ${size_ratio}%), fileCount ${prior_files} (delta: $file_delta)"
    if [ "$size_ratio" -gt 300 ]; then
      flag_red "unpacked size is ${size_ratio}% of prior version — 3x+ growth is rare in legit releases"
    elif [ "$size_ratio" -gt 150 ]; then
      flag_yellow "unpacked size is ${size_ratio}% of prior version — sanity-check what was added"
    fi
    # File count jump without proportional size change = single fat payload (Mini Shai-Hulud pattern).
    if [ "$file_delta" -gt 0 ] && [ "$file_delta" -lt 5 ] && [ "$size_ratio" -gt 200 ]; then
      flag_red "added $file_delta file(s) but size jumped ${size_ratio}% — consistent with a single planted payload"
    fi
  fi

  # Extract and scan
  sandboxed_extract "$tarball" "$SCAN_DIR/extracted"
  local pkg_root="$SCAN_DIR/extracted/package"
  [ -d "$pkg_root" ] || die "tarball did not extract a 'package/' directory"
  run_static_checks "$pkg_root"
  check_external "$name" "$version" "$meta_file"

  # Report
  echo
  echo "==> report"
  echo "    package:     $name@$version"
  echo "    published:   $pub_date (${age_days}d ago)"
  echo "    tarball:     ${size_kb}KB"
  echo "    red flags:   ${#FLAGS_RED[@]}"
  echo "    yellow flags: ${#FLAGS_YELLOW[@]}"

  if [ "${#FLAGS_RED[@]}" -gt 0 ] && [ "$FORCE" -eq 0 ]; then
    echo
    die "ABORT: red flags present. Re-run with --force to install anyway, or pick a different version."
  fi

  if [ "$ASSUME_YES" -eq 0 ]; then
    echo
    read -p "proceed with install? [y/N] " ans
    case "$ans" in y|Y|yes) ;; *) die "aborted by user" ;; esac
  fi

  echo
  echo "==> installing $name@$version via $MANAGER (--ignore-scripts, --bypass cooldown)"
  case "$MANAGER" in
    npm) npm install "${name}@${version}" --min-release-age=0 --ignore-scripts ;;
    bun) bun add "${name}@${version}" --minimum-release-age=0 --ignore-scripts ;;
    *)   die "unknown manager: $MANAGER" ;;
  esac

  echo
  echo "==> done. Install scripts were SKIPPED."
  echo "    If $name needs postinstall (native modules), inspect the script and"
  echo "    re-run manually after review:  (cd node_modules/$name && npm run postinstall)"
}

# ---- Dispatch ----
if [ "$SELF_TEST" -eq 1 ]; then do_self_test; fi
if [ -n "$SCAN_LOCAL" ]; then do_scan_local "$SCAN_LOCAL"; fi
do_hotpatch
