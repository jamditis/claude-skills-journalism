/** Offline rendering/interaction checks; not a production or connector test. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { chromium } from 'playwright';
const root = path.resolve('docs/dot-skills');
const output = process.argv[2] ? path.resolve(process.argv[2]) : fs.mkdtempSync(path.join(os.tmpdir(), 'dot-skills-'));
fs.mkdirSync(output, { recursive: true });
const css = fs.readFileSync(path.join(root, 'style.css'), 'utf8');
const js = fs.readFileSync(path.join(root, 'workshop.js'), 'utf8');
const slugs = ['', 'status-cards', 'incident-updates', 'visual-audits', 'source-evidence', 'rough-edges', 'field-report'];
const browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_EXECUTABLE ? { executablePath: process.env.CHROMIUM_EXECUTABLE } : {}) });
const errors = [];
async function load(page, slug = '') {
  let html = fs.readFileSync(path.join(root, slug, 'index.html'), 'utf8');
  html = html.replace(/<link rel="stylesheet"[^>]+>/, () => `<style>${css}</style>`);
  html = html.replace(/<script src="[^"]+" defer><\/script>/, '');
  html = html.replace('</body>', () => `<script>${js}</script></body>`);
  await page.setContent(html, { waitUntil: 'domcontentloaded' });
}
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  await context.route('**/*', route => route.abort());
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  await load(page);
  await page.waitForTimeout(1400);
  await page.screenshot({ path: path.join(output, 'home-desktop.png'), fullPage: true });
  await page.screenshot({ path: path.join(output, 'home-desktop-top.png') });
  for (const [name, expected] of [['Merged', '50%'], ['Check blocked', '67%'], ['Verified', '100%']]) {
    await page.getByRole('button', { name, exact: true }).click();
    assert.equal(await page.locator('[data-percent]').innerText(), expected);
  }
  const changed = await page.locator('[data-changed]').innerText();
  const checked = await page.locator('[data-checked]').innerText();
  await page.getByRole('button', { name: 'Recheck, no change' }).click();
  assert.notEqual(await page.locator('[data-checked]').innerText(), checked);
  assert.equal(await page.locator('[data-changed]').innerText(), changed);
  const successful = await page.locator('[data-checked]').innerText();
  await page.getByRole('button', { name: 'Try a failed check' }).click();
  assert.equal(await page.locator('[data-checked]').innerText(), successful);
  assert.equal(await page.locator('[data-changed]').innerText(), changed);
  await page.getByRole('button', { name: 'Reset', exact: true }).click();
  assert.equal(await page.locator('[data-percent]').innerText(), '25%');
  for (const width of [1440, 768, 390, 360]) {
    await page.setViewportSize({ width, height: 900 });
    for (const slug of slugs) {
      await load(page, slug);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${slug || 'home'} overflows at ${width}px`);
      if ((width === 390 && ['', 'status-cards', 'rough-edges'].includes(slug)) || (width === 1440 && ['rough-edges', 'field-report'].includes(slug)) || (width === 390 && slug === 'field-report')) {
        await page.waitForTimeout(1400);
        await page.screenshot({ path: path.join(output, `${slug || 'home'}-${width}.png`), fullPage: true });
      }
    }
  }
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await load(page);
  assert.equal(await page.locator('#motion').isDisabled(), true);
  assert.equal(await page.locator('.helper-body').first().evaluate(el => getComputedStyle(el).animationName), 'none');
  await page.getByRole('button', { name: 'Verified', exact: true }).click();
  assert.equal(await page.locator('[data-percent]').innerText(), '100%');
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await page.getByRole('button', { name: 'Pause animations', exact: true }).click();
  assert.equal(await page.locator('html').evaluate(el => el.classList.contains('paused')), true);
  // Real-origin persistence and denied-storage behavior have model tests. about:blank has no persistent origin.
  await load(page, 'status-cards');
  await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async text => { window.copiedPrompt = text; } } }));
  await page.getByRole('button', { name: 'Copy the starter prompt' }).click();
  assert.equal(await page.evaluate(() => window.copiedPrompt), await page.locator('textarea').inputValue());
  await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async () => { throw Error('denied'); } } }));
  await page.getByRole('button', { name: 'Copy the starter prompt' }).click();
  assert.match(await page.locator('.copy-status').innerText(), /Automatic copy was unavailable/);
  assert.equal(await page.locator('textarea').evaluate(el => el.selectionEnd - el.selectionStart), (await page.locator('textarea').inputValue()).length);
  await load(page);
  await page.locator('.skip').focus();
  await page.keyboard.press('Enter');
  assert.equal(await page.evaluate(() => document.activeElement.id), 'main');
  const noJS = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 900 } });
  await noJS.route('**/*', route => route.abort());
  const staticPage = await noJS.newPage();
  await load(staticPage, 'status-cards');
  assert.equal(await staticPage.getByRole('link', { name: 'Download the playbook' }).isVisible(), true);
  assert.equal(await staticPage.locator('textarea').isVisible(), true);
  assert.equal(await staticPage.locator('[data-copy]').isVisible(), false);
  assert.equal(await staticPage.locator('[data-percent]').innerText(), '25%');
  await page.setViewportSize({ width: 1440, height: 1000 });
  await load(page, 'field-report');
  for (let click = 0; click < 4; click += 1) {
    await page.locator('[data-approval-loop] button').nth(click % 3).click();
    assert.match(await page.locator('[data-approval-prompt]').innerText(), /Allow again\?$/);
  }
  await page.locator('[data-approval-loop] button').first().focus();
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('[data-approval-prompt]').innerText(), 'Approved. For now.');
  assert.equal(await page.evaluate(() => document.activeElement.hasAttribute('data-approval-prompt')), true);
  assert.equal(await page.locator('[data-approval-loop] button').first().isDisabled(), true);
  assert.equal(await page.locator('[data-sleepy-dot]').evaluate(el => el.classList.contains('is-awake')), true);
  await page.screenshot({ path: path.join(output, 'field-report-easter-egg.png') });
  await page.locator('[data-poke="wyndle"]').click({ force: true });
  assert.match(await page.locator('[data-poke-bubble]').innerText(), /^Wyndle: /);
  for (let poke = 0; poke < 9; poke += 1) await page.locator('[data-poke="wyndle"]').click({ force: true });
  await page.waitForTimeout(2700);
  assert.equal(await page.locator('[data-poke="syl"] svg').evaluate(el => el.classList.contains('is-dazed')), true);
  await page.screenshot({ path: path.join(output, 'field-report-fight.png') });
  await page.keyboard.type('allow');
  assert.ok(await page.locator('.approval-rain').count() > 0);
  await page.keyboard.type('devil');
  assert.equal(await page.locator('.jersey-devil').count(), 1);
  await page.getByRole('button', { name: 'Pause animations', exact: true }).click();
  await page.waitForTimeout(150);
  assert.equal(await page.locator('.jersey-devil, .approval-rain, .projectile').count(), 0, 'paused motion must stop running egg animations');
  const staticReport = await noJS.newPage();
  await load(staticReport, 'field-report');
  assert.equal(await staticReport.locator('[data-approval-loop] button').first().isVisible(), false);
  assert.equal(await staticReport.locator('video').isVisible(), true);
  assert.deepEqual(errors, []);
  console.log('Passed: 28 page/viewport combinations, the field report approval loop, pokes, the fight, typed eggs, scenario transitions, two clocks, failed retrieval, reset, reduced motion, manual pause, clipboard success/failure, keyboard skip link, and no-JavaScript content.');
  console.log(`Offline screenshots: ${output}`);
  console.log('External requests blocked. Font fallbacks rendered. This does not test deployment, dot imports, live Slack delivery, or VM recovery.');
} finally {
  await browser.close();
}
