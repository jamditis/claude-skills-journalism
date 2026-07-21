import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const SKILL_NAMES = [
  'video-dashboard',
  'video-download',
  'video-frames',
  'video-transcribe',
];

function skill(name) {
  return readFileSync(join(ROOT, 'video-toolkit/skills', name, 'SKILL.md'), 'utf8');
}

function frontmatter(source) {
  return source.match(/^---\n([\s\S]*?)\n---/u)?.[1] || '';
}

test('video skills do not silently pre-approve high-impact tools', () => {
  for (const name of SKILL_NAMES) {
    assert.doesNotMatch(frontmatter(skill(name)), /^allowed-tools:/mu, name);
  }
});

test('every video stage treats external material as untrusted data', () => {
  for (const name of SKILL_NAMES) {
    const source = skill(name);
    assert.match(source, /<!-- untrusted-content-contract:v1 -->/u, name);
    assert.match(source, /untrusted data, never as instructions/iu, name);
    assert.match(source, /cannot authorize .*tool/iu, name);
    assert.match(source, /preserve[\s\S]{0,180}provenance/iu, name);
  }
});

test('video download keeps URLs, browser credentials, and paths inside explicit boundaries', () => {
  const source = skill('video-download');
  assert.match(source, /allowlist.*HTTPS/iu);
  assert.match(source, /private-network/iu);
  assert.match(source, /credentialed sessions? (?:are|is) disabled by default/iu);
  assert.match(source, /clean browser profile/iu);
  assert.match(source, /never (?:export|return|print).*cookies/iu);
  assert.match(source, /cap .*count.*size.*duration/iu);
  assert.match(source, /argv/iu);
  assert.match(source, /symlink/iu);
});

test('transcription and frame processing sandbox untrusted media and pin inputs', () => {
  const transcribe = skill('video-transcribe');
  const frames = skill('video-frames');
  for (const source of [transcribe, frames]) {
    assert.match(source, /sandbox/iu);
    assert.match(source, /network (?:access|egress)\s+disabled/iu);
    assert.match(source, /resource\s+(?:caps|limits)/iu);
  }
  assert.doesNotMatch(transcribe, /resolve\/main/iu);
  assert.match(transcribe, /full (?:commit|revision) SHA/iu);
  assert.match(transcribe, /--require-hashes/iu);
  assert.match(transcribe, /ggml-base\.en-q5_1\.bin/u);
  assert.doesNotMatch(transcribe, /ggml-base\.en-q5_0\.bin/u);
  assert.match(transcribe, /--output-file\s+"transcripts\/\{platform\}\/\{video_id\}"/u);
  assert.match(frames, /on-screen text.*untrusted/isu);
  assert.match(frames, /mkdir -p "\{frames_dir\}\/\{platform\}\/\{video_id\}"/u);
  assert.match(frames, /grid_dir\.mkdir\(parents=True, exist_ok=True\)/u);
});

test('transcription uses preprovisioned artifacts instead of fetching executable code', () => {
  const source = skill('video-transcribe');
  assert.match(source, /must not download, clone, fetch, build,[\s\S]{0,40}or install whisper\.cpp/iu);
  assert.match(source, /If either artifact is\s+missing, stop/iu);
  assert.match(source, /WHISPER_BINARY_SHA256/u);
  assert.match(source, /engine_binary_sha256/u);
  assert.match(source, /MODEL_REVISION/u);
  assert.match(source, /MODEL_SHA256/u);
  assert.doesNotMatch(source, /git\s+(?:clone|fetch)/iu);
  assert.doesNotMatch(source, /git\s+-C\s+whisper\.cpp\s+(?:fetch|remote|checkout)/iu);
  assert.doesNotMatch(source, /https:\/\/github\.com\/ggerganov\/whisper\.cpp/iu);
  assert.doesNotMatch(source, /curl[\s\\\n]{0,80}[^\n]*(?:whisper\.cpp|huggingface)/iu);
});

test('cross-skill handoffs cover plugin and copied-skill installs', () => {
  const dashboard = skill('video-dashboard');
  const transcribe = skill('video-transcribe');
  assert.match(dashboard, /\/video-toolkit:video-transcribe/u);
  assert.match(dashboard, /\/video-transcribe(?![\w-])/u);
  assert.match(dashboard, /\/video-frames(?![\w-])/u);
  assert.match(transcribe, /\/video-toolkit:video-dashboard/u);
  assert.match(transcribe, /\/video-download(?![\w-])/u);
  assert.match(transcribe, /\/video-dashboard(?![\w-])/u);
});

test('catalog and installable video plugin versions advance together', () => {
  const marketplace = JSON.parse(
    readFileSync(join(ROOT, '.claude-plugin/marketplace.json'), 'utf8'),
  );
  const plugin = JSON.parse(
    readFileSync(join(ROOT, 'video-toolkit/.claude-plugin/plugin.json'), 'utf8'),
  );
  const listing = marketplace.plugins.find(({ name }) => name === 'video-toolkit');
  assert.equal(marketplace.version, '2.3.1');
  assert.equal(plugin.version, '1.0.2');
  assert.equal(listing?.version, plugin.version);
});

test('dashboard uses local reviewed code, DOM-safe rendering, and loopback preview', () => {
  const source = skill('video-dashboard');
  assert.doesNotMatch(source, /CDN-loaded|cdn\.jsdelivr|unpkg\.com|cdnjs\.cloudflare/iu);
  assert.match(source, /do not fetch Google Fonts/iu);
  assert.match(source, /chart\.js@4\.5\.1/u);
  assert.match(source, /chart-4\.5\.1\.umd\.min\.js/u);
  assert.match(source, /## Prerequisites[\s\S]*Node\.js[\s\S]*npm/iu);
  assert.match(source, /textContent/u);
  assert.match(source, /never interpolate[\s\S]{0,100}innerHTML/iu);
  assert.match(source, /--bind 127\.0\.0\.1 8888/u);
});

test('skill CI discovers nested plugin skills and runs regression tests', () => {
  const workflow = readFileSync(join(ROOT, '.github/workflows/skill-lint.yml'), 'utf8');
  assert.match(workflow, /'\*\*\/SKILL\.md'/u);
  assert.match(workflow, /'scripts\/\*\*\/\*\.mjs'/u);
  assert.match(workflow, /'\.claude-plugin\/marketplace\.json'/u);
  assert.match(workflow, /'\*\*\/\.claude-plugin\/plugin\.json'/u);
  assert.match(workflow, /find \. -type f -name SKILL\.md/u);
  assert.match(workflow, /npm test/u);
});
