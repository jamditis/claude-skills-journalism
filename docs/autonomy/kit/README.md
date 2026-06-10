# Autonomous GitHub-issue workhorse

Most people who work with a coding agent have never considered this is possible:
you can point an agent at your own GitHub issues and let it work them on a
schedule, unattended, while you do something else. This kit is a careful
way to try that — and "careful" is the whole point.

On a schedule, it picks one open issue from the repos you choose, hands it to your
coding agent, has a *second* model review the change, and opens a pull request for
you to approve and merge. It never merges its own work. It only touches the files
you've told it it can touch. And it files new issues for follow-up work it finds,
so tasks survive forgetting, deletion, and a compacted context.

It's a small software production line with the human review and approval steps
built in — not a button that turns your codebase into unreviewed output that may
or may not work. The difference between those two things is bounded scope, an
independent reviewer, and a person at the merge gate. This kit is built around
those three.

This is the runnable companion to the essay
["How I run dev work with Claude"](../). The essay explains the why; this folder
is how you set up the part most people ask about first.

## Who this is for

You work with a coding agent (Claude Code, Codex, or similar). You don't have to
write the code yourself, or even know Python. Hand your agent two files, answer its
questions, and it builds the loop for your machine.

## How to use it

1. Open a session with your coding agent.
2. Give it `BUILD-WITH-YOUR-AGENT.md` and `config.example.yaml`.
3. Say: "set this up for me — ask me whatever you need."
4. Answer its questions — which repos, which issues are fair game, how tight a
   surface, how often, how it reaches you.
5. It writes the scheduler, the issue picker, and the prompt wiring for your OS,
   then dry-runs it once before arming the schedule.

Start tiny. One repo, one `agent-ready` label you apply by hand, `docs/**` only, a
small change cap, summaries to your terminal. Watch a week of pull requests. Then
widen one ring at a time as you trust it.

## What's in the box

- `BUILD-WITH-YOUR-AGENT.md` — the spec your agent follows: the invariants, the
  architecture, and a per-OS recipe for Mac, Windows, and Linux.
- `config.example.yaml` — the single file you edit. Repos and focus, label gates,
  the file paths and change caps that bound the blast radius, cost knobs, and the
  safety rails.
- `prompts.md` — the standing instruction blocks the sessions run on. The part
  that's universal across stacks; copy-paste ready and yours to edit.
- `reference/` — short, readable reference implementations of the wake loop, the
  issue picker, and the receipt-token verifier. Illustrative, not drop-in.
- `templates/` — scheduler entries for cron, launchd, and Task Scheduler, plus a
  starter standards file.
- `COSTS.md` — read this before you raise the cadence. Subscription vs. metered
  billing, and what changes around June 1, 2026.
- `estimate_cost.py` + `cost-estimator.html` — put a number on it before you arm
  the loop. Both turn the cadence, effort, and timeout dials into estimated
  runs/day and a monthly cost range, subscription vs. metered. The script reads
  your `config.yaml` (or flags); the HTML page is the same math in the browser.

## Aiming it (this is the feature)

The reason to trust this is how tightly you can aim it. Each of these is an
independent dial you can keep narrow:

- **Which repos** — and which one is the focus right now.
- **Which issues** — a label like `agent-ready` you apply by hand is the tightest
  gate.
- **Which files** — allow `docs/**` only, or deny `.github/workflows/**` and
  `infra/**`, or both.
- **How big** — cap the files and lines a single change can touch.
- **Who checks** — a second model reviews every diff before commit.
- **Who approves** — you do. It never merges its own pull request.

Tighten all of them and the blast radius is near zero; loosen them as your
confidence grows.

## Before you start

- **Platform:** the Linux path is what this was built and run on, so it's the
  tested one — specifically a Raspberry Pi 5 (8GB) on Ubuntu 25.10, ARM64, with
  Python 3.13, cron, tmux, and `timeout --foreground` from uutils coreutils.
  Another Linux distribution shares the same primitives but differs in detail, so
  verify on yours too. The macOS and Windows recipes follow the same five
  primitives but haven't been run end-to-end as of this version — testing them is
  planned. If you're on either, treat that column as a solid starting point, not a
  guarantee: have your agent verify each piece on a throwaway issue before you arm
  the schedule. The primitives table in `BUILD-WITH-YOUR-AGENT.md` is where the
  per-OS choices live. On Windows specifically, the recommended path is to run the
  loop inside WSL, which reuses the tested Linux primitives; native Task Scheduler
  is an advanced, still-untested fallback.
- **Cost:** the loop is cheap only if your CLIs are logged into a subscription
  rather than billing an API key, and only if you keep the cadence sane. Read
  `COSTS.md` first, then run `python3 estimate_cost.py config.yaml` (or open
  `cost-estimator.html`) to put a number on your settings.
- **Auth:** GitHub access comes from the `gh` CLI (`gh auth login`). The only
  other credential you might set is a notifier token, if you want phone alerts.

## License

MIT, same as the rest of this repo. Adapt it freely.
