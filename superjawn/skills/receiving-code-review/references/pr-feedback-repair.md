# Pull request feedback repair

When to read this: Use this reference when a pull request has review feedback that may require code changes or thread resolution.

## Start from the exact head

Record the pull request number and current remote head.
Confirm that your checkout matches the head you intend to repair.
Stop if the remote head moves unexpectedly.
Do not resolve threads against a different commit than the one you verified.

Example inspection:

```bash
gh pr view <number> --json headRefName,headRefOid,baseRefName,state,reviewDecision,statusCheckRollup,mergeStateStatus,reviews,comments
git fetch origin "pull/<number>/head"
git rev-parse HEAD
git rev-parse FETCH_HEAD
```

Here `origin` is the base repository. GitHub publishes every pull request head
there as `pull/<number>/head`, including heads from forks, where `headRefName`
names a branch in the contributor's repository instead.
Compare both local identifiers with `headRefOid` before editing.

## Read every feedback surface

Inspect:

1. Top-level review decisions and summaries.
2. General pull request comments.
3. Inline review comments.
4. Review-thread resolution state.
5. Required checks and merge state.

Do not assume a top-level summary contains every inline finding.
Do not treat a reaction or approval as proof that all threads are resolved.

Use the repository's approved interface to query review threads.
For GitHub, this read-only query includes inline comments and thread state:

```bash
gh api graphql \
  -F o=OWNER -F r=REPO -F n=NUMBER \
  -f query='
query($o: String!, $r: String!, $n: Int!, $after: String) {
  repository(owner: $o, name: $r) {
    pullRequest(number: $n) {
      headRefOid
      reviewThreads(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          comments(first: 50) {
            nodes { databaseId author { login } body }
          }
        }
      }
    }
  }
}'
```

If `hasNextPage` is true, rerun the query with `-F after=<endCursor>`.
Keep the query read-only until you know which threads are complete.
Use the `resolveReviewThread` mutation only for step 7, after steps 1 through 6 are complete.

## Classify each finding

For every item, record:

- Comment or thread ID.
- File and line.
- Reviewer's claim.
- Current head.
- Evidence checked.
- Disposition: supported, unsupported, unclear, or already fixed.

Ask for clarification before changing code for an unclear finding.
Do not implement the clear items if unresolved ambiguity can change their design.

## Reproduce when practical

Try to reproduce behavior findings with the smallest faithful evidence.
Use an existing test, focused command, log, or direct behavior check.
Security, data-loss, concurrency, and public-contract findings need stronger evidence than a style comment.

If reproduction is not practical, inspect the exact execution path and state the limit.
Do not claim that a finding is fixed when the affected behavior was not checked.

## Fix only supported findings

Verify the claim against the codebase and requirements.
Fix it when the evidence supports it.
Reject it when concrete code, tests, or requirements disprove it.
Do not add speculative features or abstractions to satisfy vague ideas of completeness.

For a confirmed bug class, inspect sibling instances in the changed scope.
Verify each instance before editing it.
Stop at clear scope and ownership boundaries.

## Verify each repair

Apply one coherent repair at a time.
Run the smallest affected check.
Then run the relevant broader check when the risk requires it.
Inspect the final diff for unintended changes.

Keep a simple repair record:

```text
Finding: <thread or comment ID>
Disposition: fixed | rejected | deferred
Evidence: <test, code path, or requirement>
Fix paths: <paths>
Verification: <command and result>
```

## Reply and react by convention

Follow the repository's rule for replies and reactions.
Reply in the inline thread when the feedback is inline.
Use a top-level comment only for a summary or a repository convention that requires it.
Keep the reply factual: state the fix, evidence, or reason for rejection.
Do not use performative agreement.

Do not react during inspect-only work.
Do not send notifications that the repository does not require.

## Push before resolution

Complete these steps in order:

1. Complete all supported repairs.
2. Verify each repair locally.
3. Commit each repair separately if that improves the history.
4. Push the verified set once.
5. Confirm the remote pull request head.
6. Reply with the evidence.
7. Resolve each completed thread.

Leave a thread open when the fix is unpushed, disputed, deferred, or unverified.

## Report state accurately

Use the platform's actual state.
An open pull request is not merged.
A merged pull request is not necessarily deployed.
A deployed change is not verified live until a direct check confirms it.

Report each state separately:

- Pull request state.
- Exact head.
- Check status.
- Open thread count.
- Merge state.
- Deployment state.
- Live verification state.

## Final check

- Did you compare the local and remote heads?
- Did you inspect reviews, comments, inline comments, and thread state?
- Did you reproduce behavioral findings when practical?
- Did you fix only findings supported by evidence?
- Did you follow the repository's reply and reaction convention?
- Are resolved threads fixed and pushed at the exact head?
- Does the handoff separate open, merged, deployed, and live states?

## Sources

- GitHub Docs, ["About pull request reviews"](https://docs.github.com/en/pull-requests/reference/pull-request-reviews).
- GitHub Docs, ["Reviewing proposed changes in a pull request"](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-proposed-changes-in-a-pull-request).
- GitHub GraphQL API, ["Pulls"](https://docs.github.com/en/graphql/reference/pulls).
