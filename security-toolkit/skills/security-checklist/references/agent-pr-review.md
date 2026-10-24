# Running an AI agent as a pull request reviewer

When to read this: Use this reference when you build or audit a bot that reviews pull requests with a coding agent.

A PR is untrusted input. Its
author controls every file in it, including files your agent might read as
instructions. Design the reviewer so a hostile PR can waste a review but cannot
change what the reviewer does or what it can write.

## Treat the PR as inert data

- Check out the exact head commit into a clean temporary worktree. Run the agent
  from a neutral working directory that holds a read-only copy or index of that
  tree, not from inside the PR checkout.
- Remove or ignore PR-controlled instruction, hook, and tool-configuration files
  (for example `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.codex/`, editor and MCP
  configuration). The agent must not load them as instructions.
- Take the review rules from the base commit, not the head. A PR must not be able
  to rewrite the rules it is judged by.
- Give the agent a read-only tool set. Disable shell writes, network connectors,
  and package installs. The reviewer does not build, test, or run PR code.
- Strip GitHub tokens and every credential the agent does not need before it starts.
  Leave only the model-provider credential required for the review.

## Pin what was reviewed

- Record the head SHA, base SHA, and merge-base once, before the review starts.
- Compute a digest of the reviewed diff and the list of covered files. If the
  output does not match that evidence, discard it. Do not post it.
- Post the review against the commit you reviewed, even if the PR has moved.
  Say in the review body that newer commits are not covered.
- Do not automatically review each new push. Require an explicit request for a
  later review.

## Scope the credentials

- Prefer a GitHub App over a personal token. Request only the permissions the
  bot needs (for example pull requests: write, contents: read, metadata: read).
  Disable webhooks you do not use.
- Mint a short-lived installation token for one repository just before each
  write. Discard read tokens before the agent starts.
- When git fetches with that token, pass it through `GIT_CONFIG_COUNT`,
  `GIT_CONFIG_KEY_0=http.extraHeader`, and `GIT_CONFIG_VALUE_0`, or use a
  one-shot `GIT_ASKPASS` helper. Never pass the token as a command argument.
  Disable credential helpers and redirects, and bound the network operation.
- Keep the private key in a secret store. Never write it to a file, a command
  argument, a log, or terminal output.

## Limit what the bot can say

- Post `COMMENT` reviews only. Never `APPROVE` or `REQUEST_CHANGES`. A person or a
  separate merge policy decides.
- Neutralize `@` mentions in generated text so the bot cannot notify people.
- Accept commands only from users whose repository permission you confirmed
  through the API. Accept `role_name` values `admin`, `maintain`, or `write`, or
  `permission` values `admin` or `write`. Check again just before you act.
  Ignore comments from bots.

## Make every write idempotent

- Put a hidden marker (job ID and head SHA) in each review and reply. Before
  posting, and again on any retry, search for that marker. If it exists, the
  write already happened.
- Write an "attempted" receipt before the POST. If the response is lost, inspect
  GitHub before you retry. An unconfirmed outcome stays on hold until a person or
  a check confirms it.

## Choose the reviewing model on purpose

- As a review heuristic, use a reviewer from a different model provider than the
  PR author when the author is known to be an agent. Research on model evaluators
  shows self-preference for their own provider's generations.
- Fail over to another engine only on matched availability errors (quota, rate
  limit, sign-in). Never fail over because of the findings, invalid output, or
  mismatched evidence. Those are failures to report.

## Operate it safely

- Run a single reviewer instance behind a process lock, or use a distributed
  lock when several instances can receive work.
- Report a stall after a period with no output instead of killing work in
  progress. To cancel, signal the recorded process group, never a process name.
- Count your API calls per poll and keep them inside the rate limit with room to
  spare.

## Quick audit questions

1. Can a file in the PR change the reviewer's instructions or tools?
2. Can the PR change the review rules it is judged by?
3. Can the bot approve, merge, push, or mention people?
4. Does a lost HTTP response risk a duplicate review?
5. Can a token the bot holds write to a repository other than the one under
   review?
6. Can a reviewer from the author's own provider review the change?

If any answer is yes, fix that before the bot reviews outside contributions.

## Sources

- [Registering a GitHub App from a manifest](https://docs.github.com/en/apps/sharing-github-apps/registering-a-github-app-from-a-manifest)
- [Generating an installation access token](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app)
- [Create a review for a pull request](https://docs.github.com/en/rest/pulls/reviews#create-a-review-for-a-pull-request)
- [Get repository permissions for a user](https://docs.github.com/en/rest/collaborators/collaborators#get-repository-permissions-for-a-user)
- [Rate limits for the REST API](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- Panickssery et al., ["LLM Evaluators Recognize and Favor Their Own Generations"](https://arxiv.org/abs/2404.13076)
