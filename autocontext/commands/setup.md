---
description: First-run configuration for the autocontext plugin
---

Run the autocontext first-run setup wizard. Use AskUserQuestion for each step. Group questions into batches of 2 (up to 4 per AskUserQuestion call) to keep the flow efficient.

## Setup workflow

This skill guides you through initial configuration of the autocontext plugin. Your answers will be saved to `~/.claude/autocontext.json` for use across all projects.

If `~/.claude/autocontext.json` already exists, read it first and present current values as defaults. The user is re-running setup to change settings.

### Batch 1 (steps 1-2)

#### Step 1: Identity

Identity is required for lesson attribution. No automatic fallback — you must explicitly set it.

**Question:** What should we call you in lesson attribution?

**Options:**
- Your name (text input)
- Username (text input)
- Email address (text input)
- Other (text input)

#### Step 2: Test quality rules

Select which automated test quality checks you want enabled when reviewing test code.

**Question:** Which built-in test quality rules do you want enabled?

**Available rules (multi-select):**
- Tautological test check — flags tests that describe code instead of testing behavior
- No mock everything — warns when mocks are the assertions instead of testing actual behavior
- No happy path only — requires error cases and edge case tests alongside happy path
- No bare assertions — flags `assert True`, `assert is not None`, and similar weak assertions
- Test independence — flags tests that pass without their feature code present

You can enable all, some, or none of these. They can be toggled later.

### Batch 2 (steps 3-4)

#### Step 3: Lesson loading aggressiveness

Configure how many lessons to load at session start based on relevance confidence.

**Question:** How aggressively should lessons be loaded at session start?

**Options:**
- Conservative — load up to 5 lessons with confidence >= 0.7. Minimal context, high precision.
- Balanced (Recommended) — load up to 15 lessons with confidence >= 0.3. Good mix of depth and specificity.
- Aggressive — load up to 25 lessons with confidence >= 0.1. Maximum context, may include tangential material.

Conservative is safer for focused work. Balanced provides good coverage. Aggressive helps when exploring unfamiliar codebases.

#### Step 4: Lesson persistence

Choose how new lessons discovered during sessions should be saved.

**Question:** How should new lessons be persisted at session end?

**Options:**
- Auto-persist with curator validation (Recommended) — new lessons are automatically added, but marked for review. You can curate them later with `/autocontext-review`.
- Always ask before persisting — each new lesson prompts for approval before being added.
- Auto-persist everything — new lessons are immediately added without any review step.

### Batch 3 (steps 5-6)

#### Step 5: Staleness and decay

Controls when unused lessons start losing confidence. After the staleness window, confidence drops by 0.1 every 30 days until the lesson is effectively forgotten.

**Question:** How long before unused lessons start losing confidence?

**Options:**
- 30 days (rapid turnover) — best for fast-moving prototypes where context changes quickly.
- 60 days (Recommended) — balanced for most projects with regular development cadence.
- 120 days (long-running) — for stable projects where lessons stay relevant longer.
- 180 days (archival) — minimal decay, good for slow-moving or reference-heavy codebases.

**Config mapping:**
- 30 days → `staleness_days: 30`
- 60 days → `staleness_days: 60`
- 120 days → `staleness_days: 120`
- 180 days → `staleness_days: 180`

#### Step 6: Pre-tool-use injection

The pre-tool-use hook checks loaded lessons before every Edit, Write, and Bash call. If a lesson's tags match the file being edited or command being run, it injects a brief warning. Some users find this helpful as a guardrail; others find mid-flow interruptions disruptive.

**Question:** Should autocontext inject lesson-based warnings before edits?

**Options:**
- Enabled (Recommended) — inject relevant warnings before Edit/Write/Bash. Catches known gotchas before you hit them.
- Errors only — only inject warnings for lessons tagged as bugs, errors, or breaking changes. Quieter.
- Disabled — no pre-tool warnings. Lessons are still loaded at session start but don't interrupt workflow.

**Config mapping:**
- Enabled → `pretooluse_hook: "enabled"`
- Errors only → `pretooluse_hook: "errors_only"`
- Disabled → `pretooluse_hook: "disabled"`

Note: for backwards compatibility, `true` is treated as `"enabled"` and `false` as `"disabled"`.

### Batch 4 (steps 7-8)

#### Step 7: Correction sensitivity

Controls how aggressively the system captures user corrections as lesson candidates. The user-prompt-submit hook pattern-matches messages for correction phrases and queues them for curation.

**Question:** How sensitive should correction detection be?

**Options:**
- High — capture any redirect, including soft phrases like "actually", "remember that", "keep in mind". Catches more but may pick up non-corrections.
- Medium (Recommended) — capture explicit corrections like "no, use X instead", "that's wrong", "don't do that", "you forgot". Good signal-to-noise ratio.
- Low — only capture strong rejections like "that's wrong", "stop doing", "don't do that". Fewest false positives.

**Config mapping:**
- High → `correction_sensitivity: "high"` — all patterns active
- Medium → `correction_sensitivity: "medium"` — exclude soft patterns ("actually", "remember that/this", "keep in mind")
- Low → `correction_sensitivity: "low"` — only: "that's wrong", "don't do that", "stop doing", "no, use X instead"

#### Step 8: Performance baselines

Tracks test and build command execution times. When a command takes more than 10% longer than its baseline, a warning is injected. Useful for catching performance regressions early.

**Question:** Should autocontext track test/build performance baselines?

**Options:**
- Enabled with auto-detect (Recommended) — track common test/build commands (pytest, npm test, cargo test, etc.) automatically.
- Enabled with custom commands — you'll specify which commands to track after setup.
- Disabled — no performance tracking.

If "Enabled with custom commands" is selected, follow up with an open-ended question asking for the commands as a comma-separated list. Store them in `baseline_commands`.

**Config mapping:**
- Enabled with auto-detect → `performance_baselines: true`, default `baseline_commands`
- Enabled with custom → `performance_baselines: true`, user-supplied `baseline_commands`
- Disabled → `performance_baselines: false`, empty `baseline_commands`

### Batch 5 (steps 9-10)

#### Step 9: Playbook auto-generation

The playbook (`playbook.md`) is a human-readable summary of all active lessons, regenerated from `lessons.json` on every session start and end. Useful for onboarding or documentation but adds processing time.

**Question:** Should autocontext auto-generate the playbook file?

**Options:**
- Auto-generate (Recommended) — regenerate `playbook.md` on every session start/end. Always up to date.
- Manual only — only regenerate when you run `/autocontext-review`. Less overhead.
- Disabled — no playbook file generated. Lessons are still loaded but not rendered to markdown.

**Config mapping:**
- Auto-generate → `playbook_generation: "auto"`
- Manual only → `playbook_generation: "manual"`
- Disabled → `playbook_generation: "disabled"`

#### Step 10: Multi-machine awareness

Lessons can be tagged with `machine:hostname` to limit them to specific machines. This is useful when the same project is worked on across multiple nodes with different environments (e.g., a Pi with ARM64 vs. a Windows GPU workstation).

**Question:** Do you work on projects across multiple machines?

**Options:**
- Single machine — no machine tagging needed. All lessons apply everywhere.
- Multiple machines — lessons can be machine-scoped. Enter machine hostnames after setup.
- Auto-detect — use the current hostname automatically. Lessons without machine tags apply everywhere.

If "Multiple machines" is selected, follow up with an open-ended question asking for hostnames as a comma-separated list.

**Config mapping:**
- Single machine → `multi_machine: {"enabled": false}`
- Multiple machines → `multi_machine: {"enabled": true, "machines": [...]}`
- Auto-detect → `multi_machine: {"enabled": true, "machines": ["auto"]}`

When `machines` contains `"auto"`, the session-start hook resolves it to `socket.gethostname()` at runtime.

### Batch 6 (steps 11-12)

#### Step 11: Skill learning

Track which skills are active when corrections happen. This enables lessons to accumulate per-skill and eventually improve the skill files via `/autocontext-evolve`.

**Question:** Do you want autocontext to track corrections per-skill?

**Options:**
- Yes, track all skills (recommended)
- Only specific skills (will ask which ones)
- No, skip skill tracking

If "Yes": set `skill_learning.enabled = true`, `skill_learning.scope = "all"`
If "Only specific skills": ask a follow-up text input for comma-separated skill names, set `skill_learning.scope = ["name1", "name2"]`
If "No": set `skill_learning.enabled = false`

#### Step 12: Evolution aggressiveness

Controls the minimum evidence threshold for `/autocontext-evolve` to consider a lesson ready.

**Question:** How aggressive should skill evolution be?

**Options:**
- Conservative (confidence >= 0.9, 5+ validations) — only well-proven lessons
- Moderate (confidence >= 0.85, 3+ validations) (recommended)
- Aggressive (confidence >= 0.7, 2+ validations) — faster evolution, more risk

Set `skill_learning.evolution_confidence` and `skill_learning.evolution_min_validations` based on selection.

## Configuration output

After answering all questions, write `~/.claude/autocontext.json` with the collected values. Structure:

```json
{
  "identity": "<name>",
  "test_quality_rules": {
    "tautological_test_check": true/false,
    "no_mock_everything": true/false,
    "no_happy_path_only": true/false,
    "no_bare_assertions": true/false,
    "test_independence": true/false
  },
  "lesson_loading": {
    "strategy": "conservative|balanced|aggressive",
    "max_lessons": 5|15|25,
    "min_confidence": 0.7|0.3|0.1
  },
  "lesson_persistence": {
    "strategy": "auto_persist_with_review|ask_before_persist|auto_persist_all",
    "require_approval": false|true|false,
    "mark_for_review": true|false|false
  },
  "staleness": {
    "days": 30|60|120|180
  },
  "pretooluse_injection": {
    "mode": "enabled|errors_only|disabled"
  },
  "correction_sensitivity": "high|medium|low",
  "performance_baselines": {
    "enabled": true|false,
    "baseline_commands": [...]
  },
  "playbook": {
    "generation": "auto|manual|disabled"
  },
  "multi_machine": {
    "enabled": true|false,
    "machines": []
  },
  "skill_learning": {
    "enabled": true|false,
    "scope": "all"|["name1", "name2"],
    "evolution_confidence": 0.9|0.85|0.7,
    "evolution_min_validations": 5|3|2
  }
}
```

After writing the config:
1. Confirm setup is complete with a summary table of all settings
2. Inform the user they can now run `/autocontext-init` in any project to start using autocontext
3. Note they can re-run `/autocontext-setup` anytime to change settings

The global config persists across all projects. Per-project `config.json` (created by `/autocontext-init`) inherits from global but can override any value.
