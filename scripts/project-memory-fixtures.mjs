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
  if (!fromProject || fromProject.startsWith('..') || isAbsolute(fromProject)) {
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

function countText(body, text) {
  return body.split(text).length - 1;
}

function readOutput(project, output, label) {
  const path = containedPath(project, output.path, label);
  requireRegularFile(path, label);
  return { path, body: readFileSync(path, 'utf8') };
}

function snapshotProjectTree(project) {
  const snapshot = {};
  const walk = (directory, prefix = '') => {
    for (const entry of readdirSync(directory, { withFileTypes: true })
      .sort((left, right) => left.name.localeCompare(right.name))) {
      const path = prefix ? `${prefix}/${entry.name}` : entry.name;
      const absolutePath = containedPath(project, path, 'Snapshot path');
      if (entry.isDirectory()) {
        walk(absolutePath, path);
      } else if (entry.isFile()) {
        snapshot[path] = {
          kind: 'file',
          body: readFileSync(absolutePath).toString('base64'),
        };
      } else if (entry.isSymbolicLink()) {
        snapshot[path] = {
          kind: 'symlink',
          target: readlinkSync(absolutePath),
        };
      } else {
        snapshot[path] = { kind: 'other' };
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
    if (existsSync(absolutePath)) {
      throw new Error(`Fixture input already exists: ${absolutePath}`);
    }
  }
  for (const [path, body] of entries) {
    const absolutePath = containedPath(project, path, 'Fixture input');
    mkdirSync(dirname(absolutePath), { recursive: true });
    writeFileSync(absolutePath, body, { flag: 'wx' });
  }

  return {
    project,
    snapshot: snapshotProjectTree(project),
  };
}

export function verifyProjectMemoryOutput(projectDir, client) {
  const project = requireDisposableProject(projectDir);
  const fixtureDefinition = fixtureFor(client);
  const root = readOutput(project, fixtureDefinition.output.root, 'root output');
  const nested = readOutput(project, fixtureDefinition.output.nested, 'nested output');

  if (countText(root.body, fixtureDefinition.existing.root) !== 1) {
    throw new Error('Project-memory did not preserve the existing root guidance exactly once');
  }
  if (countText(nested.body, fixtureDefinition.existing.nested) !== 1) {
    throw new Error('Project-memory did not preserve the existing nested guidance exactly once');
  }

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

  const otherClient = client === 'claude' ? 'codex' : 'claude';
  for (const otherFile of fixtureFor(otherClient).cleanup.paths) {
    if (existsSync(containedPath(project, otherFile, 'Other-client output'))) {
      throw new Error(`Project-memory created the other client's ${otherFile}`);
    }
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
  return fixtureDefinition.cleanup.paths.map((path) => {
    const absolutePath = containedPath(project, path, 'Cleanup path');
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
