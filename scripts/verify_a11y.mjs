// WCAG 2.2 AA verification: serves docs/ via Python http.server, scans every
// docs/**/index.html with axe-core, writes scan-results.json, and exits non-zero
// if any page has impact >= moderate (so it doubles as a CI gate).

import { spawn } from 'node:child_process';
import { createServer, connect } from 'node:net';
import { readdirSync, statSync, writeFileSync } from 'node:fs';
import { join, relative, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright';
import { AxeBuilder } from '@axe-core/playwright';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');
const DOCS_DIR = join(REPO_ROOT, 'docs');
const RESULTS_PATH = join(__dirname, 'scan-results.json');
const DEFAULT_PORT = 8765;
const QUIET = process.argv.includes('--quiet');
const TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];
const SEVERE_IMPACTS = new Set(['critical', 'serious', 'moderate']);

function findFreePort(start) {
  return new Promise((resolve, reject) => {
    const tryPort = (p) => {
      if (p > start + 100) return reject(new Error('no free port'));
      const srv = createServer();
      srv.once('error', () => tryPort(p + 1));
      srv.once('listening', () => srv.close(() => resolve(p)));
      srv.listen(p, '127.0.0.1');
    };
    tryPort(start);
  });
}

function findIndexes(dir, out = []) {
  for (const ent of readdirSync(dir)) {
    const full = join(dir, ent);
    let st;
    try { st = statSync(full); } catch { continue; }
    if (st.isDirectory()) findIndexes(full, out);
    else if (ent === 'index.html') out.push(full);
  }
  return out;
}

// Readiness probe via a raw TCP connect (node:net), NOT an HTTP fetch. A
// successful connect means the listener is accepting, which is all "ready"
// needs here. The old version used global fetch (undici) and never consumed
// the response body, which parked the keep-alive socket in a paused state;
// undici's later handling of that idle connection intermittently tripped
// `assert(!this.paused)` and crashed the whole run (see issue #121). A connect
// probe has no response body and no connection pool, so that failure class
// cannot occur.
export function waitForPort(port, { host = '127.0.0.1', timeoutMs = 10000, intervalMs = 100 } = {}) {
  const probe = () => new Promise((resolve) => {
    const sock = connect({ port, host });
    const finish = (ok) => { sock.removeAllListeners(); sock.destroy(); resolve(ok); };
    sock.once('connect', () => finish(true));
    sock.once('error', () => finish(false));
    sock.setTimeout(Math.max(250, intervalMs), () => finish(false));
  });
  return (async () => {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      if (await probe()) return;
      await new Promise((r) => setTimeout(r, intervalMs));
    }
    throw new Error(`server on ${host}:${port} did not start within ${timeoutMs}ms`);
  })();
}

function truncate(s, n) { return s && s.length > n ? s.slice(0, n) + '...' : (s || ''); }

function pad(s, n) { s = String(s); return s.length >= n ? s : s + ' '.repeat(n - s.length); }

async function main() {
  const port = await findFreePort(DEFAULT_PORT);
  const server = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], {
    cwd: DOCS_DIR, detached: true, stdio: 'ignore',
  });
  let killed = false;
  const cleanup = () => {
    if (killed) return;
    killed = true;
    try { process.kill(-server.pid, 'SIGTERM'); } catch {}
  };
  // ENOENT or other spawn failures fire 'error' asynchronously. Without this listener,
  // node terminates with an unhandled error and the rest of the script never runs.
  server.on('error', (err) => {
    cleanup();
    console.error(`fatal: failed to spawn python3 (${err.code || 'ERR'}): ${err.message}`);
    console.error('Ensure python3 is installed and on PATH (used to serve docs/ for axe scanning).');
    process.exit(2);
  });
  server.unref();
  process.on('exit', cleanup);
  process.on('SIGINT', () => { cleanup(); process.exit(130); });

  try {
    await waitForPort(port);

    const indexFiles = findIndexes(DOCS_DIR);
    const pages = indexFiles.map((abs) => {
      const rel = relative(DOCS_DIR, abs);
      const dir = rel === 'index.html' ? '' : dirname(rel);
      const url = `http://127.0.0.1:${port}/${dir ? dir + '/' : ''}`;
      return { abs, rel, dir, url };
    }).sort((a, b) => a.rel.localeCompare(b.rel));

    const browser = await chromium.launch();
    const ctx = await browser.newContext();
    const results = [];

    for (const p of pages) {
      const page = await ctx.newPage();
      let entry;
      try {
        await page.goto(p.url, { waitUntil: 'load', timeout: 30000 });
        const ax = await new AxeBuilder({ page }).withTags(TAGS).analyze();
        const byImpact = { critical: 0, serious: 0, moderate: 0, minor: 0 };
        const violations = ax.violations.map((v) => {
          if (v.impact && byImpact[v.impact] !== undefined) byImpact[v.impact] += 1;
          return {
            id: v.id, impact: v.impact, help: v.help, helpUrl: v.helpUrl,
            nodes: v.nodes.map((n) => ({
              html: truncate(n.html, 200),
              target: n.target,
              failureSummary: n.failureSummary || '',
            })),
          };
        });
        entry = { url: p.url, path: p.rel, violationCount: violations.length, byImpact, violations };
      } catch (err) {
        entry = { url: p.url, path: p.rel, violationCount: 0, byImpact: { critical: 0, serious: 0, moderate: 0, minor: 0 }, violations: [], error: String(err.message || err) };
      } finally {
        await page.close();
      }
      results.push(entry);
    }

    await browser.close();

    writeFileSync(RESULTS_PATH, JSON.stringify(results, null, 2));

    const totals = { total: 0, critical: 0, serious: 0, moderate: 0, minor: 0, errors: 0 };
    const errored = [];
    for (const r of results) {
      totals.total += r.violationCount;
      totals.critical += r.byImpact.critical;
      totals.serious += r.byImpact.serious;
      totals.moderate += r.byImpact.moderate;
      totals.minor += r.byImpact.minor;
      if (r.error) {
        totals.errors += 1;
        errored.push(r);
      }
    }

    if (!QUIET) {
      const sorted = [...results].sort((a, b) => (b.error ? 1 : 0) - (a.error ? 1 : 0) || b.violationCount - a.violationCount);
      const widths = { p: Math.max(4, ...sorted.map((r) => r.path.length)), n: 6 };
      console.log(pad('PATH', widths.p) + ' | ' + pad('TOTAL', widths.n) + ' | ' + pad('CRIT', widths.n) + ' | ' + pad('SERIOUS', widths.n) + ' | ' + pad('MOD', widths.n) + ' | ' + pad('MINOR', widths.n) + ' | ' + pad('ERR', widths.n));
      console.log('-'.repeat(widths.p) + '-+-' + '-'.repeat(widths.n) + '-+-' + '-'.repeat(widths.n) + '-+-' + '-'.repeat(widths.n) + '-+-' + '-'.repeat(widths.n) + '-+-' + '-'.repeat(widths.n) + '-+-' + '-'.repeat(widths.n));
      for (const r of sorted) {
        console.log(pad(r.path, widths.p) + ' | ' + pad(r.violationCount, widths.n) + ' | ' + pad(r.byImpact.critical, widths.n) + ' | ' + pad(r.byImpact.serious, widths.n) + ' | ' + pad(r.byImpact.moderate, widths.n) + ' | ' + pad(r.byImpact.minor, widths.n) + ' | ' + pad(r.error ? 'YES' : '0', widths.n));
      }
      console.log();
    }

    if (errored.length) {
      console.error(`scan errors on ${errored.length} page${errored.length === 1 ? '' : 's'}:`);
      for (const r of errored) console.error(`  ${r.path}: ${r.error}`);
    }

    console.log(`pages scanned: ${results.length}`);
    console.log(`TOTAL | CRIT | SERIOUS | MOD | MINOR | ERR`);
    console.log(`${totals.total} | ${totals.critical} | ${totals.serious} | ${totals.moderate} | ${totals.minor} | ${totals.errors}`);

    const severe = results.some((r) => r.byImpact.critical + r.byImpact.serious + r.byImpact.moderate > 0);
    cleanup();
    // Exit 2 when any page failed to scan (a clean a11y report on the others is not
    // a pass, we don't know about the failed pages). Exit 1 for real violations.
    // Exit 0 only when every page scanned cleanly.
    if (errored.length) process.exit(2);
    process.exit(severe ? 1 : 0);
  } catch (err) {
    cleanup();
    console.error('fatal:', err.message || err);
    process.exit(2);
  }
}

// Only run the scan when executed directly (node verify_a11y.mjs). When the
// module is imported, e.g. by verify_a11y.test.mjs to exercise waitForPort,
// importing must not spawn the server or launch a browser.
const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) main();
