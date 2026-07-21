// Upgrades the "last updated" tape written by scripts/updated-stamp.mjs.
//
// The HTML carries only the absolute date ("Updated Jul 7, 2026"), because a
// relative age baked into a static file is wrong the day after it is built.
// This turns each stamp into "Updated 3 days ago" and ages the tape, keeping
// the exact date in the tooltip. Presentation lives in updated.css, so the tape
// is already drawn before this runs.
(function () {
  'use strict';

  var DAY = 86400000;
  // Age at which a skill stops reading as current. These skills cite statutes,
  // platform APIs, and vendor behavior, so a year-old one is worth checking
  // against its sources before trusting it.
  var TIERS = [
    { name: 'fresh', maxDays: 90 },
    { name: 'aging', maxDays: 270 },
  ];

  function tierFor(days) {
    for (var i = 0; i < TIERS.length; i++) {
      if (days <= TIERS[i].maxDays) return TIERS[i].name;
    }
    return 'stale';
  }

  function relative(days) {
    if (days < 1) return 'today';
    var value, unit;
    if (days < 30) { value = days; unit = 'day'; }
    else if (days < 365) { value = Math.round(days / 30.44); unit = 'month'; }
    else { value = Math.round(days / 365.25); unit = 'year'; }
    if (value < 1) value = 1;
    if (typeof Intl === 'undefined' || !Intl.RelativeTimeFormat) {
      return value + ' ' + unit + (value === 1 ? '' : 's') + ' ago';
    }
    return new Intl.RelativeTimeFormat('en', { numeric: 'auto' }).format(-value, unit);
  }

  function upgrade(tape) {
    var iso = tape.getAttribute('data-updated-at');
    var when = iso ? new Date(iso) : null;
    if (!when || isNaN(when.getTime())) return;

    var time = tape.querySelector('time');
    if (!time) return;
    var absolute = time.textContent;
    // Clock skew, or a commit dated ahead of the reader, reads as today rather
    // than as a negative age.
    var days = Math.max(0, Math.floor((Date.now() - when.getTime()) / DAY));

    tape.setAttribute('data-tier', tierFor(days));
    time.textContent = relative(days);
    tape.title = 'Last changed ' + absolute;
  }

  function run() {
    var tapes = document.querySelectorAll('.updated-tape[data-updated-at]');
    Array.prototype.forEach.call(tapes, upgrade);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
