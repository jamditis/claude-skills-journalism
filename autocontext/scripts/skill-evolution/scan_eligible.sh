#!/usr/bin/env bash
set -euo pipefail

# Scan for skills with lessons eligible for evolution
# Outputs JSON summary of eligible skills

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(dirname "$0")")")}"
SCRIPT_DIR="$(dirname "$0")"

source "$PLUGIN_ROOT/scripts/config-utils.sh"

STORE_PATH=$(read_config "skill_learning.global_store" "$HOME/.claude/skill-lessons")
STORE_PATH="${STORE_PATH/#\~/$HOME}"

EVOLUTION_CONFIDENCE=$(read_config "skill_learning.evolution_confidence" "0.85")
EVOLUTION_MIN_VALIDATIONS=$(read_config "skill_learning.evolution_min_validations" "3")
BACKUP_DIR=$(read_config "skill_learning.backup_dir" "$HOME/.claude/skill-lessons/backups")
BACKUP_DIR="${BACKUP_DIR/#\~/$HOME}"
MODEL_CMD=$(read_config "skill_learning.evolution_model" "claude -p")

# Ensure store exists
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from store import ensure_store
ensure_store('$STORE_PATH')
"

# Scan for eligible skills and output JSON summary
export AUTOCONTEXT_SCRIPT_DIR="$SCRIPT_DIR"
export AUTOCONTEXT_STORE_PATH="$STORE_PATH"
export AUTOCONTEXT_EVOLUTION_CONFIDENCE="$EVOLUTION_CONFIDENCE"
export AUTOCONTEXT_EVOLUTION_MIN_VALIDATIONS="$EVOLUTION_MIN_VALIDATIONS"

python3 - <<'PYEOF'
import sys
import json
import os

script_dir = os.environ["AUTOCONTEXT_SCRIPT_DIR"]
store_path = os.environ["AUTOCONTEXT_STORE_PATH"]
min_conf = float(os.environ["AUTOCONTEXT_EVOLUTION_CONFIDENCE"])
min_vals = int(os.environ["AUTOCONTEXT_EVOLUTION_MIN_VALIDATIONS"])

sys.path.insert(0, script_dir)
from store import load_index, get_eligible_lessons

index = load_index(store_path)
summary = {}
for skill_name in index.get("skills", {}):
    eligible = get_eligible_lessons(
        skill_name,
        min_confidence=min_conf,
        min_validations=min_vals,
        store_path=store_path,
    )
    if eligible:
        avg_conf = sum(l.get("confidence", 0) for l in eligible) / len(eligible)
        projects = set()
        for l in eligible:
            projects.update(l.get("source_projects", []))
        summary[skill_name] = {
            "count": len(eligible),
            "avg_confidence": round(avg_conf, 2),
            "source_projects": sorted(projects),
            "lessons": eligible,
        }

if not summary:
    print("No skills have lessons eligible for evolution.")
else:
    print(json.dumps(summary, indent=2))
PYEOF
