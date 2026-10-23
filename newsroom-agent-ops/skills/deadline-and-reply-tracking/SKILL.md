---
name: deadline-and-reply-tracking
description: Use to track deadlines, acknowledgments, reply windows, and the next owner action across calendars, messages, and task records.
---

# Deadline and reply tracking

Reconcile the latest evidence for work that is due, blocked, or waiting.

## When to use

- A calendar deadline is near or has passed.
- A sent request is waiting for acknowledgment or a substantive reply.
- Several systems show different dates or statuses.
- A public-records request has a statutory clock or appeal window.

## When not to use

- The user needs legal advice about a deadline.
- No source establishes the date or reply obligation.
- The item is already complete and readback confirms the result.

## What you need

- Calendar and message search.
- The current task or request record.
- The source that establishes each due date.
- A jurisdiction-specific, current legal source for statutory deadlines.
- A written authorization policy for external actions.

Before any external action, read the project instruction file (AGENTS.md for
Codex, CLAUDE.md for Claude Code). The written policy must state who may send
or change what, to whom, and when. If a follow-up is not authorized, prepare it
as a draft.

## Workflow

1. Identify the item, owner, timezone, and controlling source.
2. Resolve duplicate calendar entries before calculating status.
3. Read the latest message or record that sets the due date or reply direction.
4. Compare the tracker status with completion evidence.
5. Calculate the due date using the governing calendar and current rule.
6. Record acknowledgments, extensions, partial replies, and appeals separately.
7. Classify the item as due, blocked, waiting, complete, or disputed.
8. Name the next owner action and the evidence needed to close it.
9. Verify authorized tracker changes by readback.
10. State legal uncertainty and link the current authoritative source.

## Rules

- Do not mark an item complete from silence.
- Do not use an old snapshot when a newer source exists.
- Keep acknowledgment and completion separate.
- Keep statutory, negotiated, and internal deadlines separate.
- Record the timezone and business-day rule.
- Do not guess an extension or appeal window.
- A sent follow-up is not a received reply.

## Public-records example

    Request: City purchasing records
    Submitted: April 2
    Statutory clock: [current jurisdiction rule and source]
    Acknowledgment: April 4, tracking ID [id]
    Agency direction: Estimated response May 1
    Current state: Waiting
    Next owner action: Review the estimate on May 1
    Appeal window: [date or unresolved, with source]
    Completion evidence: None

Check the controlling law and current agency guidance before calculating dates.
Use **foia-requests** for U.S. request drafting and appeals. Use
**brazil-records-requests** for Brazil's access-to-information process.

## Output template

    Item | Controlling source | Due or reply date | State | Next owner action
    [item] | [source] | [date and timezone] | [state] | [action]

    Conflicts:
    - [source A says X; source B says Y]

    Unverified:
    - [claim or missing evidence]

## Failure modes

- Counting from the wrong start event.
- Treating calendar days as business days.
- Losing an appeal window after a partial denial.
- Treating an acknowledgment as completion.
- Following up after an authorized extension without checking the latest thread.
- Marking complete because no reply arrived.

## Related skills

- foia-requests
- brazil-records-requests
- scheduled-briefing
- email-request-intake
- record-reconciliation
