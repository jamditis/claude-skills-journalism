---
name: autocontext-skill-lesson-injector
description: Inject global skill lessons when a skill is loaded
hooks:
  - event: PreToolUse
    type: prompt
    matcher: "Skill"
---

Check if skill learning is enabled. Read the config with this fallback chain:
1. `.autocontext/config.json` -> `skill_learning.enabled`
2. `~/.claude/autocontext.json` -> `skill_learning.enabled`
3. Default: `false`

If disabled, do nothing.

If enabled, extract the skill name from `tool_input.skill`. Then check if `~/.claude/skill-lessons/<skill-name>.json` exists.

If the file exists, read it and find lessons where `folded` is `false`. If there are un-folded lessons, inject them as a brief note:

```
Note: The following patterns have been learned from real usage of this skill:
- [lesson text] (confidence: [score], from: [comma-separated source_projects])
```

Cap at 5 lessons, sorted by confidence descending. If no un-folded lessons exist, do nothing.

The global store path defaults to `~/.claude/skill-lessons/` but can be overridden by `skill_learning.global_store` in config.
