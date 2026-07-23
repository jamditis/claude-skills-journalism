import assert from 'node:assert/strict';
import {
  mkdtempSync,
  mkdirSync,
  rmSync,
  symlinkSync,
  unlinkSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import {
  afterEach,
  test,
} from 'node:test';

import {
  VISUAL_EXPLAINER_FIXTURES,
  VISUAL_EXPLAINER_TIMEOUT_MS,
  buildVisualExplainerInvocation,
  parseCliArgs,
  runVisualExplainerPilot,
  verifyVisualExplainerInstall,
  verifyVisualExplainerOutput,
} from './visual-explainer-runtime-pilot.mjs';

const projectDir = '/tmp/visual-explainer-runtime/project';
const codexHome = '/tmp/visual-explainer-runtime/codex';
const disposableRoots = [];

const validHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Newsroom flow</title>
</head>
<body>
  <main>
    <h1>Newsroom flow</h1>
    <h2>Four stages</h2>
    <section class="pipeline">
      <article><h3>Receive tips</h3></article>
      <svg aria-hidden="true"></svg>
      <article><h3>Verify evidence</h3></article>
      <article><h3>Assign an editor</h3></article>
      <article><h3>Publish corrected story</h3></article>
    </section>
    <aside><h2>Audit trail</h2></aside>
  </main>
</body>
</html>`;

function createFixtureProject(html = validHtml) {
  const root = mkdtempSync(join(tmpdir(), 'visual-explainer-pilot-test-'));
  disposableRoots.push(root);
  const skillRoot = join(root, '.agents', 'skills', 'visual-explainer');
  mkdirSync(join(skillRoot, 'references'), { recursive: true });
  mkdirSync(join(skillRoot, 'templates'), { recursive: true });
  writeFileSync(join(skillRoot, 'SKILL.md'), '---\nname: visual-explainer\n---\n');
  writeFileSync(join(skillRoot, 'references', 'css-patterns.md'), '# CSS\n');
  writeFileSync(join(skillRoot, 'templates', 'architecture.html'), '<main></main>\n');
  writeFileSync(join(root, 'v-ex-1.html'), html);
  return root;
}

afterEach(() => {
  for (const root of disposableRoots.splice(0)) {
    rmSync(root, { recursive: true, force: true });
  }
});

test('V-ex-1 preserves the accepted prompt, resources, and output contract', () => {
  assert.deepEqual(Object.keys(VISUAL_EXPLAINER_FIXTURES), ['v-ex-1']);
  const fixture = VISUAL_EXPLAINER_FIXTURES['v-ex-1'];
  assert.equal(fixture.output, 'v-ex-1.html');
  assert.deepEqual(fixture.resources, [
    'references/css-patterns.md',
    'templates/architecture.html',
  ]);
  assert.match(fixture.prompt, /newsroom receives tips, verifies evidence/u);
  assert.match(fixture.prompt, /Do not use external images or runtime CDN scripts/u);
});

test('Codex invocation uses the project standards skill and writable sandbox', () => {
  const invocation = buildVisualExplainerInvocation('codex', 'v-ex-1', {
    projectDir,
    codexHome,
  });
  assert.equal(invocation.command, 'codex');
  assert.equal(invocation.cwd, projectDir);
  assert.deepEqual(invocation.env, { CODEX_HOME: codexHome });
  assert.ok(invocation.args.includes('--ignore-user-config'));
  assert.ok(invocation.args.includes('--ignore-rules'));
  assert.ok(invocation.args.includes('--ephemeral'));
  assert.deepEqual(
    invocation.args.slice(
      invocation.args.indexOf('--sandbox'),
      invocation.args.indexOf('--sandbox') + 2,
    ),
    ['--sandbox', 'workspace-write'],
  );
  assert.match(invocation.args.at(-1), /^\$visual-explainer Create/u);
  assert.match(
    invocation.args.at(-1),
    /\.agents\/skills\/visual-explainer\/templates\/architecture\.html/u,
  );
});

test('authorized unboxed fallback replaces the nested writable sandbox', () => {
  const invocation = buildVisualExplainerInvocation('codex', 'v-ex-1', {
    projectDir,
    codexHome,
    unboxed: true,
  });
  assert.ok(invocation.args.includes('--dangerously-bypass-approvals-and-sandbox'));
  assert.ok(!invocation.args.includes('--sandbox'));
});

test('fixture verifier accepts installed resources and semantic ordered output', () => {
  const root = createFixtureProject();
  const install = verifyVisualExplainerInstall(root, 'v-ex-1');
  assert.equal(
    install.skillRoot,
    join(root, '.agents', 'skills', 'visual-explainer'),
  );
  const output = verifyVisualExplainerOutput(root, 'v-ex-1');
  assert.equal(output.outputPath, join(root, 'v-ex-1.html'));
  assert.equal(output.bytes, Buffer.byteLength(validHtml));
});

test('fixture verifier rejects missing resources and malformed output', () => {
  const missingResource = createFixtureProject();
  unlinkSync(join(
    missingResource,
    '.agents',
    'skills',
    'visual-explainer',
    'references',
    'css-patterns.md',
  ));
  assert.throws(
    () => verifyVisualExplainerInstall(missingResource, 'v-ex-1'),
    /Missing installed resource references\/css-patterns\.md/u,
  );

  const outOfOrder = createFixtureProject(
    validHtml.replace('Receive tips', '__TEMP_STAGE__')
      .replace('Publish corrected story', 'Receive tips')
      .replace('__TEMP_STAGE__', 'Publish corrected story'),
  );
  assert.throws(
    () => verifyVisualExplainerOutput(outOfOrder, 'v-ex-1'),
    /Fixture output text is out of order/u,
  );

  const remoteRuntime = createFixtureProject(
    validHtml.replace('</head>', '<script src="https://cdn.example/app.js"></script></head>'),
  );
  assert.throws(
    () => verifyVisualExplainerOutput(remoteRuntime, 'v-ex-1'),
    /must not load a runtime script from a CDN/u,
  );
});

test('install verifier rejects a required resource behind a linked parent', () => {
  const root = createFixtureProject();
  const skillRoot = join(root, '.agents', 'skills', 'visual-explainer');
  const externalReferences = join(root, 'external-references');
  mkdirSync(externalReferences);
  writeFileSync(join(externalReferences, 'css-patterns.md'), '# External CSS\n');
  rmSync(join(skillRoot, 'references'), { recursive: true });
  symlinkSync(externalReferences, join(skillRoot, 'references'), 'dir');

  assert.throws(
    () => verifyVisualExplainerInstall(root, 'v-ex-1'),
    /installed resource references\/css-patterns\.md escapes the installed skill root/u,
  );
});

test('runtime runner avoids a shell and preserves timeout and environment', () => {
  const calls = [];
  runVisualExplainerPilot(
    {
      command: 'fixture-client',
      args: ['--json'],
      cwd: projectDir,
      env: { CODEX_HOME: codexHome },
    },
    {
      env: { PATH: '/bin' },
      run: (command, args, options) => {
        calls.push({ command, args, options });
        return { status: 0 };
      },
    },
  );

  assert.equal(VISUAL_EXPLAINER_TIMEOUT_MS, 300_000);
  assert.equal(calls[0].options.shell, false);
  assert.equal(calls[0].options.timeout, VISUAL_EXPLAINER_TIMEOUT_MS);
  assert.deepEqual(calls[0].options.env, {
    PATH: '/bin',
    CODEX_HOME: codexHome,
  });
});

test('CLI and invocation reject ambiguous or unsupported inputs', () => {
  assert.throws(
    () => parseCliArgs(['codex', 'v-ex-1', '--project', '--unboxed']),
    /--project requires a directory value/u,
  );
  assert.throws(
    () => parseCliArgs(['codex', 'v-ex-1']),
    /A disposable --project directory is required/u,
  );
  assert.throws(
    () => parseCliArgs(['claude', 'v-ex-1', '--project', projectDir]),
    /Unsupported visual-explainer pilot client/u,
  );
  assert.throws(
    () => parseCliArgs(['codex', 'toString', '--project', projectDir]),
    /Unsupported visual-explainer fixture/u,
  );
  assert.throws(
    () => parseCliArgs([
      'codex',
      'v-ex-1',
      '--project',
      projectDir,
      '--dry-run',
      '--verify-only',
    ]),
    /cannot be combined/u,
  );
  assert.throws(
    () => buildVisualExplainerInvocation('claude', 'v-ex-1', {
      projectDir,
      codexHome,
    }),
    /Unsupported visual-explainer pilot client/u,
  );
  assert.throws(
    () => buildVisualExplainerInvocation('codex', 'toString', {
      projectDir,
      codexHome,
    }),
    /Unsupported visual-explainer fixture/u,
  );
  assert.throws(
    () => buildVisualExplainerInvocation('codex', 'v-ex-1', { projectDir }),
    /CODEX_HOME is required/u,
  );
  assert.deepEqual(
    parseCliArgs([
      'codex',
      'v-ex-1',
      '--project',
      projectDir,
      '--unboxed',
      '--verify-only',
    ]),
    {
      client: 'codex',
      fixtureId: 'v-ex-1',
      projectDir,
      unboxed: true,
      dryRun: false,
      verifyOnly: true,
    },
  );
});
