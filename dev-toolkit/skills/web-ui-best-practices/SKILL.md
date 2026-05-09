---
name: web-ui-best-practices
description: Signs of taste in web UI. Use when building or reviewing any user-facing web interface — dashboards, SaaS apps, marketing sites, internal tools. Covers interaction speed, navigation depth, visual restraint, copy quality, and the small details that separate polished products from rough ones.
---

# Web UI best practices

Principles for building web interfaces that feel fast, intentional, and respectful of the user's time. Every rule here is a smell test — violating one is fine if you have a reason, violating several means the UI needs work.

## Speed

Every interaction completes in under 100ms. If it can't, fake it.

- Optimistic UI updates — show the result before the server confirms
- Debounce inputs, but never debounce perceived response
- Prefetch likely next routes on hover or viewport entry
- Use `will-change` and `transform` for animations, never `top`/`left`
- Measure with `performance.now()`, not gut feel

```js
// Optimistic delete — remove from UI immediately, reconcile later
async function handleDelete(id) {
  setItems(prev => prev.filter(i => i.id !== id));
  try {
    await api.delete(`/items/${id}`);
  } catch {
    setItems(prev => [...prev, originalItem]);
    toast("Couldn't delete. Restored.");
  }
}
```

### Skeleton loading states

Never show a spinner when you know the shape of what's coming. Render a skeleton that matches the layout, then swap in real content.

```css
.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

## Modern CSS toolkit

Four capabilities matured between 2023 and 2026 that change how you build component-level responsive layouts and SPA-like transitions without JavaScript. Reach for them before adding a framework.

### Container queries

Container queries let a component respond to **its container's** size, not the viewport's. The same card can render in a 300px sidebar and a 900px main column without media-query coordination at the page level.

```css
.card-list {
  container-type: inline-size;
  container-name: cards;
}

@container cards (min-width: 480px) {
  .card { display: grid; grid-template-columns: 120px 1fr; }
}
```

Stable in all major browsers since 2023. Replaces most "the same component in two places needs to look different" hacks.

### `:has()` parent selector

`:has()` lets a parent style itself based on its descendants — the long-requested "parent selector." Useful for marking a form field as in-error, a card as having an attached image, or a row as containing a focused input — all without JS.

```css
/* Highlight a form group when its input has focus */
.form-group:has(input:focus) {
  outline: 2px solid var(--color-primary);
}

/* Add bottom margin to articles that contain a figure */
article:has(figure) {
  margin-bottom: 2rem;
}
```

Stable in Chrome, Safari, and Firefox since late 2023. Cuts a real category of JS-driven class toggling.

### View transitions

The View Transitions API animates between two DOM states (route changes, modal open/close, list-item swaps) without a framework. The browser snapshots the old state, swaps in the new state, then crossfades or slides between them.

```js
// Same-document transition (Chrome 111+, Safari TP, Firefox behind a flag)
function navigate(newView) {
  if (!document.startViewTransition) {
    renderView(newView);
    return;
  }
  document.startViewTransition(() => renderView(newView));
}
```

```css
/* Smooth crossfade by default; override per element */
::view-transition-old(*) { animation-duration: 200ms; }
::view-transition-new(*) { animation-duration: 200ms; }
```

Cross-document view transitions (between full page navigations) shipped to Chrome 126 in 2024 and let MPAs feel like SPAs. Pair with `prefers-reduced-motion` so users with motion sensitivity get an instant swap, not an animation.

### Scroll-driven animations

`animation-timeline: scroll()` and `animation-timeline: view()` drive CSS animations from scroll position instead of wall-clock time. The classic use case is a progress indicator at the top of an article that fills as you scroll.

```css
@keyframes fill { from { transform: scaleX(0); } to { transform: scaleX(1); } }

.read-progress {
  position: fixed; top: 0; left: 0; right: 0; height: 3px;
  background: var(--color-primary);
  transform-origin: left;
  animation: fill linear;
  animation-timeline: scroll(root);
}
```

Stable in Chromium-based browsers (Chrome 115+, Edge); not yet in Safari or Firefox as of 2026-05. Use as progressive enhancement; provide a JS fallback or accept a less-flashy baseline elsewhere.

## No product tours

If you need a tour to explain your UI, the UI is wrong. Instead:

- Empty states that teach by doing ("Create your first project")
- Progressive disclosure — show features when they become relevant
- Inline hints that disappear after first use
- Defaults that work without configuration

## URLs

Slugs are short, readable, and human-guessable. No UUIDs, no query param soup.

```
Good:  /projects/weather-app
       /settings/billing
       /docs/api/auth

Bad:   /projects/550e8400-e29b-41d4-a716-446655440000
       /app?view=settings&tab=billing&subsection=plan
       /dashboard#!/module/documents/list?filter=active
```

- Use slugs derived from user-provided names
- Keep nesting to 3 segments max
- Make URLs copyable and shareable — they are the product's memory

## Persistent resumable state

Users leave and come back. Respect that.

- Save draft form state to `localStorage` or the server
- Restore scroll position on back navigation
- Preserve filter/sort selections across sessions
- URL encodes the current view state — sharing a URL reproduces the view

```js
// Persist form state across sessions
function usePersistentForm(key, defaults) {
  const [state, setState] = useState(() => {
    const saved = localStorage.getItem(key);
    return saved ? JSON.parse(saved) : defaults;
  });

  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(state));
  }, [key, state]);

  return [state, setState];
}
```

## Color restraint

Not more than 3 colors. One primary, one accent, one for danger/destructive. Everything else is shades of gray.

```css
:root {
  --color-primary: #2563eb;
  --color-accent: #f59e0b;
  --color-danger: #ef4444;

  --gray-50: #fafafa;
  --gray-100: #f4f4f5;
  --gray-200: #e4e4e7;
  --gray-400: #a1a1aa;
  --gray-600: #52525b;
  --gray-900: #18181b;
}
```

- Use opacity and lightness to create hierarchy, not new hues
- Dark mode is the same 3 colors with inverted grays
- If you reach for a 4th color, you're compensating for weak layout

## No visible scrollbars

Hide them unless the user is actively scrolling. Content feels infinite, not trapped.

```css
/* Hide scrollbar across browsers */
.scroll-container {
  overflow-y: auto;
  scrollbar-width: none;          /* Firefox */
  -ms-overflow-style: none;       /* IE/Edge */
}
.scroll-container::-webkit-scrollbar {
  display: none;                  /* Chrome/Safari */
}
```

Use scroll shadows to hint at overflow without chrome:

```css
.scroll-shadow {
  background:
    linear-gradient(white 30%, transparent),
    linear-gradient(transparent, white 70%) 0 100%,
    radial-gradient(farthest-side at 50% 0, rgba(0,0,0,.15), transparent),
    radial-gradient(farthest-side at 50% 100%, rgba(0,0,0,.15), transparent) 0 100%;
  background-repeat: no-repeat;
  background-size: 100% 40px, 100% 40px, 100% 12px, 100% 12px;
  background-attachment: local, local, scroll, scroll;
}
```

## Navigation depth

All navigation is 3 steps or fewer from anywhere. If the user needs more than 3 clicks to reach a destination, flatten the hierarchy.

- Breadcrumbs for depth, not for navigation
- Global nav always visible, never hidden behind a hamburger on desktop
- Use `Cmd+K` / `Ctrl+K` as the escape hatch for power users

### Command palette (Cmd+K)

Every app with more than one page needs a command palette.

```js
// Minimal Cmd+K listener
useEffect(() => {
  function handleKeyDown(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault();
      setCommandPaletteOpen(true);
    }
  }
  document.addEventListener("keydown", handleKeyDown);
  return () => document.removeEventListener("keydown", handleKeyDown);
}, []);
```

Keep the palette simple:
- Fuzzy search over page names, recent actions, settings
- Show keyboard shortcuts inline
- Most recent items first
- No categories until you have 20+ commands

## Clipboard

Copy and paste should work everywhere the user expects it.

- One-click copy on codes, URLs, API keys, IDs
- Paste from clipboard into file uploads, image fields
- Show brief confirmation on copy ("Copied!") that auto-dismisses

```js
async function copyToClipboard(text, label = "Copied") {
  await navigator.clipboard.writeText(text);
  toast(label, { duration: 1500 });
}
```

## Hit targets

Larger hit targets for buttons and inputs. WCAG 2.2 (success criterion 2.5.8) sets the floor at **24×24 CSS pixels**; Apple's Human Interface Guidelines and most native iOS/Android conventions recommend **44×44 points** as the comfortable target. Use 44px as the working minimum for primary actions; 24px as the absolute legal floor for secondary controls (e.g., dense table-row icons).

```css
button, .btn, [role="button"] {
  min-height: 44px;
  min-width: 44px;
  padding: 10px 20px;
}

input, select, textarea {
  min-height: 44px;
  padding: 10px 12px;
  font-size: 16px;  /* Prevents iOS Safari zoom on focus */
}
```

- Adjacent clickable elements need at least 8px gap
- Icon-only buttons get larger padding than labeled buttons
- Don't rely on hover states for critical affordances — they don't exist on touch

## Honest cancellation

One-click cancel. No guilt trips, no dark patterns, no "Are you sure you want to miss out?"

- Cancel button is always visible alongside confirm
- Account deletion works on the first try
- Unsubscribe is one click, not a preference center
- Downgrade flows don't require contacting support

## Tooltips

Very minimal. Tooltips are a confession that the UI doesn't speak for itself.

- Only on icon-only buttons (to provide the label)
- Never on text that's already readable
- Show on hover after 300ms delay, not instantly
- Dismiss on scroll
- Never use tooltips for essential information

## Copy

Active voice. Max 7 words per sentence. Talk like a person, not a legal document.

```
Good:  "Project created"
       "Saved 2 minutes ago"
       "Delete this file?"

Bad:   "Your project has been successfully created!"
       "Changes were last saved approximately 2 minutes ago"
       "Are you sure you want to permanently delete this file? This action cannot be undone."
```

- Buttons are verbs: "Save", "Delete", "Send" — not "Submit", "OK", "Confirm"
- Error messages say what happened and what to do next
- Never blame the user ("Invalid input" → "Enter a valid email")
- Use sentence case everywhere, never Title Case in UI copy

## Optical alignment

Optical alignment over geometric alignment. The eye doesn't see pixels, it sees weight.

- Play icons shift 2-3px right inside circles to look centered
- Text with leading capital letters aligns optically left of its bounding box
- Icons next to text need 1-2px vertical offset depending on the glyph
- Padding around text is visually balanced, not mathematically equal — bottom padding is often 1-2px more than top

```css
/* Geometric center ≠ optical center */
.play-button svg {
  transform: translateX(2px);
}

/* Visually balanced card padding */
.card {
  padding: 20px 24px 22px 24px;
}
```

## Left-to-right reading flow

Optimized for L-to-R reading and the F-pattern scan.

- Most important content in the top-left quadrant
- Primary actions on the right (where the eye ends a line)
- Labels above inputs, not beside them
- Tables: most-scanned column is leftmost
- Don't center-align body text — left-align everything except single-line headings

## Reassurance about loss

Users fear losing work. Prevent it and prove it.

- Auto-save with visible "Saved" indicator and timestamp
- Undo after destructive actions (soft delete, not hard delete)
- "You have unsaved changes" on navigation away
- Version history for anything longer than a tweet
- Confirmation only for irreversible actions, not routine ones

```js
// Warn on unsaved changes
useEffect(() => {
  function handleBeforeUnload(e) {
    if (hasUnsavedChanges) {
      e.preventDefault();
      e.returnValue = "";
    }
  }
  window.addEventListener("beforeunload", handleBeforeUnload);
  return () => window.removeEventListener("beforeunload", handleBeforeUnload);
}, [hasUnsavedChanges]);
```

## Copyable brand assets

Ship a `/brand` or `/press` page with a downloadable SVG logo and brand kit. Don't make people screenshot your logo.

- SVG logo with transparent background
- Color codes (hex, RGB, HSL)
- Font names and weights
- Usage guidelines (minimum size, clear space, don'ts)
- One-click download as ZIP

## Checklist

Use this when reviewing any web UI:

- [ ] Every interaction under 100ms (or optimistically faked)
- [ ] No product tour or onboarding modal
- [ ] URLs are short, readable, no UUIDs
- [ ] State persists across sessions and page reloads
- [ ] 3 colors max (plus grays)
- [ ] No visible scrollbars at rest
- [ ] Any destination reachable in 3 steps or fewer
- [ ] SVG logo and brand kit downloadable
- [ ] Skeleton loaders, not spinners
- [ ] Clipboard copy works on codes, keys, URLs
- [ ] Touch targets 44px minimum
- [ ] Cancel is honest and one-click
- [ ] Cmd+K command palette exists
- [ ] Tooltips only on icon-only buttons
- [ ] Copy is active voice, 7 words max
- [ ] Optical alignment, not geometric
- [ ] Content follows L-to-R F-pattern
- [ ] Auto-save with visible status and undo
