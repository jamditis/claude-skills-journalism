/* Local demonstrations only. No connectors, sends, schedules, or live checks. */
(function () {
  'use strict';
  const milestones = ['Scope agreed', 'Implementation', 'Review + merge', 'Release', 'Live check', 'Staff acceptance'];
  const scenarios = {
    starting: { label: 'Building', fractions: [1, .5, 0, 0, 0, 0], changed: '09:20', note: 'The scope is agreed and the build is partly complete. No release or live check yet.' },
    merged: { label: 'Merged, not released', fractions: [1, 1, 1, 0, 0, 0], changed: '09:30', note: 'The change passed review and was merged. That is not evidence of a release or a working staff workflow.' },
    blocked: { label: 'Verification blocked', fractions: [1, 1, 1, 1, 0, 0], changed: '09:35', note: 'The release is recorded, but the test browser is unreachable. Keep earned progress; do not invent a live result.' },
    verified: { label: 'Verified complete', fractions: [1, 1, 1, 1, 1, 1], changed: '09:40', note: 'In this example, the current release passed the live check and the intended staff role completed the agreed task.' }
  };

  function calculateProgress(rows) {
    if (!Array.isArray(rows)) throw new TypeError('Milestones must be an array.');
    let earned = 0, total = 0;
    for (const row of rows) {
      if (!Number.isFinite(row.weight) || row.weight <= 0 || !Number.isFinite(row.fraction) || row.fraction < 0 || row.fraction > 1) throw new RangeError('Use positive weights and fractions from 0 to 1.');
      if (row.blocked && row.fraction === 1) throw new RangeError('A completed milestone cannot also be blocked.');
      earned += row.weight * row.fraction;
      total += row.weight;
    }
    if (!rows.length) return 0;
    return rows.every(row => row.fraction === 1) ? 100 : Math.min(99, Math.round(earned / total * 100));
  }

  function createState(scenario = 'starting') {
    const source = scenarios[scenario];
    if (!source) throw new RangeError('Unknown demo scenario.');
    return {
      scenario, label: source.label, note: source.note, minute: 40,
      checked: '09:40', changed: source.changed,
      rows: milestones.map((label, index) => ({ label, weight: 1, fraction: source.fractions[index], blocked: scenario === 'blocked' && index === 4 })),
      message: 'Fictional example loaded. Nothing has been checked or sent.'
    };
  }

  function transition(state, event) {
    if (event.type === 'scenario') return createState(event.scenario);
    if (event.type === 'reset') return createState();
    if (event.type === 'failure') return { ...state, message: 'Simulated retrieval failure. The last successful check and progress-change times stay put.' };
    if (event.type === 'check') {
      const minute = state.minute + 1;
      const checked = `${String(9 + Math.floor(minute / 60)).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')}`;
      return { ...state, minute, checked, message: 'Simulated evidence recheck: no new progress. Only the successful-check time changed.' };
    }
    throw new RangeError('Unknown demo action.');
  }

  // The same model is exercised by Node tests and the browser demo.
  if (typeof module !== 'undefined' && module.exports) module.exports = { calculateProgress, createState, transition };
  if (typeof document === 'undefined') return;

  const motion = document.querySelector('#motion');
  const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
  let userPaused = false;
  try { userPaused = localStorage.getItem('dot-skills-motion') === 'paused'; } catch (_) { /* Storage is optional. */ }
  let paused;
  function applyMotion() {
    paused = preference.matches || userPaused;
    document.documentElement.classList.toggle('paused', paused);
    if (!motion) return;
    motion.disabled = preference.matches;
    motion.setAttribute('aria-pressed', String(paused));
    motion.setAttribute('aria-label', preference.matches ? 'Animations disabled by your device setting' : paused ? 'Resume animations' : 'Pause animations');
    motion.textContent = preference.matches ? 'Reduced motion' : paused ? 'Motion paused' : 'Pause motion';
  }
  applyMotion();
  motion?.addEventListener('click', () => {
    userPaused = !userPaused;
    try { localStorage.setItem('dot-skills-motion', userPaused ? 'paused' : 'on'); } catch (_) { /* Keep working without persistence. */ }
    applyMotion();
  });
  preference.addEventListener('change', applyMotion);

  function animateOnce(element, className) {
    if (paused || !element) return;
    element.classList.remove(className);
    void element.offsetWidth; // Restart a finite animation after a repeated click.
    element.classList.add(className);
  }

  const helper = document.querySelector('#helper');
  const aside = document.querySelector('#helper-note');
  const reminders = ['Nice bar. Where is the evidence?', 'A merge is not a launch.', 'Same post. Fewer pings.', 'Little bounce. No extra permissions.'];
  let nudge = 0;
  helper?.addEventListener('click', () => {
    aside.textContent = reminders[nudge++ % reminders.length];
    animateOnce(helper, 'is-bouncing');
    animateOnce(aside, 'is-changing');
  });
  helper?.addEventListener('pointermove', event => {
    if (paused) return;
    const bounds = helper.getBoundingClientRect();
    const x = Math.max(-3, Math.min(3, (event.clientX - bounds.left - bounds.width / 2) / 18));
    helper.querySelector('.pupils')?.setAttribute('transform', `translate(${x} -2)`);
  });
  helper?.addEventListener('pointerleave', () => helper.querySelector('.pupils')?.removeAttribute('transform'));

  document.querySelectorAll('[data-tracker-demo]').forEach(demo => {
    let state = createState();
    const tracker = demo.querySelector('.tracker');
    function render(announce = false) {
      const percent = calculateProgress(state.rows);
      tracker.dataset.state = state.scenario;
      demo.querySelector('[data-percent]').textContent = `${percent}%`;
      demo.querySelector('[data-fill]').style.width = `${percent}%`;
      const meter = demo.querySelector('[role="progressbar"]');
      meter.setAttribute('aria-valuenow', String(percent));
      meter.setAttribute('aria-valuetext', `${percent}% of the agreed example scope`);
      demo.querySelector('[data-badge]').textContent = state.label;
      demo.querySelector('[data-note]').textContent = state.note;
      demo.querySelector('[data-checked]').textContent = `Example day, ${state.checked}`;
      demo.querySelector('[data-changed]').textContent = `Example day, ${state.changed}`;
      demo.querySelectorAll('[data-milestone]').forEach((item, index) => {
        const row = state.rows[index];
        item.dataset.complete = String(row.fraction === 1);
        item.querySelector('span').textContent = row.blocked ? 'Blocked' : row.fraction === 1 ? 'Complete' : row.fraction > 0 ? 'In progress' : 'Not verified';
      });
      demo.querySelectorAll('[data-scenario]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.scenario === state.scenario)));
      if (announce) demo.querySelector('[data-result]').textContent = state.message;
    }
    demo.querySelectorAll('[data-scenario]').forEach(button => button.addEventListener('click', () => {
      const previous = state.scenario;
      state = transition(state, { type: 'scenario', scenario: button.dataset.scenario });
      state.message = `${state.label}: ${calculateProgress(state.rows)}% of the example scope. ${state.note}`;
      render(true);
      tracker.classList.remove('is-celebrating');
      if (state.scenario === 'verified' && previous !== 'verified') animateOnce(tracker, 'is-celebrating');
    }));
    demo.querySelectorAll('[data-demo-action]').forEach(button => button.addEventListener('click', () => {
      state = transition(state, { type: button.dataset.demoAction });
      if (button.dataset.demoAction === 'reset') tracker.classList.remove('is-celebrating');
      render(true);
    }));
    render();
  });

  document.querySelectorAll('[data-copy]').forEach(button => button.addEventListener('click', async () => {
    const target = document.getElementById(button.dataset.copy);
    const feedback = button.closest('.prompt').querySelector('.copy-status');
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(target.value);
      feedback.textContent = 'Copied. Replace the bracketed details before using it.';
    } catch (_) {
      target.focus();
      target.select();
      feedback.textContent = 'Automatic copy was unavailable. The text is selected; use your device’s copy command.';
    }
  }));
  // Helpers blink at their own pace. The nudge helper is skipped because its pupils follow the pointer.
  document.querySelectorAll('.mascot').forEach((dot, index) => {
    if (dot.closest('#helper')) return;
    dot.classList.add('blinky');
    dot.style.setProperty('--blink-delay', `${(index * 1.7) % 6}s`);
  });

  // Field report easter egg: an approval card that keeps asking until you give up.
  const approval = document.querySelector('[data-approval-loop]');
  if (approval) {
    const prompt = approval.querySelector('[data-approval-prompt]');
    const sleeper = document.querySelector('[data-sleepy-dot]');
    const sleeperTag = document.querySelector('[data-sleepy-tag]');
    const asks = ['Allow this again?', 'Approval expired. Allow again?', 'Are you sure? Allow again?', 'Couldn’t confirm this request’s status. Allow again?', 'Saved rule rejected (reason: null). Allow again?'];
    let approvals = 0;
    approval.querySelectorAll('button').forEach(button => button.addEventListener('click', () => {
      approvals += 1;
      animateOnce(approval, 'is-nagging');
      if (approvals < asks.length) { prompt.textContent = asks[approvals]; return; }
      prompt.textContent = 'Approved. For now.';
      approval.querySelectorAll('button').forEach(item => { item.disabled = true; });
      prompt.focus(); // The focused button was just disabled; keep keyboard users on the card.
      sleeper?.classList.add('is-awake');
      if (sleeperTag) sleeperTag.textContent = 'Syl · back online (for now)';
      animateOnce(approval, 'is-done');
    }));
  }

  document.querySelectorAll('[data-js-only]').forEach(element => { element.hidden = false; });
}());
