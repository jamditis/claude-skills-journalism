# Slop-era principles

When to read this: Use these principles when polished output may hide weak intent, weak evidence, or incomplete review.

## The common problem

Generative systems can produce clean form before they establish meaning or correctness.
Grammar, formatting, and confidence no longer prove that a person applied judgment.
Judge the artifact by its intent, evidence, constraints, and review history.

## Recover the intent

A reader must be able to tell what the writer means and why the artifact exists.
If the intent is not recoverable, polished wording makes the problem harder to see.
For a low-stakes internal note, direct bullets can be better than expanded prose.
Do not add a wind-up, a hedge, or a false personal reaction to make a point sound human.

Ask:

- What decision or action should this text support?
- Which claim matters most?
- What evidence supports that claim?
- Which uncertainty must remain visible?
- Can the reader reconstruct the original intent?

## Treat form as untrusted

Clean syntax is not evidence of a sound process.
A fluent bug diagnosis is still a hypothesis.
A polished issue report can still contain invented causes.
A complete-looking draft can still stop before the difficult verification work.

Read important output line by line.
Check claims against source material.
Name the unverified part instead of presenting partial work as complete.

## Report editorial observations before interpretations

An error report or correction should lead with what the audience received.
Identify the published wording, data, image, or action that is wrong.
Link it to the source record and state the correction before you discuss why the error happened.
Keep automated or speculative analysis separate from the correction.

For example:

> The chart labels 2024 revenue as $4.2 million. The audited statement reports $2.4 million. Correct the chart and every dependent sentence. Review the spreadsheet formula separately before assigning a cause.

This order gives the audience a verified correction without turning an unverified cause into part of the record.

## Prevent recurring editorial errors

Fix the template, style guide, checklist, or CMS field that allowed the error.
Require essential metadata before publication when the publishing system supports that rule.
Use a manual check when judgment is necessary, and name its owner.

Example:

> Published photos repeatedly lack credits.

Weak response:

> Patch the credit into each story after publication.

Better response:

> Make the credit field required in the photo workflow. Repair the existing stories and record any source that has no known credit.

## Fix the source of repeated defects

When the same edit recurs, inspect the shared template, source data, style guidance, or publishing workflow.
A correction at that source protects later stories and every downstream format.
Do not silently copy the same exception into each story.
Escalate a source-data correction when another team owns the record.
Label a local workaround and its removal condition when no safe source fix is available.

## Limit output to review capacity

High output volume can exceed the review process that makes it trustworthy.
Produce work in units that a responsible reviewer can inspect.
Do not open many speculative reports or patches merely because generation is cheap.
Finish verification and cleanup before starting more parallel work.

## Use agents where they help

Agents are useful for search, comparison, prototypes, and repeatable checks.
They do not remove the need for ownership.
The operator remains responsible for what is filed, published, merged, or sent.

Use automation to amplify a disciplined process:

- Start from observed facts.
- Keep the scope small.
- Verify source claims.
- Preserve invariants.
- Review the final artifact.
- State what remains uncertain.

## Review questions

- Is the purpose clear without the decorative prose?
- Does every conclusion trace to evidence?
- Does a correction distinguish the verified error from its possible cause?
- Did a repeated defect lead to a template, source-data, or workflow fix?
- Is the output small enough for real review?
- Does a named person own the final judgment?

## Sources

- George Hotz, ["The Eternal Sloptember"](https://geohot.github.io/blog/jekyll/update/2026/05/24/the-eternal-sloptember.html), on capability, review asymmetry, and the gap between clean form and sound process.
- Caleb Gross, ["You can just say it"](https://noperator.dev/posts/you-can-just-say-it/), on recoverable intent and direct expression.
- Armin Ronacher, ["Building Pi With Pi"](https://lucumr.pocoo.org/2026/5/24/pi-oss/), on issue quality, invariants, maintainer load, and ownership.
