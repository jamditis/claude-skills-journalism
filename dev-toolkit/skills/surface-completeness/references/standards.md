# Standards for action hierarchy and accessible presentation

Use primary sources for the decision in scope. Recheck current guidance when its
precise requirements matter. These sources guide behavior. They do not replace
the project's accepted design system or prescribe an imported palette.

- [USWDS button](https://designsystem.digital.gov/components/button/): action
  emphasis, clear labels, and limits on competing prominent buttons.
- [GOV.UK Design System button](https://design-system.service.gov.uk/components/button/):
  primary, secondary, and warning actions, including when an alternative action
  should have less visual emphasis.
- [Material Design 3 buttons](https://m3.material.io/components/buttons/overview):
  button emphasis and variants. Apply the hierarchy principle through existing
  project tokens instead of copying its component library.
- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/):
  normative success criteria. Use the project's required conformance level. Do
  not present an AAA recommendation or another design system's convention as an
  AA requirement.
- [Use of Color, SC 1.4.1](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html):
  do not make color alone carry an action's meaning, state, or error information.
- [Contrast (Minimum), SC 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
  and [Non-text Contrast, SC 1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html):
  inspect actual text and component-state pairings, including focus indicators.
- [Focus Visible, SC 2.4.7](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html),
  [Focus Not Obscured (Minimum), SC 2.4.11](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html),
  and [Pause, Stop, Hide, SC 2.2.2](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html):
  preserve keyboard navigation and control over affected moving or changing
  content.
- [Target Size (Minimum), SC 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html):
  check target size and spacing, including the stated exceptions. Preserve
  stricter local control-size rules where the project already requires them.

Record the relevant source, its specific recommendation or criterion, the local
rule or token that implements it, and observed evidence. Design-system
conventions about button hierarchy are usability guidance, not universal laws
about hues. A green primary action can be valid in a system that defines it that
way. A color request is not permission to make Cancel look like that primary
action.
