---
name: copywriting-preflight
event: UserPromptSubmit
description: Detects writing and revision requests and prompts an intent interview before drafting
match_patterns:
  - "blog post"
  - "substack post"
  - "op-ed"
  - "press release"
  - "newsletter"
  - "talking points"
  - "write a post"
  - "write an article"
  - "write an essay"
  - "write a pitch"
  - "write copy"
  - "write the copy"
  - "draft a post"
  - "draft an article"
  - "draft a pitch"
  - "draft an announcement"
  - "polish the draft"
  - "punch up the copy"
  - "rewrite the post"
  - "rewrite the article"
  - "revise the draft"
  - "tighten the copy"
---

# Copywriting preflight

When the user asks for a new piece of writing or a revision, interview them about intent **before** drafting a single word. Jumping straight to a draft produces generic copy that misses the audience, message, and tone the user actually had in mind — and then both of you spend more time fixing the wrong draft than a 30-second interview would have cost.

This hook does not write anything. It pauses to gather intent, then gets out of the way.

## Detection criteria

Skip very short messages (a one-line aside is rarely a real writing request). Otherwise, treat the message as a writing task when it contains:

- **New writing:** "write/draft/create a [post, article, blog, essay, script, copy, memo, pitch, newsletter, press release, announcement, proposal, one-pager, talking points]", plus named forms like "op-ed", "blog post", "substack post", "press release".
- **Revision:** a revision verb ("revise", "rewrite", "rework", "polish", "tighten", "punch up", "edit", "refine", "strengthen") **next to** a writing-context word ("draft", "post", "article", "piece", "copy", "script", "newsletter", "write-up"). Require both, so "tighten that" about a code hook does not trip it.

Check revision first — it is the more specific case, since it implies a piece already exists.

The `match_patterns` above are deliberately writing-noun-specific (`blog post`, `op-ed`, `write copy`) rather than bare verbs (`write a`, `rewrite`), so code prompts like "write a SQL query" or "rewrite this regex" never trip the interview. If a borderline prompt does match, apply the verb-plus-writing-noun test before interviewing and skip silently when the request turns out to be about code.

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
