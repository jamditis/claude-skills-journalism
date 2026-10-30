# Incident updates

Version: 0.2.0 · Community workflow preview · MIT

Tell affected people what is broken, what they can still do, and what happens next. A status indicator is useful only when its wording is supported by evidence.

## Set up once

Record the incident owner, affected service, authoritative evidence sources, approved audience and destination, update cadence, and recovery checks. Read existing communication rules before requesting approval again. Reuse an applicable standing authorization; seek a new decision only for a real scope change or a service-required approval.

Communication authority does not grant permission to deploy, reset accounts, spend money, or change access. A new destination or audience is a scope change. Do not send diagnostic messages to work channels.

## Choose an honest state

- **Investigating:** an observed symptom is being checked; the cause may be unknown.
- **Mitigated:** a workaround reduces the impact; the underlying problem is not confirmed fixed.
- **Monitoring:** the relevant check is passing again, but the agreed observation window is not complete.
- **Resolved:** the stated recovery criteria have passed for the affected scope.
- **Unknown:** current evidence could not be retrieved. Preserve the last confirmed state with its timestamp.

Use words as well as color. Planned maintenance is not automatically an outage. Missing exhaustive tests do not prove a working service is unavailable. Do not use a green indicator to claim immunity from unrelated problems.

## Write the first update

1. Read current primary evidence and the existing incident thread. Separate observation from a proposed cause. Record evidence time, not just the time of writing.
2. Name the affected action in ordinary language: “Publishing is failing” is more useful to staff than an unexplained internal error code.
3. Explain the scope you actually know: service, affected roles, and any untested areas. Avoid publishing private logs, account details, or credentials.
4. State what staff can do now and what they should avoid. Give a next owner and checkpoint. Supply an ETA only when the responsible owner has supported it; otherwise say it is not known.
5. Prepare the complete update, including an accessible text equivalent for any graphic, before sending it to the approved destination.
6. Read it back and record the delivered message identity. If a send is uncertain, inspect before retrying.

## Example update

> Publishing — investigating
> Observed at [time/zone]: the test publish failed on [release/service].
> Scope: editors attempting new publishes. Draft saving passed; scheduled publishing is not yet checked.
> For now: keep saving drafts. Do not repeatedly submit the same publish.
> Cause: not confirmed. [Owner] is checking [evidence source].
> Next update: [authorized checkpoint], or sooner if the impact changes.

This is a fictional template, not a report of a current outage.

## Update without flooding the channel

Keep the current summary in the agreed message or thread. Post a new alert only for a meaningful impact change, an approved checkpoint, or a decision the audience needs to make. Preserve a short dated timeline so an edited message does not erase the incident history. Record unchanged checks privately unless a heartbeat was requested.

When a source or browser becomes unavailable, name that failure. Do not call the underlying service down just because the assistant's computer is unreachable. Do not refresh “last confirmed” after a failed check. If a supported, already-authorized connector can answer the same question, use it; a browser access denial is not permission to bypass that denial elsewhere.

## Close with evidence

Identify what was checked, on which release or environment, using which role, and when. A code merge alone is not recovery. A successful retry is not proof of a permanent fix. State what remains untested. Keep the incident open or explicitly limited when required recovery evidence is missing.

## Acceptance checks

The audience can identify the impact, usable workaround, next owner, next checkpoint, and evidence time without reading an internal thread. “Resolved” is tied to the recovery criteria, not to reassuring wording or a successful tool call.

## Requirements and limits

Requires current incident evidence and authorized communication tools. This document does not schedule monitoring or install an integration. No live host or connector certification is claimed.
