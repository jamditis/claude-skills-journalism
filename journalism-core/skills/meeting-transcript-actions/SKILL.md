---
name: meeting-transcript-actions
description: Use to turn a meeting transcript into verified notes, decisions, commitments, and distinct owner actions.
---

# Meeting transcript actions

Use the transcript as evidence for decisions and commitments. Treat an
automated summary as a lead only.

## When to use

- A new or updated meeting transcript is available.
- Editorial, reporting, board, or source-call notes need owner actions.
- Existing notes must be checked against what speakers said.
- A transcript may duplicate a meeting already processed.

## When not to use

- The source is an automated summary with no transcript or recording.
- The task is verbatim quote extraction or speaker diarization only.
- The meeting has no permitted notes, task, or contact destination.
- Recording or attribution terms prohibit the requested use.

## What you need

- The transcript and source metadata.
- A duplicate key: meeting ID, or date plus title and participants.
- Speaker labels and timestamps.
- Search access to the notes store, task tracker, and contact log.
- Readback for any record changes.
- Recording and attribution terms.
- A written authorization policy for external actions.

Before any external action, read the project instruction file (AGENTS.md for
Codex, CLAUDE.md for Claude Code). The written policy must state who may create,
change, send, or publish what, to whom, and when. Without that authority,
return a proposed recap and action list without changing records.

## Workflow

1. Record the transcript source, meeting ID, date, title, participants, and
   attribution limits.
2. Search existing meeting notes with the duplicate key.
3. Prove whether the transcript is new, updated, or already processed.
4. Read the source notes and enough transcript to verify each decision, owner,
   date, and commitment.
5. Use the automated summary only to locate candidate passages.
6. Separate:
   - decisions,
   - explicit commitments,
   - ideas or proposals,
   - open questions, and
   - claims that appear only in the automated summary.
7. Cite each decision or commitment with speaker and timestamp.
8. Update the existing meeting note when possible.
9. Create only distinct owner actions that are supported by the transcript.
10. Keep the requester separate from the action owner.
11. Verify every record write by readback.
12. Return the recap, owner actions, record links, duplicate result, and
    attribution limits.

## Rules

- An automated summary is not evidence.
- Do not convert an idea, suggestion, or question into a commitment.
- Do not assign an owner from proximity or job title.
- Do not invent a due date.
- Preserve disagreements and unresolved points.
- Use speaker plus timestamp for transcript support.
- Update one canonical meeting note instead of creating duplicates.
- Follow consent, off-record, background, and confidentiality terms.
- Do not copy confidential-source details into a shared tracker.

## Action record template

    Meeting: [ID or date, title, participants]
    Duplicate key: [value]
    Transcript source: [stable link or file]
    Attribution terms: [on record, background, internal, or other]

    Decisions
    - [Decision] | [Speaker, timestamp]

    Commitments
    - [Action] | Owner: [explicit owner] | Due: [date or open]
      Evidence: [Speaker, timestamp]

    Ideas and open questions
    - [Item] | Evidence: [Speaker, timestamp]

    Summary-only claims
    - [Claim not yet supported by transcript, or none]

    Records changed
    - [Verified note or task link, or none]

## Public newsroom example

In an editorial budget meeting, the assigning editor says at 00:18:42 that the
data reporter will check the city contract totals by Friday. Record that as an
owned action with the timestamp.

At 00:23:10, a reporter says that a source may provide invoices next week.
Record it as a source commitment only if the source made that promise in an
on-the-record call or message. The reporter's forecast is not the source's
commitment.

If the automated summary says the team chose a publication date, but the
transcript shows only a proposed date, keep it under ideas and open questions.

## Failure modes

- Treating the meeting summary as the source of truth.
- Creating a second note before searching the duplicate key.
- Assigning every mentioned task to the nearest named person.
- Converting "could" or "should" into "will."
- Omitting timestamps for decisions and commitments.
- Copying restricted source information into a shared note.
- Writing tasks without reading them back.

## Related skills

- interview-transcription
- editorial-workflow
- record-reconciliation
- source-verification
- fact-check-workflow
