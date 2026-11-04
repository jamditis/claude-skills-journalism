import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const PNG_SIGNATURE = '89504e470d0a1a0a';

const marketplace = JSON.parse(readFileSync(join(ROOT, '.claude-plugin/marketplace.json'), 'utf8'));
const plugins = marketplace.plugins.map((plugin) => plugin.source.replace(/^\.\//u, ''));

// The plugin directory warns on ICON_MISSING and accepts only square PNG or
// JPEG icons, 512-2048 px, under 2 MB, at .claude-plugin/icon.png by default.
test('every marketplace plugin ships a valid square PNG icon', () => {
  for (const plugin of plugins) {
    const icon = join(ROOT, plugin, '.claude-plugin/icon.png');
    assert.ok(existsSync(icon), `${plugin}: missing .claude-plugin/icon.png`);
    const bytes = readFileSync(icon);
    assert.equal(bytes.subarray(0, 8).toString('hex'), PNG_SIGNATURE, `${plugin}: not a PNG`);
    const width = bytes.readUInt32BE(16);
    const height = bytes.readUInt32BE(20);
    assert.equal(width, height, `${plugin}: icon is not square`);
    assert.ok(width >= 512 && width <= 2048, `${plugin}: icon is ${width} px`);
    assert.ok(statSync(icon).size < 2 * 1024 * 1024, `${plugin}: icon is over 2 MB`);
  }
});

// An SVG next to the PNG could be picked up by the validator and rejected.
test('plugin icons have an SVG source and no SVG in the manifest folder', () => {
  const sources = new Set(readdirSync(join(ROOT, 'assets/plugin-icons')));
  for (const plugin of plugins) {
    assert.ok(sources.has(`${plugin}.svg`), `${plugin}: missing assets/plugin-icons/${plugin}.svg`);
    assert.ok(!existsSync(join(ROOT, plugin, '.claude-plugin/icon.svg')), `${plugin}: remove icon.svg`);
  }
  for (const source of sources) {
    assert.ok(plugins.includes(source.replace(/\.svg$/u, '')), `${source}: no matching plugin`);
  }
});
