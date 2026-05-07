#!/usr/bin/env bash
# Structural validator for superjawn skill ports.
#
# Usage:
#   superjawn/scripts/validate-skill.sh                    # validate all ported skills
#   superjawn/scripts/validate-skill.sh <name> [<name>...] # validate specific skills
#
# Per skill, asserts:
#   1. SKILL.md exists at superjawn/skills/<name>/SKILL.md
#   2. Frontmatter present with `name: <name>` and a non-empty `description:`
#   3. MIT attribution comment block present (mentions obra/superpowers, MIT,
#      and CREDITS.md per the v0.1.0 attribution pattern)
#   4. Every `superjawn:<x>` cross-reference points to a ported skill
#      (superjawn/skills/<x>/ exists)
#   5. Every `superpowers:<x>` cross-reference points to an upstream skill
#      OR an upstream agent (skills/<x>/ or agents/<x>.md in the cached release)
#
# Exits non-zero if any assertion fails.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUPERJAWN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$SUPERJAWN_DIR/skills"
UPSTREAM_DIR="${SUPERJAWN_UPSTREAM_DIR:-$HOME/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7}"

if [[ ! -d "$UPSTREAM_DIR" ]]; then
  echo "error: upstream cache not found at $UPSTREAM_DIR" >&2
  echo "set SUPERJAWN_UPSTREAM_DIR or install claude-plugins-official/superpowers" >&2
  exit 2
fi

errors=0
checked=0

fail() {
  local name="$1" msg="$2"
  printf 'FAIL  %-32s  %s\n' "$name" "$msg"
  errors=$((errors + 1))
}

pass() {
  local name="$1" msg="$2"
  printf 'pass  %-32s  %s\n' "$name" "$msg"
}

# Extract frontmatter block (between the first two `---` lines).
extract_frontmatter() {
  awk '
    BEGIN { in_fm = 0; seen = 0 }
    /^---$/ {
      if (!seen) { in_fm = 1; seen = 1; next }
      else if (in_fm) { exit }
    }
    in_fm { print }
  ' "$1"
}

# Extract every `<plugin>:<name>` cross-reference token.
extract_crossrefs() {
  grep -oE '(superjawn|superpowers):[a-z][a-z0-9_-]*' "$1" | sort -u || true
}

check_skill() {
  local name="$1"
  local skill_md="$SKILLS_DIR/$name/SKILL.md"
  local skill_errors_before=$errors

  if [[ ! -f "$skill_md" ]]; then
    fail "$name" "SKILL.md missing at $skill_md"
    return
  fi

  # 1+2. Frontmatter shape.
  if ! head -1 "$skill_md" | grep -qx -- '---'; then
    fail "$name" "first line is not '---' (no opening frontmatter delimiter)"
    return
  fi

  local fm
  fm="$(extract_frontmatter "$skill_md")"
  if [[ -z "$fm" ]]; then
    fail "$name" "frontmatter is empty or unterminated"
    return
  fi
  if ! grep -qx -- "name: $name" <<<"$fm"; then
    fail "$name" "frontmatter 'name' field does not match directory ($name)"
  fi
  if ! grep -qE '^description: .+$' <<<"$fm"; then
    fail "$name" "frontmatter missing non-empty 'description' field"
  fi

  # 3. MIT attribution.
  if ! grep -q 'obra/superpowers' "$skill_md"; then
    fail "$name" "MIT attribution missing reference to obra/superpowers"
  fi
  if ! grep -q 'MIT-licensed' "$skill_md"; then
    fail "$name" "MIT attribution missing 'MIT-licensed' phrasing"
  fi
  if ! grep -q 'See CREDITS.md' "$skill_md"; then
    fail "$name" "MIT attribution missing 'See CREDITS.md' pointer"
  fi

  # 4+5. Cross-references resolve.
  local ref plugin target
  while IFS= read -r ref; do
    [[ -z "$ref" ]] && continue
    plugin="${ref%%:*}"
    target="${ref#*:}"

    if [[ "$plugin" == "superjawn" ]]; then
      # Self-reference is fine (skill referring to itself in examples).
      [[ "$target" == "$name" ]] && continue
      if [[ ! -d "$SKILLS_DIR/$target" ]]; then
        fail "$name" "cross-ref superjawn:$target does not resolve (not ported in this repo)"
      fi
    elif [[ "$plugin" == "superpowers" ]]; then
      if [[ ! -d "$UPSTREAM_DIR/skills/$target" && ! -f "$UPSTREAM_DIR/agents/$target.md" ]]; then
        fail "$name" "cross-ref superpowers:$target does not resolve (no upstream skill or agent)"
      fi
    fi
  done < <(extract_crossrefs "$skill_md")

  if (( errors == skill_errors_before )); then
    pass "$name" "ok"
  fi
  checked=$((checked + 1))
}

if [[ $# -eq 0 ]]; then
  for d in "$SKILLS_DIR"/*/; do
    check_skill "$(basename "$d")"
  done
else
  for name in "$@"; do
    check_skill "$name"
  done
fi

echo
printf 'checked: %d, errors: %d\n' "$checked" "$errors"
exit "$errors"
