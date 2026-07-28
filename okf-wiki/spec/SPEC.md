# OKF spec v1

Open Knowledge Format (OKF) is a convention for storing knowledge as small markdown
files that both people and agents can read. One file describes one concept and carries
its own provenance. Directory `index.md` files provide navigation. A validator enforces
the contract so the knowledge base stays consistent as it grows.

This is the generic spec. A project may layer its own conventions on top (extra tags,
naming patterns, a fixed section list), but must not weaken the rules below.

## A note on version numbers

Three separate numbers show up in this project, and none of them track each other:

1. **Upstream Google OKF's own spec version** — `0.1` (June 2026), then `0.2` (July 2026,
   adding the trust/provenance/attestation vocabulary this document adopts below). This is
   Google's number, not this fork's.
2. **This skill's package version** (the `version:` field in `SKILL.md`'s frontmatter) —
   its own release-numbering axis for the skill/plugin itself (bug fixes, secret-scanner
   hardening, Codex compatibility, and so on). It has no relationship to either spec version.
3. **This fork's own bundle-format version** (the `okf_version` marker every bundle-root
   `index.md` declares, and what `SUPPORTED_VERSIONS` in `validate.py` checks) — `0.1`, then
   `0.2` (new allowed types), then `0.3` (datetime-form `timestamp`), and now `0.4` (this
   patch: the v0.2 trust/provenance fields below, and the required-key rename they force).

So "OKF v0.2" (upstream Google's spec) and "`okf_version: 0.2`" (a bundle declared under
*this fork's* second format revision, from months before Google's v0.2 existed) are two
unrelated things that happen to share a digit. Where this document says "upstream v0.2" it
means Google's; a bare "`okf_version: 0.4`" always means this fork's own marker.

## Relationship to upstream OKF

This spec is a strict fork of Google's Open Knowledge Format
([GoogleCloudPlatform/knowledge-catalog](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)).
It keeps the core idea (knowledge as small markdown files with YAML frontmatter and
`index.md` navigation) and tightens the contract so a validator can enforce it. If you
already know upstream OKF, these are the intentional differences to author against;
upstream conventions will otherwise produce files this validator rejects.

- Required keys. Upstream requires only `type` and treats everything else as recommended,
  with any extra key allowed. Here, for a bundle declaring `okf_version` `0.1` through `0.3`,
  all seven of `type`, `title`, `description`, `source`, `verified`, `timestamp`, and `tags`
  are required and non-empty. For a bundle declaring `0.4`, `verified` is renamed to
  `verified_on` in that required list (see "Trust and provenance (upstream v0.2 vocabulary)"
  for why), so a `0.4` bundle requires `type`, `title`, `description`, `source`,
  `verified_on`, `timestamp`, and `tags` instead. Either way, a file that conforms upstream
  (say, `type` alone) fails validation here.
- `resource` becomes `source`. Upstream's optional `resource` is one canonical URI for the
  underlying asset. This spec drops `resource` and requires `source`, a non-empty list of
  provenance pointers (paths, commands, URLs, events). Upstream v0.2 separately introduces its
  own richer `sources` (plural) — this fork adopts that too, as an optional companion to the
  required `source`; see below.
- Citations fold into `source`. Upstream lists sources under a `# Citations` heading and
  allows a `references/` subdirectory. Here there is neither; all provenance lives in the
  `source` frontmatter list (and, optionally, the richer `sources` list below).
- `verified`/`verified_on` is added. Upstream v0.1 has no such key. Through `okf_version`
  `0.3`, this spec requires `verified`, the ISO date the fact was last confirmed true, kept
  distinct from `timestamp` (when the file was authored or edited). At `0.4`, this fork's own
  field is renamed `verified_on` to free the name `verified` for upstream v0.2's own
  `verified` — a different thing (see below).
- `timestamp`'s datetime form. Upstream's `timestamp` is an ISO 8601 datetime, and
  `check_dates` accepts that form for `timestamp` in a `0.3`-or-later bundle (with or without
  an offset, including a trailing `Z`), so an upstream bundle validates here unchanged. A
  `0.1`/`0.2` bundle's `timestamp` stays date-only. `verified`/`verified_on` is always
  date-only, in every version: it records the day a fact was last confirmed true, and a time
  of day there is false precision about the confirmation.
- The type vocab is closed. Upstream types are freeform and unregistered, and consumers
  must tolerate unknown ones. Here the set is fixed (see Type vocab) and an unlisted type
  fails the build, which catches typos; extending it is a deliberate spec edit.
- Links are strict, and must be relative. Upstream treats a broken link as tolerable
  ("consumers MUST tolerate broken links") and permits bundle-root-relative targets like
  `/tables/customers.md`. Here every intra-bundle link must resolve or validation fails, the
  `[[slug]]` wikilink form is rejected outright, and any target beginning with `/` is
  rejected as a root-relative link — so an upstream `/tables/customers.md` must be rewritten
  relative to the file that links it.
- A root `index.md` declaring `okf_version` is mandatory. Upstream treats `index.md` and
  `okf_version` as optional. Here the bundle root must contain an `index.md` whose
  frontmatter declares `okf_version` (and carries nothing else), so an upstream bundle with
  no root index, or one that omits the version marker, fails validation.
- Secret values fail the build. Upstream OKF has no secret-scanning rule. Here `validate.py`
  scans every markdown file for private-key blocks, cloud-token shapes, and `secret=<value>`
  assignments and fails the bundle on a hit, so an upstream bundle that inlines a credential
  value passes upstream but is rejected here (see Security).
- Trust/provenance/attestation fields are adopted, not required. Upstream v0.2 adds
  `generated`, `sources`, `status`, `stale_after`, `verified` (the new, upstream shape), and
  an `Attested Computation` type — all of it optional there, and all of it optional here too.
  Adopting none of it leaves a bundle exactly as valid as before; see the dedicated section
  below.

This fork's own format version differs from upstream's on a separate axis (see "A note on
version numbers" above): upstream is now `0.1`/`0.2`, this fork's current bundle-format
version is `0.4` (the validator still accepts `0.1`, `0.2`, and `0.3`). Every difference
above pulls the same direction: upstream stays minimal and needs no tooling to stay
portable, while this fork adds a validator that fails the build when a bundle drifts.

## Bundle model

A bundle is a directory tree. The simplest bundle is one directory of concept files
with an `index.md`. Larger bundles group concepts into subdirectories by subject.

```
<bundle-root>/
  index.md                 carries okf_version, here and nowhere else
  <section>/
    index.md               navigation for the section
    <concept>.md           one concept per file
```

## Files

- The bundle-root `index.md` carries `okf_version` (one of `"0.1"`–`"0.4"`; `scaffold.py`
  still writes `"0.3"` by default, `"0.4"` only with `--trust-signals`) in frontmatter —
  only there.
- Per-directory `index.md`: a heading, an optional one-line preamble, then bullet
  navigation. No frontmatter. (Keep the preamble to one line — it orients, it doesn't narrate.)
- `log.md` (optional, per directory): dated entries, newest first, no frontmatter.
- Concept files: one concept each, frontmatter required (below).
- Reserved filenames: `index.md`, `log.md`.
- All markdown files use a lowercase `.md` extension. A non-lowercase extension (`.MD`,
  `.Md`) is non-conforming and rejected — the validator discovers files case-insensitively
  so such a file cannot escape validation, and link checks match `.md` case-insensitively too.

The validator enforces the frontmatter rules here — reserved files carry no frontmatter, and
only the bundle-root `index.md` carries `okf_version` (and nothing else). The index/log body
shapes above are recommendations for human readers, not validator-checked structure.

The current format version is `0.4`, but `scaffold.py` still emits `0.3` by default —
unchanged from before this patch — and only writes `0.4` when explicitly asked
(`scaffold.py --trust-signals`; see Tooling). The validator accepts `0.1` through `0.4`
either way, so a newer validator still reads an older bundle. Version `0.2` added allowed
types. Version `0.3` admitted a full datetime in `timestamp`. Version `0.4` renames
`verified` to `verified_on` (freeing `verified` for the new upstream-v0.2 shape) and adds the
optional trust/provenance fields below — a bundle that adopts none of them still only needs to
declare `0.4` because of the rename; one that keeps declaring `0.1`–`0.3` keeps the old
`verified` field exactly as before and simply cannot use the new optional fields (see next
section). The marker makes these grammar changes explicit, so an older validator reports a
clear unsupported-version error instead of a misleading field error.

## Concept frontmatter (required keys, all non-empty)

For a bundle declaring `okf_version` `0.1` through `0.3`:

| key | value |
| --- | --- |
| `type` | one of the type vocab below |
| `title` | the concept name |
| `description` | one line |
| `source` | YAML list of provenance pointers (paths, commands, URLs, events) |
| `verified` | ISO date `YYYY-MM-DD` the fact was last confirmed true (see note below) |
| `timestamp` | ISO date authored/updated, or in a `0.3` bundle a full ISO 8601 datetime |
| `tags` | YAML list |

For a bundle declaring `okf_version` `0.4`, the table is identical except `verified` is
named `verified_on` (same required-ness, same meaning, same date-only rule — only the key
name changes, to make room for the new `verified` described below).

`verified`/`verified_on` note: it records when the fact was last confirmed true, which is not
always today. A fact you re-checked against reality now is confirmed today, as is one the user
is the authority for — a decision, preference, or intent they state directly. But a fact the
user is recalling about external or system state is a source claim, not a re-check: date it to
when that state was last checked or to the recollection's own date, not today. A claim copied
from a dated source without re-checking carries that source's date. A fact taken from an
undated record you cannot re-confirm (a memory file, an old conversation) carries the oldest
date you can evidence — file timestamp, introducing commit, or the date it was said — never
today; if no date can be evidenced, the fact is not yet verifiable, so find a datable source or
leave it out. When the date is uncertain, round it down: an older `verified`/`verified_on`
reads as "may be stale," today reads as "just confirmed." The date is the contract; a caveat in
the concept body does not undo it, because the validator and tools read only the date.

`timestamp` may be an ISO date (`YYYY-MM-DD`) in every supported format version. A `0.3` or
`0.4` bundle may instead preserve a full datetime in the exact form
`YYYY-MM-DDTHH:MM:SS[.fraction][Z|+HH:MM|-HH:MM]`; a space may replace `T`. Versions `0.1`
and `0.2` remain date-only. `verified`/`verified_on` is always date-only.

`source` quoting rule (hard): QUOTE every element of the `source` list. Source pointers
routinely carry YAML-significant characters — a `#` (e.g. `"issue #445"`) starts a comment
and corrupts the flow sequence, a colon-space `: ` splits a mapping — so a strict parser
rejects an unquoted source. Always quote them:

```yaml
source: ["README.md", "issue #445", "git log 9c2e510"]
```

The validator enforces this in both list styles. In flow style (`["a", b]`) an unquoted
element carrying a significant character fails to parse and is reported as an error. In block
style (`- a`) YAML would silently drop an inline `#` comment and pass, so the validator also
scans the raw source text and rejects an unquoted element with a `#`. An element that is
already quote-safe (a bare filename) is accepted either way — quote everything anyway so you
never have to judge which is which.

`tags` and `description` follow a lighter rule: quote an element only when it contains a
YAML-significant character (a colon-space `: `, a leading `[ { # * & ! | > % @` or quote,
or a trailing `:`); plain kebab tokens like `canonical` may stay unquoted. Quoting when
unsure is always safe. Hard quoting is `source` only.

Provenance lives in `source` — there is no separate citations section or references directory.

## Trust and provenance (upstream v0.2 vocabulary)

Upstream Google OKF v0.2 (July 2026) added a second kind of frontmatter field: not one that
describes a concept, but one a consumer uses to decide whether to trust it before reading the
body. This fork adopts that vocabulary as optional additions, available on any concept
regardless of type, in a bundle declaring `okf_version` `0.4`. None of it is required. A
concept that uses none of these fields is exactly as valid as one authored against `0.1`.

As with upstream, this fork records the raw signals and leaves scoring to the consumer — there
is no computed trust score anywhere in a concept file or in the validator's output. A tool that
wants "only surface human-reviewed metrics" derives that filter itself from the fields below.

- **`generated`** — an optional mapping `{by, at}`: who or what produced the current content,
  and when it last meaningfully changed. `by` is a non-empty string identifying the producer
  (a model/agent name, or `human:<id>`); `at` is an ISO date or full ISO 8601 datetime. This
  sits alongside the required `timestamp`, not in place of it — `timestamp` is this fork's own
  authored/updated marker and stays required; `generated` is the richer, optional upstream
  form for describing production, and the two may describe the same event.
- **`verified`** (only meaningful in a `0.4` bundle, where it is not the required key — see
  above) — an optional YAML list of independent confirmations, each a mapping
  `{by, at}`: `by` a non-empty string (a `human:<id>` actor or a machine/agent identifier), `at`
  an ISO date. A consumer derives a trust tier from this list: no `verified` key is
  *unverified*; every entry from a machine/agent actor only is *machine-confirmed*; any entry
  from a `human:<id>` actor is *human-reviewed*. The validator checks only that the list is
  well-formed (non-empty entries, valid dates) — deriving and filtering on a tier is a
  consumer's job, not this format's.
- **`sources`** (plural, distinct from the required singular `source`) — an optional YAML list
  of structured provenance objects, each with a required `id` (non-empty string, unique within
  the list — used to key an in-body footnote like `[^warehouse-schema]`) and `resource`
  (non-empty string: a URL or bundle-relative path), plus optional `title`, `author`
  (non-empty strings), `usage_count` (a non-negative integer), and `last_modified` (an ISO
  date). Where the required `source` is a flat list of quoted pointers, `sources` lets each
  pointer carry its own credibility signals and be cited per-claim in the body via an ordinary
  markdown footnote. The validator checks shape only — it does not cross-check that every
  `[^id]` footnote in the body has a matching `sources[].id`, or vice versa; treat that
  cross-reference as a human/reviewer responsibility for now.
- **`status`** — an optional string, one of `draft`, `stable`, `deprecated`. Absent means
  `stable`. A `deprecated` concept is kept for history/reproducibility but should not be
  surfaced to new work.
- **`stale_after`** — an optional ISO date `YYYY-MM-DD`. An absolute date, deliberately, not a
  relative TTL: staleness is then a plain date comparison with no reference to when the
  concept happened to be read.

None of the above changes what the validator requires; it only makes the *absence* of these
fields distinguishable from their presence where they matter to a consumer deciding whether to
act on a concept. Absence means the signal was not supplied. A trust field that is explicitly
present with a YAML null value is invalid; present fields must have the shape documented above.

## Type vocab

Infrastructure and ops (fleet maps, system docs): `Machine`, `Network`, `Service`,
`Session`, `Project`, `Repo`, `Credential`, `Path`, `Process`.

Domain-neutral (newsrooms, research atlases, decision logs): `Concept`, `Decision`,
`Event`, `Person`, `Org`, `Source`.

`Reference` is the catch-all for a concept that is not one of the others. Index files carry
no frontmatter, so there is no `Index` type. The set is closed: an unlisted type fails the
build, which catches typos. To extend it, add the type here and in `scripts/validate.py`.
`Attested Computation` joins this closed vocabulary only in a bundle declaring
`okf_version` `0.4`; versions `0.1` through `0.3` reject it.

### `Attested Computation` (upstream v0.2)

A concept of this type carries a sanctioned way to compute a value, and the means to check
that the sanctioned computation actually ran — the answer to "was this number produced the way
we said it must be," distinct from `verified` above (which confirms a *definition* still
matches policy, not that any one run produced a correct value). It carries these keys in
addition to the seven (or, at `0.4`, six-plus-`verified_on`) base required keys:

| key | value |
| --- | --- |
| `runtime` | non-empty string naming the execution environment (e.g. `bigquery`) |
| `parameters` | YAML list (possibly empty) of mappings, each `{name, type, required}` — the declared inputs a caller may fill; nothing else |
| `executor` | mapping `{resource, receipt}` — `resource` points at the skill/tool that runs the computation, `receipt` a list naming what it returns (e.g. `[job_id, executed_sql, result]`) |
| `attester` | mapping `{resource}` — points at the deterministic, non-LLM checker that compares a receipt against this concept's sanctioned computation |

OKF records the computation and how to check it; this fork's validator checks only that these
four keys are present and correctly shaped when `type: Attested Computation`. It never runs
the computation, the executor, or the attester itself — that is a consumer's runtime
responsibility, entirely outside this format and this validator.

## Links

Relative markdown links. Every link to a file inside the bundle must resolve to a file that
exists; a link that escapes the bundle root or dangles fails validation. The bundle is
validated as one self-contained tree (see Federation for combining several).

The `[[slug]]` wikilink form is not an OKF link, and the validator rejects it. It is the
auto-memory cross-reference idiom and easy to reach for by habit, but a `[[slug]]` is never
resolved or checked, so a dead reference would pass silently. Always link with
`[text](relative/path.md)`.

## Federation (optional)

Several bundles can be combined into one tree. Add a new root `index.md` that carries
`okf_version` and links to each member, then place each bundle under a uniquely named
subdirectory of that root. A member's own `index.md` is now a nested section index, so remove
its `okf_version` frontmatter block entirely — a nested `index.md` carries no frontmatter at
all. Write cross-bundle links as relative paths into the sibling directories. Validate by
pointing the validator at the new root, so every link resolves and the single `okf_version`
gate runs once at the top.

A member's marker is stripped when it is nested, so it can no longer be validated on its own
from inside the combined tree — validate the assembled root instead. (Per-node validation that
keeps a marker in each member is planned but not yet built.) Most single-repo knowledge bases
never need any of this.

## Security (hard)

- No secret VALUES anywhere. A credential concept documents the key name, where it lives, and
  how it is retrieved — never the value itself.
- The validator scans for private-key blocks, cloud-token shapes, and `secret=<value>`
  assignments and fails the build on a hit. If a pattern false-positives on legitimate text,
  narrow the pattern; do not delete the rule.
- OKF makes no claim about whether your bundle is public or private. That is your decision —
  but a bundle that documents real infrastructure is usually internal. Decide deliberately
  before publishing.

## Tooling

- `validate.py` — frontmatter conformance, date/list checks, link resolution, secret scan.
  Run it before every commit; it must exit 0.
- `scaffold.py` — generate a conforming starter bundle.
