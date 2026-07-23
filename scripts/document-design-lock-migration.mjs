import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import {
  lstatSync,
  readFileSync,
  readdirSync,
  realpathSync,
  renameSync,
  unlinkSync,
  writeFileSync,
} from 'node:fs';
import { isAbsolute, join, relative, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { isDeepStrictEqual } from 'node:util';

export const LEGACY_SKILL_NAME = 'Document design';
export const CANONICAL_SKILL_NAME = 'document-design';

const EXPECTED_SOURCE = 'jamditis/claude-skills-journalism';
const EXPECTED_SOURCE_TYPE = 'github';
const EXPECTED_SKILL_PATH = 'pdf-playground/skills/document-design/SKILL.md';
const LOCK_FILE_NAME = 'skills-lock.json';
const SHA256_PATTERN = /^[a-f0-9]{64}$/u;

function isRecord(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function assertLockShape(lock) {
  if (!isRecord(lock) || lock.version !== 1 || !isRecord(lock.skills)) {
    throw new Error('skills-lock.json must contain a version 1 skills object');
  }
}

function assertExpectedIdentity(record) {
  if (
    !isRecord(record)
    || record.source !== EXPECTED_SOURCE
    || record.sourceType !== EXPECTED_SOURCE_TYPE
    || record.skillPath !== EXPECTED_SKILL_PATH
    || typeof record.computedHash !== 'string'
    || !SHA256_PATTERN.test(record.computedHash)
  ) {
    throw new Error(`refusing to migrate ambiguous ${LEGACY_SKILL_NAME} lock entry`);
  }
}

function sortSkills(skills) {
  return Object.fromEntries(
    Object.entries(skills).sort(([left], [right]) => {
      if (left < right) return -1;
      if (left > right) return 1;
      return 0;
    }),
  );
}

export function migrateDocumentDesignLock(lock) {
  assertLockShape(lock);
  const migratedLock = structuredClone(lock);
  const legacy = migratedLock.skills[LEGACY_SKILL_NAME];
  const canonical = migratedLock.skills[CANONICAL_SKILL_NAME];

  if (legacy === undefined) {
    if (canonical !== undefined) assertExpectedIdentity(canonical);
    return {
      lock: migratedLock,
      status: canonical === undefined ? 'absent' : 'current',
    };
  }

  assertExpectedIdentity(legacy);
  if (canonical !== undefined) {
    assertExpectedIdentity(canonical);
    if (!isDeepStrictEqual(legacy, canonical)) {
      throw new Error('conflicting legacy and canonical lock entries require manual recovery');
    }
    delete migratedLock.skills[LEGACY_SKILL_NAME];
    migratedLock.skills = sortSkills(migratedLock.skills);
    return { lock: migratedLock, status: 'collapsed' };
  }

  delete migratedLock.skills[LEGACY_SKILL_NAME];
  migratedLock.skills[CANONICAL_SKILL_NAME] = legacy;
  migratedLock.skills = sortSkills(migratedLock.skills);
  return { lock: migratedLock, status: 'migrated' };
}

function assertContainedPath(projectRoot, path, label) {
  const realPath = realpathSync(path);
  const pathFromRoot = relative(projectRoot, realPath);
  if (
    pathFromRoot === ''
    || pathFromRoot.startsWith('..')
    || isAbsolute(pathFromRoot)
  ) {
    throw new Error(`${label} escaped the project root`);
  }
  return realPath;
}

function verifyLockPath(project) {
  const projectRoot = realpathSync(resolve(project));
  const lockPath = join(projectRoot, LOCK_FILE_NAME);
  const lockStat = lstatSync(lockPath);
  if (lockStat.isSymbolicLink()) throw new Error(`${LOCK_FILE_NAME} must not be a symbolic link`);
  if (!lockStat.isFile()) throw new Error(`${LOCK_FILE_NAME} must be a regular file`);
  assertContainedPath(projectRoot, lockPath, LOCK_FILE_NAME);

  return { lockPath, lockStat, projectRoot };
}

function verifyInstalledPath(projectRoot) {
  const installedPath = join(
    projectRoot,
    '.agents',
    'skills',
    CANONICAL_SKILL_NAME,
  );
  const installedStat = lstatSync(installedPath);
  if (installedStat.isSymbolicLink()) {
    throw new Error(`installed ${CANONICAL_SKILL_NAME} path is a symbolic link`);
  }
  if (!installedStat.isDirectory()) {
    throw new Error(`installed ${CANONICAL_SKILL_NAME} path must be a directory`);
  }
  assertContainedPath(projectRoot, installedPath, `installed ${CANONICAL_SKILL_NAME} path`);

  return installedPath;
}

function readProjectLock(lockPath) {
  try {
    return JSON.parse(readFileSync(lockPath, 'utf8'));
  } catch (error) {
    throw new Error(`could not parse ${LOCK_FILE_NAME}: ${error.message}`);
  }
}

function collectSkillFiles(basePath, directory, files) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isSymbolicLink()) {
      throw new Error(`installed ${CANONICAL_SKILL_NAME} contains a symbolic link`);
    }
    if (entry.isDirectory()) {
      if (entry.name !== '.git' && entry.name !== 'node_modules') {
        collectSkillFiles(basePath, path, files);
      }
      continue;
    }
    if (!entry.isFile()) {
      throw new Error(`installed ${CANONICAL_SKILL_NAME} contains a non-file resource`);
    }
    files.push({
      content: readFileSync(path),
      relativePath: relative(basePath, path).replaceAll('\\', '/'),
    });
  }
}

export function computeSkillFolderHash(skillPath) {
  const files = [];
  collectSkillFiles(skillPath, skillPath, files);
  files.sort((left, right) => left.relativePath.localeCompare(right.relativePath));
  const hash = createHash('sha256');
  for (const file of files) {
    hash.update(file.relativePath);
    hash.update(file.content);
  }
  return hash.digest('hex');
}

export function verifyCanonicalDocumentDesignProject(project) {
  const { lockPath, projectRoot } = verifyLockPath(project);
  const lock = readProjectLock(lockPath);
  assertLockShape(lock);
  if (lock.skills[LEGACY_SKILL_NAME] !== undefined) {
    throw new Error(`${LEGACY_SKILL_NAME} lock identity still exists`);
  }
  const record = lock.skills[CANONICAL_SKILL_NAME];
  if (record === undefined) {
    throw new Error(`${CANONICAL_SKILL_NAME} lock identity is missing`);
  }
  assertExpectedIdentity(record);

  const installedPath = verifyInstalledPath(projectRoot);
  const skill = readFileSync(join(installedPath, 'SKILL.md'), 'utf8');
  const frontmatter = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/u.exec(skill)?.[1];
  const nameLines = frontmatter
    ?.split(/\r?\n/u)
    .filter((line) => /^name:/u.test(line)) ?? [];
  if (nameLines.length !== 1 || !/^name:[ \t]*document-design[ \t]*$/u.test(nameLines[0])) {
    throw new Error(`installed ${CANONICAL_SKILL_NAME} frontmatter is not canonical`);
  }
  const computedHash = computeSkillFolderHash(installedPath);
  if (computedHash !== record.computedHash) {
    throw new Error(`installed ${CANONICAL_SKILL_NAME} content hash does not match the lock`);
  }
  return { computedHash, installedPath, lockPath, record };
}

function writeLockAtomically(lockPath, lock, mode) {
  const temporaryPath = `${lockPath}.migration-${process.pid}-${Date.now()}`;
  const serialized = `${JSON.stringify(lock, null, 2)}\n`;
  try {
    writeFileSync(temporaryPath, serialized, { encoding: 'utf8', flag: 'wx', mode });
    renameSync(temporaryPath, lockPath);
  } catch (error) {
    try {
      unlinkSync(temporaryPath);
    } catch {}
    throw error;
  }
}

export function migrateDocumentDesignProject(project, { write = true } = {}) {
  const { lockPath, lockStat, projectRoot } = verifyLockPath(project);
  const parsed = readProjectLock(lockPath);
  const result = migrateDocumentDesignLock(parsed);
  if (result.status === 'absent') return result;

  const installedPath = verifyInstalledPath(projectRoot);
  if (result.status === 'migrated' || result.status === 'collapsed') {
    const installedHash = computeSkillFolderHash(installedPath);
    const lockedHash = parsed.skills[LEGACY_SKILL_NAME].computedHash;
    if (installedHash !== lockedHash) {
      throw new Error(
        `installed ${CANONICAL_SKILL_NAME} content hash does not match the legacy lock`,
      );
    }
  }
  if (write && (result.status === 'migrated' || result.status === 'collapsed')) {
    writeLockAtomically(lockPath, result.lock, lockStat.mode & 0o777);
  }
  return result;
}

function usage() {
  return [
    'Usage: node scripts/document-design-lock-migration.mjs [options]',
    '',
    'Options:',
    '  --project <path>  Project containing skills-lock.json (default: current directory)',
    '  --check           Report whether migration is required without writing',
    '  --verify          Verify the post-update canonical identity and content hash',
    '  --help            Show this help',
  ].join('\n');
}

function parseArguments(args) {
  const options = { check: false, project: process.cwd(), verify: false };
  for (let index = 0; index < args.length; index += 1) {
    const argument = args[index];
    if (argument === '--check') {
      options.check = true;
    } else if (argument === '--verify') {
      options.verify = true;
    } else if (argument === '--project') {
      index += 1;
      if (!args[index]) throw new Error('--project requires a path');
      options.project = args[index];
    } else if (argument === '--help') {
      options.help = true;
    } else {
      throw new Error(`unknown argument: ${argument}`);
    }
  }
  if (options.check && options.verify) {
    throw new Error('--check and --verify cannot be combined');
  }
  return options;
}

function runCli(args) {
  const options = parseArguments(args);
  if (options.help) {
    console.log(usage());
    return;
  }
  if (options.verify) {
    const result = verifyCanonicalDocumentDesignProject(options.project);
    console.log(
      `Verified ${CANONICAL_SKILL_NAME} lock identity, installed path, and content hash ${result.computedHash}.`,
    );
    return;
  }

  const result = migrateDocumentDesignProject(options.project, { write: !options.check });
  if (options.check && (result.status === 'migrated' || result.status === 'collapsed')) {
    console.error(`${LOCK_FILE_NAME} requires ${LEGACY_SKILL_NAME} key migration`);
    process.exitCode = 1;
    return;
  }

  const messages = {
    absent: `No ${LEGACY_SKILL_NAME} or ${CANONICAL_SKILL_NAME} lock entry found.`,
    collapsed: `Collapsed identical ${LEGACY_SKILL_NAME} and ${CANONICAL_SKILL_NAME} lock entries.`,
    current: `${CANONICAL_SKILL_NAME} lock identity is already current.`,
    migrated: `Migrated ${LEGACY_SKILL_NAME} lock identity to ${CANONICAL_SKILL_NAME}.`,
  };
  console.log(messages[result.status]);
}

const invokedPath = process.argv[1] ? pathToFileURL(resolve(process.argv[1])).href : '';
if (invokedPath === import.meta.url) {
  try {
    runCli(process.argv.slice(2));
  } catch (error) {
    assert(error instanceof Error);
    console.error(error.message);
    process.exitCode = 1;
  }
}
