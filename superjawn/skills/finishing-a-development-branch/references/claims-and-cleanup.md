# Claims and cleanup

When to read this: Use this reference when merged work needs claim, branch, worktree, or release cleanup.

Use the repository's claim and release conventions.
If it has none, the rules below are one workable pattern.

## Claim protocol

Add a claim label such as `agent:claimed` only when work starts.
Record the worker and current branch in the repository's coordination record.
Remove the claim when work stops, transfers, or its pull request merges or closes.

A repository can define a stale-claim window that fits its work cycle.
For example, treat a claim as stale when both conditions are true:

1. It has no update for 24 hours.
2. It has no open pull request.

Another worker can release a stale claim after checking for unrecorded work.
Do not take an active claim merely because its worker is offline.

## Link issues to the correct completion state

Keep these states distinct:

| State | Meaning |
| --- | --- |
| Pull request open | A change is proposed and under review |
| Merged | The change entered the base branch |
| Deployed | The release system delivered the change |
| Live | A direct check confirmed the user-facing result |

In a repository with a separate deployment step, use `Refs #n` in the pull request.
Do not use a closing keyword at merge.
Add a status label such as `status:awaiting-deploy` when the pull request merges.
Close the issue only after a live check.
Include a short receipt that states what changed, where it is live, and how it was checked.

When merge makes the change live, a closing keyword can be correct.
Confirm the repository's release model before choosing the keyword.

## Update parent work

When a child issue closes, tick its item in the parent issue.
Close the parent only when every child is live or otherwise resolved.
Do not treat a merged child as complete when deployment remains.

## Milestones

If the repository uses milestones, one workable rule is to give every new issue a milestone.
Choose the closest open milestone that matches the work.
Create a milestone only when none fits and the repository's process permits it.
Move the issue if its release scope changes.
Close a milestone when it has no open items.

## Stacked pull requests

State the parent pull request, base branch, and position in the stack.
Keep each layer coherent and reviewable.
Do not describe a child layer as independently mergeable when it requires its parent.
Update stack metadata when a layer moves or lands.

Example:

```text
Stack position: 2 of 3
Parent PR: #41
Base branch: feature/storage-layer
Depends on: schema introduced by #41
```

## Cleanup after merge

Delete the merged branch and remove its worktree only after you verify the pull request and local state.
Preserve unique work in a commit and an approved remote or handoff location.

Inspect the exact state:

```bash
gh pr view <number> --json state,headRefOid,mergeCommit
git rev-parse <branch>
git -C <worktree> status --porcelain
```

Confirm that `state` is `MERGED` and the branch revision equals `headRefOid`.
Confirm that the worktree status prints nothing.
Never use `git worktree remove --force` to get past a dirty worktree.

Cleanup order:

1. Confirm the pull request is `MERGED` and record `headRefOid` and `mergeCommit`.
2. Confirm the branch revision equals `headRefOid` and the worktree is clean.
3. Remove the clean worktree without `--force`.
4. Only then delete the local branch with `git branch -D <branch>`.
5. Delete the remote branch when the repository process permits it.
6. Remove the claim.
7. Update the ledger or coordination record.

## Session-end inventory

Before ending the session, list:

- Open claims.
- Local branches created or used.
- Remote branches created or used.
- Worktrees created or used.
- Pull requests and their actual state.
- Deployments still waiting.
- Live checks still waiting.

Release, finish, or record each item.
Do not report the session as clean while an unrecorded claim or worktree remains.

## Completion language

Use exact statements:

- `PR #42 is open.`
- `PR #42 merged at commit abc123.`
- `The release completed.`
- `The live page returned the expected version.`

Do not use `done` to combine review, merge, deployment, and live verification.

## Final check

- Is the claim active and current?
- Does each issue follow the repository's milestone convention?
- Does the pull request use the correct issue link?
- Is the repository's awaiting-deploy status present when needed?
- Did a live check happen before issue closure?
- Is the parent issue current?
- Are merged branches and worktrees removed?
- Does the handoff distinguish every state?

## Sources

- GitHub Docs, ["Linking a pull request to an issue"](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).
- GitHub Docs, ["About milestones"](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones).
- GitHub Docs, ["Managing the automatic deletion of branches"](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-the-automatic-deletion-of-branches).
