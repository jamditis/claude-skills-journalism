# Cross-client compatibility smoke check

Run the full fixture against one candidate tree:

```sh
SKILL_EVAL_RUN_ROOT="$HOME/.cache/skill-eval-runs" \
node scripts/skill-behavior-eval.mjs \
  --candidate-only \
  --candidate . \
  --fixtures scripts/fixtures/compat-smoke.json \
  --runtime both \
  --all \
  --max-cases 227 \
  --concurrency 3 \
  --output /tmp/compat-smoke-<date>
```

`--max-cases` must be at least the number of cases in the selection.
This fixture contains 76 skills and 227 prompt cases. Each case runs once in
each selected client. The report keeps fixture order even when client processes
run concurrently.

Each skill has up to three cases. They prove different things:

| Category | Prompt | A pass shows |
|---|---|---|
| `activation` | Names the skill (`/skill-evaluation:<skill>` in Claude Code, `$<skill>` in Codex) | The client accepts the named skill. The answer itself is not graded |
| `implicit-activation` | The same request without the skill name | The client accepts the skill when it is the only one installed |
| `unrelated-non-trigger` | An unrelated request | The client leaves the skill alone |

The default run installs one candidate skill and tells the client that a
single candidate is installed. That is easier than real use. A pass there
does not show that the client finds the skill among many.

## Competitive selection

Add `--competitive` to install every skill in the fixture set for each case
and to remove the single-candidate hint. The run skips named `activation`
cases, because naming a skill bypasses selection. The report records each
skill the client loaded in `runtimeEvidence.activatedSkills`.

A competitive `implicit-activation` pass shows that the client picked and
loaded the right skill from the full set. A competitive
`unrelated-non-trigger` pass shows that the client left the candidate alone;
another installed skill may still apply.

`director` has no implicit case. It is explicit-only by design and must not
activate unprompted.

Report the categories separately. A skill that passes only `activation` is
tested when invoked by name, not for automatic selection. Claim automatic
selection only from a competitive pass. A dry
run marks a missing skill as `missing-skill` and lists it in `missingSkills`
instead of stopping.

This result is activation evidence for the tested tree and client versions. It
is not a package-wide support claim and does not replace resource, runtime,
security-boundary, or clean-environment checks.

## Scoring

The fixture set uses `selection` scoring. A case passes on the decision, the
named skill, and, for implicit and unrelated cases, runtime activation
evidence. Branch wording and expected terms are reported as `advisory`; they
were not calibrated against real client output.

Two decision rules apply under selection scoring:

- When the fixture expects `use`, `ask` also passes if the response names the
  candidate skill. Picking the right skill and then asking for missing input
  is a correct selection.
- An unrelated case gates only on the candidate staying unused: the response
  must not name it, and the client must not load it. The decision word is
  advisory, because a neighboring skill or a request for input can be the
  right answer.

A pass shows that the client selected and loaded the skill. It does not grade
the answer itself.

## Run location

Set `SKILL_EVAL_RUN_ROOT` to a directory outside the system temporary
directory. Codex refuses to create its sandbox helpers under `/tmp`, so a run
home there blocks every shell read, including reading `SKILL.md`.

Optional `SKILL_EVAL_CLAUDE_MODEL` and `SKILL_EVAL_CODEX_MODEL` pin the models.
Record the client versions and models with any published result.
