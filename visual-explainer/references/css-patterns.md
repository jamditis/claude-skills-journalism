# CSS patterns for diagrams

Reusable CSS patterns for building self-contained HTML diagrams. Read this before generating any page.

## Theme setup

Define all colors as CSS custom properties. Support both light and dark themes.

```css
:root {
  /* Surfaces */
  --bg: #0f1117;
  --surface: #181b24;
  --surface-raised: #1e2230;
  --border: rgba(255, 255, 255, 0.08);

  /* Text */
  --text: #e8eaed;
  --text-dim: #8b8fa3;
  --text-muted: #5a5e72;

  /* Accents — customize per diagram */
  --accent-a: #5b8af0;
  --accent-a-dim: rgba(91, 138, 240, 0.12);
  --accent-b: #3dc9a8;
  --accent-b-dim: rgba(61, 201, 168, 0.12);
  --accent-c: #f0a05b;
  --accent-c-dim: rgba(240, 160, 91, 0.12);
  --accent-d: #e06080;
  --accent-d-dim: rgba(224, 96, 128, 0.12);

  /* Semantic */
  --pass: #3dc9a8;
  --fail: #e06080;
  --warn: #f0a05b;
  --info: #5b8af0;
}

@media (prefers-color-scheme: light) {
  :root {
    --bg: #f5f6f8;
    --surface: #ffffff;
    --surface-raised: #f0f1f4;
    --border: rgba(0, 0, 0, 0.08);

    --text: #1a1d26;
    --text-dim: #5a5e72;
    --text-muted: #8b8fa3;

    --accent-a: #3366cc;
    --accent-a-dim: rgba(51, 102, 204, 0.08);
    --accent-b: #2a9d84;
    --accent-b-dim: rgba(42, 157, 132, 0.08);
    --accent-c: #cc7a2a;
    --accent-c-dim: rgba(204, 122, 42, 0.08);
    --accent-d: #cc3355;
    --accent-d-dim: rgba(204, 51, 85, 0.08);
  }
}
```

## Background atmosphere

Never use flat solid backgrounds. Pick one:

### Radial glow
```css
body {
  background: var(--bg);
  background-image: radial-gradient(ellipse at 20% 50%, var(--accent-a-dim), transparent 60%);
}
```

### Dot grid
```css
body {
  background: var(--bg);
  background-image: radial-gradient(circle, var(--border) 1px, transparent 1px);
  background-size: 24px 24px;
}
```

### Diagonal lines
```css
body {
  background: var(--bg);
  background-image: repeating-linear-gradient(
    -45deg,
    transparent,
    transparent 10px,
    var(--border) 10px,
    var(--border) 11px
  );
}
```

### Gradient mesh
```css
body {
  background: var(--bg);
  background-image:
    radial-gradient(at 20% 30%, var(--accent-a-dim) 0, transparent 50%),
    radial-gradient(at 80% 70%, var(--accent-b-dim) 0, transparent 50%);
}
```

## Section / node cards

The foundational building block.

```css
.node {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  min-width: 0; /* overflow protection */
}

/* Colored accent border (left side) */
.node[data-accent="a"] { border-left: 3px solid var(--accent-a); }
.node[data-accent="b"] { border-left: 3px solid var(--accent-b); }
.node[data-accent="c"] { border-left: 3px solid var(--accent-c); }
.node[data-accent="d"] { border-left: 3px solid var(--accent-d); }
```

### Depth tiers

Signal importance through visual depth.

```css
/* Hero — executive summary, key findings, lead metric */
.node--hero {
  background: var(--surface-raised);
  border-color: var(--accent-a);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2), 0 0 0 1px var(--border);
}

/* Elevated — important but not hero */
.node--elevated {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

/* Recessed — secondary content, reference material */
.node--recessed {
  background: var(--bg);
  border-style: dashed;
  opacity: 0.85;
}

/* Glass — overlay content */
.node--glass {
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(12px);
  border-color: rgba(255, 255, 255, 0.1);
}
```

### Monospace labels

```css
.label {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-dim);
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.5rem;
}

/* Colored dot indicator */
.label::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-a);
}
.label[data-accent="b"]::before { background: var(--accent-b); }
.label[data-accent="c"]::before { background: var(--accent-c); }
.label[data-accent="d"]::before { background: var(--accent-d); }
```

## Overflow protection

Critical rules to prevent layout breaks.

```css
/* Every grid/flex child needs this */
* { min-width: 0; }

/* Don't use display:flex on <li> — it kills list markers.
   Use absolute positioning for custom markers instead. */
li {
  position: relative;
  padding-left: 1.2em;
}
li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--accent-a);
}

/* Long words / URLs */
.node, td, th {
  overflow-wrap: break-word;
  word-break: break-word;
}

/* Scrollable containers for wide content */
.scroll-x {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
```

## Mermaid zoom controls

Every `.mermaid-wrap` needs interactive controls.

```css
.mermaid-wrap {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface);
}

.zoom-controls {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  display: flex;
  gap: 0.25rem;
  z-index: 10;
}

.zoom-controls button {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
  font-size: 1rem;
  display: grid;
  place-items: center;
}

.zoom-controls button:hover {
  background: var(--surface-raised);
}

.mermaid-viewport {
  cursor: grab;
  transform-origin: 0 0;
  transition: transform 0.1s ease;
}

.mermaid-viewport.dragging {
  cursor: grabbing;
  transition: none;
}
```

```html
<div class="mermaid-wrap">
  <div class="zoom-controls">
    <button onclick="zoomIn(this)" title="Zoom in">+</button>
    <button onclick="zoomOut(this)" title="Zoom out">−</button>
    <button onclick="zoomReset(this)" title="Reset zoom">⟳</button>
  </div>
  <div class="mermaid-viewport">
    <pre class="mermaid">graph TD...</pre>
  </div>
</div>
```

```javascript
function initZoom(wrap) {
  const vp = wrap.querySelector('.mermaid-viewport');
  let scale = 1, panX = 0, panY = 0, dragging = false, startX, startY;

  function apply() {
    vp.style.transform = `translate(${panX}px,${panY}px) scale(${scale})`;
  }

  wrap.querySelector('[title="Zoom in"]').onclick = () => { scale = Math.min(scale * 1.2, 5); apply(); };
  wrap.querySelector('[title="Zoom out"]').onclick = () => { scale = Math.max(scale / 1.2, 0.3); apply(); };
  wrap.querySelector('[title="Reset zoom"]').onclick = () => { scale = 1; panX = 0; panY = 0; apply(); };

  wrap.addEventListener('wheel', (e) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      scale *= e.deltaY < 0 ? 1.08 : 1 / 1.08;
      scale = Math.max(0.3, Math.min(5, scale));
      apply();
    }
  }, { passive: false });

  vp.addEventListener('mousedown', (e) => {
    if (scale <= 1) return;
    dragging = true;
    startX = e.clientX - panX;
    startY = e.clientY - panY;
    vp.classList.add('dragging');
  });
  window.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    panX = e.clientX - startX;
    panY = e.clientY - startY;
    apply();
  });
  window.addEventListener('mouseup', () => {
    dragging = false;
    vp.classList.remove('dragging');
  });
}

document.querySelectorAll('.mermaid-wrap').forEach(initZoom);
```

## Grid layouts

### Architecture (2-column with sidebar)
```css
.arch-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

@media (max-width: 768px) {
  .arch-grid { grid-template-columns: 1fr; }
}
```

### Horizontal pipeline
```css
.pipeline {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  gap: 0.5rem;
  align-items: center;
}

.pipeline-arrow {
  text-align: center;
  color: var(--text-dim);
  font-size: 1.2rem;
}

@media (max-width: 768px) {
  .pipeline {
    grid-auto-flow: row;
    grid-auto-columns: unset;
  }
  .pipeline-arrow { transform: rotate(90deg); }
}
```

### Dashboard card grid
```css
.dash-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}
```

### Data table container
```css
.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 12px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

thead {
  position: sticky;
  top: 0;
  z-index: 2;
  background: var(--surface-raised);
}

th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid var(--border);
  white-space: nowrap;
}

td {
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--border);
}

tr:nth-child(even) td {
  background: rgba(128, 128, 128, 0.03);
}

tr:hover td {
  background: var(--accent-a-dim);
}

/* Numeric columns */
.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
}
```

## Connectors

### CSS arrows (vertical)
```css
.arrow-down {
  width: 2px;
  height: 2rem;
  background: var(--border);
  margin: 0 auto;
  position: relative;
}
.arrow-down::after {
  content: '▼';
  position: absolute;
  bottom: -0.5rem;
  left: 50%;
  transform: translateX(-50%);
  color: var(--text-dim);
  font-size: 0.6rem;
}
```

### CSS arrows (horizontal)
```css
.arrow-right {
  height: 2px;
  background: var(--border);
  flex: 1;
  position: relative;
}
.arrow-right::after {
  content: '▶';
  position: absolute;
  right: -0.4rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-dim);
  font-size: 0.5rem;
}
```

## Animations

### Staggered fade-in
```css
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.fade-in {
  opacity: 0;
  animation: fadeUp 0.4s ease forwards;
  animation-delay: calc(var(--i, 0) * 60ms);
}

@media (prefers-reduced-motion: reduce) {
  .fade-in {
    opacity: 1;
    animation: none;
  }
}
```

### Hover lift
```css
.lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
```

### Scale fade (KPIs, badges)
```css
@keyframes fadeScale {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}
```

### Draw-in (SVG connectors)
```css
@keyframes drawIn {
  from { stroke-dashoffset: var(--len); }
  to { stroke-dashoffset: 0; }
}

.connector {
  stroke-dasharray: var(--len);
  animation: drawIn 0.6s ease forwards;
}
```

### CSS counter animation (no JS needed)
```css
@property --num {
  syntax: '<integer>';
  inherits: false;
  initial-value: 0;
}

.count-up {
  transition: --num 1.2s ease;
  counter-reset: num var(--num);
}
.count-up::after {
  content: counter(num);
}
```

## Status indicators

Styled spans, never emoji.

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.15rem 0.6rem;
  border-radius: 100px;
  font-size: 0.75rem;
  font-weight: 500;
}

.badge--pass {
  background: rgba(61, 201, 168, 0.12);
  color: var(--pass);
}
.badge--pass::before {
  content: '✓';
  font-weight: 700;
}

.badge--fail {
  background: rgba(224, 96, 128, 0.12);
  color: var(--fail);
}
.badge--fail::before {
  content: '✗';
  font-weight: 700;
}

.badge--warn {
  background: rgba(240, 160, 91, 0.12);
  color: var(--warn);
}
.badge--warn::before {
  content: '!';
  font-weight: 700;
}
```

## KPI cards

```css
.kpi {
  text-align: center;
  padding: 1.5rem 1rem;
}
.kpi-value {
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1;
  color: var(--text);
}
.kpi-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-dim);
  margin-top: 0.4rem;
}
.kpi-delta {
  font-size: 0.8rem;
  margin-top: 0.3rem;
}
.kpi-delta.up { color: var(--pass); }
.kpi-delta.down { color: var(--fail); }
```

## Collapsible sections

```css
details {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-top: 0.75rem;
}

summary {
  cursor: pointer;
  font-weight: 600;
  color: var(--text-dim);
  list-style: none;
}
summary::before {
  content: '▸ ';
}
details[open] summary::before {
  content: '▾ ';
}
```

## Sparklines (inline SVG)

```html
<svg width="60" height="20" viewBox="0 0 60 20">
  <polyline
    points="0,18 10,12 20,14 30,6 40,8 50,2 60,4"
    fill="none"
    stroke="var(--accent-a)"
    stroke-width="1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
  />
</svg>
```

## Responsive breakpoint

```css
@media (max-width: 768px) {
  .arch-grid,
  .dash-grid {
    grid-template-columns: 1fr;
  }

  .node {
    padding: 1rem;
  }

  .kpi-value {
    font-size: 2rem;
  }

  h1 { font-size: 1.5rem; }
}
```
