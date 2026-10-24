# Lease and done lifecycle

The producer owns the lease. The agent's explicit done operation records that
the run and its summary are complete. The producer clears the lease only after
it confirms summary delivery.

## Producer pseudocode

    function acquire(run):
        lease = read_active_lease()
        if lease exists and producer_is_alive(lease.pid, lease.process_start):
            queue(run)
            return BUSY

        if lease exists:
            # The old producer died, but its run may still be working or may
            # need recovery. Adopt that run instead of starting a new one.
            preserve_for_audit(lease)
            if not compare_and_swap_owner(lease, current_pid(), current_process_start()):
                queue(run)
                return BUSY        # another producer adopted it first
            queue(run)
            supervise(lease.run_id)
            return BUSY

        # Create the lease only if no lease exists, in one step: for example,
        # write a temp file, then link() it to the lease path, which fails if
        # the path exists. A plain rename would replace another producer's lease.
        if not create_exclusive({
            run_id: run.id,
            pid: current_pid(),
            process_start: current_process_start(),
            acquired_at: now()
        }):
            queue(run)
            return BUSY            # another producer created a lease first
        inject(run)
        supervise(run.id)
        return ACCEPTED

    function supervise(run_id):
        while active_lease_matches(run_id):
            if explicit_done_exists(run_id):
                if not summary_is_written(run_id):
                    record_blocked(run_id, "done without a readable summary")
                    alert_operator(run_id)
                    return BLOCKED     # keep the lease
                if deliver_summary_once(run_id) != CONFIRMED:
                    wait_for_event_or_probe_interval()
                    continue           # delivery not confirmed; keep the lease
                archive_checkpoint(run_id)
                clear_lease(run_id)
                return COMPLETE

            if session_is_really_lost() and not operator_hold_exists(run_id):
                restart_fresh_session()
                reinject_recovery_notice(run_id)
            elif done_was_refused(run_id) or no_checkpoint_progress_for(run_id, stall_threshold):
                # A refused done step or a hung tool call. Keep the lease:
                # ending a live run can repeat or lose a side effect.
                alert_operator_once(run_id, "run is stalled; lease held")

            wait_for_event_or_probe_interval()

    function deliver_summary_once(run_id):
        if delivery_receipt_exists(run_id):
            return CONFIRMED
        if destination_has_summary(run_id):
            # Covers a send that landed before a crash or is now visible.
            record_delivery_receipt(run_id)
            return CONFIRMED
        if not destination_can_be_checked():
            # Send once, then wait for a person; never retry blind.
            if not delivery_pending(run_id):
                mark_delivery_pending(run_id)
                send_summary(run_id, idempotency_key=run_id)
            alert_operator_once(run_id, "confirm summary delivery by hand")
            if operator_confirmed_delivery(run_id):
                record_delivery_receipt(run_id)
                return CONFIRMED
            return PENDING
        if delivery_pending(run_id) and pending_age(run_id) < confirmation_window:
            return PENDING         # still in flight; do not resend yet
        mark_delivery_pending(run_id)
        send_summary(run_id, idempotency_key=run_id)
        return PENDING             # confirm on a later probe

A producer restart is not session loss. Only the done path clears a lease, so a
restarted producer finds the old run's lease, takes ownership of the same run
ID, and keeps supervising it. `compare_and_swap_owner` replaces the owner only
if the lease still names the dead producer, so two restarted producers cannot
both adopt it.

Set `stall_threshold` above the longest run you expect. A stall alert never
releases the lease. The operator inspects the run and decides. To end it, the
operator first sets an operator hold for the run, so the producer does not start
a replacement session. Then the operator stops the session and confirms that it
exited, reconciles any pending side effect, clears the lease by hand, and
removes the hold. Never clear the lease while any session for the run can still
act: the next run would overlap it.

Deliver the summary before clearing the lease. Record the receipt only after
the destination shows the summary; an accepted or queued send is not proof.
Until then, delivery stays pending and the lease stays in place.

A local receipt alone cannot prevent a duplicate: the producer can stop after
the destination accepts the summary but before anything is saved. So check the
destination before every send, send with the run ID as an idempotency key, and
resend only after the confirmation window passes with no copy at the
destination. If the destination cannot be checked, send once, alert the
operator, and hold the lease until a person confirms delivery. Put the run ID
in the summary so a duplicate is easy to recognize. Prefer a destination you
can read back: with a write-only notifier, every run waits for a person.

Elapsed age alone is not session loss. The producer checks the real session or
process and compares both process ID and process start marker.

## Agent pseudocode

    function run_task(run):
        checkpoint(run.id, "started")
        read_every_prompt_page(run.id)

        for step in plan:
            checkpoint(run.id, "working", next=step)

            if step.has_external_action:
                # Replace the whole side_effect record for each action, so an
                # earlier action's completion cannot carry over.
                checkpoint(
                    run.id,
                    "side-effect-pending",
                    side_effect={kind: step.kind, target: step.target,
                                 idempotency_key: step.key, intended_at: now(),
                                 completed_at: null, external_id: null,
                                 readback: null}
                )
                result = perform_once(step)
                readback = inspect_external_state(result)
                checkpoint(
                    run.id,
                    "side-effect-complete",
                    side_effect.external_id=result.id,
                    side_effect.readback=readback,
                    side_effect.completed_at=now()
                )

        write_summary_file(run.id)
        checkpoint(run.id, "summary-written")
        done(run.id)

## Done checks

The done operation fails closed unless:

- The run ID matches the active lease.
- Every prompt page is recorded as read.
- The checkpoint phase is summary-written or blocked.
- The summary file exists and is readable.
- No side effect is unresolved: if `side_effect.intended_at` is set,
  `completed_at` and `readback` are set too. Check the `side_effect` record,
  not the phase, because a blocked checkpoint replaces the phase. Each action
  writes a fresh record, so an earlier action's completion cannot satisfy this
  check.

When done refuses, it records which check failed in the checkpoint and returns
that reason to the agent. The agent fixes the cause, such as reading the
unrecorded prompt pages, and runs done again. If it cannot, it writes a blocked
checkpoint and summary and runs done. An unresolved side effect still refuses,
even in a blocked checkpoint; the producer's stall alert brings in a person.

Make done idempotent for the same completed run. A second call can report
already complete, but it must not mark another run complete. Done never clears
the lease itself.
