# Claude skills for journalism, media, and academia

A curated collection of Claude Code skills designed for journalists, researchers, academics, media professionals, and communications practitioners.

## What are Claude skills?

Skills are modular instruction sets that extend Claude's capabilities for specialized tasks. Each skill contains domain-specific knowledge, workflows, templates, and best practices that Claude loads automatically when relevant to your work.

## Installation

### For Claude Code users

```bash
# Clone to your Claude skills directory
git clone https://github.com/jamditis/claude-skills-journalism.git ~/.claude/skills/journalism-skills

# Or install individual skills
cp -r source-verification ~/.claude/skills/
```

### For Claude.ai users

Skills can be added via the Claude.ai interface under Settings > Skills.

## Skills overview

### Journalism and media

| Skill | Description |
|-------|-------------|
| [source-verification](./source-verification/) | SIFT method, digital verification, reverse image search, social media account analysis, building verification trails |
| [foia-requests](./foia-requests/) | Public records request drafting, tracking systems, appeals process, state-specific guidance |
| [data-journalism](./data-journalism/) | Data acquisition, cleaning, analysis, visualization, and storytelling for newsrooms |
| [interview-transcription](./interview-transcription/) | Interview preparation, recording workflows, transcription, quote management, source databases |
| [social-media-intelligence](./social-media-intelligence/) | Social monitoring, narrative tracking, account analysis, coordination detection, OSINT |
| [crisis-communications](./crisis-communications/) | Breaking news protocol, rapid verification, crisis response templates, misinformation counter-messaging |

### Academic and research

| Skill | Description |
|-------|-------------|
| [academic-writing](./academic-writing/) | Research design, literature reviews, IMRaD structure, peer review responses, grant proposals |
| [digital-archive](./digital-archive/) | Building archives with AI enrichment, entity extraction, knowledge graphs |

### Communications and publishing

| Skill | Description |
|-------|-------------|
| [newsletter-publishing](./newsletter-publishing/) | Email newsletter creation, subscriber management, deliverability, A/B testing, analytics |

### Development (for building tools)

| Skill | Description |
|-------|-------------|
| [vibe-coding](./vibe-coding/) | AI-assisted software development methodology based on YC best practices |
| [electron-dev](./electron-dev/) | Electron + React desktop application development patterns |
| [python-pipeline](./python-pipeline/) | Data processing pipelines with modular architecture |
| [web-scraping](./web-scraping/) | Content extraction with anti-bot handling and poison pill detection |
| [zero-build-frontend](./zero-build-frontend/) | Static web apps without build tools, CDN-loaded frameworks |
| [accessibility-compliance](./accessibility-compliance/) | WCAG compliance, alt text, accessible charts, keyboard navigation, screen reader support |

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

### FOIA requests

When working with public records:

```
"Draft a FOIA request for EPA records about [topic]"
"How do I appeal this FOIA denial?"
"Track my pending public records requests"
```

### Data journalism

When analyzing data for stories:

```
"Help me clean this messy CSV of campaign finance data"
"What's the right chart type for showing change over time?"
"Write a methodology box for my data story"
```

### Academic writing

When working on research:

```
"Help me structure my literature review"
"Draft a response to these peer reviewer comments"
"Create an abstract for my paper about [topic]"
```

### Interview management

When conducting interviews:

```
"Help me prepare questions for an interview with [source]"
"Set up a transcription workflow for my recordings"
"Create a source database for my investigation"
```

### Social media intelligence

When investigating online narratives:

```
"Help me analyze this account for authenticity"
"Track how this claim is spreading across platforms"
"Check for signs of coordinated behavior"
```

### Crisis communications

When handling breaking news or crises:

```
"Help me verify this breaking news claim"
"Draft a holding statement for [situation]"
"Set up a rapid verification workflow"
```

### Newsletter publishing

When building audience through email:

```
"Help me design a newsletter template"
"What subject lines work best for journalism newsletters?"
"Set up A/B testing for my newsletter"
```

### Accessibility

When building accessible content:

```
"Write alt text for this news photo"
"Make this data visualization accessible"
"Audit my site for WCAG compliance"
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

## Related resources

### Skills and context engineering
- [Agent Skills for Context Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) - Foundational skill patterns
- [Anthropic official skills](https://github.com/anthropics/skills)
- [Claude Code documentation](https://docs.anthropic.com/claude-code)
- [Agent Skills Standard](http://agentskills.io)

### Journalism resources
- [NICAR (Investigative Reporters & Editors)](https://www.ire.org/nicar/)
- [First Draft News](https://firstdraftnews.org/)
- [Verification Handbook](https://verificationhandbook.com/)
- [Bellingcat OSINT guides](https://www.bellingcat.com/resources/)

## License

MIT License - See [LICENSE](./LICENSE) for details.

## Author

Joe Amditis ([@jamditis](https://github.com/jamditis))

---

*Built with Claude Code*
