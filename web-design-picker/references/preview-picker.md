# Combined preview picker architecture

The picker is a neutral review shell that lets a client compare complete sites without merging their CSS or JavaScript.

## Required structure

```html
<header class="review-bar">
  <div class="identity">…</div>
  <nav role="tablist">…direction tabs…</nav>
  <div class="actions">
    <a href="design-assets.html">Assets</a>
    <a data-open-selected>Open selected</a>
    <button data-presentation>Full-screen view</button>
  </div>
</header>
<main class="stage">
  <iframe data-key="direction-a" src="concepts/direction-a.html"></iframe>
  …
</main>
<button data-restore>Show design controls</button>
<p aria-live="polite" class="sr-only"></p>
```

Use one iframe per direction. This prevents style collisions and ensures each concept remains a real standalone page.

## State and navigation

- Store selected direction in the URL hash.
- Read the hash on initial load and `hashchange`.
- Preserve unknown hashes by falling back to the configured default.
- Use `aria-selected`, `aria-controls`, meaningful iframe titles, and a live region.
- Support Left/Right arrows, Home, End, and optional keys 1 through 9.
- Move focus with keyboard navigation.
- Update the “Open selected” link whenever the direction changes.

## Media management

When a direction becomes inactive:

- pause all videos inside its same-origin iframe
- do not reset the current time unless the project requires it
- attempt playback in the newly active frame only for muted autoplay media

Wrap same-origin iframe access in `try/catch` so the picker does not fail if a future direction is hosted elsewhere.

## Presentation mode

Use a reliable class-based presentation mode:

- hide the review bar
- expand the stage to the full viewport
- reveal a small restore control
- exit on Escape

The browser Fullscreen API may be added as an enhancement, but class-based presentation mode must still work when fullscreen permission is denied.

## Responsive behavior

Desktop:

- project identity, direction tabs, and actions share one bar

Tablet:

- identity and actions occupy the first row
- tabs occupy a second row

Mobile:

- keep all three direction labels visible
- shorten supporting descriptions rather than shrinking text below a readable size
- reduce secondary actions before compressing primary controls

## Visual neutrality

The picker must not make one direction look more important. Use a dark or otherwise neutral shell, consistent tab widths, and no direction-specific theme outside the active indicator.
