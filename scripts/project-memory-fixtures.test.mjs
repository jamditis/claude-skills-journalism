import assert from 'node:assert/strict';
import fs from 'node:fs';
import { syncBuiltinESMExports } from 'node:module';
import {
  chmodSync,
  lstatSync,
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
const preparedSnapshots = new Map();
const repositoryRoot = fileURLToPath(new URL('..', import.meta.url));

function newProject(fixtureId) {
  const project = mkdtempSync(join(tmpdir(), `project-memory-${fixtureId}-`));
  disposableRoots.push(project);
  const fixture = {
    project,
    prepared: prepareProjectMemoryFixture(project, fixtureId),
  };
  preparedSnapshots.set(project, fixture.prepared.snapshot);
  return fixture;
}

function verifyOutput(project, client, preparedSnapshot = preparedSnapshots.get(project)) {
  return verifyProjectMemoryOutput(project, client, preparedSnapshot);
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
    preparedSnapshots.delete(root);
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

  const result = verifyOutput(project, 'claude');
  assert.deepEqual(result.paths, [
    join(project, 'CLAUDE.md'),
    join(project, 'packages/archive/CLAUDE.md'),
  ]);
});

test('Codex fixture preserves existing guidance and keeps nested scope local', () => {
  const { project } = newProject('codex');
  const fixture = PROJECT_MEMORY_FIXTURES.codex;
  writeAcceptedOutput(project, fixture);

  const result = verifyOutput(project, 'codex');
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
    () => verifyOutput(overwritten, 'codex'),
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
    () => verifyOutput(leaked, 'claude'),
    /root output contains nested-only guidance/iu,
  );

  const otherClientNested = newProject('codex').project;
  writeAcceptedOutput(otherClientNested, fixture);
  writeFileSync(
    join(otherClientNested, 'packages/archive/CLAUDE.md'),
    '# Wrong client output\n',
  );
  assert.throws(
    () => verifyOutput(otherClientNested, 'codex'),
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
    () => verifyOutput(reordered, 'claude'),
    /root output does not keep required guidance under its heading/iu,
  );

  const embeddedHeading = newProject('claude').project;
  writeAcceptedOutput(embeddedHeading, fixture);
  writeFileSync(
    join(embeddedHeading, fixture.output.root.path),
    `${fixture.existing.root}prefix ${fixture.output.root.requiredText[0]} suffix\n`
      + `${fixture.output.root.requiredText[1]}\n`,
  );
  assert.throws(
    () => verifyOutput(embeddedHeading, 'claude'),
    /required heading must be an exact Markdown line/iu,
  );

  const reorderedExisting = newProject('codex').project;
  const reorderedCodex = PROJECT_MEMORY_FIXTURES.codex;
  writeAcceptedOutput(reorderedExisting, reorderedCodex);
  writeFileSync(
    join(reorderedExisting, reorderedCodex.output.root.path),
    '# Existing project guidance\n\n'
      + '- Keep the manual sign-off before public releases.\n'
      + '## Release safety\n\n'
      + `${reorderedCodex.output.root.requiredText.join('\n')}\n`,
  );
  assert.throws(
    () => verifyOutput(reorderedExisting, 'codex'),
    /changed the order of existing root guidance/iu,
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
    () => verifyOutput(duplicatedLine, 'codex'),
    /did not preserve the existing root guidance exactly once/u,
  );
});

test('output verifier rejects guidance inside fenced code blocks and comments', () => {
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  const fenced = newProject('claude').project;
  writeAcceptedOutput(fenced, fixture);
  writeFileSync(
    join(fenced, fixture.output.root.path),
    `${fixture.existing.root}\`\`\`md\n${fixture.output.root.requiredText.join('\n')}\n\`\`\`\n`,
  );
  assert.throws(
    () => verifyOutput(fenced, 'claude'),
    /required heading must be an exact Markdown line/iu,
  );

  const commented = newProject('claude').project;
  writeAcceptedOutput(commented, fixture);
  writeFileSync(
    join(commented, fixture.output.root.path),
    `${fixture.existing.root}<!--\n${fixture.output.root.requiredText.join('\n')}\n-->\n`,
  );
  assert.throws(
    () => verifyOutput(commented, 'claude'),
    /required heading must be an exact Markdown line/iu,
  );

  const reopenedComment = newProject('claude').project;
  writeAcceptedOutput(reopenedComment, fixture);
  writeFileSync(
    join(reopenedComment, fixture.output.root.path),
    `${fixture.existing.root}<!-- closed --> <!--\n`
      + `${fixture.output.root.requiredText.join('\n')}\n-->\n`,
  );
  assert.throws(
    () => verifyOutput(reopenedComment, 'claude'),
    /required heading must be an exact Markdown line/iu,
  );
});

test('output verifier rejects required guidance inside raw HTML blocks', () => {
  const { project } = newProject('claude');
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  writeAcceptedOutput(project, fixture);
  writeFileSync(
    join(project, fixture.output.root.path),
    `${fixture.existing.root}<pre>\n${fixture.output.root.requiredText.join('\n')}\n</pre>\n`,
  );

  assert.throws(
    () => verifyOutput(project, 'claude'),
    /required heading must be an exact Markdown line/iu,
  );
});

test('output verifier keeps type-one blocks open through invalid closing tags', () => {
  const { project } = newProject('claude');
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  writeAcceptedOutput(project, fixture);
  writeFileSync(
    join(project, fixture.output.root.path),
    `${fixture.existing.root}<pre>\n</pre >\n${fixture.output.root.requiredText.join('\n')}\n</pre>\n`,
  );

  assert.throws(
    () => verifyOutput(project, 'claude'),
    /required heading must be an exact Markdown line/iu,
  );
});

test('output verifier rejects required guidance inside other raw HTML blocks', () => {
  const { project } = newProject('claude');
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  writeAcceptedOutput(project, fixture);
  writeFileSync(
    join(project, fixture.output.root.path),
    `${fixture.existing.root}<div>\n${fixture.output.root.requiredText.join('\n')}\n</div>\n`,
  );

  assert.throws(
    () => verifyOutput(project, 'claude'),
    /required heading must be an exact Markdown line/iu,
  );
});

test('output verifier rejects required guidance after closing type-six HTML tags', () => {
  const { project } = newProject('claude');
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  writeAcceptedOutput(project, fixture);
  writeFileSync(
    join(project, fixture.output.root.path),
    `${fixture.existing.root}</div> trailing text\n${fixture.output.root.requiredText.join('\n')}\n\n`,
  );

  assert.throws(
    () => verifyOutput(project, 'claude'),
    /required heading must be an exact Markdown line/iu,
  );
});

test('output verifier rejects required guidance after all type-six HTML tags', () => {
  const { project } = newProject('claude');
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  writeAcceptedOutput(project, fixture);
  writeFileSync(
    join(project, fixture.output.root.path),
    `${fixture.existing.root}Visible context\n<menuitem>\n`
      + `${fixture.output.root.requiredText.join('\n')}\n\n`,
  );

  assert.throws(
    () => verifyOutput(project, 'claude'),
    /required heading must be an exact Markdown line/iu,
  );
});

test('output verifier rejects required guidance inside every raw HTML block form', () => {
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  const cases = [
    ['processing instruction', '<?project-memory', '?>'],
    ['CDATA section', '<![CDATA[', ']]>'],
    ['HTML declaration', '<!DOCTYPE html', '>'],
    ['type-six HTML block', '<div>', '</div>'],
    ['type-seven HTML block', '<project-memory>', ''],
  ];

  for (const [name, opening, closing] of cases) {
    const { project } = newProject('claude');
    writeAcceptedOutput(project, fixture);
    writeFileSync(
      join(project, fixture.output.root.path),
      `${fixture.existing.root}${opening}\n${fixture.output.root.requiredText.join('\n')}\n${closing}\n`,
    );

    assert.throws(
      () => verifyOutput(project, 'claude'),
      /required heading must be an exact Markdown line/iu,
      name,
    );
  }
});

test('output verifier accepts type-seven tags inside paragraphs', () => {
  const { project } = newProject('claude');
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  writeAcceptedOutput(project, fixture);
  writeFileSync(
    join(project, fixture.output.root.path),
    `${fixture.existing.root}Visible context\n<project-memory>\n`
      + `${fixture.output.root.requiredText.join('\n')}\n`,
  );

  assert.doesNotThrow(() => verifyOutput(project, 'claude'));
});

test('output verifier accepts inline type-one and type-seven HTML', () => {
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  const visibleCases = [
    'Visible context\n<pre/>',
    '> Visible context\n<project-memory>',
  ];

  for (const prefix of visibleCases) {
    const { project } = newProject('claude');
    writeAcceptedOutput(project, fixture);
    writeFileSync(
      join(project, fixture.output.root.path),
      `${fixture.existing.root}${prefix}\n${fixture.output.root.requiredText.join('\n')}\n`,
    );

    assert.doesNotThrow(() => verifyOutput(project, 'claude'));
  }
});

test('output verifier ignores raw tags inside existing HTML comments', () => {
  const { project } = newProject('claude');
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  writeAcceptedOutput(project, fixture);
  writeFileSync(
    join(project, fixture.output.root.path),
    `${fixture.existing.root}<!--\n<pre>\n-->\n${fixture.output.root.requiredText.join('\n')}\n`,
  );

  assert.doesNotThrow(() => verifyOutput(project, 'claude'));
});

test('output verifier accepts guidance after an inert HTML comment marker', () => {
  const { project } = newProject('claude');
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  writeAcceptedOutput(project, fixture);
  writeFileSync(
    join(project, fixture.output.root.path),
    `${fixture.existing.root}<script>\nconst marker = '<!--';\n</script>\n`
      + `${fixture.output.root.requiredText.join('\n')}\n`,
  );

  assert.doesNotThrow(() => verifyOutput(project, 'claude'));
});

test('output verifier preserves existing Markdown section boundaries', () => {
  const { project } = newProject('codex');
  const fixture = PROJECT_MEMORY_FIXTURES.codex;
  const changedExisting = fixture.existing.root.replace(
    '## Release safety\n- Keep',
    '## Release safety\n### Release exception\n- Keep',
  );
  writeAcceptedOutput(project, fixture);
  writeFileSync(
    join(project, fixture.output.root.path),
    `${changedExisting}${fixture.output.root.requiredText.join('\n')}\n`,
  );

  assert.throws(
    () => verifyOutput(project, 'codex'),
    /changed the structure of existing root guidance/iu,
  );
});

test('output verifier rejects headings that reparent existing sections', () => {
  const { project } = newProject('codex');
  const fixture = PROJECT_MEMORY_FIXTURES.codex;
  const changedExisting = fixture.existing.root.replace(
    '## Release safety',
    '# Different project\n## Release safety',
  );
  writeAcceptedOutput(project, fixture);
  writeFileSync(
    join(project, fixture.output.root.path),
    `${changedExisting}${fixture.output.root.requiredText.join('\n')}\n`,
  );

  assert.throws(
    () => verifyOutput(project, 'codex'),
    /changed the structure of existing root guidance/iu,
  );
});

test('output verifier rejects indented headings that reparent existing sections', () => {
  const { project } = newProject('codex');
  const fixture = PROJECT_MEMORY_FIXTURES.codex;
  const changedExisting = fixture.existing.root.replace(
    '## Release safety',
    ' # Different project\n## Release safety',
  );
  writeAcceptedOutput(project, fixture);
  writeFileSync(
    join(project, fixture.output.root.path),
    `${changedExisting}${fixture.output.root.requiredText.join('\n')}\n`,
  );

  assert.throws(
    () => verifyOutput(project, 'codex'),
    /changed the structure of existing root guidance/iu,
  );
});

test('output verifier rejects setext headings that change existing sections', () => {
  const { project } = newProject('codex');
  const fixture = PROJECT_MEMORY_FIXTURES.codex;
  const changedExisting = fixture.existing.root.replace(
    '- Keep',
    'Different project\n=================\n- Keep',
  );
  writeAcceptedOutput(project, fixture);
  writeFileSync(
    join(project, fixture.output.root.path),
    `${changedExisting}${fixture.output.root.requiredText.join('\n')}\n`,
  );

  assert.throws(
    () => verifyOutput(project, 'codex'),
    /changed the structure of existing root guidance/iu,
  );
});

test('output verifier rejects duplicated required guidance', () => {
  const { project } = newProject('codex');
  const fixture = PROJECT_MEMORY_FIXTURES.codex;
  writeAcceptedOutput(project, fixture);
  writeFileSync(
    join(project, fixture.output.root.path),
    `${fixture.existing.root}${fixture.output.root.requiredText.join('\n')}\n`
      + `${fixture.output.root.requiredText[1]}\n`,
  );

  assert.throws(
    () => verifyOutput(project, 'codex'),
    /required text must appear exactly once/iu,
  );
});

test('output verifier rejects required guidance in a nested subsection', () => {
  const { project } = newProject('claude');
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  writeAcceptedOutput(project, fixture);
  writeFileSync(
    join(project, fixture.output.root.path),
    `${fixture.existing.root}${fixture.output.root.requiredText[0]}\n### Different scope\n`
      + `${fixture.output.root.requiredText[1]}\n`,
  );

  assert.throws(
    () => verifyOutput(project, 'claude'),
    /changes the required guidance structure/iu,
  );
});

test('output verifier accepts quoted headings in a required section', () => {
  const { project } = newProject('claude');
  const fixture = PROJECT_MEMORY_FIXTURES.claude;
  writeAcceptedOutput(project, fixture);
  writeFileSync(
    join(project, fixture.output.root.path),
    `${fixture.existing.root}${fixture.output.root.requiredText[0]}\n> ## Note\n`
      + `${fixture.output.root.requiredText[1]}\n`,
  );

  assert.doesNotThrow(() => verifyOutput(project, 'claude'));
});

test('output verifier requires the prepared snapshot before accepting mutations', () => {
  const fixture = newProject('codex');
  writeAcceptedOutput(fixture.project, PROJECT_MEMORY_FIXTURES.codex);
  writeFileSync(join(fixture.project, 'unrelated-output.txt'), 'Unexpected output\n');

  assert.throws(
    () => verifyProjectMemoryOutput(fixture.project, 'codex'),
    /requires a prepared snapshot/iu,
  );
});

test('output verifier allows mutations only at expected output paths', () => {
  const project = mkdtempSync(join(tmpdir(), 'project-memory-activation-tree-'));
  disposableRoots.push(project);
  writeFileSync(join(project, 'README.md'), '# Original project\n');
  const prepared = prepareProjectMemoryFixture(project, 'codex');
  writeAcceptedOutput(project, PROJECT_MEMORY_FIXTURES.codex);

  writeFileSync(join(project, 'README.md'), '# Changed project\n');
  assert.throws(
    () => verifyProjectMemoryOutput(project, 'codex', prepared.snapshot),
    /activation changed README\.md/iu,
  );

  writeFileSync(join(project, 'README.md'), '# Original project\n');
  writeFileSync(join(project, 'unrelated-output.txt'), 'Unexpected output\n');
  assert.throws(
    () => verifyProjectMemoryOutput(project, 'codex', prepared.snapshot),
    /activation changed unrelated-output\.txt/iu,
  );
});

test('output verifier rejects other-client instruction files anywhere in the tree', () => {
  const { project } = newProject('codex');
  const fixture = PROJECT_MEMORY_FIXTURES.codex;
  writeAcceptedOutput(project, fixture);
  mkdirSync(join(project, '.claude'));
  writeFileSync(join(project, '.claude/CLAUDE.md'), '# Wrong client output\n');

  assert.throws(
    () => verifyOutput(project, 'codex'),
    /created the other client's \.claude\/CLAUDE\.md/u,
  );
});

test('output verifier allows only other-client files present in the prepared snapshot', () => {
  const project = mkdtempSync(join(tmpdir(), 'project-memory-existing-client-'));
  disposableRoots.push(project);
  mkdirSync(join(project, '.claude'));
  writeFileSync(join(project, '.claude/CLAUDE.md'), '# Existing other-client file\n');
  const prepared = prepareProjectMemoryFixture(project, 'codex');
  writeAcceptedOutput(project, PROJECT_MEMORY_FIXTURES.codex);

  assert.doesNotThrow(() => verifyProjectMemoryOutput(
    project,
    'codex',
    prepared.snapshot,
  ));

  writeFileSync(join(project, 'packages/archive/CLAUDE.md'), '# Newly created leak\n');
  assert.throws(
    () => verifyProjectMemoryOutput(project, 'codex', prepared.snapshot),
    /created the other client's packages\/archive\/CLAUDE\.md/u,
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

  const prototypeName = newProject('codex');
  writeFileSync(join(prototypeName.project, '__proto__'), 'new file\n');
  assert.throws(
    () => verifyProjectMemoryNonTrigger(
      prototypeName.project,
      'codex',
      prototypeName.prepared.snapshot,
    ),
    /non-trigger changed __proto__/u,
  );

  const changedMode = newProject('codex');
  chmodSync(join(changedMode.project, 'AGENTS.md'), 0o600);
  assert.throws(
    () => verifyProjectMemoryNonTrigger(
      changedMode.project,
      'codex',
      changedMode.prepared.snapshot,
    ),
    /non-trigger changed AGENTS\.md/u,
  );
});

test('non-trigger check detects special permission mutations', {
  skip: process.platform === 'win32',
}, (context) => {
  const fixture = newProject('codex');
  const path = join(fixture.project, 'AGENTS.md');
  const permissionBits = lstatSync(path).mode & 0o777;
  chmodSync(path, permissionBits | 0o4000);
  if ((lstatSync(path).mode & 0o4000) === 0) {
    context.skip('The filesystem does not preserve the setuid bit');
    return;
  }

  assert.throws(
    () => verifyProjectMemoryNonTrigger(
      fixture.project,
      'codex',
      fixture.prepared.snapshot,
    ),
    /non-trigger changed AGENTS\.md/iu,
  );
});

test('snapshot classification uses lstat when directory entry types are unknown', () => {
  const fixture = newProject('codex');
  const originalReadDirectory = fs.readdirSync;
  fs.readdirSync = (...args) => {
    const entries = originalReadDirectory(...args);
    if (!args[1]?.withFileTypes) return entries;
    return entries.map((entry) => ({
      name: entry.name,
      isDirectory: () => false,
      isFile: () => false,
      isSymbolicLink: () => false,
    }));
  };
  syncBuiltinESMExports();

  try {
    assert.doesNotThrow(() => verifyProjectMemoryNonTrigger(
      fixture.project,
      'codex',
      fixture.prepared.snapshot,
    ));
  } finally {
    fs.readdirSync = originalReadDirectory;
    syncBuiltinESMExports();
  }
});

test('fixture containment accepts legal dot-prefixed names', () => {
  const project = mkdtempSync(join(tmpdir(), 'project-memory-dot-name-'));
  disposableRoots.push(project);
  mkdirSync(join(project, '..notes'));
  assert.doesNotThrow(() => prepareProjectMemoryFixture(project, 'codex'));
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

test('output verification rejects symlinked existing ancestors', () => {
  const verifiedProject = newProject('codex');
  const fixture = PROJECT_MEMORY_FIXTURES.codex;
  const outside = mkdtempSync(join(tmpdir(), 'project-memory-verify-outside-'));
  disposableRoots.push(outside);
  writeFileSync(
    join(verifiedProject.project, fixture.output.root.path),
    `${fixture.existing.root}${fixture.output.root.requiredText.join('\n')}\n`,
  );
  rmSync(join(verifiedProject.project, 'packages'), { recursive: true });
  mkdirSync(join(outside, 'archive'));
  writeFileSync(
    join(outside, 'archive/AGENTS.md'),
    `${fixture.existing.nested}${fixture.output.nested.requiredText.join('\n')}\n`,
  );
  symlinkSync(outside, join(verifiedProject.project, 'packages'));

  assert.throws(
    () => verifyProjectMemoryOutput(
      verifiedProject.project,
      'codex',
      verifiedProject.prepared.snapshot,
    ),
    /nested output ancestor must not be a symbolic link/iu,
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
