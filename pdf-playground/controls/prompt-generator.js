/**
 * PDF Playground — Prompt generator
 *
 * Tracks design changes made through the control panel and generates
 * Claude Code prompts that can be pasted back to apply those changes
 * to the HTML source file.
 */

(function () {
  "use strict";

  // Pending changes keyed by "type::label" to deduplicate
  const pending = new Map();

  // Callbacks to notify the UI when changes update
  const listeners = [];

  function onUpdate(fn) {
    listeners.push(fn);
  }

  function notifyListeners() {
    listeners.forEach((fn) => fn(getAll()));
  }

  // --- Recording changes ---

  /**
   * Record a single design change.
   * Deduplicates by type+label so changing the same slider twice
   * keeps only the latest value.
   *
   * @param {string} type     - Category: "color", "font", "size", "toggle", "layout"
   * @param {string} label    - Human-readable label: "Primary color", "Body font size"
   * @param {object} details  - { from, to } or { action, target } depending on type
   */
  function recordChange(type, label, details) {
    // Skip no-op changes (e.g. background #ffffff -> #ffffff)
    if (details.from && details.to &&
        details.from.toLowerCase() === details.to.toLowerCase()) {
      return;
    }
    const key = type + "::" + label;
    pending.set(key, { type, label, details, time: Date.now() });
    notifyListeners();
  }

  /**
   * Remove a single pending change by its key.
   */
  function removeChange(key) {
    pending.delete(key);
    notifyListeners();
  }

  /**
   * Clear all pending changes.
   */
  function clearAll() {
    pending.clear();
    notifyListeners();
  }

  // --- Prompt generation ---

  /**
   * Generate a prompt string for one change.
   */
  function generateSinglePrompt(type, label, details) {
    switch (type) {
      case "color":
        return "Change the " + label.toLowerCase() + " from " + details.from + " to " + details.to;
      case "font":
        return "Switch the " + label.toLowerCase() + " to " + details.to;
      case "size":
        return "Set the " + label.toLowerCase() + " to " + details.to;
      case "toggle":
        if (details.action === "hide") {
          return "Remove the " + label.toLowerCase() + " section";
        }
        return "Add back the " + label.toLowerCase() + " section";
      case "layout":
        return "Change the " + label.toLowerCase() + " to " + details.to;
      default:
        return "Change " + label.toLowerCase() + " to " + (details.to || details.action);
    }
  }

  /**
   * Generate a combined prompt for all pending changes.
   * Returns a multi-line string ready to paste into Claude Code.
   */
  function generateCombinedPrompt() {
    var entries = getAll();
    if (entries.length === 0) return "";

    var templateName = (window.PDFPlaygroundTemplateMap && window.PDFPlaygroundTemplateMap.name) || "document";

    if (entries.length === 1) {
      var e = entries[0];
      return generateSinglePrompt(e.type, e.label, e.details) + " in the " + templateName;
    }

    var lines = ["Apply the following changes to the " + templateName + ":"];
    entries.forEach(function (entry, i) {
      lines.push((i + 1) + ". " + generateSinglePrompt(entry.type, entry.label, entry.details));
    });
    return lines.join("\n");
  }

  /**
   * Get all pending changes as an array, sorted by time recorded.
   */
  function getAll() {
    return Array.from(pending.entries())
      .sort(function (a, b) { return a[1].time - b[1].time; })
      .map(function (pair) {
        return Object.assign({ key: pair[0] }, pair[1]);
      });
  }

  // --- Clipboard ---

  /**
   * Copy the combined prompt to the system clipboard and show a toast.
   */
  function copyToClipboard() {
    var text = generateCombinedPrompt();
    if (!text) {
      showToast("No changes to copy");
      return;
    }

    navigator.clipboard.writeText(text).then(function () {
      showToast("Copied " + pending.size + " change" + (pending.size === 1 ? "" : "s") + " to clipboard");
    }).catch(function () {
      // Fallback: select a temporary textarea
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
        showToast("Copied " + pending.size + " change" + (pending.size === 1 ? "" : "s") + " to clipboard");
      } catch (_) {
        showToast("Copy failed — select and copy manually");
      }
      document.body.removeChild(ta);
    });
  }

  // --- Toast ---

  function showToast(message) {
    var existing = document.getElementById("pdf-playground-toast");
    if (existing) existing.remove();

    var toast = document.createElement("div");
    toast.id = "pdf-playground-toast";
    toast.textContent = message;
    document.body.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        toast.classList.add("visible");
      });
    });

    setTimeout(function () {
      toast.classList.remove("visible");
      setTimeout(function () { toast.remove(); }, 300);
    }, 2500);
  }

  // --- Public API ---

  window.PDFPlaygroundPrompt = {
    recordChange: recordChange,
    removeChange: removeChange,
    clearAll: clearAll,
    getAll: getAll,
    generateSinglePrompt: generateSinglePrompt,
    generateCombinedPrompt: generateCombinedPrompt,
    copyToClipboard: copyToClipboard,
    onUpdate: onUpdate,
    showToast: showToast,
  };
})();
