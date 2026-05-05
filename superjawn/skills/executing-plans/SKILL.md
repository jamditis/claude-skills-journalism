---
name: executing-plans
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
---

<!--
Adapted from obra/superpowers executing-plans skill (v5.0.7), MIT-licensed,
copyright 2025 Jesse Vincent. Modifications copyright 2026 Joe Amditis.
Modifications add a per-task research phase (drift check before
implementation), plus updates to cross-references.
See CREDITS.md.
-->

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the superjawn:executing-plans skill to implement this plan."

**Note:** Tell your human partner that superjawn works much better with access to subagents. The quality of its work will be significantly higher if run on a platform with subagent support (such as Claude Code or Codex). If subagents are available, use superpowers:subagent-driven-development instead of this skill.

## Research phase (per task)

Before implementing each task in the plan, run a quick drift check. **Default-on**: skip only with explicit, justified statement per task.

### 1. What to verify

The plan was written at a point in time. Before each task, verify:
- **Authoritative state:** If the task touches an external API or file the plan references, confirm the API contract or file content hasn't changed. Live curl, file read, version check.
- **Codebase drift:** If the task assumes a function/module exists at a specific path, grep to confirm it still does.
- **Repo state:** Has anyone landed conflicting work on the branch since the plan was drafted?

### 2. Dispatch

- Inline for single-file or single-API checks
- `Explore` subagent for codebase-drift questions spanning multiple files
- `general-purpose` subagent for verification that spans external sources

### 3. Record findings

Append a short note to the execution journal (or PR description) for each task:

```
Task N drift check: <PASS / FAIL> — <one-line summary>
```

If FAIL, escalate before implementing — the plan may need revision.

### 4. Skip protocol

If skipping the per-task drift check, write one line in the journal: `Task N drift check skipped because <reason>.`

**Valid reasons:**
- Task is purely additive within a file the previous task just created (no external state to verify)
- Plan was drafted within the current session and nothing has changed
- Task is a pure mechanical commit / rebase / push step

**Invalid reasons:** "I think I know", "seems straightforward", "moving fast", "user wants this done quickly", "already familiar with this codebase". If those are tempting, do the check.

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns about the plan
3. If concerns: Raise them with your human partner before starting
4. If no concerns: Create TodoWrite and proceed

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Run the drift check (see "Research phase (per task)" above)
3. Follow each step exactly (plan has bite-sized steps)
4. Run verifications as specified
5. Mark as completed

### Step 3: Complete Development

After all tasks complete and verified:
- Announce: "I'm using the superpowers:finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Drift-check each task against current codebase reality before implementing (see Research phase)
- Don't skip verifications
- Reference skills when plan says to
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent

## Integration

**Required workflow skills:**
- **superpowers:using-git-worktrees** - REQUIRED: Set up isolated workspace before starting
- **superjawn:writing-plans** - Creates the plan this skill executes
- **superpowers:finishing-a-development-branch** - Complete development after all tasks
