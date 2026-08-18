---
type: Process
title: "tests and CI"
description: "pytest covers the okf-wiki scaffolder and validator; three GitHub Actions workflows gate pull requests."
source: ["okf-wiki/tests/test_okf_wiki.py", ".github/workflows/okf-wiki-tests.yml", ".github/workflows/skill-lint.yml", ".github/workflows/security-toolkit-hotpatch-selftest.yml"]
verified: 2026-06-26
timestamp: 2026-06-26
tags: [tests, ci]
---
# tests and CI

`okf-wiki/tests/test_okf_wiki.py` exercises the scaffolder and the validator as a
user would, running the real CLI scripts in temp directories. One test validates
this committed example bundle, so a stale or broken wiki cannot merge. Run it with
`python3 -m pytest okf-wiki/tests/ -q`.

Three GitHub Actions workflows gate pull requests by path:

- `okf-wiki-tests.yml`, runs the pytest suite when anything under `okf-wiki/**`
  changes (so edits to this bundle are validated in CI, via
  [the OKF format](okf-format.md) validator).
- `skill-lint.yml`, lints `*/SKILL.md` and `hooks/*.md` frontmatter and structure.
- `security-toolkit-hotpatch-selftest.yml`, self-tests the supply-chain hotpatch
  scanner against synthetic malicious fixtures.

The repository also follows a test-first bug-fixing rule documented in `CLAUDE.md`:
reproduce a bug with a failing test before fixing it.
