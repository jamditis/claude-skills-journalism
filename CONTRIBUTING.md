# Contributing

Thanks for your interest in contributing to this skill collection. Whether you're fixing a bug, improving an existing skill, or proposing a new one, this guide will help you get started.

## Quick start

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/claude-skills-journalism.git`
3. Create a branch: `git checkout -b my-skill-or-fix`
4. Make your changes
5. Test with Claude Code locally
6. Submit a pull request

## Adding a new skill

### Directory structure

Each skill lives in its own directory at the repo root:

```
skill-name/
├── SKILL.md          # Main instructions (required)
├── templates/        # Reusable templates (optional)
├── examples/         # Example inputs/outputs (optional)
└── scripts/          # Helper scripts (optional)
```

### SKILL.md format

Every skill needs a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: skill-name
description: When to use this skill and what it does
---

# Skill title

Instructions, workflows, and knowledge for Claude to use.
```

The `description` field is what Claude uses to decide when to activate the skill, so make it specific about trigger conditions.

### Skill guidelines

- **Focus area:** journalism, media, communications, academic, or technical workflows that support those fields
- **Actionable content:** include workflows and decision trees, not just reference info
- **Templates:** provide templates where applicable — they make skills immediately useful
- **Sources:** cite standards, style guides, or verification methods you reference
- **Sentence case:** use sentence case for all headings, not title case
- **No AI slop:** avoid the banned words and patterns listed in the [ai-writing-detox](./ai-writing-detox/) skill

### Testing your skill

Before submitting:

1. Install the skill locally: `cp -r your-skill/ ~/.claude/skills/`
2. Start a Claude Code session
3. Give it a prompt that should trigger the skill
4. Verify it activates and produces useful output
5. Test edge cases and different prompt phrasings

## Adding a hook

Hooks are single markdown files in the `hooks/` directory. Each hook has frontmatter specifying when it runs:

```yaml
---
name: hook-name
description: What this hook checks
event: PostToolUse | PreToolUse | UserPromptSubmit | Stop | SessionStart
tools: [Write, Edit]  # for Pre/PostToolUse hooks
---

Hook instructions here.
```

All hooks should be **non-blocking warnings** — they provide guidance but don't prevent actions.

## Improving existing skills

Improvements to existing skills are welcome. Common areas:

- Adding templates for new use cases
- Expanding workflows with missing steps
- Fixing outdated references or broken links
- Adding examples that demonstrate the skill in action

## Reporting bugs

Use the [bug report template](https://github.com/jamditis/claude-skills-journalism/issues/new?template=bug_report.yml) to file issues. Include your Claude Code version (`claude --version`) and steps to reproduce.

## Proposing new skills

Use the [skill request template](https://github.com/jamditis/claude-skills-journalism/issues/new?template=skill_request.yml) to propose ideas. Describe the target audience, key workflows, and any reference materials.

## Style guide

- Sentence case for all headings
- Keep descriptions short and direct
- Avoid AI writing patterns (see [ai-writing-detox](./ai-writing-detox/))
- Include actionable steps, not just theory
- Cite your sources

## Code of conduct

This project follows the [Contributor Covenant](./CODE_OF_CONDUCT.md). Be respectful and constructive.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](./LICENSE).
