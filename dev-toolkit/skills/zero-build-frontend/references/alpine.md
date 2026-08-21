## Alpine.js 3.x, CSP-compatible client-side reactivity

Alpine.js is a minimal alternative to Vue/React for sprinkles of interactivity.
Use its dedicated [CSP build](https://alpinejs.dev/advanced/csp), which avoids
the standard build's `Function`-style evaluation and works without
`'unsafe-eval'`. Keep complex behavior in a same-origin external component file;
simple property and method references remain in `x-*` attributes.

```html
<script defer src="/js/alpine-components.js"></script>
<script defer src="/vendor/alpine-csp-3.15.12.min.js"></script>

<!-- Toggle visibility -->
<div x-data="togglePanel">
  <button @click="toggle">Toggle</button>
  <div x-show="open" x-transition>Content here</div>
</div>

<!-- Two-way binding + computed -->
<div x-data="nameForm">
  <input x-model="first" placeholder="First">
  <input x-model="last" placeholder="Last">
  <p x-text="fullName"></p>
</div>

<!-- Fetch on mount -->
<div x-data="itemList" x-init="load">
  <template x-for="item in items" :key="item.id">
    <li x-text="item.title"></li>
  </template>
</div>
```

```javascript
// public/js/alpine-components.js, loaded before the deferred CSP runtime
document.addEventListener('alpine:init', () => {
  Alpine.data('togglePanel', () => ({
    open: false,
    toggle() { this.open = !this.open; }
  }));

  Alpine.data('nameForm', () => ({
    first: '',
    last: '',
    get fullName() { return `Hello, ${this.first} ${this.last}`; }
  }));

  Alpine.data('itemList', () => ({
    items: [],
    async load() {
      const response = await fetch('/api/items');
      if (!response.ok) throw new Error('Item request failed');
      this.items = await response.json();
    }
  }));
});
```

Alpine pairs naturally with htmx: htmx swaps a server-rendered fragment in, Alpine handles whatever client-side state that fragment needs (open/close, optimistic toggles, form validation).
