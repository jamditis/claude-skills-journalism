# Security-toolkit Codex project-copy preflight

Tracking issue: [#234](https://github.com/jamditis/claude-skills-journalism/issues/234).

## Result and scope

The four shared skills remain candidates. This run observed intended selection
in four explicit fixtures and two implicit fixtures, plus an unrelated request
that selected no skill. It did **not** pass the installed-resource or security
runtime gates: every security response reported a Bubblewrap startup failure
when trying to read files. A separate local copy probe found a real packaging
gap in `supply-chain-hardening`.

No hotpatch mapping was created. Its command, sandbox lifecycle, cooldown bypass,
install, failure handling, and cleanup remain Claude-only pending a separately
accepted design. This is not a security-content review or a package support
claim.

## Environment and evidence

- Tested source: `9e8e419a916f1f26c57ebe71acc9152c95b5117d` on September 4, 2026.
- Codex CLI 0.153.2 on Linux; configured model `gpt-6-astra`, effort `high`.
  These are local configuration values, not an independently verified serving
  model identity.
- Manual recursive copies of all four `security-toolkit/skills/<name>`
  directories into a disposable project's `.agents/skills/<name>`; no skills
  installer, plugin adapter, command wrapper, or symlink was used.
- Existing user configuration, authentication, skill catalog, and host guidance
  remained in scope. No `HOME` or `CODEX_HOME` override was used. This was not a
  clean-profile or no-Claude-environment test.
- Each invocation used `--ephemeral --sandbox read-only
  --skip-git-repo-check`, with a 150-second process limit. All seven exited 0.

The [sanitized evidence](evidence/security-toolkit-codex-preflight-2026-09-04.json)
contains the exact prompts, shared boundary, invocation shape, source/copy
SHA-256 values, final responses, and observed event types. Only the disposable
root path was replaced with `<RUN_ROOT>` in responses. The CLI JSONL exposed
agent messages and turn completion, not command-level tool traces. Therefore
the reported sandbox failures and non-execution statements are not independent
proof of security enforcement.

The route follows [OpenAI's skill discovery and activation documentation](https://learn.chatgpt.com/docs/build-skills):
project `.agents/skills` directories, explicit `$skill` selection, and implicit
description matching. That documentation establishes the route, not these
skills' correctness.

## Fixture observations

| Fixture | Reported selection | Limit |
|---|---|---|
| Explicit `$api-hardening` | `api-hardening`; identified research-first preflight | Reported reading supplied skill text, not the installed file |
| Explicit `$secure-auth` | `secure-auth`; identified research-first preflight | Same filesystem limit; generated WebAuthn assets were not verified |
| Explicit `$security-checklist` | `security-checklist`; identified research-first preflight and separate issue-creation authority | Same filesystem limit; sibling resource read unverified |
| Explicit `$supply-chain-hardening` | `supply-chain-hardening`; identified version preflight and proposed script path | Same filesystem limit; resource existence unknown to the fixture |
| Implicit public API planning | `api-hardening` | Catalog selection only; full instructions unread |
| Implicit npm supply-chain planning | `supply-chain-hardening` | Catalog selection only; scan resources unread |
| Unrelated autumn poem | None | No security skill selection; host-guidance read also reported blocked |

The repeated reported error was
`bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`.
The sandbox was not disabled to obtain a passing result. Exit 0 means the
fixture returned a response, not that its requested filesystem reads succeeded.

## Installed-resource gap

The standalone supply-chain skill contains only `SKILL.md` and
`agents/openai.yaml`. Its instructions name `scripts/hotpatch.example.sh` and
claim a shipped synthetic fixture. Both assets exist at the **package** root:

- `security-toolkit/scripts/hotpatch.example.sh`
- `security-toolkit/test-fixtures/fake-mini-shai.tgz`

Neither is copied by installing only the directory that contains this skill's
`SKILL.md`. The local probe confirmed both source assets exist and both expected
skill-local destinations are absent. All eight installed files still matched
their source bytes after the runtime fixtures. The Claude command was not
copied into the project.

This is a copy-layout result, separate from the nested runtime's failed reads.
It does not establish behavior for a whole-package install or symlink route.
An asset-transport or instruction change must be evaluated separately; copying
the hotpatch command into Codex is not the fix.

## Authority boundaries and remaining work

The prompts allowed routing and local inspection only, not applying security
recipes. They explicitly withheld research, package/lifecycle execution,
credential access, mutations, external issue creation, subagent dispatch, and
hotpatch. Model-service authentication and transport still used the existing
Codex profile; this was not a network-isolation test.

The three application-security skills prescribe current research before
recipes. `security-checklist` also prescribes filing audit findings as issues;
that instruction is not independent permission to write externally. The
supply-chain quick-start prescribes upgrades, configuration writes, copying,
and script execution; none was authorized by the fixture. Responses stayed at
preflight and reported no such execution, but the absent tool traces leave
enforcement unproved.

Next, resolve the standalone resource layout, then rerun on a host where the
read-only sandbox can initialize. Capture command-level traces and verify
filesystem, shell, network, credential, and external-write boundaries there.
Add clean-profile and no-Claude-environment coverage, remaining implicit and
non-trigger cases, and drift tests for any approved adapter. Keep #234 open.

## Reproduction

Use a checkout pinned to the tested source revision. Create a disposable
project and recursively copy each of the four skill directories into
`<project>/.agents/skills/`; copy the directories themselves, not the whole
package. Compare the source and copied `SKILL.md` hashes with the evidence.
Check the two package-level asset paths above and their corresponding
skill-local destinations without executing either asset.

For each case in the evidence JSON, append `sharedBoundary` to `prompt`, then
run the recorded invocation with a fresh output filename and a 150-second
timeout. Keep the configured sandbox in place. Inspect selection, full-file
read evidence, exit status, and tool traces separately; never score an exit-0
response as a passed filesystem or authority gate.

For example, after preparing the project, set the two input paths below and
run the first explicit case. Preserve stdout and stderr as well as the final
answer: `-o` alone does not retain event evidence.

```bash
project_dir=/absolute/path/to/prepared/project
evidence_file=/absolute/path/to/security-toolkit-codex-preflight-2026-09-04.json
result_dir=$(mktemp -d)
fixture_prompt=$(node -e '
  const fs = require("node:fs");
  const evidence = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
  process.stdout.write(evidence.cases[0].prompt + "\n\n" + evidence.sharedBoundary);
' "$evidence_file")
if timeout --foreground 150 codex exec --ephemeral --sandbox read-only \
  --skip-git-repo-check -C "$project_dir" --json \
  -o "$result_dir/answer.txt" "$fixture_prompt" \
  > "$result_dir/events.jsonl" 2> "$result_dir/stderr.txt"; then
  fixture_status=0
else
  fixture_status=$?
fi
printf '%s\n' "$fixture_status" > "$result_dir/exit-status.txt"
```
