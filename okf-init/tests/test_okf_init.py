"""Tests for the okf-init skill: the scaffolder and the validator.

Each test runs the real CLI scripts in a temp directory, the same way a user
would. Run: python3 -m pytest okf-init/tests/ -q
"""
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCAFFOLD = SKILL / "scripts" / "scaffold.py"
VALIDATE = SKILL / "scripts" / "validate.py"

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
    assert 'okf_version: "0.1"' in root


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
    (b / "index.md").write_text('---\nokf_version: "0.2"\n---\n# root\n', encoding="utf-8")
    rc, out = validate(b)
    assert rc == 1 and "not supported" in out


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
