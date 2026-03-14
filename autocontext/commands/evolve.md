---
description: Evolve skill files by integrating validated lessons from real usage
---

This command improves skill .md files based on lessons accumulated in the global skill lesson store.

## Argument handling

The user may invoke this command with arguments:
- `/autocontext-evolve` — default: scan and evolve interactively
- `/autocontext-evolve --rollback <skill-name>` — restore from backup
- `/autocontext-evolve --export` — export lessons to JSON
- `/autocontext-evolve --import <path>` — import lessons from JSON

Parse the arguments from the user's input. If `--rollback` is present, run the rollback flow. If `--export` or `--import`, run the sync flow. Otherwise, run the default evolution flow.

## Default evolution flow

1. Run the scan script to find eligible skills:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/skill-evolution/scan_eligible.sh"
   ```

2. If no skills are eligible, report that and exit.

3. Present the summary to the user using AskUserQuestion: which skill(s) to evolve? Include lesson count and average confidence per skill. Add an "All" option and a "Skip" option.

4. For each selected skill:
   a. Read the current skill .md file using the `find_skill_path` function:
      ```bash
      python3 -c "
      import sys
      sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts/skill-evolution')
      from apply_edit import find_skill_path
      path = find_skill_path('SKILL_NAME')
      print(path or 'NOT_FOUND')
      "
      ```
   b. If NOT_FOUND, warn and skip.
   c. Read the skill file content.
   d. Run generate_diff to create an improved version:
      ```bash
      python3 -c "
      import sys, json
      sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts/skill-evolution')
      from generate_diff import generate_evolved_skill
      from store import get_eligible_lessons

      lessons = get_eligible_lessons('SKILL_NAME')
      with open('SKILL_PATH') as f:
          content = f.read()
      result = generate_evolved_skill(content, lessons)
      if result:
          print(result)
      else:
          print('GENERATION_FAILED')
      "
      ```
   e. If generation failed, offer the append fallback.
   f. Show a diff between the original and evolved content.
   g. Ask the user via AskUserQuestion:
      - **Accept** — apply the edit
      - **Edit** — let user make manual changes first
      - **Reject** — skip, lessons stay
      - **Append instead** — use the fallback section
   h. Apply the chosen action using apply_edit functions.
   i. Mark evolved lessons as folded.

## Rollback flow

```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts/skill-evolution')
from apply_edit import rollback
backup, restored = rollback('SKILL_NAME')
if restored:
    print(f'Restored {restored} from {backup}')
else:
    print('No backup found for SKILL_NAME')
"
```

## Export flow

Uses `sync.py` (no inline duplication):

```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts/skill-evolution')
from sync import export_all
path = export_all()
print(f'Exported to {path}')
"
```

## Import flow

Uses `sync.py` (no inline duplication):

```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts/skill-evolution')
from sync import import_lessons
summary = import_lessons('IMPORT_PATH')
for skill, counts in summary.items():
    print(f'{skill}: added {counts[\"added\"]}, merged {counts[\"merged\"]}')
"
```
