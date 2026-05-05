---
name: executing-plans
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
---

<!--
Adapted from obra/superpowers executing-plans skill (v5.0.7), MIT-licensed,
copyright 2025 Jesse Vincent. Modifications copyright 2026 Joe Amditis.
v0.1.0 added a per-task drift check (default-on research). v0.2.0
replaced that with a one-time freshness check at execution start,
default-skip with explicit triggers (cross-session plan, external API,
main/master branch), fixing the "execution journal undefined" and
"master-branch guardrail not in drift check" bugs surfaced by smoke
testing. See CREDITS.md.
-->

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the superjawn:executing-plans skill to implement this plan."

**Note:** Tell your human partner that superjawn works much better with access to subagents. The quality of its work will be significantly higher if run on a platform with subagent support (such as Claude Code or Codex). If subagents are available, use superpowers:subagent-driven-development instead of this skill.

## Freshness check (when artifact is stale)

The plan was written at a point in time. **Default-skip.** Run only when one of these triggers fires:

- **Cross-session execution.** The plan was drafted in a prior session — different cwd, different transcript, or different day. If you wrote the plan yourself in this session, the freshness check is not needed.
- **External API/service touched.** Any task in the plan calls an external API, service, or file outside the repo (e.g., live HTTP, third-party SDK call, OS-managed config). Internal state can be assumed stable; external contracts cannot.
- **Working on main/master.** Current branch is `main` or `master`. Heightened drift risk because integration work assumes the branch is in sync, and other people landing commits can invalidate the plan's assumptions silently.

If none of the triggers fire, write one line into the execution journal and proceed:

```
[YYYY-MM-DD HH:MM] Freshness check skipped — none of the triggers fired (current session, no external APIs, on feature branch <name>).
```

### When the check fires

Verify, in order, BEFORE running any tasks:

1. **Authoritative state.** For each external API/file the plan references, hit the real source — live curl, file read, version check. Confirm the contract still matches what the plan assumed.
2. **Codebase drift.** Grep that any function/module/path the plan names still exists at the expected location with the expected shape.
3. **Repo state.** `git log <plan-write-sha>..HEAD` if you can identify when the plan was written; otherwise `git log --since='1 week ago' --oneline`. Has anyone landed conflicting work since the plan was drafted?

### Findings location: the execution journal

Findings land in a per-plan execution journal at:

```
.superpowers/exec-journal-<plan-slug>.md
```

Where `<plan-slug>` is the kebab-case basename of the plan file (e.g., `2026-05-05-superjawn-batch-1.md` → `exec-journal-2026-05-05-superjawn-batch-1.md`). The journal is created on first run if it doesn't exist; entries are appended in chronological order. The directory `.superpowers/` is git-ignored by upstream convention.

One line per check:

```
[YYYY-MM-DD HH:MM] Freshness check: <PASS / FAIL> — <one-line summary>
```

If FAIL on any check, **stop and escalate to your human partner before implementing** — the plan may need revision.

### Master-branch guardrail

If the trigger fired because you're on `main` or `master`, the freshness check ALSO requires explicit user consent before any implementation begins. Per the upstream rule "never start implementation on main/master without explicit user consent," ask first, then proceed. Document the consent in the journal as part of the freshness check entry.

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns about the plan
3. Run the freshness check (see "Freshness check (when artifact is stale)" above) — single decision, write the result line to the execution journal
4. If concerns or freshness FAIL: Raise them with your human partner before starting
5. If no concerns and freshness PASS or skipped: Create TodoWrite and proceed

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

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
- Run the freshness check at Step 1 — default-skip, but fires for cross-session plans, external APIs, or main/master branch work
- Don't skip verifications
- Reference skills when plan says to
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent (the freshness check enforces this when triggered)

## Integration

**Required workflow skills:**
- **superpowers:using-git-worktrees** - REQUIRED: Set up isolated workspace before starting
- **superjawn:writing-plans** - Creates the plan this skill executes
- **superpowers:finishing-a-development-branch** - Complete development after all tasks
