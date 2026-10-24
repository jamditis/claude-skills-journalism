---
name: document-delivery
description: Use to prepare, inspect, share, and deliver an editable document or PDF from verified source material.
---

# Document delivery

Keep content creation, sharing, sending, and publication as separate states.

## When to use

- A requester needs a memo, letter, packet, report, or editable document.
- A finished document must be shared or sent to an authorized recipient.
- The workflow needs proof of recipient access or delivery.

## When not to use

- The request is only for content research or a draft outline.
- Publication or external delivery has no explicit authority.
- The source material or brand assets are unavailable or unverified.

## What you need

- Verified source files and current brand assets.
- A document tool that preserves native structure.
- An export or render path for visual inspection.
- A sharing or sending capability with access readback.
- A tracking record for delivery status.
- A written authorization policy for external actions.

Before any external action, read the project instruction file (AGENTS.md for
Codex, CLAUDE.md for Claude Code). The written policy must state who may send,
share, publish, or change what, to whom, and when. Draft authority does not
grant delivery or publication authority.

## Workflow

1. Confirm the requested format, audience, source set, and delivery state.
2. Ground factual text in the supplied sources.
3. Confirm that brand assets and document templates are current.
4. Build the editable document with native headings, lists, tables, links, alt
   text, and page structure.
5. Export the requested final format.
6. Inspect every page for clipping, missing fonts, broken links, blank pages,
   unreadable contrast, and incorrect pagination.
7. Compare the export with the editable source.
8. Before an authorized share, inspect link settings and recipient access.
9. Before an authorized send, confirm the recipient, subject, attachments, and
   final version.
10. Send once, then verify the send record and recipient-visible copy.
11. Update the tracking record from readback.
12. Return editable and exported locations, inspection result, sharing state,
   and delivery receipt.

## Rules

- Preserve source meaning and the requested format.
- Use a copy for destructive conversion when the original must remain editable.
- Do not use a draft label as permission to publish.
- Do not replace recipient-specific access with a public link.
- Do not claim delivery from a queued or accepted send.
- Inspect an ambiguous send before retrying.
- Keep sensitive attachments out of public or broadly shared storage.
- Record the exact delivered version.

## Delivery checklist

    Content
    - [ ] Facts match supplied sources
    - [ ] Names, dates, and links are verified
    - [ ] Requested edits are present

    Document
    - [ ] Native headings and reading order work
    - [ ] Images have alt text when required
    - [ ] Export has no clipping or blank pages

    Access
    - [ ] Sharing scope matches the request
    - [ ] Recipient access was tested or read back
    - [ ] Attachment is the inspected final version

    Delivery
    - [ ] Send is authorized
    - [ ] Exact recipient and subject are confirmed
    - [ ] Send log has one receipt
    - [ ] Received copy or destination record is verified

## Failure modes

- Building from an outdated template or brand asset.
- Flattening an editable document into an image-only file.
- Inspecting only the source and not the export.
- Sharing a public link when named access was requested.
- Attaching an earlier file with the same name.
- Treating send acceptance as recipient delivery.

## Related skills

- pdf-design
- document-design
- email-request-intake
- unattended-agent-runs
