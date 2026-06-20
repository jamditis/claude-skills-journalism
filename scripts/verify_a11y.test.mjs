// Tests for the readiness probe in verify_a11y.mjs (run: `npm test`).
//
// Regression coverage for issue #121: the old readiness check used global fetch
// (undici) and left the response body unconsumed, which intermittently crashed
// the run with `assert(!this.paused)`. waitForPort uses a raw TCP connect — no
// body, no connection pool — so that failure class is gone. These tests pin the
// probe's contract and stress the path that used to crash.
//
// They deliberately never free a local port and reuse it: that races the OS
// port allocator. Live cases hold their server open for the whole test; the
// "down" case targets port 0 on loopback, which can never have a listener, so
// connect() always fails locally with no routing and nothing to reassign.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { waitForPort } from './verify_a11y.mjs';

const HOST = '127.0.0.1';

function canBindLoopback() {
  return new Promise((resolve) => {
    const s = createServer();
    s.once('error', () => resolve(false));
    s.listen(0, HOST, () => s.close(() => resolve(true)));
  });
}

// Some restricted sandboxes forbid binding a loopback listener (listen EPERM).
// A real a11y run always has loopback (the gate serves docs/ on 127.0.0.1), but
// `npm test` may run in such a sandbox. Mirror test_embed.py's
// skip-when-prerequisite-missing pattern: probe once, skip the listener-based
// tests rather than hard-failing the suite. The "down" test only connects, so
// it still runs.
const noBind = (await canBindLoopback()) ? false : 'loopback binding unavailable in this environment';

function listenHttp() {
  const server = createServer((req, res) => res.end('ok'));
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, HOST, () => resolve({ server, port: server.address().port }));
  });
}

function closeServer(server) {
  return new Promise((resolve) => server.close(resolve));
}

test('resolves once the server is accepting connections', { skip: noBind }, async () => {
  const { server, port } = await listenHttp();
  try {
    await waitForPort(port, { timeoutMs: 2000, intervalMs: 25 });
  } finally {
    await closeServer(server);
  }
});

test('rejects when the target never accepts', async () => {
  // Port 0 on loopback is the deterministic "always refused" target: nothing
  // can ever listen on port 0 (listen(0) means "auto-assign", the bound port is
  // never literally 0), so connect() fails immediately and locally with no
  // routing involved and no port the OS could reassign. Every probe fails, so
  // waitForPort must exhaust its deadline and throw.
  await assert.rejects(
    () => waitForPort(0, { host: HOST, timeoutMs: 300, intervalMs: 50 }),
    /did not start/,
  );
});

test('stress: 250 sequential probes never crash (undici-free readiness path)', { skip: noBind }, async () => {
  const { server, port } = await listenHttp();
  try {
    for (let i = 0; i < 250; i++) {
      await waitForPort(port, { timeoutMs: 1000, intervalMs: 25 });
    }
  } finally {
    await closeServer(server);
  }
});
