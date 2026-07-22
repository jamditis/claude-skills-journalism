import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const CONTRACT = '<!-- untrusted-content-contract:v1 -->';
const NETWORK_FACING_SKILLS = [
  'dev-toolkit/skills/accessibility-compliance/SKILL.md',
  'dev-toolkit/skills/mobile-debugging/SKILL.md',
  'dev-toolkit/skills/python-pipeline/SKILL.md',
  'dev-toolkit/skills/web-scraping/SKILL.md',
  'dev-toolkit/skills/zero-build-frontend/SKILL.md',
  'journalism-core/skills/crisis-communications/SKILL.md',
  'journalism-core/skills/data-journalism/SKILL.md',
  'journalism-core/skills/fact-check-workflow/SKILL.md',
  'journalism-core/skills/social-media-intelligence/SKILL.md',
  'journalism-core/skills/source-verification/SKILL.md',
  'research-toolkit/skills/content-access/SKILL.md',
  'research-toolkit/skills/digital-archive/SKILL.md',
  'research-toolkit/skills/page-monitoring/SKILL.md',
  'research-toolkit/skills/web-archiving/SKILL.md',
  'superjawn/skills/brainstorming/SKILL.md',
  'superjawn/skills/executing-plans/SKILL.md',
  'superjawn/skills/systematic-debugging/SKILL.md',
  'superjawn/skills/using-git-worktrees/SKILL.md',
  'superjawn/skills/writing-skills/SKILL.md',
];

test('every remaining network-facing skill carries the standalone trust contract', () => {
  const missing = [];
  const required = [
    /untrusted data, (?:not|never as) instructions/i,
    /run tools, reveal secrets, change policy, or expand scope/i,
    /delimit/i,
    /provenance/i,
    /redirect/i,
    /private-network/i,
    /content size/i,
    /structured extraction/i,
    /schema validation/i,
    /explicit user confirmation/i,
    /writes, uploads, credential use, command execution, or publication/i,
    /system prompts or private context/i,
    /EXTERNAL_DATA/i,
  ];

  for (const file of NETWORK_FACING_SKILLS) {
    const source = readFileSync(join(ROOT, file), 'utf8');
    const markerIndex = source.indexOf(CONTRACT);
    if (markerIndex === -1) {
      missing.push(`${file}: version marker`);
      continue;
    }
    const contractHeading = source.indexOf('\n## Untrusted content boundary', markerIndex);
    const nextHeading = source.indexOf('\n## ', contractHeading + 4);
    if (contractHeading === -1 || nextHeading === -1) {
      missing.push(`${file}: bounded contract block`);
      continue;
    }
    const contract = source.slice(markerIndex, nextHeading);
    for (const pattern of required) {
      if (!pattern.test(contract)) missing.push(`${file}: ${pattern}`);
    }
  }
  assert.deepEqual(missing, []);
});

test('canonical contract documents standalone copies and expected residual risk', () => {
  const source = readFileSync(join(ROOT, 'specs/untrusted-content-contract.md'), 'utf8');
  assert.match(source, /copy the contract into each standalone skill/i);
  assert.match(source, /network access remains expected/i);
  assert.match(source, /does not make retrieved content trustworthy/i);
  assert.match(source, /untrusted-content-contract:v1/);
});
