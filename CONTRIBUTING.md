# Contributing

Thanks for your interest in contributing to this skill collection. Whether you're fixing a bug, improving an existing skill, or proposing a new one, this guide will help you get started.

## Quick start

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/claude-skills-journalism.git`
3. Create a branch: `git checkout -b my-skill-or-fix`
4. Make your changes
5. Test with Claude Code and Codex locally
6. Submit a pull request

## Dot workflows and field notes

The [dot workshop](https://skills.amditis.tech/dot-skills/) is deliberately separate from the stable Claude Code and Codex skill catalog. It combines practical workflows, an early community sharing experiment, and first-person accounts of failures. Read [DOT-SKILLS.md](./DOT-SKILLS.md) for the available playbooks, contribution format, permission-record template, and validation boundaries.

Keep this section whimsical, bouncy, quirky, and fun. Do not replace its pixel helpers and paper workshop with the main docs theme. Keep the prose concrete: explain what someone was trying to do, what happened, what helped, and what remains broken. A stranger should not have to read old PRs to understand the example.

A dot contribution needs readable instructions, a worked example, required inputs/tools, approval scope, known failure cases, and an honest validation record. Use fictional or cleared/redacted data. The current Markdown playbooks are not native dot installers or stable catalog entries. Do not apply the stable-skill installation claims below to them. Test the local pages and demo, and distinguish those results from actual dot/connector tests. See [the scoped instructions](./docs/dot-skills/AGENTS.md).

## Adding a new skill

### Directory structure

Each skill lives in its own directory. Most skills are nested under a package:

```
package/skills/skill-name/
├── SKILL.md          # Main instructions (required)
├── agents/
│   └── openai.yaml      # Codex interface metadata (required)
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

Instructions, workflows, and knowledge for supported coding agents to use.
```

The `description` field helps supported clients decide when to activate the skill, so make it specific about trigger conditions.

### Skill guidelines

- **Focus area:** journalism, media, communications, academic, or technical workflows that support those fields
- **Actionable content:** include workflows and decision trees, not just reference info
- **Templates:** provide templates where applicable, they make skills immediately useful
- **Sources:** cite standards, style guides, or verification methods you reference
- **Sentence case:** use sentence case for all headings, not title case
- **No AI slop:** avoid the banned words and patterns listed in the [ai-writing-detox](./journalism-core/skills/ai-writing-detox/) skill

### Testing your skill

Before submitting:

1. Add or update `SKILL.md` and `agents/openai.yaml`.
2. Add the skill to `skills-catalog.yaml`, the package README, and the root README.
3. Add or update the matching `docs/<skill-name>/index.html` page.
4. Install it: `mkdir -p ~/.claude/skills <project>/.agents/skills`, then `cp -r your-skill/ ~/.claude/skills/` (Claude Code) and `cp -r your-skill/ <project>/.agents/skills` (Codex). Start a session in each.
5. Verify expected activation, unrelated non-activation, resource access, and useful output in both clients.
6. Test edge cases and different prompt phrasings.
7. Run the repository validation commands documented in `AGENTS.md`.

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

Most hooks are **non-blocking warnings**. `one-way-door-check` and `no-ai-attribution` block intentionally. Each hook documents its behavior.

## Improving existing skills

Improvements to existing skills are welcome. Common areas:

- Adding templates for new use cases
- Expanding workflows with missing steps
- Fixing outdated references or broken links
- Adding examples that demonstrate the skill in action

## Reporting bugs

Use the [bug report template](https://github.com/jamditis/claude-skills-journalism/issues/new?template=bug_report.yml) to file issues. Include your Claude Code version (`claude --version`) and steps to reproduce. For dot reports, name the surface and observed date, the intended task, the exact failure, and the validation limits; do not invent a model or backend version you cannot inspect.

## Proposing new skills

Use the [skill request template](https://github.com/jamditis/claude-skills-journalism/issues/new?template=skill_request.yml) to propose ideas. Describe the target audience, key workflows, and any reference materials.

## Style guide

- Sentence case for all headings
- Keep descriptions short and direct
- Avoid AI writing patterns (see [ai-writing-detox](./journalism-core/skills/ai-writing-detox/))
- Include actionable steps, not just theory
- Cite your sources

## Code of conduct

This project follows the [Contributor Covenant](./CODE_OF_CONDUCT.md). Be respectful and constructive.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](./LICENSE).
