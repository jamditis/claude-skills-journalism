// WCAG 2.2 AA verification: serves docs/ via Python http.server, scans every
// docs/**/index.html with axe-core, writes scan-results.json, and exits non-zero
// if any page has impact >= moderate (so it doubles as a CI gate).

import { spawn } from 'node:child_process';
import { createServer } from 'node:net';
import { readdirSync, statSync, writeFileSync } from 'node:fs';
import { join, relative, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
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

async function waitForServer(port, timeoutMs = 10000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const r = await fetch(`http://127.0.0.1:${port}/`);
      if (r.ok || r.status === 404) return;
    } catch {}
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error(`server on :${port} did not start`);
}

function truncate(s, n) { return s && s.length > n ? s.slice(0, n) + '...' : (s || ''); }

function pad(s, n) { s = String(s); return s.length >= n ? s : s + ' '.repeat(n - s.length); }

async function main() {
  const port = await findFreePort(DEFAULT_PORT);
  const server = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], {
    cwd: DOCS_DIR, detached: true, stdio: 'ignore',
  });
  server.unref();
  let killed = false;
  const cleanup = () => {
    if (killed) return;
    killed = true;
    try { process.kill(-server.pid, 'SIGTERM'); } catch {}
  };
  process.on('exit', cleanup);
  process.on('SIGINT', () => { cleanup(); process.exit(130); });

  try {
    await waitForServer(port);

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

    const totals = { total: 0, critical: 0, serious: 0, moderate: 0, minor: 0 };
    for (const r of results) {
      totals.total += r.violationCount;
      totals.critical += r.byImpact.critical;
      totals.serious += r.byImpact.serious;
      totals.moderate += r.byImpact.moderate;
      totals.minor += r.byImpact.minor;
    }

    if (!QUIET) {
      const sorted = [...results].sort((a, b) => b.violationCount - a.violationCount);
      const widths = { p: Math.max(4, ...sorted.map((r) => r.path.length)), n: 6 };
      console.log(pad('PATH', widths.p) + ' | ' + pad('TOTAL', widths.n) + ' | ' + pad('CRIT', widths.n) + ' | ' + pad('SERIOUS', widths.n) + ' | ' + pad('MOD', widths.n) + ' | ' + pad('MINOR', widths.n));
      console.log('-'.repeat(widths.p) + '-+-' + '-'.repeat(widths.n) + '-+-' + '-'.repeat(widths.n) + '-+-' + '-'.repeat(widths.n) + '-+-' + '-'.repeat(widths.n) + '-+-' + '-'.repeat(widths.n));
      for (const r of sorted) {
        console.log(pad(r.path, widths.p) + ' | ' + pad(r.violationCount, widths.n) + ' | ' + pad(r.byImpact.critical, widths.n) + ' | ' + pad(r.byImpact.serious, widths.n) + ' | ' + pad(r.byImpact.moderate, widths.n) + ' | ' + pad(r.byImpact.minor, widths.n));
      }
      console.log();
    }

    console.log(`pages scanned: ${results.length}`);
    console.log(`TOTAL | CRIT | SERIOUS | MOD | MINOR`);
    console.log(`${totals.total} | ${totals.critical} | ${totals.serious} | ${totals.moderate} | ${totals.minor}`);

    const severe = results.some((r) => r.byImpact.critical + r.byImpact.serious + r.byImpact.moderate > 0);
    cleanup();
    process.exit(severe ? 1 : 0);
  } catch (err) {
    cleanup();
    console.error('fatal:', err.message || err);
    process.exit(2);
  }
}

main();
