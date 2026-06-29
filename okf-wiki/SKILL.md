---
name: okf-wiki
description: Scaffold a new Open Knowledge Format (OKF) knowledge base and populate it from existing material: a tree of small markdown concept files with YAML frontmatter, a spec, a validator, and session-start hooks that orient Claude on the knowledge base before it works. Use when the user wants to start an OKF atlas/wiki/knowledge base, build one from existing docs, plans, notes, or a repo, structure docs as one-concept-per-file with provenance, or initialize OKF in a repo (optionally into its GitHub wiki).
license: MIT
metadata:
  author: jamditis
  version: "0.6.0"
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

## Start here: scope the wiki with the user

Before you scaffold anything, settle four things with the user. They shape what gets created and
how it is published, and they are awkward to retrofit once concepts exist. Ask with `AskUserQuestion`
rather than in prose, in two steps: the first three questions in one call, then the publish question
as a follow-up call only if the audience came back public or both (it does not apply to an
internal-only wiki, and its relevant options depend on that answer, so it cannot share the first
batch). Infer the title from the repo or project and confirm it. Skip any question the user already
answered in their request — do not re-ask what they have told you.

1. **Audience** — who reads this wiki? This answer sets the others:
   - **Internal (agents and teammates):** the orientation hooks earn their keep, so keep them on.
     The bundle may hold infrastructure detail, so it usually lives in a private repo. The in-repo
     `bundle/` is the source of truth.
   - **Public (people browsing):** readability and secret-scrubbing come first; the hooks matter
     less, since people read it and agents do not. Plan a published view (see Publish below).
   - **Both:** the in-repo `bundle/` is the source of truth with hooks on for agents, plus a
     published view for people. Default here when the user is unsure.
2. **Title and sections** — the knowledge-base title (infer it, then confirm) and the starting
   sections. Offer sections as a use-case preset, not a blank prompt:
   - Newsroom institutional memory: `people, orgs, sources, decisions, beats`
   - Research atlas: `concepts, sources, methods, findings`
   - Infrastructure or fleet map: `machines, services, networks, credentials, processes`
   - Decision log: `decisions, context, events`
   The chosen title and list feed `--title` and `--sections` below; the user can edit the list.
3. **Populate now or later** — author concepts now from existing material (a repo, docs, notes, or a
   URL: gather it and enter the authoring loop after scaffolding), or scaffold an empty tree the user
   fills in later.
4. **Publish target** — a follow-up `AskUserQuestion` call, made only after the audience comes back
   public or both (skip it entirely for an internal-only wiki):
   - **In-repo bundle only (default):** the validator and relative links work directly, with no
     extra surface to maintain. Right for most wikis.
   - **GitHub wiki:** an optional reading surface. Advanced and manual — see "Optional: publish into
     a GitHub wiki" below, bootstrapped with `scripts/gh-wiki-bootstrap.py`.
   - **GitHub Pages:** a browsable site rendered from the bundle. Not built yet — treat it as a
     goal and keep the in-repo bundle as the source of truth.

Carry the answers into the scaffold command (the title and sections, plus `--no-hooks` if the user
opts out of the hooks for a public-only wiki) and into the populate step. The audience answer is
also the visibility decision the "Before finishing" section asks you to make deliberately — you are
making it here, up front, where it can steer the rest of the setup.

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
    index.md              carries okf_version: "0.2"
    <section>/
      index.md
      example-concept.md  a starter concept with full frontmatter
```

Docs and tooling sit at the project root; only `bundle/` is validated. Keep them
separate — the validator treats every non-reserved `.md` inside the bundle as a
concept that needs frontmatter, so a stray `SPEC.md` inside `bundle/` would fail.
The `.claude/` hooks sit outside `bundle/`, so they never trip the concept checks.

## How to run it

`${CLAUDE_SKILL_DIR}` below is this skill's own directory (the folder holding this
`SKILL.md`). Claude Code substitutes it with the real absolute path before you run the
command, so it works regardless of the current directory. On Windows, use `python` instead
of `python3` (stock Windows has no `python3`). The `--title` and `--sections` come from the
onboarding answers above, and `--no-hooks` only if the user opted out. Scaffold into a new
directory; it validates automatically at the end:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/scaffold.py" ./my-knowledge-base \
  --title "Team knowledge base" \
  --sections concepts,services,decisions
```

Default section is `concepts`. Use `--force` to write into a non-empty directory,
`--no-validate` to skip the validation run, and `--date YYYY-MM-DD` to set the sample
frontmatter date. The session hooks are written by default; `--no-hooks` skips them and
`--hooks-os posix|windows` overrides the auto-detected launch command (see below).

Validate any time, from the scaffolded project root (use `python` on Windows):

```bash
python3 scripts/validate.py --bundle bundle    # must exit 0
```

## Populate the bundle: author concepts from existing material

Scaffolding leaves an empty tree with one placeholder concept. The usual next request
— "here are my docs / plans / notes / repo, build the wiki" — has no importer script, and
can't have one: deciding what counts as a single concept, writing its one-line description,
choosing its `type`, and pointing `source` at real provenance is judgment work, not a
mechanical transform. So you (Claude) author the concepts directly, in this loop:

1. **Gather the source.** Read what the user pointed you at — a file, a folder, a repo, or a
   URL (fetch a URL first). Skim the whole thing before writing anything, so you can see the
   natural concept boundaries.
2. **Decide concept boundaries.** One file is one concept: one thing a reader would look up on
   its own (a service, a decision, a path, a person, an event). Split a doc that covers five
   things into five concepts; merge fragments that only mean something together into one. A
   heading is a hint, not a rule — do not blindly map one `##` to one file.
3. **Draft each concept** at `bundle/<section>/<slug>.md` with the full frontmatter
   (`type, title, description, source, verified, timestamp, tags`):
   - `type` from the vocab. Infrastructure: Machine, Network, Service, Session, Project,
     Repo, Credential, Path, Process. Domain-neutral: Concept, Decision, Event, Person,
     Org, Source. Plus Reference (the catch-all). The set is closed; an unlisted type fails.
   - `description` is one line. `source` — quote every element — points at where the fact
     actually came from (the origin file path, URL, command, or event), not at this skill.
   - Set `timestamp` to today. `verified` is the date the fact was last confirmed true — set it by
     how you came to know it, not reflexively to today:
     - You re-checked it against reality now, or the user is the authority for it (a decision,
       preference, or intent they state in this session): today.
     - The user is recalling external or system state (a spec, a path, a config): their memory is a
       source claim, not a re-check, so date it to when that state was last checked or to the
       recollection's own date — not today just because it came up now.
     - It was copied from a dated source without re-checking: the date it was last known true (the
       source's own date), not today.
     - It came from an undated record you cannot re-confirm (a memory file, an old conversation):
       the oldest date you can evidence — file timestamp, introducing commit, or the date it was
       said — never today. If you cannot evidence any date at all, it is not yet a verifiable fact;
       find a datable source or leave the concept out.
     When the date is uncertain, round it down: an older `verified` correctly reads as "may be
     stale, re-check," while today reads as "just confirmed." The frontmatter date is the contract;
     a caveat in the body does not undo an overstated value, because the validator and tools read
     only the date.
   - Strip secret values as you go: a credential concept names the key and its retrieval path,
     never the value. The validator fails the build on a leaked secret.
4. **Place and link.** Put each concept in the right section (create sections as needed), add a
   bullet for it to that section's `index.md`, and cross-link related concepts with relative
   `[text](path.md)` links — not `[[slug]]` wikilinks. `[[slug]]` is the auto-memory idiom; the
   OKF validator rejects it and never resolves it, so a typo'd or deleted reference passes silently.
   When you create a new section, also link it from the bundle-root `index.md` — that root is the
   navigation map the session anchor loads, so a section missing from it is invisible to orientation
   even though validation still passes.
5. **Clear the placeholder.** If you scaffolded fresh, delete the starter `example-concept.md` (and
   its bullet in the section `index.md`) once real concepts exist — otherwise the sample ships in
   the finished wiki and still passes validation.
6. **Validate in a loop.** Run `python3 scripts/validate.py --bundle bundle`, fix what it
   reports, repeat until it exits 0. Unquoted `source` elements and missing frontmatter keys are
   the common failures. Author in batches and validate between them rather than writing fifty
   files and debugging the lot.

### When the source is already OKF

If the user points you at an existing OKF bundle (e.g. an upstream example: an `index.md`
carrying `okf_version` plus concept files with frontmatter), you are adopting it, not importing
it. Copy or clone the tree in, point the validator at the new root, and fix any links that broke
in the move. To keep it as its own area beside other content, give it a uniquely named top
directory, then create one combined-root `index.md` that carries `okf_version` and strip the
frontmatter from each adopted bundle's own root `index.md`, turning it into a normal section index
(the validator allows `okf_version` on the one combined root only; a nested `index.md` that still
carries it fails validation). Write cross-links as relative paths and validate the combined root.
Re-authoring an already-conforming bundle into your own concepts is wasted work; only reshape it if
that is the actual goal.

## The format, briefly

Full contract in `spec/SPEC.md`. The load-bearing rules:

- **Required frontmatter** on every concept: `type, title, description, source, verified,
  timestamp, tags`. `type` is one of: Machine, Network, Service, Session, Project, Repo,
  Credential, Path, Process (infrastructure); Concept, Decision, Event, Person, Org, Source
  (domain-neutral); or Reference (catch-all).
- **Quote every `source` element** — source pointers carry `#` and `: ` which break YAML
  if unquoted. `source: ["README.md", "issue #445"]`.
- **`verified`** is the date the fact was last confirmed true — a re-check against reality, or the
  user stating a fact they are the authority for (a decision, a preference); a fact they merely
  recall about external state is a source claim, not a re-check. **`timestamp`** is when the concept
  was authored/updated. Both ISO `YYYY-MM-DD`. See the authoring loop above for the full date rules.
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
GitHub wiki is an optional reading surface, and wiring it up is an advanced, manual step —
most users should skip it and keep the bundle in-repo.

A wiki with zero pages has no git repo to push to and no API, so the very first page must be
created through the web UI. `scripts/gh-wiki-bootstrap.py` automates that one step, but it
drives a real logged-in browser, so it needs two things you provide yourself (a GitHub PAT
does not work — wiki pages are a web-UI-only surface):

- **Playwright with Chromium installed:** `pip install playwright && playwright install chromium`.
- **A saved GitHub web session:** a Playwright `storageState` JSON, captured from a browser
  where you have already logged into GitHub. The script reuses that session; it does not log
  in for you. Pass its path with `--state` (default: `~/.cache/gh_state.json`).

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gh-wiki-bootstrap.py" owner/repo --state path/to/gh_state.json
# then: git clone https://github.com/owner/repo.wiki.git and push your pages
```

Note the impedance: GitHub wikis are flatter than an OKF tree and use `[[WikiLinks]]`, so
OKF's nested directories and relative links need adapting for the wiki surface. Treat the
wiki as a published view, not the source of truth. (v0.1 ships the bootstrap step; an
automatic bundle-to-wiki sync is not built yet.)

## Before finishing

- Run the validator and confirm it exits 0.
- Confirm the visibility you set during onboarding still fits what got authored: a bundle that
  ended up documenting real infrastructure is usually internal. OKF takes no position; you must.
