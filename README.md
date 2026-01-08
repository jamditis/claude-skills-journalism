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

### Academic and research

| Skill | Description |
|-------|-------------|
| [academic-writing](./academic-writing/) | Research design, literature reviews, IMRaD structure, peer review responses, grant proposals |
| [digital-archive](./digital-archive/) | Building archives with AI enrichment, entity extraction, knowledge graphs |

### Development (for building tools)

| Skill | Description |
|-------|-------------|
| [vibe-coding](./vibe-coding/) | AI-assisted software development methodology based on YC best practices |
| [electron-dev](./electron-dev/) | Electron + React desktop application development patterns |
| [python-pipeline](./python-pipeline/) | Data processing pipelines with modular architecture |
| [web-scraping](./web-scraping/) | Content extraction with anti-bot handling and poison pill detection |
| [zero-build-frontend](./zero-build-frontend/) | Static web apps without build tools, CDN-loaded frameworks |

### Security (ship without getting sued)

| Skill | Description |
|-------|-------------|
| [security-checklist](./security-checklist/) | Pre-deployment security audit covering auth, input validation, secrets, and compliance |
| [secure-auth](./secure-auth/) | Production-ready authentication patterns (sessions, JWTs, OAuth, MFA) |
| [api-hardening](./api-hardening/) | Rate limiting, input validation, CORS, API key management |

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

- [Anthropic official skills](https://github.com/anthropics/skills)
- [Claude Code documentation](https://docs.anthropic.com/claude-code)
- [Agent Skills Standard](http://agentskills.io)
- [NICAR (Investigative Reporters & Editors)](https://www.ire.org/nicar/)
- [First Draft News](https://firstdraftnews.org/)
- [Verification Handbook](https://verificationhandbook.com/)

## License

MIT License - See [LICENSE](./LICENSE) for details.

## Author

Joe Amditis ([@jamditis](https://github.com/jamditis))

---

*Built with Claude Code*
