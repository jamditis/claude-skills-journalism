# autocontext

A Claude Code plugin that gives your AI assistant a memory for each project.

## The problem

Every time you start a new Claude Code session, Claude starts from scratch. It doesn't remember that the database migration broke last time you used mocks, that the deploy script needs a cache clear first, or that the API returns dates in a weird format. You end up correcting the same mistakes across sessions, and those corrections vanish when the conversation ends.

## What autocontext does

Autocontext listens to your conversations and captures the moments where you correct Claude — "no, use the other API", "you forgot to clear the cache", "that's the wrong import path." It saves those corrections as structured lessons in a JSON file inside your project.

The next time you open a session in that project, autocontext loads the relevant lessons and uses them to avoid repeating the same mistakes. Lessons that keep proving useful gain confidence over time. Lessons that go stale lose confidence and eventually fade out.

It's like giving Claude a notebook that it reviews before starting work each day.

## What it looks like in practice

- You tell Claude "no, always use `pytest -x` here, not `pytest`" → autocontext captures that as a lesson candidate
- Next session, when Claude is about to run `pytest`, autocontext injects a warning: "lesson: always use `pytest -x` in this project"
- If Claude follows the lesson without you correcting it again, the lesson's confidence goes up
- If you correct it differently, the old lesson decays

Over weeks of use, your project builds up a curated knowledge base of project-specific patterns, gotchas, and preferences that Claude loads automatically.

## Install

```bash
# Clone claude-skills-journalism anywhere, then install the autocontext
# skill into ~/.claude/skills/ (Claude Code discovers skills one level deep):
git clone https://github.com/jamditis/claude-skills-journalism ~/projects/claude-skills-journalism
mkdir -p ~/.claude/skills
cp -r ~/projects/claude-skills-journalism/autocontext ~/.claude/skills/
# or: ln -sfn ~/projects/claude-skills-journalism/autocontext ~/.claude/skills/autocontext
```

Claude Code loads the skill automatically on next launch.

## Quick start

1. Run `/autocontext:setup` to configure your preferences (identity, sensitivity, loading behavior — 10 steps total).
2. In any project, run `/autocontext:init` to create the `.autocontext/` directory and start accumulating lessons.
3. Just use Claude Code normally. Autocontext runs in the background.

## Commands

| Command | What it does |
|---------|-------------|
| `/autocontext:setup` | One-time setup wizard for global preferences (10 steps covering identity, test rules, loading, persistence, staleness, injection mode, correction sensitivity, baselines, playbook, and multi-machine support) |
| `/autocontext:init` | Set up autocontext in the current project |
| `/autocontext:review` | Review accumulated lessons — approve, edit, delete, or mark as superseded |
| `/autocontext:status` | See how many lessons you have, their confidence levels, and any pending items |

## How it works under the hood

Autocontext uses Claude Code's hook system to run at five points in every session:

1. **When a session starts** — loads lessons from `.autocontext/lessons.json`, ranked by relevance to the files you've been working on. If there are lesson candidates from your last session, a curator pass decides which ones are worth keeping.
2. **Before each edit or command** — checks if any loaded lessons are relevant to the file being edited or the command being run. If so, it injects a short warning so Claude doesn't repeat a known mistake.
3. **When you type a message** — pattern-matches for correction phrases like "no, use X instead" or "you forgot to..." and queues them as lesson candidates.
4. **After test file edits** — runs quality checks on test code (catches tautological assertions, happy-path-only test suites, and other common test smells). Also tracks build/test times against baselines to flag performance regressions.
5. **When a session ends** — lessons that were loaded and not contradicted get a confidence boost. The playbook summary file is regenerated.

## Cross-developer sharing

Lessons are stored in `.autocontext/lessons.json` (git-tracked). When multiple developers use Claude Code on the same repo, their lessons accumulate independently and merge on `git pull`.

The union merge driver (`scripts/merge-driver.py`) handles conflicts by merging lessons from both sides, deduplicating by text, and preserving tombstoned deletions. To set it up, run `/autocontext:init` and select "Yes, set up cross-developer sharing."

Deleted lessons use a tombstone pattern (`"deleted": true`) rather than hard deletion. This prevents a lesson deleted on one machine from being resurrected by a merge from another.

## Built-in test quality rules

These run automatically on PostToolUse when a test file is edited:

| Rule | What it catches |
|------|----------------|
| `tautological_test_check` | Tests that assert current output rather than desired behavior |
| `no_mock_everything` | Mocked return values used as the expected assertions |
| `no_happy_path_only` | Test suites with no error, edge case, or failure tests |
| `no_assert_true` | Weak assertions: `assert True`, `assert is not None`, `self.assertTrue(True)` |
| `test_independence` | Tests that would pass even if the feature code were absent |

Rules are configurable per-project in `.autocontext/config.json` under `builtin_rules`.

## Configuration

Two config files live in `.autocontext/`:

**`config.json`** (git-tracked, shared across developers):

| Key | Default | Description |
|-----|---------|-------------|
| `max_session_lessons` | 15 | Max lessons to load at session start |
| `confidence_threshold` | 0.3 | Minimum confidence to load a lesson |
| `staleness_days` | 60 | Days before confidence starts decaying |
| `performance_baselines` | true | Track test/build time regressions |
| `pretooluse_hook` | `enabled` | Pre-tool injection mode: `enabled`, `errors_only`, or `disabled` |
| `persistence_mode` | `auto_curated` | How new lessons are saved: `auto_curated`, `ask_before_persist`, or `auto_all` |
| `correction_sensitivity` | `medium` | Correction detection tier: `high`, `medium`, or `low` |
| `playbook_generation` | `auto` | Playbook regeneration: `auto`, `manual`, or `disabled` |
| `multi_machine` | `{"enabled": false}` | Machine-scoped lessons with hostname list |
| `builtin_rules` | all true | Toggle individual test quality rules |
| `activity_signals` | (see below) | Override which tools/patterns count as meaningful activity (see Transcript scanner section) |

**`config.local.json`** (gitignored, per-developer):

| Key | Description |
|-----|-------------|
| `identity` | Your name or username for lesson attribution |

Machine-specific lessons can be tagged with `machine:<hostname>` to prevent them loading on other machines.

## Transcript scanner

The plugin includes a transcript scanner utility that detects meaningful activity in Claude Code session transcripts. It powers the activity gate in `session-end.sh` (skipping lesson validation when only research happened) and can be used by custom hooks.

**Usage from a hook script:**

```bash
RESULT=$(python3 "$PLUGIN_ROOT/scripts/transcript-scanner.py" \
    --transcript "$TRANSCRIPT_PATH" \
    --since "$LAST_HANDOFF_MTIME" \
    --config ".autocontext/config.json")

# Returns JSON:
# {"meaningful": true, "level": "high", "signals": [...], "tool_counts": {...}}
```

**Arguments:**
- `--transcript` — path to the session JSONL file
- `--since` — Unix timestamp (seconds). Only scan entries after this time. Default: scan all.
- `--config` — path to config file. Reads `activity_signals` key if present.

**Signal levels:**

| Level | Triggers |
|-------|----------|
| High | Write, Edit, Bash with `git commit` / `gh pr create` / `firebase deploy` / `systemctl restart` |
| Medium | Agent, Bash with `git push` / `npm run build` / `cargo build` |
| Low | Read, Grep, Glob, unmatched Bash (does not trigger `meaningful: true`) |

**Custom signal config** (optional key in `.autocontext/config.json`):

```json
{
  "activity_signals": {
    "high_tool_names": ["Write", "Edit"],
    "medium_tool_names": ["Agent"],
    "high_bash_patterns": ["git commit", "gh pr create", "deploy"],
    "medium_bash_patterns": ["git push", "npm run build"]
  }
}
```

Each sub-key fully replaces that tier's defaults when present.

## Inspiration and attribution

This plugin was inspired by two projects:

- **[autocontext](https://github.com/greyhaven-ai/autocontext)** by Greyhaven AI — a closed-loop system for improving agent behavior over repeated runs. Its architecture of persistent playbooks, curator agents, and confidence-scored knowledge directly shaped how this plugin handles lesson persistence and validation cycles.

- **[autoresearch](https://github.com/karpathy/autoresearch)** by Andrej Karpathy — AI agents running autonomous research loops. The pattern of accumulating structured knowledge across sessions and using it to inform future runs was a key influence on the session-start/session-end lifecycle design.
