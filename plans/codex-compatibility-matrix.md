# Codex compatibility matrix

- Status: phase-two runtime pilots; journalism-core, visual-explainer, and portable okf-wiki scaffolding have scoped passes
- Last evidence update: July 23, 2026
- Architecture: [Codex compatibility architecture decision](2026-07-21-codex-compatibility-architecture.md)

> **The released packages are now newer than everything tested here.** The v2.4.0
> release (July 24, 2026) publishes marketplace 2.4.0, `journalism-core` 1.3.0,
> and `okf-wiki` 0.7.0. Every version recorded below is the version that was
> actually exercised — marketplace 2.3.3, `journalism-core` 1.2.0, `okf-wiki`
> 0.6.1 — and those are deliberately **not** bumped to match the release, because
> this file records evidence and the rule under [Tool baseline](#tool-baseline) is
> to never rewrite an older result as if it ran on the newer version.
>
> The practical consequence for a reader: the unversioned install commands in the
> README now deliver packages that no pilot here has covered. Treat the passes
> below as evidence for the 2.3.3-era packages, not as a support claim for 2.4.0,
> until the pilots are re-run against the released versions. Re-running them is
> what clears this note.

## How to read this matrix

This file records what has been proved for each package. Installation alone is
not a support claim. A package becomes **tested for Codex** only after its
install, discovery, activation, non-activation, resource, runtime, and
no-Claude-environment gates pass.

Status labels:

- **Baseline installed:** a clean client installed the package or skill, but
  runtime behavior is not yet proved.
- **Runtime pilot passed:** paired client behavior passed for the named install
  paths. Other install paths and package-wide support gates remain unclaimed
  unless their evidence says otherwise.
- **Candidate:** the shared skills appear portable from static review, but the
  runtime gates are pending.
- **Adapter required:** static review found a platform-bound path, instruction,
  layout, or generated artifact.
- **Standards blocked:** shared frontmatter fails the Agent Skills validator.
- **Claude-only surface:** the component has no approved Codex mapping.
- **Not assessed:** no runtime claim has been tested.

## Tool baseline

| Tool | Version or revision | Role |
|---|---|---|
| Repository | `b0617649515d24ebfcd51f15bceb1d76b03db668` | Architecture commit used as the phase-one worktree base |
| Repository release verification | [`9eef57629edbaa19bf47ec35296acebdd7b4ab1f`](https://github.com/jamditis/claude-skills-journalism/commit/9eef57629edbaa19bf47ec35296acebdd7b4ab1f) | July 23 post-merge `master` head used for the phase-one release evidence |
| Repository visual-explainer pilot | [`f6a4b84dd2e9feafc6c2bf067f873e9301a083c2`](https://github.com/jamditis/claude-skills-journalism/commit/f6a4b84dd2e9feafc6c2bf067f873e9301a083c2) | July 23 `master` head installed for the V-ex-1 runtime evidence |
| Repository okf-wiki pilot | [`cabb43bc2515c6c30a3d0839909f786e7afbcba8`](https://github.com/jamditis/claude-skills-journalism/commit/cabb43bc2515c6c30a3d0839909f786e7afbcba8) | July 23 `master` head installed for the Okf-1 no-Claude runtime evidence |
| Repository Document design lock pilot | [`d49ed1022a012269a237f7749b0e47c099e7add6`](https://github.com/jamditis/claude-skills-journalism/commit/d49ed1022a012269a237f7749b0e47c099e7add6) | July 23 `master` head used for the D-lock-1 update target |
| Claude Code | 2.1.215; 2.1.218 | Phase-one marketplace validation, then the post-merge clean `journalism-core` install |
| Codex CLI | 0.145.0 | Legacy-compatible marketplace and clean `journalism-core` install |
| skills CLI | 1.5.19; 1.5.20 | Phase-one standards discovery, then post-merge project and user install canaries |
| Agent Skills validator | `agentskills/agentskills@38a2ff82958afee88dadf4831509e6f7e9d8ef4e` | Shared frontmatter contract |
| Agent Skills validator, scheduled | Default-branch head (`38a2ff82958afee88dadf4831509e6f7e9d8ef4e` on July 23, 2026) | Upstream drift signal |
| Claude marketplace | 2.3.3 | Catalog version after the phase-one frontmatter release bumps |
| Node.js on Legion | 22.17.0 | Local test and matrix tooling |
| Node.js on LOJ | 22.23.1 | Repository verification |

Update this table whenever newer client behavior is used as evidence. Do not
rewrite an older result as if it ran on the newer version.

## Baseline evidence

### I-phase-1: package inventory

Environment: the authoritative LOJ worktree at the phase-one branch tip.

Result: the Claude marketplace contained 12 packages and the repository
contained 60 root or nested skills. Package component counts, versions, and
included or excluded surfaces were checked against the marketplace, child
manifests, and discovered `SKILL.md` paths. The package matrix below records the
inventory. Its linked validator and repository results provide the structural
proof for packages that contain shared skills.

### C-base-1: clean Claude package install

Environment: disposable empty `CLAUDE_CONFIG_DIR` on Windows.

```powershell
$env:CLAUDE_CONFIG_DIR = '<empty-temp-directory>'
claude plugin validate '<checkout>'
claude plugin marketplace add '<checkout>'
claude plugin install journalism-core@claude-skills-journalism --scope user
claude plugin list
```

Result: marketplace validation passed; `journalism-core` 1.2.0 installed and
enabled; 14 installed `SKILL.md` files were present. Activation and output were
not tested in this evidence item.

### C-phase-1: repeatable Claude install canary

Environment: a temporary `CLAUDE_CONFIG_DIR` created and removed by the Node
canary. The canary uses the local checkout as the marketplace source.

```bash
npm run canary:journalism-core:claude
```

Result on Claude Code 2.1.215: the current marketplace passed strict validation;
`journalism-core` 1.2.0 installed and enabled; the installed skill names matched
the expected 14-name set and all 17 installed files matched the source hashes.
The canary runs on relevant pull requests, weekly, and on manual dispatch
against the current Claude Code release.

### K-base-1: clean Codex package install through the legacy path

Environment: disposable empty `CODEX_HOME` on Windows.

```powershell
$env:CODEX_HOME = '<empty-temp-directory>'
codex plugin marketplace add jamditis/claude-skills-journalism --json
codex plugin add journalism-core@claude-skills-journalism --json
```

Result: Codex read `.claude-plugin/marketplace.json`, used the package-level
Claude manifest fallback, installed `journalism-core` 1.2.0, and copied all 14
nested skills. No `.codex-plugin/plugin.json` was present. Root skills, Claude
commands, Claude agents, and Claude hooks were not mapped by this test.

### K-phase-1: repeatable Codex legacy-package canary

Environment: a temporary `CODEX_HOME` created and removed by the Node canary.
The canary uses the local checkout as the marketplace source and refuses a
native Codex marketplace or `journalism-core` plugin manifest.

```bash
npm run canary:journalism-core:codex
```

Result on Codex 0.145.0: `journalism-core` 1.2.0 installed and enabled through
the Claude marketplace and package manifests; the installed skill names matched
the expected 14-name set and all 17 installed files matched the source hashes.
The same workflow runs against the current Codex release to warn when this
fallback changes.

### S-base-1: standards-based Codex skill install

Environment: disposable empty project directory on Windows.

```powershell
$env:DISABLE_TELEMETRY = '1'
npx -y skills@1.5.19 add jamditis/claude-skills-journalism `
  --skill fact-check-workflow --agent codex --copy -y
```

Result: the CLI found 60 skills and installed `fact-check-workflow` under
`.agents/skills`. Its lock record preserved the GitHub source, path, and content
hash. Activation and mixed-install behavior were not tested.

### S-phase-1: full journalism-core standards canary

Environment: a disposable project directory with the local
`journalism-core` directory as the standards source.

```bash
npm run canary:journalism-core:codex-skills
```

Result on skills CLI 1.5.19: all 14 skills and 17 files were copied to
`.agents/skills`, their hashes matched the source, and `skills-lock.json`
contained the same 14 names with content hashes. A second
manual check used the public GitHub `journalism-core` subdirectory URL and
produced the same installed set. The scheduled workflow exercises the current
skills CLI release.

### S-global-phase-1: user-level journalism-core standards canary

Environment: a disposable home directory and a separate disposable project
directory. The canary sets both `HOME` and `USERPROFILE` so the install cannot
write to the runner's real user directory.

```bash
npm run canary:journalism-core:codex-skills-global
```

Result on skills CLI 1.5.20: all 14 skills and 17 files were copied to
`~/.agents/skills`, their hashes matched the source, and no file was written to
the disposable project's `.agents/skills` directory. This is Codex's documented
user-level discovery path. The scheduled workflow exercises the current skills
CLI release.

### V-base-1: Agent Skills validation

Environment: disposable checkout at the source baseline. Windows runs set
`PYTHONUTF8=1` because the pinned validator otherwise follows the legacy system
code page.

```powershell
$env:PYTHONUTF8 = '1'
uvx --from "git+https://github.com/agentskills/agentskills.git@38a2ff82958afee88dadf4831509e6f7e9d8ef4e#subdirectory=skills-ref" `
  skills-ref validate '<skill-directory>'
```

Result: 55 of 60 skills passed. `document-design` failed its name, directory,
and `version` checks. The four video skills failed because `argument-hint` is
not an Agent Skills field.

### V-phase-1: repaired standards baseline

```bash
npm run validate:agent-skills
```

Result: all 60 skills passed the pinned official validator. The wrapper finds
root and nested skills, skips installed copies, sets `PYTHONUTF8=1`, and reports
each skill result. Linux pull-request CI runs this command.

### V-upstream-1: current upstream validator canary

```bash
npm run validate:agent-skills:upstream
```

Result on July 21, 2026: all 60 skills passed the current Agent Skills
default-branch validator. Its head was still the pinned revision above. A
separate weekly and manually dispatched job follows the current upstream head;
pull-request validation stays pinned so upstream changes cannot alter a PR gate
without review.

### F-phase-1: affected Claude package regression

Environment: disposable Claude marketplace install plus read-only `--plugin-dir`
invocations with built-in tools disabled.

Result: Claude validated the marketplace, installed `pdf-playground` 1.3.2 and
`video-toolkit` 1.0.3, and found one and four skills respectively. Explicit
`document-design` and `video-download` invocations received their supplied
arguments after the nonstandard `argument-hint` fields were removed. No files
or external tool requests were allowed during the invocations. The affected
package versions were patch-bumped because [Claude uses the declared plugin
version to resolve cached installs](https://code.claude.com/docs/en/plugin-marketplaces#version-resolution-and-release-channels).

### Cv-base-1: Codex creator-helper comparison

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" `
  '<skill-directory>'
```

Result: 54 of 60 passed. The helper rejected the five failures above and also
rejected the standards-valid `compatibility` field in `visual-explainer`. This
extra failure is an expected client/spec difference, not permission to weaken
the shared standard.

### R-base-1: repository checks

Environment: LOJ clean worktree after `npm ci --ignore-scripts`.

```bash
npm test
npm run check:docs-css
```

Result: 93 of 93 tests passed and 49 page-specific Tailwind stylesheets were
current after the architecture record was added.

### R-phase-1: phase-one repository checks

Environment: authoritative LOJ worktree after the phase-one files were synced
with LF line endings.

```bash
npm test
npm run check:docs-css
```

Result: 114 of 114 tests passed on Linux and all 49 page-specific Tailwind
stylesheets were current. The added adversarial fixtures reject linked install
roots, linked skill resources, and Windows shell parsing of client arguments.
The earlier Windows staging run passed 109 tests with the one NTFS-impossible
colon fixture skipped. Actionlint 1.7.12 accepted both changed workflow files,
`git diff --check` passed, and strict Claude marketplace validation passed on
Claude Code 2.1.215. The Windows CSS freshness check also verified all 49
stylesheets after line endings were normalized for comparison.

### P-release-1: post-merge master verification

Environment: public `master` at
[`9eef57629edbaa19bf47ec35296acebdd7b4ab1f`](https://github.com/jamditis/claude-skills-journalism/commit/9eef57629edbaa19bf47ec35296acebdd7b4ab1f)
on July 23, 2026.

The manually dispatched
[Client compatibility canary run 30026490472](https://github.com/jamditis/claude-skills-journalism/actions/runs/30026490472)
passed all five jobs from `master`:

- Claude Code 2.1.218 installed `journalism-core` 1.2.0 with the expected 14
  skills and 17 source-matching files.
- Codex CLI 0.145.0 installed the same package, skill set, and files through
  the legacy-compatible marketplace path.
- skills CLI 1.5.20 installed the expected 14 skills and 17 files through both
  the project and user standards paths.
- The current upstream Agent Skills validator passed all 60 skills. Its
  default-branch revision remained
  [`38a2ff82958afee88dadf4831509e6f7e9d8ef4e`](https://github.com/agentskills/agentskills/commit/38a2ff82958afee88dadf4831509e6f7e9d8ef4e).

A separate empty `CLAUDE_CONFIG_DIR` cloned the public repository and confirmed
marketplace 2.3.3 exposes installable `pdf-playground` 1.3.2 and
`video-toolkit` 1.0.3. Both installed and were enabled. A fresh
`skills@1.5.20` public-repository discovery found exactly 60 source skills.
The disposable configurations were not reused as runtime evidence.

### J-release-1: paired journalism-core runtime pilot

Environment: public `master` at
[`9eef57629edbaa19bf47ec35296acebdd7b4ab1f`](https://github.com/jamditis/claude-skills-journalism/commit/9eef57629edbaa19bf47ec35296acebdd7b4ab1f)
installed into separate disposable Claude and Codex profiles on July 23, 2026.
The [paired runtime record](2026-07-23-journalism-core-runtime-pilot.md)
contains the exact scope, prompts, selection evidence, output summaries,
resource hash, harness adjustments, verification, and cleanup.

Result: Claude Code 2.1.218 passed explicit activation through the installed
namespaced command, implicit `source-verification` selection, unrelated
non-trigger behavior, and installed `photo-metadata/reference.md` resolution.
Codex CLI 0.145.0 passed the same behavior through a skills CLI 1.5.20 project
standards install. The legacy-compatible Codex package path and user-level
standards path remain install-only evidence.

### V-ex-release-1: visual-explainer root-skill runtime pilot

Environment: public `master` at
[`f6a4b84dd2e9feafc6c2bf067f873e9301a083c2`](https://github.com/jamditis/claude-skills-journalism/commit/f6a4b84dd2e9feafc6c2bf067f873e9301a083c2)
installed into a disposable Codex project on July 23, 2026. The
[runtime record](2026-07-23-visual-explainer-runtime-pilot.md) contains the
exact scope, install command, file-manifest digest, prompt, installed resource
reads, output digest, render review, validator difference, legacy omission,
harness behavior, and cleanup.

Result: Codex CLI 0.145.0 discovered `$visual-explainer` after skills CLI
1.5.20 copied the 24-file root skill into `.agents/skills`. V-ex-1 read the
installed `references/css-patterns.md` and `templates/architecture.html`, then
produced the requested four-stage newsroom architecture HTML. Desktop, mobile,
light, and dark checks found no overflow or runtime errors; the automated axe
checks found no WCAG 2.2 A or AA violations.

The legacy-compatible Codex plugin route cached the source root `SKILL.md` but
did not register it as a root skill. Codex generated three untested command
wrappers; they remain outside this root-skill runtime claim. The official
validator accepted the standards copy, while the creator helper produced only
the already-allowlisted `compatibility`-field difference.

### Okf-release-1: okf-wiki no-Claude runtime pilot

Environment: public `master` at
[`cabb43bc2515c6c30a3d0839909f786e7afbcba8`](https://github.com/jamditis/claude-skills-journalism/commit/cabb43bc2515c6c30a3d0839909f786e7afbcba8)
installed into a disposable Codex project with a separate empty home on July
23, 2026. The [runtime record](2026-07-23-okf-wiki-runtime-pilot.md)
contains the exact isolation, source and output manifests, accepted prompt,
commands, generated-file inventory, validation, trust boundary, adapter
classification, uninstall behavior, and cleanup.

Result: Codex CLI 0.145.0 discovered `$okf-wiki` after skills CLI 1.5.20
copied the 114-file root skill into `.agents/skills`. The skill read its
installed instructions, spec, scaffolder, validator, and hook templates;
invoked the scaffolder once; created exactly nine portable/project files and
three Claude adapter files; and reported that exact inventory. Codex passed the
scaffolder's built-in validation and one direct portable validation, then the
harness repeated validation after the session. No Claude configuration
directory was available outside the generated output, no interactive prompt
appeared, and no hook executed.

The `.claude/` settings and hooks are recorded as a Claude Code adapter, not
Codex project behavior. Removing the installed skill left the generated
project intact and valid, while the empty lock entry, Claude adapter directory,
and OKF user data remained independently removable.

### D-lock-release-1: Document design standards lock migration

Environment: Codex CLI 0.145.0 with a disposable skills CLI 1.5.20 project on
July 23, 2026. The
[migration record](2026-07-23-document-design-lock-migration.md) contains the
historical fixture, exact source commits, hashes, failure, migration boundary,
two update passes, verification, and cleanup.

Result: skills CLI 1.5.20 exited 1 when its project updater passed the
historical `Document design` lock key back to the current repository. The
explicit repository migration renamed only the exact
`jamditis/claude-skills-journalism` and
`pdf-playground/skills/document-design/SKILL.md` identity. It left the
installed directory and complete record intact, rejected ambiguous inputs, and
did not run automatically.

After migration, two consecutive skills CLI updates exited 0. Exactly one
`document-design` lock identity remained; its repository source, skill path,
installed directory, frontmatter, and content hash matched. The second update
left the lock and installed-tree digests unchanged. This is local lock
migration evidence, not public catalog history or a mixed-install claim.

## Package matrix

| Package | Version and components | Current classification | Included and excluded scope | Evidence | Next proof |
|---|---|---|---|---|---|
| `autocontext` | 1.1.0; no skills; five commands; one agent; six hook files | Claude-only surface | Include nothing in the Codex claim. Commands, curator agent, hook lifecycle, persisted data, and compatibility environment variables need a separate design. | [I-phase-1](#i-phase-1-package-inventory) | Define state, lifecycle, authority, and uninstall contracts in a separate accepted decision. |
| `dev-toolkit` | 1.1.1; 11 nested skills | Candidate with adapter review | Instruction-led skills may be shared. Exclude Claude tool vocabulary, `CLAUDE.md` updates, hook wiring, and Claude subagent syntax until tested. | [V-phase-1](#v-phase-1-repaired-standards-baseline) covers structure | Classify each skill; add explicit trigger and non-trigger fixtures for the portable subset. |
| `journalism-core` | 1.2.0; 14 nested skills | Runtime pilot passed on the Claude package and Codex project-standards paths | Include the 14 shared skills. No commands, agents, or hooks are part of this package. The legacy-compatible Codex package and user-level standards paths remain install-only. | [J-release-1](#j-release-1-paired-journalism-core-runtime-pilot), [C-phase-1](#c-phase-1-repeatable-claude-install-canary), [K-phase-1](#k-phase-1-repeatable-codex-legacy-package-canary), [S-phase-1](#s-phase-1-full-journalism-core-standards-canary), [S-global-phase-1](#s-global-phase-1-user-level-journalism-core-standards-canary), [V-phase-1](#v-phase-1-repaired-standards-baseline) | Add a no-Claude-environment gate and scheduled runtime regression before a broader package support claim. |
| `okf-wiki` | 0.6.1; one root skill; scripts and generated Claude settings | Pre-set portable runtime pilot passed; instruction and Claude-output adapters remain | Include the tested Okf-1 path: standards discovery, installed spec and scaffolder reads, explicit project-relative scaffolding, validation, examples, and the generated OKF bundle. Exclude the unadapted general instructions that name `AskUserQuestion` and `${CLAUDE_SKILL_DIR}`. The generated `.claude/settings.json` and hook scripts are an inert Claude Code adapter, not Codex configuration or lifecycle behavior. | [Okf-release-1](#okf-release-1-okf-wiki-no-claude-runtime-pilot), [V-phase-1](#v-phase-1-repaired-standards-baseline), and [R-phase-1](#r-phase-1-phase-one-repository-checks) | Port and test general onboarding and skill-root resolution; add scheduled Okf-1 coverage against current Codex; test mixed-client hook trust separately before any cross-client lifecycle claim. |
| `pdf-design` | 1.1.0; one root skill | Adapter required | Shared design guidance and assets are candidates. Hard-coded `~/.claude` and host-specific browser paths are excluded from a Codex claim. | [V-phase-1](#v-phase-1-repaired-standards-baseline) covers structure | Add a no-Claude path-resolution fixture before editing paths. |
| `pdf-playground` | 1.3.2; one nested skill; eight commands; one hook file | Candidate plus Claude-only surfaces | `document-design` is shared. Its historical project lock identity has an explicit migration. Commands and hook behavior remain Claude-only until mapped. | [D-lock-release-1](#d-lock-release-1-document-design-standards-lock-migration), [V-phase-1](#v-phase-1-repaired-standards-baseline), and [F-phase-1](#f-phase-1-affected-claude-package-regression); lock migration, standards, Claude install, and argument delivery pass | Test Codex activation, non-activation, resource loading, and output before a runtime claim. |
| `project-templates-toolkit` | 1.0.0; three nested skills | Adapter required | Retrospective and template selection may be shared. `project-memory` must distinguish `CLAUDE.md` from `AGENTS.md` scope. | [V-phase-1](#v-phase-1-repaired-standards-baseline) covers structure | Add paired Claude/Codex project-memory fixtures before changing generated instructions. |
| `research-toolkit` | 1.1.0; six nested skills | Candidate | Include shared instruction-led skills. Network and external-content trust boundaries stay unchanged. | [V-phase-1](#v-phase-1-repaired-standards-baseline) covers structure | Add representative activation, non-activation, network-boundary, and resource checks. |
| `security-toolkit` | 1.2.0; four nested skills; one command | Candidate plus Claude-only surface | The four shared skills are candidates. `/security-toolkit:hotpatch` and its sandbox lifecycle remain Claude-only. | [V-phase-1](#v-phase-1-repaired-standards-baseline) covers structure; [R-phase-1](#r-phase-1-phase-one-repository-checks) covers security tests | Test skill activation separately; do not map `hotpatch` without authority and failure-semantics tests. |
| `superjawn` | 1.0.0; 14 nested skills | Not assessed | No package-wide claim. Each skill needs review for Claude tool names, namespacing, agent dispatch, and parallel-agent assumptions. | [V-phase-1](#v-phase-1-repaired-standards-baseline) covers structure only | Evaluate one skill at a time with client-specific tool traces. Do not bulk-port. |
| `video-toolkit` | 1.0.3; four nested skills; external media runtimes | Candidate; runtime dependencies pending | Shared frontmatter and Claude argument delivery pass. GPU, CPU, browser, media sandbox, and hosted-API behavior remain unclaimed. | [V-phase-1](#v-phase-1-repaired-standards-baseline), [F-phase-1](#f-phase-1-affected-claude-package-regression), and [R-phase-1](#r-phase-1-phase-one-repository-checks) | Run dependency, no-GPU, activation, non-activation, and output fixtures. |
| `visual-explainer` | 0.7.1; one root skill; eight source commands | Runtime pilot passed on the Codex project-standards path; command surfaces unclaimed | Include the root skill and its relative resources only through `.agents/skills`. The legacy route omits root-skill registration. Its three client-generated command wrappers and all eight source commands remain outside this claim. | [V-ex-release-1](#v-ex-release-1-visual-explainer-root-skill-runtime-pilot), [V-phase-1](#v-phase-1-repaired-standards-baseline), and [Cv-base-1](#cv-base-1-codex-creator-helper-comparison) | Add a no-Claude-environment gate and scheduled runtime regression before a broader package claim; test command wrappers only in a separately scoped issue. |

## Pilot fixtures

These fixtures define the minimum behavior to test. Store raw outputs or CI
links beside the matrix result when each one runs.

### J-core-1: explicit verification workflow

Prompt:

> Use the installed fact-check workflow to build a verification plan for an
> unsigned screenshot claiming that a city budget doubled in 2025. Treat the
> claim as unverified and do not invent sources.

Expected result: the intended skill is selected; the response separates the
claim, evidence needed, primary sources, corroboration, status, and uncertainty;
no unsupported factual verdict is produced.

### J-core-2: implicit verification trigger

Prompt:

> I received an unsigned screenshot with a public-spending claim. What should I
> verify before publication?

Expected result: a relevant journalism-core verification skill activates without
an explicit skill name and follows its sourcing and uncertainty rules.

### J-core-3: non-trigger

Prompt:

> Calculate an 18% tip on a $42 meal.

Expected result: no journalism-core skill activates.

### V-ex-1: root-skill layout

Install `visual-explainer` through the standards path, then ask for a small HTML
architecture diagram from supplied text.

Expected result: the root skill is discovered, reads its relative references and
assets from the installed copy, and produces the requested file. The legacy
package path is expected not to expose this root skill until evidence says
otherwise.

The exact accepted prompt and semantic output verifier live in
`scripts/visual-explainer-runtime-pilot.mjs`. Run them with:

```bash
CODEX_HOME='<disposable-codex-home>' \
  npm run pilot:visual-explainer -- codex v-ex-1 \
  --project '<disposable-project>'
```

### Okf-1: no-Claude scaffold

Run the installed `okf-wiki` skill against an empty temporary project with no
Claude configuration directory available.

Expected result: portable OKF files validate and no missing `~/.claude` path
causes the run to fail. Generated Claude settings are recorded as a Claude
adapter rather than silently treated as Codex configuration.

The exact accepted prompt, empty-Claude preconditions, generated-file
inventory, and portable validator live in
`scripts/okf-wiki-runtime-pilot.mjs`. Run them with:

```bash
CODEX_HOME='<disposable-home>/.codex' \
  npm run pilot:okf-wiki -- codex okf-1 \
  --project '<disposable-project>' \
  --client-home '<disposable-home>'
```

Expected files are nine portable/project files and three `.claude/` adapter
files. No hook runs under Codex. The standards-installed skill, generated
Claude adapter, and generated OKF project have separate removal lifecycles.

## Known differences and allowlist

| Difference | Scope | Policy | Removal condition |
|---|---|---|---|
| Codex `quick_validate.py` rejects `compatibility` | `visual-explainer/SKILL.md` on Codex 0.145.0 | Allow only this validator difference while the official validator and installed Codex runtime accept the skill. | Codex aligns its helper, the installed runtime rejects the skill, or the field is no longer needed. |
| Official validator uses the Windows legacy code page by default | Windows validation at validator commit `38a2ff8` | Set `PYTHONUTF8=1`; run the required CI gate on Ubuntu. | Upstream reads `SKILL.md` as UTF-8 explicitly. |
| Legacy Codex plugin install omits root skills and Claude-only components | Root-skill packages, commands, agents, and hooks | Do not claim those components through the legacy package path. Prefer standards installation for skills. | A documented and tested Codex adapter exposes the component. |
| [Codex does not deduplicate same-name skills across install roots](https://github.com/openai/codex/issues/22626#issuecomment-4452261501) | `.agents/skills`, `$CODEX_HOME/skills`, legacy plugin cache, and desktop import | Recommend `.agents/skills` through `npx skills` for new Codex users and one Codex path per skill. Do not recommend the bundled installer or mixed paths during phase one. | Duplicate identity, precedence, update, uninstall, recovery, and drift tests pass for the paths being combined. |

Do not add an expected difference merely to make CI green. Each entry needs a
standards or runtime citation, the narrow affected path, and a condition for
removal.

## Public catalog watch

On July 21, 2026, [skills.sh listed this repository](https://www.skills.sh/jamditis/claude-skills-journalism)
with 56 indexed skills and 13.6K aggregate installs while the checkout contained
60 skills. The four video skills were absent, matching their pre-fix validator
failures. `document-design` appeared in the aggregate but its
[detail page](https://www.skills.sh/jamditis/claude-skills-journalism/document-design)
did not show first-seen or install data. Other aggregate and detail counts also
differed, so these numbers are a dated catalog snapshot rather than a stable
user total.

On July 23, 2026, a cache-revalidated public fetch listed 62 catalog rows while
the same public repository produced exactly 60 skills through
`skills@1.5.20`. Comparing the two name sets found all 60 current skills plus
only the deleted `animated-sprite-gen` and `nano-banana-image-gen` rows. This is
a catalog deletion discrepancy rather than a missing-source problem. It is
tracked in [repository issue #219](https://github.com/jamditis/claude-skills-journalism/issues/219)
and the existing upstream stale-snapshot report
[`vercel-labs/skills#1189`](https://github.com/vercel-labs/skills/issues/1189).

The existing `document-design` URL now serves the normalized lowercase identity
and current skill content, but the catalog shows 2 installs and “First Seen:
Today.” Its earlier catalog history was therefore not preserved across the
frontmatter-name repair. Recovery requires a catalog-side identity/metrics
alias or restoration for the same repository, path, and slug; another source
rename would create more identity churn and is not a recovery. Track that
catalog-side request with #219 and the upstream stale-snapshot report above.

[D-lock-release-1](#d-lock-release-1-document-design-standards-lock-migration)
separately proves the local `Document design` lock migration and prevents two
lock identities from remaining for one installed directory. That project
migration neither restores nor changes public catalog metrics.

## Mixed-install cases still pending

Desktop import has not been exercised for this repository. Before recommending
more than one Codex installation path in the same profile, test:

1. import into a clean Codex profile;
2. import when the same skill exists under `.agents/skills`;
3. import when the containing plugin is installed from the legacy marketplace;
4. update one copy while another remains stale;
5. uninstall one path and confirm discovery, recovery, and lock data.

Record duplicate identity, precedence, activation, update, uninstall, recovery,
and drift results here. Until then, documentation must recommend one Codex
installation path per skill or package.
