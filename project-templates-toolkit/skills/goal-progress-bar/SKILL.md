---
name: goal-progress-bar
description: Use to show weighted progress for a multi-step task and update it from recorded evidence.
---

# Goal progress bar

Use this skill for work with three or more steps that runs long enough for
someone to ask how close it is to done. Skip it for a quick answer or one-step
task.

Each task gets one tracker file. The script renders the current percentage,
bar, and row status at each checkpoint. Never type or adjust those values by
hand.

## Define what done means

Agree the deliverables and acceptance evidence before choosing weights. The
percentage measures completion of that scope. It is not elapsed time, an ETA,
confidence, or permission to release. Include review, deployment, live checks,
or requester decisions only when the task actually requires them.

For a long-running or shared goal, read
[evidence and scope](references/evidence-and-scope.md). Keep evidence and owners
beside the tracker without adding fields to its row format.

## Set up a tracker

1. Write `<goal>-progress.json` in your task folder. The file is a JSON list of
   `[name, weight, fraction]` rows.
2. Use one row for each deliverable or proof that moves the goal. Examples
   include code, review, release, live verification, and requester approval.
   Use names the requester understands.
3. Use weight `1` for a small row and `2` for a large or critical row. Choose
   weights before reporting progress. End with
   the rows that prove the work is complete in real use.
4. Add a fourth field to a row that cannot move:
   `[name, weight, fraction, "blocked"]`. Remove the field when work resumes.

## Render the tracker

Run the script from the task folder. Replace `<skill-root>` with the folder
that contains this `SKILL.md`:

```bash
python3 <skill-root>/scripts/progress.py <goal>-progress.json "<Goal name>"
```

On Windows, use `py -3` or your installed Python 3 command instead of `python3`.
Quote paths containing spaces. The same script accepts UTF-8 trackers with or
without a byte-order mark, including files written by Windows PowerShell.

Add `--chat` for emoji codes suited to chat systems that render common emoji
shortcodes:

```bash
python3 <skill-root>/scripts/progress.py <goal>-progress.json "<Goal name>" --chat
```

The chat bar uses green squares for complete work, one yellow square for
partial work, and white squares for the rest. Each row starts with a green,
yellow, white, or red status circle. Send the rendered text without a code
block if the destination converts emoji codes.

## Update at each checkpoint

A checkpoint is a finished step, such as a reviewed change, release, live
check, or answer from the requester.

- Back up the tracker before each edit, for example:
  `cp <goal>-progress.json <goal>-progress.json.bak-<date>-<time>`.
- Set a code row to `1.0` only when its defined work is complete.
- Set a proof row to `1.0` only with real evidence, such as a receipt, live
  read, or requester answer. Never round up to done before the proof exists.
- Add a row when the goal grows. Never delete a row to raise the percentage.
- A newly discovered requirement can lower the percentage. Explain the scope
  change. If work is explicitly removed from scope, retain the old tracker and
  record the decision before calculating the revised baseline.
- Preserve earned progress while a row is blocked. Record the blocker and next
  owner in the evidence notes. A row at `1.0` cannot also be marked `blocked`.
- Reopen a proof row when its supporting build, artifact, or external state
  changes. Old evidence does not prove the current result.

## Input and completion checks

Names must be nonempty single-line text. Weights must be positive finite
numbers; fractions must be finite numbers from `0` to `1`. A fourth field must
be exactly `"blocked"`, for unfinished work only. An empty tracker renders 0%.
Missing, malformed, or invalid trackers exit `2` without printing progress.

The renderer reserves 100% and a fully complete bar for rows whose fractions
are all `1`. It checks the numbers, not their evidence. Verify every acceptance
condition before setting those fractions. Never invent approval or a live
readback to finish the bar.

## Share the result

- Paste the full script output without changes. Never type a percentage or bar
  by hand.
- Share it when work starts, at meaningful checkpoints, and when work ends. Do
  not post it again when nothing changed.
- When the destination supports message editing, update the first progress
  message in place and post a new message only at large milestones.
- In an issue or ledger, place the current output between these markers:

```html
<!-- progress:start -->
<!-- progress:end -->
```

A finished task can replace the block with one dated 100% completion line. The
next task then owns the live progress block.
