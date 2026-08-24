import {
  existsSync,
  lstatSync,
  mkdirSync,
  readlinkSync,
  readFileSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import {
  dirname,
  isAbsolute,
  relative,
  resolve,
  sep,
} from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const SKILL_PATH = 'project-templates-toolkit/skills/project-memory/SKILL.md';

const ROOT_REQUIRED_TEXT = Object.freeze([
  '## Project knowledge',
  '- Use UTC for all publish timestamps.',
]);
const NESTED_REQUIRED_TEXT = Object.freeze([
  '## Archive package',
  '- Run npm run test:archive for changes below packages/archive.',
]);
const EXISTING_ROOT = '# Existing project guidance\n\n'
  + '## Release safety\n'
  + '- Keep the manual sign-off before public releases.\n\n';
const EXISTING_NESTED = '# Existing archive guidance\n\n'
  + '## Data handling\n'
  + '- Never commit source interview recordings.\n\n';
const NON_TRIGGER = Object.freeze({
  prompt: 'Calculate an 18% tip on a $42 meal. Do not edit any files.',
  expectedMutation: false,
});

function fixture(client, instructionFile, activationPrompt) {
  const rootPath = instructionFile;
  const nestedPath = `packages/archive/${instructionFile}`;
  return Object.freeze({
    client,
    activation: Object.freeze({ prompt: activationPrompt }),
    nonTrigger: NON_TRIGGER,
    existing: Object.freeze({
      root: EXISTING_ROOT,
      nested: EXISTING_NESTED,
    }),
    output: Object.freeze({
      root: Object.freeze({
        path: rootPath,
        requiredText: ROOT_REQUIRED_TEXT,
      }),
      nested: Object.freeze({
        path: nestedPath,
        requiredText: NESTED_REQUIRED_TEXT,
      }),
    }),
    cleanup: Object.freeze({
      paths: Object.freeze([rootPath, nestedPath]),
    }),
  });
}

export const PROJECT_MEMORY_FIXTURES = Object.freeze({
  claude: fixture(
    'claude',
    'CLAUDE.md',
    'Merge project knowledge into the existing CLAUDE.md files. Preserve every '
      + 'existing line exactly once and do not rewrite unrelated guidance. Add '
      + '"Use UTC for all publish timestamps." under "Project knowledge" in '
      + 'the root CLAUDE.md. Add "Run npm run test:archive for changes below '
      + 'packages/archive." under "Archive package" only in '
      + 'packages/archive/CLAUDE.md. Do not create AGENTS.md.',
  ),
  codex: fixture(
    'codex',
    'AGENTS.md',
    'Merge project knowledge into the existing AGENTS.md files. Preserve every '
      + 'existing line exactly once and do not rewrite unrelated guidance. Add '
      + '"Use UTC for all publish timestamps." under "Project knowledge" in '
      + 'the root AGENTS.md, where it governs the repository. Add "Run npm run '
      + 'test:archive for changes below packages/archive." under "Archive '
      + 'package" only in packages/archive/AGENTS.md, where its scope is the '
      + 'directory tree rooted at packages/archive. Do not create CLAUDE.md.',
  ),
});

function fixtureFor(client) {
  if (!Object.hasOwn(PROJECT_MEMORY_FIXTURES, client)) {
    throw new Error(`Unsupported project-memory fixture client: ${client}`);
  }
  return PROJECT_MEMORY_FIXTURES[client];
}

function containedPath(projectDir, path, label) {
  const project = resolve(projectDir);
  const candidate = resolve(project, path);
  const fromProject = relative(project, candidate);
  if (
    !fromProject
    || fromProject === '..'
    || fromProject.startsWith(`..${sep}`)
    || isAbsolute(fromProject)
  ) {
    throw new Error(`${label} must resolve below the disposable project`);
  }
  return candidate;
}

function requireDisposableProject(projectDir) {
  const project = resolve(projectDir);
  if (!existsSync(project)) {
    throw new Error(`Disposable project does not exist: ${project}`);
  }
  const stat = lstatSync(project);
  if (!stat.isDirectory() || stat.isSymbolicLink()) {
    throw new Error(`Disposable project must be a real directory: ${project}`);
  }
  return project;
}

function requireRegularFile(path, label) {
  if (!existsSync(path)) throw new Error(`Missing ${label}: ${path}`);
  const stat = lstatSync(path);
  if (!stat.isFile() || stat.isSymbolicLink()) {
    throw new Error(`${label} must be a regular file: ${path}`);
  }
}

function requireRealAncestors(project, candidate, label) {
  const ancestors = [];
  for (let ancestor = dirname(candidate); ancestor !== project; ancestor = dirname(ancestor)) {
    if (dirname(ancestor) === ancestor) {
      throw new Error(`${label} ancestor escaped the disposable project`);
    }
    ancestors.push(ancestor);
  }
  for (const ancestor of ancestors.reverse()) {
    let stat;
    try {
      stat = lstatSync(ancestor);
    } catch (error) {
      if (error.code === 'ENOENT') break;
      throw error;
    }
    if (stat.isSymbolicLink()) {
      throw new Error(`${label} ancestor must not be a symbolic link: ${ancestor}`);
    }
    if (!stat.isDirectory()) {
      throw new Error(`${label} ancestor must be a directory: ${ancestor}`);
    }
  }
}

function verifyPreservedGuidance(body, existing, label) {
  const outputLines = body.split(/\r?\n/u);
  const expectedLines = existing.split(/\r?\n/u).filter(Boolean);
  for (const line of new Set(expectedLines)) {
    const expectedCount = expectedLines.filter((candidate) => candidate === line).length;
    const actualCount = outputLines.filter((candidate) => candidate === line).length;
    if (actualCount !== expectedCount) {
      throw new Error(
        `Project-memory did not preserve the existing ${label} guidance exactly once`,
      );
    }
  }
  let previousIndex = -1;
  for (const line of expectedLines) {
    const index = outputLines.indexOf(line, previousIndex + 1);
    if (index < 0) {
      throw new Error(`Project-memory changed the order of existing ${label} guidance`);
    }
    previousIndex = index;
  }
}

function verifyRequiredSection(body, requiredText, label) {
  const [heading, ...guidance] = requiredText;
  const lines = body.split(/\r?\n/u);
  const headingIndex = lines.indexOf(heading);
  const headingMatch = /^(#{1,6})\s/u.exec(heading);
  if (headingIndex < 0 || !headingMatch) {
    throw new Error(
      `Project-memory ${label} required heading must be an exact Markdown line`,
    );
  }

  const headingLevel = headingMatch[1].length;
  let sectionEnd = lines.length;
  for (let index = headingIndex + 1; index < lines.length; index += 1) {
    const nextHeading = /^(#{1,6})\s/u.exec(lines[index]);
    if (nextHeading && nextHeading[1].length <= headingLevel) {
      sectionEnd = index;
      break;
    }
  }

  let previousIndex = headingIndex;
  for (const text of guidance) {
    const index = lines.indexOf(text, previousIndex + 1);
    if (index < 0 || index >= sectionEnd) {
      throw new Error(
        `Project-memory ${label} output does not keep required guidance under its heading`,
      );
    }
    previousIndex = index;
  }
}

function readOutput(project, output, label) {
  const path = containedPath(project, output.path, label);
  requireRealAncestors(project, path, label);
  requireRegularFile(path, label);
  return { path, body: readFileSync(path, 'utf8') };
}

function snapshotProjectTree(project) {
  const snapshot = Object.create(null);
  const walk = (directory, prefix = '') => {
    for (const entry of readdirSync(directory, { withFileTypes: true })
      .sort((left, right) => left.name.localeCompare(right.name))) {
      const path = prefix ? `${prefix}/${entry.name}` : entry.name;
      const absolutePath = containedPath(project, path, 'Snapshot path');
      const stat = lstatSync(absolutePath);
      const mode = stat.mode & 0o777;
      if (entry.isDirectory()) {
        snapshot[path] = { kind: 'directory', mode };
        walk(absolutePath, path);
      } else if (entry.isFile()) {
        snapshot[path] = {
          kind: 'file',
          mode,
          body: readFileSync(absolutePath).toString('base64'),
        };
      } else if (entry.isSymbolicLink()) {
        snapshot[path] = {
          kind: 'symlink',
          mode,
          target: readlinkSync(absolutePath),
        };
      } else {
        snapshot[path] = { kind: 'other', mode };
      }
    }
  };
  walk(project);
  return snapshot;
}

export function prepareProjectMemoryFixture(projectDir, client) {
  const project = requireDisposableProject(projectDir);
  const fixtureDefinition = fixtureFor(client);
  const entries = [
    [fixtureDefinition.output.root.path, fixtureDefinition.existing.root],
    [fixtureDefinition.output.nested.path, fixtureDefinition.existing.nested],
  ];

  for (const [path] of entries) {
    const absolutePath = containedPath(project, path, 'Fixture input');
    requireRealAncestors(project, absolutePath, 'Fixture input');
    if (existsSync(absolutePath)) {
      throw new Error(`Fixture input already exists: ${absolutePath}`);
    }
  }
  for (const [path, body] of entries) {
    const absolutePath = containedPath(project, path, 'Fixture input');
    requireRealAncestors(project, absolutePath, 'Fixture input');
    mkdirSync(dirname(absolutePath), { recursive: true });
    writeFileSync(absolutePath, body, { flag: 'wx' });
  }

  return {
    project,
    snapshot: snapshotProjectTree(project),
  };
}

export function verifyProjectMemoryOutput(projectDir, client, preparedSnapshot = {}) {
  const project = requireDisposableProject(projectDir);
  const fixtureDefinition = fixtureFor(client);
  const root = readOutput(project, fixtureDefinition.output.root, 'root output');
  const nested = readOutput(project, fixtureDefinition.output.nested, 'nested output');

  verifyPreservedGuidance(root.body, fixtureDefinition.existing.root, 'root');
  verifyPreservedGuidance(nested.body, fixtureDefinition.existing.nested, 'nested');

  for (const text of fixtureDefinition.output.root.requiredText) {
    if (!root.body.includes(text)) {
      throw new Error(`Root output is missing required text: ${text}`);
    }
    if (nested.body.includes(text)) {
      throw new Error(`Nested output contains root-only guidance: ${text}`);
    }
  }
  for (const text of fixtureDefinition.output.nested.requiredText) {
    if (!nested.body.includes(text)) {
      throw new Error(`Nested output is missing required text: ${text}`);
    }
    if (root.body.includes(text)) {
      throw new Error(`Root output contains nested-only guidance: ${text}`);
    }
  }

  verifyRequiredSection(root.body, fixtureDefinition.output.root.requiredText, 'root');
  verifyRequiredSection(nested.body, fixtureDefinition.output.nested.requiredText, 'nested');

  const otherClient = client === 'claude' ? 'codex' : 'claude';
  const otherInstructionFile = fixtureFor(otherClient).output.root.path;
  const otherFile = Object.keys(snapshotProjectTree(project)).find(
    (path) => path.split('/').at(-1) === otherInstructionFile
      && !Object.hasOwn(preparedSnapshot, path),
  );
  if (otherFile) {
    throw new Error(`Project-memory created the other client's ${otherFile}`);
  }

  return { project, paths: [root.path, nested.path] };
}

export function verifyProjectMemoryNonTrigger(projectDir, client, snapshot) {
  const project = requireDisposableProject(projectDir);
  fixtureFor(client);
  const current = snapshotProjectTree(project);
  const paths = [...new Set([...Object.keys(snapshot), ...Object.keys(current)])].sort();
  for (const path of paths) {
    if (JSON.stringify(current[path]) !== JSON.stringify(snapshot[path])) {
      throw new Error(`Project-memory non-trigger changed ${path}`);
    }
  }
}

export function cleanupProjectMemoryFixture(projectDir, client) {
  const project = requireDisposableProject(projectDir);
  const fixtureDefinition = fixtureFor(client);
  const cleanupPaths = fixtureDefinition.cleanup.paths.map((path) => (
    containedPath(project, path, 'Cleanup path')
  ));
  for (const absolutePath of cleanupPaths) {
    requireRealAncestors(project, absolutePath, 'Cleanup path');
  }
  return cleanupPaths.map((absolutePath) => {
    rmSync(absolutePath, { force: true });
    return absolutePath;
  });
}

export function buildProjectMemoryInvocation(
  client,
  phase,
  {
    projectDir,
    claudeConfigDir,
    codexHome,
  } = {},
) {
  const fixtureDefinition = fixtureFor(client);
  if (phase !== 'activation' && phase !== 'nonTrigger') {
    throw new Error(`Unsupported project-memory fixture phase: ${phase}`);
  }
  if (!projectDir) throw new Error('A disposable project directory is required');
  const cwd = resolve(projectDir);
  const prompt = fixtureDefinition[phase].prompt;

  if (client === 'claude') {
    if (!claudeConfigDir) throw new Error('CLAUDE_CONFIG_DIR is required');
    return {
      command: 'claude',
      args: [
        '-p',
        phase === 'activation'
          ? `/project-templates-toolkit:project-memory ${prompt}`
          : prompt,
        '--output-format',
        'stream-json',
        '--verbose',
        '--no-session-persistence',
        '--permission-mode',
        'dontAsk',
        '--tools',
        'Read,Write,Edit',
        '--allowedTools',
        'Read,Write,Edit',
      ],
      cwd,
      env: { CLAUDE_CONFIG_DIR: resolve(claudeConfigDir) },
    };
  }

  if (!codexHome) throw new Error('CODEX_HOME is required');
  return {
    command: 'codex',
    args: [
      'exec',
      '--ignore-user-config',
      '--ignore-rules',
      '--ephemeral',
      '--sandbox',
      'workspace-write',
      '--skip-git-repo-check',
      '-C',
      cwd,
      '--json',
      phase === 'activation' ? `$project-memory ${prompt}` : prompt,
    ],
    cwd,
    env: { CODEX_HOME: resolve(codexHome) },
  };
}

export function auditCommittedProjectMemorySkill(root = ROOT) {
  const body = readFileSync(resolve(root, SKILL_PATH), 'utf8');
  const lower = body.toLowerCase();
  const claudeOutput = lower.includes('create claude.md files')
    && lower.includes('copy the appropriate template to `./claude.md`');
  const codexOutput = lower.includes('create agents.md files')
    || lower.includes('copy the appropriate template to `./agents.md`');
  const preservesExistingFiles = lower.includes('preserve every existing line')
    || lower.includes('merge into the existing instruction file');
  const nestedCodexScope = lower.includes('nested agents.md')
    && lower.includes('directory tree');

  return {
    claudeOutput,
    codexOutput,
    preservesExistingFiles,
    nestedCodexScope,
    classification:
      claudeOutput && codexOutput && preservesExistingFiles && nestedCodexScope
        ? 'shared'
        : 'adapter-required',
  };
}
