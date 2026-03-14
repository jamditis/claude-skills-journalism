# Skill evolution: self-improving skills via autocontext

**Date:** 2026-03-14
**Status:** Approved
**Approach:** B — capture in autocontext, evolve separately

## Summary

Extend the autocontext plugin so that lessons captured during skill usage are tagged with the active skill name, accumulated in a global skill lesson store, and eventually folded into the skill's actual .md file content via a new `/autocontext-evolve` command. Skills literally get better each time they're used and corrected.

## Problem

Skills in claude-skills-journalism are static markdown files. When Claude is corrected while using a skill, that correction becomes a project-local autocontext lesson — but the skill itself never improves. The same correction may need to happen again in a different project, or by a different user. There's no feedback loop from usage back to the skill content.

## Design principles

1. **Opt-in** — existing autocontext users get zero overhead unless they enable `skill_learning` in config
2. **Evidence-based evolution** — skills only change when lessons have high confidence and multiple validations
3. **Human-in-the-loop** — all skill file edits require explicit user approval via diff review
4. **Minimal autocontext changes** — the core capture/curate/validate loop stays intact; evolution is a separate module
5. **Local-first** — global skill lessons live on each machine independently, with optional export/import for sharing

## Architecture overview

### Session ID and skill tracking mechanism

Claude Code hooks receive JSON input via stdin. The `session_id` field is present in all hook event payloads. PostToolUse hooks for the Skill tool receive `tool_input.skill` containing the skill name.

A new `hooks/track-active-skill.sh` PostToolUse hook (matched on `Skill`) extracts `session_id` and `tool_input.skill` from the JSON input and appends the skill name to `/tmp/claude-skills-{session_id}`. This file accumulates all skills loaded during the session.

The `session-end.sh` hook cleans up `/tmp/claude-skills-{session_id}` to prevent temp file accumulation.

```
 CAPTURE (during normal work)
 ───────────────────────────
 User invokes skill (e.g., web-scraping)
     -> PostToolUse(Skill) fires
     -> track-active-skill.sh reads JSON stdin:
        { "tool_input": { "skill": "web-scraping" }, "session_id": "abc-123" }
     -> appends "web-scraping" to /tmp/claude-skills-abc-123

 User corrects Claude: "no, use Selenium for this"
     -> user-prompt-submit.sh detects correction
     -> reads session_id from JSON stdin
     -> reads /tmp/claude-skills-{session_id} -> finds "web-scraping"
     -> appends to .autocontext/cache/pending-lessons.json:
       { message: "...", active_skills: ["web-scraping"] }

 CURATE (next session start)
 ──────────────────────────
 session-start.sh phase 1:
     -> curator processes pending lessons
     -> outputs: { text: "...", skill: "web-scraping", scope: "project" }
     -> persists to .autocontext/lessons.json with skill + scope fields

 VALIDATE (ongoing)
 ─────────────────
 session-end.sh:
     -> loaded lessons that weren't contradicted get +0.1 confidence
     -> skill-tagged lessons validated same as any other

 PROMOTE (during review)
 ──────────────────────
 User runs /autocontext-review:
     -> sees skill-tagged lesson at high confidence
     -> selects "Promote to global"
     -> lesson copied to ~/.claude/skill-lessons/<skill>.json
     -> scope changed to "skill" in project lessons.json

 EVOLVE (on demand)
 ─────────────────
 User runs /autocontext-evolve:
     -> scans ~/.claude/skill-lessons/ for eligible lessons
     -> "web-scraping: 5 lessons ready (avg confidence 0.91)"
     -> user selects skill to evolve
     -> claude -p generates improved SKILL.md
     -> user reviews diff -> accepts/rejects/edits/appends
     -> SKILL.md updated, lessons marked as folded

 LOAD (future sessions)
 ─────────────────────
 When any project loads a skill:
     -> pre-tool-use hook checks ~/.claude/skill-lessons/<skill>.json
     -> injects any un-folded global lessons alongside the skill
     -> (folded lessons are already in the skill content itself)
```

## Component 1: Skill-aware lesson capture

### New hook: `hooks/track-active-skill.sh`

A new PostToolUse hook matched on the `Skill` tool. When Claude loads a skill via the Skill tool, this hook fires and:

1. Reads JSON from stdin, extracts `tool_input.skill` (the skill name) and `session_id`
2. Checks if the file `/tmp/claude-skills-{session_id}` exists; creates it if not
3. Appends the skill name if not already present (dedup via `grep -qxF`)

This file is the bridge between skill invocations and lesson tagging. It's read by `user-prompt-submit.sh` and cleaned up by `session-end.sh`.

**Hook registration in `plugin.json`:**

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Skill",
      "hooks": [{ "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/autocontext/hooks/track-active-skill.sh" }]
    }]
  }
}
```

### Changes to `hooks/user-prompt-submit.sh`

When a correction is detected, the hook currently writes to `pending-lessons.json` with the user's message and timestamp. New behavior: read `session_id` from the JSON stdin payload, then read `/tmp/claude-skills-{session_id}` (populated by the new `track-active-skill.sh` hook above) and add active skill names to the pending lesson metadata.

Pending lesson format gains a new field:

```json
{
  "user_message": "no, use Selenium not requests for this site",
  "timestamp": "2026-03-14T15:30:00Z",
  "active_skills": ["web-scraping"],
  "session_id": "abc-123"
}
```

If no skills are active, `active_skills` is an empty array — the lesson is project-only, same as today.

### Changes to `hooks/session-start.sh` curator phase

The curator's prompt gets an additional instruction: "If the lesson is tagged with a skill, include a `skill` field in the output. If the lesson is specific to this project, set `scope: 'project'`. If it's useful across any project using this skill, set `scope: 'skill'`."

Curated lesson in `lessons.json` gains two new optional fields:

```json
{
  "id": "lesson_x1y2z3",
  "text": "News sites with JavaScript paywalls need Selenium, not requests",
  "skill": "web-scraping",
  "scope": "project",
  "confidence": 0.7,
  "...existing fields..."
}
```

### New hook: `hooks/skill-lesson-injector.md`

A new PreToolUse prompt-based hook matched on `Skill`. This is separate from the existing `pre-tool-use.md` (which matches `Edit|Write|Bash`) to avoid complicating the existing hook's file-path-oriented logic.

When the Skill tool is about to fire:

1. Extract the skill name from `tool_input.skill`
2. Check `~/.claude/skill-lessons/<skill>.json` for un-folded global lessons
3. If lessons exist with `folded: false`, inject them as additional context alongside the skill content

Injection format:

```
Note: The following patterns have been learned from real usage of this skill:
- [lesson text] (confidence: 0.92, from: rosen-frontend, reroute-nj)
- [lesson text] (confidence: 0.88, from: reroute-nj)
```

This hook only fires when `skill_learning.enabled` is true in the nearest `.autocontext/config.json` or `~/.claude/autocontext.json`.

### Changes to `hooks/session-end.sh`

No structural changes. Skill-tagged lessons are validated identically to other lessons — confidence bumps on unchallenged usage, no bump on contradiction.

### Changes to `commands/review.md`

When reviewing a skill-tagged lesson, add a new action: **"Promote to global"**. This copies the lesson to `~/.claude/skill-lessons/<skill>.json` with `scope: "skill"` and updates the original in the project's `lessons.json`.

### Config additions

New section in `.autocontext/config.json`:

```json
{
  "skill_learning": {
    "enabled": false,
    "scope": "all",
    "confidence_for_promotion": 0.85,
    "global_store": "~/.claude/skill-lessons/"
  }
}
```

- `enabled` — master toggle, defaults to `false` for existing users
- `scope` — `"all"` (track all skills) or an array like `["web-scraping", "data-journalism"]`
- `confidence_for_promotion` — minimum confidence before a lesson is eligible for promotion or evolution
- `global_store` — path to global skill lesson directory

### Changes to `/autocontext-setup`

Two new steps added to the wizard:

**Step 11: Skill learning**
> "Do you want autocontext to track which skills are active when corrections happen? This lets lessons accumulate per-skill and eventually improve the skill files themselves."
> Options: Yes (recommended) / No / Only specific skills

**Step 12: Evolution settings**
> "When running /autocontext-evolve, how aggressive should the evolution be?"
> Options:
> - Conservative (confidence >= 0.9, 5+ validations) — only proven lessons
> - Moderate (confidence >= 0.85, 3+ validations) — recommended
> - Aggressive (confidence >= 0.7, 2+ validations) — faster evolution, more risk

## Component 2: Global skill lesson store

### Directory structure

```
~/.claude/skill-lessons/
├── index.json                    # Registry of all skill lesson files
├── web-scraping.json             # Lessons for the web-scraping skill
├── data-journalism.json
├── security-checklist.json
├── backups/                      # Pre-evolution backups of skill files
│   └── web-scraping-2026-03-14T15:00:00Z.md
└── exports/                      # For cross-machine sync
    └── 2026-03-14-export.json
```

### `index.json` schema

```json
{
  "skills": {
    "web-scraping": {
      "lesson_count": 12,
      "last_evolved": "2026-03-10T14:00:00Z",
      "skill_path": "/path/to/web-scraping/SKILL.md",
      "evolution_count": 3
    }
  },
  "created": "2026-03-14T15:00:00Z",
  "schema_version": 1
}
```

### Per-skill lesson file schema

```json
{
  "skill": "web-scraping",
  "lessons": [
    {
      "id": "skill_lesson_a1b2",
      "text": "News sites with JS paywalls need Selenium, not requests",
      "confidence": 0.92,
      "validated_count": 8,
      "source_projects": ["rosen-frontend", "reroute-nj"],
      "promoted_from": "lesson_x1y2z3",
      "created": "2026-03-01T10:30:00Z",
      "last_validated": "2026-03-13T14:00:00Z",
      "folded": false
    }
  ],
  "schema_version": 1
}
```

- `source_projects` — tracks which projects contributed this lesson
- `promoted_from` — ID of the project-level lesson this was promoted from
- `folded` — true once the lesson has been integrated into the skill file via evolution

## Component 3: Evolution engine

### New command: `/autocontext-evolve`

Entry point: `commands/evolve.md`
Engine: `scripts/skill-evolution/`

The command accepts optional arguments parsed from the user's slash command input. Claude Code passes the full argument string after the command name to the command's markdown prompt, which instructs Claude to interpret it:

- `/autocontext-evolve` — default mode: scan, present, and evolve skills interactively
- `/autocontext-evolve --rollback <skill>` — restore a skill from its most recent backup
- `/autocontext-evolve --export` — export global lessons to a JSON file
- `/autocontext-evolve --import <path>` — import lessons from an export file

The `evolve.md` command prompt includes instructions for Claude to parse these arguments from the user's input and route to the appropriate action. No separate command registrations needed — the single command handles all modes via argument parsing within the markdown prompt.

### Command flow (default mode)

1. **Scan** — read `~/.claude/skill-lessons/` for skills with eligible lessons (confidence >= threshold, validated_count >= min, folded == false)
2. **Present** — show summary per skill: lesson count, average confidence, source projects
3. **Select** — user picks which skill(s) to evolve, or skips
4. **Generate** — for each selected skill:
   a. Read current skill .md file content
   b. Read all eligible lessons for that skill
   c. Shell out to `claude -p` with the evolution prompt (see below)
   d. Receive full updated skill content
5. **Review** — present diff to user with four options:
   - **Accept** — write updated content to skill .md file
   - **Edit** — user makes manual adjustments, then write
   - **Reject** — skip this skill, lessons stay in the store
   - **Append** — fall back to adding a `## Learned patterns` section at the bottom
6. **Cleanup** — mark evolved lessons as `folded: true`, update `index.json`, back up the original skill file

### Evolution prompt

```
You are improving a Claude Code skill based on validated lessons
learned from real usage. The skill's current content and the lessons
are provided below.

RULES:
- Integrate lessons naturally into the existing content
- Don't create a separate "lessons" section — weave guidance
  into the flow where it belongs
- Preserve the skill's existing structure, voice, and formatting
- Higher-confidence lessons should be treated as more authoritative
- If a lesson contradicts existing guidance, the lesson wins
  (it's from real usage)
- Don't add preamble or meta-commentary
- Output the complete updated skill content, nothing else

CURRENT SKILL CONTENT:
<skill>
{full skill .md content}
</skill>

LESSONS TO INTEGRATE (sorted by confidence):
<lessons>
{each lesson with confidence score and source projects}
</lessons>
```

### Append fallback format

```markdown
## Learned patterns

<!-- Auto-generated by autocontext skill evolution. Do not edit manually. -->

- **[0.92]** News sites with JS paywalls need Selenium, not requests
  _Sources: rosen-frontend, reroute-nj_

- **[0.88]** Always set User-Agent to a real browser string
  _Sources: reroute-nj_
```

On the next `/autocontext-evolve` run, the command can re-attempt to integrate these naturally.

### Safety guardrails

1. **Backup before edit** — copy original to `~/.claude/skill-lessons/backups/<skill>-<timestamp>.md`
2. **Minimum evidence threshold** — configurable, defaults to confidence >= 0.85 AND validated_count >= 3
3. **Diff review is mandatory** — no silent edits, user always sees what's changing
4. **Rollback** — `/autocontext-evolve --rollback <skill>` restores from most recent backup

### Consolidated config schema

The `skill_learning` section in `.autocontext/config.json` is the single source of truth for all skill evolution settings. The full schema (replacing the partial version shown in Component 1):

```json
{
  "skill_learning": {
    "enabled": false,
    "scope": "all",
    "global_store": "~/.claude/skill-lessons/",
    "confidence_for_promotion": 0.85,
    "evolution_confidence": 0.85,
    "evolution_min_validations": 3,
    "backup_dir": "~/.claude/skill-lessons/backups/",
    "evolution_model": "claude -p"
  }
}
```

The global config `~/.claude/autocontext.json` also gains this section as a default. Per-project config overrides global, same as existing autocontext settings.

## Component 4: Sync mechanism

### Export

`/autocontext-evolve --export`

Writes all global skill lessons to `~/.claude/skill-lessons/exports/<date>-export.json`. This file can be committed to the plugin repo, shared via Drive, or copied via scp.

### Import

`/autocontext-evolve --import <path>`

Reads an export file and merges into the local global store using the same union merge logic as autocontext's merge-driver.py:
- Additive `validated_count`
- Highest `confidence` wins
- Newest `last_validated` timestamp wins
- New lessons (by ID) are added
- `folded` state preserved (if folded on either side, stays folded)

Reports what was added/updated after merge.

## Files changed (complete list)

| File | Change | Description |
|------|--------|-------------|
| `hooks/track-active-skill.sh` | **New** | PostToolUse(Skill) hook: write active skill name to /tmp/claude-skills-{session_id} |
| `hooks/skill-lesson-injector.md` | **New** | PreToolUse(Skill) hook: inject global lessons when a skill loads |
| `hooks/user-prompt-submit.sh` | Modify | Read session_id from stdin JSON, read active skills from /tmp, add to pending lessons |
| `hooks/session-start.sh` | Modify | Curator prompt includes skill field; global config inherits skill_learning |
| `hooks/session-end.sh` | Modify | Validate skill-tagged lessons; clean up /tmp/claude-skills-{session_id} |
| `commands/review.md` | Modify | Add "Promote to global" action for skill-tagged lessons |
| `commands/setup.md` | Modify | Add steps 11-12 for skill learning config |
| `commands/evolve.md` | **New** | The /autocontext-evolve command (handles evolve, rollback, export, import via args) |
| `scripts/skill-evolution/evolve.sh` | **New** | Evolution engine entry point |
| `scripts/skill-evolution/generate-diff.py` | **New** | Claude-powered skill rewriting |
| `scripts/skill-evolution/apply-edit.py` | **New** | Write approved changes + backup |
| `scripts/skill-evolution/sync.py` | **New** | Export/import for cross-machine sharing |
| `plugin.json` | Modify | Register /autocontext-evolve command + track-active-skill + skill-lesson-injector hooks |

## Testing strategy

1. **Unit tests for tagging** — verify user-prompt-submit correctly reads skill names and tags pending lessons
2. **Unit tests for promotion** — verify lessons are correctly copied to global store with proper metadata
3. **Integration test for evolution** — set up a test skill with known content, add mock lessons, run evolution, verify diff output
4. **Rollback test** — verify backup is created before edit and `/autocontext-evolve --rollback` restores correctly
5. **Sync round-trip** — export from machine A, import on machine B, verify union merge semantics
6. **Backward compatibility** — verify autocontext works identically when `skill_learning.enabled` is false (default)

## Resolved design decisions

1. **Skill path resolution** — at evolve time, the engine resolves skill paths dynamically by searching `CLAUDE_PLUGIN_ROOT` directories and the plugin cache (`~/.claude/plugins/`) for the skill name. The `index.json` `skill_path` is a hint/cache, not authoritative. If the path is stale (file doesn't exist), the engine searches for the skill and updates `index.json`. If the skill can't be found, the evolution is skipped with a warning.

2. **Multi-skill corrections** — if multiple skills are active during a correction, all are tagged in `active_skills`. The curator decides which skill(s) the lesson applies to based on the lesson's content. A lesson about Selenium belongs to `web-scraping` even if `data-journalism` was also active.

3. **Version conflicts** — if the plugin repo updates a skill upstream, the user's local evolutions are overwritten. The backup system at `~/.claude/skill-lessons/backups/` preserves the evolved version. Users can re-apply evolutions after an upstream update by running `/autocontext-evolve` again — the un-folded lessons are still in the global store and will generate a new diff against the updated skill content. This is acceptable because evolved skills should eventually feed improvements back upstream via PRs.

## Future considerations

- A merge strategy for upstream updates (auto-reapply evolved patterns to new upstream content)
- Collaborative curation UI beyond the CLI
- Cross-user lesson sharing (plugin marketplace-level evolution)
