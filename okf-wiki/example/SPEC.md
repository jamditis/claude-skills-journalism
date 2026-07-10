# OKF spec v1

Open Knowledge Format (OKF) is a convention for storing knowledge as small markdown
files that both people and agents can read. One file describes one concept and carries
its own provenance. Directory `index.md` files provide navigation. A validator enforces
the contract so the knowledge base stays consistent as it grows.

This is the generic spec. A project may layer its own conventions on top (extra tags,
naming patterns, a fixed section list), but must not weaken the rules below.

## Relationship to upstream OKF

This spec is a strict fork of Google's Open Knowledge Format v0.1
([GoogleCloudPlatform/knowledge-catalog](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/ee67a5ca27044ebe7c38385f5b6cffc2305a9c1a/okf/SPEC.md)).
It keeps the core idea (knowledge as small markdown files with YAML frontmatter and
`index.md` navigation) and tightens the contract so a validator can enforce it. If you
already know upstream OKF, these are the intentional differences to author against;
upstream conventions will otherwise produce files this validator rejects.

- Required keys. Upstream requires only `type` and treats `title`, `description`,
  `resource`, `tags`, and `timestamp` as recommended, with any extra key allowed. Here all
  seven of `type`, `title`, `description`, `source`, `verified`, `timestamp`, and `tags`
  are required and non-empty, so a file that conforms upstream (say, `type` alone) fails
  validation here.
- `resource` becomes `source`. Upstream's optional `resource` is one canonical URI for the
  underlying asset. This spec drops `resource` and requires `source`, a non-empty list of
  provenance pointers (paths, commands, URLs, events).
- Citations fold into `source`. Upstream lists sources under a `# Citations` heading and
  allows a `references/` subdirectory. Here there is neither; all provenance lives in the
  `source` frontmatter list.
- `verified` is added. Upstream has no such key. This spec requires `verified`, the ISO
  date the fact was last confirmed true, kept distinct from `timestamp` (when the file was
  authored or edited).
- Dates are date-only. Upstream's `timestamp` is an ISO 8601 datetime. Here `check_dates`
  parses both `verified` and `timestamp` as `YYYY-MM-DD` only, so an upstream timestamp like
  `2026-05-28T14:30:00Z` fails validation and must be truncated to its date.
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

The format version differs too: upstream is `0.1`, this spec's current version is `0.2`
(the validator still accepts `0.1`). Every difference above pulls the same direction:
upstream stays minimal and needs no tooling to stay portable, while this spec adds a
validator that fails the build when a bundle drifts.

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

- The bundle-root `index.md` carries `okf_version: "0.2"` in frontmatter — only there.
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

The current format version is `0.2`. The validator accepts `0.1` and `0.2`, so a newer
validator still reads an older bundle, and new scaffolds emit `0.2`. Adding allowed types is
backward compatible and bumps the format version: a bundle using the newer types declares
`0.2`, so an older validator reports a clear unsupported-version error instead of a misleading
bad-type one.

## Concept frontmatter (required keys, all non-empty)

| key | value |
| --- | --- |
| `type` | one of the type vocab below |
| `title` | the concept name |
| `description` | one line |
| `source` | YAML list of provenance pointers (paths, commands, URLs, events) |
| `verified` | ISO date `YYYY-MM-DD` the fact was last confirmed true (see note below) |
| `timestamp` | ISO date authored/updated |
| `tags` | YAML list |

`verified` note: it records when the fact was last confirmed true, which is not always today. A
fact you re-checked against reality now is confirmed today, as is one the user is the authority for
— a decision, preference, or intent they state directly. But a fact the user is recalling about
external or system state is a source claim, not a re-check: date it to when that state was last
checked or to the recollection's own date, not today. A claim copied from a dated source without
re-checking carries that source's date. A fact taken from an undated record you cannot re-confirm (a
memory file, an old conversation) carries the oldest date you can evidence — file timestamp,
introducing commit, or the date it was said — never today; if no date can be evidenced, the fact is
not yet verifiable, so find a datable source or leave it out. When the date is uncertain, round it
down: an older `verified` reads as "may be stale," today reads as "just confirmed." The date is the
contract; a caveat in the concept body does not undo it, because the validator and tools read only
the date.

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

## Type vocab

Infrastructure and ops (fleet maps, system docs): `Machine`, `Network`, `Service`,
`Session`, `Project`, `Repo`, `Credential`, `Path`, `Process`.

Domain-neutral (newsrooms, research atlases, decision logs): `Concept`, `Decision`,
`Event`, `Person`, `Org`, `Source`.

`Reference` is the catch-all for a concept that is not one of the others. Index files carry
no frontmatter, so there is no `Index` type. The set is closed: an unlisted type fails the
build, which catches typos. To extend it, add the type here and in `scripts/validate.py`.

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
