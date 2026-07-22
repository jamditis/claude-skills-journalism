import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import {
  SKILLS_REF_REVISION,
  SKILLS_REF_SOURCE,
  UPSTREAM_SKILLS_REF_SOURCE,
  findSkillDirectories,
  validateSkillDirectories,
} from './validate-agent-skills.mjs';

test('standards validation pins the reviewed Agent Skills revision', () => {
  assert.equal(SKILLS_REF_REVISION, '38a2ff82958afee88dadf4831509e6f7e9d8ef4e');
  assert.equal(
    SKILLS_REF_SOURCE,
    `git+https://github.com/agentskills/agentskills.git@${SKILLS_REF_REVISION}#subdirectory=skills-ref`,
  );

  const pkg = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
  assert.equal(pkg.scripts['validate:agent-skills'], 'node scripts/validate-agent-skills.mjs');
  assert.equal(
    pkg.scripts['validate:agent-skills:upstream'],
    'node scripts/validate-agent-skills.mjs --upstream',
  );
  assert.equal(
    UPSTREAM_SKILLS_REF_SOURCE,
    'git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref',
  );
});

test('the scheduled canary checks the current upstream Agent Skills validator', () => {
  const workflow = readFileSync(
    new URL('../.github/workflows/compatibility-canary.yml', import.meta.url),
    'utf8',
  );

  assert.match(workflow, /upstream-agent-skills:/u);
  assert.match(workflow, /if: github\.event_name != 'pull_request'/u);
  assert.match(workflow, /npm run validate:agent-skills:upstream/u);
});

test('skill discovery covers root and nested skills while skipping installed copies', (t) => {
  const root = mkdtempSync(join(tmpdir(), 'agent-skills-validation-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));

  for (const directory of [
    'root-skill',
    'plugin/skills/nested-skill',
    '.agents/skills/imported-copy',
    'node_modules/package/skills/dependency-copy',
  ]) {
    const path = join(root, directory);
    mkdirSync(path, { recursive: true });
    writeFileSync(join(path, 'SKILL.md'), '---\nname: fixture\ndescription: Fixture\n---\n');
  }

  assert.deepEqual(
    findSkillDirectories(root).map((path) => path.slice(root.length + 1).replaceAll('\\', '/')),
    ['plugin/skills/nested-skill', 'root-skill'],
  );
});

test('validator runner forces UTF-8 and reports every skill result', () => {
  const directories = ['/repo/first-skill', '/repo/second-skill'];
  const calls = [];
  const results = validateSkillDirectories(directories, {
    command: 'uvx-test',
    run(command, args, options) {
      calls.push({ command, args, options });
      const failed = args.at(-1).endsWith('second-skill');
      return {
        status: failed ? 1 : 0,
        stdout: failed ? '' : `Valid skill: ${args.at(-1)}\n`,
        stderr: failed ? 'Validation failed\n' : '',
      };
    },
  });

  assert.equal(calls.length, 2);
  for (const call of calls) {
    assert.equal(call.command, 'uvx-test');
    assert.deepEqual(call.args.slice(0, 4), [
      '--from',
      SKILLS_REF_SOURCE,
      'skills-ref',
      'validate',
    ]);
    assert.equal(call.options.env.PYTHONUTF8, '1');
    assert.equal(call.options.encoding, 'utf8');
  }
  assert.deepEqual(results.map(({ status }) => status), [0, 1]);
  assert.match(results[1].stderr, /Validation failed/u);
});

test('validator runner can select the current upstream source', () => {
  const calls = [];
  const results = validateSkillDirectories(['/repo/skill'], {
    source: UPSTREAM_SKILLS_REF_SOURCE,
    run(command, args) {
      calls.push({ command, args });
      return { status: 0, stdout: '', stderr: '' };
    },
  });

  assert.equal(results[0].status, 0);
  assert.equal(calls[0].args[1], UPSTREAM_SKILLS_REF_SOURCE);
});
