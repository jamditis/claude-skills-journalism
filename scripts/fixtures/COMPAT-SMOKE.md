# Cross-client compatibility smoke check

Run the full fixture against one candidate tree:

```sh
node scripts/skill-behavior-eval.mjs \
  --candidate-only \
  --candidate . \
  --fixtures scripts/fixtures/compat-smoke.json \
  --runtime both \
  --all \
  --max-cases 100 \
  --concurrency 3 \
  --output /tmp/compat-smoke-<date>
```

Candidate-only mode applies `--max-cases` to the number of distinct skills.
This fixture contains 76 skills and 227 prompt cases. Each case runs once in
each selected client. The report keeps fixture order even when client processes
run concurrently.

Each skill has up to three cases. They prove different things:

| Category | Prompt | A pass shows |
|---|---|---|
| `activation` | Names the skill (`/skill-evaluation:<skill>` in Claude Code, `$<skill>` in Codex) | The skill loads and gives a correct answer when a user asks for it by name |
| `implicit-activation` | The same request without the skill name | The client selects the skill on its own from an ordinary request |
| `unrelated-non-trigger` | An unrelated request | The client leaves the skill alone |

`director` has no implicit case. It is explicit-only by design and must not
activate unprompted.

Report the categories separately. A skill that passes only `activation` is
tested when invoked by name, not for automatic selection. A dry
run marks a missing skill as `missing-skill` and lists it in `missingSkills`
instead of stopping.

This result is activation evidence for the tested tree and client versions. It
is not a package-wide support claim and does not replace resource, runtime,
security-boundary, or clean-environment checks.
