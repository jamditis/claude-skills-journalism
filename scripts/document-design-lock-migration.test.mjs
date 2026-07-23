import assert from 'node:assert/strict';
import {
  chmodSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

import {
  CANONICAL_SKILL_NAME,
  LEGACY_SKILL_NAME,
  computeSkillFolderHash,
  migrateDocumentDesignLock,
  migrateDocumentDesignProject,
  verifyCanonicalDocumentDesignProject,
} from './document-design-lock-migration.mjs';

const FIXTURE_PATH = new URL('./fixtures/document-design-lock-v1.json', import.meta.url);

function readFixture() {
  return JSON.parse(readFileSync(FIXTURE_PATH, 'utf8'));
}

function makeProject(t, lock = readFixture()) {
  const project = mkdtempSync(join(tmpdir(), 'document-design-lock-test-'));
  t.after(() => rmSync(project, { recursive: true, force: true }));
  mkdirSync(join(project, '.agents', 'skills', CANONICAL_SKILL_NAME), { recursive: true });
  writeFileSync(
    join(project, '.agents', 'skills', CANONICAL_SKILL_NAME, 'SKILL.md'),
    '---\nname: Document design\ndescription: Historical fixture\n---\n',
  );
  const projectLock = structuredClone(lock);
  const installedHash = computeSkillFolderHash(
    join(project, '.agents', 'skills', CANONICAL_SKILL_NAME),
  );
  for (const name of [LEGACY_SKILL_NAME, CANONICAL_SKILL_NAME]) {
    if (projectLock.skills[name]) projectLock.skills[name].computedHash = installedHash;
  }
  writeFileSync(
    join(project, 'skills-lock.json'),
    `${JSON.stringify(projectLock, null, 2)}\n`,
  );
  return project;
}

test('the fixture captures the historical lock key, source path, and installed path', (t) => {
  const fixture = readFixture();
  const project = makeProject(t, fixture);

  assert.deepEqual(Object.keys(fixture.skills), [LEGACY_SKILL_NAME]);
  assert.equal(
    fixture.skills[LEGACY_SKILL_NAME].skillPath,
    'pdf-playground/skills/document-design/SKILL.md',
  );
  assert.equal(
    lstatSync(join(project, '.agents', 'skills', CANONICAL_SKILL_NAME)).isDirectory(),
    true,
  );
});

test('the migration renames only the exact legacy identity and preserves its record', () => {
  const fixture = readFixture();
  const originalRecord = structuredClone(fixture.skills[LEGACY_SKILL_NAME]);
  const result = migrateDocumentDesignLock(fixture);

  assert.equal(result.status, 'migrated');
  assert.deepEqual(Object.keys(result.lock.skills), [CANONICAL_SKILL_NAME]);
  assert.deepEqual(result.lock.skills[CANONICAL_SKILL_NAME], originalRecord);
  assert.deepEqual(Object.keys(fixture.skills), [LEGACY_SKILL_NAME]);
});

test('a second migration is byte-for-byte idempotent', (t) => {
  const project = makeProject(t);
  const first = migrateDocumentDesignProject(project);
  const firstBytes = readFileSync(join(project, 'skills-lock.json'));
  const second = migrateDocumentDesignProject(project);
  const secondBytes = readFileSync(join(project, 'skills-lock.json'));

  assert.equal(first.status, 'migrated');
  assert.equal(second.status, 'current');
  assert.deepEqual(secondBytes, firstBytes);
  assert.equal(
    readFileSync(
      join(project, '.agents', 'skills', CANONICAL_SKILL_NAME, 'SKILL.md'),
      'utf8',
    ),
    '---\nname: Document design\ndescription: Historical fixture\n---\n',
  );
});

test('an identical duplicate is collapsed without changing the canonical record', () => {
  const fixture = readFixture();
  const record = structuredClone(fixture.skills[LEGACY_SKILL_NAME]);
  fixture.skills[CANONICAL_SKILL_NAME] = structuredClone(record);
  const result = migrateDocumentDesignLock(fixture);

  assert.equal(result.status, 'collapsed');
  assert.deepEqual(Object.keys(result.lock.skills), [CANONICAL_SKILL_NAME]);
  assert.deepEqual(result.lock.skills[CANONICAL_SKILL_NAME], record);
});

test('conflicting duplicate identities fail closed', () => {
  const fixture = readFixture();
  fixture.skills[CANONICAL_SKILL_NAME] = {
    ...fixture.skills[LEGACY_SKILL_NAME],
    computedHash: 'f'.repeat(64),
  };

  assert.throws(
    () => migrateDocumentDesignLock(fixture),
    /conflicting legacy and canonical lock entries/u,
  );
});

test('unrelated source, path, type, or malformed hashes fail closed', () => {
  for (const patch of [
    { source: 'someone/another-repository' },
    { sourceType: 'local' },
    { skillPath: 'another/path/SKILL.md' },
    { computedHash: 'not-a-sha256' },
  ]) {
    const fixture = readFixture();
    Object.assign(fixture.skills[LEGACY_SKILL_NAME], patch);
    assert.throws(
      () => migrateDocumentDesignLock(fixture),
      /refusing to migrate ambiguous Document design lock entry/u,
    );
  }
});

test('missing locks, linked locks, and linked installed paths are rejected', (t) => {
  const missing = mkdtempSync(join(tmpdir(), 'document-design-lock-missing-'));
  t.after(() => rmSync(missing, { recursive: true, force: true }));
  assert.throws(() => migrateDocumentDesignProject(missing), /skills-lock\.json/u);

  const linkedLockProject = makeProject(t);
  const realLock = join(linkedLockProject, 'real-lock.json');
  writeFileSync(realLock, readFileSync(join(linkedLockProject, 'skills-lock.json')));
  rmSync(join(linkedLockProject, 'skills-lock.json'));
  symlinkSync(realLock, join(linkedLockProject, 'skills-lock.json'));
  assert.throws(() => migrateDocumentDesignProject(linkedLockProject), /symbolic link/u);

  const linkedInstallProject = makeProject(t);
  const linkedInstall = join(linkedInstallProject, '.agents', 'skills', CANONICAL_SKILL_NAME);
  rmSync(linkedInstall, { recursive: true });
  symlinkSync(tmpdir(), linkedInstall, 'dir');
  assert.throws(
    () => migrateDocumentDesignProject(linkedInstallProject),
    /installed document-design path is a symbolic link/u,
  );
});

test('atomic replacement preserves the lock file mode', (t) => {
  const project = makeProject(t);
  const lockPath = join(project, 'skills-lock.json');
  chmodSync(lockPath, 0o640);

  migrateDocumentDesignProject(project);

  assert.equal(lstatSync(lockPath).mode & 0o777, 0o640);
});

test('migration rejects an installed tree whose content has drifted from the legacy lock', (t) => {
  const project = makeProject(t);
  writeFileSync(
    join(project, '.agents', 'skills', CANONICAL_SKILL_NAME, 'drift.md'),
    'changed after install',
  );

  assert.throws(
    () => migrateDocumentDesignProject(project),
    /content hash does not match the legacy lock/u,
  );
  const lock = JSON.parse(readFileSync(join(project, 'skills-lock.json'), 'utf8'));
  assert.deepEqual(Object.keys(lock.skills), [LEGACY_SKILL_NAME]);
});

test('post-update verification checks the canonical path, source, frontmatter, and hash', (t) => {
  const project = makeProject(t);
  const installedPath = join(project, '.agents', 'skills', CANONICAL_SKILL_NAME);
  writeFileSync(
    join(installedPath, 'SKILL.md'),
    '---\nname: document-design\ndescription: Current fixture\n---\n',
  );
  const fixture = readFixture();
  const record = {
    ...fixture.skills[LEGACY_SKILL_NAME],
    computedHash: computeSkillFolderHash(installedPath),
  };
  writeFileSync(
    join(project, 'skills-lock.json'),
    `${JSON.stringify({
      version: 1,
      skills: { [CANONICAL_SKILL_NAME]: record },
    }, null, 2)}\n`,
  );

  const result = verifyCanonicalDocumentDesignProject(project);
  assert.equal(result.computedHash, record.computedHash);
  assert.equal(result.record.source, 'jamditis/claude-skills-journalism');
  assert.equal(
    result.record.skillPath,
    'pdf-playground/skills/document-design/SKILL.md',
  );

  writeFileSync(join(installedPath, 'changed.md'), 'drift');
  assert.throws(
    () => verifyCanonicalDocumentDesignProject(project),
    /content hash does not match/u,
  );
});

test('package scripts keep migration explicit and the live updater canary separate', () => {
  const packageJson = JSON.parse(
    readFileSync(new URL('../package.json', import.meta.url), 'utf8'),
  );
  assert.equal(
    packageJson.scripts['migrate:document-design-lock'],
    'node scripts/document-design-lock-migration.mjs',
  );
  assert.equal(
    packageJson.scripts['canary:document-design-lock'],
    'node scripts/document-design-lock-update-canary.mjs',
  );

  const canary = readFileSync(
    new URL('./document-design-lock-update-canary.mjs', import.meta.url),
    'utf8',
  );
  assert.match(canary, /SKILLS_CLI_VERSION = '1\.5\.20'/u);
  assert.match(canary, /CODEX_CLI_VERSION = '0\.145\.0'/u);
  assert.match(canary, /assertStatus\(prechange, 1/u);
  assert.match(canary, /assertStatus\(firstUpdate, 0/u);
  assert.match(canary, /assertStatus\(secondUpdate, 0/u);
  assert.match(canary, /removeCanaryRoot\(canaryRoot\)/u);
  assert.doesNotMatch(canary, /shell:\s*true/u);
});
