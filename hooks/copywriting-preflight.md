---
name: copywriting-preflight
event: UserPromptSubmit
description: Detects writing and revision requests and prompts an intent interview before drafting
match_patterns:
  # Noun forms that rarely appear in code or admin prompts (safe to match bare)
  - "op-ed"
  - "press release"
  - "substack post"
  - "talking points"
  # Drafting: a verb paired with a writing noun, so code prompts do not match
  - "write a blog post"
  - "draft a blog post"
  - "write a newsletter"
  - "draft a newsletter"
  - "write an article"
  - "draft an article"
  - "write an essay"
  - "draft an essay"
  - "write a memo"
  - "draft a memo"
  - "write a pitch"
  - "draft a pitch"
  - "write a proposal"
  - "draft a proposal"
  - "write a one-pager"
  - "draft a one-pager"
  - "draft an announcement"
  - "write copy"
  - "write the copy"
  - "draft the copy"
  # Revision: a verb paired with a writing noun
  - "rewrite the post"
  - "rewrite the article"
  - "rewrite the draft"
  - "rewrite the copy"
  - "revise the draft"
  - "revise the article"
  - "revise the piece"
  - "polish the draft"
  - "polish the copy"
  - "punch up the copy"
  - "tighten the copy"
  - "tighten the draft"
  - "edit the draft"
  - "refine the draft"
  - "strengthen the piece"
---

# Copywriting preflight

When the user asks for a new piece of writing or a revision, interview them about intent **before** drafting a single word. Jumping straight to a draft produces generic copy that misses the audience, message, and tone the user actually had in mind — and then both of you spend more time fixing the wrong draft than a 30-second interview would have cost.

This hook does not write anything. It pauses to gather intent, then gets out of the way.

## Detection criteria

The signal is the verb-plus-writing-noun pairing, not message length. A terse command that matches a writing pattern — "write copy", "op-ed", "press release" — is still a real request, and terse is often exactly when an intent interview is most useful, so do not skip it for being short. Treat the message as a writing task when it contains:

- **New writing:** a drafting verb ("write", "draft", "create") next to a prose form (post, blog post, article, essay, memo, pitch, newsletter, press release, op-ed, announcement, proposal, one-pager, copy, talking points).
- **Revision:** a revision verb ("revise", "rewrite", "rework", "polish", "tighten", "punch up", "edit", "refine", "strengthen") **next to** a writing-context word ("draft", "post", "article", "piece", "copy", "newsletter", "write-up"). Require both, so "tighten that" about a code hook does not trip it.

Check revision first — it is the more specific case, since it implies a piece already exists.

The `match_patterns` above pair a verb with a writing noun (`write a newsletter`, `rewrite the post`) and keep bare nouns only for forms that rarely show up in code or admin prompts (`op-ed`, `press release`). That is why "write a SQL query", "build a newsletter signup form", and "rewrite this regex" never trip the interview. "Script" is deliberately left out: in a code repo "write a script" almost always means code, not a screenplay. If a borderline prompt still matches, apply the verb-plus-writing-noun test before interviewing and skip silently when the request turns out to be about code.

## Response (new writing)

Before drafting, use `AskUserQuestion` to map out:

1. **Audience** — who is this for?
2. **Key message** — what is the one thing they should take away (the thesis)?
3. **Tone** — formal, conversational, urgent, reflective?
4. **Emphasis** — what should be foregrounded, and what should be played down?
5. **Voice** — first person, organizational voice, journalistic remove?
6. **Boundaries** — specific points to include, and anything to avoid?

Then draft against the answers, not against a guess.

## Response (revision)

Before rewriting, use `AskUserQuestion` to clarify:

1. **What is working and what is not** in the current draft?
2. **Should the framing or angle change**, or only the execution?
3. **Any shifts in emphasis or tone** from the current version?

Then revise to the brief, rather than re-drafting from scratch and discarding what already worked.

## Loading a style guide

If the project defines a writing style guide — a `STYLE_GUIDE.md`, a voice-and-tone doc, or whatever path the project configures — load it into context before drafting so the piece matches the established voice. If none exists, ask the user whether one should be followed.

## Finalizing

Before calling a draft done, read it back against the intent answers and the style guide: does it hit the audience, carry the key message, and stay in the right voice? If the project has an editorial or preflight check, run it on the draft. Fix what drifted before handing the draft over.

## Non-blocking

This hook prompts an interview but does not block any tool. The user can decline the questions and ask you to draft directly; the goal is a deliberate pause, not a gate.
