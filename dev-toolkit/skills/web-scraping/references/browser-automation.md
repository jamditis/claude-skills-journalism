# Browser automation by structured reference

When to read this: Use this reference before an automated workflow navigates a browser or interacts with a live page.

## Navigation rule

Get a structured accessibility snapshot of the page.
Act on the element references, roles, names, labels, or test identifiers that the snapshot returns.
Get a new snapshot after navigation or a significant document change.
Assume old references are invalid after the page changes.

Do not use a screenshot to decide where to click.
Screenshots verify visual results.
They do not provide stable navigation targets.

## Preferred selector order

Use the most user-visible stable selector that is available:

1. Accessible role and name.
2. Associated form label.
3. Visible text with a narrow scope.
4. Stable test identifier supplied by the application.
5. A small CSS selector only when no semantic selector exists.

Avoid selectors based on layout, generated classes, element position, or long DOM paths.

## Playwright example

Use locators that follow the accessibility tree.

```python
page.get_by_role("button", name="Submit").click()
page.get_by_label("Email").fill("reporter@example.test")
```

After submission, assert the result with a locator.
Take a screenshot only when visual evidence is useful.

## Chrome DevTools MCP example

Ask the tool for a structured page or accessibility snapshot.
Find the button named `Save draft` in the returned structure.
Activate the returned element reference.
Request a new snapshot before the next action.

Do not infer coordinates from a DevTools screenshot.

## Browser-extension agent example

Ask the extension agent to list interactive elements with references.
Select the reference for `Search` and enter the query through that reference.
Ask for a fresh element list after the results page loads.

Do not tell the extension to click the control near a visual landmark.

## Screenshots as evidence

Use screenshots to:

- Confirm layout after an action.
- Record before-and-after evidence.
- Investigate a visual defect.
- Check responsive behavior.
- Verify that a canvas or image rendered.

Keep the viewport and test data consistent when comparing images.
Remove or replace private data before capture.

## Coordinate exception

Coordinates are acceptable only when the target has no accessible element interface.
Typical cases are canvas, WebGL, remote desktop video, and some embedded media controls.
State why structured navigation is unavailable before using coordinates.
Capture evidence after the action.
Stop if a missed coordinate could cause a destructive or external action.

## Keep the browser sandbox enabled

When an agent drives a browser on the user's machine, keep the browser sandbox enabled.
Do not use `--no-sandbox` to fix a Chrome or Chromium launch failure.
The browser processes untrusted page content.
Fix the runtime, permissions, container, or supported browser installation instead.
Move to another supported browser environment if the current one cannot keep the sandbox enabled.
In a container, run the browser as a non-root user or use the official Playwright image with its documented sandbox configuration.

## Avoid native and browser-owned dialogs

Avoid print dialogs, save dialogs, profile choosers, password prompts, notification prompts, and operating-system file pickers when a DOM or automation API can do the work.
Configure permissions before navigation when the test requires them.
Use the automation client's file chooser API for an authorized upload.
Handle JavaScript alert, confirm, and prompt dialogs through the client's dialog event.
Playwright dismisses these dialogs automatically when no handler is registered.
If you register a dialog handler, it must accept or dismiss the dialog, or the action stalls.

Never accept a permission or confirmation dialog merely to continue the script.
Confirm that the task authorizes the resulting action.

## Re-snapshot conditions

Get a new structured snapshot after:

- Navigation.
- Form submission.
- Opening or closing a modal.
- Changing a filter that replaces results.
- Expanding content that rebuilds the document.
- Switching frames or tabs.

For small value changes that do not alter the document, reuse the current locator when the client supports stable locators.

## Failure handling

If a reference fails, do not guess coordinates.
Get a new snapshot and locate the element again.
If the element is absent, check loading state, frame context, authorization, and page errors.
Move to another structured browser tool if the current client cannot expose the target.

## Final check

- Did navigation use semantic selectors or returned references?
- Did you re-snapshot after the page changed?
- Did screenshots serve only as evidence?
- Did you state the reason for any coordinate action?
- Did the browser keep its sandbox enabled?
- Did you avoid unnecessary native dialogs?
- Did you verify the result through page state or a screenshot?

## Sources

- [Playwright locators](https://playwright.dev/docs/locators), on role, label, text, and test-id selectors.
- [Playwright screenshots](https://playwright.dev/docs/screenshots), on page and element captures.
- [Playwright dialogs](https://playwright.dev/docs/dialogs), on alert, confirm, prompt, and before-unload handling.
- [Playwright Python Docker guide](https://playwright.dev/python/docs/docker), on container users and sandbox configuration.
- [Chrome DevTools Protocol Accessibility domain](https://chromedevtools.github.io/devtools-protocol/tot/Accessibility/), on accessibility-tree inspection.
- [Chromium sandbox design](https://chromium.googlesource.com/chromium/src/+/main/docs/design/sandbox.md), on isolating processes that handle untrusted data.
