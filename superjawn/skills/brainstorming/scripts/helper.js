(function() {
  const WS_URL = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/';
  const MAX_QUEUE = 30;
  let ws = null;
  let eventQueue = [];
  let reconnectTimer = null;

  function clean(value, maximum) {
    const normalized = String(value).replace(/[\u0000-\u001f\u007f]+/gu, ' ').trim();
    return Array.from(normalized).slice(0, maximum).join('');
  }

  function prepareEvent(event) {
    if (!event || (event.type !== 'click' && event.type !== 'choice')) return null;
    const choice = event.choice ?? event.value;
    if (typeof choice !== 'string' || choice.length === 0) return null;
    const safeChoice = clean(choice, 128);
    if (!safeChoice) return null;
    const safe = { type: event.type, choice: safeChoice };
    if (typeof event.text === 'string' && event.text.length > 0) {
      const safeText = clean(event.text, 512);
      if (safeText) safe.text = safeText;
    }
    if (event.id === null) {
      safe.id = null;
    } else if (typeof event.id === 'string') {
      const safeId = clean(event.id, 128);
      if (safeId) safe.id = safeId;
    }
    return safe;
  }

  function connect() {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      eventQueue.forEach(event => ws.send(JSON.stringify(event)));
      eventQueue = [];
    };

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        if (data && data.type === 'reload' && Object.keys(data).length === 1) {
          window.location.reload();
        }
      } catch {
        ws.close(1008, 'Invalid control message');
      }
    };

    ws.onclose = () => {
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connect, 1000);
    };
  }

  function sendEvent(event) {
    const safeEvent = prepareEvent(event);
    if (!safeEvent) return false;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(safeEvent));
    } else {
      if (eventQueue.length === MAX_QUEUE) eventQueue.shift();
      eventQueue.push(safeEvent);
    }
    return true;
  }

  // Capture clicks on choice elements
  document.addEventListener('click', (e) => {
    const target = e.target.closest('[data-choice]');
    if (!target) return;

    sendEvent({
      type: 'click',
      text: target.textContent.trim(),
      choice: target.dataset.choice,
      id: target.id || null
    });

    // Update indicator bar (defer so toggleSelect runs first)
    setTimeout(() => {
      const indicator = document.getElementById('indicator-text');
      if (!indicator) return;
      const container = target.closest('.options') || target.closest('.cards');
      const selected = container ? container.querySelectorAll('.selected') : [];
      if (selected.length === 0) {
        indicator.textContent = 'Click an option above, then return to the terminal';
      } else {
        const labelText = selected.length === 1
          ? (selected[0].querySelector('h3, .content h3, .card-body h3')?.textContent?.trim() || selected[0].dataset.choice)
          : String(selected.length);
        const span = document.createElement('span');
        span.className = 'selected-text';
        span.textContent = labelText + ' selected';
        indicator.replaceChildren(span, ', return to terminal to continue');
      }
    }, 0);
  });

  // Frame UI: selection tracking
  window.selectedChoice = null;

  window.toggleSelect = function(el) {
    const container = el.closest('.options') || el.closest('.cards');
    const multi = container && container.dataset.multiselect !== undefined;
    if (container && !multi) {
      container.querySelectorAll('.option, .card').forEach(o => o.classList.remove('selected'));
    }
    if (multi) {
      el.classList.toggle('selected');
    } else {
      el.classList.add('selected');
    }
    window.selectedChoice = el.dataset.choice;
  };

  // Expose API for explicit use
  window.brainstorm = {
    send: sendEvent,
    choice: (value) => sendEvent({ type: 'choice', choice: value })
  };

  connect();
})();
