# hooks

17 standalone workflow hooks under `hooks/`. Most are non-blocking warnings; `one-way-door-check` and `no-ai-attribution` block until resolved. `prose-question-guard` blocks a stop once to move a prose question into `AskUserQuestion`. See [the hooks catalog](../systems/hooks-catalog.md) for how they install and fire.

## Writing quality
- [accessibility-check](accessibility-check.md)
- [ai-slop-detector](ai-slop-detector.md)
- [ap-style-check](ap-style-check.md)
- [copywriting-preflight](copywriting-preflight.md)

## Verification
- [data-methodology-check](data-methodology-check.md)
- [source-attribution-check](source-attribution-check.md)
- [verification-reminder](verification-reminder.md)

## Editorial workflow
- [deadline-tracker](deadline-tracker.md)
- [legal-review-flag](legal-review-flag.md)
- [pre-publish-checklist](pre-publish-checklist.md)
- [source-diversity-check](source-diversity-check.md)

## Preservation
- [archive-reminder](archive-reminder.md)

## Interaction
- [prose-question-guard](prose-question-guard.md)

## Development
- [bug-report-detector](bug-report-detector.md)
- [no-ai-attribution](no-ai-attribution.md)
- [one-way-door-check](one-way-door-check.md)
- [pre-commit-review](pre-commit-review.md)
