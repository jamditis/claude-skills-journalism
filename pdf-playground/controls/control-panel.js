/**
 * PDF Playground — Control panel
 *
 * Builds a sidebar with live design controls. When an iframe with
 * id="preview-frame" exists, all CSS changes target the iframe's
 * document (wrapper mode). Otherwise targets the current document
 * (injection mode, fallback).
 *
 * Requires prompt-generator.js and a template map to be loaded first.
 */

(function () {
  "use strict";

  var map = window.PDFPlaygroundTemplateMap;
  var prompt = window.PDFPlaygroundPrompt;

  if (!map) {
    console.warn("[PDF Playground] No template map found. Control panel not loaded.");
    return;
  }
  if (!prompt) {
    console.warn("[PDF Playground] Prompt generator not found. Control panel not loaded.");
    return;
  }

  // Prevent double-init
  if (document.getElementById("pdf-playground-controls")) return;

  // --- Target document (iframe or current page) ---

  var previewFrame = document.getElementById("preview-frame");
  var targetDoc = null;

  function getTargetDoc() {
    if (previewFrame && previewFrame.contentDocument) {
      return previewFrame.contentDocument;
    }
    return document;
  }

  // Wait for iframe to load before initializing controls
  function onTargetReady(callback) {
    if (!previewFrame) {
      targetDoc = document;
      callback();
      return;
    }
    function check() {
      try {
        if (previewFrame.contentDocument && previewFrame.contentDocument.body) {
          targetDoc = previewFrame.contentDocument;
          callback();
          return;
        }
      } catch (e) {
        // cross-origin, fall back
        targetDoc = document;
        callback();
        return;
      }
      setTimeout(check, 100);
    }
    if (previewFrame.contentDocument && previewFrame.contentDocument.body) {
      targetDoc = previewFrame.contentDocument;
      callback();
    } else {
      previewFrame.addEventListener("load", function () {
        targetDoc = previewFrame.contentDocument;
        callback();
      });
      // Also poll in case load already fired
      setTimeout(check, 200);
    }
  }

  // --- Helpers ---

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === "className") node.className = attrs[k];
        else if (k === "textContent") node.textContent = attrs[k];
        else if (k.indexOf("on") === 0) node.addEventListener(k.slice(2).toLowerCase(), attrs[k]);
        else node.setAttribute(k, attrs[k]);
      });
    }
    if (children) {
      children.forEach(function (c) {
        if (typeof c === "string") node.appendChild(document.createTextNode(c));
        else if (c) node.appendChild(c);
      });
    }
    return node;
  }

  function setCSS(selector, prop, value) {
    var doc = getTargetDoc();
    var targets = doc.querySelectorAll(selector);
    targets.forEach(function (t) {
      t.style.setProperty(prop, value);
    });
  }

  function setCSSVariable(name, value) {
    var doc = getTargetDoc();
    doc.documentElement.style.setProperty(name, value);
  }

  function getCurrentCSSVariable(name) {
    var doc = getTargetDoc();
    return getComputedStyle(doc.documentElement).getPropertyValue(name).trim();
  }

  // --- Google Fonts loader ---

  var loadedFonts = {};

  function loadGoogleFont(fontName) {
    if (loadedFonts[fontName]) return;
    loadedFonts[fontName] = true;

    // Load into the target document (iframe) so the font renders there
    var doc = getTargetDoc();
    var link = doc.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://fonts.googleapis.com/css2?family=" +
      encodeURIComponent(fontName) +
      ":ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap";
    doc.head.appendChild(link);
  }

  // --- Undo/redo stack ---

  var undoStack = [];
  var redoStack = [];
  var panel; // forward declaration

  function captureState() {
    var state = { colors: {}, headingFont: null, bodyFont: null };
    if (map.colors) {
      map.colors.forEach(function (c) {
        state.colors[c.variable] = getCurrentCSSVariable(c.variable) || c.default;
      });
    }
    var headingSelect = panel && panel.querySelector("[data-font-key='heading']");
    var bodySelect = panel && panel.querySelector("[data-font-key='body']");
    state.headingFont = headingSelect ? headingSelect.value : (map.fonts && map.fonts.heading ? map.fonts.heading.default : null);
    state.bodyFont = bodySelect ? bodySelect.value : (map.fonts && map.fonts.body ? map.fonts.body.default : null);
    return state;
  }

  function applyState(state) {
    Object.keys(state.colors).forEach(function (varName) {
      setCSSVariable(varName, state.colors[varName]);
    });
    if (map.colors) {
      map.colors.forEach(function (c) {
        var val = state.colors[c.variable];
        if (!val) return;
        var row = panel.querySelector("[data-color-var='" + c.variable + "']");
        if (row) {
          var colorInput = row.querySelector(".ctrl-color-input");
          var hexInput = row.querySelector(".ctrl-color-hex");
          if (colorInput) colorInput.value = val;
          if (hexInput) hexInput.value = val;
        }
      });
    }
    if (state.headingFont && map.fonts && map.fonts.heading) {
      loadGoogleFont(state.headingFont);
      map.fonts.heading.targets.forEach(function (selector) {
        setCSS(selector, "font-family", "'" + state.headingFont + "', Georgia, serif");
      });
      var headingSelect = panel.querySelector("[data-font-key='heading']");
      if (headingSelect) headingSelect.value = state.headingFont;
    }
    if (state.bodyFont && map.fonts && map.fonts.body) {
      loadGoogleFont(state.bodyFont);
      map.fonts.body.targets.forEach(function (selector) {
        setCSS(selector, "font-family", "'" + state.bodyFont + "', -apple-system, BlinkMacSystemFont, sans-serif");
      });
      var bodySelect = panel.querySelector("[data-font-key='body']");
      if (bodySelect) bodySelect.value = state.bodyFont;
    }
  }

  function pushUndo() {
    undoStack.push(captureState());
    redoStack = [];
    updateUndoRedoButtons();
  }

  function undo() {
    if (undoStack.length === 0) return;
    redoStack.push(captureState());
    applyState(undoStack.pop());
    updateUndoRedoButtons();
  }

  function redo() {
    if (redoStack.length === 0) return;
    undoStack.push(captureState());
    applyState(redoStack.pop());
    updateUndoRedoButtons();
  }

  var undoBtn, redoBtn;
  function updateUndoRedoButtons() {
    if (undoBtn) undoBtn.disabled = undoStack.length === 0;
    if (redoBtn) redoBtn.disabled = redoStack.length === 0;
  }

  // Keyboard shortcuts
  document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) {
      e.preventDefault();
      undo();
    } else if ((e.ctrlKey || e.metaKey) && (e.key === "y" || (e.key === "z" && e.shiftKey))) {
      e.preventDefault();
      redo();
    }
  });

  // --- Build panel ---

  panel = el("div", { id: "pdf-playground-controls" });

  // Expand label (visible when collapsed)
  var expandLabel = el("span", {
    className: "panel-expand-label",
    textContent: "Controls",
    onClick: function () { panel.classList.remove("collapsed"); }
  });

  // Header
  undoBtn = el("button", {
    className: "panel-btn",
    textContent: "\u21A9",
    title: "Undo (Ctrl+Z)",
    onClick: function () { undo(); }
  });
  undoBtn.disabled = true;

  redoBtn = el("button", {
    className: "panel-btn",
    textContent: "\u21AA",
    title: "Redo (Ctrl+Y)",
    onClick: function () { redo(); }
  });
  redoBtn.disabled = true;

  var header = el("div", { className: "panel-header" }, [
    expandLabel,
    el("span", { className: "panel-title", textContent: "PDF Playground" }),
    el("div", { className: "panel-actions" }, [
      undoBtn,
      redoBtn,
      el("button", {
        className: "panel-btn",
        textContent: "\u2192",
        title: "Collapse panel",
        onClick: function () { panel.classList.add("collapsed"); }
      }),
    ]),
  ]);
  panel.appendChild(header);

  // Scrollable body
  var body = el("div", { className: "panel-body" });
  panel.appendChild(body);

  // --- Section builder ---

  function buildSection(label, buildFn) {
    var section = el("div", { className: "ctrl-section open" });
    var sectionHeader = el("div", { className: "ctrl-section-header" }, [
      el("span", { className: "ctrl-section-label", textContent: label }),
      el("span", { className: "ctrl-section-chevron", textContent: "\u25BC" }),
    ]);
    sectionHeader.addEventListener("click", function () {
      section.classList.toggle("open");
    });
    section.appendChild(sectionHeader);

    var sectionBody = el("div", { className: "ctrl-section-body" });
    buildFn(sectionBody);
    section.appendChild(sectionBody);

    body.appendChild(section);
  }

  // --- Presets section ---

  if (map.presets && map.presets.length > 0) {
    buildSection("Presets", function (container) {
      var presetGrid = el("div", { className: "ctrl-preset-grid" });
      map.presets.forEach(function (preset) {
        var swatch = el("div", { className: "ctrl-preset-swatch" });
        swatch.style.background = preset.colors["--red"] || "#ccc";

        var btn = el("button", {
          className: "ctrl-preset-btn",
          title: preset.label,
          onClick: function () {
            pushUndo();
            Object.keys(preset.colors).forEach(function (varName) {
              setCSSVariable(varName, preset.colors[varName]);
            });
            if (map.colors) {
              map.colors.forEach(function (c) {
                var val = preset.colors[c.variable];
                if (!val) return;
                var row = panel.querySelector("[data-color-var='" + c.variable + "']");
                if (row) {
                  var ci = row.querySelector(".ctrl-color-input");
                  var hi = row.querySelector(".ctrl-color-hex");
                  if (ci) ci.value = val;
                  if (hi) hi.value = val;
                }
                prompt.recordChange("color", c.label, { from: c.default, to: val });
              });
            }
            if (preset.headingFont && map.fonts && map.fonts.heading) {
              loadGoogleFont(preset.headingFont);
              map.fonts.heading.targets.forEach(function (sel) {
                setCSS(sel, "font-family", "'" + preset.headingFont + "', Georgia, serif");
              });
              var hs = panel.querySelector("[data-font-key='heading']");
              if (hs) hs.value = preset.headingFont;
              prompt.recordChange("font", map.fonts.heading.label, { from: map.fonts.heading.default, to: preset.headingFont });
            }
            if (preset.bodyFont && map.fonts && map.fonts.body) {
              loadGoogleFont(preset.bodyFont);
              map.fonts.body.targets.forEach(function (sel) {
                setCSS(sel, "font-family", "'" + preset.bodyFont + "', -apple-system, BlinkMacSystemFont, sans-serif");
              });
              var bs = panel.querySelector("[data-font-key='body']");
              if (bs) bs.value = preset.bodyFont;
              prompt.recordChange("font", map.fonts.body.label, { from: map.fonts.body.default, to: preset.bodyFont });
            }
            presetGrid.querySelectorAll(".ctrl-preset-btn").forEach(function (b) {
              b.classList.remove("active");
            });
            btn.classList.add("active");
          },
        }, [swatch, el("span", { className: "ctrl-preset-label", textContent: preset.label })]);

        presetGrid.appendChild(btn);
      });
      container.appendChild(presetGrid);
    });
  }

  // --- Colors section ---

  if (map.colors && map.colors.length > 0) {
    buildSection("Colors", function (container) {
      map.colors.forEach(function (c) {
        var hexInput = el("input", {
          className: "ctrl-color-hex",
          type: "text",
          value: c.default,
        });

        var colorInput = el("input", {
          className: "ctrl-color-input",
          type: "color",
          value: c.default,
        });

        function applyColor(newValue) {
          pushUndo();
          setCSSVariable(c.variable, newValue);
          colorInput.value = newValue;
          hexInput.value = newValue;
          prompt.recordChange("color", c.label, { from: c.default, to: newValue });
        }

        colorInput.addEventListener("input", function () {
          applyColor(this.value);
        });

        hexInput.addEventListener("change", function () {
          var v = this.value.trim();
          if (/^#[0-9a-fA-F]{3,8}$/.test(v)) {
            applyColor(v);
          }
        });

        var row = el("div", { className: "ctrl-row", "data-color-var": c.variable }, [
          el("span", { className: "ctrl-label", textContent: c.label }),
          el("div", { className: "ctrl-color-wrap" }, [colorInput, hexInput]),
        ]);
        container.appendChild(row);
      });
    });
  }

  // --- Fonts section ---

  if (map.fonts) {
    buildSection("Typography", function (container) {
      ["heading", "body"].forEach(function (key) {
        var cfg = map.fonts[key];
        if (!cfg) return;

        var select = el("select", { className: "ctrl-font-select", "data-font-key": key });
        cfg.options.forEach(function (fontName) {
          var opt = el("option", { value: fontName, textContent: fontName });
          if (fontName === cfg.default) opt.selected = true;
          select.appendChild(opt);
        });

        select.addEventListener("change", function () {
          pushUndo();
          var fontName = this.value;
          loadGoogleFont(fontName);
          var fallback = key === "heading"
            ? ", Georgia, serif"
            : ", -apple-system, BlinkMacSystemFont, sans-serif";
          cfg.targets.forEach(function (selector) {
            setCSS(selector, "font-family", "'" + fontName + "'" + fallback);
          });
          prompt.recordChange("font", cfg.label, { from: cfg.default, to: fontName });
        });

        var row = el("div", { className: "ctrl-row" }, [
          el("span", { className: "ctrl-label", textContent: cfg.label }),
          select,
        ]);
        container.appendChild(row);
      });

      if (map.sliders) {
        map.sliders.forEach(function (s) {
          if (s.id === "body-font-size" || s.id === "heading-scale" || s.id === "line-height") {
            container.appendChild(buildSlider(s));
          }
        });
      }
    });
  }

  // --- Slider builder ---

  function buildSlider(s) {
    var valueDisplay = el("span", {
      className: "ctrl-slider-value",
      textContent: s.default + s.unit,
    });

    var slider = el("input", {
      className: "ctrl-slider",
      type: "range",
      min: String(s.min),
      max: String(s.max),
      step: String(s.step),
      value: String(s.default),
    });

    slider.addEventListener("input", function () {
      var val = parseFloat(this.value);
      valueDisplay.textContent = (Math.round(val * 100) / 100) + s.unit;

      if (s.isScale && s.scaleTargets) {
        Object.keys(s.scaleTargets).forEach(function (selector) {
          var base = s.scaleTargets[selector];
          var newSize = Math.round(base.base * val * 100) / 100;
          setCSS(selector, "font-size", newSize + base.unit);
        });
      } else if (s.targets && s.targets.length > 0) {
        s.targets.forEach(function (selector) {
          setCSS(selector, s.property, val + s.unit);
        });
        if (s.mirrorProperty) {
          s.targets.forEach(function (selector) {
            setCSS(selector, s.mirrorProperty, val + s.unit);
          });
        }
      }

      prompt.recordChange("size", s.label, { from: s.default + s.unit, to: val + s.unit });
    });

    return el("div", { className: "ctrl-row" }, [
      el("span", { className: "ctrl-label", textContent: s.label }),
      el("div", { className: "ctrl-slider-wrap" }, [slider, valueDisplay]),
    ]);
  }

  // --- Spacing section ---

  if (map.sliders) {
    var spacingSliders = map.sliders.filter(function (s) {
      return s.id === "page-padding";
    });
    if (spacingSliders.length > 0) {
      buildSection("Spacing", function (container) {
        spacingSliders.forEach(function (s) {
          container.appendChild(buildSlider(s));
        });
      });
    }
  }

  // --- Sections (toggles) ---

  if (map.toggles && map.toggles.length > 0) {
    buildSection("Sections", function (container) {
      map.toggles.forEach(function (t) {
        var checkbox = el("input", { type: "checkbox" });
        checkbox.checked = t.default;

        checkbox.addEventListener("change", function () {
          var visible = this.checked;
          var doc = getTargetDoc();
          var elements = doc.querySelectorAll(t.selector);
          elements.forEach(function (elem) {
            elem.style.display = visible ? "" : "none";
          });
          prompt.recordChange("toggle", t.label, {
            action: visible ? "show" : "hide",
            target: t.selector,
          });
        });

        var toggle = el("label", { className: "ctrl-toggle" }, [
          checkbox,
          el("span", { className: "ctrl-toggle-track" }),
        ]);

        var row = el("div", { className: "ctrl-row" }, [
          el("span", { className: "ctrl-label", textContent: t.label }),
          toggle,
        ]);
        container.appendChild(row);
      });
    });
  }

  // --- Layout section ---

  if (map.layout && map.layout.length > 0) {
    buildSection("Layout", function (container) {
      map.layout.forEach(function (l) {
        if (l.type === "buttonGroup") {
          var group = el("div", { className: "ctrl-btn-group" });

          l.options.forEach(function (opt) {
            var btn = el("button", {
              className: "ctrl-btn-option" + (opt.value === l.default ? " active" : ""),
              textContent: opt.label,
            });
            btn.addEventListener("click", function () {
              group.querySelectorAll(".ctrl-btn-option").forEach(function (b) {
                b.classList.remove("active");
              });
              btn.classList.add("active");
              setCSS(l.target, l.property, opt.value);
              prompt.recordChange("layout", l.label, { from: l.default, to: opt.label + " columns" });
            });
            group.appendChild(btn);
          });

          var row = el("div", { className: "ctrl-row" }, [
            el("span", { className: "ctrl-label", textContent: l.label }),
            group,
          ]);
          container.appendChild(row);

        } else if (l.type === "select") {
          var select = el("select", { className: "ctrl-font-select" });
          l.options.forEach(function (opt) {
            var option = el("option", { value: opt.value, textContent: opt.label });
            if (opt.value === l.default) option.selected = true;
            select.appendChild(option);
          });

          select.addEventListener("change", function () {
            var val = this.value;
            var selectedLabel = l.options.find(function (o) { return o.value === val; });
            l.target.split(",").forEach(function (selector) {
              setCSS(selector.trim(), l.property, val);
            });
            prompt.recordChange("layout", l.label, {
              from: l.default,
              to: selectedLabel ? selectedLabel.label : val,
            });
          });

          var row = el("div", { className: "ctrl-row" }, [
            el("span", { className: "ctrl-label", textContent: l.label }),
            select,
          ]);
          container.appendChild(row);
        }
      });
    });
  }

  // --- Footer (pending changes + actions) ---

  var footer = el("div", { className: "panel-footer" });

  var pendingCountBadge = el("span", { className: "pending-count", textContent: "0" });
  var pendingChevron = el("span", { className: "pending-chevron", textContent: "\u25B2" });
  var pendingTitle = el("span", { className: "pending-title" }, ["Changes"]);
  var pendingList = el("div", { className: "pending-list" });

  var pendingHeader = el("div", { className: "pending-header" }, [
    pendingTitle, pendingCountBadge, pendingChevron
  ]);
  pendingHeader.addEventListener("click", function () {
    pendingList.classList.toggle("open");
    pendingChevron.classList.toggle("open");
  });

  // Pending list is positioned absolutely (expands upward)
  footer.appendChild(pendingList);
  footer.appendChild(pendingHeader);

  // Action buttons
  var actionsBar = el("div", { className: "panel-actions-bar" }, [
    el("button", {
      className: "action-btn action-btn-primary",
      textContent: "Copy changes",
      onClick: function () { prompt.copyToClipboard(); },
    }),
    el("button", {
      className: "action-btn action-btn-secondary",
      textContent: "Reset",
      onClick: function () {
        prompt.clearAll();
        if (previewFrame) {
          previewFrame.contentWindow.location.reload();
        } else {
          window.location.reload();
        }
      },
    }),
  ]);
  footer.appendChild(actionsBar);

  panel.appendChild(footer);

  // --- Update pending list when changes happen ---

  function rebuildPendingList(changes) {
    pendingCountBadge.textContent = String(changes.length);

    while (pendingList.firstChild) {
      pendingList.removeChild(pendingList.firstChild);
    }

    changes.forEach(function (c, i) {
      var text = (i + 1) + ". " + prompt.generateSinglePrompt(c.type, c.label, c.details);
      var removeBtn = el("button", {
        className: "pending-item-remove",
        textContent: "\u2715",
        onClick: function (e) {
          e.stopPropagation();
          prompt.removeChange(c.key);
        },
      });
      var item = el("div", { className: "pending-item" }, [
        el("span", { className: "pending-item-text", textContent: text }),
        removeBtn,
      ]);
      pendingList.appendChild(item);
    });

    if (changes.length > 0 && !pendingList.classList.contains("open")) {
      pendingList.classList.add("open");
      pendingChevron.classList.add("open");
    }
  }

  prompt.onUpdate(rebuildPendingList);

  // --- Inject panel and initialize ---

  document.body.appendChild(panel);

  // Pre-load fonts once the target document is ready
  onTargetReady(function () {
    if (map.fonts) {
      if (map.fonts.heading) loadGoogleFont(map.fonts.heading.default);
      if (map.fonts.body) loadGoogleFont(map.fonts.body.default);
    }
    if (map.presets) {
      map.presets.forEach(function (p) {
        if (p.headingFont) loadGoogleFont(p.headingFont);
        if (p.bodyFont) loadGoogleFont(p.bodyFont);
      });
    }

    // Read current color values from the target document
    if (map.colors) {
      map.colors.forEach(function (c) {
        var currentValue = getCurrentCSSVariable(c.variable) || c.default;
        var row = panel.querySelector("[data-color-var='" + c.variable + "']");
        if (row) {
          var colorInput = row.querySelector(".ctrl-color-input");
          var hexInput = row.querySelector(".ctrl-color-hex");
          if (colorInput) colorInput.value = currentValue;
          if (hexInput) hexInput.value = currentValue;
        }
      });
    }

    console.log("[PDF Playground] Control panel ready for template: " + map.name);
  });

  // Cleanup function
  window.PDFPlaygroundCleanup = function () {
    panel.remove();
    var toast = document.getElementById("pdf-playground-toast");
    if (toast) toast.remove();
  };

  console.log("[PDF Playground] Control panel loaded for template: " + map.name);
})();
