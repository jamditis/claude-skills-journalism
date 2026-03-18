// ask-ai.js — "Ask an AI about this" dropdown for skills.amditis.tech
// Self-contained vanilla JS. No external CSS dependencies.
// Injected after the last <header> element on each page.

(function () {
  'use strict';

  // -- Theme constants (cream) --
  var COLORS = {
    buttonBg: '#3d4b40',
    buttonText: '#ffffff',
    buttonBorder: '#3d4b40',
    panelBg: '#ffffff',
    panelText: '#121212',
    panelBorder: '#d6cdb7',
    panelShadow: '0 10px 25px rgba(0,0,0,0.1)',
    itemHover: '#f5f0e6',
    iconColor: '#3d4b40',
  };

  var FONT = "'Plus Jakarta Sans', sans-serif";

  // -- SVG icons (inline, 20x20) --
  // All icon markup is static/hardcoded. No user input is interpolated.

  function makeChevronIcon() {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '16');
    svg.setAttribute('height', '16');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    var polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    polyline.setAttribute('points', '6 9 12 15 18 9');
    svg.appendChild(polyline);
    return svg;
  }

  function makeClaudeIcon() {
    // Sparkle/star shape
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '20');
    svg.setAttribute('height', '20');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', COLORS.iconColor);
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    var polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    polygon.setAttribute('points', '12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2');
    svg.appendChild(polygon);
    return svg;
  }

  function makeChatIcon() {
    // Chat bubble
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '20');
    svg.setAttribute('height', '20');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', COLORS.iconColor);
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z');
    svg.appendChild(path);
    return svg;
  }

  function makeGeminiIcon() {
    // Diamond shape
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '20');
    svg.setAttribute('height', '20');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', COLORS.iconColor);
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
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
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '20');
    svg.setAttribute('height', '20');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', COLORS.iconColor);
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    var path1 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path1.setAttribute('d', 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4');
    var polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    polyline.setAttribute('points', '7 10 12 15 17 10');
    var line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', '12');
    line.setAttribute('y1', '15');
    line.setAttribute('x2', '12');
    line.setAttribute('y2', '3');
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

  function buildPrompt() {
    var title = getTitle();
    var hostname = window.location.hostname;
    var url = window.location.href;
    return (
      'I\'m reading about "' + title + '" on ' + hostname + '.\n\n' +
      'URL: ' + url + '\n\n' +
      'Can you explain the key concepts and help me apply them?'
    );
  }

  // -- Turndown loader (lazy) --

  var turndownPromise = null;

  function loadTurndown() {
    if (turndownPromise) return turndownPromise;
    turndownPromise = new Promise(function (resolve, reject) {
      if (window.TurndownService) {
        resolve(window.TurndownService);
        return;
      }
      var script = document.createElement('script');
      script.src = 'https://unpkg.com/turndown/dist/turndown.js';
      script.onload = function () {
        resolve(window.TurndownService);
      };
      script.onerror = function () {
        turndownPromise = null;
        reject(new Error('Failed to load Turndown.js'));
      };
      document.head.appendChild(script);
    });
    return turndownPromise;
  }

  function downloadMarkdown() {
    loadTurndown()
      .then(function (TurndownService) {
        var td = new TurndownService({ headingStyle: 'atx', codeBlockStyle: 'fenced' });
        var mainEl = document.querySelector('main');
        var html = mainEl ? mainEl.innerHTML : document.body.innerHTML;
        var md = td.turndown(html);
        var title = getTitle();
        var url = window.location.href;
        var full = '# ' + title + '\n\nSource: ' + url + '\n\n' + md;
        var blob = new Blob([full], { type: 'text/markdown;charset=utf-8' });
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

  // -- Style helpers --

  function applyStyles(el, styles) {
    var css = '';
    for (var key in styles) {
      if (styles.hasOwnProperty(key)) {
        css += key + ':' + styles[key] + ';';
      }
    }
    el.style.cssText = css;
  }

  // -- Build the component --

  function createComponent() {
    var prompt = buildPrompt();
    var encoded = encodeURIComponent(prompt);

    // Wrapper — matches max-w-4xl (56rem) with horizontal padding
    var wrapper = document.createElement('div');
    applyStyles(wrapper, {
      'max-width': '56rem',
      'margin': '0 auto',
      'padding': '1rem 1.5rem 0',
      'position': 'relative',
      'z-index': '20',
      'font-family': FONT,
    });

    // Container for positioning
    var container = document.createElement('div');
    applyStyles(container, {
      'position': 'relative',
      'display': 'inline-block',
    });

    // Trigger button
    var trigger = document.createElement('button');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-haspopup', 'true');
    trigger.setAttribute('type', 'button');
    applyStyles(trigger, {
      'background': COLORS.buttonBg,
      'color': COLORS.buttonText,
      'border': '1px solid ' + COLORS.buttonBorder,
      'border-radius': '0.5rem',
      'padding': '0.5rem 1rem',
      'font-family': FONT,
      'font-size': '0.875rem',
      'font-weight': '600',
      'cursor': 'pointer',
      'display': 'inline-flex',
      'align-items': 'center',
      'gap': '0.5rem',
      'line-height': '1.4',
      'transition': 'opacity 0.15s ease',
    });

    var triggerLabel = document.createElement('span');
    triggerLabel.textContent = 'Ask an AI about this';
    trigger.appendChild(triggerLabel);
    trigger.appendChild(makeChevronIcon());

    trigger.addEventListener('mouseenter', function () {
      trigger.style.opacity = '0.85';
    });
    trigger.addEventListener('mouseleave', function () {
      trigger.style.opacity = '1';
    });

    // Dropdown panel
    var panel = document.createElement('div');
    panel.setAttribute('role', 'menu');
    applyStyles(panel, {
      'display': 'none',
      'position': 'absolute',
      'top': 'calc(100% + 0.5rem)',
      'left': '0',
      'min-width': '15rem',
      'background': COLORS.panelBg,
      'color': COLORS.panelText,
      'border': '1px solid ' + COLORS.panelBorder,
      'border-radius': '0.75rem',
      'box-shadow': COLORS.panelShadow,
      'padding': '0.375rem',
      'z-index': '50',
      'font-family': FONT,
    });

    // Menu items config
    var menuItems = [
      { label: 'Ask Claude', iconFn: makeClaudeIcon, href: 'https://claude.ai/new?q=' + encoded },
      { label: 'Ask ChatGPT', iconFn: makeChatIcon, href: 'https://chatgpt.com/?q=' + encoded },
      { label: 'Ask Gemini', iconFn: makeGeminiIcon, href: 'https://gemini.google.com/app?q=' + encoded },
      { label: 'Download as markdown', iconFn: makeDownloadIcon, action: downloadMarkdown },
    ];

    var ITEM_STYLES = {
      'display': 'flex',
      'align-items': 'center',
      'gap': '0.625rem',
      'width': '100%',
      'padding': '0.5rem 0.75rem',
      'border': 'none',
      'background': 'transparent',
      'color': COLORS.panelText,
      'font-family': FONT,
      'font-size': '0.875rem',
      'font-weight': '500',
      'text-decoration': 'none',
      'cursor': 'pointer',
      'border-radius': '0.5rem',
      'transition': 'background 0.12s ease',
      'text-align': 'left',
      'box-sizing': 'border-box',
    };

    menuItems.forEach(function (item) {
      var el;
      if (item.href) {
        el = document.createElement('a');
        el.href = item.href;
        el.target = '_blank';
        el.rel = 'noopener noreferrer';
      } else {
        el = document.createElement('button');
        el.setAttribute('type', 'button');
        el.addEventListener('click', function () {
          closeDropdown();
          item.action();
        });
      }
      el.setAttribute('role', 'menuitem');
      applyStyles(el, ITEM_STYLES);

      el.appendChild(item.iconFn());
      var span = document.createElement('span');
      span.textContent = item.label;
      el.appendChild(span);

      el.addEventListener('mouseenter', function () {
        el.style.background = COLORS.itemHover;
      });
      el.addEventListener('mouseleave', function () {
        el.style.background = 'transparent';
      });

      panel.appendChild(el);
    });

    // -- Toggle logic --

    var isOpen = false;

    function openDropdown() {
      isOpen = true;
      panel.style.display = 'block';
      trigger.setAttribute('aria-expanded', 'true');
      // Reposition if overflowing right edge
      requestAnimationFrame(function () {
        var rect = panel.getBoundingClientRect();
        if (rect.right > window.innerWidth - 8) {
          panel.style.left = 'auto';
          panel.style.right = '0';
        }
      });
    }

    function closeDropdown() {
      isOpen = false;
      panel.style.display = 'none';
      trigger.setAttribute('aria-expanded', 'false');
      // Reset positioning
      panel.style.left = '0';
      panel.style.right = 'auto';
    }

    trigger.addEventListener('click', function (e) {
      e.stopPropagation();
      if (isOpen) {
        closeDropdown();
      } else {
        openDropdown();
      }
    });

    // Close on outside click
    document.addEventListener('click', function (e) {
      if (isOpen && !container.contains(e.target)) {
        closeDropdown();
      }
    });

    // Close on Escape
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && isOpen) {
        closeDropdown();
        trigger.focus();
      }
    });

    // Assemble
    container.appendChild(trigger);
    container.appendChild(panel);
    wrapper.appendChild(container);

    return wrapper;
  }

  // -- Inject into page --

  function inject() {
    var headers = document.querySelectorAll('header');
    if (!headers.length) return;
    var lastHeader = headers[headers.length - 1];
    var component = createComponent();
    lastHeader.parentNode.insertBefore(component, lastHeader.nextSibling);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }
})();
