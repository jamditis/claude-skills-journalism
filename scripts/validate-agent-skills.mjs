import {
  cpSync,
  existsSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, join, relative, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
import { parseDocument } from 'yaml';

export const SKILLS_REF_REVISION = '38a2ff82958afee88dadf4831509e6f7e9d8ef4e';
export const SKILLS_REF_SOURCE =
  `git+https://github.com/agentskills/agentskills.git@${SKILLS_REF_REVISION}#subdirectory=skills-ref`;
export const UPSTREAM_SKILLS_REF_SOURCE =
  'git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref';

const SKIP_DIRECTORIES = new Set(['.agents', '.git', 'node_modules']);
const CLAUDE_EXPLICIT_FIELD = 'disable-model-invocation';

export function findSkillDirectories(root, current = root, directories = []) {
  for (const entry of readdirSync(current, { withFileTypes: true })) {
    if (entry.isDirectory() && SKIP_DIRECTORIES.has(entry.name)) continue;

    const path = join(current, entry.name);
    if (entry.isDirectory()) {
      findSkillDirectories(root, path, directories);
    } else if (entry.isFile() && entry.name === 'SKILL.md') {
      directories.push(current);
    }
  }

  return directories.sort((left, right) => left.localeCompare(right));
}

export function validateSkillDirectories(
  directories,
  {
    command = process.platform === 'win32' ? 'uvx.exe' : 'uvx',
    run = spawnSync,
    source = SKILLS_REF_SOURCE,
  } = {},
) {
  return directories.map((directory) => {
    let validationDirectory = directory;
    let temporaryRoot = null;

    const skillPath = join(directory, 'SKILL.md');
    if (existsSync(skillPath)) {
      const skill = readFileSync(skillPath, 'utf8');
      const frontmatter = skill.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/u);
      const document = frontmatter ? parseDocument(frontmatter[1], { uniqueKeys: true }) : null;
      const explicitValue = document?.get(CLAUDE_EXPLICIT_FIELD);

      if (document?.errors.length || (explicitValue !== undefined && typeof explicitValue !== 'boolean')) {
        return {
          directory,
          status: 1,
          stdout: '',
          stderr: `${CLAUDE_EXPLICIT_FIELD} must be one top-level boolean field`,
        };
      }

      if (explicitValue !== undefined) {
        temporaryRoot = mkdtempSync(join(tmpdir(), 'agent-skills-validation-'));
        validationDirectory = join(temporaryRoot, basename(directory));
        cpSync(directory, validationDirectory, { recursive: true });
        document.delete(CLAUDE_EXPLICIT_FIELD);
        const projected = skill.replace(frontmatter[0], `---\n${document.toString()}---\n`);
        writeFileSync(join(validationDirectory, 'SKILL.md'), projected, 'utf8');
      }
    }

    let result;
    try {
      result = run(
        command,
        ['--from', source, 'skills-ref', 'validate', validationDirectory],
        {
          encoding: 'utf8',
          env: { ...process.env, PYTHONUTF8: '1' },
        },
      );
    } finally {
      if (temporaryRoot) rmSync(temporaryRoot, { recursive: true, force: true });
    }

    return {
      directory,
      status: result.status ?? 1,
      stdout: (result.stdout ?? '').replaceAll(validationDirectory, directory),
      stderr: (result.stderr ?? result.error?.message ?? '').replaceAll(validationDirectory, directory),
    };
  });
}

function runCli() {
  const args = process.argv.slice(2);
  const unsupported = args.filter((arg) => arg !== '--upstream');
  if (unsupported.length > 0) {
    console.error('Usage: node scripts/validate-agent-skills.mjs [--upstream]');
    process.exitCode = 2;
    return;
  }

  const root = fileURLToPath(new URL('..', import.meta.url));
  const directories = findSkillDirectories(root);
  const source = args.includes('--upstream') ? UPSTREAM_SKILLS_REF_SOURCE : SKILLS_REF_SOURCE;

  if (directories.length === 0) {
    console.error('No SKILL.md files found.');
    process.exitCode = 1;
    return;
  }

  const results = validateSkillDirectories(directories, { source });
  for (const result of results) {
    const displayPath = relative(root, result.directory) || basename(result.directory);
    const output = `${result.stdout}${result.stderr}`.trim();
    console.log(`${result.status === 0 ? 'PASS' : 'FAIL'} ${displayPath}`);
    if (output) console.log(output);
  }

  const failed = results.filter(({ status }) => status !== 0);
  console.log(`Validated ${results.length} skills; ${failed.length} failed.`);
  if (failed.length > 0) process.exitCode = 1;
}

const entryPoint = process.argv[1] ? pathToFileURL(resolve(process.argv[1])).href : '';
if (entryPoint === import.meta.url) runCli();
