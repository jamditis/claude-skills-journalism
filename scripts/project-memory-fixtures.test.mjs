import assert from 'node:assert/strict';
import {
  mkdtempSync,
  mkdirSync,
  readFileSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  afterEach,
  test,
} from 'node:test';

import {
  PROJECT_MEMORY_FIXTURES,
  auditCommittedProjectMemorySkill,
  buildProjectMemoryInvocation,
  cleanupProjectMemoryFixture,
  prepareProjectMemoryFixture,
  verifyProjectMemoryNonTrigger,
  verifyProjectMemoryOutput,
} from './project-memory-fixtures.mjs';

const disposableRoots = [];
const repositoryRoot = fileURLToPath(new URL('..', import.meta.url));

function newProject(fixtureId) {
  const project = mkdtempSync(join(tmpdir(), `project-memory-${fixtureId}-`));
  disposableRoots.push(project);
  return {
    project,
    prepared: prepareProjectMemoryFixture(project, fixtureId),
  };
}

function writeAcceptedOutput(project, fixture) {
  const rootPath = join(project, fixture.output.root.path);
  const nestedPath = join(project, fixture.output.nested.path);
  writeFileSync(
    rootPath,
    `${fixture.existing.root}${fixture.output.root.requiredText.join('\n')}\n`,
  );
  writeFileSync(
    nestedPath,
    `${fixture.existing.nested}${fixture.output.nested.requiredText.join('\n')}\n`,
  );
}

afterEach(() => {
  for (const root of disposableRoots.splice(0)) {
    rmSync(root, { recursive: true, force: true });
  }
});

test('paired fixtures record activation, non-trigger, output, and cleanup contracts', () => {
  assert.deepEqual(Object.keys(PROJECT_MEMORY_FIXTURES), ['claude', 'codex']);

  const claude = PROJECT_MEMORY_FIXTURES.claude;
  const codex = PROJECT_MEMORY_FIXTURES.codex;
  assert.equal(claude.output.root.path, 'CLAUDE.md');
  assert.equal(claude.output.nested.path, 'packages/archive/CLAUDE.md');
  assert.equal(codex.output.root.path, 'AGENTS.md');
  assert.equal(codex.output.nested.path, 'packages/archive/AGENTS.md');
  assert.match(claude.activation.prompt, /preserve every existing line/iu);
  assert.match(codex.activation.prompt, /directory tree rooted at packages\/archive/u);
  assert.equal(claude.nonTrigger.expectedMutation, false);
  assert.equal(codex.nonTrigger.expectedMutation, false);
  assert.deepEqual(claude.cleanup.paths, [
    'CLAUDE.md',
    'packages/archive/CLAUDE.md',
  ]);
  assert.deepEqual(codex.cleanup.paths, [
    'AGENTS.md',
    'packages/archive/AGENTS.md',
  ]);
});

test('Claude fixture preserves existing guidance and keeps nested scope local', () => {
  const { project } = newProject('claude');
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  writeAcceptedOutput(project, fixture);

  const result = verifyProjectMemoryOutput(project, 'claude');
  assert.deepEqual(result.paths, [
    join(project, 'CLAUDE.md'),
    join(project, 'packages/archive/CLAUDE.md'),
  ]);
});

test('Codex fixture preserves existing guidance and keeps nested scope local', () => {
  const { project } = newProject('codex');
  const fixture = PROJECT_MEMORY_FIXTURES.codex;
  writeAcceptedOutput(project, fixture);

  const result = verifyProjectMemoryOutput(project, 'codex');
  assert.deepEqual(result.paths, [
    join(project, 'AGENTS.md'),
    join(project, 'packages/archive/AGENTS.md'),
  ]);
});

test('output verifier rejects overwritten guidance and scope leakage', () => {
  const overwritten = newProject('codex').project;
  const fixture = PROJECT_MEMORY_FIXTURES.codex;
  writeAcceptedOutput(overwritten, fixture);
  writeFileSync(
    join(overwritten, fixture.output.root.path),
    `${fixture.output.root.requiredText.join('\n')}\n`,
  );
  assert.throws(
    () => verifyProjectMemoryOutput(overwritten, 'codex'),
    /did not preserve the existing root guidance/u,
  );

  const leaked = newProject('claude').project;
  const claude = PROJECT_MEMORY_FIXTURES.claude;
  writeAcceptedOutput(leaked, claude);
  writeFileSync(
    join(leaked, claude.output.root.path),
    `${readFileSync(join(leaked, claude.output.root.path), 'utf8')}`
      + `${claude.output.nested.requiredText[0]}\n`,
  );
  assert.throws(
    () => verifyProjectMemoryOutput(leaked, 'claude'),
    /root output contains nested-only guidance/iu,
  );

  const otherClientNested = newProject('codex').project;
  writeAcceptedOutput(otherClientNested, fixture);
  writeFileSync(
    join(otherClientNested, 'packages/archive/CLAUDE.md'),
    '# Wrong client output\n',
  );
  assert.throws(
    () => verifyProjectMemoryOutput(otherClientNested, 'codex'),
    /created the other client's packages\/archive\/CLAUDE\.md/u,
  );
});

test('output verifier rejects reordered sections and duplicated preserved lines', () => {
  const reordered = newProject('claude').project;
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  writeAcceptedOutput(reordered, fixture);
  writeFileSync(
    join(reordered, fixture.output.root.path),
    `${fixture.existing.root}${fixture.output.root.requiredText[1]}\n`
      + `${fixture.output.root.requiredText[0]}\n`,
  );
  assert.throws(
    () => verifyProjectMemoryOutput(reordered, 'claude'),
    /root output does not keep required guidance under its heading/iu,
  );

  const duplicatedLine = newProject('codex').project;
  const codex = PROJECT_MEMORY_FIXTURES.codex;
  writeAcceptedOutput(duplicatedLine, codex);
  writeFileSync(
    join(duplicatedLine, codex.output.root.path),
    `${readFileSync(join(duplicatedLine, codex.output.root.path), 'utf8')}`
      + '- Keep the manual sign-off before public releases.\n',
  );
  assert.throws(
    () => verifyProjectMemoryOutput(duplicatedLine, 'codex'),
    /did not preserve the existing root guidance exactly once/u,
  );
});

test('output verifier rejects other-client instruction files anywhere in the tree', () => {
  const { project } = newProject('codex');
  const fixture = PROJECT_MEMORY_FIXTURES.codex;
  writeAcceptedOutput(project, fixture);
  mkdirSync(join(project, '.claude'));
  writeFileSync(join(project, '.claude/CLAUDE.md'), '# Wrong client output\n');

  assert.throws(
    () => verifyProjectMemoryOutput(project, 'codex'),
    /created the other client's \.claude\/CLAUDE\.md/u,
  );
});

test('non-trigger check detects any instruction-file mutation', () => {
  const unchanged = newProject('codex');
  assert.doesNotThrow(() => verifyProjectMemoryNonTrigger(
    unchanged.project,
    'codex',
    unchanged.prepared.snapshot,
  ));

  writeFileSync(
    join(unchanged.project, 'AGENTS.md'),
    `${readFileSync(join(unchanged.project, 'AGENTS.md'), 'utf8')}changed\n`,
  );
  assert.throws(
    () => verifyProjectMemoryNonTrigger(
      unchanged.project,
      'codex',
      unchanged.prepared.snapshot,
    ),
    /non-trigger changed AGENTS\.md/u,
  );


  const createdOtherClientFile = newProject('codex');
  writeFileSync(
    join(createdOtherClientFile.project, 'packages/archive/CLAUDE.md'),
    '# Unexpected output\n',
  );
  assert.throws(
    () => verifyProjectMemoryNonTrigger(
      createdOtherClientFile.project,
      'codex',
      createdOtherClientFile.prepared.snapshot,
    ),
    /non-trigger changed packages\/archive\/CLAUDE\.md/u,
  );

  const createdUnrelatedFile = newProject('claude');
  writeFileSync(
    join(createdUnrelatedFile.project, 'README.md'),
    '# Unexpected output\n',
  );
  assert.throws(
    () => verifyProjectMemoryNonTrigger(
      createdUnrelatedFile.project,
      'claude',
      createdUnrelatedFile.prepared.snapshot,
    ),
    /non-trigger changed README\.md/u,
  );

  const createdEmptyDirectory = newProject('claude');
  mkdirSync(join(createdEmptyDirectory.project, 'empty-output'));
  assert.throws(
    () => verifyProjectMemoryNonTrigger(
      createdEmptyDirectory.project,
      'claude',
      createdEmptyDirectory.prepared.snapshot,
    ),
    /non-trigger changed empty-output/u,
  );
});

test('prepare and cleanup reject symlinked existing ancestors', () => {
  const prepareProject = mkdtempSync(join(tmpdir(), 'project-memory-symlink-prepare-'));
  const prepareOutside = mkdtempSync(join(tmpdir(), 'project-memory-symlink-outside-'));
  disposableRoots.push(prepareProject, prepareOutside);
  symlinkSync(prepareOutside, join(prepareProject, 'packages'));
  assert.throws(
    () => prepareProjectMemoryFixture(prepareProject, 'codex'),
    /Fixture input ancestor must not be a symbolic link/u,
  );
  assert.throws(
    () => readFileSync(join(prepareOutside, 'archive/AGENTS.md'), 'utf8'),
    /ENOENT/u,
  );

  const cleanupProject = newProject('claude').project;
  const cleanupOutside = mkdtempSync(join(tmpdir(), 'project-memory-cleanup-outside-'));
  disposableRoots.push(cleanupOutside);
  rmSync(join(cleanupProject, 'packages'), { recursive: true });
  mkdirSync(join(cleanupOutside, 'archive'));
  writeFileSync(join(cleanupOutside, 'archive/CLAUDE.md'), '# Keep me\n');
  symlinkSync(cleanupOutside, join(cleanupProject, 'packages'));
  assert.throws(
    () => cleanupProjectMemoryFixture(cleanupProject, 'claude'),
    /Cleanup path ancestor must not be a symbolic link/u,
  );
  assert.equal(
    readFileSync(join(cleanupOutside, 'archive/CLAUDE.md'), 'utf8'),
    '# Keep me\n',
  );
  assert.equal(
    readFileSync(join(cleanupProject, 'CLAUDE.md'), 'utf8'),
    PROJECT_MEMORY_FIXTURES.claude.existing.root,
  );
});

test('cleanup removes fixture outputs without deleting the disposable project', () => {
  const { project } = newProject('claude');
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  writeAcceptedOutput(project, fixture);
  const removed = cleanupProjectMemoryFixture(project, 'claude');
  assert.deepEqual(removed, fixture.cleanup.paths.map((path) => join(project, path)));
  assert.throws(
    () => readFileSync(join(project, 'CLAUDE.md'), 'utf8'),
    /ENOENT/u,
  );
  assert.throws(
    () => readFileSync(join(project, 'packages/archive/CLAUDE.md'), 'utf8'),
    /ENOENT/u,
  );
});

test('runtime invocations isolate both clients and target their own fixture', () => {
  const claude = buildProjectMemoryInvocation('claude', 'activation', {
    projectDir: '/tmp/project-memory/claude-project',
    claudeConfigDir: '/tmp/project-memory/claude-home',
  });
  assert.equal(claude.command, 'claude');
  assert.equal(claude.env.CLAUDE_CONFIG_DIR, '/tmp/project-memory/claude-home');
  assert.match(claude.args[1], /^\/project-templates-toolkit:project-memory /u);

  const codex = buildProjectMemoryInvocation('codex', 'activation', {
    projectDir: '/tmp/project-memory/codex-project',
    codexHome: '/tmp/project-memory/codex-home',
  });
  assert.equal(codex.command, 'codex');
  assert.equal(codex.env.CODEX_HOME, '/tmp/project-memory/codex-home');
  assert.ok(codex.args.includes('workspace-write'));
  assert.match(codex.args.at(-1), /^\$project-memory /u);
});

test('current shared skill proves the adapter boundary before a rewrite', () => {
  assert.deepEqual(auditCommittedProjectMemorySkill(), {
    claudeOutput: true,
    codexOutput: false,
    preservesExistingFiles: false,
    nestedCodexScope: false,
    classification: 'adapter-required',
  });
});

test('matrix and package wording keep the untested clients explicit', () => {
  const matrix = readFileSync(
    join(repositoryRoot, 'plans/codex-compatibility-matrix.md'),
    'utf8',
  );
  const packageReadme = readFileSync(
    join(repositoryRoot, 'project-templates-toolkit/README.md'),
    'utf8',
  );
  assert.match(
    matrix,
    /paired contract fixtures now pin Claude `CLAUDE\.md` and Codex `AGENTS\.md`/u,
  );
  assert.match(
    matrix,
    /`project-retrospective` and `template-selector` remain shared candidates/u,
  );
  assert.match(
    packageReadme,
    /Codex `AGENTS\.md` output is not supported yet/u,
  );
});
