import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import {
  accessSync,
  constants,
  existsSync,
  lstatSync,
  readFileSync,
  readdirSync,
  realpathSync,
  statSync,
  writeFileSync,
} from 'node:fs';
import {
  delimiter,
  isAbsolute,
  relative,
  resolve,
} from 'node:path';
import { pathToFileURL } from 'node:url';
import { isDeepStrictEqual } from 'node:util';

export const OKF_PILOT_TIMEOUT_MS = 300_000;
export const OKF_VALIDATION_TIMEOUT_MS = 60_000;

const PORTABLE_FILES = Object.freeze([
  'README.md',
  'SPEC.md',
  'bundle/concepts/example-concept.md',
  'bundle/concepts/index.md',
  'bundle/decisions/example-concept.md',
  'bundle/decisions/index.md',
  'bundle/index.md',
  'requirements.txt',
  'scripts/validate.py',
]);

const CLAUDE_ADAPTER_FILES = Object.freeze([
  '.claude/hooks/okf-anchor.py',
  '.claude/hooks/okf-orient.py',
  '.claude/settings.json',
]);

const COPIED_RESOURCES = Object.freeze([
  Object.freeze({ source: 'requirements.txt', output: 'requirements.txt' }),
  Object.freeze({ source: 'spec/SPEC.md', output: 'SPEC.md' }),
  Object.freeze({ source: 'scripts/validate.py', output: 'scripts/validate.py' }),
  Object.freeze({
    source: 'templates/hooks/okf-anchor.py',
    output: '.claude/hooks/okf-anchor.py',
  }),
  Object.freeze({
    source: 'templates/hooks/okf-orient.py',
    output: '.claude/hooks/okf-orient.py',
  }),
]);

const REQUIRED_INSTALLED_READS = Object.freeze([
  Object.freeze({
    path: '.agents/skills/okf-wiki/SKILL.md',
    marker: 'name: okf-wiki',
  }),
  Object.freeze({
    path: '.agents/skills/okf-wiki/spec/SPEC.md',
    marker: '# OKF spec v1',
  }),
]);

const OKF_REPORT_SCHEMA = Object.freeze({
  type: 'object',
  additionalProperties: false,
  required: [
    'installed_files_read',
    'commands_run',
    'files_created',
    'trust_or_approval_prompt',
    'notes',
  ],
  properties: {
    installed_files_read: {
      type: 'array',
      items: { type: 'string' },
    },
    commands_run: {
      type: 'array',
      items: { type: 'string' },
    },
    files_created: {
      type: 'array',
      items: { type: 'string' },
    },
    trust_or_approval_prompt: { type: 'boolean' },
    notes: { type: 'string' },
  },
});

export const OKF_PILOT_FIXTURES = Object.freeze({
  'okf-1': Object.freeze({
    target: 'okf-1',
    title: 'Codex no-Claude pilot',
    sections: Object.freeze(['concepts', 'decisions']),
    portableFiles: PORTABLE_FILES,
    claudeAdapterFiles: CLAUDE_ADAPTER_FILES,
    prompt:
      '$okf-wiki Scaffold an internal-only empty OKF knowledge base at '
      + './okf-1 titled "Codex no-Claude pilot" with exactly the sections '
      + 'concepts and decisions. All onboarding choices are settled: scaffold '
      + 'only, do not populate from sources, and do not publish. Use the '
      + 'installed skill copy under .agents/skills/okf-wiki. No Claude '
      + 'configuration is available outside this project, and do not invoke '
      + 'any Claude executable. Keep the default Claude hook generation '
      + 'enabled so this pilot can record '
      + 'those files as inert Claude adapter output; do not execute the hooks '
      + 'or treat them as Codex configuration. Do not read or write outside '
      + 'this disposable project and its supplied client home. Run the '
      + 'scaffolder once, validate the portable bundle, and report the exact '
      + 'installed files read, commands run, files created, and any trust or '
      + 'approval prompt. In installed_files_read, list only resources you '
      + 'inspected with a read command; list executed scripts only in '
      + 'commands_run. Read .agents/skills/okf-wiki/SKILL.md and '
      + '.agents/skills/okf-wiki/spec/SPEC.md in separate read commands, and '
      + 'report those exact paths without a leading ./. In files_created, '
      + 'list every generated file as a '
      + 'project-relative path beginning with ./okf-1/. Leave the generated '
      + 'project in place for verification.',
  }),
});

function fixtureFor(id) {
  if (!Object.hasOwn(OKF_PILOT_FIXTURES, id)) {
    throw new Error(`Unsupported okf-wiki fixture: ${id}`);
  }
  return OKF_PILOT_FIXTURES[id];
}

function childPath(root, child, label) {
  const absoluteRoot = resolve(root);
  const absoluteChild = resolve(absoluteRoot, child);
  const fromRoot = relative(absoluteRoot, absoluteChild);
  if (!fromRoot || fromRoot.startsWith('..') || isAbsolute(fromRoot)) {
    throw new Error(`${label} must resolve below the disposable project`);
  }
  return absoluteChild;
}

function requireDirectory(path, label) {
  if (!existsSync(path)) throw new Error(`Missing ${label}: ${path}`);
  const stat = lstatSync(path);
  if (!stat.isDirectory() || stat.isSymbolicLink()) {
    throw new Error(`${label} must be a real directory: ${path}`);
  }
}

function requireRegularFile(path, label) {
  if (!existsSync(path)) throw new Error(`Missing ${label}: ${path}`);
  const stat = lstatSync(path);
  if (!stat.isFile() || stat.isSymbolicLink()) {
    throw new Error(`${label} must be a regular file: ${path}`);
  }
}

function requireContainedRealPath(path, root, label) {
  const realRoot = realpathSync(root);
  const realPath = realpathSync(path);
  const fromRoot = relative(realRoot, realPath);
  if (!fromRoot || fromRoot.startsWith('..') || isAbsolute(fromRoot)) {
    throw new Error(`${label} escapes the installed skill root: ${path}`);
  }
}

function relativeFiles(root) {
  const files = [];

  function walk(directory, prefix = '') {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const relativePath = prefix ? `${prefix}/${entry.name}` : entry.name;
      const path = resolve(directory, entry.name);
      const stat = lstatSync(path);
      if (stat.isSymbolicLink()) {
        files.push(relativePath);
      } else if (stat.isDirectory()) {
        walk(path, relativePath);
      } else if (stat.isFile()) {
        files.push(relativePath);
      } else {
        throw new Error(`unsupported generated path: ${relativePath}`);
      }
    }
  }

  walk(root);
  return files.sort();
}

function sha256File(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex');
}

function installedResourceFiles(skillRoot) {
  const resources = relativeFiles(skillRoot);
  for (const resource of resources) {
    const resourcePath = resolve(skillRoot, resource);
    requireRegularFile(resourcePath, `installed resource ${resource}`);
    requireContainedRealPath(
      resourcePath,
      skillRoot,
      `installed resource ${resource}`,
    );
  }
  return resources;
}

export function verifyNoClaudePreconditions(
  projectDir,
  clientHome,
  fixtureId,
  { allowOutput = false } = {},
) {
  const fixture = fixtureFor(fixtureId);
  const project = resolve(projectDir);
  const home = resolve(clientHome);
  requireDirectory(project, 'disposable project');
  requireDirectory(home, 'disposable client home');
  if (existsSync(resolve(project, '.claude'))) {
    throw new Error('disposable project must not contain .claude before the pilot');
  }
  if (existsSync(resolve(home, '.claude'))) {
    throw new Error('disposable client home must not contain .claude');
  }
  const target = childPath(project, fixture.target, 'Fixture target');
  if (!allowOutput && existsSync(target)) {
    throw new Error('fixture target must not already exist');
  }
  if (allowOutput) requireDirectory(target, 'generated fixture target');
  return { project, home, target };
}

export function verifyNoClaudeExecutable({ env = process.env } = {}) {
  const pathValue = env.PATH ?? env.Path ?? env.path ?? '';
  const extensions = process.platform === 'win32'
    ? (env.PATHEXT ?? '.COM;.EXE;.BAT;.CMD').split(';')
    : [''];
  const accessMode = process.platform === 'win32'
    ? constants.F_OK
    : constants.X_OK;

  for (const directory of pathValue.split(delimiter)) {
    if (!directory) {
      throw new Error(
        'PATH must not contain empty entries for the no-Claude pilot',
      );
    }
    if (!isAbsolute(directory)) {
      throw new Error(
        `PATH entries must be absolute for the no-Claude pilot: ${directory}`,
      );
    }
    const searchDirectory = directory;
    for (const executableName of ['claude', 'claude-code']) {
      for (const extension of extensions) {
        const candidate = resolve(
          searchDirectory,
          `${executableName}${extension.toLowerCase()}`,
        );
        let available = false;
        try {
          if (statSync(candidate).isFile()) {
            accessSync(candidate, accessMode);
            available = true;
          }
        } catch {
          // Missing, non-executable, and inaccessible candidates are unavailable.
        }
        if (available) {
          throw new Error(
            `Claude executable must not be available on PATH: ${candidate}`,
          );
        }
      }
    }
  }
}

export function verifyOkfInstall(projectDir, fixtureId) {
  fixtureFor(fixtureId);
  const project = resolve(projectDir);
  requireDirectory(project, 'disposable project');
  const skillRoot = childPath(
    project,
    '.agents/skills/okf-wiki',
    'Installed skill root',
  );
  requireDirectory(skillRoot, 'installed skill root');
  requireContainedRealPath(skillRoot, project, 'Installed skill root');
  const resources = [
    'SKILL.md',
    'requirements.txt',
    'scripts/scaffold.py',
    'scripts/validate.py',
    'spec/SPEC.md',
    'templates/hooks/okf-anchor.py',
    'templates/hooks/okf-orient.py',
  ];
  for (const resource of resources) {
    const resourcePath = resolve(skillRoot, resource);
    requireRegularFile(resourcePath, `installed resource ${resource}`);
    requireContainedRealPath(
      resourcePath,
      skillRoot,
      `installed resource ${resource}`,
    );
  }
  return { project, skillRoot, resources };
}

export function snapshotOkfInstall(projectDir, fixtureId) {
  const install = verifyOkfInstall(projectDir, fixtureId);
  const resources = installedResourceFiles(install.skillRoot);
  const digests = {};
  for (const resource of resources) {
    digests[resource] = sha256File(resolve(install.skillRoot, resource));
  }
  return Object.freeze({
    skillRoot: install.skillRoot,
    resources: Object.freeze(resources),
    digests: Object.freeze(digests),
  });
}

export function verifyOkfInstallUnchanged(
  projectDir,
  fixtureId,
  snapshot,
) {
  if (!snapshot || typeof snapshot !== 'object') {
    throw new Error('A pre-run installed resource snapshot is required');
  }
  const install = verifyOkfInstall(projectDir, fixtureId);
  const resources = installedResourceFiles(install.skillRoot);
  if (
    snapshot.skillRoot !== install.skillRoot
    || !isDeepStrictEqual(snapshot.resources, resources)
  ) {
    throw new Error('installed skill inventory changed during the Codex run');
  }
  for (const resource of resources) {
    const digest = sha256File(resolve(install.skillRoot, resource));
    if (digest !== snapshot.digests?.[resource]) {
      throw new Error(
        `installed resource changed during the Codex run: ${resource}`,
      );
    }
  }
  return install;
}

export function verifyOkfOutput(
  projectDir,
  fixtureId,
  { installSnapshot } = {},
) {
  const fixture = fixtureFor(fixtureId);
  const project = resolve(projectDir);
  const target = childPath(project, fixture.target, 'Fixture target');
  requireDirectory(target, 'generated fixture target');

  const expected = [...fixture.portableFiles, ...fixture.claudeAdapterFiles].sort();
  const actual = relativeFiles(target);
  for (const relativePath of expected) {
    if (!actual.includes(relativePath)) {
      throw new Error(`missing generated file: ${relativePath}`);
    }
    const path = resolve(target, relativePath);
    const stat = lstatSync(path);
    if (!stat.isFile() || stat.isSymbolicLink()) {
      throw new Error(`generated file must be regular and not linked: ${relativePath}`);
    }
    requireContainedRealPath(path, target, `Generated file ${relativePath}`);
  }
  for (const relativePath of actual) {
    if (!expected.includes(relativePath)) {
      throw new Error(`unexpected generated file: ${relativePath}`);
    }
  }

  const snapshot = installSnapshot ?? snapshotOkfInstall(project, fixtureId);
  const { skillRoot } = verifyOkfInstallUnchanged(
    project,
    fixtureId,
    snapshot,
  );
  for (const { source, output } of COPIED_RESOURCES) {
    const sourcePath = resolve(skillRoot, source);
    requireRegularFile(sourcePath, `installed resource ${source}`);
    requireContainedRealPath(sourcePath, skillRoot, `Installed resource ${source}`);
    if (sha256File(resolve(target, output)) !== snapshot.digests[source]) {
      throw new Error(`generated file differs from installed source: ${output}`);
    }
  }

  const readmeLines = readFileSync(resolve(target, 'README.md'), 'utf8')
    .split(/\r?\n/u);
  if (readmeLines[0] !== `# ${fixture.title}`) {
    throw new Error('generated README title does not match the fixture');
  }

  const bundleIndexLines = readFileSync(
    resolve(target, 'bundle/index.md'),
    'utf8',
  ).split(/\r?\n/u);
  const bundleTitle = bundleIndexLines.find((line) => line.startsWith('# '));
  if (bundleTitle !== `# ${fixture.title}`) {
    throw new Error('generated bundle title does not match the fixture');
  }
  const sectionsHeading = bundleIndexLines.indexOf('## Sections');
  const sectionNavigation = sectionsHeading === -1
    ? []
    : bundleIndexLines
      .slice(sectionsHeading + 1)
      .filter((line) => line.length > 0);
  const expectedNavigation = fixture.sections.map(
    (section) => `- [${section}](${section}/index.md)`,
  );
  if (!isDeepStrictEqual(sectionNavigation, expectedNavigation)) {
    throw new Error('generated section navigation does not match the fixture');
  }
  for (const section of fixture.sections) {
    const sectionLines = readFileSync(
      resolve(target, `bundle/${section}/index.md`),
      'utf8',
    ).split(/\r?\n/u);
    if (sectionLines[0] !== `# ${section}`) {
      throw new Error(`generated section heading does not match: ${section}`);
    }
  }

  const settingsPath = resolve(target, '.claude/settings.json');
  let settings;
  try {
    settings = JSON.parse(readFileSync(settingsPath, 'utf8'));
  } catch (error) {
    throw new Error(`generated Claude settings are not valid JSON: ${error.message}`);
  }
  const interpreter = process.platform === 'win32' ? 'python' : 'python3';
  const expectedSettings = {
    hooks: {
      SessionStart: [{
        hooks: [{
          type: 'command',
          command: interpreter,
          args: ['${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-anchor.py'],
        }],
      }],
      PreToolUse: [{
        hooks: [{
          type: 'command',
          command: interpreter,
          args: ['${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-orient.py'],
        }],
      }],
    },
  };
  if (!isDeepStrictEqual(settings, expectedSettings)) {
    throw new Error('generated Claude settings do not match the expected adapter');
  }

  return {
    project,
    target,
    portableFiles: [...fixture.portableFiles],
    claudeAdapterFiles: [...fixture.claudeAdapterFiles],
    settings,
  };
}

export function buildOkfInvocation(
  client,
  fixtureId,
  {
    projectDir,
    clientHome,
    codexHome,
    unboxed = false,
  } = {},
) {
  if (client !== 'codex') {
    throw new Error(`Unsupported okf-wiki pilot client: ${client}`);
  }
  const fixture = fixtureFor(fixtureId);
  if (!projectDir) throw new Error('A disposable --project directory is required');
  if (!clientHome) throw new Error('A disposable --client-home directory is required');
  if (!codexHome) throw new Error('CODEX_HOME is required for the okf-wiki pilot');
  const cwd = resolve(projectDir);
  const home = resolve(clientHome);
  const homeFromProject = relative(cwd, home);
  const projectFromHome = relative(home, cwd);
  const isSameOrBelow = (pathFromRoot) =>
    !pathFromRoot
      || (!pathFromRoot.startsWith('..') && !isAbsolute(pathFromRoot));
  if (isSameOrBelow(homeFromProject) || isSameOrBelow(projectFromHome)) {
    throw new Error('disposable project and client home must not overlap');
  }
  const resolvedCodexHome = resolve(codexHome);
  const codexHomeFromClient = relative(home, resolvedCodexHome);
  if (
    !codexHomeFromClient
    || codexHomeFromClient.startsWith('..')
    || isAbsolute(codexHomeFromClient)
  ) {
    throw new Error('CODEX_HOME must resolve below the disposable client home');
  }
  const isolationArgs = unboxed
    ? ['--dangerously-bypass-approvals-and-sandbox']
    : ['--sandbox', 'workspace-write'];
  const reportSchemaPath = childPath(
    home,
    'okf-wiki-runtime-report-schema.json',
    'Report schema',
  );
  const transcriptPath = childPath(
    home,
    'okf-wiki-runtime-transcript.jsonl',
    'Transcript',
  );
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
      '--output-schema',
      reportSchemaPath,
      '--json',
      fixture.prompt,
    ],
    cwd,
    env: {
      CODEX_HOME: resolvedCodexHome,
      HOME: home,
      USERPROFILE: home,
    },
    unsetEnv: ['CLAUDE_CONFIG_DIR', 'CLAUDE_PROJECT_DIR'],
    fixtureId,
    reportSchemaPath,
    transcriptPath,
  };
}

function isolatedEnvironment(invocation, env) {
  const childEnv = { ...env, ...invocation.env };
  for (const name of invocation.unsetEnv ?? []) delete childEnv[name];
  return childEnv;
}

function commandMatchesReport(actual, reported) {
  const normalizedActual = shellCommandBody(actual);
  const normalizedReported = reported
    .trim()
    .replace(/\s+/gu, ' ');
  return normalizedActual === normalizedReported;
}

function shellCommandBody(command) {
  let body = command.trim();
  const shellPrefix = /^\/(?:usr\/)?bin\/bash\s+-lc\s+/u;
  if (shellPrefix.test(body)) {
    body = body.replace(shellPrefix, '');
    const quote = body[0];
    if ((quote === '"' || quote === "'") && body.at(-1) === quote) {
      body = body.slice(1, -1);
      if (quote === '"') {
        body = body
          .replace(/\\(["\\$`])/gu, '$1')
          .replace(/\\\r?\n/gu, '');
      }
    }
  }
  return body.replace(/\s+/gu, ' ').trim();
}

function escapeRegularExpression(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/gu, '\\$&');
}

function exactInstalledReadPath(command) {
  const body = shellCommandBody(command);
  for (const { path } of REQUIRED_INSTALLED_READS) {
    const resource = escapeRegularExpression(path);
    const acceptedPatterns = [
      new RegExp(`^cat\\s+${resource}$`, 'iu'),
      new RegExp(
        `^sed\\s+-n\\s+(["'])\\d+(?:,\\d+)?p\\1\\s+${resource}$`,
        'iu',
      ),
      new RegExp(`^head\\s+-n\\s+\\d+\\s+${resource}$`, 'iu'),
      new RegExp(`^tail\\s+-n\\s+\\+?\\d+\\s+${resource}$`, 'iu'),
      new RegExp(
        `^get-content\\s+(?:-literalpath\\s+)?${resource}`
          + String.raw`(?:\s+-totalcount\s+\d+)?$`,
        'iu',
      ),
      new RegExp(`^type\\s+${resource}$`, 'iu'),
    ];
    if (acceptedPatterns.some((pattern) => pattern.test(body))) return path;
  }
  return undefined;
}

export function parseCodexTranscript(
  transcript,
  fixtureId,
  { platform = process.platform } = {},
) {
  const fixture = fixtureFor(fixtureId);
  const lines = transcript.split(/\r?\n/u).filter((line) => line.trim());
  if (lines.length === 0) {
    throw new Error('Codex JSONL transcript is empty');
  }
  const events = lines.map((line, index) => {
    try {
      return JSON.parse(line);
    } catch (error) {
      throw new Error(
        `Codex transcript line ${index + 1} is not valid JSON: ${error.message}`,
      );
    }
  });
  for (const event of events) {
    const eventType = `${event?.type ?? ''} ${event?.item?.type ?? ''}`;
    if (/\b(?:approval|trust)(?:_|\.|-|$)/iu.test(eventType)) {
      throw new Error('Codex transcript contains a trust or approval prompt event');
    }
  }

  const completedItems = events
    .filter((event) => event?.type === 'item.completed')
    .map((event) => event.item);
  const commandRecords = completedItems.filter(
    (item) => item?.type === 'command_execution'
      && typeof item.command === 'string',
  );
  const commands = commandRecords.map((item) => item.command);
  const claudeExecutablePattern = new RegExp(
    String.raw`(?:^|[\s;&|()"'\x60])`
      + String.raw`(?:[^\s;&|()"'\x60]*[/\\])?`
      + String.raw`claude(?:-code)?(?:\.(?:exe|cmd|bat|com))?`
      + String.raw`(?=$|[\s;&|()"'\x60])`,
    'iu',
  );
  for (const command of commands) {
    const body = shellCommandBody(command);
    const normalizedBody = body.replaceAll('\\', '/').toLowerCase();
    if (normalizedBody.includes('.claude/')) {
      throw new Error(
        'Codex transcript accesses generated Claude adapter files',
      );
    }
    if (claudeExecutablePattern.test(body)) {
      throw new Error('Codex transcript invokes a Claude executable');
    }
  }

  const pythonCommand = platform === 'win32' ? 'python' : 'python3';
  const scaffoldPrefixPattern = new RegExp(
    String.raw`(?:^|&&\s+)`
      + `${escapeRegularExpression(pythonCommand)}`
      + String.raw`\s+`
      + String.raw`\.agents/skills/okf-wiki/scripts/scaffold\.py\s+`,
    'u',
  );
  const scaffoldRecords = commandRecords.filter((item) =>
    scaffoldPrefixPattern.test(shellCommandBody(item.command)),
  );
  const acceptedScaffoldPattern = new RegExp(
    String.raw`^(?:test\s+!\s+-e\s+\./`
      + `${escapeRegularExpression(fixture.target)}`
      + String.raw`\s+&&\s+)?`
      + `${escapeRegularExpression(pythonCommand)}`
      + String.raw`\s+`
      + String.raw`\.agents/skills/okf-wiki/scripts/scaffold\.py\s+`
      + String.raw`\./${escapeRegularExpression(fixture.target)}\s+`
      + String.raw`--title\s+(["'])`
      + `${escapeRegularExpression(fixture.title)}`
      + String.raw`\1\s+--sections\s+`
      + `${fixture.sections.map(escapeRegularExpression).join(',')}$`,
    'u',
  );
  if (
    scaffoldRecords.length !== 1
    || scaffoldRecords[0].status !== 'completed'
    || scaffoldRecords[0].exit_code !== 0
    || !acceptedScaffoldPattern.test(
      shellCommandBody(scaffoldRecords[0].command),
    )
  ) {
    throw new Error('Codex transcript must contain exactly one accepted scaffold command');
  }
  const scaffoldCommands = scaffoldRecords.map((item) => item.command);

  for (const { path, marker } of REQUIRED_INSTALLED_READS) {
    const successfulRead = commandRecords.some(
      (item) => item.status === 'completed'
        && item.exit_code === 0
        && exactInstalledReadPath(item.command) === path
        && typeof item.aggregated_output === 'string'
        && item.aggregated_output.includes(marker),
    );
    if (!successfulRead) {
      throw new Error(
        `Codex transcript is missing successful installed resource read: ${path}`,
      );
    }
  }

  const target = escapeRegularExpression(fixture.target);
  const acceptedTargetPrecheck = new RegExp(
    String.raw`^test\s+!\s+-e\s+\./${target}$`,
    'u',
  );
  const acceptedValidator = new RegExp(
    `^${escapeRegularExpression(pythonCommand)}\\s+`
      + String.raw`(?:scripts/validate\.py\s+--bundle\s+bundle`
      + `|\\./${target}/scripts/validate\\.py\\s+`
      + `--bundle\\s+\\./${target}/bundle)$`,
    'u',
  );
  const acceptedInventory = new RegExp(
    String.raw`^find\s+\./${target}\s+-type\s+f\s+-print\s+`
      + String.raw`\|\s+LC_ALL=C\s+sort$`,
    'u',
  );
  const validatorRecords = commandRecords.filter((item) =>
    acceptedValidator.test(shellCommandBody(item.command)),
  );
  if (
    validatorRecords.length !== 1
    || validatorRecords[0].status !== 'completed'
    || validatorRecords[0].exit_code !== 0
  ) {
    throw new Error(
      'Codex transcript must contain exactly one accepted validator command',
    );
  }
  const disallowedRecord = commandRecords.find((item) => {
    const body = shellCommandBody(item.command);
    return item.status !== 'completed'
      || item.exit_code !== 0
      || !(
        exactInstalledReadPath(body)
        || acceptedScaffoldPattern.test(body)
        || acceptedTargetPrecheck.test(body)
        || acceptedValidator.test(body)
        || acceptedInventory.test(body)
      );
  });
  if (disallowedRecord) {
    throw new Error(
      'Codex transcript command falls outside the accepted disposable command boundary: '
        + shellCommandBody(disallowedRecord.command),
    );
  }

  const reportItems = completedItems.filter(
    (item) => item?.type === 'agent_message' && typeof item.text === 'string',
  );
  if (reportItems.length === 0) {
    throw new Error('Codex transcript is missing the structured final report');
  }
  for (const item of reportItems) {
    try {
      const candidate = JSON.parse(item.text);
      if (candidate?.trust_or_approval_prompt === true) {
        throw new Error('Codex reported a trust or approval prompt');
      }
    } catch (error) {
      if (error.message === 'Codex reported a trust or approval prompt') {
        throw error;
      }
      // Only the final agent message is required to be the structured report.
    }
  }
  let report;
  try {
    report = JSON.parse(reportItems.at(-1).text);
  } catch (error) {
    throw new Error(`Codex final report is not valid JSON: ${error.message}`);
  }
  if (
    !report
    || !Array.isArray(report.installed_files_read)
    || !Array.isArray(report.commands_run)
    || !Array.isArray(report.files_created)
    || typeof report.trust_or_approval_prompt !== 'boolean'
    || typeof report.notes !== 'string'
  ) {
    throw new Error('Codex final report does not match the required evidence shape');
  }
  if (report.trust_or_approval_prompt) {
    throw new Error('Codex reported a trust or approval prompt');
  }
  const expectedFilesCreated = [
    ...fixture.portableFiles,
    ...fixture.claudeAdapterFiles,
  ].sort().map((path) => `./${fixture.target}/${path}`);
  const reportedFilesCreated = report.files_created.every(
    (path) => typeof path === 'string',
  )
    ? [...report.files_created].sort()
    : [];
  if (!isDeepStrictEqual(reportedFilesCreated, expectedFilesCreated)) {
    throw new Error(
      'Codex final report does not list the exact generated file inventory',
    );
  }
  const reportedReads = [...new Set(report.installed_files_read)].sort();
  if (
    !isDeepStrictEqual(
      reportedReads,
      REQUIRED_INSTALLED_READS.map(({ path }) => path).sort(),
    )
  ) {
    throw new Error('Codex final report does not list the exact installed files read');
  }
  const commandMismatchIndex = report.commands_run.findIndex(
    (reported, index) => index >= commands.length
      || typeof reported !== 'string'
      || !commandMatchesReport(commands[index], reported),
  );
  if (
    report.commands_run.length !== commands.length
    || commandMismatchIndex !== -1
  ) {
    throw new Error(
      'Codex final report does not exactly match the captured command log'
      + (
        commandMismatchIndex === -1
          ? ''
          : ` at command ${commandMismatchIndex + 1}`
      ),
    );
  }
  return {
    commands,
    events,
    report,
    scaffoldCommands,
  };
}

export function runOkfPilot(
  invocation,
  {
    run = spawnSync,
    env = process.env,
  } = {},
) {
  if (existsSync(invocation.reportSchemaPath)) {
    throw new Error(
      `Refusing to replace an existing report schema: ${invocation.reportSchemaPath}`,
    );
  }
  if (existsSync(invocation.transcriptPath)) {
    throw new Error(
      `Refusing to replace an existing transcript: ${invocation.transcriptPath}`,
    );
  }
  writeFileSync(
    invocation.reportSchemaPath,
    `${JSON.stringify(OKF_REPORT_SCHEMA, null, 2)}\n`,
    { encoding: 'utf8', flag: 'wx', mode: 0o600 },
  );
  const result = run(invocation.command, invocation.args, {
    cwd: invocation.cwd,
    env: isolatedEnvironment(invocation, env),
    encoding: 'utf8',
    shell: false,
    stdio: ['ignore', 'pipe', 'pipe'],
    timeout: OKF_PILOT_TIMEOUT_MS,
    windowsHide: true,
  });
  const transcript = result.stdout ?? '';
  writeFileSync(
    invocation.transcriptPath,
    transcript,
    { encoding: 'utf8', flag: 'wx', mode: 0o600 },
  );
  if (result.status !== 0) {
    throw new Error(
      `${invocation.command} okf-wiki pilot failed with status `
      + `${result.status ?? 'unknown'}: ${result.stderr ?? ''}`.trim(),
    );
  }
  return {
    ...parseCodexTranscript(transcript, invocation.fixtureId),
    transcriptPath: invocation.transcriptPath,
  };
}

export function runOkfValidation(
  projectDir,
  fixtureId,
  {
    pythonCommand = process.platform === 'win32' ? 'python' : 'python3',
    run = spawnSync,
    env = process.env,
  } = {},
) {
  const fixture = fixtureFor(fixtureId);
  const target = childPath(projectDir, fixture.target, 'Fixture target');
  requireDirectory(target, 'generated fixture target');
  const result = run(
    pythonCommand,
    ['scripts/validate.py', '--bundle', 'bundle'],
    {
      cwd: target,
      env,
      encoding: 'utf8',
      shell: false,
      timeout: OKF_VALIDATION_TIMEOUT_MS,
      windowsHide: true,
    },
  );
  if (result.status !== 0) {
    throw new Error(
      `generated OKF validation failed with status ${result.status ?? 'unknown'}: `
      + `${result.stderr ?? ''}`.trim(),
    );
  }
  if (!/\bPASS\b/u.test(result.stdout ?? '')) {
    throw new Error('generated OKF validation did not report PASS');
  }
  return {
    command: pythonCommand,
    stdout: result.stdout,
    target,
  };
}

export function verifyOkfPythonDependencies(
  {
    pythonCommand = process.platform === 'win32' ? 'python' : 'python3',
    run = spawnSync,
    env = process.env,
  } = {},
) {
  const result = run(
    pythonCommand,
    ['-c', 'import yaml'],
    {
      env,
      encoding: 'utf8',
      shell: false,
      timeout: OKF_VALIDATION_TIMEOUT_MS,
      windowsHide: true,
    },
  );
  if (result.status !== 0) {
    throw new Error(
      'PyYAML is required before running the okf-wiki pilot; install '
      + '.agents/skills/okf-wiki/requirements.txt into the selected '
      + 'Python environment',
    );
  }
  return { command: pythonCommand };
}

export function parseCliArgs(args) {
  const [client, fixtureId, ...options] = args;
  let projectDir;
  let clientHome;
  let unboxed = false;
  let dryRun = false;
  let verifyOnly = false;

  for (let index = 0; index < options.length; index += 1) {
    const option = options[index];
    if (option === '--project' || option === '--client-home') {
      const value = options[index + 1];
      if (!value || value.startsWith('--')) {
        throw new Error(`${option} requires a directory value`);
      }
      if (option === '--project') projectDir = value;
      else clientHome = value;
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
      'Usage: node scripts/okf-wiki-runtime-pilot.mjs codex okf-1 '
      + '--project <disposable-project> --client-home <disposable-home> '
      + '[--unboxed] [--dry-run|--verify-only]',
    );
  }
  if (client !== 'codex') {
    throw new Error(`Unsupported okf-wiki pilot client: ${client}`);
  }
  fixtureFor(fixtureId);
  if (!projectDir) throw new Error('A disposable --project directory is required');
  if (!clientHome) throw new Error('--client-home is required');
  if (dryRun && verifyOnly) {
    throw new Error('--dry-run and --verify-only cannot be combined');
  }
  return {
    client,
    fixtureId,
    projectDir,
    clientHome,
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
    clientHome,
    unboxed,
    dryRun,
    verifyOnly,
  } = parseCliArgs(process.argv.slice(2));

  if (verifyOnly) {
    verifyNoClaudePreconditions(projectDir, clientHome, fixtureId, {
      allowOutput: true,
    });
    verifyOkfInstall(projectDir, fixtureId);
    verifyOkfPythonDependencies();
    const output = verifyOkfOutput(projectDir, fixtureId);
    const validation = runOkfValidation(projectDir, fixtureId);
    console.log(JSON.stringify({
      fixture: fixtureId,
      target: output.target,
      portableFiles: output.portableFiles,
      claudeAdapterFiles: output.claudeAdapterFiles,
      validation: validation.stdout.trim(),
    }, null, 2));
    return;
  }

  const invocation = buildOkfInvocation(client, fixtureId, {
    projectDir,
    clientHome,
    codexHome: process.env.CODEX_HOME,
    unboxed,
  });
  if (dryRun) {
    console.log(JSON.stringify(invocation, null, 2));
    return;
  }

  verifyNoClaudeExecutable();
  verifyNoClaudePreconditions(projectDir, clientHome, fixtureId);
  const installSnapshot = snapshotOkfInstall(projectDir, fixtureId);
  verifyOkfPythonDependencies();
  const evidence = runOkfPilot(invocation);
  verifyOkfInstallUnchanged(
    projectDir,
    fixtureId,
    installSnapshot,
  );
  const output = verifyOkfOutput(projectDir, fixtureId, {
    installSnapshot,
  });
  const validation = runOkfValidation(projectDir, fixtureId);
  console.log(JSON.stringify({
    fixture: fixtureId,
    target: output.target,
    portableFiles: output.portableFiles,
    claudeAdapterFiles: output.claudeAdapterFiles,
    transcript: evidence.transcriptPath,
    commands: evidence.commands,
    installedFilesRead: evidence.report.installed_files_read,
    filesCreated: evidence.report.files_created,
    trustOrApprovalPrompt: evidence.report.trust_or_approval_prompt,
    validation: validation.stdout.trim(),
  }, null, 2));
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
