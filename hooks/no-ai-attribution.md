---
name: no-ai-attribution
event: PreToolUse
tools:
  - Bash
description: Block AI attribution in git and gh commands (commit, PR create, comment, review) before they land, so authorship in the record stays human
---

# No AI attribution

When a `git commit`, a `gh pr create`, or a `gh pr comment` is about to run, check the message it carries for AI authorship credit and stop the action if it finds any. The published record of who wrote what should name people, not tools. A "generated with" line in a commit, a `Co-Authored-By` trailer naming a model, or a tool credit in a PR body all put a machine's name where a contributor's belongs, and once it is in git history or on a merged PR it is part of the project's provenance for good.

For a newsroom the stakes are higher than tidiness. Bylines and authorship are an editorial commitment: a reader, an editor, or a source who follows the trail should find the person accountable for the work, not a model version. This hook keeps that line clean at the moment the credit would otherwise enter the record.

## When it runs

On a `Bash` tool call whose command writes a message into the project record:

- `git commit` (including `git commit -m`, `git commit -am`, and a `git commit` chained after `&&`), checked against the commit message.
- `gh pr create`, checked against the title and body.
- `gh pr comment`, `gh issue comment`, and `gh pr review`, checked against the comment or review body.

Anything else passes straight through. The check reads the message text the command is about to submit, not the diff.

Because the hook binds to the `Bash` tool, it only sees these commands when they run as shell calls. A commit, PR, or comment made through a non-Bash path (an IDE's git integration, the GitHub web UI, or an MCP GitHub connector) does not pass through it, so it guards the command-line workflow rather than every write to the record. The same holds for a message posted through a raw `gh api` call (for example a review-thread reply to `repos/{owner}/{repo}/pulls/{n}/comments/{id}/replies`): the match keys on the `git` and `gh` subcommands listed above, not on arbitrary API URLs.

## What it flags

The message is refused when it carries author credit to an AI tool, model, or vendor. The patterns it looks for:

- "Generated with", "Created by", "Written by", or "Co-authored with" followed by an assistant, model, or company name.
- A `Co-Authored-By:` trailer whose name or email points at a model or tool rather than a person.
- A standalone model, assistant, or vendor name presented as the author or contributor (for example a "Claude", "GPT", "Copilot", or company-name credit line).
- "AI-assisted", "AI-generated", or an emoji-and-tool sign-off used as a byline.

Naming a tool as the *subject* of the work is fine: "switch the parser to the new tokenizer" or "document the Claude API client" describes the change and is not a byline. The hook targets credit lines, not every mention of a tool.

## How to respond

When the hook stops the action, edit the message to remove the attribution, then run the command again:

1. **Delete the credit line or trailer.** No "generated with", no `Co-Authored-By` naming a model, no "AI-assisted" sign-off.
2. **Keep the message about the work.** A commit message explains why the change was made; a PR body explains what it does and how to verify it. Neither needs to say what wrote it.
3. **If a real person co-authored, name the person.** A `Co-Authored-By:` trailer for a human collaborator is correct and stays; only tool and model credits are removed.

The standard is zero AI attribution anywhere in the record: commits, PR titles and bodies, issue and review comments, docs, and code comments.

## Blocking vs advisory

This ships as a blocking hook: it returns a `deny` decision so the commit or PR command does not run until the attribution is gone. Authorship in history is expensive to rewrite after the fact (a force-push to amend a pushed commit, an edit to a merged PR body), so this is one of the cases where stopping the action beats surfacing a warning that can be scrolled past.

If you would rather be reminded than gated, wire it as advisory the way `archive-reminder` and `verification-reminder` run in this collection: surface the matched line as context and let the command proceed. Advisory keeps the friction low; blocking guarantees nothing slips into the record. Pick by how reversible the surface is. For pushed commits and merged PRs, blocking is the safer default.
