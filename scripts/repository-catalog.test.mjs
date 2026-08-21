import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';
import { parse } from 'yaml';

import {
  ROOT,
  findSkillFiles,
  loadCatalog,
  normalizeRepositoryPath,
  validateCatalog,
} from './repository-catalog.mjs';

test('the catalog covers each skill and its Codex UI metadata', () => {
  const catalog = loadCatalog();
  const errors = validateCatalog(catalog);

  assert.deepEqual(errors, []);
  assert.equal(catalog.schema_version, 1);
  assert.equal(catalog.skills.length, findSkillFiles().length);

  for (const skill of catalog.skills) {
    const metadataPath = join(ROOT, skill.path, 'agents', 'openai.yaml');
    assert.ok(existsSync(metadataPath), `${skill.path}: missing agents/openai.yaml`);

    const metadata = parse(readFileSync(metadataPath, 'utf8'));
    assert.deepEqual(Object.keys(metadata), ['interface']);
    assert.match(metadata.interface.display_name, /\S/u);
    assert.match(metadata.interface.short_description, /\S/u);
    assert.ok(
      metadata.interface.short_description.length <= 80,
      `${skill.path}: short_description exceeds 80 characters`,
    );
  }
});

test('the catalog validator rejects missing, duplicate, and unsafe skill entries', () => {
  const missing = structuredClone(loadCatalog());
  const removed = missing.skills.pop();
  assert.ok(
    validateCatalog(missing).includes(`${removed.path}: skill is missing from catalog`),
  );

  const duplicate = structuredClone(loadCatalog());
  duplicate.skills[1].name = duplicate.skills[0].name;
  assert.ok(
    validateCatalog(duplicate).some((error) => error.includes('duplicate or missing skill name')),
  );

  const unsafe = structuredClone(loadCatalog());
  unsafe.skills[0].path = '../outside';
  assert.ok(
    validateCatalog(unsafe).includes('../outside: path must stay inside the repository'),
  );
});

test('repository catalog paths use forward slashes on Windows-style input', () => {
  assert.equal(
    normalizeRepositoryPath('journalism-core\\skills\\source-verification'),
    'journalism-core/skills/source-verification',
  );
});

test('skill lint watches and directly validates repository catalog inputs', () => {
  const workflow = readFileSync(join(ROOT, '.github', 'workflows', 'skill-lint.yml'), 'utf8');
  for (const path of [
    'skills-catalog.yaml',
    'scripts/fixtures/**',
    'docs/skill-behavior-evaluations.md',
  ]) {
    assert.match(workflow, new RegExp(`- '${path.replaceAll('*', '\\*')}'`, 'u'));
  }
  assert.match(workflow, /lint-skills:[\s\S]*?run: npm ci[\s\S]*?name: Validate repository catalog/u);
  assert.match(workflow, /name: Validate repository catalog\s+run: npm run validate:catalog/u);
});

test('root package metadata matches the public repository', () => {
  const packageData = JSON.parse(readFileSync(join(ROOT, 'package.json'), 'utf8'));
  const lockData = JSON.parse(readFileSync(join(ROOT, 'package-lock.json'), 'utf8'));
  const marketplace = JSON.parse(
    readFileSync(join(ROOT, '.claude-plugin', 'marketplace.json'), 'utf8'),
  );

  assert.equal(packageData.version, marketplace.version);
  assert.equal(lockData.version, marketplace.version);
  assert.equal(lockData.packages[''].version, marketplace.version);
  assert.equal(packageData.license, 'MIT');
  assert.equal(lockData.packages[''].license, 'MIT');
  assert.equal(packageData.author, 'Joe Amditis');
  assert.equal(
    packageData.repository.url,
    'git+https://github.com/jamditis/claude-skills-journalism.git',
  );
});

test('repository influence records identify the exact upstream source and license', () => {
  for (const path of ['INFLUENCES.md', 'THIRD_PARTY_NOTICES.md']) {
    const source = readFileSync(join(ROOT, path), 'utf8');
    assert.match(source, /mattpocock\/skills/u);
    assert.match(source, /5b15a47f2d7150f545fbcacbfe381787fc0230dc/u);
    assert.match(source, /MIT/u);
  }
});
