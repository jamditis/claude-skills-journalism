# Dot workshop instructions

This directory is an intentional visual exception to the main documentation. Read the repository's `AGENTS.md` and `DOT-SKILLS.md` as well.

## Preserve the character

Keep the whimsical, bouncy, quirky workshop: warm paper, pixel helpers, off-kilter notes, tactile cards, and expressive animations (a few gentle loops, such as blinking or a dozing helper, are welcome; keep big movements finite). Do not normalize it into the main site's restrained docs theme or a generic software landing page. Use sentence case. Give mouse and keyboard users equivalent useful controls. Respect the OS reduced-motion preference and a persistent manual pause; the static version must remain readable and functional.

## Preserve the point

This is a useful skill library, an early community sharing experiment, and a candid account of dot failures. Explain a task and its context before an issue number, private workflow name, or technical shortcut. Write firsthand accounts as firsthand accounts. Keep the actual frustration: repeated permissions, browser crashes, lost sign-ins, unreliable scheduled jobs, unwanted initiative, and missing diagnostic visibility. Do not soften those into generic praise or blame every failure on the user's configuration.

Separate observed behavior, documented product claims, inference, and unknown causes. Verify changing product/usage claims against primary sources. A successful workaround is not a product fix. The Activity view is not the same claim as a full diagnostic trace. Do not imply access to private internal reasoning.

## Keep useful boundaries

Reuse current, applicable standing authorization rather than repeatedly requesting it. Do not evade a real denial. Name a routing restriction, missing access, expired sign-in, review error, or uncertain delivery accurately. Do not publish placeholders, duplicates, or diagnostic messages when one edited post was requested. Preserve the last-good state and failed-check evidence.

Public examples must use fictional or explicitly cleared/redacted data. Do not commit private Slack screenshots or identifiers. The current playbooks are Markdown previews, not native dot plugins or stable entries in the main skills catalog. Do not claim installation, scheduling, live validation, or universal compatibility from local page tests.

## Change and test together

Update the relevant HTML, companion playbook, manifest, and top-level guide together. Preserve legacy download URLs. No remote services are called by the interactive demo. Its timestamps and progress are simulated; a failed check must not advance freshness, and 100% must require all agreed milestones.

Run `node --test scripts/dot-skills.test.mjs`, then the applicable repository checks. Inspect desktop and mobile renders, keyboard interactions, repeated clicks, clipboard failure, blocked storage, manual pause, OS reduced motion, and no-JavaScript content. State any tests that could not run. Open ready-for-review pull requests; do not merge without the owner's explicit approval.

## The field report

`field-report/` is the long version of the field notebook: the full story from an interview with the author, including the support cases, the agent the author built before dots existed, and the Blender work. Keep it first person and specific. Quote dots and support replies only with colleague names, channel IDs, and private identifiers removed. Do not add claims the author did not make or the sources do not support.

## Avoid the vibe-coded look

The dot pages use Pixelify Sans for headlines and Plus Jakarta Sans for text, not the Fraunces-and-italics look the main site keeps on purpose. Do not bring back: eyebrow labels above headlines, numbered labels like "01 /", offset "box behind a box" shadows, colored left edges or colored tabs on cards, bento card grids, an italic or underlined word inside a headline, gradient blobs, pills above a call to action, pulsing dots, scroll-triggered reveals, text under 13px, or lines that explain the page to itself ("Playful instructions. Visible limits."). Prose follows the owner's writing rules: no em dashes, capitalize after a colon, no wind-ups or mic-drop closers.

## Easter eggs

They should be found by people clicking around absentmindedly, and they must never hide information. Current eggs: the field report's approval card (five presses), poking Wyndle or Syl for real quotes, ten fast pokes to start a fight, clicking a `null` in the report, typing "allow" or "devil" on any dot page, and ten fast nudges of the home page helper. Every egg honors Pause motion and reduced motion by skipping the movement and keeping the joke.
