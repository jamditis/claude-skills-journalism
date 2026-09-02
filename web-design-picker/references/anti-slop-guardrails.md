# Anti-slop guardrails

Use this as a review checklist, not a rigid style ban. A pattern can be valid when the subject, content, and interaction justify it. The failure mode is defaulting to the pattern because it is easy or currently fashionable.

## Supplied design tells

- Leading zeroes before section numbers such as 01, 02, 03.
- Tiny low-contrast subtext.
- Fake depth with a box behind another box for no functional reason.
- Tan sites dominated by oversized calls to action.
- The same stock “editorial” serif used in generic AI layouts.
- A small explanatory line above every headline.
- Bento grids.
- A random italic word in a headline.
- Gradient blobs in the background.
- A genre-claim pill with a glowing dot above the main CTA.
- Random colored left edges on blocks, buttons, or cards.
- Eyebrows formatted as a dash plus text.
- Rounded cards with a colored top or side rule.
- Eyebrows formatted as chips with dots.
- Self-justifying subheads only the creator understands.
- Inconsistent light/dark mode behavior.
- Defaulting to Geist Mono.
- Purple gradients or gradient overuse.
- Excessive glassmorphism.
- Colors used without semantic logic.
- Verbose sections that do not help the user decide.
- Random sliding text carousels.
- Incorrect strokes around rounded boxes.
- Defaulting to Inter for everything.
- Pulsing dots in lists.
- Generic startup-SaaS styling for unrelated organizations.
- Oversized custom cursors.
- Scroll-triggered reveal effects.
- Pill-shaped everything.
- Defaulting to Space Grotesk.
- Contact buttons that only open an email client while pretending to be a form.
- Purple-heavy pages with no real form.
- One undifferentiated scroll sequence with no meaningful sections.
- Newsletter forms that exist only because a template included one.
- Underlining the random italicized word in a headline.

Original list updated August 25, 2026.

## Review method

For every flagged pattern, ask:

1. What user, content, or brand need does this solve?
2. Would the page still communicate its idea without it?
3. Is it repeated because it is part of a coherent system or because the template repeats it?
4. Does it make the subject feel more specific or more like a generic startup?
5. Is there a less familiar but clearer solution?

## Stronger alternatives

- Replace decorative eyebrows with direct headings or meaningful metadata.
- Replace rounded card grids with editorial rows, diagrams, tables, spatial groupings, or full-width sections.
- Replace gradient atmosphere with a deliberate palette, texture, photography, drawing, or negative space.
- Replace reveal animation with state change, comparison, layer toggles, or no animation.
- Replace stock font pairings with type chosen for the organization’s actual voice and licensing context.
- Replace generic “learn more” CTAs with a concrete next action.
- Replace a mailto CTA with a real intake flow or an honest downloadable project brief.
- Replace vague claims with inputs, outputs, process, evidence, or constraints.

## Automated lint limitations

`scripts/slop_lint.py` uses string and CSS heuristics. It will produce false positives and cannot judge whether a pattern is justified. Use it to force a review, not to outsource design judgment.
