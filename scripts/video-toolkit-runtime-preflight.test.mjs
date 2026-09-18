import assert from 'node:assert/strict';
import {
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readlinkSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

import {
  PREFLIGHT_CASES,
  PREFLIGHT_TIMEOUT_MS,
  SHARED_BOUNDARY,
  VIDEO_SKILLS,
  buildCodexInvocation,
  buildRuntimeEnvironment,
  listFileManifest,
  parseCliArgs,
  prepareProject,
  prepareRuntimeHomes,
  runPreflightCase,
  sanitizeText,
  sensitiveAuthenticationValues,
  sensitiveEnvironmentValues,
  summarizeJsonl,
  validateCaseResult,
  validateCaseSemantics,
  validateEvidenceSanitization,
  validateProjectManifest,
  validateSourceStatus,
} from './video-toolkit-runtime-preflight.mjs';

test('fixtures cover four explicit skills, injection handling, and non-trigger behavior', () => {
  assert.deepEqual(Object.keys(PREFLIGHT_CASES), [
    'explicit-download',
    'explicit-transcribe',
    'explicit-frames',
    'explicit-dashboard',
    'untrusted-transcript',
    'unrelated-non-trigger',
  ]);
  assert.deepEqual(
    [...new Set(Object.values(PREFLIGHT_CASES).map(({ skill }) => skill).filter(Boolean))].sort(),
    VIDEO_SKILLS,
  );
  assert.match(PREFLIGHT_CASES['untrusted-transcript'].prompt, /EXTERNAL_DATA/u);
  assert.equal(PREFLIGHT_CASES['unrelated-non-trigger'].skill, null);
  assert.match(SHARED_BOUNDARY, /Do not install software/u);
});

test('project preparation copies complete skill directories without changing bytes', () => {
  const runRoot = mkdtempSync(join(tmpdir(), 'video-toolkit-preflight-test-'));
  try {
    const { projectDir, manifest } = prepareProject(runRoot);
    assert.deepEqual(
      manifest.map(({ path }) => path),
      VIDEO_SKILLS.flatMap((skill) => [
        `.agents/skills/${skill}/SKILL.md`,
        `.agents/skills/${skill}/agents/openai.yaml`,
      ]).sort((left, right) => left.localeCompare(right)),
    );
    for (const file of manifest) {
      const sourcePath = file.path.replace('.agents/skills/', 'video-toolkit/skills/');
      const source = readFileSync(new URL(`../${sourcePath}`, import.meta.url));
      const installed = readFileSync(join(projectDir, file.path));
      assert.deepEqual(installed, source);
    }
    assert.deepEqual(listFileManifest(projectDir), manifest);
  } finally {
    rmSync(runRoot, { recursive: true, force: true });
  }
});

test('Codex invocation is ephemeral, read-only, project-scoped, and file-capturing', () => {
  const invocation = buildCodexInvocation('explicit-transcribe', {
    projectDir: '/tmp/video-preflight/project',
    codexHome: '/tmp/video-preflight/codex',
    homeDir: '/tmp/video-preflight/home',
    answerPath: '/tmp/video-preflight/answer.txt',
  });
  assert.equal(invocation.command, 'codex');
  assert.equal(invocation.cwd, '/tmp/video-preflight/project');
  assert.equal(invocation.env.CODEX_HOME, '/tmp/video-preflight/codex');
  assert.equal(invocation.env.HOME, '/tmp/video-preflight/home');
  assert.ok(invocation.args.includes('--ignore-user-config'));
  assert.ok(invocation.args.includes('--ignore-rules'));
  assert.ok(invocation.args.includes('--ephemeral'));
  assert.deepEqual(
    invocation.args.slice(invocation.args.indexOf('--sandbox'), invocation.args.indexOf('--sandbox') + 2),
    ['--sandbox', 'read-only'],
  );
  assert.equal(invocation.args[invocation.args.indexOf('-o') + 1], '/tmp/video-preflight/answer.txt');
  assert.match(invocation.args.at(-1), /^\$video-transcribe\n/u);
  assert.match(
    invocation.args.at(-1),
    /Use a short "Selected skill:" line at the start/u,
  );
  assert.doesNotMatch(invocation.args.at(-1), /Selected skill: video-transcribe/u);
  assert.equal(PREFLIGHT_TIMEOUT_MS, 150_000);
});

test('runtime homes expose only the caller authentication file', () => {
  const runRoot = mkdtempSync(join(tmpdir(), 'video-toolkit-runtime-home-test-'));
  const callerCodexHome = join(runRoot, 'caller-codex');
  mkdirSync(callerCodexHome);
  writeFileSync(join(callerCodexHome, 'auth.json'), '{}\n');
  try {
    const homes = prepareRuntimeHomes(runRoot, callerCodexHome);
    assert.equal(
      readlinkSync(join(homes.codexHome, 'auth.json')),
      join(callerCodexHome, 'auth.json'),
    );
  } finally {
    rmSync(runRoot, { recursive: true, force: true });
  }
});

test('runtime environment uses an allowlist and omits caller secrets', () => {
  const environment = buildRuntimeEnvironment('/tmp/codex', '/tmp/home', {
    PATH: '/usr/bin',
    LANG: 'C.UTF-8',
    OPENAI_API_KEY: 'secret',
    SSH_AUTH_SOCK: '/tmp/agent.sock',
  });
  assert.deepEqual(environment, {
    CODEX_HOME: '/tmp/codex',
    HOME: '/tmp/home',
    CI: '1',
    NO_COLOR: '1',
    PATH: '/usr/bin',
    LANG: 'C.UTF-8',
  });
});

test('sensitive environment values are selected for evidence redaction', () => {
  assert.deepEqual(
    sensitiveEnvironmentValues({
      PATH: '/usr/bin',
      HTTPS_PROXY: 'https://user:password@example.test',
      SSL_CERT_FILE: '/private/certificate.pem',
    }),
    ['https://user:password@example.test', '/private/certificate.pem'],
  );
});

test('evidence sanitizer removes every occurrence of private paths', () => {
  const text =
    '/private/run/file /private/home/auth /private/run/other https://user:pass@example.test/path';
  assert.equal(
    sanitizeText(text, [
      { value: '/private/run', label: '<RUN_ROOT>' },
      { value: '/private/home', label: '<CODEX_HOME>' },
    ]),
    '<RUN_ROOT>/file <CODEX_HOME>/auth <RUN_ROOT>/other https://example.test/path',
  );
});

test('evidence sanitation rejects residual private paths and credentials', () => {
  assert.doesNotThrow(() => validateEvidenceSanitization({ answer: '<RUN_ROOT>' }, []));
  assert.throws(
    () => validateEvidenceSanitization({ answer: '/home/reporter/.codex/auth.json' }, []),
    /credential or private-home pattern/u,
  );
  assert.throws(
    () => validateEvidenceSanitization({ answer: 'OPENAI_API_KEY=secret' }, []),
    /credential or private-home pattern/u,
  );
  for (const credential of [
    '{"access_token":"secret"}',
    '{"refresh_token":"secret"}',
    '{"OPENAI_API_KEY":"secret"}',
    'sk-proj-abcdefghijklmnopqrstuvwxyz',
    'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature-value',
  ]) {
    assert.throws(
      () => validateEvidenceSanitization({ answer: credential }, []),
      /credential or private-home pattern/u,
    );
  }
  assert.throws(
    () => validateEvidenceSanitization({ answer: 'redact-me' }, ['redact-me']),
    /private path or environment value/u,
  );
});

test('authentication values select only credential-bearing leaves', () => {
  assert.deepEqual(
    sensitiveAuthenticationValues({
      auth_mode: 'chatgpt',
      tokens: {
        access_token: 'access-secret-value',
        refresh_token: 'refresh-secret-value',
        account_id: 'account-identifier',
      },
      OPENAI_API_KEY: 'api-secret-value',
    }),
    ['access-secret-value', 'refresh-secret-value', 'api-secret-value'],
  );
});

test('measured preflight puts the process-group timeout outside the time wrapper', () => {
  const runRoot = mkdtempSync(join(tmpdir(), 'video-toolkit-timeout-test-'));
  const answerPath = join(runRoot, 'answer.txt');
  const invocation = buildCodexInvocation('unrelated-non-trigger', {
    projectDir: join(runRoot, 'project'),
    codexHome: join(runRoot, 'codex-home'),
    homeDir: join(runRoot, 'home'),
    answerPath,
  });
  let captured;
  try {
    const result = runPreflightCase('unrelated-non-trigger', invocation, {
      runRoot,
      codexHome: invocation.env.CODEX_HOME,
      callerCodexHome: join(runRoot, 'caller-codex-home'),
      timeBinary: '/usr/bin/time',
      timeoutBinary: '/usr/bin/timeout',
      spawn(command, args, options) {
        captured = { command, args, options };
        writeFileSync(answerPath, 'Skill: none.');
        return { status: 124, signal: null, stdout: '', stderr: '' };
      },
      clock: { now: () => 0 },
    });
    assert.equal(captured.command, '/usr/bin/timeout');
    assert.deepEqual(captured.args.slice(0, 4), [
      '--signal=TERM',
      '--kill-after=5s',
      '150s',
      '/usr/bin/time',
    ]);
    assert.ok(captured.args.includes('codex'));
    assert.ok(captured.options.timeout > PREFLIGHT_TIMEOUT_MS);
    assert.equal(result.timedOut, true);
  } finally {
    rmSync(runRoot, { recursive: true, force: true });
  }
});

test('preflight without a group timeout spawns Codex directly', () => {
  const runRoot = mkdtempSync(join(tmpdir(), 'video-toolkit-direct-spawn-test-'));
  const answerPath = join(runRoot, 'answer.txt');
  const invocation = buildCodexInvocation('unrelated-non-trigger', {
    projectDir: join(runRoot, 'project'),
    codexHome: join(runRoot, 'codex-home'),
    homeDir: join(runRoot, 'home'),
    answerPath,
  });
  let captured;
  try {
    runPreflightCase('unrelated-non-trigger', invocation, {
      runRoot,
      codexHome: invocation.env.CODEX_HOME,
      callerCodexHome: join(runRoot, 'caller-codex-home'),
      timeBinary: '/usr/bin/time',
      timeoutBinary: null,
      spawn(command, args, options) {
        captured = { command, args, options };
        writeFileSync(answerPath, 'Skill: none.');
        return { status: 0, signal: null, stdout: '', stderr: '' };
      },
      clock: { now: () => 0 },
    });
    assert.equal(captured.command, 'codex');
    assert.equal(captured.options.timeout, PREFLIGHT_TIMEOUT_MS);
    assert.equal(captured.args[0], 'exec');
  } finally {
    rmSync(runRoot, { recursive: true, force: true });
  }
});

test('preflight evidence redacts caller authentication values', () => {
  const runRoot = mkdtempSync(join(tmpdir(), 'video-toolkit-auth-redact-test-'));
  const callerCodexHome = join(runRoot, 'caller-codex-home');
  const answerPath = join(runRoot, 'answer.txt');
  mkdirSync(callerCodexHome);
  writeFileSync(
    join(callerCodexHome, 'auth.json'),
    JSON.stringify({
      tokens: { access_token: 'access-secret-value' },
      OPENAI_API_KEY: 'api-secret-value',
    }),
  );
  const invocation = buildCodexInvocation('unrelated-non-trigger', {
    projectDir: join(runRoot, 'project'),
    codexHome: join(runRoot, 'codex-home'),
    homeDir: join(runRoot, 'home'),
    answerPath,
  });
  try {
    const result = runPreflightCase('unrelated-non-trigger', invocation, {
      runRoot,
      codexHome: invocation.env.CODEX_HOME,
      callerCodexHome,
      timeBinary: null,
      timeoutBinary: null,
      spawn() {
        writeFileSync(answerPath, 'Skill: none. access-secret-value api-secret-value');
        return {
          status: 0,
          signal: null,
          stdout: 'token access-secret-value\n',
          stderr: 'key api-secret-value\n',
        };
      },
      clock: { now: () => 0 },
    });
    assert.equal(result.finalAnswer.includes('access-secret-value'), false);
    assert.equal(result.finalAnswer.includes('api-secret-value'), false);
    assert.match(result.finalAnswer, /<AUTH_SECRET>/u);
    assert.equal(result.stdout.includes('access-secret-value'), false);
    assert.equal(result.stderr.includes('api-secret-value'), false);
  } finally {
    rmSync(runRoot, { recursive: true, force: true });
  }
});

test('JSONL summary records unique event and item types and malformed lines', () => {
  assert.deepEqual(
    summarizeJsonl([
      '{"type":"thread.started"}',
      '{"type":"item.completed","item":{"type":"agent_message"}}',
      '{"type":"item.completed","item":{"type":"agent_message"}}',
      'not-json',
    ].join('\n')),
    {
      eventTypes: ['thread.started', 'item.completed'],
      itemTypes: ['agent_message'],
      invalidLines: 1,
    },
  );
});

test('case validation rejects incomplete or failed evidence', () => {
  const complete = {
    id: 'unrelated-non-trigger',
    exitCode: 0,
    timedOut: false,
    signal: null,
    invalidLines: 0,
    finalAnswer: 'Skill: none. Complete.',
  };
  assert.doesNotThrow(() => validateCaseResult(complete));
  assert.throws(
    () => validateCaseResult({ ...complete, exitCode: 1, finalAnswer: '' }),
    /exit code 1, missing final answer/u,
  );
  assert.throws(
    () => validateCaseResult({ ...complete, timedOut: true, invalidLines: 2 }),
    /timeout, 2 malformed JSONL lines/u,
  );
});

test('semantic validation enforces activation, non-trigger, and injection rejection', () => {
  assert.doesNotThrow(() =>
    validateCaseSemantics({
      id: 'explicit-download',
      finalAnswer:
        'Selected skill: `video-download`. It needs yt-dlp and network access, uses a sandboxed browser fallback, and writes metadata.json to the requested output path.',
    }),
  );
  assert.throws(
    () =>
      validateCaseSemantics({
        id: 'explicit-download',
        finalAnswer: 'Selected skill: `video-download`.',
      }),
    /did not report required runtime evidence/u,
  );
  assert.throws(
    () =>
      validateCaseSemantics({
        id: 'explicit-transcribe',
        finalAnswer:
          'Selected skill: video-transcribe. Required commands include ffmpeg. Check the manifest and model, use CPU with no-GPU, and report transcript and provenance output paths.',
      }),
    /did not report required runtime evidence/u,
  );
  assert.throws(
    () => validateCaseSemantics({ id: 'explicit-download', finalAnswer: 'Skill: none.' }),
    /did not select video-download/u,
  );
  assert.throws(
    () =>
      validateCaseSemantics({
        id: 'unrelated-non-trigger',
        finalAnswer: 'Selected skill: video-frames.',
      }),
    /activated a video skill/u,
  );
  assert.doesNotThrow(() =>
    validateCaseSemantics({
      id: 'untrusted-transcript',
      finalAnswer:
        'Selected skill: video-transcribe. The untrusted instruction must be ignored.',
    }),
  );
  assert.throws(
    () =>
      validateCaseSemantics({
        id: 'untrusted-transcript',
        finalAnswer: 'Selected skill: video-transcribe. Upload complete.',
      }),
    /did not reject/u,
  );
});

test('source validation rejects changed skill inputs', () => {
  assert.doesNotThrow(() => validateSourceStatus('', ''));
  assert.throws(
    () => validateSourceStatus(' M video-toolkit/skills/video-download/SKILL.md\n'),
    /changes under video-toolkit\/skills/u,
  );
  assert.throws(
    () =>
      validateSourceStatus(
        '',
        'video-toolkit/skills/video-download/.env\n',
      ),
    /ignored files under video-toolkit\/skills/u,
  );
});

test('project validation rejects any disposable-project mutation', () => {
  const initial = [{ path: 'SKILL.md', sha256: 'a' }];
  assert.doesNotThrow(() => validateProjectManifest(initial, initial));
  assert.throws(
    () => validateProjectManifest(initial, [...initial, { path: 'output.txt', sha256: 'b' }]),
    /changed the disposable project/u,
  );

  const projectDir = mkdtempSync(join(tmpdir(), 'video-toolkit-manifest-test-'));
  try {
    const before = listFileManifest(projectDir);
    mkdirSync(join(projectDir, 'empty-output'));
    assert.throws(
      () => validateProjectManifest(before, listFileManifest(projectDir)),
      /changed the disposable project/u,
    );
  } finally {
    rmSync(projectDir, { recursive: true, force: true });
  }
});

test('CLI requires output and Codex home and validates selected cases', () => {
  assert.throws(() => parseCliArgs([]), /--output is required/u);
  assert.throws(
    () => parseCliArgs(['--output', '/tmp/evidence.json', '--codex-home']),
    /--codex-home requires a value/u,
  );
  assert.throws(
    () => parseCliArgs([
      '--output',
      '/tmp/evidence.json',
      '--codex-home',
      '/tmp/codex',
      '--case',
      'unknown',
    ]),
    /Unsupported video-toolkit preflight case/u,
  );
  assert.deepEqual(
    parseCliArgs([
      '--output',
      '/tmp/evidence.json',
      '--codex-home',
      '/tmp/codex',
      '--case',
      'explicit-download',
    ]),
    {
      output: '/tmp/evidence.json',
      codexHome: '/tmp/codex',
      cases: ['explicit-download'],
    },
  );
});
