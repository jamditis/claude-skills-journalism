# Recovery checkpoint schema

Keep one bounded checkpoint for the active run. Write it atomically. Do not put
secrets, full message bodies, or private source material in it.

## Required fields

    schema_version: 1
    run_id: "unique producer-assigned id"
    producer:
      pid: 12345
      process_start: "platform process start marker"
    phase: "started"
    task_source: "inbox or event reference"
    prompt_pages:
      total: 3
      read: [1, 2, 3]
    current_step: "short statement"
    next_step: "short statement"
    assumptions: []
    holds_checked_at: "RFC 3339 timestamp"
    side_effect:
      kind: null
      target: null
      idempotency_key: null
      intended_at: null
      completed_at: null
      external_id: null
      readback: null
    summary_path: null
    updated_at: "RFC 3339 timestamp"

## Phases

| Phase | Meaning | Required next check |
|---|---|---|
| started | The run was accepted and no work is complete | Read all prompt pages |
| working | Read-only or local work is in progress | Follow current_step |
| side-effect-pending | An external action can be in flight | Inspect external state before retry |
| side-effect-complete | The external action has an exact ID and readback | Continue from next_step |
| summary-written | The producer can read the final summary | Run the explicit done step |
| blocked | Safe progress stopped and the reason is recorded | Deliver the blocked summary |

## Update boundary

Write the checkpoint:

1. At run start.
2. After the full-prompt gate.
3. At each task boundary.
4. Immediately before every external action.
5. Immediately after readback of every external action.
6. After the summary file is complete.

Each external action replaces the whole `side_effect` record. The pending write
sets `intended_at` and clears the other result fields. The readback write sets
`external_id`, `readback`, and `completed_at`. A blocked checkpoint changes the
phase but leaves the `side_effect` record as it is, so done can still see an
unresolved action.

Keep exact external IDs, but keep secret values and unnecessary personal data
out of the checkpoint.

## Atomic write

Write a complete temporary file in the same directory, flush it, then rename it
over the active checkpoint. A partial checkpoint must never replace the last
valid one.
