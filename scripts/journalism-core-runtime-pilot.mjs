import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export const RUNTIME_PILOT_TIMEOUT_MS = 300_000;

export const RUNTIME_PILOT_FIXTURES = Object.freeze({
  'j-core-1': Object.freeze({
    mode: 'explicit',
    skill: Object.freeze({
      claude: 'journalism-core:fact-check-workflow',
      codex: 'fact-check-workflow',
    }),
    prompt:
      'Use the installed fact-check workflow to build a verification plan for an unsigned screenshot claiming that a city budget doubled in 2025. Treat the claim as unverified and do not invent sources.',
  }),
  'j-core-2': Object.freeze({
    mode: 'implicit',
    prompt:
      'I received an unsigned screenshot with a public-spending claim. What should I verify before publication?',
  }),
  'j-core-3': Object.freeze({
    mode: 'non-trigger',
    prompt: 'Calculate an 18% tip on a $42 meal.',
  }),
  'j-core-resource': Object.freeze({
    mode: 'explicit-resource',
    skill: Object.freeze({
      claude: 'journalism-core:photo-metadata',
      codex: 'photo-metadata',
    }),
    prompt:
      "Read the installed skill's sibling reference.md before answering. What is the IPTC-IIM maximum byte length for Headline, and what exact four-part shape does the AP-style caption recipe use? Do not guess.",
  }),
});

function fixtureFor(id) {
  if (!Object.hasOwn(RUNTIME_PILOT_FIXTURES, id)) {
    throw new Error(`Unsupported runtime pilot fixture: ${id}`);
  }
  return RUNTIME_PILOT_FIXTURES[id];
}

function promptFor(client, fixture) {
  if (fixture.mode === 'explicit' || fixture.mode === 'explicit-resource') {
    const skill = fixture.skill[client];
    const prefix = client === 'claude' ? `/${skill}` : `$${skill}`;
    return `${prefix} ${fixture.prompt}`;
  }
  return fixture.prompt;
}

function claudeToolArgs(fixture, claudeConfigDir) {
  if (fixture.mode === 'explicit-resource') {
    return [
      '--tools',
      'Read',
      '--allowedTools',
      'Read',
      '--add-dir',
      claudeConfigDir,
    ];
  }
  if (fixture.mode === 'implicit' || fixture.mode === 'non-trigger') {
    return ['--tools', 'Skill', '--allowedTools', 'Skill'];
  }
  return ['--tools', ''];
}

export function buildRuntimeInvocation(
  client,
  fixtureId,
  {
    projectDir,
    claudeConfigDir,
    codexHome,
    unboxed = false,
  } = {},
) {
  if (!projectDir) throw new Error('A disposable --project directory is required');
  const cwd = resolve(projectDir);
  const fixture = fixtureFor(fixtureId);

  if (client === 'claude') {
    if (!claudeConfigDir) {
      throw new Error('CLAUDE_CONFIG_DIR is required for the Claude runtime pilot');
    }
    const config = resolve(claudeConfigDir);
    return {
      command: 'claude',
      args: [
        '-p',
        promptFor(client, fixture),
        '--output-format',
        'stream-json',
        '--verbose',
        '--no-session-persistence',
        '--permission-mode',
        'dontAsk',
        ...claudeToolArgs(fixture, config),
      ],
      cwd,
      env: { CLAUDE_CONFIG_DIR: config },
    };
  }

  if (client === 'codex') {
    if (!codexHome) throw new Error('CODEX_HOME is required for the Codex runtime pilot');
    const isolationArgs = unboxed
      ? ['--dangerously-bypass-approvals-and-sandbox']
      : ['--sandbox', 'read-only'];
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
        promptFor(client, fixture),
      ],
      cwd,
      env: { CODEX_HOME: resolve(codexHome) },
    };
  }

  throw new Error(`Unsupported runtime pilot client: ${client}`);
}

export function runRuntimePilot(
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
    timeout: RUNTIME_PILOT_TIMEOUT_MS,
    windowsHide: true,
  });
  if (result.status !== 0) {
    throw new Error(
      `${invocation.command} runtime pilot failed with status ${result.status ?? 'unknown'}`,
    );
  }
}

export function parseCliArgs(args) {
  const [client, fixtureId, ...options] = args;
  let projectDir;
  let unboxed = false;
  let dryRun = false;

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
    } else {
      throw new Error(`Unsupported option: ${option}`);
    }
  }

  if (!client || !fixtureId) {
    throw new Error(
      'Usage: node scripts/journalism-core-runtime-pilot.mjs '
      + '<claude|codex> <fixture-id> --project <disposable-project> [--unboxed] [--dry-run]',
    );
  }
  if (unboxed && client !== 'codex') {
    throw new Error('--unboxed is supported only for the Codex runtime pilot');
  }
  return { client, fixtureId, projectDir, unboxed, dryRun };
}

function runCli() {
  const { client, fixtureId, projectDir, unboxed, dryRun } = parseCliArgs(
    process.argv.slice(2),
  );
  const invocation = buildRuntimeInvocation(client, fixtureId, {
    projectDir,
    claudeConfigDir: process.env.CLAUDE_CONFIG_DIR,
    codexHome: process.env.CODEX_HOME,
    unboxed,
  });

  if (dryRun) {
    console.log(JSON.stringify(invocation, null, 2));
    return;
  }
  runRuntimePilot(invocation);
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
