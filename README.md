# Claude skills for journalism, media, and academia

A curated collection of Claude Code skills designed for journalists, researchers, academics, media professionals, and communications practitioners.

**Docs site:** [jamditis.github.io/claude-skills-journalism](https://jamditis.github.io/claude-skills-journalism/) — interactive skill browser, setup guides, and full documentation.

## Guides

Setup and workflow guides, separate from the skills themselves:

| Guide | Description |
|-------|-------------|
| [Persistent sessions](https://jamditis.github.io/claude-skills-journalism/persistent-sessions/) | Keep Claude Code sessions alive through disconnects using tmux — setup, key bindings, activity notifications, and scheduler coexistence |

## What are Claude skills?

Skills are modular instruction sets that extend Claude's capabilities for specialized tasks. Each skill contains domain-specific knowledge, workflows, templates, and best practices that Claude loads automatically when relevant to your work.

## Installation

**Prerequisite:** You need [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) installed. Run `claude --version` in your terminal to check.

### Plugins (recommended)

Plugins give you slash commands you can run directly inside Claude Code. Run these two commands in your terminal:

```
claude plugin marketplace add https://github.com/jamditis/claude-skills-journalism
claude plugin install pdf-playground@claude-skills-journalism
```

Then restart Claude Code (close and reopen). See the [PDF Playground README](./pdf-playground/) for detailed setup instructions and troubleshooting.

**Available plugins:**

| Plugin | Description | Commands |
|--------|-------------|----------|
| [pdf-playground](./pdf-playground/) | Create branded proposals, reports, one-pagers, newsletters, slides, and event materials with an interactive control panel for live design editing (colors, fonts, spacing, sections) and a guided wizard for proposals | `/pdf-playground:proposal`, `/pdf-playground:report`, `/pdf-playground:onepager`, `/pdf-playground:newsletter`, `/pdf-playground:slides`, `/pdf-playground:event`, `/pdf-playground:preview` |

### Skills (manual installation)

Skills load automatically when relevant to your work. To install them, clone this repo into your Claude skills directory:

```
git clone https://github.com/jamditis/claude-skills-journalism.git ~/.claude/skills/journalism-skills
```

Or copy individual skills:

```
cp -r source-verification ~/.claude/skills/
```

### For Claude.ai users

Skills can be added via the Claude.ai interface under Settings > Skills.

## Skills overview

### Core journalism skills

| Skill | Description |
|-------|-------------|
| [source-verification](./source-verification/) | SIFT method, digital verification, reverse image search, social media account analysis, building verification trails |
| [foia-requests](./foia-requests/) | Public records request drafting, tracking systems, appeals process, state-specific guidance |
| [data-journalism](./data-journalism/) | Data acquisition, cleaning, analysis, visualization, and storytelling for newsrooms |
| [newsroom-style](./newsroom-style/) | AP Style enforcement, attribution rules, headline formatting, number conventions |
| [interview-prep](./interview-prep/) | Pre-interview research, question frameworks, recording consent, attribution guidelines |
| [interview-transcription](./interview-transcription/) | Recording workflows, transcription, quote management, source databases |
| [story-pitch](./story-pitch/) | Pitch templates for daily news, features, investigations, op-eds, and freelance queries |
| [fact-check-workflow](./fact-check-workflow/) | Claim extraction, evidence gathering, rating scales, correction protocols |
| [editorial-workflow](./editorial-workflow/) | Story assignment tracking, deadline management, editorial calendars, handoff protocols |
| [crisis-communications](./crisis-communications/) | Breaking news protocol, rapid verification, crisis response, misinformation countering |
| [social-media-intelligence](./social-media-intelligence/) | Social monitoring, narrative tracking, account analysis, coordination detection, OSINT |

### Communications and publishing

| Skill | Description |
|-------|-------------|
| [newsletter-publishing](./newsletter-publishing/) | Email newsletter creation, subscriber management, deliverability, A/B testing |

### Design and production

| Skill | Description |
|-------|-------------|
| [pdf-design](./pdf-design/) | Professional PDF reports and proposals with brand system, budget tables, and multi-page layouts. For the full interactive experience, use [pdf-playground](./pdf-playground/) instead |
| [visual-explainer](./visual-explainer/) | Turn complex data into styled HTML pages — architecture diagrams, data tables, flowcharts, timelines, source maps, and dashboards with dark/light theme support |

### Writing quality

| Skill | Description |
|-------|-------------|
| [ai-writing-detox](./ai-writing-detox/) | Eliminate AI-generated patterns that erode reader trust. Banned words, phrases, and structures with alternatives |

### Project documentation

| Skill | Description |
|-------|-------------|
| [project-memory](./project-memory/) | Generate CLAUDE.md files that capture project-specific knowledge. Includes templates for editorial tools, events, publications, research, pipelines, and archives |
| [project-retrospective](./project-retrospective/) | Generate LESSONS.md files that document what worked and what didn't. Templates for investigations, events, publications, and tools |
| [template-selector](./template-selector/) | Decision tree for choosing the right project documentation template |

### Academic and research

| Skill | Description |
|-------|-------------|
| [academic-writing](./academic-writing/) | Research design, literature reviews, IMRaD structure, peer review responses, grant proposals |
| [digital-archive](./digital-archive/) | Building archives with AI enrichment, entity extraction, knowledge graphs |
| [web-archiving](./web-archiving/) | Wayback Machine, Archive.today, legal evidence preservation, multi-archive redundancy |
| [content-access](./content-access/) | Unpaywall, CORE, Semantic Scholar APIs, library databases, ethical access patterns |
| [page-monitoring](./page-monitoring/) | Change detection, RSS generation, webhook alerts, automatic archiving on changes |

### Development (for building tools)

| Skill | Description |
|-------|-------------|
| [test-first-bugs](./test-first-bugs/) | Test-driven bug fixing: write failing test first, then fix with subagents |
| [vibe-coding](./vibe-coding/) | AI-assisted software development methodology based on YC best practices |
| [electron-dev](./electron-dev/) | Electron + React desktop application development patterns |
| [python-pipeline](./python-pipeline/) | Data processing pipelines with modular architecture |
| [web-scraping](./web-scraping/) | Content extraction with anti-bot handling and poison pill detection |
| [zero-build-frontend](./zero-build-frontend/) | Static web apps without build tools, CDN-loaded frameworks |
| [mobile-debugging](./mobile-debugging/) | Eruda, vConsole, remote debugging, iOS debugging, console capture |
| [accessibility-compliance](./accessibility-compliance/) | WCAG compliance, alt text, accessible charts, keyboard navigation |
| [one-way-door](./one-way-door/) | Flag irreversible architectural decisions (data models, infra, auth, APIs) before committing |

### Security (ship without getting sued)

| Skill | Description |
|-------|-------------|
| [security-checklist](./security-checklist/) | Pre-deployment security audit covering auth, input validation, secrets, and compliance |
| [secure-auth](./secure-auth/) | Production-ready authentication patterns (sessions, JWTs, OAuth, MFA) |
| [api-hardening](./api-hardening/) | Rate limiting, input validation, CORS, API key management |

## Hooks

Hooks are automated checks that run at specific points in your workflow. All hooks are **non-blocking warnings**—they provide guidance but don't prevent actions.

### Writing quality hooks

| Hook | Event | Description |
|------|-------|-------------|
| [ap-style-check](./hooks/ap-style-check.md) | PostToolUse | Flag common AP Style violations |
| [ai-slop-detector](./hooks/ai-slop-detector.md) | PostToolUse | Warn about AI-generated patterns |
| [accessibility-check](./hooks/accessibility-check.md) | PostToolUse | Check alt text, heading structure, link text |

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

## Skill structure

Each skill follows the Claude Agent Skills standard:

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

Contributions welcome! Please:

1. Fork the repository
2. Create a skill following the structure above
3. Include practical examples and templates
4. Submit a pull request

### Skill guidelines

- Focus on journalism, media, communications, or academic use cases
- Include actionable workflows, not just information
- Provide templates where applicable
- Cite sources for verification methods and standards
- Test with Claude Code before submitting

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
- [Agent Skills Standard](http://agentskills.io)
- [NICAR (Investigative Reporters & Editors)](https://www.ire.org/nicar/)
- [First Draft News](https://firstdraftnews.org/)
- [Verification Handbook](https://verificationhandbook.com/)
- [AP Stylebook](https://www.apstylebook.com/)
- [Bellingcat OSINT guides](https://www.bellingcat.com/resources/)

## License

MIT License - See [LICENSE](./LICENSE) for details.

## Author

Joe Amditis ([@jamditis](https://github.com/jamditis))

---

*Built with Claude Code*
