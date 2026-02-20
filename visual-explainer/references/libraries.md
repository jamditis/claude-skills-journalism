# External libraries (CDN)

Optional libraries loaded via CDN when pure CSS/HTML isn't enough. Read this before using any library in generated pages.

## Mermaid.js

Handles flowcharts, sequence diagrams, ER diagrams, state machines, mind maps, class diagrams. Auto-layout.

**Do NOT use for dashboards** — CSS Grid card layouts with Chart.js look better for those.

### CDN imports

```html
<!-- Mermaid 11 -->
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';

  // For complex graphs: ELK layout engine
  import elkLayouts from 'https://cdn.jsdelivr.net/npm/@mermaid-js/layout-elk@0.1/dist/mermaid-layout-elk.esm.min.mjs';

  mermaid.registerLayoutLoaders(elkLayouts);

  mermaid.initialize({
    startOnLoad: true,
    theme: 'base',
    look: 'handDrawn',  // or 'classic'
    layout: 'elk',       // for complex graphs
    themeVariables: {
      fontFamily: 'var(--font-body)',
      fontSize: '16px',
      primaryColor: '#5b8af0',
      primaryTextColor: '#e8eaed',
      primaryBorderColor: '#3a6dd8',
      secondaryColor: '#3dc9a8',
      tertiaryColor: '#f0a05b',
      lineColor: '#5a5e72',
      background: '#181b24',
      mainBkg: '#1e2230',
      nodeBorder: '#3a4560',
    }
  });
</script>
```

### Theming rules

Always use `theme: 'base'` for full `themeVariables` customization. Built-in themes (`dark`, `forest`, `neutral`) ignore most variable overrides.

For dark mode detection at initialization:

```javascript
const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

mermaid.initialize({
  theme: 'base',
  themeVariables: isDark ? {
    // dark palette
    primaryColor: '#5b8af0',
    primaryTextColor: '#e8eaed',
    background: '#181b24',
    mainBkg: '#1e2230',
  } : {
    // light palette
    primaryColor: '#3366cc',
    primaryTextColor: '#1a1d26',
    background: '#f5f6f8',
    mainBkg: '#ffffff',
  }
});
```

Mermaid initializes once — use this pattern rather than trying to switch reactively. CSS-styled elements around the diagram respond to theme changes instantly; SVG internals don't.

### CSS overrides for Mermaid

```css
/* Node text — always use CSS, never classDef color: */
.node rect, .node polygon { rx: 8; ry: 8; }
.label { font-family: var(--font-body) !important; }

/* Edge labels */
.edgeLabel { font-size: 0.8rem; }
```

**Never set `color:` in classDef** — it hardcodes text color that breaks in the opposite color scheme. Use semi-transparent fills (8-digit hex) with `20`–`44` alpha for subtle effects:

```
classDef primary fill:#5b8af033,stroke:#5b8af0
classDef success fill:#3dc9a833,stroke:#3dc9a8
classDef warning fill:#f0a05b33,stroke:#f0a05b
classDef danger fill:#e0608033,stroke:#e06080
```

### Writing valid Mermaid

**Quote labels** containing special characters (parentheses, colons, commas, brackets, ampersands):

```
A["API Gateway (v2)"] --> B["Auth: JWT"]
C["Config & Settings"] --> D["Database"]
```

**Keep node IDs simple** — alphanumeric, no spaces:

```
apiGateway["API Gateway"] --> authService["Auth Service"]
```

**Limit diagrams to 15–20 nodes** maximum for readability. Use `subgraph` blocks to organize complex diagrams.

**State diagrams** have stricter parsing. Avoid `<br/>`, parentheses in labels, and multiple colons. When labels need special characters, use `flowchart` instead of `stateDiagram-v2`.

## Chart.js

Bar charts, line charts, pie/doughnut, radar. Use for dashboard KPIs and data visualizations.

### CDN import

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
```

### Basic setup

```javascript
const ctx = document.getElementById('myChart').getContext('2d');
new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    datasets: [{
      label: 'Page views',
      data: [12000, 15000, 18000, 14000, 21000],
      backgroundColor: 'rgba(91, 138, 240, 0.6)',
      borderColor: '#5b8af0',
      borderWidth: 1,
      borderRadius: 4,
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: {
        labels: {
          color: getComputedStyle(document.documentElement)
            .getPropertyValue('--text').trim(),
          font: { family: getComputedStyle(document.documentElement)
            .getPropertyValue('--font-body').trim() }
        }
      }
    },
    scales: {
      x: { ticks: { color: 'var(--text-dim)' }, grid: { color: 'var(--border)' } },
      y: { ticks: { color: 'var(--text-dim)' }, grid: { color: 'var(--border)' } }
    }
  }
});
```

### Accessibility for charts

Always provide a data table alternative alongside Chart.js visualizations:

```html
<figure>
  <canvas id="myChart" role="img" aria-label="Bar chart showing monthly page views"></canvas>
  <details>
    <summary>View data table</summary>
    <table>
      <caption>Monthly page views</caption>
      <thead><tr><th scope="col">Month</th><th scope="col">Views</th></tr></thead>
      <tbody>
        <tr><td>Jan</td><td>12,000</td></tr>
        <!-- ... -->
      </tbody>
    </table>
  </details>
</figure>
```

## anime.js

Orchestrate complex entrance sequences for diagrams with 10+ elements.

### CDN import

```html
<script src="https://cdn.jsdelivr.net/npm/animejs@3.2.2/lib/anime.min.js"></script>
```

### Staggered entrance

```javascript
if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  anime({
    targets: '.node',
    opacity: [0, 1],
    translateY: [20, 0],
    delay: anime.stagger(60),
    duration: 400,
    easing: 'easeOutCubic'
  });
}
```

Use sparingly. CSS `animation-delay` with `calc(var(--i) * 60ms)` handles most cases without a library.

## Google Fonts

Always include `display=swap` for fast rendering.

```html
<link href="https://fonts.googleapis.com/css2?family=Display+Font:wght@400;600;700&family=Mono+Font:wght@400;500&display=swap" rel="stylesheet">
```

### Font pairing suggestions

Vary these across diagrams. Never converge on the same pair.

| Category | Display / heading | Body / mono | Mood |
|----------|-------------------|-------------|------|
| Editorial | Playfair Display | Source Serif Pro | Classic newspaper |
| Modern editorial | DM Serif Display | DM Sans | Contemporary magazine |
| Technical | JetBrains Mono | IBM Plex Sans | IDE / blueprint |
| Humanist | Bricolage Grotesque | Fragment Mono | Warm technical |
| Data-dense | Instrument Serif | JetBrains Mono | Wire service / data |
| Academic | Libre Baskerville | Fira Code | Research paper |
| Bold | Space Grotesk | Space Mono | Impact dashboard |
| Warm | Fraunces | Inter | Feature story |
| Clean | Outfit | Source Code Pro | Minimal report |
| Newsroom | Bitter | Inconsolata | Working document |

Remember: Inter, Roboto, Arial, and system-ui are banned as primary fonts. Use distinctive choices.
