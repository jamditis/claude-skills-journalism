import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { parse } from 'yaml';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const SKIP_DIRS = new Set(['.git', '.agents', 'node_modules']);

function findSkillFiles(dir = ROOT, files = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.isDirectory() && SKIP_DIRS.has(entry.name)) continue;
    const path = join(dir, entry.name);
    if (entry.isDirectory()) findSkillFiles(path, files);
    else if (entry.isFile() && entry.name === 'SKILL.md') files.push(path);
  }
  return files;
}

test('every SKILL.md has parseable YAML frontmatter required for CLI discovery', () => {
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

    if (typeof data.name === 'string' && data.name.trim()) {
      const existing = names.get(data.name);
      if (existing) errors.push(`${displayPath}: duplicate skill name ${data.name} (also ${existing})`);
      else names.set(data.name, displayPath);
    }
  }

  assert.deepEqual(errors, []);
});
