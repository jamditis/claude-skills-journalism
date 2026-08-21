## ESM import maps

Import maps let you write `import x from 'react'` in a `<script type="module">` without a bundler, the browser resolves the bare specifier against the map. Stable in all major browsers since 2023.

```html
<script type="importmap">
{
  "imports": {
    "@app/runtime": "/vendor/react-runtime-19.2.8.mjs",
    "lodash-es": "/vendor/lodash-es-4.18.1.mjs",
    "@my-app/": "/src/"
  }
}
</script>
```

The trailing `/` form (`"@my-app/": "/src/"`) lets you import any file under
that local prefix. Import maps do not add integrity protection to a remote ESM
dependency graph: SRI on the first module cannot authenticate its transitive
imports. Keep the whole graph local and lockfile-verified.
