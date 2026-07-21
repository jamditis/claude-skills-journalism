const crypto = require('crypto');
const http = require('http');
const fs = require('fs');
const path = require('path');

// ========== WebSocket Protocol (RFC 6455) ==========

const OPCODES = { TEXT: 0x01, CLOSE: 0x08, PING: 0x09, PONG: 0x0A };
const MAX_FRAME_BYTES = 8 * 1024;
const MAX_MESSAGE_BYTES = 4 * 1024;
const WS_MAGIC = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11';
const EVENT_WINDOW_MS = 10 * 1000;
const MAX_EVENTS_PER_WINDOW = 30;

function computeAcceptKey(clientKey) {
  return crypto.createHash('sha1').update(clientKey + WS_MAGIC).digest('base64');
}

function encodeFrame(opcode, payload) {
  const fin = 0x80;
  const len = payload.length;
  let header;

  if (len < 126) {
    header = Buffer.alloc(2);
    header[0] = fin | opcode;
    header[1] = len;
  } else if (len < 65536) {
    header = Buffer.alloc(4);
    header[0] = fin | opcode;
    header[1] = 126;
    header.writeUInt16BE(len, 2);
  } else {
    header = Buffer.alloc(10);
    header[0] = fin | opcode;
    header[1] = 127;
    header.writeBigUInt64BE(BigInt(len), 2);
  }

  return Buffer.concat([header, payload]);
}

function decodeFrame(buffer) {
  if (buffer.length < 2) return null;

  const firstByte = buffer[0];
  const fin = (firstByte & 0x80) !== 0;
  const reserved = firstByte & 0x70;
  const secondByte = buffer[1];
  const opcode = firstByte & 0x0F;
  const masked = (secondByte & 0x80) !== 0;
  let payloadLen = secondByte & 0x7F;
  let offset = 2;

  if (reserved !== 0) throw new Error('Reserved WebSocket bits are not supported');
  if (!fin) throw new Error('Fragmented WebSocket frames are not supported');
  if (!masked) throw new Error('Client frames must be masked');

  if (payloadLen === 126) {
    if (buffer.length < 4) return null;
    payloadLen = buffer.readUInt16BE(2);
    offset = 4;
  } else if (payloadLen === 127) {
    if (buffer.length < 10) return null;
    const longLength = buffer.readBigUInt64BE(2);
    if (longLength > BigInt(MAX_FRAME_BYTES)) {
      throw new Error('Frame payload exceeds maximum');
    }
    payloadLen = Number(longLength);
    offset = 10;
  }

  if (payloadLen > MAX_FRAME_BYTES) {
    throw new Error('Frame payload exceeds maximum (' + payloadLen + ' > ' + MAX_FRAME_BYTES + ')');
  }
  if (opcode >= 0x08 && payloadLen > 125) {
    throw new Error('Control frame payload exceeds maximum');
  }

  const maskOffset = offset;
  const dataOffset = offset + 4;
  const totalLen = dataOffset + payloadLen;
  if (buffer.length < totalLen) return null;

  const mask = buffer.slice(maskOffset, dataOffset);
  const data = Buffer.alloc(payloadLen);
  for (let i = 0; i < payloadLen; i++) {
    data[i] = buffer[dataOffset + i] ^ mask[i % 4];
  }

  return { opcode, payload: data, bytesConsumed: totalLen };
}

// ========== Configuration ==========

const PORT = Number(process.env.BRAINSTORM_PORT || (49152 + Math.floor(Math.random() * 16383)));
const HOST = process.env.BRAINSTORM_HOST || '127.0.0.1';
const URL_HOST = process.env.BRAINSTORM_URL_HOST || (HOST === '127.0.0.1' ? 'localhost' : HOST);
const PUBLIC_ORIGIN = process.env.BRAINSTORM_PUBLIC_ORIGIN || null;
const SESSION_TOKEN = process.env.BRAINSTORM_TOKEN || crypto.randomBytes(32).toString('base64url');
const SESSION_DIR = process.env.BRAINSTORM_DIR || '/tmp/brainstorm';
const CONTENT_DIR = path.join(SESSION_DIR, 'content');
const STATE_DIR = path.join(SESSION_DIR, 'state');
let ownerPid = process.env.BRAINSTORM_OWNER_PID ? Number(process.env.BRAINSTORM_OWNER_PID) : null;

if (!Number.isInteger(PORT) || PORT < 1 || PORT > 65535) {
  throw new Error('BRAINSTORM_PORT must be an integer from 1 to 65535');
}

const MIME_TYPES = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.svg': 'image/svg+xml'
};

// ========== Session Security ==========

function isLoopbackHost(hostname) {
  const normalized = String(hostname).replace(/^\[|\]$/g, '').toLowerCase();
  return normalized === 'localhost' || normalized === '::1' || normalized === '127.0.0.1';
}

function formatHostname(hostname) {
  const value = String(hostname);
  return value.includes(':') && !value.startsWith('[') ? `[${value}]` : value;
}

function createSecurityContext({ host, port, publicOrigin = null, sessionToken, urlHost }) {
  if (typeof sessionToken !== 'string' || !/^[A-Za-z0-9_-]{43,}$/u.test(sessionToken)) {
    throw new Error('Session capability token must be at least 43 base64url characters');
  }

  const fallbackOrigin = `http://${formatHostname(urlHost)}:${port}`;
  const configuredOrigin = publicOrigin || fallbackOrigin;
  let primary;
  try {
    primary = new URL(configuredOrigin);
  } catch {
    throw new Error('BRAINSTORM_PUBLIC_ORIGIN must be an absolute HTTP(S) origin');
  }
  if (!['http:', 'https:'].includes(primary.protocol)
      || primary.username || primary.password
      || primary.pathname !== '/' || primary.search || primary.hash) {
    throw new Error('BRAINSTORM_PUBLIC_ORIGIN must be an HTTP(S) origin without a path');
  }
  if (!isLoopbackHost(host) && !isLoopbackHost(primary.hostname) && primary.protocol !== 'https:') {
    throw new Error('A non-loopback public origin must use HTTPS through a trusted proxy or tunnel');
  }

  const allowedOrigins = new Set([primary.origin.toLowerCase()]);
  if (!publicOrigin && (isLoopbackHost(host) || isLoopbackHost(urlHost))) {
    allowedOrigins.add(`http://localhost:${port}`);
    allowedOrigins.add(`http://127.0.0.1:${port}`);
    allowedOrigins.add(`http://[::1]:${port}`);
  }

  return {
    allowedHosts: new Set([...allowedOrigins].map(origin => new URL(origin).host.toLowerCase())),
    allowedOrigins,
    bootstrapUrl: `${primary.origin}/?token=${encodeURIComponent(sessionToken)}`,
    cookieName: 'brainstorm_session_' + crypto.createHash('sha256').update(sessionToken).digest('hex').slice(0, 16),
    cookieSecure: primary.protocol === 'https:',
    primaryOrigin: primary.origin,
    token: sessionToken,
  };
}

const SECURITY = createSecurityContext({
  host: HOST,
  port: PORT,
  publicOrigin: PUBLIC_ORIGIN,
  sessionToken: SESSION_TOKEN,
  urlHost: URL_HOST,
});

function safeTokenEqual(candidate, expected) {
  if (typeof candidate !== 'string') return false;
  const left = Buffer.from(candidate);
  const right = Buffer.from(expected);
  return left.length === right.length && crypto.timingSafeEqual(left, right);
}

function parseCookies(header = '') {
  const cookies = new Map();
  for (const pair of header.split(';')) {
    const separator = pair.indexOf('=');
    if (separator === -1) continue;
    const name = pair.slice(0, separator).trim();
    const value = pair.slice(separator + 1).trim();
    if (name) cookies.set(name, value);
  }
  return cookies;
}

function hasCapability(req, security) {
  return safeTokenEqual(parseCookies(req.headers.cookie).get(security.cookieName), security.token);
}

function hasExpectedHost(req, security) {
  const host = String(req.headers.host || '').toLowerCase();
  return security.allowedHosts.has(host);
}

function validateWebSocketRequest(req, security = SECURITY) {
  if (!hasExpectedHost(req, security)) return { ok: false, status: 403, reason: 'Unexpected Host' };
  const origin = String(req.headers.origin || '').toLowerCase();
  if (!security.allowedOrigins.has(origin)) return { ok: false, status: 403, reason: 'Unexpected Origin' };
  if (!hasCapability(req, security)) return { ok: false, status: 401, reason: 'Missing capability' };
  let requestUrl;
  try {
    requestUrl = new URL(req.url, 'http://request.invalid');
  } catch {
    return { ok: false, status: 400, reason: 'Invalid WebSocket path' };
  }
  if (requestUrl.pathname !== '/' || requestUrl.search) {
    return { ok: false, status: 400, reason: 'Invalid WebSocket path' };
  }
  if (req.method !== 'GET'
      || String(req.headers.upgrade || '').toLowerCase() !== 'websocket'
      || !String(req.headers.connection || '').toLowerCase().split(/\s*,\s*/).includes('upgrade')
      || req.headers['sec-websocket-version'] !== '13') {
    return { ok: false, status: 400, reason: 'Invalid WebSocket handshake' };
  }
  const key = req.headers['sec-websocket-key'];
  if (typeof key !== 'string' || Buffer.from(key, 'base64').length !== 16) {
    return { ok: false, status: 400, reason: 'Invalid WebSocket key' };
  }
  return { ok: true };
}

// ========== Templates and Constants ==========

const WAITING_PAGE = `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Brainstorm Companion</title>
<style>body { font-family: system-ui, sans-serif; padding: 2rem; max-width: 800px; margin: 0 auto; }
h1 { color: #333; } p { color: #666; }</style>
</head>
<body><h1>Brainstorm Companion</h1>
<p>Waiting for the agent to push a screen...</p></body></html>`;

const frameTemplate = fs.readFileSync(path.join(__dirname, 'frame-template.html'), 'utf-8');
const helperScript = fs.readFileSync(path.join(__dirname, 'helper.js'), 'utf-8');
const helperInjection = '<script>\n' + helperScript + '\n</script>';

// ========== Helper Functions ==========

function isFullDocument(html) {
  const trimmed = html.trimStart().toLowerCase();
  return trimmed.startsWith('<!doctype') || trimmed.startsWith('<html');
}

function wrapInFrame(content) {
  return frameTemplate.replace('<!-- CONTENT -->', content);
}

function getNewestScreen() {
  const files = fs.readdirSync(CONTENT_DIR)
    .filter(f => f.endsWith('.html'))
    .map(f => {
      const filePath = resolveContentPath('/files/' + encodeURIComponent(f), CONTENT_DIR);
      return filePath ? { path: filePath, mtime: fs.statSync(filePath).mtime.getTime() } : null;
    })
    .filter(Boolean)
    .sort((a, b) => b.mtime - a.mtime);
  return files.length > 0 ? files[0].path : null;
}

function resolveContentPath(requestPathname, contentDir = CONTENT_DIR) {
  if (!requestPathname.startsWith('/files/')) return null;
  let fileName;
  try {
    fileName = decodeURIComponent(requestPathname.slice('/files/'.length));
  } catch {
    return null;
  }
  if (!fileName || fileName === '.' || fileName === '..'
      || fileName.includes('/') || fileName.includes('\\')
      || path.basename(fileName) !== fileName) {
    return null;
  }

  try {
    const root = fs.realpathSync(contentDir);
    const candidate = fs.realpathSync(path.join(root, fileName));
    if (!candidate.startsWith(root + path.sep) || !fs.statSync(candidate).isFile()) return null;
    return candidate;
  } catch {
    return null;
  }
}

function writeResponse(res, status, body, headers = {}) {
  res.writeHead(status, {
    'Cache-Control': 'no-store',
    'Referrer-Policy': 'no-referrer',
    'X-Content-Type-Options': 'nosniff',
    ...headers,
  });
  res.end(body);
}

// ========== HTTP Request Handler ==========

function handleRequest(req, res) {
  let requestUrl;
  try {
    requestUrl = new URL(req.url, 'http://request.invalid');
  } catch {
    writeResponse(res, 400, 'Bad request');
    return;
  }

  if (!hasExpectedHost(req, SECURITY)) {
    writeResponse(res, 421, 'Unexpected Host');
    return;
  }
  if (req.method !== 'GET') {
    writeResponse(res, 405, 'Method not allowed', { Allow: 'GET' });
    return;
  }

  const bootstrapToken = requestUrl.pathname === '/' ? requestUrl.searchParams.get('token') : null;
  if (bootstrapToken !== null) {
    if (!safeTokenEqual(bootstrapToken, SECURITY.token)) {
      writeResponse(res, 401, 'Invalid capability');
      return;
    }
    const cookie = `${SECURITY.cookieName}=${SECURITY.token}; HttpOnly; SameSite=Strict; Path=/`
      + (SECURITY.cookieSecure ? '; Secure' : '');
    writeResponse(res, 303, '', { Location: '/', 'Set-Cookie': cookie });
    return;
  }
  if (!hasCapability(req, SECURITY)) {
    writeResponse(res, 401, 'Missing capability');
    return;
  }

  touchActivity();
  if (requestUrl.pathname === '/') {
    const screenFile = getNewestScreen();
    let html = screenFile
      ? (raw => isFullDocument(raw) ? raw : wrapInFrame(raw))(fs.readFileSync(screenFile, 'utf-8'))
      : WAITING_PAGE;

    if (html.includes('</body>')) {
      html = html.replace('</body>', helperInjection + '\n</body>');
    } else {
      html += helperInjection;
    }

    writeResponse(res, 200, html, { 'Content-Type': 'text/html; charset=utf-8' });
  } else if (requestUrl.pathname.startsWith('/files/')) {
    const filePath = resolveContentPath(requestUrl.pathname);
    if (!filePath) return writeResponse(res, 404, 'Not found');
    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';
    writeResponse(res, 200, fs.readFileSync(filePath), { 'Content-Type': contentType });
  } else {
    writeResponse(res, 404, 'Not found');
  }
}

// ========== WebSocket Connection Handling ==========

const clients = new Set();

function rejectUpgrade(socket, status, reason) {
  const labels = { 400: 'Bad Request', 401: 'Unauthorized', 403: 'Forbidden' };
  socket.end(
    `HTTP/1.1 ${status} ${labels[status] || 'Rejected'}\r\n`
    + 'Connection: close\r\n'
    + 'Content-Type: text/plain; charset=utf-8\r\n'
    + `Content-Length: ${Buffer.byteLength(reason)}\r\n\r\n${reason}`
  );
}

function closeConnection(socket, code) {
  const payload = Buffer.alloc(2);
  payload.writeUInt16BE(code);
  socket.end(encodeFrame(OPCODES.CLOSE, payload));
  clients.delete(socket);
}

function handleUpgrade(req, socket, head = Buffer.alloc(0)) {
  const validation = validateWebSocketRequest(req);
  if (!validation.ok) {
    rejectUpgrade(socket, validation.status, validation.reason);
    return;
  }

  const accept = computeAcceptKey(req.headers['sec-websocket-key']);
  socket.write(
    'HTTP/1.1 101 Switching Protocols\r\n' +
    'Upgrade: websocket\r\n' +
    'Connection: Upgrade\r\n' +
    'Sec-WebSocket-Accept: ' + accept + '\r\n\r\n'
  );

  let buffer = Buffer.alloc(0);
  const connectionState = { eventTimes: [] };
  clients.add(socket);

  function processChunk(chunk) {
    buffer = Buffer.concat([buffer, chunk]);
    if (buffer.length > MAX_FRAME_BYTES + 14) {
      closeConnection(socket, 1009);
      return;
    }
    while (buffer.length > 0) {
      let result;
      try {
        result = decodeFrame(buffer);
      } catch {
        closeConnection(socket, 1002);
        return;
      }
      if (!result) break;
      buffer = buffer.slice(result.bytesConsumed);

      switch (result.opcode) {
        case OPCODES.TEXT: {
          try {
            const text = new TextDecoder('utf-8', { fatal: true }).decode(result.payload);
            handleMessage(text, connectionState);
          } catch {
            console.error(JSON.stringify({ type: 'user-event-rejected' }));
            closeConnection(socket, 1008);
            return;
          }
          break;
        }
        case OPCODES.CLOSE:
          closeConnection(socket, 1000);
          return;
        case OPCODES.PING:
          socket.write(encodeFrame(OPCODES.PONG, result.payload));
          break;
        case OPCODES.PONG:
          break;
        default: {
          const closeBuf = Buffer.alloc(2);
          closeBuf.writeUInt16BE(1003);
          socket.end(encodeFrame(OPCODES.CLOSE, closeBuf));
          clients.delete(socket);
          return;
        }
      }
    }
  }

  socket.on('data', processChunk);
  if (head.length > 0) processChunk(head);

  socket.on('close', () => clients.delete(socket));
  socket.on('error', () => clients.delete(socket));
}

function boundedString(value, field, maximum, { nullable = false } = {}) {
  if (nullable && value === null) return null;
  if (typeof value !== 'string' || value.length === 0 || [...value].length > maximum) {
    throw new Error(`Invalid ${field}`);
  }
  if (/[\u0000-\u001f\u007f]/u.test(value)) throw new Error(`Invalid ${field}`);
  return value;
}

function normalizeEvent(text, timestamp = Date.now()) {
  if (typeof text !== 'string' || Buffer.byteLength(text, 'utf8') > MAX_MESSAGE_BYTES) {
    throw new Error('Event exceeds maximum size');
  }
  let event;
  try {
    event = JSON.parse(text);
  } catch {
    throw new Error('Invalid event JSON');
  }
  if (!event || typeof event !== 'object' || Array.isArray(event)) {
    throw new Error('Invalid event object');
  }
  const allowedFields = new Set(['type', 'choice', 'value', 'text', 'id', 'timestamp']);
  for (const field of Object.keys(event)) {
    if (!allowedFields.has(field)) throw new Error(`Unsupported event field: ${field}`);
  }
  if (event.type !== 'click' && event.type !== 'choice') {
    throw new Error('Unsupported event type');
  }
  if (event.timestamp !== undefined
      && (!Number.isSafeInteger(event.timestamp) || event.timestamp < 0)) {
    throw new Error('Invalid timestamp');
  }
  if (event.type === 'click' && event.value !== undefined) {
    throw new Error('Unsupported event field: value');
  }
  if (event.choice !== undefined && event.value !== undefined) {
    throw new Error('Provide one choice value');
  }

  const normalized = {
    type: event.type,
    choice: boundedString(event.choice ?? event.value, 'choice', 128),
  };
  if (event.text !== undefined) normalized.text = boundedString(event.text, 'text', 512);
  if (event.id !== undefined) normalized.id = boundedString(event.id, 'id', 128, { nullable: true });
  normalized.timestamp = timestamp;
  return normalized;
}

function consumeEventAllowance(state, now = Date.now()) {
  const cutoff = now - EVENT_WINDOW_MS;
  state.eventTimes = state.eventTimes.filter(time => time >= cutoff);
  if (state.eventTimes.length >= MAX_EVENTS_PER_WINDOW) return false;
  state.eventTimes.push(now);
  return true;
}

function handleMessage(text, connectionState) {
  if (!consumeEventAllowance(connectionState)) {
    throw new Error('Event rate limit exceeded');
  }
  const event = normalizeEvent(text);
  touchActivity();
  console.log(JSON.stringify({ source: 'user-event', ...event }));
  const eventsFile = path.join(STATE_DIR, 'events');
  fs.appendFileSync(eventsFile, JSON.stringify(event) + '\n', { encoding: 'utf8', mode: 0o600 });
}

function broadcast(msg) {
  const frame = encodeFrame(OPCODES.TEXT, Buffer.from(JSON.stringify(msg)));
  for (const socket of clients) {
    try { socket.write(frame); } catch (e) { clients.delete(socket); }
  }
}

// ========== Activity Tracking ==========

const IDLE_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes
let lastActivity = Date.now();

function touchActivity() {
  lastActivity = Date.now();
}

// ========== File Watching ==========

const debounceTimers = new Map();

// ========== Server Startup ==========

function startServer() {
  if (!fs.existsSync(CONTENT_DIR)) fs.mkdirSync(CONTENT_DIR, { recursive: true, mode: 0o700 });
  if (!fs.existsSync(STATE_DIR)) fs.mkdirSync(STATE_DIR, { recursive: true, mode: 0o700 });
  fs.chmodSync(SESSION_DIR, 0o700);
  fs.chmodSync(CONTENT_DIR, 0o700);
  fs.chmodSync(STATE_DIR, 0o700);

  // Track known files to distinguish new screens from updates.
  // macOS fs.watch reports 'rename' for both new files and overwrites,
  // so we can't rely on eventType alone.
  const knownFiles = new Set(
    fs.readdirSync(CONTENT_DIR).filter(f => f.endsWith('.html'))
  );

  const server = http.createServer(handleRequest);
  server.on('upgrade', handleUpgrade);

  const watcher = fs.watch(CONTENT_DIR, (eventType, filename) => {
    if (!filename || !filename.endsWith('.html')) return;

    if (debounceTimers.has(filename)) clearTimeout(debounceTimers.get(filename));
    debounceTimers.set(filename, setTimeout(() => {
      debounceTimers.delete(filename);
      const filePath = path.join(CONTENT_DIR, filename);

      if (!fs.existsSync(filePath)) return; // file was deleted
      touchActivity();

      if (!knownFiles.has(filename)) {
        knownFiles.add(filename);
        const eventsFile = path.join(STATE_DIR, 'events');
        if (fs.existsSync(eventsFile)) fs.unlinkSync(eventsFile);
        console.log(JSON.stringify({ type: 'screen-added', file: filePath }));
      } else {
        console.log(JSON.stringify({ type: 'screen-updated', file: filePath }));
      }

      broadcast({ type: 'reload' });
    }, 100));
  });
  watcher.on('error', (err) => console.error('fs.watch error:', err.message));

  function shutdown(reason) {
    console.log(JSON.stringify({ type: 'server-stopped', reason }));
    const infoFile = path.join(STATE_DIR, 'server-info');
    if (fs.existsSync(infoFile)) fs.unlinkSync(infoFile);
    fs.writeFileSync(
      path.join(STATE_DIR, 'server-stopped'),
      JSON.stringify({ reason, timestamp: Date.now() }) + '\n',
      { encoding: 'utf8', mode: 0o600 }
    );
    watcher.close();
    clearInterval(lifecycleCheck);
    server.close(() => process.exit(0));
  }

  function ownerAlive() {
    if (!ownerPid) return true;
    try { process.kill(ownerPid, 0); return true; } catch (e) { return e.code === 'EPERM'; }
  }

  // Check every 60s: exit if owner process died or idle for 30 minutes
  const lifecycleCheck = setInterval(() => {
    if (!ownerAlive()) shutdown('owner process exited');
    else if (Date.now() - lastActivity > IDLE_TIMEOUT_MS) shutdown('idle timeout');
  }, 60 * 1000);
  lifecycleCheck.unref();

  // Validate owner PID at startup. If it's already dead, the PID resolution
  // was wrong (common on WSL, Tailscale SSH, and cross-user scenarios).
  // Disable monitoring and rely on the idle timeout instead.
  if (ownerPid) {
    try { process.kill(ownerPid, 0); }
    catch (e) {
      if (e.code !== 'EPERM') {
        console.log(JSON.stringify({ type: 'owner-pid-invalid', pid: ownerPid, reason: 'dead at startup' }));
        ownerPid = null;
      }
    }
  }

  server.listen(PORT, HOST, () => {
    if (!isLoopbackHost(HOST)) {
      console.error(JSON.stringify({
        type: 'security-warning',
        message: 'NON-LOOPBACK BINDING: use TLS and access control through a trusted proxy or tunnel',
      }));
    }
    const info = JSON.stringify({
      type: 'server-started', port: Number(PORT), host: HOST,
      url_host: URL_HOST, origin: SECURITY.primaryOrigin, url: SECURITY.bootstrapUrl,
      screen_dir: CONTENT_DIR, state_dir: STATE_DIR
    });
    console.log(info);
    fs.writeFileSync(path.join(STATE_DIR, 'server-info'), info + '\n', { encoding: 'utf8', mode: 0o600 });
  });
}

if (require.main === module) {
  startServer();
}

module.exports = {
  OPCODES,
  computeAcceptKey,
  consumeEventAllowance,
  createSecurityContext,
  decodeFrame,
  encodeFrame,
  handleRequest,
  normalizeEvent,
  resolveContentPath,
  validateWebSocketRequest,
};
