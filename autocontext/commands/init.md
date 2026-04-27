---
description: Initialize .autocontext/ in the current project for knowledge persistence
---

Initialize the autocontext knowledge directory in the current project. Use AskUserQuestion for setup decisions.

## Pre-initialization check

First, the script checks if `.autocontext/` already exists in the project root. If it does, you'll be informed and asked:

**Question:** This project already has autocontext initialized. Reinitialize?

**Options:**
- Yes — set up fresh configuration (existing lessons are NOT deleted)
- No — exit and use current setup

If you choose to reinitialize, existing lessons in `.autocontext/lessons.json` will be preserved but all config files will be reset.

## Setup questions

### Step 1: Seed from CLAUDE.md (if applicable)

If a `CLAUDE.md` file exists in the project root:

**Question:** This project has a CLAUDE.md. Seed initial lessons from it?

**Options:**
- Yes, extract and let me review each one — parses CLAUDE.md and shows each extracted lesson for approval
- Yes, extract automatically — extracts all lessons without review
- No, start fresh — begins with empty lessons

This helps bootstrap project knowledge from existing documentation.

### Step 2: Cross-developer sharing

**Question:** Will other developers use Claude Code on this repo?

**Options:**
- Yes, set up cross-developer sharing — enables the union merge driver for collaborative lesson management
- No, just me — single-developer setup, simpler merge strategy

Cross-developer sharing allows multiple Claude instances to work on the same lessons.json without conflicts.

### Step 3: Performance baselines

**Question:** Track test/build performance baselines?

**Options:**
- Yes — initialize baseline tracking for test and build performance
- No — skip baseline tracking

Performance baselines help detect regressions in test suite and build times over time.

## Directory structure creation

The script will create the following structure in `.autocontext/`:

```
.autocontext/
├── config.json              # Project configuration (shared)
├── config.local.json        # Local developer identity
├── lessons.json             # Accumulated lessons (git-tracked)
├── playbook.md              # Curated lesson playbook (auto-generated)
├── .gitignore               # Ignore cache and local files
├── .gitattributes           # (if sharing enabled) Configure merge driver
├── cache/                   # Temporary files (not git-tracked)
│   ├── pending-lessons.json # (if ask_before_persist) Awaiting approval
│   └── curated-pending.json # From /autocontext:review sessions
└── archive/                 # Tombstoned lessons (git-tracked)
    └── superseded.json      # Deleted lessons for reference
```

## Configuration templates

The script copies template files from `${CLAUDE_PLUGIN_ROOT}/templates/`:
- `config.json` — project-level settings
- `config.local.json` — developer identity and preferences
- `lessons.json` — empty initial lessons
- `.gitignore` — excludes cache and local files
- `.gitattributes` — (if sharing) configures union merge driver

The `project_name` in config.json will be set to the git repository name or directory basename if not in a git repo.

## Global config inheritance

After copying the config template, merge values from `~/.claude/autocontext.json` (if it exists) into the project's `config.json`. Global settings provide defaults; per-project config can override them later.

Mapping from global to project config:
- `lesson_loading.max_lessons` → `max_session_lessons`
- `lesson_loading.min_confidence` → `confidence_threshold`
- `staleness.days` → `staleness_days`
- `performance_baselines.enabled` → `performance_baselines`
- `performance_baselines.baseline_commands` → `baseline_commands` (only if user chose custom commands)
- `pretooluse_injection.mode` → `pretooluse_hook`
- `lesson_persistence.strategy` → `persistence_mode` (`auto_persist_with_review` → `auto_curated`, `ask_before_persist` → `ask_before_persist`, `auto_persist_all` → `auto_all`)
- `correction_sensitivity` → `correction_sensitivity`
- `playbook.generation` → `playbook_generation`
- `multi_machine` → `multi_machine`
- `test_quality_rules` → `builtin_rules`
- `identity` → written to `config.local.json`

## Cross-developer merge driver

If you selected cross-developer sharing, the script will:

1. Copy `.gitattributes` template
2. Install the union merge driver via git config:
   ```
   git config merge.autocontext-union.name "Autocontext lessons.json union merge"
   git config merge.autocontext-union.driver "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/merge-driver.py %O %A %B"
   ```

This allows `lessons.json` to be merged non-destructively when multiple developers commit lessons in parallel.

## CLAUDE.md seeding (if enabled)

If you selected CLAUDE.md seeding, the script runs:
```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/seed-from-claude-md.py CLAUDE.md .autocontext/lessons.json
```

This parses the CLAUDE.md file and extracts structured lessons. If you chose "extract and review," each lesson will be presented for approval before being added.

## Playbook generation

After all setup is complete, the script generates an initial playbook:
```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/generate-playbook.py .autocontext/lessons.json .autocontext/playbook.md
```

The playbook is a curated, readable summary of your project's lessons. It's automatically regenerated after each `/autocontext:review` session.

## Completion summary

Once initialization is complete, you'll see a summary of what was created:
- Number of lessons (if seeded from CLAUDE.md)
- Configuration files created
- Merge driver status (if applicable)
- Path to playbook.md for reading
- Next steps: run `/autocontext:review` to curate lessons, or just start coding

You can now use the autocontext plugin in this project. Lessons will automatically accumulate during sessions.
