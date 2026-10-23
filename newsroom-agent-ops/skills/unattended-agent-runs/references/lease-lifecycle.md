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
                deliver_summary_once(run_id)   # skips if a delivery receipt exists
                archive_checkpoint(run_id)
                clear_lease(run_id)
                return COMPLETE

            if session_is_really_lost():
                restart_fresh_session()
                reinject_recovery_notice(run_id)

            wait_for_event_or_probe_interval()

A producer restart is not session loss. Only the done path clears a lease, so a
restarted producer finds the old run's lease, takes ownership of the same run
ID, and keeps supervising it. `compare_and_swap_owner` replaces the owner only
if the lease still names the dead producer, so two restarted producers cannot
both adopt it.

Deliver the summary before clearing the lease, and record a delivery receipt
keyed by run ID. If the producer stops between delivery and clearing, the next
producer adopts the lease, sees the receipt, and finishes without sending the
summary twice.

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
