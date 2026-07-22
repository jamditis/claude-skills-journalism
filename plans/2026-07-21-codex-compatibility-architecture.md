# Codex compatibility architecture decision

- Status: accepted
- Decision date: July 21, 2026
- Decision owner: Joe Amditis
- Implementation branch: `feat/codex-compatibility`
- Base commit: `64dc95d8584d66e35ceb79e3c43e7fa3d201d3e4`

## Decision summary

Add Codex support inside `jamditis/claude-skills-journalism`. Keep the current
repository name, GitHub identity, skill directory paths, plugin names, release
history, and Claude installation path.

The shared contract is each skill's standards-conforming `SKILL.md`, scripts,
references, and assets. Claude and Codex packaging are adapter layers around
that shared content. The existing Claude marketplace remains authoritative for
Claude. Codex's standards-based skill installation is the primary Codex path.
Codex documents `.claude-plugin/marketplace.json` as a legacy-compatible
marketplace location. Its fallback to each package's
`.claude-plugin/plugin.json` is observed behavior and remains a monitored
convenience rather than the native package contract.

Do not add native Codex marketplace or plugin manifests during the first phase.
Add them later only when a tested Codex feature needs them or when the
package-level Claude-manifest fallback stops working. Do not create a second
repository, rename this repository, move skill directories, or introduce a
private cross-vendor metadata format.

Use the reversible public display name **Journalism agent skills** where a
vendor-neutral label helps. Keep technical identifiers unchanged.

## Why this decision is needed

The repository started as a Claude Code collection and is now used through
more than one agent. It has community and catalog value that should not be
split to make the file layout look cleaner:

- 335 GitHub stars and 57 forks at the decision date;
- about 15,000 listed installs on skills.sh;
- 60 `SKILL.md` files in 12 Claude marketplace packages;
- an established Claude marketplace name, plugin names, and install commands;
- external links and installed copies that refer to the current repository and
  skill paths.

GitHub redirects most repository traffic after a rename, but skills.sh keys a
listing to its `owner/repository` source. A July 2026 report showed old and new
repository names becoming separate skills.sh identities without transferred
install counts. A second repository would split stars, forks, issues, releases,
install counts, documentation, and maintainer attention by design.

There is no published `jamditis/Codex-skills-journalism` repository in the
authenticated GitHub account. The Codex marketplace registered on the Legion
as `claude-skills-journalism` points to
`https://github.com/jamditis/claude-skills-journalism.git`. That local entry is
not evidence of a separate port.

## Evidence behind the decision

The following checks were run against the repository at the base commit.

### Existing Claude behavior

- Claude Code 2.1.215 accepted the root marketplace with
  `claude plugin validate`.
- A disposable `CLAUDE_CONFIG_DIR` added the local marketplace and installed
  `journalism-core@claude-skills-journalism` version 1.2.0.
- The clean install contained all 14 `journalism-core` skills.

These results establish the Claude baseline that later work must preserve.

### Existing Codex behavior

- A disposable empty `CODEX_HOME` with Codex CLI 0.145.0 added the untouched
  GitHub repository and installed `journalism-core` through
  `.claude-plugin/marketplace.json`.
- That legacy install copied all 14 nested `journalism-core` skills without a
  `.codex-plugin/plugin.json` file.
- Codex did not turn root `SKILL.md` files, Claude commands, Claude agents, or
  Claude hooks into equivalent Codex components.
- `npx skills add` found all 60 skills in the repository and installed
  `fact-check-workflow` for Codex under `.agents/skills`.
- Codex source currently checks native marketplace and plugin manifests before
  legacy Claude manifests. The legacy marketplace location is documented by
  Codex; fallback to a package's `.claude-plugin/plugin.json` and its exact
  precedence are observed implementation behavior.
- Codex desktop documents import from another agent and says the source setup is
  left unchanged. This repository's desktop-import result and mixed-install
  behavior have not yet been tested.

The clean tests prove that useful Codex paths already exist. They do not prove
that every installed workflow behaves correctly or that the legacy reader will
remain available.

### Standards baseline

The official `skills-ref` validator was pinned to Agent Skills repository commit
`38a2ff82958afee88dadf4831509e6f7e9d8ef4e` for the audit. With Python UTF-8
mode enabled, 55 of 60 skills passed.

The five standards failures are:

- `pdf-playground/skills/document-design/SKILL.md`: display-style `name`, a
  name/directory mismatch, and a top-level `version` field;
- the four `video-toolkit` skills: Claude-only `argument-hint` frontmatter.

Codex 0.145.0's bundled `quick_validate.py` passed 54 of 60. It rejected the
same five files and also rejected `compatibility` in
`visual-explainer/SKILL.md`, even though `compatibility` is allowed by the Agent
Skills specification. The official validator also needs `PYTHONUTF8=1` on
Windows because its current default text decoding follows the legacy system
code page.

These client and platform differences must be visible in tests. A vendor helper
does not override the shared specification.

### Independent review

Claude Code CLI 2.1.215 ran `claude-fable-5` at high effort as a read-only
architecture reviewer. It agreed with one repository, the current slug, shared
skill content, one release history, deferred platform-bound packages, and no
early dual manifests. Its main correction was to make standards compliance the
foundation and treat Codex's Claude-manifest reader as a monitored bonus. The
standards-first correction is adopted. The reader claim is narrowed because the
official Codex manual documents the legacy marketplace location, while the
per-package Claude manifest fallback remains source-observed behavior.

## Contract hierarchy

The project relies on three layers in this order:

1. **Agent Skills specification.** This defines the portable skill directory,
   `SKILL.md`, standard frontmatter, scripts, references, assets, and relative
   file references. Shared skill content targets this layer.
2. **Vendor-owned packaging.** `.claude-plugin` is the supported Claude adapter.
   A future `.codex-plugin` or `.agents/plugins` layer would be a supported
   Codex adapter. Each vendor owns only its layer.
3. **Codex compatibility paths.** Codex's legacy-compatible marketplace location
   and desktop import flow are documented Codex behavior. The package-level
   fallback to `.claude-plugin/plugin.json` is tested and source-observed, but it
   is not the documented native plugin contract.

When the layers disagree, protect the shared skill contract and record the
client-specific behavior. Do not weaken a standards-conforming skill solely to
make an internal vendor helper pass unless the installed runtime also fails and
no smaller adapter can solve it.

## Canonical source and adapter placement

The canonical source for a portable workflow is its existing skill directory:

```text
<package>/skills/<skill>/
├── SKILL.md
├── scripts/
├── references/
└── assets/
```

Root-skill packages keep their current layout unless an installed-runtime test
proves that an adapter is required. Do not move or rename directories to make a
catalog look uniform. Directory paths are part of skill discovery, skills.sh
identity, documentation, forks, and installed update paths.

Vendor adapters live beside the package they adapt:

- Claude: existing `.claude-plugin/plugin.json`, commands, agents, and hook
  configuration;
- Codex, when justified: `.codex-plugin/plugin.json`, `agents/openai.yaml`,
  Codex hooks, or another documented Codex component;
- repository catalogs: keep `.claude-plugin/marketplace.json`; add
  `.agents/plugins/marketplace.json` only when a native Codex package requires
  it.

Do not duplicate scripts, references, assets, or skill bodies. A wrapper or
generated adapter is allowed only after two real cases show the same mapping and
a drift test protects it. Until then, prefer a small explicit adapter.

## Frontmatter policy

Shared `SKILL.md` files use the Agent Skills fields needed by the workflow:

- `name` and `description` are required;
- `license`, `metadata`, and `compatibility` may be used when the specification's
  stated purpose calls for them;
- `allowed-tools` remains experimental and must not be used as a portable
  security boundary;
- vendor-only fields do not belong in shared frontmatter.

If Claude needs an invocation hint, command wrapper, hook, or agent definition,
put it in the Claude adapter or express non-load-bearing guidance in the skill
body. The four video skills must not rely on `argument-hint` for their portable
behavior.

`compatibility` is standards-valid but rejected by Codex 0.145.0's creator
helper. Keep the standards validator authoritative, test the installed Codex
runtime separately, and maintain a narrow expected-difference list until Codex
and the specification agree. Do not add `compatibility` mechanically to every
skill; most skills do not need it.

## Distribution and support policy

Claude users keep the current marketplace flow and plugin names.

For Codex, support is introduced in this order:

1. standards-based installation through skills.sh or `npx skills add`;
2. the documented legacy-compatible marketplace location, with the current
   package-manifest fallback covered by a clean-install canary;
3. Codex desktop import for existing Claude users who choose to import;
4. native Codex manifests only after a trigger below is met.

The desktop import journey is additive: it leaves the Claude setup in place.
Instructions and scripts must therefore work when the same user has both tools
installed and may invoke the same skill from either one. Shared content must not
assume that `~/.claude` exists, that a Claude-only tool name is available, or
that only one agent will touch a workspace.

Recommend standards-based installation through skills.sh or `npx skills add`
for a new Codex setup. Treat the legacy marketplace as a package-install
convenience and desktop import as a migration path until collision tests prove
mixed installs safe. Documentation must tell users to choose one Codex install
path per skill or package during this period.

Before recommending mixed installs, test desktop import into:

- a clean Codex profile;
- a profile where the same skill was installed through `npx skills add`;
- a profile where the containing plugin was installed through the legacy
  marketplace path.

For each case, record duplicate identity handling, discovery and activation
precedence, update behavior, uninstall behavior, recovery after one copy is
removed, and content drift when installed copies differ.

Do not claim that the whole repository is Codex-compatible at once. Publish
support per package after its runtime gates pass. Early documentation should
state the tested client version and distinguish standards-based skills from
Claude-only commands, hooks, and agents.

## Trigger for native Codex manifests

Add a native Codex manifest only when at least one of these conditions is
demonstrated:

- a documented Codex component is needed for behavior that a bare skill cannot
  provide;
- the package-level Claude-manifest fallback stops installing a package;
- a Codex-native marketplace provides user value that skills.sh cannot provide;
- root-skill or resource layout needs an adapter that the native manifest can
  express;
- measured Codex marketplace usage justifies the permanent version-sync cost.

Before adding the first native manifest, write a failing install or runtime test
that proves the need. Preserve the Claude manifest. Define which fields are
canonical, how versions stay equal, and how CI detects drift before publishing.

## Package routing

| Package | Current shape | Initial Codex treatment |
|---|---|---|
| `journalism-core` | 14 nested, instruction-led skills | Regression baseline and first runtime pilot |
| `research-toolkit` | Six nested, instruction-led skills | Standards validation, then grouped runtime tests |
| `dev-toolkit` | 11 nested skills with several Claude assumptions | Port portable skills first; audit tool vocabulary separately |
| `security-toolkit` | Four nested skills plus a Claude command | Skills may port; `hotpatch` remains Claude-only until mapped and tested |
| `visual-explainer` | Root skill plus Claude commands | Root-layout canary through standards install; commands remain Claude-only |
| `pdf-design` | Root skill with hard-coded Claude paths | Remove path assumptions before a Codex support claim |
| `project-templates-toolkit` | Three nested skills centered on `CLAUDE.md` | Design explicit `CLAUDE.md` and `AGENTS.md` branches |
| `okf-wiki` | Root skill, scripts, tests, and generated Claude settings | Runtime canary in a no-Claude environment; preserve OKF behavior |
| `pdf-playground` | One nested skill, eight Claude commands, and a hook script | Fix standards failure; treat command and hook mapping as later work |
| `video-toolkit` | Four nested skills with vendor frontmatter and external runtimes | Fix shared frontmatter; defer runtime support until dependencies are tested |
| `superjawn` | 14 nested workflow skills with Claude tool and subagent assumptions | Evaluate each skill; do not bulk-label the package portable |
| `autocontext` | Commands, agent, and hooks; no skill | Separate integration project after lifecycle and storage design |

This table is routing, not a support claim.

## Pilot sequence

The first three packages exercise different failure modes:

1. **`journalism-core` regression baseline.** It already installs through both
   tested clients. Add activation, non-activation, reference-resolution, and
   output checks so later changes cannot silently break it.
2. **`visual-explainer` layout canary.** Expect standards-based installation to
   see the root skill and the legacy Codex plugin path not to expose it. Record
   that asymmetry. Do not move the skill to make both paths look identical.
3. **`okf-wiki` behavior canary.** Run its scripts and scaffolding in an
   environment without Claude installed. Separate portable OKF behavior from
   generated Claude settings before adding Codex behavior.

`document-design` is the negative standards fixture until its failing test is
in place. After the test proves the current violation, fix its frontmatter and
move `version` into `metadata` if the skill still needs a skill-level version.

## Verification gates

A package can be labeled tested for Codex only when evidence proves every
applicable gate.

### Shared skill gates

- The official `skills-ref` validator passes every portable skill.
- Skill names match their directory names.
- Standard file references are relative to the skill root and resolve in an
  installed copy.
- No portable instruction depends on a Claude-only frontmatter field, path,
  environment variable, tool name, command, hook, or agent.
- Network, credential, shell, and external-write requirements are explicit and
  unchanged by the port.

### Claude regression gates

- `claude plugin validate <path>` passes.
- A disposable Claude configuration can add the marketplace and install the
  package.
- Documented and previously verified commands, agents, hooks, scripts, and skill
  activation still work.
- Components that were inert or unverified at the baseline remain explicitly
  classified; making them active is separate work with its own tests.
- Package tests and repository tests pass.

### Codex gates

- A disposable empty `CODEX_HOME` or project installs the intended skill or
  package through the documented support path.
- Every intended skill is discoverable.
- Explicit invocation, representative implicit triggers, and non-trigger prompts
  behave as specified in a fresh session.
- Scripts resolve resources from the installed copy rather than the source
  checkout.
- The test runs in an environment without `~/.claude` unless Claude is an
  explicit package requirement.
- Any expected difference between the Agent Skills validator and a Codex helper
  is narrow, recorded, and verified against the installed runtime.
- Desktop import and mixed-install behavior are not labeled supported until the
  collision cases above pass, including update, uninstall, and recovery checks.

### Repository gates

- `npm test` passes.
- `npm run check:docs-css` passes.
- Package-specific tests pass.
- Catalog names, descriptions, and versions agree wherever the same package is
  represented.
- A clean-install canary detects a Codex release that removes or changes the
  package-level Claude-manifest fallback.

Run the official validator in Linux CI. If it runs on Windows, set
`PYTHONUTF8=1`. Pin the validator for repeatable pull-request results and update
the pin in a separate scheduled canary so upstream changes are reviewed rather
than absorbed silently.

### Required evidence record

Maintain a checked-in `plans/codex-compatibility-matrix.md`. Give every package
one row containing:

- support classification and which components are included or excluded;
- Claude, Codex, skills CLI, and validator versions used;
- exact installation path and commands;
- test fixtures, trigger prompts, non-trigger prompts, and expected results;
- known client differences and their narrow allowlist;
- links to CI runs, pull requests, or local verification records that carry the
  evidence.

A package support claim is incomplete until its matrix row points to current
proof. The routing table in this decision is a work queue and does not replace
that evidence record.

## Rollout plan

### Phase one: standards and baselines

- Add a failing repository test that reproduces the five current Agent Skills
  validation failures.
- Add `plans/codex-compatibility-matrix.md` and seed all 12 package rows from the
  verified inventory without overstating runtime support.
- Add a validator harness with a pinned standards validator and explicit UTF-8
  behavior.
- Fix `document-design` and the four video-skill frontmatter failures while
  preserving Claude invocation guidance.
- Add clean Claude and Codex install baselines for `journalism-core`.
- Document the existing Codex installation choices without claiming package
  behavior that has not passed runtime tests.

### Phase two: representative pilots

- Add activation and non-activation checks for `journalism-core`.
- Test `visual-explainer` through the standards path and record the legacy
  marketplace limitation.
- Test `okf-wiki` in a no-Claude environment and design only the adapter its
  failing tests require.

### Phase three: grouped package work

- Port instruction-led packages in small pull requests grouped by runtime
  shape.
- Handle root skills, commands, hooks, agents, and generated project settings as
  separate adapter problems.
- Publish a Codex support statement only for packages whose gates pass.

### Phase four: native packaging, if triggered

- Introduce the smallest native Codex adapter proven necessary by a failing
  test.
- Add cross-manifest version and description checks before the adapter is
  published.
- Re-run both clients' clean-install and fresh-session tests before release.

## One-way doors kept closed

The following decisions remain deferred because reversing them would break
identity, installs, or support promises:

- renaming the GitHub repository or marketplace;
- creating a separate Codex repository or mirror;
- moving or renaming skill directories;
- publishing native Codex manifests before their maintenance contract exists;
- adding a private neutral metadata schema;
- promising repository-wide Codex support before per-package runtime proof;
- mapping Claude hooks, agents, and commands by filename without lifecycle and
  authority tests.
- choosing a persistent-state schema or storage location for cross-client data;
- enabling new automatic execution or changing hook failure behavior;
- changing credential, authentication, or authorization boundaries;
- widening network access, shell authority, or external-write behavior.

The last four require a separate accepted decision before implementation, even
when a runtime test appears to pass.

Revisit a deferred decision only with new evidence such as a skills.sh identity
migration, documented cross-vendor manifest support, a changed Agent Skills
standard, a broken clean-install canary, or measured demand for a native Codex
package surface.

## Consequences

This design protects the repository's public identity and keeps one editable
copy of each workflow. Standards fixes improve every conforming client. Claude
users keep their current installation path, and Codex users gain a support path
that does not depend on a duplicate repository.

The tradeoff is that the repository will carry mixed support states for a time.
Some skills are portable, some install but still contain Claude assumptions, and
some packages have no standards-based equivalent for their commands, hooks, or
agents. Documentation and tests must state those boundaries plainly.

Native Codex packaging may arrive later. Deferring it avoids a second manifest
catalog and permanent sync work before user value is known, while the clean
install canary gives early warning if the package-level fallback changes.

## Definition of done

The architecture work is complete when this decision is accepted, stored in the
repository, and verified against the current evidence. The compatibility port is
complete only when:

- all 60 shared skills pass the Agent Skills validation policy or are explicitly
  classified as vendor-only and excluded with a reason;
- every package has a documented support state;
- every package has a current row in the checked-in compatibility matrix with
  client versions, commands, fixtures, expected differences, and evidence links;
- every package claimed for Codex passes its clean-install, discovery,
  activation, non-activation, resource, runtime, and no-Claude-environment gates;
- every install path claimed as compatible with another passes duplicate
  identity, precedence, update, uninstall, recovery, and drift tests;
- Claude marketplace validation, installation, behavior, and tests remain green;
- scripts and assets have one canonical copy;
- any native adapters have drift tests and synchronized package metadata;
- the public documentation distinguishes standards-based skills, tested Codex
  packages, and Claude-only components;
- no rename, repository split, directory move, or widened security boundary was
  introduced without a separate accepted decision.

## Superseded hypothesis

The July 21 handoff proposed testing dual Claude and Codex manifests first. The
research and clean-install evidence gathered afterward supersede that ordering.
The handoff remains useful as an inventory and research log, but this accepted
decision controls implementation: standards first, manifests only after a
measured trigger.

## References

- [Agent Skills specification](https://agentskills.io/specification)
- [Claude plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference)
- [Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [Codex plugins](https://learn.chatgpt.com/docs/build-plugins)
- [Codex import from another agent](https://learn.chatgpt.com/docs/import.md)
- [GitHub repository renames](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository)
- [skills.sh API identity](https://www.skills.sh/docs/api)
- [skills.sh rename report](https://github.com/vercel-labs/skills/issues/1651)
- [Codex marketplace precedence source](https://github.com/openai/codex/blob/c5eb33aed12d4977dc38403ecf8b42d89939ea32/codex-rs/core-plugins/src/marketplace.rs)
- [Codex plugin-manifest precedence source](https://github.com/openai/codex/blob/c5eb33aed12d4977dc38403ecf8b42d89939ea32/codex-rs/exec-server-protocol/src/protocol.rs)
