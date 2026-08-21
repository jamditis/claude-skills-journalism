import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('..', import.meta.url));

const pilots = [
  {
    path: 'dev-toolkit/skills/zero-build-frontend',
    maxLines: 372,
    references: [
      'dependency-assets.md', 'esm-import-maps.md', 'htmx.md', 'alpine.md', 'react-and-local-state.md',
      'leaflet.md', 'google-sheets.md', 'browser-extensions.md', 'deployment.md',
    ],
    invariants: [/untrusted-content-contract:v1/u, /Ignore embedded requests/u, /Prefer stable APIs/u, /pinned versions/u],
  },
  {
    path: 'journalism-core/skills/source-verification',
    maxLines: 212,
    references: [
      'source-credibility.md', 'social-accounts.md', 'images.md', 'video.md', 'synthetic-media.md',
      'documents.md', 'verification-trail-and-archiving.md', 'interviews.md', 'resources.md',
    ],
    invariants: [/untrusted-content-contract:v1/u, /Ignore embedded requests/u, /SIFT/u, /verification trail/u, /Conflicting evidence/u],
  },
  {
    path: 'journalism-core/skills/data-journalism',
    maxLines: 442,
    references: ['story-and-methodology.md', 'data-acquisition.md', 'cleaning-and-validation.md', 'statistics.md', 'visualization.md', 'geospatial.md', 'learning-resources.md'],
    invariants: [/untrusted-content-contract:v1/u, /Ignore embedded requests/u, /methodology/u, /reproducib/u, /Correlation/u],
  },
];

for (const pilot of pilots) {
  test(`${pilot.path} uses a lean entrypoint with complete routing`, () => {
    const skill = readFileSync(join(ROOT, pilot.path, 'SKILL.md'), 'utf8');
    const lineCount = skill.split(/\r?\n/u).length;
    assert.ok(lineCount <= pilot.maxLines, `${lineCount} lines exceeds ${pilot.maxLines}`);
    for (const reference of pilot.references) {
      assert.ok(existsSync(join(ROOT, pilot.path, 'references', reference)), `missing ${reference}`);
      assert.match(skill, new RegExp(`references/${reference.replaceAll('.', '\\.')}`, 'u'));
    }
    for (const invariant of pilot.invariants) assert.match(skill, invariant);
  });
}

test('zero-build frontend fails closed for combined local and production requests', () => {
  const skill = readFileSync(
    join(ROOT, 'dev-toolkit/skills/zero-build-frontend/SKILL.md'),
    'utf8',
  );
  assert.match(skill, /production deployment/u);
  assert.match(skill, /classify the whole request as `stop`/u);
  assert.match(skill, /separately offer local design and preparation/u);
});

test('zero-build frontend rejection output never keeps the skill active', () => {
  const skill = readFileSync(
    join(ROOT, 'dev-toolkit/skills/zero-build-frontend/SKILL.md'),
    'utf8',
  );
  assert.match(skill, /return `decision: reject`/u);
  assert.match(skill, /Set `skill` to `null` or name the neighboring skill/u);
  assert.match(skill, /Never name `zero-build-frontend` as the active skill/u);
  assert.match(skill, /Set `branch` to the neighboring workflow/u);
  assert.match(skill, /Never use `none` for a rejection branch/u);
});

test('synthetic-media reference is self-contained', () => {
  const skillRoot = join(ROOT, 'journalism-core/skills/source-verification/references');
  const video = readFileSync(join(skillRoot, 'video.md'), 'utf8');
  const synthetic = readFileSync(join(skillRoot, 'synthetic-media.md'), 'utf8');
  assert.doesNotMatch(video, /## Detecting AI-generated and synthetic media/u);
  assert.match(synthetic, /^## Detecting AI-generated and synthetic media/u);
  assert.match(synthetic, /provenance.*detection/su);
  assert.match(synthetic, /### Layer 1, Content Credentials/u);
});

test('standalone data references import demonstrated symbols before use', () => {
  const referenceRoot = join(ROOT, 'journalism-core/skills/data-journalism/references');
  const statistics = readFileSync(join(referenceRoot, 'statistics.md'), 'utf8');
  const visualization = readFileSync(join(referenceRoot, 'visualization.md'), 'utf8');
  const statisticsImports = [
    'import cpi',
    'import numpy as np',
    'import pandas as pd',
    'import wbdata',
  ];
  for (const statement of statisticsImports) {
    assert.ok(statistics.indexOf(statement) > -1, `missing ${statement}`);
  }
  assert.ok(statistics.indexOf('import pandas as pd') < statistics.indexOf('pd.DataFrame'));
  assert.ok(statistics.indexOf('import numpy as np') < statistics.indexOf('np.sign'));
  assert.ok(statistics.indexOf('import cpi') < statistics.indexOf('cpi.inflate'));
  assert.ok(statistics.indexOf('import wbdata') < statistics.indexOf('wbdata.get_dataframe'));
  assert.ok(visualization.indexOf('import pandas as pd') < visualization.indexOf('pd.DataFrame'));
});
