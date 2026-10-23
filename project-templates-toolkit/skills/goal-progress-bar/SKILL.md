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

## Set up a tracker

1. Write `<goal>-progress.json` in your task folder. The file is a JSON list of
   `[name, weight, fraction]` rows.
2. Use one row for each deliverable or proof that moves the goal. Examples
   include code, review, release, live verification, and requester approval.
   Use names the requester understands.
3. Use weight `1` for a small row and `2` for a large or critical row. End with
   the rows that prove the work is complete in real use.
4. Add a fourth field to a row that cannot move:
   `[name, weight, fraction, "blocked"]`. Remove the field when work resumes.

## Render the tracker

Run the script from the task folder. Replace `<skill-root>` with the folder
that contains this `SKILL.md`:

```bash
python3 <skill-root>/scripts/progress.py <goal>-progress.json "<Goal name>"
```

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
