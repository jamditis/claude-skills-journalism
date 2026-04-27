---
description: Interactively review and curate accumulated project lessons
---

Review accumulated lessons in `.autocontext/lessons.json`. Use AskUserQuestion to walk through lessons.

## Initialization

The script first reads `.autocontext/lessons.json` and separates lessons into two groups:
- **Active lessons** — `deleted: false` or not marked deleted
- **Tombstoned lessons** — `deleted: true` (lessons that were intentionally removed)

If `.autocontext/cache/curated-pending.json` exists (from previous curation sessions with pending items), those are presented first for final approval.

## Review order

Active lessons are sorted by **confidence score (lowest first)**. Low-confidence lessons need the most attention — these are either new, frequently contradicted, or validated by few developers.

## Lesson presentation

Lessons are presented in batches of 3-4 using AskUserQuestion. For each lesson, the review shows:

- **Text** — the lesson content
- **Category** — lesson type (bug-fix, architecture, workflow, pattern, gotcha, etc.)
- **Confidence** — current score (0.0 to 1.0)
- **Validated count** — how many sessions/developers have confirmed it
- **Created by** — which developer/session discovered it
- **Age** — how long ago it was created

Example format:
```
Lesson: "Always run git pull before pushing to main"
Category: workflow
Confidence: 0.9 | Validated: 12 times | Created by: alice | Age: 45 days
```

## Review actions

For each lesson, you choose one action:

**Options:**
- Approve — increase confidence by +0.2 (confirms lesson is valuable)
- Edit — modify lesson text, category, or tags
- Delete — tombstone the lesson (marks as `deleted: true`)
- Supersede — replace this lesson with a newer/better version
- Skip — leave unchanged and move to next

### Approve
Bumps confidence by 0.2. Use this when you confirm a lesson is still valid and useful.

### Edit
Opens the lesson for modification. You can update:
- Lesson text (the knowledge itself)
- Category (bug-fix, architecture, workflow, pattern, gotcha, integration, test-strategy)
- Tags (optional metadata)

Edited lessons are automatically marked as reviewed by you.

### Delete
Marks the lesson as tombstoned (`deleted: true`). The original content is preserved in `.autocontext/archive/superseded.json` for historical reference, but the lesson won't load during future sessions.

Use this for lessons that are outdated, wrong, or no longer relevant.

### Supersede
Replace the current lesson with a completely new version. You provide the new lesson text. The old lesson is tombstoned and the new one is added as a fresh, high-confidence lesson.

Use this when a lesson is correct in spirit but the specific guidance has changed (e.g., "Use React class components" → "Use React functional components with hooks").

### Skip
Leaves the lesson unchanged and moves to the next one. Use this when you're not sure or want to review later.

### Promote to global (skill-tagged lessons only)

When a lesson has a `skill` field (non-null) and `skill_learning.enabled` is true in config, a sixth action is available:

- **Promote to global** — Copy this lesson to the global skill lesson store using the store module. Update the original lesson's `scope` to `"skill"` in `lessons.json`. Report: "Promoted to global store for [skill name]."

The global store path comes from config: `skill_learning.global_store` (default `~/.claude/skill-lessons/`).

To perform the promotion, run:

```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts/skill-evolution')
from store import promote_lesson, ensure_store
import json

ensure_store()
lesson = json.loads('''LESSON_JSON_HERE''')
result = promote_lesson(lesson, 'SKILL_NAME_HERE', 'PROJECT_NAME_HERE')
print('promoted' if result else 'already_exists')
"
```

Only show this action when `skill_learning.enabled` is true in config and the lesson has a non-null `skill` field.

## Tombstoned lessons

After reviewing all active lessons, you'll be asked about any tombstoned lessons:

**Question:** There are N tombstoned lessons. What would you like to do?

**Options:**
- Remove all tombstones permanently — deletes archived lessons (cannot be undone)
- Let me review them individually — presents each tombstone for potential restoration or permanent removal
- Keep them — preserves tombstones for historical reference

If you choose to review individually, each tombstoned lesson is presented with options to:
- Restore — mark as `deleted: false` and add back to active lessons
- Permanently remove — delete from archive (cannot be undone)
- Skip — leave in archive

## Playbook regeneration

After all reviews are complete, the script automatically regenerates `.autocontext/playbook.md` using:
```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/generate-playbook.py .autocontext/lessons.json .autocontext/playbook.md
```

The playbook reflects your curated lessons and is the human-readable summary of project knowledge.

## Review summary

At the end, you'll see a report:

```
Review complete:
- N lessons reviewed
- M lessons approved (confidence increased)
- K lessons deleted (tombstoned)
- J lessons edited
- Playbook regenerated with X active lessons
```

This summary confirms what changed and gives you confidence that the curation was applied.

## Tips

- **Low-confidence lessons first** — the review order (lowest confidence first) helps you focus on lessons that need validation
- **Be liberal with approval** — if a lesson is still correct, approve it. This builds signal about what's truly useful.
- **Supersede instead of delete** — if a lesson is mostly right but needs an update, supersede it rather than deleting. This preserves the learning path.
- **Regular curation** — run `/autocontext:review` weekly or after major changes to keep lessons fresh and accurate
