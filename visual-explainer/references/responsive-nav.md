# Responsive section navigation

Sticky sidebar TOC on desktop, horizontal scrollable bar on mobile. Use for multi-section pages (4+ sections).

## HTML structure

```html
<div class="wrap">
  <nav class="toc" aria-label="Table of contents">
    <a href="#s1" class="toc-link active">Overview</a>
    <a href="#s2" class="toc-link">Architecture</a>
    <a href="#s3" class="toc-link">Analysis</a>
    <a href="#s4" class="toc-link">Data</a>
    <a href="#s5" class="toc-link">Findings</a>
  </nav>

  <div class="main">
    <section id="s1"><!-- ... --></section>
    <section id="s2"><!-- ... --></section>
    <section id="s3"><!-- ... --></section>
    <section id="s4"><!-- ... --></section>
    <section id="s5"><!-- ... --></section>
  </div>
</div>
```

## CSS

```css
.wrap {
  display: grid;
  grid-template-columns: 170px 1fr;
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

/* Sidebar TOC — desktop */
.toc {
  position: sticky;
  top: 2rem;
  align-self: start;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  max-height: calc(100vh - 4rem);
  overflow-y: auto;
}

.toc-link {
  display: block;
  padding: 0.4rem 0.75rem;
  font-size: 0.8rem;
  color: var(--text-dim);
  text-decoration: none;
  border-left: 2px solid transparent;
  border-radius: 0 4px 4px 0;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.toc-link:hover {
  color: var(--text);
  background: var(--accent-a-dim);
}

.toc-link.active {
  color: var(--accent-a);
  border-left-color: var(--accent-a);
  background: var(--accent-a-dim);
  font-weight: 600;
}

/* Mobile — horizontal bar */
@media (max-width: 999px) {
  .wrap {
    grid-template-columns: 1fr;
    gap: 0;
    padding: 0;
  }

  .toc {
    position: sticky;
    top: 0;
    z-index: 200;
    flex-direction: row;
    overflow-x: auto;
    overflow-y: hidden;
    background: var(--bg);
    border-bottom: 1px solid var(--border);
    padding: 0 1rem;
    gap: 0;
    max-height: none;
  }

  .toc-link {
    border-left: none;
    border-bottom: 2px solid transparent;
    border-radius: 0;
    padding: 0.75rem 0.75rem;
    flex-shrink: 0;
  }

  .toc-link.active {
    border-left-color: transparent;
    border-bottom-color: var(--accent-a);
  }

  .main {
    padding: 1.5rem;
  }

  /* Hide scrollbar but keep scrollable */
  .toc {
    scrollbar-width: none;
    -ms-overflow-style: none;
  }
  .toc::-webkit-scrollbar { display: none; }
}
```

## JavaScript — intersection observer

```javascript
(function() {
  const links = document.querySelectorAll('.toc-link');
  const sections = document.querySelectorAll('section[id]');
  const toc = document.querySelector('.toc');

  // Intersection observer — highlight current section
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        links.forEach(link => {
          link.classList.toggle('active', link.getAttribute('href') === '#' + id);
        });

        // Auto-scroll active tab into view on mobile
        const activeLink = toc.querySelector('.active');
        if (activeLink && window.innerWidth < 1000) {
          activeLink.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest',
            inline: 'center'
          });
        }
      }
    });
  }, {
    rootMargin: '-20% 0px -75% 0px',
    threshold: 0
  });

  sections.forEach(section => observer.observe(section));

  // Smooth scroll on click
  links.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(link.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
        history.replaceState(null, '', link.getAttribute('href'));
      }
    });
  });
})();
```

## Customization

- Adjust sidebar width (`170px` to `200px`) based on content length.
- Replace `var(--accent-a)` with your diagram's accent color.
- Modify `rootMargin` values to change when sections activate.
- Skip TOC entirely for pages with fewer than 4 sections.
