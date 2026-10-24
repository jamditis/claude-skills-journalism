---
name: unattended-agent-runs
description: Use to design or operate recurring newsroom agent work without a person watching each run. Covers a simple process-per-run starter and a persistent supervised session.
---

# Unattended agent runs

Run recurring work with explicit authority, durable state, bounded resources,
and recovery that does not repeat external actions.

## When to use

- A scheduled process checks an inbox, calendar, task queue, or issue pool.
- A long-running agent receives recurring work from a local producer.
- A run must recover safely after a restart or context loss.
- The operator needs proof that messages, files, or other external actions landed.

## When not to use

- A person is actively supervising one short task.
- The work has no stable authorization or escalation policy.
- The requested action needs a person at the moment it occurs.
- A one-off batch can use a normal interactive session.

## What you need

- A scheduler or event producer.
- A supervisor that can restart the agent process or session.
- A pinned working directory and state directory.
- A notifier and a summary file that the producer can deliver.
- A send log or other readback path for external actions.
- Resource controls for memory, swap, CPU, and worker fan-out.
- A written authorization policy for external actions.

Before any external action, read the project instruction file (AGENTS.md for
Codex, CLAUDE.md for Claude Code). The written policy must state who may send
or change what, to whom, and when. If the policy does not authorize an action,
prepare a draft or record a blocker instead of acting.

## Choose the run tier

### Tier 1: Fresh process for each run

Use one new process for each scheduled event. Give it one bounded task, a
timeout that allows output to flush, a summary destination, and a narrow scope.
This is the easiest design to inspect and replace.

Start with the repository's
[autonomy kit](https://github.com/jamditis/claude-skills-journalism/tree/master/docs/autonomy/kit). Its process-per-run loop
is a suitable starter for scheduled issue work. Treat a timeout as a cost or
stall backstop, not proof that the task failed safely.

### Tier 2: Persistent supervised session

Use one supervised session when startup cost, recurring context, or long work
makes a fresh process impractical. The producer must hold a single-flight lease
until the session performs an explicit done step and the producer confirms
summary delivery. Do not release the lease because time elapsed. If done is
refused, or the run makes no checkpoint progress past a stall threshold, the
producer alerts the operator once and keeps the lease.

The producer identity must include the process ID and process start time. Probe
the real session for loss. A reused process ID must not inherit an old lease.
A producer restart does not end the run: the new producer adopts the existing
lease and keeps supervising that run until its done step.

## Workflow

1. Receive one self-contained task with a unique run ID.
2. Create a recovery checkpoint with phase started, so a session lost during
   the prompt read still leaves a run to recover.
3. Read the full prompt page by page. Record each page read. Do not substitute
   a checksum, search result, parser, or prior template for this gate.
4. Re-read the standing holds list for this run.
5. Record the next step and move the phase to working.
6. Before an external action, write side-effect-pending with a fresh
   side-effect record: the intended target, idempotency key, intended time, and
   evidence to inspect.
7. Perform the authorized action once.
8. Read back the external state. Record its exact ID, the readback, and the
   completion time, and move the checkpoint to side-effect-complete.
9. Continue from the checkpoint. Keep assumptions, open questions, and source
   limits explicit.
10. Write the final summary to the configured summary file.
11. Record summary-written.
12. Run the explicit done step once. It records completion; the producer
    clears the lease only after it confirms summary delivery.

Use [references/checkpoint-schema.md](references/checkpoint-schema.md) for the
checkpoint fields and phases. Use
[references/lease-lifecycle.md](references/lease-lifecycle.md) for lease and
done pseudocode.

## Rules

### Recovery

- After a restart, start a fresh agent session.
- Read only the active checkpoint and the task sections needed to continue.
- Do not replay the prior terminal transcript.
- Do not repeat an action recorded as complete.
- If the phase is side-effect-pending, inspect the external system before any
  retry. The action may have completed before the session stopped.
- If no checkpoint is active, do not carry the last run's project, assumptions,
  or unfinished work into the next run.
- Never block on input. Notify the requester, continue on a stated safe
  assumption when possible, and record that assumption.
- If safe progress is impossible, write a blocked checkpoint and summary, then
  complete the run without the external action.
- If done refuses, read the reason, fix it, and run done again. If you cannot
  fix it, write a blocked summary that names the reason.

### Messaging and delivery

- Contact a requester only when input is required or the finished result is
  ready.
- Do not send progress or acknowledgment messages unless the policy requires
  them.
- During configured quiet hours, put authorized messages in a held queue.
- Before releasing a held message, check the send log and destination for a
  duplicate.
- An accepted or queued send is not delivery proof.
- Verify a received copy or destination record. Inspect an ambiguous send
  before any retry.
- Delivering the requested result completes the request. Do not wait for an
  acknowledgment unless the workflow requires one.
- The producer delivers the run summary. The agent writes the file and does
  not send its own status.

### Resource and persistence

- Apply memory high, memory maximum, swap maximum, and CPU controls to the
  session scope, not only the supervisor.
- Keep parallel worker fan-out small, usually two or three.
- Offload large renders, media processing, or broad data jobs to suitable
  compute.
- Do not run expressions shaped like .{0,N}(a|b).{0,N} over minified one-line
  files. Use fixed-string searches or a bounded index-and-slice tool.
- An incident showed why this matters: a run pinned every core and a hardware
  watchdog reset the board.
- Use supervised user services with persistence enabled where the platform
  supports them.
- Prove restart behavior with a real reboot.
- Pin both the working directory and state directory. Do not rely on a hidden
  default or symlink.

Platform examples are in
[references/service-examples.md](references/service-examples.md). They cover
Linux systemd user units, macOS launchd, and Windows Task Scheduler.

## Short completion record

    Run: [id]
    Result: [finished | blocked]
    Sources checked: [list]
    External actions: [action, exact ID, readback]
    Assumptions: [list or none]
    Held messages: [list or none]
    Recovery phase: summary-written
    Summary path: [path]

## Failure modes

- Lease released on a timer: A long valid run overlaps the next run.
- Process ID without start time: A recycled ID appears to own the lease.
- Partial prompt read: A late hold or delivery rule is missed.
- Retry after an unknown send: The recipient receives a duplicate.
- State in the terminal log only: Recovery repeats work or loses scope.
- Unpinned state path: The producer writes to an inbox the session does not read.
- Unlimited fan-out: Workers compete for memory and make recovery less reliable.

## Related skills

- scheduled-briefing
- email-request-intake
- multi-agent-coordinator
- issue-pool-progression
