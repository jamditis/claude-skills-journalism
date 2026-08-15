import assert from 'node:assert/strict';
import { existsSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const DOCS = join(ROOT, 'docs');
const PAGE = join(DOCS, 'video-toolkit', 'index.html');
const STYLESHEET = join(DOCS, 'assets', 'tailwind', 'video-toolkit.css');

test('video toolkit docs explain the four-stage reporting pipeline and its boundaries', () => {
  assert.equal(existsSync(PAGE), true, 'docs/video-toolkit/index.html is missing');
  const page = readFileSync(PAGE, 'utf8');

  assert.match(
    page,
    /<link rel="stylesheet" href="\.\.\/assets\/tailwind\/video-toolkit\.css" data-tailwind-build="3\.4\.19">/u,
  );
  assert.doesNotMatch(page, /cdn\.tailwindcss\.com|\btailwind\.config\s*=/u);
  assert.match(page, /Plugin · v1\.0\.3/u);
  assert.match(page, /\/plugin install video-toolkit@claude-skills-journalism/u);
  assert.match(page, /data-updated-slug="video-toolkit"/u);

  for (const skill of ['video-download', 'video-transcribe', 'video-frames', 'video-dashboard']) {
    assert.match(page, new RegExp(`\\b${skill}\\b`, 'u'));
  }

  assert.match(page, /untrusted data/iu);
  assert.match(page, /explicit user approval/iu);
  assert.match(page, /private-network access blocked/iu);
  assert.match(page, /exact Chart\.js asset/iu);
  assert.match(page, /provenance sidecar/iu);
  assert.match(page, /Node\.js[\s\S]*npm/iu);
});

test('homepage lists video toolkit once, before visual explainer, with accurate counts', () => {
  const index = readFileSync(join(DOCS, 'index.html'), 'utf8');

  assert.match(index, />62 Skills \/\/ 12 Plugins \/\/ 17 Hooks</u);
  assert.match(index, /id="finder-count">62 skills, 12 plugins</u);
  assert.match(index, />12 Plugins<\/span>/u);
  assert.equal((index.match(/href="video-toolkit\/"/gu) || []).length, 1);

  const pluginsStart = index.indexOf('<!-- Plugins -->');
  const nextSection = index.indexOf('<!-- Core Journalism Skills -->', pluginsStart);
  const plugins = index.slice(pluginsStart, nextSection);
  const video = plugins.indexOf('href="video-toolkit/"');
  const visual = plugins.indexOf('href="visual-explainer/"');
  assert.ok(video >= 0, 'video-toolkit plugin card is missing');
  assert.ok(video < visual, 'video-toolkit card must appear before visual-explainer');

  const videoCard = plugins.slice(video, plugins.indexOf('</a>', video));
  assert.match(videoCard, /data-updated-slug="video-toolkit"/u);
  assert.match(
    videoCard,
    /data-keywords="[^"]*video-download[^"]*video-transcribe[^"]*video-frames[^"]*video-dashboard[^"]*"/u,
  );
});

test('video toolkit page is part of the pinned Tailwind build', () => {
  const manifest = JSON.parse(readFileSync(join(DOCS, 'tailwind-pages.json'), 'utf8'));
  assert.ok(manifest['video-toolkit/index.html']);
  assert.equal(existsSync(STYLESHEET), true, 'generated video-toolkit.css is missing');
  assert.ok(statSync(STYLESHEET).size > 1000, 'generated video-toolkit.css is unexpectedly small');
});
