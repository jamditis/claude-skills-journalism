---
name: autocontext-setup
description: First-run configuration for the autocontext plugin
---

Run the autocontext first-run setup wizard. Use AskUserQuestion for each step.

## Setup workflow

This skill guides you through initial configuration of the autocontext plugin. Your answers will be saved to `~/.claude/autocontext.json` for use across all projects.

### Step 1: Identity

Identity is required for lesson attribution. No automatic fallback — you must explicitly set it.

**Question:** What should we call you in lesson attribution?

**Options:**
- Your name (text input)
- Username (text input)
- Email address (text input)
- Other (text input)

This value will be stored in your global autocontext config.

### Step 2: Test quality rules

Select which automated test quality checks you want enabled when reviewing test code.

**Question:** Which built-in test quality rules do you want enabled?

**Available rules (multi-select):**
- Tautological test check — flags tests that describe code instead of testing behavior
- No mock everything — warns when mocks are the assertions instead of testing actual behavior
- No happy path only — requires error cases and edge case tests alongside happy path
- No bare assertions — flags `assert True`, `assert is not None`, and similar weak assertions
- Test independence — flags tests that pass without their feature code present

You can enable all, some, or none of these. They can be toggled later.

### Step 3: Lesson loading aggressiveness

Configure how many lessons to load at session start based on relevance confidence.

**Question:** How aggressively should lessons be loaded at session start?

**Options:**
- Conservative — load up to 5 lessons with confidence >= 0.7. Minimal context, high precision.
- Balanced (Recommended) — load up to 15 lessons with confidence >= 0.3. Good mix of depth and specificity.
- Aggressive — load up to 25 lessons with confidence >= 0.1. Maximum context, may include tangential material.

Conservative is safer for focused work. Balanced provides good coverage. Aggressive helps when exploring unfamiliar codebases.

### Step 4: Lesson persistence

Choose how new lessons discovered during sessions should be saved.

**Question:** How should new lessons be persisted at session end?

**Options:**
- Auto-persist with curator validation (Recommended) — new lessons are automatically added, but marked for review. You can curate them later with `/autocontext-review`.
- Always ask before persisting — each new lesson prompts for approval before being added.
- Auto-persist everything — new lessons are immediately added without any review step.

Auto-persist with curator validation balances safety and convenience. Always ask is safest but requires more interaction. Auto-persist everything is fastest but may accumulate noise.

## Configuration output

After answering all four questions, the setup script will:

1. Create `~/.claude/autocontext.json` with your selected values
2. Confirm that setup is complete
3. Inform you that you can now run `/autocontext-init` in any project to start using autocontext

The global config will persist across all projects and can be updated anytime by running `/autocontext-setup` again.
