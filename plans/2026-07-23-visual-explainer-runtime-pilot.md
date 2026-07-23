# Visual-explainer Codex runtime pilot

- Status: passed on the Codex project-standards path
- Evidence date: July 23, 2026
- Tracking issue: [#228](https://github.com/jamditis/claude-skills-journalism/issues/228)
- Source revision: [`f6a4b84dd2e9feafc6c2bf067f873e9301a083c2`](https://github.com/jamditis/claude-skills-journalism/commit/f6a4b84dd2e9feafc6c2bf067f873e9301a083c2)

## Scope

This pilot tested the repository's `visual-explainer` 0.7.1 root skill in
Codex CLI 0.145.0 after skills CLI 1.5.20 copied it into a disposable
project's `.agents/skills/visual-explainer` directory.

The fixture exercised discovery, installed relative resources, HTML creation,
responsive rendering, and basic accessibility. It did not test the eight
source commands as Codex commands, sharing through Vercel, optional image
generation, or a user-level install. It adds no native manifest or adapter.

## Standards installation

The disposable root was
`/tmp/visual-explainer-runtime-20260723-ECLDTK`. The accepted install command
ran from its empty `project` directory:

```bash
npx -y skills@1.5.20 add \
  '<checkout>/visual-explainer' \
  --skill visual-explainer \
  --agent codex \
  --copy \
  -y
```

The installer found one skill, wrote it to
`.agents/skills/visual-explainer`, and created a `skills-lock.json` entry for
that exact name. The source and installed copies each contained 24 files.
Their sorted relative-path and content manifest had the same SHA-256 digest:

```text
83e44cc015b0ebb5b3c19cb5e5f2127b873dec8f5b07d3dc0e3e865d082b6215
```

The pinned official Agent Skills validator accepted the installed copy. Codex
0.145.0's bundled creator helper rejected only the standards-valid
`compatibility` field:

```text
Unexpected key(s) in SKILL.md frontmatter: compatibility.
```

This is the already-allowlisted validator difference, not a runtime failure.

## V-ex-1 runtime result

The exact accepted prompt is stored in
`scripts/visual-explainer-runtime-pilot.mjs`. It invokes
`$visual-explainer`, supplies a four-stage newsroom flow, requires the
installed copy to read:

- `.agents/skills/visual-explainer/references/css-patterns.md`; and
- `.agents/skills/visual-explainer/templates/architecture.html`.

The Codex command trace showed reads from the installed `SKILL.md` and both
required relative resources. It then created `v-ex-1.html` in the disposable
project. The 9,605-byte file had SHA-256 digest:

```text
2a9c3266c0dc33d6487845bd44dc6bc392e8073612bb4733558218fc8514221e
```

The output contained one primary heading, semantic stage headings, all four
requested stages in order, visible connectors, and the requested audit-trail
note. It loaded no runtime CDN script.

## Render and accessibility review

Playwright loaded the generated file at 1,440 by 1,000 pixels and 390 by 844
pixels. Both layouts had no horizontal overflow, browser console error, or
page error. The mobile layout stacked the four stages while preserving their
order and connectors. The page also rendered correctly with the dark color
scheme after its entrance animation settled.

An axe scan using the repository's lockfile-verified dependencies reported
zero WCAG 2.2 A or AA violations in the tested light desktop, light mobile,
and dark desktop renders. This automated result supports the fixture; it is
not a substitute for a full manual accessibility certification.

## Legacy-package omission

A separate empty `CODEX_HOME` added the local Claude marketplace and installed
`visual-explainer@claude-skills-journalism` 0.7.1 through Codex's
legacy-compatible plugin route.

The plugin cache retained the source root `SKILL.md` as package data, but Codex
did not register it under a standards skill root. No
`skills/*/SKILL.md` entry existed for `visual-explainer`, so
`$visual-explainer` was unavailable through that route as expected.

Codex generated three untested migrated-command wrapper skills for
`generate-slides`, `generate-web-diagram`, and `share-page`. Those wrappers
are client-generated adapter surfaces and are outside this root-skill pilot;
their existence is not a runtime support claim for the eight source commands.

## Harness behavior

Run the accepted fixture only with an explicit disposable client home and a
fresh standards install:

```bash
CODEX_HOME='<disposable-codex-home>' \
  npm run pilot:visual-explainer -- codex v-ex-1 \
  --project '<disposable-project>'
```

The runner uses `--ignore-user-config`, `--ignore-rules`, and `--ephemeral`;
starts subprocesses without a shell; applies a five-minute timeout; and
defaults to the `workspace-write` sandbox because the fixture must create an
HTML file. It refuses to reuse an existing output and verifies the installed
resources plus the generated file's semantic contract.

The nested writable sandbox could not initialize a second Bubblewrap
namespace inside the already isolated top-level session. It failed before
reading or writing a fixture file. The accepted probe was rerun with
`--unboxed`, as the repository's `AGENTS.md` permits only when the top-level
Codex session is already externally isolated and was launched with sandbox
bypass. Do not use `--unboxed` from an ordinary unsandboxed shell.

Recheck an existing artifact without invoking Codex:

```bash
npm run pilot:visual-explainer -- codex v-ex-1 \
  --project '<disposable-project>' \
  --verify-only
```

## Verification and cleanup

The focused harness tests cover the exact prompt, sandbox plan, authorized
fallback, resource checks, linked-parent containment, ordered output contract,
runtime-CDN rejection, timeout, shell avoidance, and adversarial CLI input. The
full repository suite, docs CSS freshness, and diff checks are recorded in the
pull request.

The disposable standards project, legacy Codex home, generated HTML, render
screenshots, and authentication symlink were removed after verification.
Credential content was not copied into the test root or repository.
