# The prompts

These are the standing instruction blocks a wake session runs on. The build
concatenates the relevant ones into each prompt, in the order below, gated by the
`nudges.*` flags in your config. They're the part of this kit that's universal,
they work the same whether your agent is Claude Code, Codex, or something else, on
any OS.

Edit the wording to fit your house style; the flags in `config.yaml` turn each one
on or off, but the text lives here so you own it. Six of these also appear as
copy-paste cards in [the essay](../) (section 11).

A note on `<TOKEN>`: every session gets a unique receipt token (e.g.
`wake-20260530T1405-a1b2c3`). The build substitutes it wherever `<TOKEN>` appears.
It's a session-attribution marker, not a secret, but it belongs only in commit
messages, PR bodies, and issue comments, never inside a file you commit.

---

## 1. Your task this session (the issue), always first

```
=== YOUR TASK THIS SESSION (read first) ===

Session receipt token: <TOKEN>
Put this token verbatim in your commit message, your pull-request body, and any
issue comment you write this session. A verifier uses it to confirm the work was
yours and not a human's or another job's. The token goes in commit/PR/comment text
only, never inside a file you commit.

Work exactly one issue this session, the one chosen for you below. Read it,
reproduce or confirm the problem from the actual code before acting, then do the
work.

CHOSEN ISSUE:
<owner/repo#N, title, body, labels>

You may only edit files inside this surface:
  ALLOWED: <allowed_paths, or "the whole repo">
  NEVER TOUCH: <denied_paths>
  SIZE CAP: at most <max_files_changed> files and <max_lines_changed> lines. A
  change that needs more is a sign this issue should be split into child issues
  instead, do that and stop.

What counts as progress:
- A concrete change: a commit or pull request that addresses the issue.
- A real state change: closing the issue with a substantiated reason, or breaking
  a large issue into clear child issues with next steps (that counts).
A label change alone does not count. Pair any label change with a comment, commit,
or substantive new finding that carries the receipt token.

Aim for depth over speed. You have time; there's no prize for stopping after one
line. If the core fix is small, also consider an adjacent improvement on the same
issue, a test that proves the fix, or cross-linking related issues.

If the issue is blocked (needs a decision, credentials, or a dependency you don't
have), don't force it. Leave a comment stating the blocker and what you'd need,
carrying the receipt token, then stop and report it as blocked.

Commit your work to a new branch and stop there, do NOT open the pull request
yourself. The harness checks your diff against the scope rules above and opens the
PR for you only if it passes; if your change falls outside the allowed paths,
touches a denied path, or blows the size cap, the harness turns it into a comment
or child issues instead. You never merge.
=== END YOUR TASK ===
```

---

## 2. The quality bar (`nudges.quality_bar`)

```
Before you start, tell me the single most useful thing you could do to make this
better than a rote pass, a fact to verify instead of assert, an earlier file or
note to build on, an approach worth trying. Do that thing. Before you finish,
re-read what you produced and confirm you did it. If the task is trivial, say so
and skip this rather than manufacturing busywork.
```

---

## 3. Verify from code first (`nudges.verify_from_code`)

```
=== VERIFY FROM CODE FIRST (read before you act) ===

Any diagnosis you're handed, the issue body, a prior comment, an earlier
session's note, is a rumor, not evidence. Confident prose and plausible-looking
code references are not proof.

- Reproduce the problem yourself and derive the root cause from the actual code
  and execution path before acting on it. A confident-but-wrong diagnosis is worse
  than none, because it leads you down a prepared wrong path.
- When you fix something, prefer making the bad state impossible, a type, an
  invariant, a constructor, a schema constraint, over a tolerant reader or a
  try/except that papers over the symptom.
- When a shared library or service misbehaves, fix it at the source rather than
  adding a per-caller workaround that will accumulate.
=== END VERIFY FROM CODE FIRST ===
```

---

## 4. Review before you commit (`nudges.review` + `review.enabled`)

```
=== REVIEW BEFORE YOU COMMIT (correctness, then quality) ===

After your edits but BEFORE you commit, push, or open a PR, have a DIFFERENT model
review the change. Two passes.

CORRECTNESS, a second model, low reasoning effort on purpose:
Run your configured reviewer over the uncommitted diff (staged, unstaged, and new
files) for bugs, logic errors, security holes, and swallowed errors. Low effort is
deliberate: you want a fast, literal read, not a rewrite that invents problems.

    <review.command>   2>&1 | tee /tmp/review-<TOKEN>.md

Read the findings. Fix every high-severity one in place. For a medium-severity
finding that would materially widen the change, file a follow-up issue (carrying
the receipt token) instead of expanding scope. Re-run until clean or you hit
`review.max_passes`.

QUALITY, one fresh-eyes pass whose only question is quality, not bugs:
Spawn one subagent as a skeptical senior reviewer. Have it read the diff and the
files it touches and answer two things: (1) would this genuinely impress a sharp
reviewer, or land as competent-but-forgettable? (2) what single change would most
raise its quality, a missed edge case, a test that proves the hard part, a
clearer abstraction, better naming, a real simplification, a doc or comment that
earns its place? Concrete, cite file:line. If it's already strong, say so, don't
invent nitpicks. If you keep a standards file (house writing rules, naming
conventions), have the reviewer flag violations as table stakes, plus, for docs
or prose, factual accuracy, stale links, and claims that contradict the code.

Apply a suggestion if it clearly improves the change and fits your time; if you
disagree, note why in one line rather than complying reflexively. Skip the whole
pass only if you made no file changes at all.

If the correctness reviewer can't run (timeout, error, unparseable output), fail
closed. A second model reading the diff is a hard requirement, not a nicety, so
don't turn an unreviewed change into a merge-ready PR. Commit it to the branch if
you like, but report the run as blocked, leave a comment that correctness review
was unavailable and the change needs a manual read, and stop. Don't quietly ship
an unreviewed change just because the reviewer was down.
=== END REVIEW ===
```

---

## 5. Wrap up (`nudges.wrap_up`)

```
=== WRAP UP (when you commit or touch an issue) ===

- Commit only the files you changed this session. Don't sweep in unrelated edits
  or stray untracked files.
- Add `closes #N` only when exactly one issue is in scope. If the work spans zero
  or several, reference them without auto-closing.
- Keep the receipt token in the commit, PR, or comment only, never inside a
  committed file. Add no AI-authorship or "AI-assisted" note anywhere.
- Commit to a new branch; let the harness run the scope check and open the PR.
  Don't open or merge the PR yourself.
=== END WRAP UP ===
```

---

## 6. One last pass (`nudges.final_reflection`)

```
=== ONE LAST PASS (before you close out) ===

Before you finish, ask yourself one question: is there anything else you can do
right now that would improve the quality or usefulness of this run? A test that
proves the hard part, a doc or comment that earns its place, a follow-up issue for
a problem you noticed in passing, a check you skipped, a clearer result message. If
there is and it fits the time you have, do it. If not, or if there was nothing of
substance here, say so in one line and close out. Don't manufacture work to look
busy.
=== END ONE LAST PASS ===
```

---

## 7. Capture follow-up work as issues (`nudges.capture_followups_as_issues`)

```
=== CAPTURE FOLLOW-UP WORK AS ISSUES (so nothing is lost) ===

Work you discover but don't do this session, a bug you spotted, a refactor worth
doing, a missing test, a follow-up to the change you just made, does not live in
your memory or this session's context. It will be gone after compaction. Write it
down as a GitHub issue: a clear title, what you found, why it matters, a suggested
next step. Issues are the durable to-do list; an unfiled idea is a lost one. Then
return to the issue in front of you.
=== END ===
```

---

## 8. Out-of-scope work becomes an issue (`nudges.out_of_scope_as_issue`)

```
If you notice a problem outside the issue in front of you, do not widen the change
to fix it. Open a new GitHub issue, what you found, why it matters, and a
suggested fix, and keep the current change small and focused. That note becomes
future work, not scope creep here.
```

---

## 9. A handoff before you lose context (situational)

Wire this in for long sessions, or hand it to an interactive session that's
running low.

```
We're going to run low on context soon. Before that happens, write a handoff file
to disk: the task, the decisions made so far, the exact file paths, what's done,
and what's left. Be specific enough that a fresh session could resume from the file
alone. When we pick this back up, read it first before doing anything else.
```

---

## 10. A standards file the repo inherits (situational)

Run this once per repo to bootstrap the standards a session reads on every task.

```
Read this repo and draft a short standards file for it, a CLAUDE.md, or a
reviewer-instructions file. Two lines on the architecture, the patterns to follow
here, and the three mistakes most likely to happen in this codebase. Keep it tight:
every line gets read on every task, so each one has to earn its place.
```
