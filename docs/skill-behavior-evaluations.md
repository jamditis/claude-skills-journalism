# Skill behavior evaluations

The behavior evaluation compares a baseline skill with a changed skill.

The fixture set covers these behavior classes for each pilot skill:

- Activation.
- Near-neighbor rejection.
- Branch selection.
- Safety invariants.
- Incomplete inputs.
- Authority boundaries.
- Output artifacts.

The first pilot covers `zero-build-frontend`, `source-verification`, and `data-journalism`.

## Safety and isolation

The runner copies one selected skill into a new temporary directory for each session.

Claude runs with `claude -p`, no tools, no session persistence, and only project or local settings enabled.

Codex runs with `codex exec`, an ephemeral session, a read-only sandbox, and ignored user configuration.

Each client uses its normal authentication home.

The runner does not copy OAuth files because a copied refresh token can rotate and invalidate the normal session.

The runner removes each temporary directory after the session finishes.

The runner does not call a model API.

Each session has a three-minute timeout and a two-megabyte output limit.

The runner redacts common token and credential patterns from error text.

The result file has mode `0600`.

Do not put confidential information in fixture prompts.

## Run one case

Use separate repository trees for the baseline and candidate.

```bash
npm run eval:skills -- \
  --baseline /path/to/baseline \
  --candidate /path/to/candidate \
  --case sv-activation \
  --runtime both \
  --output /path/to/private-results
```

Use `--dry-run` to inspect the command plan without starting model sessions.

Set `SKILL_EVAL_CLAUDE_MODEL` or `SKILL_EVAL_CODEX_MODEL` to pin a model.

The report records the CLI versions, fixture digest, skill digest, model response, and deterministic score.

## Run the full fixture set

The full set starts 84 sessions.

This count comes from 21 cases, two clients, and two variants.

The runner requires an explicit case limit for this costly operation.

```bash
npm run eval:skills -- \
  --baseline /path/to/baseline \
  --candidate /path/to/candidate \
  --all \
  --max-cases 21 \
  --runtime both \
  --output /path/to/private-results
```

Exit status `0` means every response passed its fixed rubric.

Exit status `2` means at least one response failed its rubric.

Exit status `1` means the runner or a client failed.

## Interpret results

Compare paired baseline and candidate results for each case and client.

A changed skill must keep safety and authority results at 100 percent.

Review failed terms before you change a skill.

A model response is evidence for review.

It is not proof that the skill is correct.
