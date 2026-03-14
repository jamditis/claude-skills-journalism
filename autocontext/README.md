# autocontext

A Claude Code plugin that accumulates project knowledge across sessions and developers. It captures corrections, patterns, and hard-won lessons as structured data, loads the most relevant ones at session start, and improves confidence scores over time as lessons are validated or contradicted.

## Install

Clone this repo and install the plugin by pointing Claude Code at the `autocontext/` directory:

```bash
# If installed as part of claude-skills-journalism:
git clone https://github.com/jamditis/claude-skills-journalism ~/.claude/skills/journalism-skills
```

Claude Code will load skills and hooks from the plugin automatically on next launch.

## Quick start

1. Run `/autocontext-setup` once to configure your identity and preferences globally.
2. In any project, run `/autocontext-init` to create `.autocontext/` and start accumulating lessons.

## Available commands

| Command | Description |
|---------|-------------|
| `/autocontext-setup` | First-run wizard: identity, test rules, loading, persistence, staleness, injection, sensitivity, baselines, playbook, multi-machine |
| `/autocontext-init` | Initialize `.autocontext/` in the current project |
| `/autocontext-review` | Interactively curate accumulated lessons (approve, edit, delete, supersede) |
| `/autocontext-status` | Show lesson counts, confidence metrics, and pending items for the current project |

## How it works

The hook lifecycle runs on every session:

1. **SessionStart** — loads lessons from `.autocontext/lessons.json`, filters by confidence threshold and machine tags, ranks by relevance to recently changed files. If lessons from the previous session were flagged as candidates, a curator LLM call runs first to decide which are worth keeping.
2. **PreToolUse** — before Edit, Write, or Bash calls, checks whether loaded lessons are relevant to the file or command. Injects targeted warnings (up to 3 per call).
3. **UserPromptSubmit** — pattern-matches messages for correction phrases ("no, use X instead", "you forgot", "remember that", etc.) and queues them as lesson candidates in `.autocontext/cache/pending-lessons.json`.
4. **PostToolUse** — after test file edits, runs deterministic quality checks (tautological assertions, happy-path-only tests, etc.) and surfaces warnings. Also tracks performance regressions if baselines are enabled.
5. **SessionEnd** — lessons that were loaded at the start are validated: confidence increases if they weren't contradicted during the session. The playbook is regenerated.
6. **Next SessionStart** — pending candidates from step 3 are passed to the curator, approved lessons are merged into `lessons.json`, and the cycle repeats.

## Cross-developer sharing

Lessons are stored in `.autocontext/lessons.json` (git-tracked). When multiple developers use Claude Code on the same repo, their lessons accumulate independently and merge on `git pull`.

The union merge driver (`scripts/merge-driver.py`) handles conflicts by merging lessons from both sides, deduplicating by text, and preserving tombstoned deletions. To set it up, run `/autocontext-init` and select "Yes, set up cross-developer sharing."

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

**`config.local.json`** (gitignored, per-developer):

| Key | Description |
|-----|-------------|
| `identity` | Your name or username for lesson attribution |

Machine-specific lessons can be tagged with `machine:<hostname>` to prevent them loading on other machines.

## Inspiration and attribution

This plugin was inspired by two projects:

- **[autocontext](https://github.com/greyhaven-ai/autocontext)** by Greyhaven AI — a closed-loop system for improving agent behavior over repeated runs. Its architecture of persistent playbooks, curator agents, and confidence-scored knowledge directly shaped how this plugin handles lesson persistence and validation cycles.

- **[autoresearch](https://github.com/karpathy/autoresearch)** by Andrej Karpathy — AI agents running autonomous research loops. The pattern of accumulating structured knowledge across sessions and using it to inform future runs was a key influence on the session-start/session-end lifecycle design.
