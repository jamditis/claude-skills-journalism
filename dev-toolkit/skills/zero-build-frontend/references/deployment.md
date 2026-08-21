## Cache busting for deployments

```html
<!-- Manual versioning for static files -->
<link rel="stylesheet" href="styles.css?v=1.3.0">
<script src="app.js?v=1.3.0"></script>

<!-- Or use build timestamp -->
<script>
  const version = Date.now();
  document.write(`<link rel="stylesheet" href="styles.css?v=${version}">`);
</script>
```

## Deployment patterns

### Static hosting (FTP/SFTP)
```
# Directory structure for WordPress wp-content deployment
wp-content/
└── archive-explorer/
    ├── index.html
    ├── index.js
    ├── index.css
    ├── components/
    │   ├── Sidebar.js
    │   ├── RecordList.js
    │   └── RecordCard.js
    └── data/
        └── archive-data.json
```

### Path management for subdirectory deployment
```javascript
// constants.js

// Auto-detect base path from current URL
const getBasePath = () => {
  const path = window.location.pathname;
  const lastSlash = path.lastIndexOf('/');
  return path.substring(0, lastSlash + 1);
};

export const BASE_PATH = getBasePath();
export const DATA_URL = `${BASE_PATH}data/archive-data.json`;

// Usage
const response = await fetch(DATA_URL);
```

## Performance tips

- **Lazy load large JSON**: Parse incrementally or paginate
- **Use CSS containment**: `contain: layout style` on repeated elements
- **Debounce search input**: Wait 300ms after typing stops
- **Virtualize long lists**: Only render visible items
- **Preload local vendors**: `<link rel="modulepreload" href="/vendor/react-runtime-19.2.8.mjs">`
