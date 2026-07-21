import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import test from 'node:test';

const require = createRequire(import.meta.url);
const TOKEN = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFG';
process.env.BRAINSTORM_HOST = '127.0.0.1';
process.env.BRAINSTORM_PORT = '54321';
process.env.BRAINSTORM_TOKEN = TOKEN;
process.env.BRAINSTORM_URL_HOST = 'localhost';
const {
  consumeEventAllowance,
  createSecurityContext,
  decodeFrame,
  handleRequest,
  normalizeEvent,
  resolveContentPath,
  validateWebSocketRequest,
} = require('../superjawn/skills/brainstorming/scripts/server.cjs');

const KEY = Buffer.alloc(16, 7).toString('base64');

function responseRecorder() {
  return {
    body: null,
    headers: null,
    status: null,
    end(body) { this.body = body; },
    writeHead(status, headers) { this.status = status; this.headers = headers; },
  };
}

function websocketRequest(cookieName, overrides = {}) {
  return {
    method: 'GET',
    url: '/',
    headers: {
      host: 'localhost:54321',
      origin: 'http://localhost:54321',
      cookie: `${cookieName}=${TOKEN}`,
      upgrade: 'websocket',
      connection: 'Upgrade',
      'sec-websocket-version': '13',
      'sec-websocket-key': KEY,
      ...overrides,
    },
  };
}

test('WebSocket validation requires the expected origin, host, and capability', () => {
  const security = createSecurityContext({
    host: '127.0.0.1',
    port: 54321,
    sessionToken: TOKEN,
    urlHost: 'localhost',
  });
  const parallelSession = createSecurityContext({
    host: '127.0.0.1',
    port: 54322,
    sessionToken: 'abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG',
    urlHost: 'localhost',
  });
  assert.notEqual(security.cookieName, parallelSession.cookieName);
  assert.throws(() => createSecurityContext({
    host: '127.0.0.1',
    port: 54321,
    sessionToken: `${'x'.repeat(43)}\r\n`,
    urlHost: 'localhost',
  }), /base64url/i);
  assert.throws(() => createSecurityContext({
    host: '0.0.0.0',
    port: 54321,
    sessionToken: TOKEN,
    urlHost: '192.0.2.10',
  }), /must use HTTPS/i);

  assert.deepEqual(validateWebSocketRequest(websocketRequest(security.cookieName), security), { ok: true });
  assert.equal(
    validateWebSocketRequest(websocketRequest(security.cookieName, { origin: 'http://attacker.example' }), security).status,
    403,
  );
  assert.equal(
    validateWebSocketRequest(websocketRequest(security.cookieName, { host: 'attacker.example' }), security).status,
    403,
  );
  assert.equal(
    validateWebSocketRequest(websocketRequest(security.cookieName, { cookie: '' }), security).status,
    401,
  );
  assert.equal(validateWebSocketRequest({ ...websocketRequest(security.cookieName), url: '/control' }, security).status, 400);
});

test('HTTP bootstrap requires the capability and exchanges it for a hardened cookie', () => {
  const denied = responseRecorder();
  handleRequest({ method: 'GET', url: '/', headers: { host: 'localhost:54321' } }, denied);
  assert.equal(denied.status, 401);

  const bootstrapped = responseRecorder();
  handleRequest({
    method: 'GET',
    url: `/?token=${TOKEN}`,
    headers: { host: 'localhost:54321' },
  }, bootstrapped);
  assert.equal(bootstrapped.status, 303);
  assert.equal(bootstrapped.headers.Location, '/');
  assert.match(bootstrapped.headers['Set-Cookie'], /HttpOnly/);
  assert.match(bootstrapped.headers['Set-Cookie'], /SameSite=Strict/);
  assert.doesNotMatch(bootstrapped.headers.Location, /token/);
});

test('frame decoder rejects malformed, fragmented, and oversized client frames', () => {
  assert.throws(
    () => decodeFrame(Buffer.from([0x81, 0x01, 0x41])),
    /masked/i,
  );
  assert.throws(
    () => decodeFrame(Buffer.from([0x01, 0x80, 0, 0, 0, 0])),
    /fragment/i,
  );

  const oversizedHeader = Buffer.alloc(8);
  oversizedHeader[0] = 0x81;
  oversizedHeader[1] = 0x80 | 126;
  oversizedHeader.writeUInt16BE(8193, 2);
  assert.throws(() => decodeFrame(oversizedHeader), /maximum/i);
});

test('event validation allowlists persisted fields and bounds attacker-controlled text', () => {
  assert.deepEqual(
    normalizeEvent(JSON.stringify({
      type: 'click',
      choice: 'layout-a',
      text: 'Layout A',
      id: 'choice-a',
      timestamp: 1,
    }), 1700000000000),
    {
      type: 'click',
      choice: 'layout-a',
      text: 'Layout A',
      id: 'choice-a',
      timestamp: 1700000000000,
    },
  );

  assert.throws(
    () => normalizeEvent(JSON.stringify({ type: 'reload', choice: 'x' })),
    /type/i,
  );
  assert.throws(
    () => normalizeEvent(JSON.stringify({ type: 'click', choice: 'x', injected: true })),
    /field/i,
  );
  assert.throws(
    () => normalizeEvent(JSON.stringify({ type: 'click', choice: 'x'.repeat(129) })),
    /choice/i,
  );
  assert.throws(
    () => normalizeEvent('x'.repeat(4097)),
    /size/i,
  );
});

test('event rate limiter caps each WebSocket independently', () => {
  const state = { eventTimes: [] };
  for (let i = 0; i < 30; i += 1) {
    assert.equal(consumeEventAllowance(state, 1000 + i), true);
  }
  assert.equal(consumeEventAllowance(state, 1030), false);
  assert.equal(consumeEventAllowance(state, 12001), true);
});

test('file resolver accepts one regular basename and rejects traversal or symlink escape', () => {
  const root = mkdtempSync(path.join(tmpdir(), 'brainstorm-security-'));
  const content = path.join(root, 'content');
  const outside = path.join(root, 'outside.txt');
  try {
    mkdirSync(content);
    writeFileSync(path.join(content, 'safe.html'), '<p>safe</p>');
    writeFileSync(outside, 'secret');
    symlinkSync(outside, path.join(content, 'escape.html'));

    assert.equal(resolveContentPath('/files/safe.html', content), path.join(content, 'safe.html'));
    assert.equal(resolveContentPath('/files/../outside.txt', content), null);
    assert.equal(resolveContentPath('/files/%2e%2e%2foutside.txt', content), null);
    assert.equal(resolveContentPath('/files/..%5coutside.txt', content), null);
    assert.equal(resolveContentPath('/files/escape.html', content), null);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('remote-binding documentation requires TLS and trusted access control', () => {
  const guide = readFileSync(
    new URL('../superjawn/skills/brainstorming/visual-companion.md', import.meta.url),
    'utf8',
  );
  assert.match(guide, /Remote exposure requires TLS/i);
  assert.match(guide, /wss:\/\//i);
  assert.match(guide, /access control through a trusted reverse proxy or authenticated tunnel/i);
});
