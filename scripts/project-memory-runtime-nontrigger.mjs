import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { prepareVariant } from './skill-behavior-eval.mjs';
import {
  buildProjectMemoryInvocation,
  prepareProjectMemoryFixture,
  verifyProjectMemoryNonTrigger,
  verifyProjectMemoryNonTriggerTrace,
} from './project-memory-fixtures.mjs';

const sourceRoot = fileURLToPath(new URL('..', import.meta.url));
const runRoot = mkdtempSync(join(tmpdir(), 'project-memory-nontrigger-'));

try {
  const clients = [];
  for (const client of ['claude', 'codex']) {
    const version = spawnSync(client, ['--version'], { encoding: 'utf8', timeout: 10_000 });
    if (version.status !== 0 || !version.stdout?.trim()) {
      throw new Error(`${client} version is unavailable`);
    }
    const prepared = prepareVariant({
      client,
      sourceRoot,
      runRoot: join(runRoot, client),
      packageName: 'project-templates-toolkit',
      skillName: 'project-memory',
      authSourceHome: join(homedir(), client === 'claude' ? '.claude' : '.codex'),
    });
    const fixture = prepareProjectMemoryFixture(prepared.projectDir, client);
    const invocation = buildProjectMemoryInvocation(client, 'nonTrigger', prepared);
    if (client === 'claude') {
      for (const flag of ['--tools', '--allowedTools']) {
        const index = invocation.args.indexOf(flag);
        if (index < 0 || index + 1 >= invocation.args.length) {
          throw new Error(`Claude invocation lacks ${flag}`);
        }
        invocation.args[index + 1] = 'Skill,Read';
      }
      invocation.args.push('--plugin-dir', prepared.pluginDir, '--prompt-suggestions', 'false');
    }
    const result = spawnSync(invocation.command, invocation.args, {
      cwd: invocation.cwd,
      env: {
        ...process.env,
        ...invocation.env,
        HOME: prepared.clientHome,
        USERPROFILE: prepared.clientHome,
      },
      encoding: 'utf8',
      maxBuffer: 8 * 1024 * 1024,
      timeout: 180_000,
    });
    if (result.status !== 0) {
      throw new Error(`${client} run failed: ${result.error?.message ?? result.signal ?? result.status}`);
    }
    const trace = verifyProjectMemoryNonTriggerTrace(client, result.stdout);
    verifyProjectMemoryNonTrigger(prepared.projectDir, client, fixture.snapshot);
    clients.push({ client, version: version.stdout.trim(), trace, projectUnchanged: true });
  }
  const sourceRevision = execFileSync('git', ['rev-parse', 'HEAD'], {
    cwd: sourceRoot, encoding: 'utf8', timeout: 10_000,
  }).trim();
  console.log(JSON.stringify({ sourceRevision, clients }, null, 2));
} finally {
  rmSync(runRoot, { recursive: true, force: true });
}
