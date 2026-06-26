"""Tests for the okf-wiki skill: the scaffolder and the validator.

Each test runs the real CLI scripts in a temp directory, the same way a user
would. Run: python3 -m pytest okf-wiki/tests/ -q
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
SCAFFOLD = SKILL / "scripts" / "scaffold.py"
VALIDATE = SKILL / "scripts" / "validate.py"
TEMPLATE_ANCHOR = SKILL / "templates" / "hooks" / "okf-anchor.py"
TEMPLATE_ORIENT = SKILL / "templates" / "hooks" / "okf-orient.py"

GOOD = """---
type: Process
title: good
description: a good concept
source: ["README.md"]
verified: 2026-06-23
timestamp: 2026-06-23
tags: ["x"]
---
# good
"""


def scaffold(target, *args):
    r = subprocess.run([sys.executable, str(SCAFFOLD), str(target), *args],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def validate(bundle, *args):
    r = subprocess.run([sys.executable, str(VALIDATE), "--bundle", str(bundle), *args],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def write_concept(bundle, text, name="concepts/c.md"):
    p = bundle / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def run_hook(script, project_dir, stdin=None, cwd=None, extra_env=None):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project_dir))
    if extra_env:
        env.update(extra_env)
    r = subprocess.run([sys.executable, str(script)], input=stdin,
                       capture_output=True, text=True, env=env, cwd=cwd)
    return r.returncode, r.stdout, r.stderr


def settings_of(target):
    return json.loads((target / ".claude" / "settings.json").read_text())


# --- scaffold ---------------------------------------------------------------

def test_default_scaffold_validates(tmp_path):
    rc, out = scaffold(tmp_path / "kb")
    assert rc == 0, out
    assert "PASS" in out
    assert (tmp_path / "kb" / "bundle" / "index.md").exists()
    assert (tmp_path / "kb" / "SPEC.md").exists()
    assert (tmp_path / "kb" / "scripts" / "validate.py").exists()


def test_multi_section_scaffold_validates(tmp_path):
    rc, out = scaffold(tmp_path / "kb", "--sections", "concepts,services,decisions")
    assert rc == 0, out
    for s in ("concepts", "services", "decisions"):
        assert (tmp_path / "kb" / "bundle" / s / "index.md").exists()


def test_root_index_carries_okf_version(tmp_path):
    scaffold(tmp_path / "kb")
    root = (tmp_path / "kb" / "bundle" / "index.md").read_text()
    assert 'okf_version: "0.2"' in root


def test_refuses_nonempty_dir_without_force(tmp_path):
    target = tmp_path / "kb"
    target.mkdir()
    (target / "keep.txt").write_text("x")
    rc, out = scaffold(target)
    assert rc == 1 and "not empty" in out


def test_force_writes_into_nonempty_dir(tmp_path):
    target = tmp_path / "kb"
    target.mkdir()
    (target / "keep.txt").write_text("x")
    rc, out = scaffold(target, "--force")
    assert rc == 0, out


def test_bad_date_arg_rejected(tmp_path):
    rc, out = scaffold(tmp_path / "kb", "--date", "2026-13-99")
    assert rc == 1 and "ISO" in out


def test_section_slugifying_to_empty_is_rejected(tmp_path):
    # a punctuation-only section name slugifies to "" and would otherwise write
    # its index over bundle/index.md, clobbering the root. Must be refused.
    rc, out = scaffold(tmp_path / "kb", "--sections", "..")
    assert rc == 1 and "no alphanumeric" in out
    assert not (tmp_path / "kb" / "bundle" / "index.md").exists()


def test_duplicate_sections_collapse(tmp_path):
    rc, out = scaffold(tmp_path / "kb", "--sections", "notes,notes")
    assert rc == 0, out
    assert (tmp_path / "kb" / "bundle" / "notes" / "index.md").exists()


def test_scaffold_writes_requirements(tmp_path):
    # the validator depends on PyYAML; the scaffolded project must declare it.
    rc, out = scaffold(tmp_path / "kb")
    assert rc == 0, out
    assert "PyYAML" in (tmp_path / "kb" / "requirements.txt").read_text()


def test_force_preserves_existing_content(tmp_path):
    # --force into a populated project must not clobber a user's own files with the
    # generic template. Scaffold once, edit content, re-scaffold --force: the edits
    # survive and the run reports what it preserved.
    target = tmp_path / "kb"
    scaffold(target)
    readme, root = target / "README.md", target / "bundle" / "index.md"
    readme.write_text("MY OWN README\n", encoding="utf-8")
    root.write_text("MY OWN INDEX\n", encoding="utf-8")
    rc, out = scaffold(target, "--force", "--no-validate")
    assert rc == 0, out
    assert readme.read_text() == "MY OWN README\n"
    assert root.read_text() == "MY OWN INDEX\n"
    assert "preserved" in out and "README.md" in out


def test_force_preserve_skips_validation(tmp_path):
    # when --force preserves a non-OKF bundle/index.md, the scaffold is no longer
    # valid by construction; it must skip validation, not fail as "a bug in
    # scaffold.py" over intentionally preserved user content.
    target = tmp_path / "kb"
    scaffold(target)
    (target / "bundle" / "index.md").write_text("# my repo index\n", encoding="utf-8")
    rc, out = scaffold(target, "--force")
    assert rc == 0, out
    assert "skipping validation" in out.lower()
    assert "bug in scaffold.py" not in out
    # the printed validate command must cd into the target, not the caller's cwd
    assert f"cd {target}" in out


def test_force_preserve_does_not_run_preserved_validator(tmp_path):
    # a preserved user scripts/validate.py must never be executed by the scaffolder.
    target = tmp_path / "kb"
    scaffold(target)
    sentinel = tmp_path / "ran"
    (target / "scripts" / "validate.py").write_text(
        f"import pathlib; pathlib.Path(r'{sentinel}').write_text('x')\n", encoding="utf-8")
    rc, out = scaffold(target, "--force")
    assert rc == 0, out
    assert not sentinel.exists(), "preserved validate.py must not be run"


def test_missing_pyyaml_skips_validation(tmp_path):
    # validate.py needs PyYAML; if it is absent the scaffold must still succeed and
    # say so plainly, not mislabel the missing dependency as a bug in scaffold.py.
    # Simulate absence with -S (no site-packages); skip if yaml is still findable.
    probe = subprocess.run(
        [sys.executable, "-S", "-c",
         "import importlib.util, sys; "
         "sys.exit(0 if importlib.util.find_spec('yaml') is None else 3)"])
    if probe.returncode != 0:
        pytest.skip("PyYAML is importable even under -S; cannot simulate its absence")
    target = tmp_path / "kb"
    r = subprocess.run([sys.executable, "-S", str(SCAFFOLD), str(target)],
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    assert r.returncode == 0, out
    assert "PyYAML is not installed" in out
    assert "bug in scaffold.py" not in out
    assert (target / "bundle" / "index.md").exists()
    # the printed validate command must cd into the target, not the caller's cwd
    assert f"cd {target}" in out


# --- validator (negative cases) ---------------------------------------------

def test_validator_passes_on_good_concept(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD)
    rc, out = validate(b)
    assert rc == 0, out


def test_missing_required_key_fails(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.replace('tags: ["x"]\n', ""))
    rc, out = validate(b)
    assert rc == 1 and "tags" in out


def test_bad_type_fails(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.replace("type: Process", "type: Wizard"))
    rc, out = validate(b)
    assert rc == 1 and "not in the spec vocab" in out


def test_domain_neutral_type_validates(tmp_path):
    # the vocab is a superset: domain-neutral types (newsroom/research/decision-log)
    # validate alongside the infrastructure types. Closed-set typo rejection is still
    # covered by test_bad_type_fails above.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    for t in ("Concept", "Decision", "Event", "Person", "Org", "Source"):
        write_concept(b, GOOD.replace("type: Process", f"type: {t}"), name=f"concepts/{t}.md")
    rc, out = validate(b)
    assert rc == 0, out


def test_invalid_date_shape_reports_cleanly(tmp_path):
    # date-shaped but invalid (month 13) — PyYAML raises ValueError during parse,
    # which is not a YAMLError. Must report cleanly, not crash with a traceback.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.replace("verified: 2026-06-23", "verified: 2026-13-99"))
    rc, out = validate(b)
    assert rc == 1 and "parse error" in out
    assert "Traceback" not in out


def test_source_must_be_list(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.replace('source: ["README.md"]', 'source: "README.md"'))
    rc, out = validate(b)
    assert rc == 1 and "must be a YAML list" in out


def test_secret_value_fails(tmp_path):
    # build an AWS-key-shaped string from fragments so no literal secret-shaped
    # token lives in this test file.
    fake = "AKIA" + "IOSFODNN7" + "EXAMPLE"
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + f"\nkey = {fake}\n")
    rc, out = validate(b)
    assert rc == 1 and "secret leak" in out


def test_dangling_link_fails(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\nSee [missing](nope.md).\n")
    rc, out = validate(b)
    assert rc == 1 and "dangling" in out


def test_bundle_path_not_a_directory_fails_cleanly(tmp_path):
    # pointing --bundle at a file (not a dir) must report a clean failure, not
    # crash with a NotADirectoryError traceback from rglob/iterdir.
    f = tmp_path / "notabundle.md"
    f.write_text(GOOD, encoding="utf-8")
    rc, out = validate(f)
    assert rc == 1 and "not a directory" in out
    assert "Traceback" not in out


def test_root_index_with_concept_frontmatter_fails(tmp_path):
    # the bundle-root index.md may carry only okf_version; arbitrary concept
    # metadata there must not slip through unchecked.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    (b / "index.md").write_text(
        '---\ntype: Credential\nnonsense: yes\n---\n# bad root\n', encoding="utf-8")
    rc, out = validate(b)
    assert rc == 1 and "only okf_version" in out


def test_root_index_missing_okf_version_fails(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    (b / "index.md").write_text("# no frontmatter here\n", encoding="utf-8")
    rc, out = validate(b)
    assert rc == 1 and "okf_version" in out


def test_root_index_unsupported_okf_version_fails(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    (b / "index.md").write_text('---\nokf_version: "0.9"\n---\n# root\n', encoding="utf-8")
    rc, out = validate(b)
    assert rc == 1 and "not supported" in out


def test_root_index_legacy_version_validates(tmp_path):
    # backward compat: a 0.1 bundle (e.g. the fleet atlas) still validates under the
    # newer validator, which accepts both 0.1 and the current format version.
    scaffold(tmp_path / "kb", "--no-validate")
    root = tmp_path / "kb" / "bundle" / "index.md"
    root.write_text(root.read_text().replace('okf_version: "0.2"', 'okf_version: "0.1"'),
                    encoding="utf-8")
    rc, out = validate(tmp_path / "kb" / "bundle")
    assert rc == 0, out


def build_federated_tree(root, members=("nodeA", "nodeB"), strip_member_markers=True):
    """Assemble a combined tree the way SPEC.md "Federation" describes: a new root
    index.md carrying okf_version, each member under its own subdirectory."""
    nav = "\n".join(f"- [{m}]({m}/index.md)" for m in members)
    (root).mkdir(parents=True, exist_ok=True)
    (root / "index.md").write_text(
        f'---\nokf_version: "0.1"\n---\n# Atlas\n\n{nav}\n', encoding="utf-8")
    for m in members:
        (root / m).mkdir(parents=True, exist_ok=True)
        marker = '---\nokf_version: "0.1"\n---\n' if not strip_member_markers else ""
        (root / m / "index.md").write_text(
            f"{marker}# {m}\n\n- [concept](concept.md)\n", encoding="utf-8")
        (root / m / "concept.md").write_text(GOOD, encoding="utf-8")


def test_federated_tree_validates(tmp_path):
    # the documented strip-and-merge procedure must actually pass: one root marker,
    # members nested as marker-less section indexes.
    root = tmp_path / "atlas"
    build_federated_tree(root)
    rc, out = validate(root)
    assert rc == 0, out


def test_nested_member_marker_fails(tmp_path):
    # the failure the SPEC warns about: leaving okf_version on a nested member index.
    root = tmp_path / "atlas"
    build_federated_tree(root, strip_member_markers=False)
    rc, out = validate(root)
    assert rc == 1
    assert "reserved file should not carry frontmatter" in out


def test_link_escaping_bundle_fails(tmp_path):
    # a link resolving above the bundle root is a hard failure even if such a file
    # exists on disk.
    (tmp_path / "outside.md").write_text("x", encoding="utf-8")
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\nSee [x](../../../outside.md).\n")
    rc, out = validate(b)
    assert rc == 1 and "escapes bundle root" in out


def test_link_with_title_resolves(tmp_path):
    # a CommonMark link with a title — [text](dest "title") — must not be flagged
    # dangling: the title is not part of the path.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + '\nSee [idx](index.md "the section index").\n')
    rc, out = validate(b)
    assert rc == 0, out


def test_root_relative_link_rejected(tmp_path):
    # a '/'-prefixed link is absolute, which the spec forbids; it must fail even
    # if bundle/index.md happens to exist.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\nSee [r](/index.md).\n")
    rc, out = validate(b)
    assert rc == 1 and "root-relative link not allowed" in out


def test_code_fence_link_examples_ignored(tmp_path):
    # a markdown link shown inside a fenced code block is illustrative, not a real
    # bundle link, and must not be reported as dangling.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\n\n```md\n[x](does-not-exist.md)\n```\n")
    rc, out = validate(b)
    assert rc == 0, out


def test_inline_code_link_example_ignored(tmp_path):
    # a link inside an inline code span is also an example, not a real link.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\n\nUse `[x](nope.md)` syntax.\n")
    rc, out = validate(b)
    assert rc == 0, out


def test_dangling_link_with_parens_caught(tmp_path):
    # a real (non-fenced) dangling link whose filename has balanced parens must
    # still be caught — the regex must not stop at the first ')'.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\nSee [x](missing(v2).md).\n")
    rc, out = validate(b)
    assert rc == 1 and "dangling" in out


def test_four_backtick_fence_wraps_triple(tmp_path):
    # a 4-backtick fence enclosing a 3-backtick example stays closed until a
    # >=4-backtick fence; the inner example link must not leak out as dangling.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\n\n````md\n```\n[x](nope.md)\n```\n````\n")
    rc, out = validate(b)
    assert rc == 0, out


def test_multi_backtick_inline_span_ignored(tmp_path):
    # a multi-backtick inline span (used when the code itself contains a backtick)
    # is still code, not a real link.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\n\nUse ``[x](nope.md)`` here.\n")
    rc, out = validate(b)
    assert rc == 0, out


def test_nonmapping_frontmatter_fails(tmp_path):
    # syntactically valid YAML that is a list (not a mapping) must fail cleanly,
    # not crash the validator with an AttributeError traceback.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, "---\n- a\n- b\n---\n# oops\n")
    rc, out = validate(b)
    assert rc == 1 and "must be a YAML mapping" in out
    assert "Traceback" not in out


def test_md_directory_fails_cleanly(tmp_path):
    # rglob("*.md") also matches a directory named like "archive.md"; reading it
    # would raise IsADirectoryError. The validator must report a clean failure, not
    # crash with a traceback (it is copied into every scaffolded project).
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    (b / "concepts" / "archive.md").mkdir(parents=True)
    rc, out = validate(b)
    assert rc == 1 and "must be a file, not a directory" in out
    assert "Traceback" not in out


def test_nonscalar_type_reports_cleanly(tmp_path):
    # type as a list/dict (a plausible YAML typo) is unhashable; counting it or
    # testing membership would crash. Must report cleanly, not traceback.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.replace("type: Process", "type: [Process]"))
    rc, out = validate(b)
    assert rc == 1 and "'type' must be a string" in out
    assert "Traceback" not in out


def test_missing_root_index_fails(tmp_path):
    # a bundle with concepts but no root index.md must fail: the okf_version gate
    # only runs when that file exists, so its absence would otherwise pass.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD)
    (b / "index.md").unlink()
    rc, out = validate(b)
    assert rc == 1 and "bundle-root index is required" in out


def test_bom_frontmatter_is_parsed(tmp_path):
    # a leading UTF-8 BOM (common from Windows editors) must not make valid
    # frontmatter read as missing; utf-8-sig strips it.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, "﻿" + GOOD)
    rc, out = validate(b)
    assert rc == 0, out


def test_github_pat_secret_detected(tmp_path):
    # build a fine-grained PAT shape from fragments so no real-looking token lives
    # in this test file. The classic gh*_ pattern misses github_pat_.
    fake = "github_pat_" + "11ABCDE" + "FGHIJKLMNOPQRSTUVWXYZ"
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + f"\ntoken = {fake}\n")
    rc, out = validate(b)
    assert rc == 1 and "secret leak" in out


def test_link_to_existing_uppercase_md_fails(tmp_path):
    # the case the prior case-sensitive design worried about: a link to an existing
    # Foo.MD used to "resolve" as valid while discovery never scanned that file. Now
    # discovery finds Target.MD and rejects it as non-conforming, so a bundle that
    # contains it fails -- the file check and the link check stay in agreement.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD, name="concepts/Target.MD")
    write_concept(b, GOOD.rstrip() + "\n\nSee [target](Target.MD).\n", name="concepts/c.md")
    rc, out = validate(b)
    assert rc == 1, out
    assert "Target.MD" in out


def test_uppercase_scheme_link_not_flagged(tmp_path):
    # an external link with an uppercase scheme must be recognized as external and
    # skipped, not resolved as a local path (which falsely fails as escaping).
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\nSee [s](HTTPS://example.com/readme.md).\n")
    rc, out = validate(b)
    assert rc == 0, out


def test_documented_credential_path_not_flagged(tmp_path):
    # OKF credential concepts document key NAMES/paths, not values; a hyphenated
    # path after a secret-ish label must not read as a high-entropy leaked value.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\nsecret: service/api/prod-client-secret-path\n")
    rc, out = validate(b)
    assert rc == 0, out


# --- session hooks: scaffold wiring -----------------------------------------

def test_default_scaffold_writes_hooks(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    c = tmp_path / "kb" / ".claude"
    assert (c / "settings.json").exists()
    assert (c / "hooks" / "okf-anchor.py").exists()
    assert (c / "hooks" / "okf-orient.py").exists()


def test_no_hooks_skips_claude_dir(tmp_path):
    rc, out = scaffold(tmp_path / "kb", "--no-validate", "--no-hooks")
    assert rc == 0, out
    assert not (tmp_path / "kb" / ".claude").exists()
    assert "skipped" in out


def test_scaffold_with_hooks_still_validates(tmp_path):
    # the .claude/ dir sits outside bundle/, so a default scaffold (hooks on)
    # must still validate clean.
    rc, out = scaffold(tmp_path / "kb")
    assert rc == 0 and "PASS" in out, out
    assert (tmp_path / "kb" / ".claude" / "settings.json").exists()


def test_settings_json_structure(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    s = settings_of(tmp_path / "kb")
    assert "SessionStart" in s["hooks"] and "PreToolUse" in s["hooks"]
    start = s["hooks"]["SessionStart"][0]["hooks"][0]
    pre_group = s["hooks"]["PreToolUse"][0]
    assert "matcher" not in pre_group  # no matcher => fires on the first tool call of any kind
    pre = pre_group["hooks"][0]
    # exec form: interpreter in `command`, script path as one `args` element (no shell
    # tokenization). The path must use the ${CLAUDE_PROJECT_DIR} placeholder, not a
    # bare cwd-relative path: the hook cwd is not guaranteed to be the project root.
    for hook, script in ((start, "okf-anchor.py"), (pre, "okf-orient.py")):
        assert hook["command"] in ("python3", "python"), hook
        assert hook["args"] == [f"${{CLAUDE_PROJECT_DIR}}/.claude/hooks/{script}"], hook


def test_hooks_os_windows_uses_python(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate", "--hooks-os", "windows")
    hook = settings_of(tmp_path / "kb")["hooks"]["SessionStart"][0]["hooks"][0]
    assert hook["command"] == "python"  # the py launcher, not python3


def test_hooks_os_posix_uses_python3(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate", "--hooks-os", "posix")
    hook = settings_of(tmp_path / "kb")["hooks"]["SessionStart"][0]["hooks"][0]
    assert hook["command"] == "python3"


def test_readme_validate_command_matches_os(tmp_path):
    # the generated README's validate command must use the same interpreter as the
    # hooks; stock Windows has no python3, so a windows scaffold must say python.
    scaffold(tmp_path / "win", "--no-validate", "--hooks-os", "windows")
    win = (tmp_path / "win" / "README.md").read_text()
    assert "python scripts/validate.py" in win and "python3 scripts/validate.py" not in win
    scaffold(tmp_path / "nix", "--no-validate", "--hooks-os", "posix")
    assert "python3 scripts/validate.py" in (tmp_path / "nix" / "README.md").read_text()


def test_force_merges_into_existing_settings(tmp_path):
    # scaffolding --force into a project that already has .claude/settings.json must
    # preserve the user's settings (permissions, unrelated events, their own
    # SessionStart hook) and add the OKF hooks, never overwrite the file wholesale.
    target = tmp_path / "kb"
    (target / ".claude").mkdir(parents=True)
    existing = {
        "permissions": {"allow": ["Bash(ls:*)"]},
        "hooks": {
            "SessionStart": [{"hooks": [{"type": "command", "command": "echo hi"}]}],
            "Stop": [{"hooks": [{"type": "command", "command": "echo bye"}]}],
        },
    }
    (target / ".claude" / "settings.json").write_text(json.dumps(existing), encoding="utf-8")
    (target / "keep.txt").write_text("x")
    rc, out = scaffold(target, "--force", "--no-validate")
    assert rc == 0, out
    s = settings_of(target)
    assert s["permissions"] == {"allow": ["Bash(ls:*)"]}  # untouched
    assert s["hooks"]["Stop"] == [{"hooks": [{"type": "command", "command": "echo bye"}]}]
    start_cmds = [h.get("command") for g in s["hooks"]["SessionStart"] for h in g["hooks"]]
    assert "echo hi" in start_cmds  # user's own hook preserved alongside ours
    anchors = [h for g in s["hooks"]["SessionStart"] for h in g["hooks"]
               if h.get("args") == ["${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-anchor.py"]]
    assert len(anchors) == 1
    assert "PreToolUse" in s["hooks"]


def test_force_merge_is_idempotent(tmp_path):
    # running the scaffold twice must not duplicate the OKF hook entries.
    target = tmp_path / "kb"
    scaffold(target, "--no-validate")
    scaffold(target, "--force", "--no-validate")
    s = settings_of(target)
    anchors = [h for g in s["hooks"]["SessionStart"] for h in g["hooks"]
               if h.get("args") == ["${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-anchor.py"]]
    orients = [h for g in s["hooks"]["PreToolUse"] for h in g["hooks"]
               if h.get("args") == ["${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-orient.py"]]
    assert len(anchors) == 1 and len(orients) == 1


def test_force_backs_up_unparseable_settings(tmp_path):
    # a settings.json that is not valid JSON must be backed up, not silently
    # discarded, before the OKF settings are written in its place.
    target = tmp_path / "kb"
    (target / ".claude").mkdir(parents=True)
    (target / ".claude" / "settings.json").write_text("not json{", encoding="utf-8")
    (target / "keep.txt").write_text("x")
    rc, out = scaffold(target, "--force", "--no-validate")
    assert rc == 0, out
    assert (target / ".claude" / "settings.json.bak").read_text() == "not json{"
    assert "backed up" in out
    assert "SessionStart" in settings_of(target)["hooks"]


def test_force_replaces_shellform_hook(tmp_path):
    # if an OKF hook is recorded in shell form (our exact path inside a `command`
    # string, e.g. hand-edited), --force must recognize it and replace it with the
    # exec-form entry, not leave both active. shlex-splitting the command exposes the
    # path token, which is then matched exactly against the paths we generate.
    target = tmp_path / "kb"
    (target / ".claude").mkdir(parents=True)
    legacy = {"hooks": {
        "SessionStart": [{"hooks": [{"type": "command",
            "command": 'python3 "${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-anchor.py"'}]}],
        "PreToolUse": [{"hooks": [{"type": "command",
            "command": 'python3 "${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-orient.py"'}]}],
    }}
    (target / ".claude" / "settings.json").write_text(json.dumps(legacy), encoding="utf-8")
    (target / "keep.txt").write_text("x")
    rc, out = scaffold(target, "--force", "--no-validate")
    assert rc == 0, out
    s = settings_of(target)
    anchors = [h for g in s["hooks"]["SessionStart"] for h in g["hooks"]
               if any("okf-anchor.py" in str(t) for t in [h.get("command")] + (h.get("args") or []))]
    assert len(anchors) == 1, s["hooks"]["SessionStart"]  # legacy entry replaced, not duplicated
    assert anchors[0]["args"] == ["${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-anchor.py"]  # exec form


def test_force_preserves_user_hook_sharing_okf_group(tmp_path):
    # a user may add their own hook into the same group as the OKF hook; replacing our
    # entry must strip only ours and keep theirs -- no whole-group drop (data loss).
    target = tmp_path / "kb"
    (target / ".claude").mkdir(parents=True)
    existing = {"hooks": {
        "SessionStart": [{"hooks": [
            {"type": "command", "command": "python3",
             "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-anchor.py"]},
            {"type": "command", "command": "echo mine"},
        ]}],
    }}
    (target / ".claude" / "settings.json").write_text(json.dumps(existing), encoding="utf-8")
    (target / "keep.txt").write_text("x")
    rc, out = scaffold(target, "--force", "--no-validate")
    assert rc == 0, out
    s = settings_of(target)
    cmds = [h.get("command") for g in s["hooks"]["SessionStart"] for h in g["hooks"]]
    assert "echo mine" in cmds  # the user's hook in the shared group survives
    anchors = [h for g in s["hooks"]["SessionStart"] for h in g["hooks"]
               if any("okf-anchor.py" in str(t) for t in [h.get("command")] + (h.get("args") or []))]
    assert len(anchors) == 1, s["hooks"]["SessionStart"]  # ours replaced once, not duplicated


def test_force_keeps_lookalike_user_hook(tmp_path):
    # a user hook whose path merely starts with our script name (a .bak/-wrapper
    # variant) is NOT ours; a whole-token match means --force must not strip it.
    target = tmp_path / "kb"
    (target / ".claude").mkdir(parents=True)
    lookalike = "${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-anchor.py.bak"
    existing = {"hooks": {
        "SessionStart": [{"hooks": [
            {"type": "command", "command": "python3", "args": [lookalike]},
        ]}],
    }}
    (target / ".claude" / "settings.json").write_text(json.dumps(existing), encoding="utf-8")
    (target / "keep.txt").write_text("x")
    rc, out = scaffold(target, "--force", "--no-validate")
    assert rc == 0, out
    s = settings_of(target)
    kept = [h for g in s["hooks"]["SessionStart"] for h in g["hooks"]
            if h.get("args") == [lookalike]]
    assert len(kept) == 1, s["hooks"]["SessionStart"]  # lookalike untouched, not stripped as ours


def test_force_keeps_same_named_hook_at_other_path(tmp_path):
    # a user hook that runs okf-anchor.py from a DIFFERENT location (a shared/global
    # hooks dir, not ${CLAUDE_PROJECT_DIR}) is not ours; exact-path matching means
    # --force must leave it in place.
    target = tmp_path / "kb"
    (target / ".claude").mkdir(parents=True)
    other = "/opt/shared/.claude/hooks/okf-anchor.py"
    existing = {"hooks": {
        "SessionStart": [{"hooks": [
            {"type": "command", "command": "python3", "args": [other]},
        ]}],
    }}
    (target / ".claude" / "settings.json").write_text(json.dumps(existing), encoding="utf-8")
    (target / "keep.txt").write_text("x")
    rc, out = scaffold(target, "--force", "--no-validate")
    assert rc == 0, out
    s = settings_of(target)
    kept = [h for g in s["hooks"]["SessionStart"] for h in g["hooks"]
            if h.get("args") == [other]]
    assert len(kept) == 1, s["hooks"]["SessionStart"]  # foreign-path hook left untouched


def test_force_backs_up_malformed_event_value(tmp_path):
    # a parseable settings.json whose event value is the wrong shape (not a list) must
    # be backed up rather than crashing the merge, preserving the original on disk.
    target = tmp_path / "kb"
    (target / ".claude").mkdir(parents=True)
    malformed = '{"hooks": {"SessionStart": 5}}'
    (target / ".claude" / "settings.json").write_text(malformed, encoding="utf-8")
    (target / "keep.txt").write_text("x")
    rc, out = scaffold(target, "--force", "--no-validate")
    assert rc == 0, out
    assert (target / ".claude" / "settings.json.bak").read_text() == malformed  # original preserved
    assert "backed up" in out
    s = settings_of(target)
    anchors = [h for g in s["hooks"]["SessionStart"] for h in g["hooks"]
               if h.get("args") == ["${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-anchor.py"]]
    assert len(anchors) == 1, s["hooks"]["SessionStart"]  # fresh hooks written after backup


def test_force_tolerates_malformed_hook_entry(tmp_path):
    # a list-shaped event holding a malformed hook entry (args not a list) must not
    # crash the merge; the odd entry is preserved (we can't claim it) and ours is added.
    target = tmp_path / "kb"
    (target / ".claude").mkdir(parents=True)
    existing = {"hooks": {
        "SessionStart": [{"hooks": [{"type": "command", "args": 5}]}],
    }}
    (target / ".claude" / "settings.json").write_text(json.dumps(existing), encoding="utf-8")
    (target / "keep.txt").write_text("x")
    rc, out = scaffold(target, "--force", "--no-validate")
    assert rc == 0, out
    s = settings_of(target)
    weird = [h for g in s["hooks"]["SessionStart"] for h in g["hooks"] if h.get("args") == 5]
    assert len(weird) == 1, s["hooks"]["SessionStart"]  # malformed entry left in place
    anchors = [h for g in s["hooks"]["SessionStart"] for h in g["hooks"]
               if h.get("args") == ["${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-anchor.py"]]
    assert len(anchors) == 1, s["hooks"]["SessionStart"]  # our hook still added


def test_force_preserves_unrelated_keys_when_hooks_malformed(tmp_path):
    # a parseable settings.json with unrelated live config (permissions) but a malformed
    # hooks subtree must keep the unrelated config in the LIVE file and just repair the
    # hooks; the original is copied to .bak. No whole-file reset, no lost permissions.
    target = tmp_path / "kb"
    (target / ".claude").mkdir(parents=True)
    existing = {"permissions": {"allow": ["Bash(ls)"]}, "hooks": {"SessionStart": 5}}
    (target / ".claude" / "settings.json").write_text(json.dumps(existing), encoding="utf-8")
    (target / "keep.txt").write_text("x")
    rc, out = scaffold(target, "--force", "--no-validate")
    assert rc == 0, out
    s = settings_of(target)
    assert s["permissions"] == {"allow": ["Bash(ls)"]}  # unrelated config kept in live file
    assert json.loads((target / ".claude" / "settings.json.bak").read_text()) == existing  # original saved
    anchors = [h for g in s["hooks"]["SessionStart"] for h in g["hooks"]
               if h.get("args") == ["${CLAUDE_PROJECT_DIR}/.claude/hooks/okf-anchor.py"]]
    assert len(anchors) == 1, s["hooks"]["SessionStart"]  # hooks repaired


# --- session hooks: behavior ------------------------------------------------

def test_anchor_injects_index_stripped(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    anchor = tmp_path / "kb" / ".claude" / "hooks" / "okf-anchor.py"
    rc, out, err = run_hook(anchor, tmp_path / "kb")
    assert rc == 0, err
    assert "begin OKF index" in out and "end OKF index" in out
    assert "okf_version" not in out  # frontmatter is stripped before injection


def test_anchor_no_bundle_is_silent(tmp_path):
    # the template script lives outside any bundle; pointed at an empty project it
    # finds no index and emits nothing.
    empty = tmp_path / "empty"
    empty.mkdir()
    rc, out, err = run_hook(TEMPLATE_ANCHOR, empty, cwd=empty)
    assert rc == 0 and out.strip() == ""


def test_orient_blocks_first_call_then_allows(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    orient = tmp_path / "kb" / ".claude" / "hooks" / "okf-orient.py"
    # isolate the marker dir to this test's scratch so it cannot collide with a
    # marker from another run (the hook stores state under the user's cache dir).
    env = {"OKF_ORIENT_STATE_DIR": str(tmp_path / "state")}
    payload = json.dumps({"session_id": "s1", "tool_name": "Read"})
    rc1, _, err1 = run_hook(orient, tmp_path / "kb", stdin=payload, extra_env=env)
    assert rc1 == 2 and "orientation" in err1.lower()
    rc2, _, err2 = run_hook(orient, tmp_path / "kb", stdin=payload, extra_env=env)
    assert rc2 == 0 and err2.strip() == ""


def test_orient_missing_session_id_skips_without_persisting(tmp_path):
    # a missing session_id must not be keyed to a constant marker (that would gate
    # once ever and skip every later session in the project). It should allow,
    # visibly, and write no marker.
    scaffold(tmp_path / "kb", "--no-validate")
    orient = tmp_path / "kb" / ".claude" / "hooks" / "okf-orient.py"
    state = tmp_path / "state"
    rc, out, err = run_hook(orient, tmp_path / "kb", stdin=json.dumps({"tool_name": "Read"}),
                            extra_env={"OKF_ORIENT_STATE_DIR": str(state)})
    assert rc == 0 and "no session_id" in err
    markers = list(state.glob("*.oriented")) if state.exists() else []
    assert markers == []  # nothing persisted, so a later session still gets gated


def test_anchor_failure_is_visible(tmp_path):
    # if the index cannot be read, the anchor stays fail-open but must say so on
    # stderr: the orient gate claims the index was injected, so a silent drop would
    # make that claim false and undiagnosable.
    scaffold(tmp_path / "kb", "--no-validate")
    anchor = tmp_path / "kb" / ".claude" / "hooks" / "okf-anchor.py"
    # invalid UTF-8 makes read_text(encoding="utf-8") raise, regardless of user/perms
    (tmp_path / "kb" / "bundle" / "index.md").write_bytes(b"\xff\xfe\x00\x00")
    rc, out, err = run_hook(anchor, tmp_path / "kb")
    assert rc == 0 and out.strip() == ""
    assert "could not inject the OKF index" in err


def test_orient_no_bundle_does_not_gate(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    payload = json.dumps({"session_id": "s1"})
    rc, out, err = run_hook(TEMPLATE_ORIENT, empty, stdin=payload, cwd=empty)
    assert rc == 0 and err.strip() == ""


def test_orient_marker_is_per_project(tmp_path):
    # a session id reused across two bundles must block in each: the marker is
    # keyed by (session, project), so one project's orientation cannot skip
    # another's gate.
    scaffold(tmp_path / "a", "--no-validate")
    scaffold(tmp_path / "b", "--no-validate")
    # one shared marker dir for both runs, so a block in each proves the marker key
    # differs by project (not just by state dir).
    env = {"OKF_ORIENT_STATE_DIR": str(tmp_path / "state")}
    payload = json.dumps({"session_id": "shared", "tool_name": "Bash"})
    rc_a, _, _ = run_hook(tmp_path / "a" / ".claude" / "hooks" / "okf-orient.py",
                          tmp_path / "a", stdin=payload, extra_env=env)
    rc_b, _, _ = run_hook(tmp_path / "b" / ".claude" / "hooks" / "okf-orient.py",
                          tmp_path / "b", stdin=payload, extra_env=env)
    assert rc_a == 2 and rc_b == 2


def _stray_hook(template, dest_dir):
    # copy a hook outside its <project>/.claude/hooks/ install dir so its __file__
    # base misses the bundle; the only resolution left is the cwd walk.
    dest_dir.mkdir(parents=True)
    dest = dest_dir / template.name
    dest.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def test_anchor_cwd_fallback_climbs_to_root_not_section(tmp_path):
    # with no CLAUDE_PROJECT_DIR and the hook run from outside its install dir, the
    # cwd fallback must climb from a section up to the bundle root, not bind to the
    # section's own index.md.
    scaffold(tmp_path / "kb", "--no-validate")
    bundle = tmp_path / "kb" / "bundle"
    section = bundle / "concepts"
    assert (section / "index.md").is_file()
    stray = _stray_hook(TEMPLATE_ANCHOR, tmp_path / "stray")
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    r = subprocess.run([sys.executable, str(stray)], input="", capture_output=True,
                       text=True, env=env, cwd=str(section))
    assert r.returncode == 0
    assert "## Sections" in r.stdout  # the root map, only present in bundle/index.md
    assert "Concepts in the concepts section." not in r.stdout  # not the section index


def test_orient_marker_keys_on_root_across_sections(tmp_path):
    # the per-session marker must key on the bundle root, so the same session acting
    # first from one section then another is not re-blocked by the gate.
    scaffold(tmp_path / "kb", "--no-validate")
    bundle = tmp_path / "kb" / "bundle"
    (bundle / "second").mkdir()
    (bundle / "second" / "index.md").write_text("# second\n", encoding="utf-8")
    stray = _stray_hook(TEMPLATE_ORIENT, tmp_path / "stray")
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    env["OKF_ORIENT_STATE_DIR"] = str(tmp_path / "state")
    payload = json.dumps({"session_id": "s1", "tool_name": "Read"})
    r1 = subprocess.run([sys.executable, str(stray)], input=payload, capture_output=True,
                        text=True, env=env, cwd=str(bundle / "concepts"))
    assert r1.returncode == 2  # first action of the session blocks once
    r2 = subprocess.run([sys.executable, str(stray)], input=payload, capture_output=True,
                        text=True, env=env, cwd=str(bundle / "second"))
    assert r2.returncode == 0  # different section, same session -> keyed on root, no re-block


def test_orient_malformed_stdin_fails_open(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    orient = tmp_path / "kb" / ".claude" / "hooks" / "okf-orient.py"
    rc, out, err = run_hook(orient, tmp_path / "kb", stdin="not json",
                            extra_env={"OKF_ORIENT_STATE_DIR": str(tmp_path / "state")})
    assert rc == 0  # never wedge a session on bad input
    assert "unexpected hook error" in err  # but surface it, never silently disable


def test_orient_unwritable_marker_fails_open_visibly(tmp_path):
    # if the marker cannot be persisted, blocking would re-fire on every retry and
    # wedge the session, so the gate allows -- but it must say so on stderr, never
    # silently. Force the failure by pointing the state dir under a path that is a
    # file, so creating the state dir raises.
    scaffold(tmp_path / "kb", "--no-validate")
    orient = tmp_path / "kb" / ".claude" / "hooks" / "okf-orient.py"
    blocker = tmp_path / "blocker"
    blocker.write_text("not a dir")  # state_dir mkdir(parents=True) will fail on this
    payload = json.dumps({"session_id": "s1", "tool_name": "Read"})
    rc, out, err = run_hook(orient, tmp_path / "kb", stdin=payload,
                            extra_env={"OKF_ORIENT_STATE_DIR": str(blocker / "state")})
    assert rc == 0  # allow rather than wedge the session
    assert "could not record orientation state" in err  # visible, not silent


# --- committed example ------------------------------------------------------

def test_committed_example_validates():
    # the example wiki of this repo lives in the tree and is linked from the docs
    # site; it must always validate clean so a stale example cannot be merged.
    example = SKILL / "example" / "bundle"
    assert example.is_dir(), "okf-wiki/example/bundle is missing"
    rc, out = validate(example)
    assert rc == 0, out


# --- authoring-error hints (#157, #158) -------------------------------------

def test_yaml_hint_names_colon_space(tmp_path):
    # #157: an unquoted colon-space in description is the common real trigger. The
    # parse-error hint must name it, not only the '#'-in-source case it used to.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.replace("description: a good concept",
                                  "description: Network analysis finding: send volume"))
    rc, out = validate(b)
    assert rc == 1
    assert "parse error" in out
    assert "colon-space" in out


def test_wikilink_fails(tmp_path):
    # #158: the [[slug]] idiom is the auto-memory convention, not OKF. An unresolved
    # [[ref]] used to pass the link check silently; it must now be reported.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\n\nSee [[activecampaign]] for the AC reference.\n")
    rc, out = validate(b)
    assert rc == 1
    assert "not an OKF link" in out
    assert "activecampaign" in out


def test_wikilink_in_code_fence_ignored(tmp_path):
    # a [[slug]] shown inside a fenced code block is illustrative, mirroring the
    # link checker's tolerance for fenced example links.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\n\n```md\nSee [[activecampaign]] (not an OKF link)\n```\n")
    rc, out = validate(b)
    assert rc == 0, out


# --- canonical/example sync (#162) ------------------------------------------

def test_example_spec_matches_canonical():
    # scaffold copies spec/SPEC.md into each bundle verbatim, and example/SPEC.md is a
    # committed copy. They must stay byte-identical, or the shipped example documents a
    # different contract than the validator enforces. Drift bit us twice (#149, #159).
    assert (SKILL / "example" / "SPEC.md").read_text(encoding="utf-8") == \
           (SKILL / "spec" / "SPEC.md").read_text(encoding="utf-8"), \
           "okf-wiki/example/SPEC.md drifted from spec/SPEC.md — re-sync the copy"


def test_example_validator_matches_canonical():
    # the example vendors scripts/validate.py; a drifted copy would validate the
    # committed example against stale rules.
    assert (SKILL / "example" / "scripts" / "validate.py").read_text(encoding="utf-8") == \
           (SKILL / "scripts" / "validate.py").read_text(encoding="utf-8"), \
           "okf-wiki/example/scripts/validate.py drifted from scripts/validate.py — re-sync the copy"


# --- source-quoting enforcement in block style (#155) -----------------------

def _concept_with_source(source_yaml):
    # a valid concept whose `source:` field is the given raw YAML (flow or block).
    return (
        "---\n"
        "type: Process\n"
        "title: good\n"
        "description: a good concept\n"
        f"{source_yaml}\n"
        "verified: 2026-06-23\n"
        "timestamp: 2026-06-23\n"
        'tags: ["x"]\n'
        "---\n# good\n"
    )


def test_source_block_unquoted_hash_fails(tmp_path):
    # the bug: block-style `- issue #445` parses to "issue" (YAML drops "#445" as a
    # comment) with no error, silently losing provenance. Must fail explicitly.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source('source:\n  - "README.md"\n  - issue #445'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "#" in out


def test_source_block_quoted_hash_passes(tmp_path):
    # quoting the element protects it — this is the documented fix, so it must pass.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source('source:\n  - "README.md"\n  - "issue #445"'))
    rc, out = validate(b)
    assert rc == 0, out


def test_source_block_hash_no_space_ok(tmp_path):
    # `issue#445` (no space before #) is NOT a YAML comment — it stays intact, so the
    # guard must not false-positive on it.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source("source:\n  - issue#445"))
    rc, out = validate(b)
    assert rc == 0, out


def test_source_flow_unquoted_hash_still_fails(tmp_path):
    # flow style was already enforced (the '#' comments out the closing ']' -> parse
    # error). Guard against regressing that while fixing block style.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source('source: ["README.md", issue #445]'))
    rc, out = validate(b)
    assert rc == 1, out


# --- source-quoting hardening: cloud-review edge cases from #166 -------------

def test_source_multiline_flow_unquoted_hash_fails(tmp_path):
    # a flow list can close on a later line, so the '#' does NOT comment out the ']' and
    # YAML parses cleanly while dropping "#445". The raw scan must still catch it.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source('source: ["README.md", issue #445\n  ]'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "#" in out


def test_source_wrapped_scalar_unquoted_hash_fails(tmp_path):
    # a block item that wraps onto a continuation line is one plain scalar; YAML strips a
    # '#' comment on the continuation too. The scan must inspect continuation lines.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source('source:\n  - issue\n    tracker #445'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "#" in out


def test_source_nested_key_not_flagged(tmp_path):
    # the scan must target only the top-level `source` provenance list. A nested
    # `source:` inside other (allowed) metadata is not the OKF source and must not make
    # a bundle with a valid top-level source fail.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source(
        'source: ["README.md"]\nextra:\n  source:\n    - issue #445'))
    rc, out = validate(b)
    assert rc == 0, out


def test_source_trailing_comment_after_complete_flow_ok(tmp_path):
    # a YAML comment after a COMPLETE value drops no data, so it must not be flagged:
    # `source: ["README.md"] # why` keeps ["README.md"].
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source('source: ["README.md"] # provenance'))
    rc, out = validate(b)
    assert rc == 0, out


def test_source_trailing_comment_after_quoted_block_item_ok(tmp_path):
    # likewise a comment after a quoted block item is benign (the element is complete).
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source('source:\n  - "README.md" # note'))
    rc, out = validate(b)
    assert rc == 0, out


def test_source_duplicate_key_later_unquoted_hash_fails(tmp_path):
    # YAML keeps the LAST of duplicate keys, so a valid first source followed by a later
    # source that drops "#445" must still fail — scan every top-level source occurrence.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source(
        'source: ["README.md"]\nsource:\n  - issue #445'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "#" in out


def test_source_unquoted_with_apostrophe_then_hash_fails(tmp_path):
    # a quote mid plain-scalar (the apostrophe in "Joe's") is literal YAML content, so
    # `- Joe's issue #445` is an unquoted scalar that still drops "#445" — the scan must
    # not mistake the apostrophe for the start of a quoted string and skip the comment.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source("source:\n  - Joe's issue #445"))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "#" in out


def test_source_block_item_with_comma_then_hash_fails(tmp_path):
    # a comma is a flow separator only inside `[...]`; in a block scalar it is literal
    # text, so `- report, #445` keeps "report," and still drops "#445". The scan must
    # not treat the comma as a completed value the way it does inside flow.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source("source:\n  - report, #445"))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "#" in out


def test_source_single_quoted_doubled_apostrophe_passes(tmp_path):
    # '' is YAML's escape for a literal apostrophe inside a single-quoted string, so
    # 'Joe''s issue #445' keeps "#445" inside the (valid, complete) string. The scan must
    # not close the string on the first quote of the pair and reject a correct pointer.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source("source: ['Joe''s issue #445']"))
    rc, out = validate(b)
    assert rc == 0, out


def test_source_multiline_quoted_scalar_passes(tmp_path):
    # a quoted scalar may wrap onto the next line; YAML folds it and keeps "#445" inside
    # the string. The scan must carry quote state across the line break, not treat the
    # continuation as plain text and reject it.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source('source: ["issue\n  tracker #445"]'))
    rc, out = validate(b)
    assert rc == 0, out


def test_source_indented_frontmatter_unquoted_hash_fails(tmp_path):
    # a consistently indented frontmatter mapping is valid YAML with top-level keys off
    # column 0. The scan must anchor to the frontmatter's base indent so it still finds
    # the real top-level `source` (and still drops its truncated provenance).
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, (
        "---\n"
        "  type: Process\n"
        "  title: t\n"
        "  description: d\n"
        "  source:\n"
        "    - issue #445\n"
        '  verified: "2026-06-23"\n'
        '  timestamp: "2026-06-23"\n'
        '  tags: ["x"]\n'
        "---\n# t\n"))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "#" in out


def test_source_comment_line_before_unquoted_item_fails(tmp_path):
    # a benign comment in the source value must not stop the scan: `source: # note` then
    # `- issue #445` still drops "#445" from the real (later) item.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source("source: # note\n  - issue #445"))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "#" in out


def test_source_flow_wrapped_at_base_indent_fails(tmp_path):
    # a flow list may wrap with no extra indentation; YAML still parses the continuation,
    # so `source: [` then a column-0 `"README.md", issue #445` still drops "#445".
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source('source: [\n"README.md", issue #445\n]'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "#" in out


def test_source_block_scalar_with_hash_passes(tmp_path):
    # a literal/folded block scalar keeps '#' as string content, not a comment, so a
    # source written that way is valid and must not be flagged.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source("source:\n  - |\n    issue #445"))
    rc, out = validate(b)
    assert rc == 0, out


def test_source_anchored_quoted_value_passes(tmp_path):
    # a YAML anchor/tag before a quoted value still protects the '#' inside the string;
    # the scan must not read the anchor as plain content and reject the quoted pointer.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source('source: [&p "issue #445"]'))
    rc, out = validate(b)
    assert rc == 0, out


# --- uppercase .md extension handling (#150 sub-item 2) ----------------------

def test_uppercase_md_file_rejected(tmp_path):
    # a Foo.MD file escaped the case-sensitive discovery (rglob("*.md")) entirely, so
    # its content was never validated. Discover it case-insensitively and reject the
    # non-conforming extension.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD, name="concepts/Foo.MD")
    rc, out = validate(b)
    assert rc == 1, out
    assert "Foo.MD" in out and ("extension" in out or "non-conforming" in out)


def test_mixedcase_md_file_rejected(tmp_path):
    # same rule for any non-lowercase extension, e.g. .Md
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD, name="concepts/Bar.Md")
    rc, out = validate(b)
    assert rc == 1, out
    assert "Bar.Md" in out


def test_dangling_uppercase_md_link_caught(tmp_path):
    # the link checker matched .md case-sensitively, so [x](ghost.MD) was skipped and a
    # dangling uppercase-extension link passed silently. It must now be caught.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\n\nSee [the ghost](ghost.MD).\n")
    rc, out = validate(b)
    assert rc == 1, out
    assert "ghost.MD" in out
