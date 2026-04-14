#!/usr/bin/env bash
# pdf-playground SessionStart hook — checks GitHub for a newer plugin version
# once every 24 hours and prints a one-line warning if the installed copy is
# out of date. Silent on network failure so the user's session never gets
# delayed or polluted by this check.

set -eu

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"
PLUGIN_JSON="$PLUGIN_ROOT/.claude-plugin/plugin.json"

# Marketplace raw URL — points at master so it always reflects the latest
# published version of pdf-playground regardless of tag cadence.
REMOTE_URL="https://raw.githubusercontent.com/jamditis/claude-skills-journalism/master/pdf-playground/.claude-plugin/plugin.json"

CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/pdf-playground"
CACHE_FILE="$CACHE_DIR/last-version-check"
CACHE_TTL_SECONDS=86400  # 24 hours

# Drain stdin — Claude Code pipes session context here and we want to
# acknowledge it without blocking the caller. The contents are unused.
cat > /dev/null || true

# Bail silently if the local plugin.json is missing or unreadable. A broken
# install should not make session start louder.
[ -r "$PLUGIN_JSON" ] || exit 0

# Need jq + curl for this to work at all. If either is missing, skip silently
# — we don't want an optional update check to become a hard dependency.
command -v jq   >/dev/null 2>&1 || exit 0
command -v curl >/dev/null 2>&1 || exit 0

LOCAL_VERSION=$(jq -r '.version // empty' "$PLUGIN_JSON" 2>/dev/null || true)
[ -n "$LOCAL_VERSION" ] || exit 0

# Rate-limit: skip the network call if the cache file was touched within the
# last CACHE_TTL_SECONDS. This keeps us well under any sensible GitHub rate
# limit even for users who open dozens of sessions a day.
mkdir -p "$CACHE_DIR" 2>/dev/null || exit 0
if [ -f "$CACHE_FILE" ]; then
  NOW=$(date +%s)
  LAST=$(stat -c %Y "$CACHE_FILE" 2>/dev/null || stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0)
  AGE=$(( NOW - LAST ))
  if [ "$AGE" -lt "$CACHE_TTL_SECONDS" ]; then
    exit 0
  fi
fi

# Fetch with a short timeout; bail silently on any network trouble.
REMOTE_JSON=$(curl -fsSL --max-time 3 "$REMOTE_URL" 2>/dev/null || true)
[ -n "$REMOTE_JSON" ] || exit 0

REMOTE_VERSION=$(printf '%s' "$REMOTE_JSON" | jq -r '.version // empty' 2>/dev/null || true)
[ -n "$REMOTE_VERSION" ] || exit 0

# Touch the cache file regardless of whether we print a warning — the point
# is to rate-limit the *check*, not the warning itself.
: > "$CACHE_FILE"

# Compare with `sort -V` so 1.10.0 sorts after 1.9.0 the way a human expects.
# If LOCAL is already >= REMOTE, nothing to say.
LATEST=$(printf '%s\n%s\n' "$LOCAL_VERSION" "$REMOTE_VERSION" | sort -V | tail -n1)
if [ "$LATEST" = "$LOCAL_VERSION" ]; then
  exit 0
fi

cat <<MSG
pdf-playground v$REMOTE_VERSION is available (installed: v$LOCAL_VERSION). Run /pdf-playground:update to upgrade, or skip with \`rm $CACHE_FILE\` to recheck later.
MSG
