---
name: pre-commit-review
event: PreToolUse
tools:
  - Bash
description: Surface the staged diff for line-by-line review before a commit, and flag deletions of safety-critical guardrails
---

# Pre-commit review

When a `git commit` is about to run, surface the diff it will capture and a short review checklist, so the change gets read instead of scrolling past unseen. Committing without reading the diff is how an accidental deletion, a leftover debug line, or a removed guardrail slips into history, and history is the one place a mistake is expensive to walk back. Reading the diff is the cheapest place to catch that, so this hook puts it in front of you at commit time.

It is advisory: by default it does not block the commit. It surfaces the diff and the checklist as context, then the commit proceeds. The value is that the change and any risky removals get seen before they land; the commit itself is not stopped. See "blocking vs advisory" below for turning it into a hard stop.

## When it runs

On a `Bash` tool call whose command is a `git commit` (including `git commit -m`, `git commit -am`, and a `git commit` chained after `&&`). Anything that is not a commit passes straight through.

The diff it reviews is whatever the commit will actually capture. For a normal commit that is the staged set (`git diff --cached`). For a commit that stages tracked files itself (`-a`, `-am`, `--all`), `git commit -a` lands the staged set as well as the unstaged changes to tracked files, so it reviews both together. A flow like `git add -p` followed by `git commit -am` does not hide the already-staged hunks. If nothing would be committed, it does nothing.

## What it surfaces

- **The diff that will be committed**, so the actual change is in front of you before it lands. Long diffs are truncated to a readable window with the total line count noted, so a large commit still announces its size rather than scrolling past.
- **A safety-removal flag.** If the diff *removes* lines carrying safety-critical language (merge restrictions, "no exceptions", "mandatory", "must not", "do not push", or anything about bypassing review), it calls that out specifically. Deleting a guardrail is occasionally correct and often a mistake, so it should be a conscious choice rather than a line that scrolled by.

## How to respond

Read the diff the hook surfaced, then confirm before the commit lands:

1. **Every removed line was removed on purpose.** Nothing deleted by accident or left over from debugging.
2. **No safety guardrail was dropped** without intent. If the safety-removal flag fired, double-check that line.
3. **The commit message explains why, not just what.** The diff already shows what changed; the message is where the reason lives.

If any of those is unsettled, fix it (amend or follow up) rather than leaving it in history.

## Blocking vs advisory

By default this is a non-blocking hook: it surfaces the diff and checklist, and the commit proceeds. That keeps the diff visible on every commit without standing between a careful author and a clean commit, and without training people to reflexively click past a gate. The trade-off is that it surfaces the change rather than enforcing a stop.

If you want a hard gate, where the commit is refused until the diff is acknowledged, wire it as a blocking hook: exit non-zero, or return an `ask` or `deny` permission decision, the way `one-way-door-check` and `enforce-test-first` block in this collection. Blocking guarantees the pause; advisory keeps the friction low. Pick by how much you trust the committing author to read what they are shown.
