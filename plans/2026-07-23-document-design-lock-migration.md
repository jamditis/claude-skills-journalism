# Document design lock-key migration

- Date: July 23, 2026
- Tracking issue: [#230](https://github.com/jamditis/claude-skills-journalism/issues/230)
- Client: Codex CLI 0.145.0
- Standards client: skills CLI 1.5.20
- Runtime: Node.js 22.23.1 and npm 10.9.8
- Historical source commit:
  [`64dc95d8584d66e35ceb79e3c43e7fa3d201d3e4`](https://github.com/jamditis/claude-skills-journalism/commit/64dc95d8584d66e35ceb79e3c43e7fa3d201d3e4)
- Update target:
  [`d49ed1022a012269a237f7749b0e47c099e7add6`](https://github.com/jamditis/claude-skills-journalism/commit/d49ed1022a012269a237f7749b0e47c099e7add6)

## Scope

The phase-one standards repair changed the skill frontmatter name from
`Document design` to `document-design`. Older project installs already used
the canonical `.agents/skills/document-design` directory, but their
`skills-lock.json` key retained the display-style name.

This evidence covers that local lock identity only. It does not merge catalog
metrics, alias skills across install roots, change the installed directory, or
claim Codex activation and output behavior for `pdf-playground`.

## Reproduction

The checked-in fixture records the historical key, repository source, source
skill path, and content hash:

```text
scripts/fixtures/document-design-lock-v1.json
fixture SHA-256: 06c6f36f29dfae539e856456786642047c0bc742c4d231c5460fe58aeecc3ebc
historical skill hash: 1a388f259e5894a04617d8b599719ec5e1adcf778eec81dbdf8324816b1ed8dc
installed directory: .agents/skills/document-design
```

The canary reconstructed the installed skill from the historical commit and
confirmed that its folder hash matched the lock. It then ran:

```bash
npx --yes skills@1.5.20 update --project -y
```

The command exited 1. The updater read `Document design` from the lock and
reported `Failed to update Document design`. The fixture lock digest and
installed folder hash remained unchanged. Source-wide deletion preflight also
printed a non-blocking warning; that warning appeared on the successful
canonical updates too and is separate from the name failure.

## Migration boundary

Run the explicit repository command from this checkout:

```bash
npm run migrate:document-design-lock -- --project '<project>'
```

The command rewrites only an entry with all of these properties:

- key `Document design`;
- source `jamditis/claude-skills-journalism`;
- source type `github`;
- skill path `pdf-playground/skills/document-design/SKILL.md`;
- a 64-character SHA-256 content hash that matches the installed tree.

It preserves the complete lock record, writes an atomic replacement with the
existing file mode, and does not edit the installed skill. An identical
canonical duplicate is collapsed. A conflicting duplicate, unexpected
source/path/type, malformed lock, linked lock, linked installed directory, or
path escape stops without rewriting the lock.

This is deliberately not an install lifecycle hook. The migration is visible,
project-scoped, reversible from version control or a lock backup, and
independent of public catalog slug history.

## Update and idempotence result

After migration, skills CLI 1.5.20 ran the same project update twice. Both
updates exited 0 and reported `Updated document-design`. After each run:

- only the `document-design` identity remained;
- the installed directory was `.agents/skills/document-design`;
- the source stayed `jamditis/claude-skills-journalism`;
- the source path stayed
  `pdf-playground/skills/document-design/SKILL.md`;
- installed frontmatter used `name: document-design`;
- the installed tree matched the update target;
- the lock hash matched the installed tree.

The first and second update produced the same values:

```text
content hash: 129514adfe5f81dd3095ff4e92cec3a5b86a05103bf6386c0d761ddba74bc335
lock SHA-256: a586c9e6d61b960a0f9f3438efaedfab2a16d6187b5f3b514c530d27e6bcd5d8
source master: d49ed1022a012269a237f7749b0e47c099e7add6
```

The canary checked the public source commit before, between, and after the
updates, then removed its disposable project, client home, and npm cache:

```bash
npm run canary:document-design-lock
```

To verify a migrated project without changing it:

```bash
node scripts/document-design-lock-migration.mjs \
  --verify --project '<project>'
```

The pure migration and filesystem boundary tests run in the normal
`npm test` suite. The live canary stays explicit because it clones the public
repository and resolves a pinned skills CLI release.
