# Newsroom agent ops

Nine skills for recurring newsroom operations work that an agent performs with
bounded authority, durable state, and verified external actions.

## Skills in this plugin

| Skill | What it covers |
|---|---|
| unattended-agent-runs | Scheduled and persistent unattended runs, leases, checkpoints, recovery, delivery checks, and resource limits |
| scheduled-briefing | Source-backed, phone-readable newsroom briefings |
| deadline-and-reply-tracking | Deadlines, acknowledgments, reply windows, and next-owner actions |
| email-request-intake | Allowlisted email intake with untrusted-content and duplicate-send controls |
| document-delivery | Editable document and PDF inspection, sharing, delivery, and readback |
| chat-mention-triage | Team-chat classification without duplicate replies |
| record-reconciliation | Canonical task, contact, and interaction records with privacy controls |
| multi-agent-coordinator | Durable coordination, watches, review gates, handoffs, and cleanup |
| issue-pool-progression | Safe progression of claimed issues through merge, deployment, and live verification |

## Shared requirements

Each skill defers to the project instruction file and requires a written
authorization policy before any external action. The policy must state who may
send or change what, to whom, and when.

The plugin describes capabilities instead of requiring a specific vendor. A
deployment can supply its own task tracker, calendar, mail reader, authorized
sender, send log, team chat, notifier, peer mailbox, and CI service.

For a simpler process-per-run starter, see the
[public autonomy kit](../docs/autonomy/kit/README.md).

## Installation

    /plugin marketplace add jamditis/claude-skills-journalism
    /plugin install newsroom-agent-ops@claude-skills-journalism

Standards-based clients can install one skill directory at a time.

## License

MIT, under the repository license.
