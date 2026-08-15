# Journalism agent skills

A collection of Agent Skills for journalists, researchers, academics, media professionals, and communications practitioners. The same repository serves Claude Code and Codex while keeping Claude-only commands, agents, and hooks clearly labeled.

**Docs site:** [skills.amditis.tech](https://skills.amditis.tech) — interactive skill browser, setup guides, and full documentation.

## Guides

Setup and workflow guides, separate from the skills themselves:

| Guide | Description |
|-------|-------------|
| [Autonomous and hands-on dev work](https://skills.amditis.tech/autonomy/) | A first-person account of running dev work with Claude in two modes — autonomous sessions that pull tasks off GitHub issues, and hands-on multi-agent reviews at the keyboard — held to one quality bar, with copy-able prompts to adapt the approach to your own agent |
| [Multi-agent workflows](https://skills.amditis.tech/workflows/) | Plain-language guide to running many AI agents on one job — fan-out, pipeline, and adversarial-verify patterns, with real examples from ICIJ, The Markup, Full Fact, and Elicit, plus honest cautions |
| [Persistent sessions](https://skills.amditis.tech/persistent-sessions/) | Keep Claude Code sessions alive through disconnects using tmux — setup, key bindings, activity notifications, and scheduler coexistence |

## What are agent skills?

Skills are modular instruction sets that an AI coding agent loads when relevant to a task. Each skill contains domain knowledge, workflows, templates, and supporting files. Shared skills in this repository follow the [Agent Skills specification](https://agentskills.io/specification); Claude and Codex provide their own installation and runtime layers around that shared content.

## Installation

Choose the section for your client. During the Codex pilot, use only one Codex installation path for a given skill or package.

### Claude Code

**Prerequisite:** You need [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) installed. Run `claude --version` in your terminal to check.

#### Plugins (recommended)

Plugins give you slash commands you can run directly inside Claude Code. Run these two commands inside a Claude Code session:

```
/plugin marketplace add jamditis/claude-skills-journalism
/plugin install pdf-playground@claude-skills-journalism
```

Then restart Claude Code (close and reopen). See the [PDF Playground README](./pdf-playground/) for detailed setup instructions and troubleshooting.

**Available plugins:**

| Plugin | Description | Commands | Updated |
|--------|-------------|----------|--------|
| [autocontext](./autocontext/) | Cross-session knowledge persistence with skill evolution. Lessons accumulate per-skill, and `/autocontext:evolve` folds them back into skill files | `/autocontext:setup`, `/autocontext:init`, `/autocontext:review`, `/autocontext:status`, `/autocontext:evolve` | Apr 27, 2026 |
| [dev-toolkit](./dev-toolkit/) | Twelve development-focused skills for journalists, researchers, and small newsroom dev teams: accessibility (WCAG 2.2), Electron app patterns, mobile/remote debugging, irreversible-decision discipline, Python data pipelines, test-first bug fixing, AI-assisted development workflows, ethical web scraping, no-build frontend patterns, signs-of-taste guidance for web UI, CLAUDE.md context maintenance, and managing attention across long sessions | n/a — skills only | Aug 15, 2026 |
| [journalism-core](./journalism-core/) | Fourteen core journalism skills, including AP-style writing, AI-slop detoxing, source verification (deepfakes/C2PA), FOIA + NJ OPRA requests, fact-checking, interview prep + transcription, story pitches, editorial workflow, crisis communications, newsletter publishing with current Gmail / Yahoo / Outlook bulk-sender requirements, and embedded photo metadata for wire distribution | n/a — skills only | Jul 25, 2026 |
| [okf-wiki](./okf-wiki/) | Scaffold an Open Knowledge Format (OKF) knowledge base: one-concept-per-file markdown with YAML frontmatter, directory navigation, and a validator. Generates a starter wiki that passes its own conformance and secret-leak checks, ships session-start hooks that orient Claude on the knowledge base before it works, and includes an optional GitHub-wiki bootstrap. For newsroom institutional memory, research atlases, decision logs, and infrastructure maps | n/a — skill only | Aug 15, 2026 |
| [pdf-design](./pdf-design/) | PDF report and proposal design system with brand variables, budget tables, and reusable content blocks (stats strips, three-column, four-tile pillars, partner grids) | n/a — skill-only | Jul 21, 2026 |
| [pdf-playground](./pdf-playground/) | Create branded proposals, reports, one-pagers, newsletters, slides, and event materials with an interactive control panel for live design editing (colors, fonts, spacing, sections) and a guided wizard for proposals | `/pdf-playground:proposal`, `/pdf-playground:report`, `/pdf-playground:onepager`, `/pdf-playground:newsletter`, `/pdf-playground:slides`, `/pdf-playground:event`, `/pdf-playground:preview` | Jul 22, 2026 |
| [project-templates-toolkit](./project-templates-toolkit/) | Three skills for setting up and closing out journalism projects: a CLAUDE.md project-memory writer (institutional knowledge), a LESSONS.md retrospective writer (failures and decisions), and a template-selector decision tree across 6 project types | n/a — skills only | Jun 24, 2026 |
| [research-toolkit](./research-toolkit/) | Six skills for research, source preservation, and academic workflows: academic writing, legal paywall-bypass via Unpaywall and library databases, web archiving (Wayback / Archive.today / ArchiveBox), web page change monitoring, AI-enriched digital archive construction, and a curated free-API catalog with sunset currency notes (IEX Cloud, CrowdTangle, ProPublica Congress, X, Reddit) | n/a — skills only | Jul 21, 2026 |
| [security-toolkit](./security-toolkit/) | Four defensive security skills covering OWASP Top 10 fundamentals and supply-chain hardening: pre-deployment audit checklists (auth, input validation, secrets management), secure authentication patterns (password hashing, session management, JWT, OAuth, passkeys), API hardening (rate limiting, CORS, request throttling, defense-in-depth for Express, FastAPI, and serverless), and npm/bun supply-chain hardening with install-time cooldown plus a sandboxed pre-install scan for the bypass case (defends against Mini Shai-Hulud-class worms) | `/security-toolkit:hotpatch` | Jul 22, 2026 |
| [superjawn](./superjawn/) | Research-augmented fork of obra/superpowers. Default-on research phase fires before brainstorming, systematic-debugging, and writing-skills. v1.0.0 ships all 14 skills with no soft dependencies on the upstream `superpowers` plugin | invoked indirectly via skills (e.g. `superjawn:brainstorming`, `superjawn:systematic-debugging`, `superjawn:writing-plans`) | Jul 21, 2026 |
| [video-toolkit](./video-toolkit/) | Four composable skills for social-video accountability reporting: downloading public video from Twitter/X, TikTok, YouTube, Instagram, and Facebook; transcribing it with a provenance sidecar and a CPU path any evaluator can re-run; extracting and vision-analyzing frames; and aggregating the result into an interactive dashboard | n/a — skills only | Jul 22, 2026 |
| [visual-explainer](./visual-explainer/) | HTML diagrams, data tables, architecture views, slide decks, and KPI dashboards adapted from nicobailon/visual-explainer with journalism, newsroom, and academic design sensibilities | `/visual-explainer:project-recap` | Jul 22, 2026 |

#### Skills (manual installation)

Most skills live inside a plugin's `skills/` directory. The `okf-wiki/SKILL.md`, `pdf-design/SKILL.md`, and `visual-explainer/SKILL.md` root-skill packages keep the skill at the package root. To install one skill without taking a whole plugin, clone the repo and copy or symlink the directory that directly contains its `SKILL.md`. Claude Code discovers skills at `~/.claude/skills/<skill-name>/SKILL.md` — one level deep:

```
git clone https://github.com/jamditis/claude-skills-journalism.git ~/projects/claude-skills-journalism
cd ~/projects/claude-skills-journalism
mkdir -p ~/.claude/skills

# Pull a single skill out of a plugin's skills/ directory:
cp -r journalism-core/skills/source-verification ~/.claude/skills/
cp -r research-toolkit/skills/free-apis-catalog ~/.claude/skills/
cp -r research-toolkit/skills/web-archiving ~/.claude/skills/
cp -r dev-toolkit/skills/web-scraping ~/.claude/skills/
cp -r security-toolkit/skills/secure-auth ~/.claude/skills/
cp -r project-templates-toolkit/skills/project-memory ~/.claude/skills/

# A root-skill package is already the directory to copy:
cp -r okf-wiki ~/.claude/skills/

# Or symlink so git pull updates them in place (ln -sfn replaces an existing link):
ln -sfn "$PWD/research-toolkit/skills/free-apis-catalog" ~/.claude/skills/free-apis-catalog
ln -sfn "$PWD/visual-explainer" ~/.claude/skills/visual-explainer
```

Do not clone the repo directly into `~/.claude/skills/journalism-skills/` — that nests each `SKILL.md` too deep and Claude Code won't find them.

### Codex

**Prerequisite:** Install [Codex CLI](https://developers.openai.com/codex/cli). Run `codex --version` in your terminal to check. The native package route below is verified with Codex CLI 0.147.0.

This repository ships native Codex manifests for 11 skill packages. Install one package through the marketplace:

```bash
codex plugin marketplace add jamditis/claude-skills-journalism
codex plugin add journalism-core@claude-skills-journalism
```

The native manifests expose shared skills. They do not convert Claude commands, agents, or hooks into Codex components. Autocontext remains Claude-only because its current package contains Claude commands and hooks, not a shared `SKILL.md`.

You can instead install standards-based skills with the `skills` CLI. This user-level command makes the 14 core skills available across your Codex projects:

```bash
npx skills@latest add https://github.com/jamditis/claude-skills-journalism/tree/master/journalism-core \
  --skill '*' --agent codex --copy -g -y
```

That command installs `journalism-core` in Codex's documented user skill directory, `~/.agents/skills`. The clean-install canary checks that exact global destination. Remove `-g` to install into the current project's `.agents/skills` directory and record the source and content hashes in that project's `skills-lock.json`. To install one skill instead:

```bash
npx skills@latest add jamditis/claude-skills-journalism \
  --skill fact-check-workflow --agent codex --copy -g -y
```

Codex desktop can [import skills from another agent](https://learn.chatgpt.com/docs/import.md). Import leaves the source installation in place. Until duplicate-identity and uninstall behavior has been tested for this repository, do not import a skill and also install the same skill through `npx skills` or the package route.

Codex's bundled skill installer writes to a different Codex-specific directory and is not a tested installation path for this repository. Codex does not deduplicate same-name skills across install roots, so don't combine it with the `.agents/skills` route above.

Use only one Codex installation path for the same skill identity. Codex does not deduplicate same-name skills across install roots.

See the checked-in [Codex compatibility matrix](./plans/codex-compatibility-matrix.md) for tested versions, package boundaries, and pending runtime gates. A valid install is not a package-wide runtime support claim. The historical pilots remain tied to their recorded snapshots. The August 2026 structure check covers native manifest discovery and clean installation.

### Claude.ai

Skills can be added via the Claude.ai interface under Settings > Skills.

## Skills overview

The `Updated` column in every table below is the date that skill or plugin last
changed, taken from git history rather than typed by hand. Use it to judge
whether your installed copy has drifted: a skill that cites statutes, platform
APIs, or vendor behavior is worth re-checking against its sources once it is
several months old. The same dates appear as tape on each card at
[skills.amditis.tech](https://skills.amditis.tech/), where the tape yellows with
age.

### Core journalism skills (in `journalism-core` plugin)

These fourteen skills ship together as the [journalism-core](./journalism-core/) plugin. Install via `/plugin install journalism-core@claude-skills-journalism` to get all of them at once.

| Skill | Description | Updated |
|-------|-------------|--------|
| [ai-writing-detox](./journalism-core/skills/ai-writing-detox/) | Eliminate AI-generated patterns that erode reader trust. Banned words, phrases, and structures with alternatives | May 8, 2026 |
| [crisis-communications](./journalism-core/skills/crisis-communications/) | Breaking news protocol, rapid verification, crisis response, misinformation countering | Jul 21, 2026 |
| [data-journalism](./journalism-core/skills/data-journalism/) | Dataset analysis, chart and map creation, statistical reasoning, data-driven story structure | Jul 21, 2026 |
| [editorial-workflow](./journalism-core/skills/editorial-workflow/) | Story assignment tracking, deadline management, editorial calendars, handoff protocols | May 8, 2026 |
| [fact-check-workflow](./journalism-core/skills/fact-check-workflow/) | Claim extraction, evidence gathering, rating scales, correction protocols | Jul 21, 2026 |
| [foia-requests](./journalism-core/skills/foia-requests/) | Public records request drafting (federal FOIA + NJ OPRA), tracking, appeals, current statutory citations | Jul 7, 2026 |
| [interview-prep](./journalism-core/skills/interview-prep/) | Pre-interview research, question frameworks, recording consent, attribution guidelines | May 8, 2026 |
| [interview-transcription](./journalism-core/skills/interview-transcription/) | Whisper / WhisperX transcription pipelines, quote management, speaker diarization | May 8, 2026 |
| [newsletter-publishing](./journalism-core/skills/newsletter-publishing/) | Email newsletter creation, subscriber management, deliverability, 2024–2026 Gmail / Yahoo / Outlook bulk-sender compliance | May 8, 2026 |
| [newsroom-style](./journalism-core/skills/newsroom-style/) | AP Style enforcement, attribution rules, headline formatting, number conventions | May 8, 2026 |
| [photo-metadata](./journalism-core/skills/photo-metadata/) | Embed caption, byline, credit, alt text, keywords, copyright / Creative Commons license, AI-source labeling (IPTC Digital Source Type), and Google-Images licensing into a photo's IPTC/EXIF/XMP metadata; strip GPS for source protection; read C2PA Content Credentials; batch-tag a folder for a news wire | Jul 24, 2026 |
| [social-media-intelligence](./journalism-core/skills/social-media-intelligence/) | Narrative tracking, coordinated-campaign analysis, account authenticity checks, OSINT for digital investigations | Jul 21, 2026 |
| [source-verification](./journalism-core/skills/source-verification/) | SIFT method, image and video verification, deepfake detection (2026), C2PA Content Credentials, verification trails | Jul 21, 2026 |
| [story-pitch](./journalism-core/skills/story-pitch/) | Pitch templates for daily news, features, investigations, op-eds, and freelance queries | May 8, 2026 |

### Research and academic skills (in `research-toolkit` plugin)

These six skills ship together as the [research-toolkit](./research-toolkit/) plugin. Install via `/plugin install research-toolkit@claude-skills-journalism` to get all of them at once.

| Skill | Description | Updated |
|-------|-------------|--------|
| [academic-writing](./research-toolkit/skills/academic-writing/) | Research design, literature reviews, IMRaD structure, peer review responses, grant proposals | May 8, 2026 |
| [content-access](./research-toolkit/skills/content-access/) | Unpaywall, CORE, Semantic Scholar APIs, library databases, ethical access patterns | Jul 21, 2026 |
| [digital-archive](./research-toolkit/skills/digital-archive/) | Building archives with AI enrichment, entity extraction, knowledge graphs | Jul 21, 2026 |
| [free-apis-catalog](./research-toolkit/skills/free-apis-catalog/) | Curated free-API catalog organized by journalism use-case, with currency notes for major API sunsets (IEX Cloud, CrowdTangle, ProPublica Congress, X, Reddit) and an evaluation rubric | May 10, 2026 |
| [page-monitoring](./research-toolkit/skills/page-monitoring/) | Change detection, RSS generation, webhook alerts, automatic archiving on changes | Jul 21, 2026 |
| [web-archiving](./research-toolkit/skills/web-archiving/) | Wayback Machine, Archive.today, legal evidence preservation, multi-archive redundancy | Jul 21, 2026 |

### Design and production

| Skill | Description | Updated |
|-------|-------------|--------|
| [pdf-design](./pdf-design/) | Professional PDF reports and proposals with brand system, budget tables, and multi-page layouts. For the full interactive experience, use [pdf-playground](./pdf-playground/) instead | Jul 21, 2026 |
| [visual-explainer](./visual-explainer/) | Turn complex data into styled HTML pages — architecture diagrams, data tables, flowcharts, timelines, source maps, and dashboards with dark/light theme support. Now registered as a plugin (`/plugin install visual-explainer@claude-skills-journalism`) | Jul 22, 2026 |

### PDF Playground skill

This skill ships inside the [pdf-playground](./pdf-playground/) plugin.

| Skill | Description | Updated |
|-------|-------------|--------|
| [document-design](./pdf-playground/skills/document-design/) | Create print-ready HTML proposals, reports, one-pagers, newsletters, slides, flyers, and other PDF-ready documents with reusable brand and layout patterns | Jul 22, 2026 |

### Superjawn skills

These fourteen skills ship inside the [superjawn](./superjawn/) plugin.

| Skill | Description | Updated |
|-------|-------------|--------|
| [brainstorming](./superjawn/skills/brainstorming/) | Explore intent, requirements, design, and relevant research before creative implementation work | Jul 21, 2026 |
| [dispatching-parallel-agents](./superjawn/skills/dispatching-parallel-agents/) | Divide independent tasks among parallel agents without shared-state conflicts | May 7, 2026 |
| [executing-plans](./superjawn/skills/executing-plans/) | Execute a written implementation plan with freshness and review checkpoints | Jul 21, 2026 |
| [finishing-a-development-branch](./superjawn/skills/finishing-a-development-branch/) | Verify completed work and choose a safe integration, pull request, or cleanup path | May 7, 2026 |
| [receiving-code-review](./superjawn/skills/receiving-code-review/) | Evaluate review feedback against the code before implementing it | May 7, 2026 |
| [requesting-code-review](./superjawn/skills/requesting-code-review/) | Request focused review before integration or after a major implementation | May 8, 2026 |
| [subagent-driven-development](./superjawn/skills/subagent-driven-development/) | Execute independent plan tasks with agents in the current session | May 8, 2026 |
| [systematic-debugging](./superjawn/skills/systematic-debugging/) | Investigate root cause and relevant evidence before proposing a bug fix | Jul 21, 2026 |
| [test-driven-development](./superjawn/skills/test-driven-development/) | Write a failing test before implementing a feature or bug fix | May 7, 2026 |
| [using-git-worktrees](./superjawn/skills/using-git-worktrees/) | Create isolated worktrees with safe directory selection and verification | Jul 21, 2026 |
| [using-superjawn](./superjawn/skills/using-superjawn/) | Discover and invoke the right Superjawn skill for the current task | May 7, 2026 |
| [verification-before-completion](./superjawn/skills/verification-before-completion/) | Run and inspect verification evidence before claiming work is complete | May 7, 2026 |
| [writing-plans](./superjawn/skills/writing-plans/) | Turn a specification or requirements into a checked implementation plan | May 7, 2026 |
| [writing-skills](./superjawn/skills/writing-skills/) | Research, create, edit, and verify reusable skills | Jul 21, 2026 |

### Project documentation skills (in `project-templates-toolkit` plugin)

These three skills ship together as the [project-templates-toolkit](./project-templates-toolkit/) plugin. Install via `/plugin install project-templates-toolkit@claude-skills-journalism` to get all of them at once.

| Skill | Description | Updated |
|-------|-------------|--------|
| [project-memory](./project-templates-toolkit/skills/project-memory/) | Generate CLAUDE.md files that capture project-specific knowledge. Includes templates for editorial tools, events, publications, research, pipelines, and archives | May 11, 2026 |
| [project-retrospective](./project-templates-toolkit/skills/project-retrospective/) | Generate LESSONS.md files that document what worked and what didn't. Templates for investigations, events, publications, and tools | May 10, 2026 |
| [template-selector](./project-templates-toolkit/skills/template-selector/) | Decision tree for choosing the right project documentation template | May 10, 2026 |

### Development skills (in `dev-toolkit` plugin)

These twelve skills ship together as the [dev-toolkit](./dev-toolkit/) plugin. Install via `/plugin install dev-toolkit@claude-skills-journalism` to get all of them at once, or copy individual skills from `dev-toolkit/skills/<name>/`.

| Skill | Description | Updated |
|-------|-------------|--------|
| [accessibility-compliance](./dev-toolkit/skills/accessibility-compliance/) | WCAG 2.2 baseline, alt text, focus management, motion preferences, accessible charts | Jul 21, 2026 |
| [claude-md-updater](./dev-toolkit/skills/claude-md-updater/) | Detect session lessons, new paths, infra changes, and workflows and propose scoped CLAUDE.md edits for approval | Jul 21, 2026 |
| [context-engineering-fundamentals](./dev-toolkit/skills/context-engineering-fundamentals/) | Attention budget, lost-in-middle recall, context degradation patterns, and mitigations for long sessions | Aug 15, 2026 |
| [electron-dev](./dev-toolkit/skills/electron-dev/) | Electron security model (contextIsolation, sandbox), IPC patterns, packaging | May 8, 2026 |
| [mobile-debugging](./dev-toolkit/skills/mobile-debugging/) | Eruda, vConsole, Chrome DevTools on Android, Safari Web Inspector for iOS, console capture | Jul 21, 2026 |
| [one-way-door](./dev-toolkit/skills/one-way-door/) | Flag irreversible architectural decisions (data models, infra, auth, APIs) before committing | Jun 10, 2026 |
| [python-pipeline](./dev-toolkit/skills/python-pipeline/) | Data pipelines (pandas, polars, DuckDB, asyncio) with modular architecture | Jul 21, 2026 |
| [test-first-bugs](./dev-toolkit/skills/test-first-bugs/) | Test-driven bug fixing: write failing test first, then fix with subagents | May 8, 2026 |
| [vibe-coding](./dev-toolkit/skills/vibe-coding/) | AI-assisted development workflow (Claude Code, Cursor, Aider, Continue) | May 8, 2026 |
| [web-scraping](./dev-toolkit/skills/web-scraping/) | Ethical scraping patterns (Playwright, robots.txt, anti-bot defense, terms-of-service) | Jul 21, 2026 |
| [web-ui-best-practices](./dev-toolkit/skills/web-ui-best-practices/) | Container queries, `:has()`, view transitions, scroll-driven animations, signs of taste in web UI | May 8, 2026 |
| [zero-build-frontend](./dev-toolkit/skills/zero-build-frontend/) | ESM import maps, htmx, Alpine.js, no-build deployment | Jul 21, 2026 |

### Security skills (in `security-toolkit` plugin)

These four skills ship together as the [security-toolkit](./security-toolkit/) plugin, paired with the `/security-toolkit:hotpatch` slash command. Install via `/plugin install security-toolkit@claude-skills-journalism` to get all of them at once.

| Skill | Description | Updated |
|-------|-------------|--------|
| [api-hardening](./security-toolkit/skills/api-hardening/) | Rate limiting, input validation, CORS, security headers, API key management, defense-in-depth for Express, FastAPI, and serverless | May 9, 2026 |
| [secure-auth](./security-toolkit/skills/secure-auth/) | Production-ready authentication patterns: password hashing, session management, JWT, OAuth, passkeys / WebAuthn, MFA | Jul 21, 2026 |
| [security-checklist](./security-toolkit/skills/security-checklist/) | Pre-deployment security audit covering OWASP Top 10 fundamentals: authentication, input validation, secrets, database security, compliance basics | May 9, 2026 |
| [supply-chain-hardening](./security-toolkit/skills/supply-chain-hardening/) | npm/bun install-time cooldown plus sandboxed pre-install scan (bwrap on Linux, sandbox-exec on macOS). Defends against Mini Shai-Hulud-class worms; paired with `/security-toolkit:hotpatch` for the cooldown-bypass case | May 11, 2026 |

### Video analysis skills (in `video-toolkit` plugin)

These four skills ship together as the [video-toolkit](./video-toolkit/) plugin and compose into one pipeline. Install via `/plugin install video-toolkit@claude-skills-journalism`, or copy individual skills from `video-toolkit/skills/<name>/`.

| Skill | What it does | Updated |
|-------|--------------|--------|
| [video-download](./video-toolkit/skills/video-download/) | Collect public video from Twitter/X, TikTok, YouTube, Instagram, and Facebook via yt-dlp, with a browser-automation fallback for broken extractors | Jul 22, 2026 |
| [video-transcribe](./video-toolkit/skills/video-transcribe/) | Batch Whisper transcription with a provenance sidecar per transcript; the CPU `whisper.cpp` path is the transcript of record so an auditor can re-run it without a GPU | Jul 22, 2026 |
| [video-frames](./video-toolkit/skills/video-frames/) | Extract frames, build 3x3 grid composites, and run vision analysis over on-screen text, setting, and presentation style | Jul 22, 2026 |
| [video-dashboard](./video-toolkit/skills/video-dashboard/) | Aggregate transcripts and frame analysis into topic, tone, and cross-platform views behind a single-page dashboard | Jul 22, 2026 |

## Hooks

Hooks are automated checks that run at specific points in your workflow. Most are **non-blocking warnings**, but three block intentionally until you resolve them: `one-way-door-check`, `enforce-test-first`, and `no-ai-attribution`.

### Writing quality hooks

| Hook | Event | Description |
|------|-------|-------------|
| [ap-style-check](./hooks/ap-style-check.md) | PostToolUse | Flag common AP Style violations |
| [ai-slop-detector](./hooks/ai-slop-detector.md) | PostToolUse | Warn about AI-generated patterns |
| [accessibility-check](./hooks/accessibility-check.md) | PostToolUse | Check alt text, heading structure, link text |
| [copywriting-preflight](./hooks/copywriting-preflight.md) | UserPromptSubmit | Interview for intent before drafting a new piece or revision |

### Verification hooks

| Hook | Event | Description |
|------|-------|-------------|
| [source-attribution-check](./hooks/source-attribution-check.md) | PostToolUse | Flag unattributed quotes and claims |
| [verification-reminder](./hooks/verification-reminder.md) | PostToolUse | Prompt to verify facts before including |
| [data-methodology-check](./hooks/data-methodology-check.md) | PostToolUse | Ensure data stories include methodology |

### Editorial workflow hooks

| Hook | Event | Description |
|------|-------|-------------|
| [source-diversity-check](./hooks/source-diversity-check.md) | PostToolUse | Note when sources may lack diversity |
| [legal-review-flag](./hooks/legal-review-flag.md) | PostToolUse | Flag potentially defamatory content |
| [pre-publish-checklist](./hooks/pre-publish-checklist.md) | Stop | Reminder checklist before completing tasks |
| [deadline-tracker](./hooks/deadline-tracker.md) | SessionStart | Surface upcoming deadlines |

### Preservation hooks

| Hook | Event | Description |
|------|-------|-------------|
| [archive-reminder](./hooks/archive-reminder.md) | PostToolUse | Remind to archive URLs when citing sources |

### Development hooks

| Hook | Event | Description |
|------|-------|-------------|
| [one-way-door-check](./hooks/one-way-door-check.md) | PreToolUse | Block creation of files representing irreversible architectural decisions |
| [bug-report-detector](./hooks/bug-report-detector.md) | UserPromptSubmit | Detect bug reports and remind to follow test-first workflow |
| [enforce-test-first](./hooks/enforce-test-first.md) | PreToolUse | Block source code edits until a test file has been written |
| [pre-commit-review](./hooks/pre-commit-review.md) | PreToolUse | Surface the staged diff for line-by-line review before a commit, and flag deletions of safety-critical guardrails |
| [no-ai-attribution](./hooks/no-ai-attribution.md) | PreToolUse | Block AI authorship credit in commits, PR bodies, and comments before they land |

## Skill structure

Each shared skill follows the Agent Skills standard:

```
skill-name/
├── SKILL.md          # Main instructions (required)
├── examples/         # Example inputs/outputs (optional)
├── templates/        # Reusable templates (optional)
└── scripts/          # Helper scripts (optional)
```

### SKILL.md format

```yaml
---
name: skill-name
description: When to use this skill and what it does
---

# Skill title

Instructions and knowledge for Claude to use.
```

## Usage examples

### Source verification

When you ask Claude to verify a claim or check a source:

```
"Can you help me verify this viral tweet claiming [X]?"
"What steps should I take to verify this document?"
"Help me check if this image is authentic"
```

### Interview preparation

When preparing for interviews:

```
"Help me prepare questions for interviewing the mayor about the budget"
"What background research should I do before this interview?"
"Create a question framework for an investigative interview"
```

### Story pitching

When developing story ideas:

```
"Help me pitch this feature story idea"
"Draft a query letter for this freelance investigation"
"What's the angle for this daily news story?"
```

### Fact-checking

When verifying claims:

```
"Walk me through fact-checking this politician's statement"
"Help me document the evidence for this claim"
"What rating should this fact-check receive?"
```

### Project documentation

When setting up or closing projects:

```
"Generate a CLAUDE.md for this investigation project"
"Write a retrospective for the conference website we just finished"
"Which template should I use for this newsletter project?"
```

### Social media intelligence

When investigating online narratives:

```
"Help me analyze this account for authenticity"
"Track how this claim is spreading across platforms"
"Check for signs of coordinated behavior"
```

### Web archiving and monitoring

When preserving or tracking content:

```
"Archive this page to multiple services for redundancy"
"Set up monitoring for changes to this government page"
"Find academic papers related to this topic"
```

## Contributing

Contributions welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full guide — skill structure, testing, and style guidelines.

Quick version: fork, create your skill with a `SKILL.md` frontmatter file, run `npm run validate:agent-skills`, test the clients affected by your change, and submit a PR.

## Target audiences

- **Investigative journalists** - source verification, FOIA, data analysis
- **Newsroom developers** - scraping, data pipelines, visualization tools
- **Academic researchers** - writing, methodology, peer review
- **Graduate students** - thesis writing, literature reviews, proposals
- **Communications professionals** - content strategy, research methods
- **Fact-checkers** - verification workflows, evidence documentation
- **Digital archivists** - preservation, metadata, knowledge graphs
- **Editors** - workflow management, style enforcement, quality control

## Related resources

- [Anthropic official skills](https://github.com/anthropics/skills)
- [Claude Code documentation](https://docs.anthropic.com/claude-code)
- [Codex skills documentation](https://learn.chatgpt.com/docs/build-skills)
- [Agent Skills specification](https://agentskills.io/specification)
- [autopunk-media-skills](https://github.com/ur-grue/autopunk-media-skills) — broadcast, TV, podcast, and radio production skills; complements this repo's investigative focus. Free library, paired with a paid product ([autopunk.io](https://autopunk.io))
- [NICAR (Investigative Reporters & Editors)](https://www.ire.org/nicar/)
- [First Draft News](https://firstdraftnews.org/)
- [Verification Handbook](https://verificationhandbook.com/)
- [AP Stylebook](https://www.apstylebook.com/)
- [Bellingcat OSINT guides](https://www.bellingcat.com/resources/)

## License

MIT License - See [LICENSE](./LICENSE) for details.

## Author

Joe Amditis ([@jamditis](https://github.com/jamditis))
