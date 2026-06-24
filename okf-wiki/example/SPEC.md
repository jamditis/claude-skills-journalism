# OKF spec v1

Open Knowledge Format (OKF) is a convention for storing knowledge as small markdown
files that both people and agents can read. One file describes one concept and carries
its own provenance. Directory `index.md` files provide navigation. A validator enforces
the contract so the knowledge base stays consistent as it grows.

This is the generic spec. A project may layer its own conventions on top (extra tags,
naming patterns, a fixed section list), but must not weaken the rules below.

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

- The bundle-root `index.md` carries `okf_version: "0.1"` in frontmatter — only there.
- Per-directory `index.md`: a heading, an optional one-line preamble, then bullet
  navigation. No frontmatter. (Keep the preamble to one line — it orients, it doesn't narrate.)
- `log.md` (optional, per directory): dated entries, newest first, no frontmatter.
- Concept files: one concept each, frontmatter required (below).
- Reserved filenames: `index.md`, `log.md`.

The validator enforces the frontmatter rules here — reserved files carry no frontmatter, and
only the bundle-root `index.md` carries `okf_version` (and nothing else). The index/log body
shapes above are recommendations for human readers, not validator-checked structure.

## Concept frontmatter (required keys, all non-empty)

| key | value |
| --- | --- |
| `type` | one of the type vocab below |
| `title` | the concept name |
| `description` | one line |
| `source` | YAML list of provenance pointers (paths, commands, URLs, events) |
| `verified` | ISO date `YYYY-MM-DD` the concept was last checked against reality |
| `timestamp` | ISO date authored/updated |
| `tags` | YAML list |

`source` quoting rule (hard): QUOTE every element of the `source` list. Source pointers
routinely carry YAML-significant characters — a `#` (e.g. `"issue #445"`) starts a comment
and corrupts the flow sequence, a colon-space `: ` splits a mapping — so a strict parser
rejects an unquoted source. Always quote them:

```yaml
source: ["README.md", "issue #445", "git log 9c2e510"]
```

The validator enforces this through the YAML parse step: an unquoted element carrying a
significant character fails to parse and is reported as an error. An element that is already
quote-safe (a bare filename) parses fine and is accepted — quote everything anyway so you
never have to judge which is which.

`tags` and `description` follow a lighter rule: quote an element only when it contains a
YAML-significant character (a colon-space `: `, a leading `[ { # * & ! | > % @` or quote,
or a trailing `:`); plain kebab tokens like `canonical` may stay unquoted. Quoting when
unsure is always safe. Hard quoting is `source` only.

Provenance lives in `source` — there is no separate citations section or references directory.

## Type vocab

`Machine`, `Network`, `Service`, `Session`, `Project`, `Repo`, `Credential`, `Path`,
`Process`, `Reference`.

`Reference` is the catch-all for a concept that is not one of the others. Index files carry
no frontmatter, so there is no `Index` type.

## Links

Relative markdown links. Every link to a file inside the bundle must resolve to a file that
exists; a link that escapes the bundle root or dangles fails validation. The bundle is
validated as one self-contained tree (see Federation for combining several).

## Federation (optional)

Several bundles can be combined into one tree by giving each a uniquely named top-level
directory and concatenating them, with cross-bundle links written as relative paths into the
sibling directories. Validate the combined result as a single bundle: assemble the tree, then
point the validator at that root so every link resolves. Most single-repo knowledge bases
never need this.

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
