#!/usr/bin/env bash
# Structural validator for superjawn skill ports.
#
# Usage:
#   superjawn/scripts/validate-skill.sh                    # validate all ported skills
#   superjawn/scripts/validate-skill.sh <name> [<name>...] # validate specific skills
#
# Per skill, in order:
#   1. SKILL.md exists
#   2. Frontmatter: `name:` matches directory, non-empty `description:`
#   3. Attribution block: required substrings present, block sits immediately after
#      frontmatter close (no blank line between --- and <!--)
#   4. Cross-refs: superjawn:<x> must resolve to a ported skill (SKILL.md must exist,
#      not just the directory); superpowers:<x> must NOT be a ported skill (dual-namespace
#      strict) — if ported, the reference must use superjawn:<x> instead; superpowers:<x>
#      is allowed only when <x> is an upstream skill or upstream agent
#   5. Parity (skill_md_parity: true in manifest): SKILL.md after stripping the MIT block
#      must be byte-identical to upstream SKILL.md
#   6. Supporting files: each file under skills/<name>/ other than SKILL.md is checked
#      against upstream; if it differs and is NOT in supporting_file_overrides, fail;
#      if it IS in overrides, verify the upstream counterpart exists (no phantom exceptions)
#
# Reads superjawn/scripts/skills-manifest.json for per-skill configuration.
# Exits with the number of failures (capped at 255 per shell convention).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUPERJAWN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$SUPERJAWN_DIR/skills"
MANIFEST="$SCRIPT_DIR/skills-manifest.json"
UPSTREAM_DIR="${SUPERJAWN_UPSTREAM_DIR:-$HOME/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7}"

# Verify dependencies.
if ! command -v jq &>/dev/null; then
  echo "error: jq is required but not found in PATH" >&2
  exit 2
fi

if [[ ! -f "$MANIFEST" ]]; then
  echo "error: manifest not found at $MANIFEST" >&2
  exit 2
fi

if ! jq empty "$MANIFEST" 2>/dev/null; then
  echo "error: manifest is not valid JSON: $MANIFEST" >&2
  exit 2
fi

if [[ ! -d "$UPSTREAM_DIR" ]]; then
  echo "error: upstream cache not found at $UPSTREAM_DIR" >&2
  echo "set SUPERJAWN_UPSTREAM_DIR or install claude-plugins-official/superpowers" >&2
  exit 2
fi

errors=0
checked=0

fail() {
  local name="$1" check="$2" msg="$3"
  printf 'FAIL  %-32s  [%-22s]  %s\n' "$name" "$check" "$msg"
  errors=$((errors + 1))
}

pass() {
  local name="$1" check="$2" msg="$3"
  printf 'pass  %-32s  [%-22s]  %s\n' "$name" "$check" "$msg"
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

# Extract every `<plugin>:<name>` cross-reference token from a file.
extract_crossrefs() {
  grep -oE '(superjawn|superpowers):[a-z][a-z0-9_-]*' "$1" | sort -u || true
}

# Strip the MIT attribution comment block from a SKILL.md.
# Removes: the line "<!--", all lines until and including "-->", exactly once, at start of body.
# The blank line that follows "-->" (between the block and the first H1) is preserved,
# so the result matches upstream layout.
strip_attribution_block() {
  python3 - "$1" <<'PY'
import sys, re, pathlib
text = pathlib.Path(sys.argv[1]).read_text()
# Remove <!-- ... --> block (with its trailing newline) once, at start of body.
stripped = re.sub(r'<!--\n.*?\n-->\n', '', text, count=1, flags=re.DOTALL)
sys.stdout.write(stripped)
PY
}

check_skill() {
  local name="$1"
  local skill_md="$SKILLS_DIR/$name/SKILL.md"
  local skill_errors_before=$errors

  # ------------------------------------------------------------------ #
  # Check 1: SKILL.md exists.                                           #
  # ------------------------------------------------------------------ #
  if [[ ! -f "$skill_md" ]]; then
    fail "$name" "structure" "SKILL.md missing at $skill_md"
    return
  fi

  # ------------------------------------------------------------------ #
  # Check 2: Frontmatter shape.                                         #
  # ------------------------------------------------------------------ #
  if ! head -1 "$skill_md" | grep -qx -- '---'; then
    fail "$name" "structure" "first line is not '---' (no opening frontmatter delimiter)"
    return
  fi

  local fm
  fm="$(extract_frontmatter "$skill_md")"
  if [[ -z "$fm" ]]; then
    fail "$name" "structure" "frontmatter is empty or unterminated"
    return
  fi
  if ! grep -qx -- "name: $name" <<<"$fm"; then
    fail "$name" "structure" "frontmatter 'name' field does not match directory ($name)"
  else
    pass "$name" "structure" "frontmatter ok"
  fi
  if ! grep -qE '^description: .+$' <<<"$fm"; then
    fail "$name" "structure" "frontmatter missing non-empty 'description' field"
  fi

  # ------------------------------------------------------------------ #
  # Check 3: Attribution block content and position.                    #
  # ------------------------------------------------------------------ #
  local attr_ok=true

  # Required substrings.
  local required_substrings=(
    "obra/superpowers"
    "MIT-licensed"
    "copyright 2025 Jesse Vincent"
    "copyright 2026 Joe Amditis"
    "See CREDITS.md"
    "Adapted from obra/superpowers"
  )
  for substr in "${required_substrings[@]}"; do
    if ! grep -qF "$substr" "$skill_md"; then
      fail "$name" "attribution" "attribution block missing required text: '$substr'"
      attr_ok=false
    fi
  done

  # Block must sit immediately after frontmatter close --- (no blank line between).
  # The line after the closing --- must be <!--.
  local line_after_fm_close
  line_after_fm_close="$(awk '
    /^---$/ { count++; if (count == 2) { getline; print; exit } }
  ' "$skill_md")"
  if [[ "$line_after_fm_close" != "<!--" ]]; then
    fail "$name" "attribution" "attribution block does not immediately follow frontmatter close --- (found: $(printf '%q' "$line_after_fm_close"))"
    attr_ok=false
  fi

  if [[ "$attr_ok" == true ]]; then
    pass "$name" "attribution" "attribution block ok"
  fi

  # ------------------------------------------------------------------ #
  # Check 4: Cross-reference namespace strict (dual-namespace rule).    #
  # ------------------------------------------------------------------ #
  local crossref_ok=true
  local ref plugin target
  while IFS= read -r ref; do
    [[ -z "$ref" ]] && continue
    plugin="${ref%%:*}"
    target="${ref#*:}"

    if [[ "$plugin" == "superjawn" ]]; then
      # Must resolve to a ported skill with an actual SKILL.md (not just a directory).
      [[ "$target" == "$name" ]] && continue
      if [[ ! -f "$SKILLS_DIR/$target/SKILL.md" ]]; then
        fail "$name" "cross-ref" "superjawn:$target does not resolve (no SKILL.md at $SKILLS_DIR/$target/SKILL.md)"
        crossref_ok=false
      fi
    elif [[ "$plugin" == "superpowers" ]]; then
      # Dual-namespace strict: if <target> has been ported, must use superjawn:<target>.
      if [[ -d "$SKILLS_DIR/$target" ]]; then
        fail "$name" "cross-ref" "superpowers:$target should be superjawn:$target (skill has been ported)"
        crossref_ok=false
      # Otherwise must exist upstream as a skill or an agent.
      elif [[ ! -d "$UPSTREAM_DIR/skills/$target" && ! -f "$UPSTREAM_DIR/agents/$target.md" ]]; then
        fail "$name" "cross-ref" "superpowers:$target does not resolve (no upstream skill or agent)"
        crossref_ok=false
      fi
    fi
  done < <(extract_crossrefs "$skill_md")

  if [[ "$crossref_ok" == true ]]; then
    pass "$name" "cross-ref" "all cross-refs resolve"
  fi

  # ------------------------------------------------------------------ #
  # Check 5: Parity check (consumer ports only).                        #
  # ------------------------------------------------------------------ #
  local parity_flag
  parity_flag="$(jq -r --arg s "$name" '.skills[$s].skill_md_parity // "null"' "$MANIFEST")"

  if [[ "$parity_flag" == "true" ]]; then
    local upstream_skill_md="$UPSTREAM_DIR/skills/$name/SKILL.md"
    if [[ ! -f "$upstream_skill_md" ]]; then
      fail "$name" "parity" "upstream SKILL.md not found at $upstream_skill_md"
    else
      local stripped
      stripped="$(strip_attribution_block "$skill_md")"
      local upstream_content
      upstream_content="$(cat "$upstream_skill_md")"
      if [[ "$stripped" == "$upstream_content" ]]; then
        pass "$name" "parity" "SKILL.md byte-identical to upstream after block strip"
      else
        fail "$name" "parity" "SKILL.md differs from upstream after stripping MIT block (run diff to inspect)"
      fi
    fi
  else
    pass "$name" "parity" "parity check skipped (not a consumer port)"
  fi

  # ------------------------------------------------------------------ #
  # Check 6: Supporting files walk.                                     #
  # ------------------------------------------------------------------ #
  local supporting_ok=true
  local overrides_json
  overrides_json="$(jq -r --arg s "$name" '.skills[$s].supporting_file_overrides // {}' "$MANIFEST")"

  while IFS= read -r -d '' local_file; do
    local rel_path="${local_file#$SKILLS_DIR/$name/}"
    [[ "$rel_path" == "SKILL.md" ]] && continue

    local upstream_file="$UPSTREAM_DIR/skills/$name/$rel_path"
    local in_overrides
    in_overrides="$(jq -r --arg f "$rel_path" 'has($f)' <<<"$overrides_json")"

    if [[ ! -f "$upstream_file" ]]; then
      # No upstream counterpart; overrides entry would be a phantom — skip silently.
      if [[ "$in_overrides" == "true" ]]; then
        fail "$name" "supporting-files" "override '$rel_path' references a non-existent upstream file (phantom exception)"
        supporting_ok=false
      fi
      continue
    fi

    if [[ "$in_overrides" == "true" ]]; then
      # File is in overrides; upstream file exists — this is a valid documented divergence.
      pass "$name" "supporting-files" "$rel_path: documented divergence ok"
    else
      # File must be byte-identical to upstream.
      if ! diff -q "$local_file" "$upstream_file" &>/dev/null; then
        fail "$name" "supporting-files" "$rel_path differs from upstream and is not listed in supporting_file_overrides"
        supporting_ok=false
      fi
    fi
  done < <(find "$SKILLS_DIR/$name" -type f -print0 | sort -z)

  if [[ "$supporting_ok" == true ]]; then
    pass "$name" "supporting-files" "all supporting files ok"
  fi

  if (( errors == skill_errors_before )); then
    : # individual pass lines already printed above
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
exit "$(( errors > 255 ? 255 : errors ))"
