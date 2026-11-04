// Renders assets/plugin-icons/<plugin>.svg to <plugin>/.claude-plugin/icon.png.
//
// The plugin directory accepts only square PNG or JPEG icons (512-2048 px,
// under 2 MB) and locks a plugin's icon the first time it is saved or
// submitted in the developer portal, so edit the SVG source, re-render, and
// review the PNG before that first submission.
//
// Usage: node scripts/render-plugin-icons.mjs [plugin ...]
// Set CHROMIUM_PATH to use a Chromium other than Playwright's own download.

import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const SOURCES = join(ROOT, 'assets/plugin-icons');
const SIZE = 1024;

const requested = process.argv.slice(2);
const plugins = (requested.length ? requested.map((name) => `${name}.svg`) : readdirSync(SOURCES))
  .filter((file) => file.endsWith('.svg'))
  .map((file) => basename(file, '.svg'));

const browser = await chromium.launch(
  process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
);
const page = await browser.newPage({ viewport: { width: SIZE, height: SIZE }, deviceScaleFactor: 1 });
let failed = false;
for (const plugin of plugins) {
  const manifestDir = join(ROOT, plugin, '.claude-plugin');
  if (!existsSync(join(manifestDir, 'plugin.json'))) {
    console.error(`${plugin}: no plugin.json, skipped`);
    failed = true;
    continue;
  }
  const svg = readFileSync(join(SOURCES, `${plugin}.svg`), 'utf8');
  await page.setContent(
    `<!doctype html><style>html,body{margin:0}svg{display:block;width:${SIZE}px;height:${SIZE}px}</style>${svg}`,
  );
  await page.locator('svg').screenshot({ path: join(manifestDir, 'icon.png'), omitBackground: false });
  console.log(`${plugin}/.claude-plugin/icon.png`);
}
await browser.close();
process.exit(failed ? 1 : 0);
