import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { basename, dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { parse } from 'yaml';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const SKIP_DIRS = new Set(['.git', '.agents', 'node_modules']);
const ALLOWED_FIELDS = new Set([
  'name',
  'description',
  'license',
  'compatibility',
  'metadata',
  'allowed-tools',
  'disable-model-invocation',
]);
const NAME_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/u;

function findSkillFiles(dir = ROOT, files = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.isDirectory() && SKIP_DIRS.has(entry.name)) continue;
    const path = join(dir, entry.name);
    if (entry.isDirectory()) findSkillFiles(path, files);
    else if (entry.isFile() && entry.name === 'SKILL.md') files.push(path);
  }
  return files;
}

test('every SKILL.md follows the repository frontmatter contract', () => {
  const files = findSkillFiles().sort();
  const names = new Map();
  const errors = [];

  assert.ok(files.length > 0, 'expected at least one SKILL.md');

  for (const path of files) {
    const displayPath = relative(ROOT, path);
    const source = readFileSync(path, 'utf8');
    const match = source.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/u);
    if (!match) {
      errors.push(`${displayPath}: missing complete YAML frontmatter`);
      continue;
    }

    let data;
    try {
      data = parse(match[1]);
    } catch (error) {
      errors.push(`${displayPath}: ${error.message}`);
      continue;
    }

    if (!data || typeof data !== 'object' || Array.isArray(data)) {
      errors.push(`${displayPath}: frontmatter must be a YAML mapping`);
      continue;
    }
    for (const field of ['name', 'description']) {
      if (typeof data[field] !== 'string' || !data[field].trim()) {
        errors.push(`${displayPath}: ${field} must be a non-empty string`);
      }
    }

    const unexpected = Object.keys(data).filter((field) => !ALLOWED_FIELDS.has(field)).sort();
    if (unexpected.length > 0) {
      errors.push(`${displayPath}: unexpected frontmatter field(s): ${unexpected.join(', ')}`);
    }

    if (typeof data.name === 'string' && data.name.trim()) {
      if (data.name.length > 64) errors.push(`${displayPath}: name must be at most 64 characters`);
      if (!NAME_PATTERN.test(data.name)) {
        errors.push(`${displayPath}: name must use lowercase letters, digits, and single hyphens`);
      }
      const directoryName = basename(dirname(path));
      if (data.name !== directoryName) {
        errors.push(`${displayPath}: name must match directory ${directoryName}`);
      }
      const existing = names.get(data.name);
      if (existing) errors.push(`${displayPath}: duplicate skill name ${data.name} (also ${existing})`);
      else names.set(data.name, displayPath);
    }

    if (typeof data.description === 'string' && data.description.length > 1024) {
      errors.push(`${displayPath}: description must be at most 1024 characters`);
    }
    for (const field of ['license', 'compatibility']) {
      if (field in data && (typeof data[field] !== 'string' || !data[field].trim())) {
        errors.push(`${displayPath}: ${field} must be a non-empty string`);
      }
    }
    if (typeof data.compatibility === 'string' && data.compatibility.length > 500) {
      errors.push(`${displayPath}: compatibility must be at most 500 characters`);
    }
    if ('allowed-tools' in data && typeof data['allowed-tools'] !== 'string') {
      errors.push(`${displayPath}: allowed-tools must be a string`);
    }
    if (
      'disable-model-invocation' in data
      && typeof data['disable-model-invocation'] !== 'boolean'
    ) {
      errors.push(`${displayPath}: disable-model-invocation must be a boolean`);
    }
    if ('metadata' in data) {
      const metadata = data.metadata;
      if (!metadata || typeof metadata !== 'object' || Array.isArray(metadata)) {
        errors.push(`${displayPath}: metadata must be a mapping`);
      } else {
        for (const [key, value] of Object.entries(metadata)) {
          if (typeof key !== 'string' || typeof value !== 'string') {
            errors.push(`${displayPath}: metadata keys and values must be strings`);
            break;
          }
        }
      }
    }
  }

  assert.deepEqual(errors, []);
});

test('published package versions stay aligned with the marketplace', () => {
  const marketplace = JSON.parse(
    readFileSync(join(ROOT, '.claude-plugin', 'marketplace.json'), 'utf8'),
  );
  assert.equal(marketplace.version, '2.5.0', 'marketplace version');
  const expected = new Map([
    ['autocontext', '1.1.1'],
    ['dev-toolkit', '1.3.0'],
    ['journalism-core', '1.4.1'],
    ['okf-wiki', '0.8.2'],
    ['pdf-design', '1.1.2'],
    ['pdf-playground', '1.3.4'],
    ['project-templates-toolkit', '1.0.2'],
    ['research-toolkit', '1.1.2'],
    ['security-toolkit', '1.2.2'],
    ['superjawn', '1.0.2'],
    ['video-toolkit', '1.0.5'],
    ['visual-explainer', '0.7.3'],
  ]);

  for (const [name, version] of expected) {
    const manifest = JSON.parse(
      readFileSync(join(ROOT, name, '.claude-plugin', 'plugin.json'), 'utf8'),
    );
    const listing = marketplace.plugins.find((plugin) => plugin.name === name);
    assert.equal(manifest.version, version, `${name} manifest version`);
    assert.equal(listing?.version, version, `${name} marketplace version`);

    const rootSkillPath = join(ROOT, name, 'SKILL.md');
    if (existsSync(rootSkillPath)) {
      const source = readFileSync(rootSkillPath, 'utf8');
      const match = source.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/u);
      assert.ok(match, `${name} root skill frontmatter`);
      const skill = parse(match[1]);
      if (skill.metadata?.version) {
        assert.equal(skill.metadata.version, version, `${name} root skill version`);
      }
    }
  }
});
