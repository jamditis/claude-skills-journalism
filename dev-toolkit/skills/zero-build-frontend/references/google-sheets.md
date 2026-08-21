## Google Sheets as database

### Fetching published CSV

Load the exact, lockfile-verified local build once before the application code:

```html
<script defer src="/vendor/papaparse-5.5.4.min.js"></script>
```

```javascript
// Google Sheets published as CSV
const SHEET_URL = 'https://docs.google.com/spreadsheets/d/e/SPREADSHEET_ID/pub?gid=0&single=true&output=csv';

async function loadFromSheets() {
  const response = await fetch(SHEET_URL);
  const csv = await response.text();

  // Parse with a locally vendored, lockfile-verified PapaParse build.
  const { data, errors } = Papa.parse(csv, {
    header: true,
    skipEmptyLines: true,
    transformHeader: (h) => h.trim().toLowerCase().replace(/\s+/g, '_')
  });

  if (errors.length > 0) {
    console.warn('CSV parsing errors:', errors);
  }

  return data;
}
```

### Real-time state with localStorage

```javascript
class DataManager {
  constructor(sheetUrl, cacheKey) {
    this.sheetUrl = sheetUrl;
    this.cacheKey = cacheKey;
    this.data = [];
    this.localState = this.loadLocalState();
  }

  loadLocalState() {
    const stored = localStorage.getItem(`${this.cacheKey}-state`);
    return stored ? JSON.parse(stored) : {};
  }

  saveLocalState() {
    localStorage.setItem(`${this.cacheKey}-state`, JSON.stringify(this.localState));
  }

  async refresh() {
    const response = await fetch(this.sheetUrl);
    const csv = await response.text();
    this.data = Papa.parse(csv, { header: true, skipEmptyLines: true }).data;

    // Merge with local state
    this.data.forEach(row => {
      const localData = this.localState[row.id];
      if (localData) {
        Object.assign(row, localData);
      }
    });

    return this.data;
  }

  updateLocal(id, updates) {
    this.localState[id] = { ...this.localState[id], ...updates };
    this.saveLocalState();

    // Update in-memory data too
    const item = this.data.find(d => d.id === id);
    if (item) Object.assign(item, updates);
  }
}

// Usage
const manager = new DataManager(SHEET_URL, 'volunteer-data');
await manager.refresh();

// Mark task as complete (stored locally)
manager.updateLocal('task-123', { completed: true, completed_at: new Date().toISOString() });
```
