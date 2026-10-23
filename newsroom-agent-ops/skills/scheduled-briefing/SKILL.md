---
name: scheduled-briefing
description: Use to create a concise scheduled newsroom briefing from calendars, assignments, inbox items, and current evidence.
---

# Scheduled briefing

Produce a phone-readable briefing that separates today's work, waiting items,
and decisions.

## When to use

- A morning, midday, afternoon, or evening briefing is scheduled.
- An editor needs a current operational snapshot.
- Several sources contain overlapping schedule and assignment entries.

## When not to use

- The user asks for a full editorial report or analytics review.
- The source systems are unavailable and the missing data would make the brief
  misleading.
- A quiet check-in contains no changed or actionable item.

## What you need

- Read access to the relevant calendar, assignment tracker, and inbox.
- A prior briefing or snapshot when continuity matters.
- A notifier or output file.
- Source timestamps and readback for any record change.
- A written authorization policy for external actions.

Before any external action, read the project instruction file (AGENTS.md for
Codex, CLAUDE.md for Claude Code). The written policy must state who may send
or change what, to whom, and when. Without that authority, return the briefing
as a draft and do not send or update records.

## Workflow

1. Set the briefing window and timezone.
2. List the source systems and their newest available timestamps.
3. Start from the supplied snapshot, but refresh only facts that affect a
   decision or owner action.
4. Collapse duplicate calendar events and already processed notifications.
5. Separate schedule, new work, waiting items, and decisions.
6. Give every action an owner and due date when the sources support them.
7. Label each item with its source.
8. State when a source was unavailable or a completion claim remains
   unverified.
9. Do not create tasks that only restate a quiet check-in.
10. If a record change is authorized, write it once and verify it by readback.

## Rules

- Prefer current source state over an old summary.
- Keep unsupported owner, status, and date fields open.
- Do not treat silence as completion.
- Use short labels and one action per line.
- Put the decisions the editor must make near the top.
- Keep background detail behind a link or source label.
- Do not send the briefing unless the authorization policy permits it.

## Phone-readable template

    [Time] newsroom briefing

    Decisions
    - [Decision needed] | Owner: [name or role] | By: [time]

    Today
    - [Time] [event or deadline] | Source: [calendar or tracker]

    New work
    - [Action] | Owner: [role] | Due: [date] | Source: [inbox or tracker]

    Waiting
    - [Item] | Waiting on: [role] | Since: [date]

    Source limits
    - [Unavailable or stale source, or none]

    Records changed
    - [Record and verified change, or none]

## Public newsroom example

    8:30 a.m. newsroom briefing

    Decisions
    - Choose the lead story for the noon update | Owner: assigning editor | By: 9 a.m.

    Today
    - 10 a.m. city budget hearing | Source: public meeting calendar
    - 2 p.m. transit data draft due | Source: assignment tracker

    New work
    - Confirm a photographer for the hearing | Owner: visuals editor | Due: 9:15 a.m.

    Waiting
    - Records request acknowledgment | Waiting on: city clerk | Since: Tuesday

    Source limits
    - Shared inbox search was unavailable. Reply status is unverified.

## Failure modes

- Copying the prior brief without checking decision-critical state.
- Listing the same event from two calendars as two events.
- Marking a task complete because it disappeared from one view.
- Adding a task for every informational message.
- Hiding an unavailable source.
- Writing a long narrative that cannot be scanned on a phone.

## Related skills

- deadline-and-reply-tracking
- editorial-workflow
- record-reconciliation
- unattended-agent-runs
