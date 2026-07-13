# Newsletter-composer overlap decision (tier B, issue #115)

Resolves the pre-publish gate the tier B checklist puts on `newsletter-composer`:
"check overlap with the already-published `newsletter-publishing` skill
(journalism-core) first; fold or differentiate, do not duplicate."

## What the published skill already owns

`journalism-core/skills/newsletter-publishing` is a channel-lifecycle skill. Its
"when to activate" list is the whole operation around a newsletter, not the
writing of any one issue:

- strategy and positioning (the strategy-document framework),
- subscriber list building and segmentation,
- email template design,
- engagement-metric analysis,
- editorial-calendar planning,
- platform migration,
- deliverability and open-rate work.

It does carry an issue-structure template (opening hook, main story, and so on),
so there is real surface for a second newsletter skill to collide with.

## What `newsletter-composer` is for

The source name and its a4000-sandbox origin point at the other half of the job:
turning source material (reporting notes, links, a transcript, a set of stories)
into the drafted copy of a single issue. That is the compose step, and it sits
downstream of strategy and upstream of send. The published skill plans and
measures the channel; the composer writes the issue that goes through it.

## Decision: differentiate, do not fold

Fold would lose a genuinely separate activation moment. A writer reaching for
"help me draft this week's issue" is not doing strategy, list management, or
metrics, and should not have to load all of that to get drafting help. Keep two
skills, with a hard scope boundary so they compose instead of overlapping:

- `newsletter-composer` activates only at "draft or revise the content of an
  issue." It owns section drafting, subject-line and preview-text options, story
  ordering, and cuts for length.
- It does not re-define strategy, list, deliverability, or metrics guidance. Any
  prompt in that territory hands off to `newsletter-publishing`.
- It reuses the published skill's issue-structure template by reference rather
  than restating it, so the two cannot drift apart.

Each skill's `SKILL.md` should carry a one-line cross-reference to the other so
the handoff is visible at load time.

## Still gating the actual publish (not resolved here)

This decision clears the duplicate-check gate only. Before `newsletter-composer`
ships it still needs:

- de-branding and de-personalization from the a4000 source (strip any
  organization names and machine-specific paths, the same scrub every tier B
  item gets),
- the standard SKILL.md description tuned for trigger accuracy,
- the catalog-manifest updates a new plugin requires (README and docs/index.html
  at minimum).

Recorded from the tier B publishing pass. The video quartet stays blocked on the
legion GPU box and is unaffected by this.
