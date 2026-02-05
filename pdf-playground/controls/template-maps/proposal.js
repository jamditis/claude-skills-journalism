/**
 * PDF Playground — Template map: Proposal
 *
 * Maps the proposal template's CSS variables, selectors, and sections
 * to human-readable control panel entries. The control-panel.js reads
 * this map to build the UI dynamically.
 */

(function () {
  "use strict";

  window.PDFPlaygroundTemplateMap = {

    name: "proposal",

    // --- Color controls ---
    // Each entry: { variable, label, default }
    // "variable" is the CSS custom property name in :root
    colors: [
      { variable: "--red",      label: "Primary color",   default: "#CA3553" },
      { variable: "--red-dark", label: "Primary dark",    default: "#a82a44" },
      { variable: "--gray-800", label: "Text color",      default: "#2d2a28" },
      { variable: "--black",    label: "Heading color",   default: "#000000" },
      { variable: "--white",    label: "Background",      default: "#ffffff" },
      { variable: "--cream",    label: "Accent bg",       default: "#faf9f7" },
      { variable: "--gray-100", label: "Light gray",      default: "#f5f4f2" },
    ],

    // --- Font controls ---
    // targets: CSS selectors that should get the font-family
    // options: list of Google Fonts to offer
    fonts: {
      heading: {
        label: "Heading font",
        targets: [
          ".cover-title", ".section-title", ".logo-primary",
          ".stat-number", ".priority-number", ".case-study-org",
          ".data-callout-stat", ".highlight-text", ".mission-text",
          ".total-amount", ".footer-page", ".page-header-right",
          ".priority-content h3", ".contact-info h4", ".total-label span",
          ".logo-ccm-title"
        ],
        default: "Playfair Display",
        options: [
          "Playfair Display",
          "Merriweather",
          "Fraunces",
          "Lora",
          "DM Serif Display",
          "Inter",
          "Montserrat",
        ],
      },
      body: {
        label: "Body font",
        targets: ["body"],
        default: "Source Sans 3",
        options: [
          "Source Sans 3",
          "Open Sans",
          "Inter",
          "Roboto",
          "Nunito",
          "Work Sans",
          "IBM Plex Sans",
        ],
      },
    },

    // --- Slider controls ---
    // Each: { property, label, unit, min, max, step, default, targets }
    // If "variable" is set, updates a CSS variable instead of a property
    sliders: [
      {
        id: "body-font-size",
        label: "Body font size",
        property: "font-size",
        targets: ["body"],
        unit: "pt",
        min: 9,
        max: 14,
        step: 0.5,
        default: 11,
      },
      {
        id: "heading-scale",
        label: "Heading scale",
        property: null,
        targets: [],
        unit: "x",
        min: 0.8,
        max: 1.3,
        step: 0.05,
        default: 1.0,
        // Special: multiplies all heading sizes by this factor
        isScale: true,
        scaleTargets: {
          ".cover-title":       { base: 42, unit: "pt" },
          ".section-title":     { base: 26, unit: "pt" },
          ".stat-number":       { base: 36, unit: "pt" },
          ".priority-number":   { base: 28, unit: "pt" },
          ".highlight-text":    { base: 14, unit: "pt" },
          ".data-callout-stat": { base: 18, unit: "pt" },
          ".case-study-org":    { base: 14, unit: "pt" },
          ".total-amount":      { base: 26, unit: "pt" },
        },
      },
      {
        id: "page-padding",
        label: "Page padding",
        property: "padding-left",
        targets: [".content-page"],
        unit: "in",
        min: 0.4,
        max: 1.0,
        step: 0.05,
        default: 0.75,
        // Also update padding-right to match
        mirrorProperty: "padding-right",
      },
      {
        id: "line-height",
        label: "Line height",
        property: "line-height",
        targets: ["body"],
        unit: "",
        min: 1.2,
        max: 2.0,
        step: 0.1,
        default: 1.6,
      },
    ],

    // --- Section toggles ---
    // Each: { selector, label, default }
    // Toggling hides/shows the matched elements
    toggles: [
      {
        id: "stat-grid",
        label: "Stat grid",
        selector: ".stat-grid",
        default: true,
      },
      {
        id: "highlight-boxes",
        label: "Highlight boxes",
        selector: ".highlight-box",
        default: true,
      },
      {
        id: "case-studies",
        label: "Case studies",
        selector: ".case-study",
        default: true,
      },
      {
        id: "budget-table",
        label: "Budget table",
        selector: ".budget-table, .total-callout",
        default: true,
      },
      {
        id: "mission-block",
        label: "Mission block",
        selector: ".cover-mission",
        default: true,
      },
    ],

    // --- Layout controls ---
    layout: [
      {
        id: "stat-columns",
        label: "Stat columns",
        type: "buttonGroup",
        target: ".stat-grid",
        property: "grid-template-columns",
        options: [
          { value: "repeat(2, 1fr)", label: "2" },
          { value: "repeat(3, 1fr)", label: "3" },
          { value: "repeat(4, 1fr)", label: "4" },
        ],
        default: "repeat(3, 1fr)",
      },
      {
        id: "heading-case",
        label: "Heading case",
        type: "select",
        target: ".cover-title, .section-title, .priority-content h3",
        property: "text-transform",
        options: [
          { value: "none",       label: "Sentence case" },
          { value: "capitalize", label: "Title case" },
          { value: "uppercase",  label: "Uppercase" },
        ],
        default: "none",
      },
    ],

    // --- Presets ---
    // Each preset overrides some or all color variables and optionally fonts
    presets: [
      {
        id: "ccm-brand",
        label: "CCM brand",
        colors: {
          "--red": "#CA3553", "--red-dark": "#a82a44",
          "--gray-800": "#2d2a28", "--black": "#000000",
          "--white": "#ffffff", "--cream": "#faf9f7", "--gray-100": "#f5f4f2",
        },
        headingFont: "Playfair Display",
        bodyFont: "Source Sans 3",
      },
      {
        id: "professional-blue",
        label: "Professional blue",
        colors: {
          "--red": "#1a5f7a", "--red-dark": "#134a5e",
          "--gray-800": "#1e3040", "--black": "#0a1628",
          "--white": "#ffffff", "--cream": "#f0f5f7", "--gray-100": "#eef2f4",
        },
        headingFont: "Merriweather",
        bodyFont: "Open Sans",
      },
      {
        id: "modern-green",
        label: "Modern green",
        colors: {
          "--red": "#2d8659", "--red-dark": "#1f6b44",
          "--gray-800": "#1a2e24", "--black": "#0d1a12",
          "--white": "#ffffff", "--cream": "#f2f8f5", "--gray-100": "#edf5f0",
        },
        headingFont: "Inter",
        bodyFont: "Work Sans",
      },
      {
        id: "warm-earth",
        label: "Warm earth",
        colors: {
          "--red": "#b5651d", "--red-dark": "#8c4e17",
          "--gray-800": "#3d2e1f", "--black": "#1a1008",
          "--white": "#fffdf9", "--cream": "#faf5ee", "--gray-100": "#f7f2ea",
        },
        headingFont: "Lora",
        bodyFont: "Nunito",
      },
      {
        id: "elegant-purple",
        label: "Elegant purple",
        colors: {
          "--red": "#6b3fa0", "--red-dark": "#553080",
          "--gray-800": "#2a2040", "--black": "#130e20",
          "--white": "#ffffff", "--cream": "#f5f2fa", "--gray-100": "#f0ecf7",
        },
        headingFont: "DM Serif Display",
        bodyFont: "IBM Plex Sans",
      },
    ],
  };
})();
