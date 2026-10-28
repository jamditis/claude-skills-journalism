# Evidence, scope, and completion

Use this reference for shared work, long-running goals, or work with external
release and verification steps. The renderer remains a small numeric tool;
the worker owns whether the recorded fractions are true.

## Keep evidence outside the numeric rows

The tracker accepts only `[name, weight, fraction]` or
`[name, weight, fraction, "blocked"]`. Use a task record or companion
`<goal>-evidence.md` for the information that supports each row:

| Row | Acceptance condition | Current evidence | Owner or next action |
| --- | --- | --- | --- |
| Implement | The requested behavior works | Build/commit and focused check result | Worker |
| Review | Required findings are resolved | Reviewed snapshot and finding dispositions | Reviewer or worker |
| Publish | The approved artifact is released | Deployment/release identifier | Authorized publisher |
| Verify live | The ordinary public route serves that artifact | URL, checked time, result, and artifact identity | Worker |

These are examples, not mandatory rows for every task. A local document edit
does not need a deployment row. Authorization and requester approval are rows
only when they are part of the task's actual completion criteria.

Use useful row names so the evidence record identifies the same deliverable.
Do not add secret values or private content to a public progress message.
Link to evidence that the intended reader can access.

## Fractions describe observable milestones

Use fractions that correspond to defined milestones. For example, a row might
be `0` before work starts, `0.5` when a draft passes its focused check, and `1`
when its acceptance condition is met. Do not estimate fractions from time
spent, number of tool calls, lines written, or a feeling that work is close.

Weights describe the agreed scope. They do not measure confidence or establish
an ETA. Keep them stable unless the scope changes. A small but required live
proof must remain visible even after a large implementation row is complete.

The overall value uses `sum(weight * fraction) / sum(weight)` and floors the
reported percentage. The renderer prevents numeric rounding from displaying
unfinished work as 100%. A plausible number is still not evidence of completion.

## Blocked work and new scope

Keep an unfinished row's earned fraction when it becomes blocked. Add the
`"blocked"` flag, then record the condition, next owner, and next action in the
evidence notes. A blocked row does not advance merely because time passes.
When it resumes, remove the flag and update from actual work.

Add rows for newly required work and explain any drop in the displayed value.
Do not shrink weights or remove difficult rows to make the bar rise. If the
requester explicitly removes a deliverable, preserve the previous tracker and
record the scope decision before reporting a revised baseline.

Revalidate proof when its target changes. A test on an earlier build, a review
of a previous snapshot, or a receipt from an earlier deployment does not prove
the current target. Reduce or reopen the affected proof row until it is checked.

## Report the useful state

Share the renderer's complete output at meaningful checkpoints. Add a short
explanation of what changed, what is blocked, and the next action. Do not post
repeated unchanged bars or use a percentage to hide an unresolved limitation.

If the destination does not render emoji shortcodes reliably, use the default
plain output. Keep text labels visible; color alone must not carry the status.
Rendering output does not authorize sending it to any external destination.

At 100%, reconcile every row with current acceptance evidence. Keep source,
review, merge, release, and live state separate when those steps apply. If work
stops or a budget expires, report the remaining scope instead of setting it done.
