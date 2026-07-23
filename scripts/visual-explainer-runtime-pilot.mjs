import { spawnSync } from 'node:child_process';
import {
  existsSync,
  lstatSync,
  readFileSync,
  realpathSync,
} from 'node:fs';
import {
  isAbsolute,
  relative,
  resolve,
} from 'node:path';
import { pathToFileURL } from 'node:url';

export const VISUAL_EXPLAINER_TIMEOUT_MS = 300_000;

export const VISUAL_EXPLAINER_FIXTURES = Object.freeze({
  'v-ex-1': Object.freeze({
    output: 'v-ex-1.html',
    resources: Object.freeze([
      'references/css-patterns.md',
      'templates/architecture.html',
    ]),
    requiredText: Object.freeze([
      'Receive tips',
      'Verify evidence',
      'Assign an editor',
      'Publish corrected story',
      'Audit trail',
    ]),
    prompt:
      'Create a self-contained HTML architecture diagram at ./v-ex-1.html '
      + 'from this supplied text: A newsroom receives tips, verifies evidence, '
      + 'assigns an editor, and publishes a corrected story with an audit trail. '
      + 'Before generating, read the installed skill copy at '
      + '.agents/skills/visual-explainer/references/css-patterns.md and '
      + '.agents/skills/visual-explainer/templates/architecture.html and use '
      + 'their patterns. Do not open a browser in this noninteractive test. '
      + 'Do not use external images or runtime CDN scripts. Include a title, '
      + 'the four stages in order, visible connecting flow, semantic headings, '
      + 'and a short audit-trail note. After writing the file, report the exact '
      + 'installed files you read and the output path.',
  }),
});

function fixtureFor(id) {
  if (!Object.hasOwn(VISUAL_EXPLAINER_FIXTURES, id)) {
    throw new Error(`Unsupported visual-explainer fixture: ${id}`);
  }
  return VISUAL_EXPLAINER_FIXTURES[id];
}

function childPath(root, child, label) {
  const absoluteRoot = resolve(root);
  const absoluteChild = resolve(absoluteRoot, child);
  const fromRoot = relative(absoluteRoot, absoluteChild);
  if (
    !fromRoot
    || fromRoot.startsWith('..')
    || isAbsolute(fromRoot)
  ) {
    throw new Error(`${label} must resolve below the disposable project`);
  }
  return absoluteChild;
}

function requireRegularFile(path, label) {
  if (!existsSync(path)) throw new Error(`Missing ${label}: ${path}`);
  const stat = lstatSync(path);
  if (!stat.isFile() || stat.isSymbolicLink()) {
    throw new Error(`${label} must be a regular file: ${path}`);
  }
}

function requireDirectory(path, label) {
  if (!existsSync(path)) throw new Error(`Missing ${label}: ${path}`);
  const stat = lstatSync(path);
  if (!stat.isDirectory() || stat.isSymbolicLink()) {
    throw new Error(`${label} must be a real directory: ${path}`);
  }
}

function requireContainedRealPath(path, root, label) {
  const realRoot = realpathSync(root);
  const realPath = realpathSync(path);
  const fromRoot = relative(realRoot, realPath);
  if (
    !fromRoot
    || fromRoot.startsWith('..')
    || isAbsolute(fromRoot)
  ) {
    throw new Error(`${label} escapes the installed skill root: ${path}`);
  }
}

export function verifyVisualExplainerInstall(projectDir, fixtureId) {
  const fixture = fixtureFor(fixtureId);
  const project = resolve(projectDir);
  requireDirectory(project, 'disposable project');
  const skillRoot = childPath(
    project,
    '.agents/skills/visual-explainer',
    'Installed skill root',
  );
  requireDirectory(skillRoot, 'installed skill root');
  requireContainedRealPath(skillRoot, project, 'Installed skill root');
  const skillFile = resolve(skillRoot, 'SKILL.md');
  requireRegularFile(skillFile, 'installed SKILL.md');
  requireContainedRealPath(skillFile, skillRoot, 'installed SKILL.md');
  for (const resource of fixture.resources) {
    const resourcePath = resolve(skillRoot, resource);
    requireRegularFile(
      resourcePath,
      `installed resource ${resource}`,
    );
    requireContainedRealPath(
      resourcePath,
      skillRoot,
      `installed resource ${resource}`,
    );
  }
  return { project, skillRoot };
}

export function verifyVisualExplainerOutput(projectDir, fixtureId) {
  const fixture = fixtureFor(fixtureId);
  const { project, skillRoot } = verifyVisualExplainerInstall(
    projectDir,
    fixtureId,
  );
  const outputPath = childPath(project, fixture.output, 'Fixture output');
  requireRegularFile(outputPath, 'fixture output');
  const html = readFileSync(outputPath, 'utf8');

  const requiredPatterns = [
    [/<!doctype html>/iu, 'HTML doctype'],
    [/<html\b[^>]*\blang=["']en["']/iu, 'English document language'],
    [/<meta\b[^>]*\bname=["']viewport["']/iu, 'viewport metadata'],
    [/<title>[^<]+<\/title>/iu, 'document title'],
    [/<main\b/iu, 'main landmark'],
    [/<h1\b/iu, 'primary heading'],
    [/<h2\b/iu, 'section heading'],
    [/<svg\b|class=["'][^"']*(?:connector|flow-arrow|pipeline__arrow)[^"']*["']/iu,
      'visible connecting flow'],
  ];
  for (const [pattern, label] of requiredPatterns) {
    if (!pattern.test(html)) throw new Error(`Fixture output is missing ${label}`);
  }

  if ((html.match(/<h1\b/giu) ?? []).length !== 1) {
    throw new Error('Fixture output must contain exactly one primary heading');
  }

  let previousIndex = -1;
  for (const text of fixture.requiredText) {
    const index = html.indexOf(text);
    if (index === -1) {
      throw new Error(`Fixture output is missing required text: ${text}`);
    }
    if (index <= previousIndex) {
      throw new Error(`Fixture output text is out of order: ${text}`);
    }
    previousIndex = index;
  }

  if (/<script\b[^>]*\bsrc\s*=\s*["']https?:\/\//iu.test(html)) {
    throw new Error('Fixture output must not load a runtime script from a CDN');
  }

  return {
    project,
    skillRoot,
    outputPath,
    bytes: Buffer.byteLength(html),
  };
}

export function buildVisualExplainerInvocation(
  client,
  fixtureId,
  {
    projectDir,
    codexHome,
    unboxed = false,
  } = {},
) {
  if (client !== 'codex') {
    throw new Error(`Unsupported visual-explainer pilot client: ${client}`);
  }
  if (!projectDir) throw new Error('A disposable --project directory is required');
  if (!codexHome) {
    throw new Error('CODEX_HOME is required for the visual-explainer runtime pilot');
  }
  const fixture = fixtureFor(fixtureId);
  const cwd = resolve(projectDir);
  const isolationArgs = unboxed
    ? ['--dangerously-bypass-approvals-and-sandbox']
    : ['--sandbox', 'workspace-write'];

  return {
    command: 'codex',
    args: [
      'exec',
      '--ignore-user-config',
      '--ignore-rules',
      '--ephemeral',
      ...isolationArgs,
      '--skip-git-repo-check',
      '-C',
      cwd,
      '--json',
      `$visual-explainer ${fixture.prompt}`,
    ],
    cwd,
    env: { CODEX_HOME: resolve(codexHome) },
  };
}

export function runVisualExplainerPilot(
  invocation,
  {
    run = spawnSync,
    env = process.env,
  } = {},
) {
  const result = run(invocation.command, invocation.args, {
    cwd: invocation.cwd,
    env: { ...env, ...invocation.env },
    shell: false,
    stdio: 'inherit',
    timeout: VISUAL_EXPLAINER_TIMEOUT_MS,
    windowsHide: true,
  });
  if (result.status !== 0) {
    throw new Error(
      `${invocation.command} visual-explainer pilot failed with status `
      + `${result.status ?? 'unknown'}`,
    );
  }
}

export function parseCliArgs(args) {
  const [client, fixtureId, ...options] = args;
  let projectDir;
  let unboxed = false;
  let dryRun = false;
  let verifyOnly = false;

  for (let index = 0; index < options.length; index += 1) {
    const option = options[index];
    if (option === '--project') {
      const value = options[index + 1];
      if (!value || value.startsWith('--')) {
        throw new Error('--project requires a directory value');
      }
      projectDir = value;
      index += 1;
    } else if (option === '--unboxed') {
      unboxed = true;
    } else if (option === '--dry-run') {
      dryRun = true;
    } else if (option === '--verify-only') {
      verifyOnly = true;
    } else {
      throw new Error(`Unsupported option: ${option}`);
    }
  }

  if (!client || !fixtureId) {
    throw new Error(
      'Usage: node scripts/visual-explainer-runtime-pilot.mjs '
      + 'codex <fixture-id> --project <disposable-project> '
      + '[--unboxed] [--dry-run|--verify-only]',
    );
  }
  if (client !== 'codex') {
    throw new Error(`Unsupported visual-explainer pilot client: ${client}`);
  }
  fixtureFor(fixtureId);
  if (!projectDir) throw new Error('A disposable --project directory is required');
  if (dryRun && verifyOnly) {
    throw new Error('--dry-run and --verify-only cannot be combined');
  }
  return {
    client,
    fixtureId,
    projectDir,
    unboxed,
    dryRun,
    verifyOnly,
  };
}

function runCli() {
  const {
    client,
    fixtureId,
    projectDir,
    unboxed,
    dryRun,
    verifyOnly,
  } = parseCliArgs(process.argv.slice(2));

  if (verifyOnly) {
    const result = verifyVisualExplainerOutput(projectDir, fixtureId);
    console.log(`PASS ${fixtureId}: ${result.bytes} bytes at ${result.outputPath}`);
    return;
  }

  const invocation = buildVisualExplainerInvocation(client, fixtureId, {
    projectDir,
    codexHome: process.env.CODEX_HOME,
    unboxed,
  });

  if (dryRun) {
    console.log(JSON.stringify(invocation, null, 2));
    return;
  }

  verifyVisualExplainerInstall(projectDir, fixtureId);
  const outputPath = childPath(
    resolve(projectDir),
    fixtureFor(fixtureId).output,
    'Fixture output',
  );
  if (existsSync(outputPath)) {
    throw new Error(`Refusing to reuse an existing fixture output: ${outputPath}`);
  }
  runVisualExplainerPilot(invocation);
  const result = verifyVisualExplainerOutput(projectDir, fixtureId);
  console.log(`PASS ${fixtureId}: ${result.bytes} bytes at ${result.outputPath}`);
}

const entryPoint = process.argv[1] ? pathToFileURL(resolve(process.argv[1])).href : '';
if (entryPoint === import.meta.url) {
  try {
    runCli();
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
