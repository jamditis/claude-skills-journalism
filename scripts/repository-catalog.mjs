import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { dirname, isAbsolute, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from 'yaml';

export const ROOT = fileURLToPath(new URL('..', import.meta.url));
const CATALOG_PATH = join(ROOT, 'skills-catalog.yaml');
const SKIP_DIRECTORIES = new Set(['.agents', '.git', 'node_modules']);
const LIFECYCLES = new Set(['stable', 'beta', 'deprecated']);
const INVOCATION_MODES = new Set(['model', 'explicit']);

export function findSkillFiles(current = ROOT, files = []) {
  for (const entry of readdirSync(current, { withFileTypes: true })) {
    if (entry.isDirectory() && SKIP_DIRECTORIES.has(entry.name)) continue;
    const path = join(current, entry.name);
    if (entry.isDirectory()) findSkillFiles(path, files);
    else if (entry.isFile() && entry.name === 'SKILL.md') files.push(path);
  }
  return files.sort((left, right) => left.localeCompare(right));
}

export function loadCatalog(path = CATALOG_PATH) {
  return parse(readFileSync(path, 'utf8'));
}

export function normalizeRepositoryPath(path) {
  return path.replaceAll('\\', '/');
}

function readSkillName(path) {
  const source = readFileSync(path, 'utf8');
  const match = source.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/u);
  if (!match) return null;
  return parse(match[1]).name ?? null;
}

export function validateCatalog(catalog, root = ROOT) {
  const errors = [];
  if (!catalog || typeof catalog !== 'object' || Array.isArray(catalog)) {
    return ['catalog must be a YAML mapping'];
  }
  if (catalog.schema_version !== 1) errors.push('schema_version must be 1');

  const defaults = catalog.defaults ?? {};
  if (!LIFECYCLES.has(defaults.lifecycle)) errors.push('defaults.lifecycle is invalid');
  if (!INVOCATION_MODES.has(defaults.invocation)) errors.push('defaults.invocation is invalid');
  if (defaults.ui_metadata !== 'agents/openai.yaml') {
    errors.push('defaults.ui_metadata must be agents/openai.yaml');
  }

  const marketplacePath = join(root, '.claude-plugin', 'marketplace.json');
  const marketplace = JSON.parse(readFileSync(marketplacePath, 'utf8'));
  const catalogPackages = new Map();
  for (const entry of catalog.packages ?? []) {
    if (!entry?.name || catalogPackages.has(entry.name)) {
      errors.push(`duplicate or missing package name: ${entry?.name ?? '<missing>'}`);
      continue;
    }
    catalogPackages.set(entry.name, entry);
  }
  const marketplacePackages = new Map(
    marketplace.plugins.map((entry) => [entry.name, entry.source]),
  );
  if (catalogPackages.size !== marketplacePackages.size) {
    errors.push('catalog package count does not match the marketplace');
  }
  for (const [name, source] of marketplacePackages) {
    const entry = catalogPackages.get(name);
    if (!entry) errors.push(`marketplace package missing from catalog: ${name}`);
    else if (entry.source !== source) errors.push(`${name}: catalog source does not match marketplace`);
  }

  const actualPaths = findSkillFiles(root)
    .map((path) => normalizeRepositoryPath(relative(root, dirname(path))));
  const catalogPaths = new Set();
  const catalogNames = new Set();
  for (const skill of catalog.skills ?? []) {
    if (!skill?.path || catalogPaths.has(skill.path)) {
      errors.push(`duplicate or missing skill path: ${skill?.path ?? '<missing>'}`);
      continue;
    }
    catalogPaths.add(skill.path);
    if (
      isAbsolute(skill.path)
      || skill.path.includes('\\')
      || skill.path.split('/').includes('..')
    ) {
      errors.push(`${skill.path}: path must stay inside the repository`);
      continue;
    }
    if (!skill.name || catalogNames.has(skill.name)) {
      errors.push(`duplicate or missing skill name: ${skill.name ?? '<missing>'}`);
    } else {
      catalogNames.add(skill.name);
    }
    if (!catalogPackages.has(skill.package)) {
      errors.push(`${skill.path}: unknown package ${skill.package ?? '<missing>'}`);
    }
    if (skill.path.split('/')[0] !== skill.package) {
      errors.push(`${skill.path}: package does not match its top-level directory`);
    }
    const lifecycle = skill.lifecycle ?? defaults.lifecycle;
    const invocation = skill.invocation ?? defaults.invocation;
    if (!LIFECYCLES.has(lifecycle)) errors.push(`${skill.path}: invalid lifecycle`);
    if (!INVOCATION_MODES.has(invocation)) errors.push(`${skill.path}: invalid invocation`);

    const skillFile = join(root, skill.path, 'SKILL.md');
    if (!existsSync(skillFile)) errors.push(`${skill.path}: SKILL.md does not exist`);
    else if (readSkillName(skillFile) !== skill.name) {
      errors.push(`${skill.path}: catalog name does not match SKILL.md`);
    }

    if (lifecycle === 'stable') {
      const metadataPath = join(root, skill.path, defaults.ui_metadata);
      if (!existsSync(metadataPath)) {
        errors.push(`${skill.path}: stable skill is missing ${defaults.ui_metadata}`);
      } else {
        const metadata = parse(readFileSync(metadataPath, 'utf8'));
        const rootKeys = Object.keys(metadata ?? {});
        const interfaceKeys = Object.keys(metadata?.interface ?? {}).sort();
        if (rootKeys.length !== 1 || rootKeys[0] !== 'interface') {
          errors.push(`${skill.path}: UI metadata must contain only interface`);
        }
        if (interfaceKeys.join(',') !== 'display_name,short_description') {
          errors.push(`${skill.path}: UI metadata interface fields are invalid`);
        }
        for (const key of ['display_name', 'short_description']) {
          if (typeof metadata?.interface?.[key] !== 'string' || !metadata.interface[key].trim()) {
            errors.push(`${skill.path}: ${key} must be a non-empty string`);
          }
        }
        if ((metadata?.interface?.short_description?.length ?? 0) > 80) {
          errors.push(`${skill.path}: short_description exceeds 80 characters`);
        }
      }
    }
  }

  for (const path of actualPaths) {
    if (!catalogPaths.has(path)) errors.push(`${path}: skill is missing from catalog`);
  }
  for (const path of catalogPaths) {
    if (!actualPaths.includes(path)) errors.push(`${path}: catalog path is not a skill`);
  }
  return errors;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const errors = validateCatalog(loadCatalog());
  if (errors.length > 0) {
    for (const error of errors) console.error(`FAIL ${error}`);
    process.exitCode = 1;
  } else {
    console.log('PASS repository catalog');
  }
}
