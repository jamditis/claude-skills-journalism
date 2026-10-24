# Cross-provider code review

When to read this: Use this reference when an independent review must check a completed change before publication or merge.

## Select from author provenance

Identify the provider that authored the change.
Choose a reviewer from a different provider.
As a review heuristic, do not use a same-provider model as the only independent review.
Keep the primary agent responsible for scope, evidence, and final judgment.

Use low reasoning effort for a trivial change.
Use high reasoning effort for behavior, security, data, migration, concurrency, or broad changes.
Client settings: Claude Code uses `--effort`; Codex uses `model_reasoning_effort` in configuration or through `-c`.
Do not pin a model name or identifier in shared workflow guidance.

## Define the exact snapshot

Record the review base, head, changed paths, and a digest of the reviewed diff.
Use committed snapshots when practical. Start a committed-snapshot review from a
clean index and worktree: a branch review can diff the working tree against the
merge base, so uncommitted edits would enter the review but not the digest.

Example:

```bash
test -z "$(git status --porcelain)" || { echo "Commit or set aside changes first" >&2; exit 1; }
base="$(git merge-base <base-branch> HEAD)"
head="$(git rev-parse HEAD)"
git diff --name-only "$base" "$head"
git diff --no-ext-diff --no-color --binary "$base" "$head" | sha256sum
```

Give the reviewer the requirements, base, head, changed paths, and digest.
Ask the reviewer to repeat the base, head, paths, and digest in the result.
Discard output that covers a different snapshot.
Do not repair mismatched evidence by relabeling it.

## Review in either direction

Use the client whose provider differs from the author.
Check the current help before relying on an option.

Codex client examples for committed work:

```bash
codex exec review --base <base-branch>
codex exec review --commit <sha>
```

Use `--base` for a committed branch diff or `--commit` for one committed change.
Use `--uncommitted` only for staged, unstaged, and untracked work that is not committed.

Claude Code client example with the exact diff on standard input and file-reading tools only:

```bash
base="$(git merge-base <base-branch> HEAD)"
head="$(git rev-parse HEAD)"
git diff --no-ext-diff --no-color --binary "$base" "$head" | \
  claude -p --permission-mode plan --strict-mcp-config --tools "Read,Grep,Glob" \
  "Review this diff (base $base, head $head). Report actionable defects with file and line evidence. Repeat the base and head in your answer."
```

Plan mode can run shell commands for exploration, so do not describe it as read-only.
The restricted tool list prevents shell execution in this example.
`--tools` limits only built-in tools. MCP servers from user or project settings still load,
so `--strict-mcp-config` without `--mcp-config` keeps every MCP server out of the review.
`claude -p` skips the workspace trust dialog.
Do not run it inside a checkout of an untrusted pull request.
See the security-toolkit `security-checklist/references/agent-pr-review.md` reference.

These are examples, not required wrappers.
Run `codex exec review --help` or `claude -p --help` for the installed version.
Use the repository's approved authentication and sandbox policy.

## Reviewer fallback

Do not switch reviewers because the reviewer found defects.
Do not switch because the output was malformed.
Do not switch because the evidence covers the wrong snapshot.
Those results require correction or a rerun with the same reviewer path.

Use a different reviewer only after you classify the current provider as unavailable.
Record the availability failure.
Keep the replacement reviewer outside the author's provider.

## Evaluate findings

The primary agent verifies each finding against the code and behavior.
Fix supported findings.
Reject unsupported findings with concrete evidence.
Do not accept a finding because it sounds confident.
Do not dismiss a finding because it came from an automated reviewer.

For each finding, record:

- Stable finding ID.
- Severity and affected path.
- Evidence.
- Disposition: fixed, rejected, or deferred.
- Verification result.

## Continue until stable

There is no fixed round cap.
Continue until a review round produces no new actionable findings.
A later round can be narrower than the first.
If new substantive defects continue to appear, stop and reconsider the design.
Repeated broad defects indicate a design or scope problem, not a need for endless patching.

## Verify fixes narrowly

After fixes, run a focused verify-fixes pass.
Give it the prior finding IDs, dispositions, fix paths, and verification evidence.
Ask whether each supported finding is fixed and whether the fix caused a local regression.
Do not restart a broad review when the behavior outside the fix did not change.
Run a new broad review only when the fix materially changes the reviewed design or behavior.

## Push and resolve in order

Verify the fix locally.
Commit and push the exact head.
Confirm the remote pull request head matches it.
Resolve only the threads whose fixes exist at that exact head.
Leave disputed, deferred, unverified, or unpushed findings open.

## Final check

- Is the reviewer from a different provider than the author?
- Does effort match the risk?
- Did the review cover the recorded base, head, paths, and digest?
- Did the primary agent verify each finding?
- Did fallback occur only for classified unavailability?
- Did the final round produce no new actionable findings?
- Did fix verification stay focused?
- Are resolved threads fixed on the exact remote head?

## Sources

- OpenAI Developers, ["Custom Code Review rules for Codex"](https://developers.openai.com/blog/custom-code-review-rules-for-codex), on scoped review rules, actionability, and review as an additional safeguard.
- [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference), for current non-interactive and permission-mode options.
- Git, ["git-diff"](https://git-scm.com/docs/git-diff), for exact diff ranges and path lists.
- Panickssery et al., ["LLM Evaluators Recognize and Favor Their Own Generations"](https://arxiv.org/abs/2404.13076), on self-preference in model evaluation.
