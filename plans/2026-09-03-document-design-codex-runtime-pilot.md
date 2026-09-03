# Document-design Codex runtime pilot

- Status: scoped Codex project-standards pass with a skill-relative resource adapter
- Evidence date: Sept. 3, 2026
- Tracking issue: [#241](https://github.com/jamditis/claude-skills-journalism/issues/241)
- Pre-adapter source: [`902cc881b5f9c8a18053d1f60dcc456851db3ee4`](https://github.com/jamditis/claude-skills-journalism/commit/902cc881b5f9c8a18053d1f60dcc456851db3ee4)

## Scope

This pilot tested `document-design` 1.3.6 with Codex CLI 0.153.0 and skills
CLI 1.5.23. The accepted route copies the skill into a disposable project's
`.agents/skills/document-design` directory. Codex used an isolated
`CODEX_HOME`, linked existing account authentication without copying its
contents, ignored user configuration and rules, and kept each session
ephemeral. No Claude environment variable was present.

The pass covers project-standards installation, explicit activation,
unrelated non-trigger behavior, installed templates, brands, controls and CSS
reference reads, one disposable HTML output, render dimensions, failure
behavior, Claude argument delivery, and cleanup. It does not cover the Codex
user-level or legacy-package routes. The eight Claude commands and the
SessionStart hook remain outside the Codex claim.

## Failing public baseline

The public repository was first installed into an empty disposable project:

```bash
npx --yes skills@latest add jamditis/claude-skills-journalism \
  --skill document-design --agent codex --copy -y
```

The installer found 64 repository skills but copied only three files for
`document-design`: `SKILL.md`, `agents/openai.yaml`, and
`references/css-patterns.md`. The explicit `$document-design` probe selected
the skill and found the instructions and CSS reference. It correctly refused
to write `dd-preflight.html` because these required installed paths were
missing:

- `templates/onepager-template.html`;
- `brands/default.yaml`; and
- `controls/control-panel.css`.

The intended output path remained absent. This is the recorded failure mode
that justified the adapter.

## Resource adapter and drift guard

The adapter keeps package-root resources for existing Claude commands and
also carries exact regular-file copies below the standards-installed skill.
`SKILL.md` now resolves `templates/`, `brands/`, `controls/`, and
`references/css-patterns.md` relative to its own installed directory instead
of assuming `CLAUDE_PLUGIN_ROOT`. It checks the runtime-neutral project-root
`pdf-playground.local.md` first and retains `.claude/pdf-playground.local.md`
as a lower-priority compatibility path for existing Claude projects.

The candidate installed 18 regular files with no symlinks. Its sorted
relative-path and content manifest matched the source skill with SHA-256:

```text
fff8a1ce4bbfa0f973a7c5f67a4892196556b0b9c8f98bbb32e16299e0beeceb
```

`scripts/document-design-portability.test.mjs` compares every duplicated
brand, control, and template byte for byte, rejects symlinks, requires the CSS
reference, rejects `CLAUDE_PLUGIN_ROOT` in the shared skill, and pins the
public support boundary.

## Codex runtime result

The candidate package was copied through the same skills CLI project route.
The explicit fixture required Codex to read the installed `SKILL.md`, CSS
reference, one-pager template, default brand, and control-panel stylesheet.
The trace showed all five reads and created `dd-1.html` at the requested path.

The 8,042-byte output had SHA-256 digest:

```text
bdcf5016e151a2c92f1610f08414f76bd887cca0047d34f746dfb7fa09cf13e1
```

It contained an English HTML document, letter-size print CSS, structural
`auto 1fr auto` footer clearance, and the required phrases “Corrections desk,”
“Report an error,” “Review the evidence,” “Publish the correction,” and
“Audit trail.” It loaded no external asset or runtime script.

Chromium rendered the page at 816 by 1,056 pixels with matching client and
scroll dimensions, no horizontal or vertical overflow, and no console or page
error. The footer ended at the page boundary. A visual screenshot check found
the footer clear of the body and all requested sections legible.

The unrelated 18% tip fixture returned `$7.56` and `$49.56`. It read no skill
and ran no command.

A focused follow-up placed `pdf-playground.local.md` in a fresh disposable
project with the organization name `Pine Street News` and primary color
`#146B55`. Codex read that runtime-neutral config before the installed
one-pager template and created `brand-proof.html` with both values. The
7,689-byte output used no external asset or runtime script and had SHA-256:

```text
1a644113b00ee65344aefc0e4aed0af8f6d0b0ef14bb24204c0794e863172299
```

A visual screenshot check found the custom green brand treatment, all body
content, the sidebar, and the footer clear and legible on one letter-size page.

## Claude regression

Claude Code 2.1.239 loaded the candidate with `--plugin-dir`, no built-in
tools, no session persistence, and an isolated configuration directory. The
explicit `/document-design` invocation received its marker and returned:

```text
CSJ_DOCUMENT_ARGUMENT_241: the arguments arrived.
```

The client reported a successful one-turn result in 1.614 seconds. The test
did not invoke a Claude command, hook, or external tool.

## Cleanup

Both disposable projects, the generated HTML, screenshot, isolated client
homes, and authentication symlinks were removed after verification. No
credential content was copied into the repository or a test root.

## Supported boundary

The approved Codex claim is the copied project-standards
`$document-design` skill with its self-contained relative resources and HTML
generation behavior. User-level installation, the legacy-compatible package
route, all eight `/pdf-playground:*` commands, interactive preview lifecycle,
and the SessionStart hook require separate tests before inclusion.
