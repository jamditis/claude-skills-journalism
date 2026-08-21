## htmx 2.x, server-rendered interactivity

htmx 2.0 (released June 2024) lets you add AJAX, WebSockets, and SSE to plain HTML through `hx-*` attributes. The server sends HTML fragments; the client swaps them in. No JS framework required.

```html
<script src="/vendor/htmx-2.0.10.min.js"></script>

<!-- Click button → POST to server → swap response into #result -->
<button hx-post="/api/clicked" hx-target="#result" hx-swap="innerHTML">
  Click me
</button>
<div id="result"></div>

<!-- Search-as-you-type with debounce -->
<input
  type="search"
  name="q"
  hx-get="/api/search"
  hx-trigger="input changed delay:300ms"
  hx-target="#results"
/>
<div id="results"></div>

<!-- Infinite scroll -->
<div hx-get="/api/items?page=2"
     hx-trigger="revealed"
     hx-swap="afterend">
  ...
</div>
```

htmx 2.x dropped IE support and tightened the API; if you're on htmx 1.x and don't need to migrate, 1.x still receives security patches. New code should target 2.x.
