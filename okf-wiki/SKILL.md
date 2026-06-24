---
name: okf-wiki
description: Scaffold a new Open Knowledge Format (OKF) knowledge base: a tree of small markdown concept files with YAML frontmatter, a spec, a validator, and session-start hooks that orient Claude on the knowledge base before it works. Use when the user wants to start an OKF atlas/wiki/knowledge base, structure docs as one-concept-per-file with provenance, or initialize OKF in a repo (optionally into its GitHub wiki).
license: MIT
metadata:
  author: jamditis
  version: "0.2.0"
  okf_spec: v1
---

# okf-wiki: scaffold an Open Knowledge Format knowledge base

OKF (Open Knowledge Format) stores knowledge as small markdown files: one concept per
file, each carrying its own provenance in YAML frontmatter, with directory `index.md`
files for navigation and a validator that enforces the contract. It is built for
knowledge bases that both people and agents read and edit — newsroom institutional
memory, a research atlas, a team's decision log, an infrastructure map.

This skill scaffolds a conforming OKF project and validates it. The format contract is
in `spec/SPEC.md` (in this skill's directory) — read it before changing structure.

## When to use

- The user wants to start an OKF knowledge base, atlas, or wiki.
- They want docs structured as one-concept-per-file with provenance, not prose pages.
- They want to "initialize OKF" in a repo, optionally publishing into its GitHub wiki.

## What gets created

`scripts/scaffold.py` writes a project that passes its own validator by construction:

```
<target>/
  SPEC.md                 the OKF format contract
  README.md               how to use and validate the bundle
  scripts/validate.py     the validator
  .claude/                session hooks that orient Claude on the bundle
    settings.json         registers the hooks (Claude Code approves them once)
    hooks/okf-anchor.py   SessionStart: load the index into context
    hooks/okf-orient.py   PreToolUse: gate the first action on orientation
  bundle/                 the OKF bundle (the validated tree)
    index.md              carries okf_version: "0.1"
    <section>/
      index.md
      example-concept.md  a starter concept with full frontmatter
```

Docs and tooling sit at the project root; only `bundle/` is validated. Keep them
separate — the validator treats every non-reserved `.md` inside the bundle as a
concept that needs frontmatter, so a stray `SPEC.md` inside `bundle/` would fail.
The `.claude/` hooks sit outside `bundle/`, so they never trip the concept checks.

## How to run it

`SKILL_DIR` below is this skill's own directory (the folder holding this `SKILL.md`).
Scaffold into a new directory; it validates automatically at the end:

```bash
python3 "$SKILL_DIR/scripts/scaffold.py" ./my-knowledge-base \
  --title "Team knowledge base" \
  --sections concepts,services,decisions
```

Default section is `concepts`. Use `--force` to write into a non-empty directory,
`--no-validate` to skip the validation run, and `--date YYYY-MM-DD` to set the sample
frontmatter date. The session hooks are written by default; `--no-hooks` skips them and
`--hooks-os posix|windows` overrides the auto-detected launch command (see below).

Validate any time, from the scaffolded project root:

```bash
python3 scripts/validate.py --bundle bundle    # must exit 0
```

## The format, briefly

Full contract in `spec/SPEC.md`. The load-bearing rules:

- **Required frontmatter** on every concept: `type, title, description, source, verified,
  timestamp, tags`. `type` is one of: Machine, Network, Service, Session, Project, Repo,
  Credential, Path, Process, Reference.
- **Quote every `source` element** — source pointers carry `#` and `: ` which break YAML
  if unquoted. `source: ["README.md", "issue #445"]`.
- **`verified`** is the date the fact was last checked against reality; **`timestamp`** is
  when the concept was authored/updated. Both ISO `YYYY-MM-DD`.
- **No secret values, ever.** A credential concept documents the key name and retrieval
  path, never the value. The validator fails the build on a leaked secret.
- **`index.md` and `log.md` are reserved** — no frontmatter (except the bundle-root
  `index.md`, which carries `okf_version` only).

## Session hooks

A scaffolded project ships a `.claude/` with two hooks so any Claude session opened in it
starts from the bundle, not from memory:

- **`okf-anchor.py`** (SessionStart) prints the bundle's root index into the session context.
- **`okf-orient.py`** (PreToolUse, no matcher) blocks the first action of the session once,
  until Claude confirms it read the index, then unblocks for the rest of the session. It is
  inert outside an OKF bundle and fails open on any error, so it never wedges a session.

Both are one cross-platform python3 script. The scripts are identical on every OS; only the
interpreter in `.claude/settings.json` changes: `python3` on macOS/Linux, `python` on
Windows. `scaffold.py` auto-detects the OS; `--hooks-os posix|windows` forces it.

Claude Code treats a checked-in `.claude/settings.json` as untrusted, so the first time the
project is opened it asks the user to approve the hooks; they run automatically after that.
To turn them off, scaffold with `--no-hooks`, or delete `.claude/` (or set `disableAllHooks`)
in an existing project.

## Optional: publish into a GitHub wiki

OKF lives best as in-repo files (the validator and relative links work directly). A repo's
GitHub wiki is an optional reading surface. A wiki with zero pages has no git repo to push
to and no API, so the first page must be created via the web UI; `scripts/gh-wiki-bootstrap.py`
does that using a saved GitHub web session (a Playwright `storageState` you supply):

```bash
python3 "$SKILL_DIR/scripts/gh-wiki-bootstrap.py" owner/repo --state path/to/gh_state.json
# then: git clone https://github.com/owner/repo.wiki.git and push your pages
```

Note the impedance: GitHub wikis are flatter than an OKF tree and use `[[WikiLinks]]`, so
OKF's nested directories and relative links need adapting for the wiki surface. Treat the
wiki as a published view, not the source of truth. (v0.1 ships the bootstrap step; an
automatic bundle-to-wiki sync is not built yet.)

## Before finishing

- Run the validator and confirm it exits 0.
- Decide visibility deliberately: a bundle documenting real infrastructure is usually
  internal. OKF takes no position; you must.
