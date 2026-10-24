# project-templates-toolkit

Four skills for setting up, tracking, and closing out journalism projects, the institutional-knowledge layer that survives staff turnover, sabbaticals, and the natural decay of "everyone just knows that."

## Skills in this plugin

| Skill | What it covers |
|---|---|
| goal-progress-bar | Script-rendered weighted progress for multi-step work, updated from recorded evidence. Nobody types or adjusts the percentage by hand. |
| project-memory | Project instruction generation that captures institutional knowledge, the things obvious to current team members but invisible to a new collaborator. Templates cover editorial tools, event websites, publications, research projects, content pipelines, and digital archives. |
| project-retrospective | LESSONS.md generation that names specific failures and the decisions that caused them. Templates for research projects, event post-mortems, editorial tools, and publications. |
| template-selector | Decision tree that picks the right starting template across project-memory and project-retrospective. Use when starting a new project or unsure which template category fits. |

## Client support

All four skills use client-neutral instructions. `project-memory` resolves
the canonical project instruction file and keeps paired merge, nested-scope,
trigger, and non-trigger fixtures for Claude Code and Codex. Runtime evidence is
still required before the package classification can change.

## Installation

```
/plugin marketplace add jamditis/claude-skills-journalism
/plugin install project-templates-toolkit@claude-skills-journalism
```

## See also

- [`dev-toolkit`](../dev-toolkit/README.md), 14 development skills (accessibility, Electron, scraping, frontend patterns, minimal-code implementation, UI completeness, project instruction maintenance)
- [`journalism-core`](../journalism-core/README.md), 16 skills for reporting, verification, publishing
- [`research-toolkit`](../research-toolkit/README.md), 6 skills for research, archives, academic workflows
- [`security-toolkit`](../security-toolkit/README.md), 3 defensive security skills for web apps and APIs
