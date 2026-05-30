# Costs

A transparent breakdown of what this can cost, so you can size it before you turn
it on. Two things set the bill: what each run is billed against, and how many runs
you fire. Everything below is one of those two.

Pricing and plan terms move. Treat the specifics here as a prompt to check your
own current plans, not as a quote.

## What each run is billed against

The biggest lever is which credential your CLIs use.

- **A subscription** (Claude Code on a Claude plan; Codex via a ChatGPT login):
  each run draws against a flat monthly plan. One more wake costs nothing extra
  until you reach the plan's limits.
- **A metered API key** (`ANTHROPIC_API_KEY`, an OpenAI API key): every token is
  pay-as-you-go. An unattended loop firing on a schedule bills continuously.

If an API key is set in your environment, confirm which auth mode each CLI is
actually using before you schedule anything — the worker and the reviewer both.
Don't assume the subscription login wins; check, because a metered key billing in
the background is the surprise you're trying to avoid.

## The high end

Maxed out — a metered API key, a wake every 15 minutes around the clock, top
reasoning effort, no hard timeout — this is a loop that can run a meaningful
monthly bill on its own, because it's paying per token for ~100 sessions a day,
each running as long as it likes. That's the ceiling. The rest of this file is how
far below it you choose to sit.

## What I run

For reference, not as a recommendation:

- Both CLIs (worker and reviewer) on subscriptions, so the marginal cost of a wake
  is effectively zero.
- An hourly wake during work hours only — about 13 sessions a day, not 100.
- Work at a real reasoning effort; review at low effort, because a fast literal
  read is what catches bugs.
- One issue per session, with a 90-minute hard timeout, so no single run can spend
  much before a human sees the result.
- Review runs locally in the session rather than as a CI job, which keeps it off
  metered Actions minutes on private repos.

That setup does real work daily and stays inside flat-rate plans.

## Calibrating to your needs

Each of these is a dial in `config.yaml` — turn it toward cheaper or toward more,
to taste:

- **Cadence** (`schedule.wake.cron`) — the largest dial. Hourly during work hours
  is ~13 runs a day; every 15 minutes is ~50.
- **Active hours** — a narrower window is fewer runs.
- **Effort** (`model.work_effort`, `model.review_effort`) — higher tiers cost more
  per run and take longer.
- **One issue per session** (built in) — bounds how much any single wake can do.
- **Hard timeout** (`schedule.timeouts.hard_minutes`) — the backstop on a runaway
  session.

If you're on metered billing and want a firm ceiling, the practical budget is
cadence × effort × timeout: fewer runs, lower effort, and a shorter cap each
multiply down the worst case.

## A change worth watching

Around mid-2026, two billing shifts are relevant to a loop like this. Check the
current terms for your own accounts:

- GitHub's Copilot billing is moving toward a credit model, and Copilot's
  automated PR review can draw on Actions minutes on private repos. Running review
  locally via a CLI keeps it off that meter.
- Anthropic has signaled changes to how non-interactive (`-p`) sessions count
  against a plan — the mode this loop runs in. Worth confirming what your plan
  currently allows for unattended `-p` runs before you raise the cadence.
