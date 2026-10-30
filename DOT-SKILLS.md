# Dot skills: the workshop and the field notebook

[Browse the workshop](https://skills.amditis.tech/dot-skills/) · [Read the field notes](https://skills.amditis.tech/dot-skills/rough-edges/) · [Read the field report](https://skills.amditis.tech/dot-skills/field-report/)

This part of the repository has three jobs: share useful workflows for ChatGPT dots, make a small start on a community skill exchange, and document the friction encountered while trying to use them. It is independent community work by Joe Amditis, not an official OpenAI marketplace.

The playful design is deliberate. The dot pages should feel whimsical, bouncy, quirky, and fun rather than inherit the more restrained design of the main skill documentation. Keep the paper, pixel helpers, expressive motion, and small surprises. Improve their execution; do not remove the personality in the name of consistency.

## What is available

| Workflow | Use it to | Instructions |
|---|---|---|
| [Status cards](https://skills.amditis.tech/dot-skills/status-cards/) | Keep one progress update grounded in scope and evidence, with separate check and progress-change timestamps | [Markdown playbook](docs/dot-skills/playbooks/status-cards.md) |
| [Incident updates](https://skills.amditis.tech/dot-skills/incident-updates/) | Explain impact, usable workarounds, next ownership, and recovery evidence | [Markdown playbook](docs/dot-skills/playbooks/incident-updates.md) |
| [Visual audits](https://skills.amditis.tech/dot-skills/visual-audits/) | Inspect actual output and report specific, reproducible findings | [Markdown playbook](docs/dot-skills/playbooks/visual-audits.md) |
| [Source evidence](https://skills.amditis.tech/dot-skills/source-evidence/) | Separate a supported claim from an inference, old evidence, or an unperformed check | [Markdown playbook](docs/dot-skills/playbooks/source-evidence.md) |

The current companions are version 0.2.0 Markdown workflow previews. They are not registered stable skills in `skills-catalog.yaml`, native dot plugin packages, or one-click installers. Readable instructions are useful without inventing a host integration. The [manifest](docs/dot-skills/playbooks/index.json) states the format and validation boundary.

The existing `verify-source-evidence-1.0.0-preview.zip` remains a separate historical document preview with its original manifest and validation notes. This refresh does not change or revalidate that archive. The existing [goal-progress-bar skill](project-templates-toolkit/skills/goal-progress-bar/) remains the script-backed renderer for its supported tracker format; the dot status-card playbook covers evidence, presentation, and delivery around it.

## Try a workflow

Read the playbook before giving it to a dot. Replace example details with the actual task, evidence sources, and approved scope. Start with one low-stakes draft or run and inspect the result. Confirm any saved rule or schedule by reading it back. Do not infer an installation, active schedule, connected account, or permission from a downloaded file.

For repeated work, record the approval once and reuse it when it still applies. A new run is not itself a reason to ask again. A new audience, identity, destination, action, or sensitive-data scope may require a new decision. An actual denial must not be bypassed through another identity or route.

### Private task record template

Keep this in the owner's private task context, not in a public issue or graphic:

```text
Goal and acceptance criteria:
Evidence sources and applicable revision:
Approved workspace/channel/original message:
Posting identity:
Permitted actions:
Approved staging destination, if needed:
Cadence, time zone, and end condition:
When to notify; when to remain quiet:
Approval source and scope; saved-rule readback:
Last successful evidence check:
Last supported progress change:
Last verified delivery and message/file identity:
Current blocker, last attempt, and next owner:
```

A record of approval is not a workaround for a tool restriction. The useful behavior is to say exactly what failed and what decision, access, or recovery is actually missing—not ask for the entire job to be approved again.

## Write the field notes for a stranger

Start with the intended task. Then explain what happened, what the owner had to do, what finally worked, and what remains unknown. Explain terms such as “staging” before using them as shorthand. A reader should not need to know the author, the Slack channels, or the previous pull requests to follow the story.

The October 29, 2026 account includes repeated approval requests, a split Slack image publication, browser/VM failures and lost sign-ins, recurring jobs that stop behaving consistently, unrequested initiative, and insufficient diagnostic visibility. Preserve the frustration rather than replacing it with generic safety or troubleshooting language.

Distinguish the author's firsthand observations from independently reproduced defects, product documentation, and speculation. The [Slack incident](https://github.com/openai/codex/issues/58068) has a dated public sequence and a [later successful update](https://github.com/openai/codex/issues/58068#issuecomment-6497709668). One successful route is not evidence of a permanent platform fix. Do not publish private screenshots, names, channel IDs, logs, or account details to make the story look better supported.

Plan and usage statements need current primary sources. OpenAI's [dot guide](https://learn.chatgpt.com/docs/dots) distinguishes dot conversations from Work or Codex tasks that a dot starts or manages. Do not turn the author's reason for experimenting into a blanket promise that every action leaves other usage untouched.

## Contribute a workflow

Open a ready-for-review pull request with:

1. A concrete task and its intended audience; required inputs and tools.
2. A readable procedure, example output, and starter prompt; the approval scope and completion checks.
3. Version, license, provenance, known failures, and the validation actually performed. Distinguish document checks, simulated demos, and live host/connector tests.

Contribute a redacted failure report by explaining the expected result, observed sequence, exact blocker, attempted recovery, and evidence limits. Do not diagnose an internal cause merely from an error message. “I could not verify it” is a useful result when it is specific.

## Maintain the pages

- `docs/dot-skills/index.html`: skill shelf, local tracker lab, and the purpose of the experiment.
- The four workflow subdirectories: examples, method, starter prompt, and download links.
- `docs/dot-skills/rough-edges/index.html`: first-person field notebook with source links.
- `docs/dot-skills/field-report/`: the long first-person essay ("A month with two ChatGPT dots"), with the Blender renders, a 720p web copy of one interstitial, and its share image. The page is static HTML; keep media small (the video is under 5 MB) and give every image real alt text.
- `docs/dot-skills/playbooks/`: downloadable workflow instructions and their manifest.
- `docs/dot-skills/style.css` and `workshop.js`: this section's isolated visual and interaction system.
- `docs/dot-skills/AGENTS.md`: the design and editorial boundaries for future edits.

Pages are checked-in static HTML. There is no production build step or connector dependency for this section. Keep the page and its playbook in agreement. Keep legacy archive URLs working. Do not change the main documentation theme to match this deliberately separate workshop.

## Check a change

Run from the repository root:

```bash
node --test scripts/dot-skills.test.mjs
node scripts/dot-skills-browser.mjs
```

The browser check uses the repository’s Playwright dependency and an installed Chromium. Set `CHROMIUM_EXECUTABLE` to use a system browser. It renders local HTML with external requests blocked; it writes screenshots to a temporary directory or the output directory supplied as its first argument.

Run the full repository validation in `AGENTS.md` before landing changes. The focused tests cover progress calculation and its false-100% guard, separate clocks, input validation, page structure, internal links, download coverage, and motion controls. They do not certify a live dot, Slack delivery, or a persistent browser session.

For a visual pass, open all six pages at desktop, intermediate, and narrow mobile widths. Exercise every scenario, repeated checks, failure and reset, keyboard use, copy success/failure, manual pause, OS reduced motion, blocked storage, and no JavaScript. Check the whole rendered frame. External fonts may be unavailable in an offline runner; record that limit rather than calling it a production rendering check.

The field report and workshop pages have a few easter eggs. Press Allow five times on the report's approval card. Poke Wyndle or Syl for something each of them said, or poke them ten times fast and they fight. Click a `null` in the report. Type "allow" or "devil" on any dot page. Nudge the home page helper ten times fast. Helpers blink on their own timers, except the home page helper, whose pupils follow the pointer. The pokeable dots and the approval card are real buttons, so they work from a keyboard. Pause motion and reduced motion skip the movement but keep the joke.

- `docs/dot-skills/rough-edges/index.html`: first-person field notebook with source links.
- `docs/dot-skills/field-report/`: the long first-person essay ("A month with two ChatGPT dots"), with the Blender renders, a 720p web copy of one interstitial, and its share image. The page is static HTML; keep media small (the video is under 5 MB) and give every image real alt text., six equal milestone weights, and sample clock times. It makes no network request, posts no message, and schedules nothing. Its celebration belongs only to the verified-complete example.
