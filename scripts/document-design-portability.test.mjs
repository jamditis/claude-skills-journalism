import assert from 'node:assert/strict';
import {
  lstatSync,
  readFileSync,
  readdirSync,
} from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const PACKAGE_ROOT = join(ROOT, 'pdf-playground');
const SKILL_ROOT = join(PACKAGE_ROOT, 'skills', 'document-design');
const PORTABLE_RESOURCE_DIRECTORIES = ['brands', 'controls', 'templates'];

function regularFileManifest(directory) {
  const files = [];

  assert.equal(
    lstatSync(directory).isSymbolicLink(),
    false,
    `portable resources must not depend on symlinks: ${directory}`,
  );

  function visit(current) {
    for (const entry of readdirSync(current, { withFileTypes: true })) {
      const path = join(current, entry.name);
      assert.equal(
        lstatSync(path).isSymbolicLink(),
        false,
        `portable resources must not depend on symlinks: ${path}`,
      );
      if (entry.isDirectory()) {
        visit(path);
      } else if (entry.isFile()) {
        files.push({
          path: relative(directory, path).replaceAll('\\', '/'),
          content: readFileSync(path),
        });
      }
    }
  }

  visit(directory);
  return files.sort((left, right) => left.path.localeCompare(right.path));
}

test('the standards-installed skill carries exact package resources', () => {
  for (const directory of PORTABLE_RESOURCE_DIRECTORIES) {
    assert.deepEqual(
      regularFileManifest(join(SKILL_ROOT, directory)),
      regularFileManifest(join(PACKAGE_ROOT, directory)),
      `${directory} drifted between package resources and the installed skill`,
    );
  }

  const cssReference = join(SKILL_ROOT, 'references', 'css-patterns.md');
  assert.equal(lstatSync(cssReference).isFile(), true);
  assert.equal(lstatSync(cssReference).isSymbolicLink(), false);
});

test('document-design resolves resources from its installed skill root', () => {
  const skill = readFileSync(join(SKILL_ROOT, 'SKILL.md'), 'utf8');

  assert.doesNotMatch(skill, /CLAUDE_PLUGIN_ROOT/u);
  assert.match(skill, /project-root\s+`?pdf-playground\.local\.md`?/u);
  assert.match(skill, /legacy `.claude\/pdf-playground\.local\.md` fallback/u);
  for (const resource of [
    'templates/',
    'brands/',
    'controls/',
    'references/css-patterns.md',
  ]) {
    assert.match(skill, new RegExp(resource.replace('/', '\\/'), 'u'));
  }
});

test('public Codex wording keeps Claude-only surfaces out of scope', () => {
  const readme = readFileSync(join(PACKAGE_ROOT, 'README.md'), 'utf8');

  assert.match(
    readme,
    /npx --yes skills@latest add jamditis\/claude-skills-journalism --skill document-design --agent codex --copy -y/u,
  );
  assert.doesNotMatch(readme, /--copy -g -y/u);
  assert.match(readme, /Invoke it with `\$document-design`/u);
  assert.match(
    readme,
    /cp \.agents\/skills\/document-design\/brands\/default\.yaml pdf-playground\.local\.md/u,
  );
  assert.match(readme, /eight\s+`\/pdf-playground:\*` commands/u);
  assert.match(readme, /SessionStart hook remain Claude Code-only/u);
});
