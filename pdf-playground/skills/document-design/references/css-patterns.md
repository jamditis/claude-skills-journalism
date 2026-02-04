# CSS patterns for print-ready documents

## Page setup

```css
@page {
  size: 8.5in 11in;
  margin: 0;
}

@media print {
  body {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
}
```

## Page breaks

```css
/* Force page break before element */
.page-break-before {
  page-break-before: always;
  break-before: page;
}

/* Force page break after element */
.page-break-after {
  page-break-after: always;
  break-after: page;
}

/* Prevent page break inside element */
.keep-together {
  page-break-inside: avoid;
  break-inside: avoid;
}
```

## Fixed page dimensions

```css
.page {
  width: 8.5in;
  height: 11in;
  padding: 0.75in;
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
}
```

## Cover page layout

```css
.cover-page {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
}

.cover-header {
  /* Top section with logo/org name */
}

.cover-content {
  /* Main title, subtitle, stats */
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.cover-footer {
  /* Date, contact info */
}
```

## Content page layout

```css
.content-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.page-header {
  /* Document title, section name */
  padding-bottom: 0.5in;
}

.page-body {
  flex: 1;
  overflow: hidden;
}

.page-footer {
  /* Page number, document title */
  position: absolute;
  bottom: 0.5in;
  left: 0.75in;
  right: 0.75in;
}
```

## Typography scale

```css
:root {
  --font-heading: 'Playfair Display', Georgia, serif;
  --font-body: 'Source Sans 3', 'Source Sans Pro', sans-serif;

  /* Type scale */
  --text-xs: 0.75rem;    /* 12px - fine print */
  --text-sm: 0.875rem;   /* 14px - captions */
  --text-base: 1rem;     /* 16px - body */
  --text-lg: 1.125rem;   /* 18px - lead text */
  --text-xl: 1.25rem;    /* 20px - subheadings */
  --text-2xl: 1.5rem;    /* 24px - section heads */
  --text-3xl: 2rem;      /* 32px - page titles */
  --text-4xl: 2.5rem;    /* 40px - cover title */
  --text-5xl: 3rem;      /* 48px - hero title */
}
```

## Color variables

```css
:root {
  --color-primary: #CA3553;
  --color-secondary: #000000;
  --color-background: #FFFFFF;
  --color-text: #2d2a28;
  --color-muted: #666666;
  --color-border: #e5e5e5;
}
```

## Budget tables

```css
.budget-table {
  width: 100%;
  border-collapse: collapse;
}

.budget-table th {
  background: var(--color-primary);
  color: white;
  padding: 0.5rem 0.75rem;
  text-align: left;
  font-weight: 600;
}

.budget-table td {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--color-border);
}

.budget-table .total-row {
  background: var(--color-primary);
  color: white;
  font-weight: 700;
}

.budget-table .amount {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
```

## Stat blocks

```css
.stats-row {
  display: flex;
  justify-content: space-around;
  gap: 1rem;
}

.stat-block {
  text-align: center;
}

.stat-number {
  font-size: var(--text-4xl);
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1;
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

## Pull quotes

```css
.pull-quote {
  border-left: 4px solid var(--color-primary);
  padding-left: 1.5rem;
  margin: 1.5rem 0;
  font-size: var(--text-lg);
  font-style: italic;
  color: var(--color-text);
}

.pull-quote cite {
  display: block;
  margin-top: 0.5rem;
  font-size: var(--text-sm);
  font-style: normal;
  color: var(--color-muted);
}
```

## Two-column layout

```css
.two-column {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.sidebar-layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}
```

## Chromium PDF generation

Due to snap confinement on some systems, use this path for PDF generation:

```bash
# Copy HTML to snap-accessible location
cp document.html ~/snap/chromium/common/pdf-work/

# Generate PDF
chromium-browser --headless --disable-gpu \
  --print-to-pdf="$HOME/snap/chromium/common/pdf-work/output.pdf" \
  --no-pdf-header-footer \
  "file://$HOME/snap/chromium/common/pdf-work/document.html"

# Copy result back
cp ~/snap/chromium/common/pdf-work/output.pdf ./
```
