# Visual audits

Version: 0.2.0 · Community workflow preview · MIT

Inspect the rendered result, not just the code that was supposed to produce it. Return findings a designer or developer can act on.

## Establish the target

Record the URL or artifact, revision, audience, primary task, reference design, and surfaces in scope. Preserve intentional differences: a playful dot workshop should not be redesigned into the rest of the documentation theme merely for consistency. Confirm whether the request authorizes an audit, implementation, publication, or a specific combination.

Read any existing review permissions before asking for them again. Do not treat a reference image as authorization to publish private screenshots.

## Inspect the actual output

1. Open the exact revision. Capture the full frame before cropping details. Record viewport dimensions and browser/device context. Review at desktop, a narrow mobile width such as 360 px, and relevant intermediate sizes. Check zoom or enlarged text where supported.
2. Check hierarchy, spacing, alignment, line length, readable type, contrast, clipping, overflow, and the accuracy of labels and numbers. A 67% label and its bar must agree. Check both the exported graphic and the real chat preview when reviewing a tracker.
3. Use the interface. Tab through controls; look for visible focus, sensible order, descriptive names, and keyboard equivalents. Exercise repeat clicks, interrupted animations, loading, failure, empty, and long-content states. Test links and downloads, not just their appearance.
4. Check motion with the normal setting, the page's pause control, and the operating system's reduced-motion preference. Keep the whimsical character when motion is enabled; keep content and functionality when it is disabled. Do not require pointer hover to reveal essential information.
5. Review content without JavaScript when practical. A script failure must not hide the guide or turn the only download into an empty container.
6. Log each finding with location, observed behavior, evidence, severity, effect on the user's task, and a specific correction. Separate a reproducible defect from a stylistic preference.

## Example finding

> **Major — mobile tracker footer**
> At 360 px wide, the evidence timestamp is clipped at the right edge in revision [ID]. Full-frame capture: [file].
> Effect: the reader cannot tell when the progress was last checked.
> Fix: allow the timestamp row to wrap and keep both labels beside their values.
> Recheck: repeat at 360 px and with enlarged text on the changed revision.

This illustrates a finding format; it is not a claim about the live dot-skills site.

## Severity

**Blocking:** the primary task cannot be completed or key information is inaccessible.
**Major:** a substantial usability or accuracy problem with a workaround.
**Minor:** a localized defect or inconsistency that does not block the task.
**Suggestion:** a design preference or optional improvement, clearly labeled as such.

## When the browser fails

Record whether the browser could not start, the computer was unreachable, sign-in was lost, or the page itself returned an error. Those are different observations. Preserve the last successful screenshot and its revision. Use a supported, authorized recovery action once when appropriate, then recheck availability. Do not claim a reboot succeeded without confirming the computer is reachable. Do not keep asking the owner to log in to a computer that cannot be reached.

Continue independent work where useful, such as reviewing source code or supplied screenshots, but label it as code-only or screenshot-only. Those checks do not establish the current live appearance. Never report “visually verified” from a test you could not perform.

## Close the loop

After a fix, capture and inspect the changed result using the same conditions. Report fixed, remaining, and untested items. Provide the artifact or revision actually reviewed. An automated accessibility scan is one check, not proof of complete accessibility.

## Requirements and limits

Needs the actual artifact or browser access for a live visual review. Browser/VM failures may prevent that review. This is a method, not a repair for the host environment or permission to publish changes. No runtime certification is claimed.
