# Quality signals for interface changes

Sources checked October 28, 2026. Recheck the linked source when a precise
threshold, supported browser, or conformance claim matters. Choose checks from
the affected user task; this is not a checklist for every edit.

## Choose evidence by the change

| Changed surface | Evidence that can expose a failure |
| --- | --- |
| Interactive control, navigation, dialog, or form | Complete the task with a keyboard. Inspect accessible name, role, state, focus order, focus entry/exit, and restoration. Use the relevant APG pattern for a custom widget. |
| Layout, typography, or content density | Check phone and desktop, long/localized content, 200% text resizing, text-spacing overrides, and reflow at 320 CSS pixels where the applicable criteria require it. |
| Motion, theme, or color | Check affected reduced-motion, forced-colors, and light/dark preferences. Confirm focus, meaning, and state remain visible. Do not force every theme on a change that cannot affect it. |
| Async, network, or account-dependent flow | Exercise relevant loading, empty, success, error, retry, offline, cancellation, and permission/session-change states. Confirm meaningful status updates are announced without moving focus. |
| Images, fonts, layout shifts, main-thread work, or third-party code | Compare loading, interaction responsiveness, and layout stability against the accepted baseline. Record measurement conditions. |
| New CSS or Web API | Verify feature support in the project's browser/device contract. Test progressive enhancement or a usable fallback, including relevant embedded webviews. |
| Drag or authentication flow | Check the specific pointer and authentication criteria, including their scope and exceptions. Keyboard support alone is not a non-dragging pointer alternative. |

Native controls are the starting point. ARIA supplies semantics, not keyboard
behavior. Test the actual task, not only the presence of roles or attributes.
Use a screen reader for changed announcements, names, roles, or focus behavior
when that evidence is needed. Record any unavailable assistive-technology test.

## Accessibility: requirements and evidence

[WCAG 2.2](https://www.w3.org/TR/WCAG22/) is the normative Recommendation.
Use the project's required conformance level. WAI Understanding documents and
APG are supporting guidance. Do not promote a draft, AAA recommendation, or a
design-system convention into an AA requirement.

- [WAI evaluation guidance](https://www.w3.org/WAI/test-evaluate/) explains why
  tools alone cannot determine conformance. Combine scans with knowledgeable
  manual checks; do not report an axe result as a complete accessibility audit.
- [APG keyboard guidance](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/)
  covers widget focus and keyboard interaction. Apply it to the widget in scope.
- [Resize text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html),
  [reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html), and
  [text spacing](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html)
  cover adaptability. Reflow's 320 CSS-pixel width is equivalent to a
  1280-pixel starting viewport at 400% zoom for vertically scrolling content.
  Essential two-dimensional content has exceptions. Text-spacing overrides
  test adaptability; they are not mandatory default design values.
- [Status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)
  covers updates announced without focus changes. Announce meaningful lifecycle
  changes rather than every token in streaming content.
- [Dragging movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html)
  and [accessible authentication](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html)
  apply to specific changed flows. Check their allowed alternatives and exceptions.

For preference behavior, consult MDN's
[reduced motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion)
and [forced colors](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/forced-colors)
references. A preference emulation check does not prove coverage of every device
or assistive-technology combination.

## Performance: field results and lab diagnostics

Current good [Core Web Vitals](https://web.dev/articles/vitals) targets are:

| Metric | Good field result | Measures |
| --- | --- | --- |
| LCP | At most 2.5 seconds | Loading the largest visible content element |
| INP | At most 200 milliseconds | Interaction responsiveness |
| CLS | At most 0.1 | Unexpected layout shifts |

Assess the 75th percentile, segmented by mobile and desktop. These are Google
experience guidelines, not WCAG criteria. Preserve stricter project budgets.

Record whether a result comes from real-user field data or a controlled lab
run. Record URL/build, device, throttling, cache state, and the user interaction
tested. Compare like conditions. A Lighthouse score is not proof that field
targets pass; lack of sufficient field traffic is "not measured", not "passed".
Use [lab/field differences](https://web.dev/articles/lab-and-field-data-differences)
to explain a discrepancy instead of averaging incompatible results. Reserve
dimensions for images and inspect font/loading changes for shifts where relevant.

## Browser support and modern features

[Baseline](https://developer.mozilla.org/en-US/docs/Glossary/Baseline/Compatibility)
describes support across its browser set. Widely available means support for
at least 30 months; newly available means the feature works in the current
stable Baseline browsers. It does not prove usability, accessibility,
performance, or support in every browser and webview.

Check feature-specific compatibility against the project's declared environments.
For a newer feature, preserve an understandable, usable fallback or progressive
enhancement. CSS [feature queries](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@supports)
test support, not implementation quality. Test the affected behavior in a second
engine when browser differences can change the result. Do not call an emulated
viewport a real-device test.

## Evidence and release record

For each check, record: user task, route/component and state, expected outcome,
source requirement, build/commit, browser/version, viewport/device, method,
observed result, evidence path, and remaining limitation. A screenshot records
appearance; a task trace records behavior. Keep known failures visible.

Use approved publication assets or suitable test data. Preserve relevant UI
context, distinguish original captures from illustrative recreations, and use
alt text to describe meaningful content. Keep the documentation's author voice
consistent. Bind final screenshots, docs, and public readback to the deployed
result before declaring the affected work complete.
