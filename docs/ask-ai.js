// ask-ai.js — "Ask an AI about this" dropdown for skills.amditis.tech
// Self-contained vanilla JS. No external CSS dependencies.
// Injected as a text-style nav link in the header/nav bar.

(function () {
  'use strict';

  // -- Theme constants --
  var COLORS = {
    triggerColor: '#6b6b6b',
    triggerHoverColor: '#121212',
    panelBg: '#ffffff',
    panelText: '#121212',
    panelBorder: '#d6cdb7',
    panelShadow: '0 10px 25px rgba(0,0,0,0.1)',
    itemHover: '#f5f0e6',
    iconColor: '#3d4b40',
  };

  var FONT = "'Plus Jakarta Sans', sans-serif";

  // -- SVG icon factories --
  // All icon markup is static/hardcoded. No user input is interpolated.

  function makeSvg(w, h, color) {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', String(w));
    svg.setAttribute('height', String(h));
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', color || 'currentColor');
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    return svg;
  }

  function makeChatIcon(size, color) {
    var svg = makeSvg(size || 20, size || 20, color || COLORS.iconColor);
    var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z');
    svg.appendChild(path);
    return svg;
  }

  function makeClaudeIcon() {
    var svg = makeSvg(20, 20, COLORS.iconColor);
    var polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    polygon.setAttribute('points', '12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2');
    svg.appendChild(polygon);
    return svg;
  }

  function makeGeminiIcon() {
    var svg = makeSvg(20, 20, COLORS.iconColor);
    var rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('x', '12');
    rect.setAttribute('y', '1');
    rect.setAttribute('width', '15.56');
    rect.setAttribute('height', '15.56');
    rect.setAttribute('rx', '2');
    rect.setAttribute('transform', 'rotate(45 12 1)');
    svg.appendChild(rect);
    return svg;
  }

  function makeDownloadIcon() {
    var svg = makeSvg(20, 20, COLORS.iconColor);
    var path1 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path1.setAttribute('d', 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4');
    var polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    polyline.setAttribute('points', '7 10 12 15 17 10');
    var line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', '12'); line.setAttribute('y1', '15');
    line.setAttribute('x2', '12'); line.setAttribute('y2', '3');
    svg.appendChild(path1);
    svg.appendChild(polyline);
    svg.appendChild(line);
    return svg;
  }

  // -- Helpers --

  function getTitle() {
    var h1 = document.querySelector('h1');
    return (h1 && h1.textContent.trim()) || document.title;
  }

  function getSlug() {
    var path = window.location.pathname.replace(/\/$/, '').split('/').pop();
    return path || 'page';
  }

  function getPageContext() {
    var root = document.querySelector('main') || document.body;
    var parts = [];

    var meta = document.querySelector('meta[name="description"]');
    if (meta && meta.content) parts.push(meta.content.trim());

    var headings = root.querySelectorAll('h2, h3');
    if (headings.length) {
      var outline = [];
      for (var i = 0; i < headings.length && i < 10; i++) {
        var text = headings[i].textContent.trim();
        if (text) outline.push('- ' + text);
      }
      if (outline.length) parts.push('Sections covered:\n' + outline.join('\n'));
    }

    var firstP = root.querySelector('p');
    if (firstP && firstP.textContent.trim()) {
      var pText = firstP.textContent.trim();
      if (pText.length > 400) pText = pText.substring(0, 400) + '...';
      parts.push('Intro: ' + pText);
    }

    return parts.join('\n\n');
  }

  function buildPrompt() {
    var title = getTitle();
    var context = getPageContext();
    var prompt = 'I\'m learning about "' + title + '".';
    if (context) prompt += '\n\nHere\'s what the page covers:\n\n' + context;
    prompt += '\n\nCan you explain the key concepts and help me understand how to apply them?';
    return prompt;
  }

  // -- Turndown loader (lazy) --

  var turndownPromise = null;

  function loadTurndown() {
    if (turndownPromise) return turndownPromise;
    turndownPromise = new Promise(function (resolve, reject) {
      if (window.TurndownService) { resolve(window.TurndownService); return; }
      var script = document.createElement('script');
      script.src = 'https://unpkg.com/turndown@7.2.0/dist/turndown.js';
      script.onload = function () { resolve(window.TurndownService); };
      script.onerror = function () { turndownPromise = null; reject(new Error('Failed to load Turndown.js')); };
      document.head.appendChild(script);
    });
    return turndownPromise;
  }

  function downloadMarkdown() {
    loadTurndown()
      .then(function (TurndownService) {
        var td = new TurndownService({ headingStyle: 'atx', codeBlockStyle: 'fenced' });
        var source = document.querySelector('main') || document.body;
        var clone = source.cloneNode(true);
        var widget = clone.querySelector('[data-ask-ai]');
        if (widget) widget.remove();
        var md = td.turndown(clone.innerHTML);
        var title = getTitle();
        var url = window.location.href;
        var blob = new Blob(['# ' + title + '\n\nSource: ' + url + '\n\n' + md], { type: 'text/markdown;charset=utf-8' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = getSlug() + '.md';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(a.href);
      })
      .catch(function (err) {
        console.error('ask-ai: markdown download failed:', err.message);
      });
  }

  // -- Build the component --

  function createComponent() {
    // Container positions the dropdown relative to the trigger
    var container = document.createElement('div');
    container.setAttribute('data-ask-ai', 'true');
    container.style.position = 'relative';

    // Trigger — styled as a nav text link with a small icon
    var trigger = document.createElement('button');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-haspopup', 'dialog');
    trigger.setAttribute('type', 'button');
    trigger.title = 'Ask an AI about this page';

    // Chat bubble icon (12px, decorative)
    var icon = makeChatIcon(12, 'currentColor');
    icon.setAttribute('aria-hidden', 'true');
    icon.setAttribute('focusable', 'false');
    trigger.appendChild(icon);

    var label = document.createElement('span');
    label.textContent = 'Ask AI';
    trigger.appendChild(label);

    trigger.style.cssText = 'display:inline-flex;align-items:center;gap:0.25rem;' +
      'background:none;border:none;padding:0;cursor:pointer;' +
      'font:inherit;letter-spacing:inherit;text-transform:inherit;' +
      'color:' + COLORS.triggerColor + ';transition:color 0.15s;white-space:nowrap;';

    trigger.addEventListener('mouseenter', function () { trigger.style.color = COLORS.triggerHoverColor; });
    trigger.addEventListener('mouseleave', function () { trigger.style.color = COLORS.triggerColor; });
    trigger.addEventListener('focus', function () { trigger.style.color = COLORS.triggerHoverColor; });
    trigger.addEventListener('blur', function () { trigger.style.color = COLORS.triggerColor; });

    // Dropdown panel
    var panel = document.createElement('div');
    panel.style.cssText = 'display:none;position:absolute;top:calc(100% + 0.5rem);right:0;' +
      'min-width:15rem;background:' + COLORS.panelBg + ';color:' + COLORS.panelText + ';' +
      'border:1px solid ' + COLORS.panelBorder + ';border-radius:0.75rem;' +
      'box-shadow:' + COLORS.panelShadow + ';padding:0.375rem;z-index:50;font-family:' + FONT + ';';

    // Menu items
    var prompt = buildPrompt();
    var encoded = encodeURIComponent(prompt);
    var menuItems = [
      { label: 'Ask Claude', iconFn: makeClaudeIcon, href: 'https://claude.ai/new?q=' + encoded },
      { label: 'Ask ChatGPT', iconFn: function () { return makeChatIcon(20, COLORS.iconColor); }, href: 'https://chatgpt.com/?q=' + encoded },
      { label: 'Ask Gemini (copies prompt)', iconFn: makeGeminiIcon, action: function () {
        navigator.clipboard.writeText(prompt).then(function () {
          window.open('https://gemini.google.com/app', '_blank', 'noopener,noreferrer');
        });
      }},
      { label: 'Download as markdown', iconFn: makeDownloadIcon, action: downloadMarkdown },
    ];

    var itemCss = 'display:flex;align-items:center;gap:0.625rem;width:100%;' +
      'padding:0.5rem 0.75rem;border:none;background:transparent;' +
      'color:' + COLORS.panelText + ';font-family:' + FONT + ';font-size:0.875rem;' +
      'font-weight:500;text-decoration:none;cursor:pointer;border-radius:0.5rem;' +
      'transition:background 0.12s;text-align:left;box-sizing:border-box;';

    menuItems.forEach(function (item) {
      var el;
      if (item.href) {
        el = document.createElement('a');
        el.href = item.href;
        el.target = '_blank';
        el.rel = 'noopener noreferrer';
        el.addEventListener('click', function () { closeDropdown(); });
      } else {
        el = document.createElement('button');
        el.setAttribute('type', 'button');
        el.addEventListener('click', function () { closeDropdown(); item.action(); });
      }
      el.style.cssText = itemCss;
      el.appendChild(item.iconFn());
      var span = document.createElement('span');
      span.textContent = item.label;
      el.appendChild(span);
      el.addEventListener('mouseenter', function () { el.style.background = COLORS.itemHover; });
      el.addEventListener('mouseleave', function () { el.style.background = 'transparent'; });
      panel.appendChild(el);
    });

    // -- Toggle logic --
    var isOpen = false;

    function openDropdown() {
      isOpen = true;
      panel.style.display = 'block';
      trigger.setAttribute('aria-expanded', 'true');
    }

    function closeDropdown() {
      isOpen = false;
      panel.style.display = 'none';
      trigger.setAttribute('aria-expanded', 'false');
    }

    trigger.addEventListener('click', function (e) {
      e.stopPropagation();
      if (isOpen) { closeDropdown(); } else { openDropdown(); }
    });

    document.addEventListener('click', function (e) {
      if (isOpen && !container.contains(e.target)) closeDropdown();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && isOpen) { closeDropdown(); trigger.focus(); }
    });

    container.appendChild(trigger);
    container.appendChild(panel);
    return container;
  }

  // -- Inject into page --

  function inject() {
    var component = createComponent();

    // Strategy: find the right-side nav links container and append there.
    // Skills index: <nav> with direct-child flex divs — use the last (right side).
    // Skills subpages: <nav> with inner flex div — append there.
    var nav = document.querySelector('nav[role="navigation"], nav#main-nav, header nav, nav');
    if (!nav) return;

    var flexChildren = nav.querySelectorAll(':scope > [class*="flex"]');
    if (flexChildren.length > 1) {
      flexChildren[flexChildren.length - 1].appendChild(component);
    } else if (flexChildren.length === 1) {
      flexChildren[0].appendChild(component);
    } else {
      nav.appendChild(component);
    }

    // Derive trigger color from a sibling link
    var siblingLink = nav.querySelector('a');
    if (siblingLink) {
      var computed = window.getComputedStyle(siblingLink);
      var btn = component.querySelector('button');
      if (btn) {
        btn.style.color = computed.color;
        COLORS.triggerColor = computed.color;
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }
})();
