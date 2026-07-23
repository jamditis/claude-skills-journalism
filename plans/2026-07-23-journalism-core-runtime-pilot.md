# Journalism-core paired runtime pilot

- Status: passed on the scoped Claude package and Codex project-standards paths
- Evidence date: July 23, 2026
- Tracking issue: [#227](https://github.com/jamditis/claude-skills-journalism/issues/227)
- Source revision: [`9eef57629edbaa19bf47ec35296acebdd7b4ab1f`](https://github.com/jamditis/claude-skills-journalism/commit/9eef57629edbaa19bf47ec35296acebdd7b4ab1f)

## Scope

This pilot tested the same public `journalism-core` 1.2.0 source in:

- Claude Code 2.1.218, installed as
  `journalism-core@claude-skills-journalism` from a fresh public-repository
  marketplace clone; and
- Codex CLI 0.145.0, installed into a disposable project's
  `.agents/skills` directory with skills CLI 1.5.20.

The legacy-compatible Codex package path and the Codex user-level standards
path retain install-canary evidence only. This pilot does not turn their
installation results into runtime claims.

## Isolation and installation

The test root was `/tmp/jcore-runtime-pilots-20260723`. It contained separate
Claude configuration and project directories plus separate Codex home and
project directories. The clients reused authenticated command-line state
through symlinks; no credential content was copied into the test root or
repository. Claude sessions used `--no-session-persistence`. Codex sessions
used `--ephemeral`, `--ignore-user-config`, and `--ignore-rules`.

The Claude marketplace install exposed all 14 namespaced journalism-core slash
commands. The Codex standards install copied the same 14 skills into
`.agents/skills`. The source, Claude-installed, and Codex-installed copies of
`photo-metadata/reference.md` had the same SHA-256 digest:

```text
0150c0db2b78ecc3c38a4d7fa585b3444c58cceb1b22dd55e21eb64f5d659d17
```

## Runtime results

| Fixture | Claude Code 2.1.218 | Codex CLI 0.145.0 |
|---|---|---|
| J-core-1 explicit `fact-check-workflow` | `/journalism-core:fact-check-workflow` selected the installed command. The response separated the claim, provenance, primary evidence, corroboration, right of response, and uncertainty, and left the unsupported claim unverifiable. | `$fact-check-workflow` selected the installed skill. The response produced the same conservative verification stages and did not invent a source or verdict. |
| J-core-2 implicit verification | The client invoked the `Skill` tool with `journalism-core:source-verification`, then returned a verification checklist with sourcing and uncertainty controls. | The client selected the fact-check and source-verification skills, read both installed `SKILL.md` files, and returned a conservative verification checklist. |
| J-core-3 unrelated non-trigger | No `Skill` tool call occurred. Output: “42 × 0.18 = **$7.56**. Total with tip: **$49.56**.” | No skill-selection message or installed-skill read occurred. Output: “An 18% tip on $42 is **$7.56**. Total: **$49.56**.” |
| Installed sibling resource | `/journalism-core:photo-metadata` read the installed cache's `skills/photo-metadata/reference.md`. It returned the 256-byte IPTC-IIM Headline limit and the reference's four-part AP caption recipe. | `$photo-metadata` read `.agents/skills/photo-metadata/reference.md` and returned the same limit and caption recipe. |

The exact accepted prompts remain in
`scripts/journalism-core-runtime-pilot.mjs` and are protected by
`scripts/journalism-core-runtime-pilot.test.mjs`.

## Harness behavior

Run one fixture only with explicit disposable client homes:

```bash
CLAUDE_CONFIG_DIR='<disposable-claude-config>' \
  npm run pilot:journalism-core -- claude j-core-1 \
  --project '<disposable-project>'

CODEX_HOME='<disposable-codex-home>' \
  npm run pilot:journalism-core -- codex j-core-1 \
  --project '<disposable-project>'
```

The runner starts subprocesses without a shell, applies a five-minute timeout,
and streams client JSON for inspection. It gives Claude only the tool needed by
the fixture. Codex defaults to its read-only sandbox.

The nested Codex read-only sandbox could not initialize a second Bubblewrap
workspace-reader namespace inside the already isolated top-level session. The
affected Codex probes were rerun with `--unboxed`, as the repository's
`AGENTS.md` permits only when the top-level Codex session is already externally
isolated and was launched with sandbox bypass. Do not use `--unboxed` from an
ordinary unsandboxed shell.

## Harness adjustments and negative evidence

- A descriptive Claude J-core-1 attempt with all tools disabled did not activate
  the installed skill. The accepted explicit test therefore uses Claude's
  stable namespaced slash-command surface.
- The first Claude resource probe did not authorize `Read`. The accepted probe
  exposes only `Read` and adds the disposable install root.
- The first nested Codex read-only probes selected the expected skills but could
  not read the workspace after sandbox initialization failed. Only the reruns
  under the repository-authorized isolated fallback count as passing output.

These adjustments are harness constraints, not additional package support
claims.

## Verification and cleanup

The repeatable harness passed its six focused tests. The repository suite
passed 120 of 120 tests, all 49 page-specific Tailwind stylesheets were current,
and `git diff --check` passed. The disposable test root was removed after the
final verification run.
