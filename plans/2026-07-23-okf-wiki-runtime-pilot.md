# Okf-wiki Codex no-Claude runtime pilot

- Status: passed for portable scaffolding on the Codex project-standards path
- Evidence date: July 23, 2026
- Tracking issue: [#226](https://github.com/jamditis/claude-skills-journalism/issues/226)
- Source revision: [`cabb43bc2515c6c30a3d0839909f786e7afbcba8`](https://github.com/jamditis/claude-skills-journalism/commit/cabb43bc2515c6c30a3d0839909f786e7afbcba8)

## Scope

This pilot tested `okf-wiki` 0.6.1 with Codex CLI 0.145.0 after
skills CLI 1.5.20 copied the root skill into a disposable project's
`.agents/skills/okf-wiki` directory. It exercised installed skill selection,
relative resource reads, one fresh scaffold, generated-file inventory, portable
validation, trust behavior, and uninstall separation.

It does not claim that Codex runs Claude Code hooks, reads
`.claude/settings.json`, maps the Claude plugin package, or supports GitHub-wiki
publishing. No native Codex manifest or new client lifecycle was added.

This was a pre-set fixture, not a general Codex onboarding test. The prompt
supplied every onboarding answer and named the installed project-relative
skill path. The unadapted instructions that name Claude Code's
`AskUserQuestion` and `${CLAUDE_SKILL_DIR}` remain outside this compatibility
claim.

## Isolation and standards installation

The disposable root was `/tmp/okf-wiki-runtime-20260723-pywnoL`. Its project
and client home were empty before installation. Neither contained a `.claude`
directory. The accepted project install was:

```bash
HOME='<disposable-home>' \
NPM_CONFIG_CACHE='<disposable-npm-cache>' \
DISABLE_TELEMETRY=1 \
npx -y skills@1.5.20 add '<checkout>/okf-wiki' \
  --skill okf-wiki \
  --agent codex \
  --copy \
  -y
```

The source and installed copies each contained 114 regular files. Their sorted
relative-path and content manifests had the same SHA-256 digest:

```text
f0af5c80f9daa4afcc71fa8e8919afa2098e59fe2f584bb85cc08df9807c99f1
```

Codex used an explicit disposable `HOME`, `USERPROFILE`, and `CODEX_HOME`; the
authenticated CLI state was reused through a symlink, and no credential
content was copied into the test root or repository. The runner removed
`CLAUDE_CONFIG_DIR` and `CLAUDE_PROJECT_DIR`, ignored user config and project
rules, used an ephemeral session, and refused a pre-existing output directory.
The hardened rerun at
`/tmp/okf-wiki-runtime-20260723-rerun-EZpptM` launched Codex with an
allowlisted executable path containing Codex and required system utilities but
no Claude executable. `command -v claude` failed before the session, no Claude
command appeared in the command record, and the generated tree was
byte-for-byte identical to the first run.

## Okf-1 runtime result

The exact accepted prompt and verifier live in
`scripts/okf-wiki-runtime-pilot.mjs`. The prompt settled every onboarding
choice: internal audience, title `Codex no-Claude pilot`, sections `concepts`
and `decisions`, scaffold-only population, no publishing, and default hook
generation retained only so its output could be classified.

Codex read the installed `SKILL.md`, `spec/SPEC.md`, and
`scripts/scaffold.py`; the scaffolder read or copied the installed validator
and hook templates. It invoked the scaffolder exactly once:

```bash
python3 .agents/skills/okf-wiki/scripts/scaffold.py ./okf-1 \
  --title 'Codex no-Claude pilot' \
  --sections concepts,decisions
```

The generated project contained exactly 12 files:

```text
.claude/hooks/okf-anchor.py
.claude/hooks/okf-orient.py
.claude/settings.json
README.md
SPEC.md
bundle/concepts/example-concept.md
bundle/concepts/index.md
bundle/decisions/example-concept.md
bundle/decisions/index.md
bundle/index.md
requirements.txt
scripts/validate.py
```

Their sorted relative-path and content manifest had SHA-256 digest:

```text
4a4689788d8d28e5b4d2a778dad5a246dd449abe56bb6a3fe05465e2256a47bd
```

The built-in validation and a second direct invocation both reported five
Markdown files, two `Reference` concepts, and:

```text
PASS: bundle conforms to OKF spec v1 (schema, dates, lists, links, secret scan).
```

## Adapter and trust boundary

The portable output is the format contract, dependency declaration, validator,
and bundle tree. `README.md` documents that surface and the optional client
adapter. The three `.claude/` files are Claude adapter output. They were copied
but never executed, and Codex neither read the settings file nor treated it as
configuration.

No interactive trust or approval prompt appeared. The scaffolder printed its
existing notice that Claude Code would request approval for the checked-in
hooks on first open. That future Claude Code prompt was not triggered or
counted as Codex behavior.

The initial `workspace-write` attempt failed before reading the skill or
touching a project file because nested Bubblewrap could not configure loopback:

```text
bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted
```

The accepted run used `--unboxed` only under the repository's `AGENTS.md`
exception for a top-level session already running in external isolation with
sandbox bypass. The disposable `HOME`, ignored config and rules, ephemeral
session, new-target precondition, project path, and exact output verifier
remained in force. This fallback is a harness constraint, not broader
authority for an ordinary shell.

## Uninstall and cleanup

The noninteractive command:

```bash
npx -y skills@1.5.20 remove okf-wiki --agent codex -y
```

removed the installed skill without touching the generated OKF project. The
project lock remained as version 1 with an empty `skills` object, and the
generated bundle still passed the portable validator. This demonstrates three
separate lifecycles:

1. remove `.agents/skills/okf-wiki` through the installer to uninstall the
   Codex skill;
2. keep or delete generated `.claude/` independently as the Claude Code
   adapter; and
3. keep or delete the generated OKF project independently as user data.

Both disposable projects, generated bundles, npm caches, authentication
symlinks, and client homes were moved to the desktop trash after verification.

## Repeatable harness

Run the accepted fixture only with an explicit disposable client home and a
fresh standards install. The selected Python environment must import PyYAML;
the runner now checks this before invoking Codex or the generated validator and
fails with a setup error if it is absent. For an isolated POSIX environment:

```bash
python3 -m venv '<disposable-home>/okf-python'
'<disposable-home>/okf-python/bin/python3' -m pip install \
  -r '<checkout>/okf-wiki/requirements.txt'
```

The runner also resolves `claude` on `PATH` without executing it and refuses
the pilot if one is available. Build a reviewed `<allowlisted-bin>` containing
Codex, Node/npm, and the required shell utilities but no Claude executable,
then place the Python environment and that directory on `PATH`:

```bash
PATH='<disposable-home>/okf-python/bin:<allowlisted-bin>' \
CODEX_HOME='<disposable-home>/.codex' \
  npm run pilot:okf-wiki -- codex okf-1 \
  --project '<disposable-project>' \
  --client-home '<disposable-home>'
```

Use `--unboxed` only under the `AGENTS.md` condition described above. Recheck
an existing artifact without invoking Codex:

```bash
CODEX_HOME='<disposable-home>/.codex' \
  npm run pilot:okf-wiki -- codex okf-1 \
  --project '<disposable-project>' \
  --client-home '<disposable-home>' \
  --verify-only
```

The focused tests pin the accepted prompt, exact portable and adapter
inventories, empty-Claude preconditions, install and output containment,
copied-resource equality, title and section navigation, the PyYAML preflight,
the no-Claude executable preflight, environment stripping, sandbox plan,
authorized fallback, validator invocation, timeout, shell avoidance, and
adversarial CLI inputs.
