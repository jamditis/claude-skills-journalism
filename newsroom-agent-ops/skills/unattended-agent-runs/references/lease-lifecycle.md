# Lease and done lifecycle

The producer owns the lease. The agent can release it only through an explicit
done operation after the summary is complete.

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

        write_atomic({
            run_id: run.id,
            pid: current_pid(),
            process_start: current_process_start(),
            acquired_at: now()
        })
        inject(run)
        return ACCEPTED

    function supervise(run_id):
        while active_lease_matches(run_id):
            if explicit_done_exists(run_id):
                if not summary_is_written(run_id):
                    record_blocked(run_id, "done without a readable summary")
                    alert_operator(run_id)
                    return BLOCKED     # keep the lease
                deliver_summary_once(run_id)
                archive_checkpoint(run_id)
                clear_lease(run_id)
                return COMPLETE

            if session_is_really_lost():
                restart_fresh_session()
                reinject_recovery_notice(run_id)

            wait_for_event_or_probe_interval()

    function deliver_summary_once(run_id):
        if delivery_receipt_exists(run_id):
            return
        if delivery_pending(run_id):
            # A send may have reached the destination before the crash.
            if destination_has_summary(run_id):
                record_delivery_receipt(run_id)
                return
        mark_delivery_pending(run_id)
        send_summary(run_id, idempotency_key=run_id)
        record_delivery_receipt(run_id)

A producer restart is not session loss. Only the done path clears a lease, so a
restarted producer finds the old run's lease, takes ownership of the same run
ID, and keeps supervising it. `compare_and_swap_owner` replaces the owner only
if the lease still names the dead producer, so two restarted producers cannot
both adopt it.

Deliver the summary before clearing the lease. A local receipt alone cannot
prevent a duplicate: the producer can stop after the destination accepts the
summary but before the receipt is saved. Record a pending marker before the
send, and send with the run ID as an idempotency key. After a restart, a
pending marker with no receipt means the send is ambiguous. Check the
destination for that run ID before sending again. If the destination supports
neither an idempotency key nor a lookup, delivery is at least once: put the run
ID in the summary so a duplicate is easy to recognize.

Elapsed age alone is not session loss. The producer checks the real session or
process and compares both process ID and process start marker.

## Agent pseudocode

    function run_task(run):
        read_every_prompt_page(run.id)
        checkpoint(run.id, "started")

        for step in plan:
            checkpoint(run.id, "working", next=step)

            if step.has_external_action:
                checkpoint(
                    run.id,
                    "side-effect-pending",
                    target=step.target,
                    idempotency_key=step.key
                )
                result = perform_once(step)
                readback = inspect_external_state(result)
                checkpoint(
                    run.id,
                    "side-effect-complete",
                    external_id=result.id,
                    readback=readback
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
- No side-effect-pending phase remains unresolved.

Make done idempotent for the same completed run. A second call can report
already complete, but it must not release another run's lease.
