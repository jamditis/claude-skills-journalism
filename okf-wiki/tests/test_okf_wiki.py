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

# Import the scaffolder module to unit-test its pure helpers directly. The CLI tests
# below drive scaffold.py as a subprocess; the requirements name-sniffing contract is
# fine-grained enough to pin here without a subprocess round-trip.
sys.path.insert(0, str(SKILL / "scripts"))
import scaffold as scaffold_mod  # noqa: E402  the module under test; the local scaffold() helper below shadows the bare name

# Load gh-wiki-bootstrap.py by path (its hyphenated name is not importable) so its
# pure save-detection helper can be unit-tested without a browser. Its playwright
# import lives inside main(), so importing the module top-level touches only stdlib.
import importlib.util  # noqa: E402
_boot_spec = importlib.util.spec_from_file_location(
    "gh_wiki_bootstrap", SKILL / "scripts" / "gh-wiki-bootstrap.py")
gh_wiki_bootstrap = importlib.util.module_from_spec(_boot_spec)
_boot_spec.loader.exec_module(gh_wiki_bootstrap)

# The scaffolder evaluates a PEP 508 environment marker on a preserved requirements.txt's
# PyYAML line only when `packaging` is importable; without it, it falls back to treating the
# line as installable. Tests that assert an EXCLUDING marker warns therefore need packaging
# present, so they guard on this. A matching or absent marker holds either way (the fallback
# also selects the env), so those need no guard.
HAS_PACKAGING = importlib.util.find_spec("packaging") is not None

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
    assert 'okf_version: "0.3"' in root


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


def test_force_preserve_warns_when_requirements_lacks_pyyaml(tmp_path):
    # A preserved requirements.txt is the user's own and stays untouched (#142). When it
    # omits PyYAML, the skip-validation message must name the exact missing dependency so
    # the user is not left to decode a later ModuleNotFoundError from validate.py.
    target = tmp_path / "kb"
    scaffold(target)
    (target / "requirements.txt").write_text("requests>=2\n", encoding="utf-8")
    rc, out = scaffold(target, "--force")
    assert rc == 0, out
    assert (target / "requirements.txt").read_text() == "requests>=2\n"  # never edited
    assert "does not list PyYAML" in out
    assert "PyYAML>=5.1" in out


def test_force_preserve_no_pyyaml_warning_when_declared(tmp_path):
    # If the preserved requirements.txt already declares PyYAML (any case or pin), the
    # targeted warning must not fire: validation is still skipped for the preserve, but we
    # do not nag a user who did the right thing. Lowercase + pin proves name normalization.
    target = tmp_path / "kb"
    scaffold(target)
    (target / "requirements.txt").write_text("pyyaml==6.0.1\n", encoding="utf-8")
    rc, out = scaffold(target, "--force")
    assert rc == 0, out
    assert "skipping validation" in out.lower()  # the preserve still skips validation
    assert "does not list PyYAML" not in out


def test_force_preserve_no_pyyaml_warning_with_include(tmp_path):
    # A "-r base.txt" include can declare PyYAML in a file the scaffolder does not read, so
    # an uncertain requirements.txt suppresses the targeted warning rather than making a
    # false "missing" claim.
    target = tmp_path / "kb"
    scaffold(target)
    (target / "requirements.txt").write_text("-r base.txt\nrequests\n", encoding="utf-8")
    rc, out = scaffold(target, "--force")
    assert rc == 0, out
    assert "skipping validation" in out.lower()
    assert "does not list PyYAML" not in out


def test_force_preserve_warns_with_constraint_file_and_no_pyyaml(tmp_path):
    # A "-c constraints.txt" only pins versions of packages installed elsewhere; unlike an
    # include it cannot supply a missing package, so a preserved file that carries only a
    # constraint and no PyYAML declaration must still warn. Guards against treating -c as an
    # include and silently suppressing the note (pip: -c "Constrain versions", not install).
    target = tmp_path / "kb"
    scaffold(target)
    (target / "requirements.txt").write_text("-c constraints.txt\nrequests\n", encoding="utf-8")
    rc, out = scaffold(target, "--force")
    assert rc == 0, out
    assert "does not list PyYAML" in out
    assert "PyYAML>=5.1" in out


@pytest.mark.skipif(not HAS_PACKAGING, reason="marker evaluation needs the packaging library")
def test_force_preserve_warns_when_pyyaml_marker_excludes_env(tmp_path):
    # #185: a PyYAML line gated by a PEP 508 marker to another environment installs nothing
    # here, so the preserved file still lacks an importable PyYAML. The name sniffer alone
    # reads it as declared and stays silent; the marker must be evaluated so the note fires
    # when the declaration will not install for the interpreter that runs validate.py.
    target = tmp_path / "kb"
    scaffold(target)
    (target / "requirements.txt").write_text(
        'PyYAML; sys_platform == "no-such-platform"\n', encoding="utf-8")
    rc, out = scaffold(target, "--force")
    assert rc == 0, out
    assert "does not list PyYAML" in out
    assert "PyYAML>=5.1" in out


def test_force_preserve_no_warning_when_pyyaml_marker_matches(tmp_path):
    # the other side: a PyYAML line whose marker selects this interpreter installs normally,
    # so the note must stay silent. Guards against over-nagging on a valid environment gate.
    # Holds with or without packaging: the marker matches, and the no-packaging fallback also
    # treats the line as installable.
    target = tmp_path / "kb"
    scaffold(target)
    (target / "requirements.txt").write_text(
        'PyYAML; python_version >= "3.0"\n', encoding="utf-8")
    rc, out = scaffold(target, "--force")
    assert rc == 0, out
    assert "skipping validation" in out.lower()
    assert "does not list PyYAML" not in out


@pytest.mark.skipif(not HAS_PACKAGING, reason="marker evaluation needs the packaging library")
def test_force_preserve_warns_when_pyyaml_hash_line_marker_excludes_env(tmp_path):
    # #185 (review): pip-compile --generate-hashes writes a requirement as a backslash-
    # continued block: the marker on the first physical line, indented `--hash` options on
    # following lines. Read physically, the first line keeps a trailing '\' that breaks marker
    # parsing, so an environment-excluded PyYAML read as installable and the note went silent.
    # Joining continuations first reconstructs the logical line, drops the hash options, and
    # the excluding marker fires the note.
    target = tmp_path / "kb"
    scaffold(target)
    (target / "requirements.txt").write_text(
        'pyyaml==6.0.1 ; sys_platform == "no-such-platform" \\\n'
        '    --hash=sha256:aaaa \\\n'
        '    --hash=sha256:bbbb\n', encoding="utf-8")
    rc, out = scaffold(target, "--force")
    assert rc == 0, out
    assert "does not list PyYAML" in out


def test_force_preserve_no_warning_when_pyyaml_hash_line_no_marker(tmp_path):
    # guard on the join: a hash-locked PyYAML with no marker reconstructs to an installable
    # line, so the note stays silent. Holds with or without packaging.
    target = tmp_path / "kb"
    scaffold(target)
    (target / "requirements.txt").write_text(
        'pyyaml==6.0.1 \\\n    --hash=sha256:aaaa \\\n    --hash=sha256:bbbb\n', encoding="utf-8")
    rc, out = scaffold(target, "--force")
    assert rc == 0, out
    assert "does not list PyYAML" not in out


def test_force_preserve_no_warning_when_comment_ends_in_backslash(tmp_path):
    # #185 (review): pip does not continue a full-line comment even when it ends in '\'. If the
    # join treated the comment as continuing, it would swallow the following PyYAML line into
    # the comment, hiding the declaration and firing a false 'missing PyYAML' note. The comment
    # must be emitted on its own so the real PyYAML line is read. Holds with or without packaging.
    target = tmp_path / "kb"
    scaffold(target)
    (target / "requirements.txt").write_text(
        "# a trailing note that ends in a backslash \\\n"
        "PyYAML==6.0.1\n", encoding="utf-8")
    rc, out = scaffold(target, "--force")
    assert rc == 0, out
    assert "does not list PyYAML" not in out


def test_force_preserve_no_warning_when_comment_backslash_precedes_include(tmp_path):
    # #185 (review): same join bug, higher-impact variant. A comment ending in '\' just before
    # an `-r` include directive would swallow the directive, so the include (which may supply
    # PyYAML from a file we do not read) goes unseen and the note wrongly fires. The comment
    # must not continue, so the `-r` line is read and suppresses the note.
    target = tmp_path / "kb"
    scaffold(target)
    (target / "requirements.txt").write_text(
        "# via requirements.in \\\n"
        "-r base.txt\n", encoding="utf-8")
    rc, out = scaffold(target, "--force")
    assert rc == 0, out
    assert "does not list PyYAML" not in out


@pytest.mark.parametrize("line,expected", [
    ("PyYAML>=5.1", True),                       # no marker: installs here
    ('PyYAML; python_version >= "3.0"', True),   # marker selects this interpreter
    ("PyYAML  # just a note", True),             # inline comment, no marker
    ("PyYAML; ", True),                          # empty marker after ';'
])
def test_requirement_marker_selects_env_true_cases(line, expected):
    # a missing, empty, or matching marker selects the current environment. These hold with
    # or without packaging, since the packaging-absent fallback also returns True, so no
    # skip guard is needed here (only the excluding case below depends on packaging).
    assert scaffold_mod._requirement_marker_selects_env(line) == expected


@pytest.mark.skipif(not HAS_PACKAGING, reason="marker evaluation needs the packaging library")
def test_requirement_marker_excludes_env():
    # an excluding marker returns False only when packaging can evaluate it; the fallback
    # (packaging absent) returns True, so this case is guarded on packaging being present.
    assert scaffold_mod._requirement_marker_selects_env(
        'PyYAML; sys_platform == "no-such-platform"') is False


@pytest.mark.skipif(not HAS_PACKAGING, reason="marker evaluation needs the packaging library")
def test_requirement_marker_hash_inside_quoted_marker_excludes():
    # a '#' inside a quoted marker string is not a pip comment; stripping at the first '#'
    # would corrupt the marker. Parsing the full requirement keeps it intact, so the
    # excluding marker still evaluates (no implementation is named "cpython#not").
    assert scaffold_mod._requirement_marker_selects_env(
        'PyYAML; implementation_name == "cpython#not"') is False


@pytest.mark.skipif(not HAS_PACKAGING, reason="marker evaluation needs the packaging library")
def test_requirement_marker_semicolon_inside_url_excludes():
    # a ';' inside a direct-reference URL is part of the URL, not the marker separator.
    # Splitting on the first ';' would misread the URL as the marker; parsing the full
    # requirement extracts the real trailing marker after ' ; ' and evaluates it.
    assert scaffold_mod._requirement_marker_selects_env(
        'PyYAML @ https://example.com/pkg;param ; sys_platform == "no-such-platform"') is False


@pytest.mark.skipif(not HAS_PACKAGING, reason="marker evaluation needs the packaging library")
def test_requirement_marker_hashed_requirement_excluded():
    # a hash-pinned line (pip-compile --generate-hashes) carries pip's per-requirement
    # `--hash` option, which packaging.requirements.Requirement rejects. The pip option must
    # be stripped before parsing, or the excluding marker is never seen and the missing-PyYAML
    # warning is wrongly suppressed. With the option dropped the marker evaluates and excludes.
    assert scaffold_mod._requirement_marker_selects_env(
        'PyYAML==6.0.1; sys_platform == "no-such-platform" '
        '--hash=sha256:aaaa --hash=sha256:bbbb') is False


def test_requirement_marker_hashed_requirement_matches():
    # a hash-pinned PyYAML with no marker still counts as installable: dropping the `--hash`
    # options leaves a bare, applicable requirement. Holds with or without packaging (the
    # packaging-absent fallback also returns True), so no skip guard is needed.
    assert scaffold_mod._requirement_marker_selects_env(
        'PyYAML==6.0.1 --hash=sha256:aaaa') is True


@pytest.mark.skipif(not HAS_PACKAGING, reason="marker evaluation needs the packaging library")
def test_requirement_marker_whitespace_hash_inside_quoted_marker_excludes():
    # #185 (review): a '#' preceded by whitespace *inside* a quoted marker value is part of the
    # marker, not a pip inline comment. Stripping the comment before parsing (the earlier
    # regex-first approach) corrupts the marker and the line reads as installable, wrongly
    # suppressing the note. Parsing the whole line first keeps the '#' intact, so the excluding
    # marker still evaluates (no implementation is named "cpython #not").
    assert scaffold_mod._requirement_marker_selects_env(
        'PyYAML; implementation_name == "cpython #not"') is False


@pytest.mark.skipif(not HAS_PACKAGING, reason="marker evaluation needs the packaging library")
def test_requirement_marker_trailing_comment_after_marker_excludes():
    # guard on the parse-first change: a real pip inline comment after the marker must still be
    # stripped so the marker evaluates. The whole-line parse fails on the trailing comment, then
    # the comment is removed on retry and the excluding marker evaluates to False.
    assert scaffold_mod._requirement_marker_selects_env(
        'PyYAML; sys_platform == "no-such-platform"  # windows only') is False


@pytest.mark.skipif(not HAS_PACKAGING, reason="marker evaluation needs the packaging library")
def test_requirement_marker_unevaluable_lockfile_marker_does_not_crash():
    # #185 (review): packaging 26 added lock-file-context marker variables. A line such as
    # `PyYAML; dependency_groups == "docs"` parses, but Marker.evaluate() raises KeyError in the
    # default metadata context because that variable is not defined there. Any evaluation failure
    # must be treated as unjudgeable and fall back to installable, not crash. Asserts the outcome
    # (True, no exception), which also holds on older packaging that rejects the marker at parse
    # time (InvalidRequirement, then True via the parse fallback).
    assert scaffold_mod._requirement_marker_selects_env(
        'PyYAML; dependency_groups == "docs"') is True


@pytest.mark.skipif(not HAS_PACKAGING, reason="marker evaluation needs the packaging library")
def test_force_preserve_no_crash_on_unevaluable_marker(tmp_path):
    # #185 (review): a preserved requirements.txt whose PyYAML line carries a marker that parses
    # but cannot be evaluated in the default context (dependency_groups, a lock-file-only
    # variable) must not crash the --force run. The marker is unjudgeable, so PyYAML counts as
    # possibly installable and the note stays silent; the run exits 0.
    target = tmp_path / "kb"
    scaffold(target)
    (target / "requirements.txt").write_text(
        'PyYAML; dependency_groups == "docs"\n', encoding="utf-8")
    rc, out = scaffold(target, "--force")
    assert rc == 0, out
    assert "does not list PyYAML" not in out


@pytest.mark.parametrize("line,expected", [
    ("PyYAML>=5.1", "pyyaml"),              # version specifier stripped, lowercased
    ("pyyaml==6.0.1  # pinned", "pyyaml"),  # pin and inline comment stripped
    ("PyYAML[extra]", "pyyaml"),            # extras bracket stripped
    ("pyyaml @ https://example.com/p.whl", "pyyaml"),  # direct reference: name kept
    ("ruamel.yaml", "ruamel-yaml"),         # PEP 503 separator collapse (not PyYAML)
    ("# a comment", None),                  # comment names no package
    ("-r base.txt", None),                  # include option names no package
    ("https://example.com/p.whl", None),    # bare URL names no distribution
    ("./local/pkg", None),                  # local path names no distribution
    ("", None),                             # blank line
])
def test_canonical_req_name(line, expected):
    # The pure name sniffer the preserved-requirements PyYAML check relies on: PEP 503
    # normalization of the leading distribution name, and None for any line that names no
    # bare package (comment, option, include, URL, or path). Pinned here so a future edit
    # to the normalization cannot silently break PyYAML detection.
    assert scaffold_mod._canonical_req_name(line) == expected


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
    # date-shaped but invalid (month 13), PyYAML raises ValueError during parse,
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


# A labeled base64url secret value: URL-safe (- and _), so the base64-standard
# generic pattern misses it. Built from fragments so no secret-shaped token lives
# in this file. Its Shannon entropy is ~4.84 bits/char, well above the 4.0 floor.
URLSAFE_SECRET = "Zk9" + "_qX2" + "-Lm7" + "vB4t" + "Nc1w" + "Rp8h" + "Ej6" + "-uYs"


def test_urlsafe_secret_passes_without_entropy_scan(tmp_path):
    # Default behavior is unchanged: the opt-in scan is off, and the generic
    # base64 pattern deliberately does not match a hyphen/underscore value.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + f"\napi_key: {URLSAFE_SECRET}\n")
    rc, out = validate(b)
    assert rc == 0, out


def test_entropy_scan_flags_urlsafe_secret(tmp_path):
    # With the opt-in flag, the same URL-safe value is caught by entropy.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + f"\napi_key: {URLSAFE_SECRET}\n")
    rc, out = validate(b, "--secret-entropy-scan")
    assert rc == 1 and "high-entropy assignment" in out


def test_entropy_scan_keeps_okf_key_path(tmp_path):
    # The precision the earlier review round asked us to keep: a slash-delimited
    # OKF key path is not a secret even under the strict scan. Its own entropy
    # (~4.07) clears the floor, so this proves the structural `/` exclusion, not
    # just the threshold, is what protects documented key paths.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\nsecret: services/api/production-primary-key-path\n")
    rc, out = validate(b, "--secret-entropy-scan")
    assert rc == 0, out


def test_entropy_scan_keeps_key_path_with_long_first_segment(tmp_path):
    # Regression for the #150 review: the `/` exclusion stops the match at the
    # separator, but a first path segment of >=24 url-safe chars was still captured
    # and entropy-checked on its own. Here `prd-usw2-mysql-rw-20260722-key-path`
    # (35 chars, entropy 4.01, above the floor) precedes the `/service` suffix, so
    # the old pattern flagged the segment as a value. The trailing lookahead now
    # requires a complete token, so a documented key path stays clean regardless of
    # how long its leading segment is.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\nsecret: prd-usw2-mysql-rw-20260722-key-path/service\n")
    rc, out = validate(b, "--secret-entropy-scan")
    assert rc == 0, out


def test_entropy_scan_ignores_low_entropy_name(tmp_path):
    # A slashless but human-readable hyphenated value stays under the floor, so
    # the strict scan does not flag it.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\napi_key: prod-key-path-name-placeholder\n")
    rc, out = validate(b, "--secret-entropy-scan")
    assert rc == 0, out


def test_entropy_scan_flags_secret_just_above_floor(tmp_path):
    # Recall is the flag's whole reason to exist, so pin it at the knife-edge: a
    # 24-char base64url value whose entropy is 4.054, just over the 4.0 floor,
    # must still flag. Below this the scan silently misses, the acknowledged
    # precision-for-recall tradeoff, so this marks where that boundary sits.
    marginal = "Ab-Cd" + "_Ef-Gh" + "_Ij-Kl" + "_Mn-Op1"
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + f"\napi_key: {marginal}\n")
    rc, out = validate(b, "--secret-entropy-scan")
    assert rc == 1 and "high-entropy assignment" in out


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


@pytest.mark.parametrize("version", ["0.1", "0.2"])
def test_root_index_legacy_version_validates(tmp_path, version):
    # Backward compatibility: older date-only bundles still validate under the
    # newer validator.
    scaffold(tmp_path / "kb", "--no-validate")
    root = tmp_path / "kb" / "bundle" / "index.md"
    root.write_text(root.read_text().replace(
        'okf_version: "0.3"', f'okf_version: "{version}"'), encoding="utf-8")
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
    # a CommonMark link with a title, [text](dest "title"), must not be flagged
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
    # still be caught, the regex must not stop at the first ')'.
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


@pytest.mark.parametrize("label, token", [
    ("Stripe secret key", "sk_" + "live_" + "A1b2C3d4E5f6G7h8I9j0K1L2"),
    ("Stripe organization key", "sk_" + "org_" + "A1b2C3d4E5f6G7h8I9j0K1L2"),
    ("Stripe webhook secret", "whsec_" + "A1b2C3d4E5f6G7h8I9j0K1L2M3n4O5p6"),
    ("GitLab token", "glpat-" + "A1b2C3d4E5f6G7h8I9j0"),
    # A valid 20-character GitLab token body can repeat characters and land just
    # below the generic 4.0-bit entropy floor (3.984 bits/character here).
    ("GitLab token", "glpat-" + "5lRDXNfPxOMFQmlFCcFZ"),
    ("GitLab token", "gloas-" + "A1b2C3d4E5f6G7h8I9j0"),
    ("GitLab token", "gldt-" + "A1b2C3d4E5f6G7h8I9j0"),
    ("GitLab token", "glrt-" + "A1b2C3d4E5f6G7h8I9j0"),
    ("GitLab token", "glrtr-" + "A1b2C3d4E5f6G7h8I9j0"),
    ("GitLab token", "glcbt-" + "abc_" + "A1b2C3d4E5f6G7h8I9j0"),
    ("GitLab token", "glptt-" + "A1b2C3d4E5f6G7h8I9j0"),
    ("GitLab token", "glft-" + "A1b2C3d4E5f6G7h8I9j0"),
    ("GitLab token", "glimt-" + "A1b2C3d4E5f6G7h8I9j0"),
    ("GitLab token", "glagent-" + "A1b2C3d4E5f6G7h8I9j0"),
    ("GitLab token", "glwt-" + "A1b2C3d4E5f6G7h8I9j0"),
    ("GitLab token", "glsoat-" + "A1b2C3d4E5f6G7h8I9j0"),
    ("GitLab token", "glffct-" + "A1b2C3d4E5f6G7h8I9j0"),
    ("npm token", "npm_" + "A1b2C3d4E5f6G7h8" + "I9j0K1L2M3n4O5p6Q7r8"),
    ("SendGrid API key", "SG." + "A" * 22 + "." + "B" * 43),
    ("Anthropic API key", "sk-" + "ant-" + "api03-" + "A1b2C3d4E5f6G7h8I9j0"),
    ("OpenAI project key", "sk-" + "proj-" + "A1b2C3d4E5f6G7h8I9j0"),
    ("OpenAI legacy key", "sk-" + "A1b2C3d4E5f6G7h8I9j0" + "K1L2M3n4O5p6Q7r8S9t0"),
])
def test_provider_token_secret_detected(tmp_path, label, token):
    # Prefix-anchored provider detectors (issue #150 move A). Each token is built
    # from fragments so no real-looking secret lives in this file. They run on the
    # default validate (no flag); the negative test below pins the path-documentation
    # precision boundary.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + f"\nkey = {token}\n")
    rc, out = validate(b)
    # Assert the specific detector, not just that some leak fired, so a token that
    # matched the wrong pattern would still be caught.
    assert rc == 1 and f"secret leak ({label})" in out


def test_gitlab_session_cookie_secret_detected(tmp_path):
    # GitLab lists the session-cookie assignment itself alongside its fixed token
    # prefixes. Build the fake cookie from fragments so no real-looking value
    # lives in this test file.
    fake = "_gitlab_" + "session=" + "A1b2C3d4E5f6G7h8I9j0K1L2M3n4O5p6"
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + f"\nCookie: {fake}\n")
    rc, out = validate(b)
    assert rc == 1 and "secret leak (GitLab session cookie)" in out


def test_provider_prefixes_do_not_flag_prose(tmp_path):
    # The provider prefixes must not fire on documentation: a placeholder ellipsis,
    # an env-var name, words that merely contain an rk_/sk_ substring (the \b anchor
    # guards these), and provider-specific OKF key paths all stay clean on the
    # default validate.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    prose = (
        "Set your sk_test_... key from the dashboard.\n"
        "The npm_config_registry env var points at the mirror.\n"
        "Use the work_live and mark_live feature flags.\n"
        "The pointer secret: svc/api/prod-key-path names a vault key, not a value.\n"
        "The pointer secret: openai/sk-proj-production-primary-key-path is a vault path.\n"
        "The pointer secret: anthropic/sk-ant-production-primary-key-path is a vault path.\n"
        "The pointer secret: gitlab/gldt-production-deploy-token-path is a vault path.\n"
        "The pointer secret: openai/sk-proj-A1b2C3d4E5f6G7h8I9j0/key-path is a vault path.\n"
        "GitLab documents the placeholder _gitlab_session=... for browser sessions.\n"
    )
    write_concept(b, GOOD.rstrip() + "\n" + prose)
    rc, out = validate(b)
    assert rc == 0, out


def test_link_to_existing_uppercase_md_fails(tmp_path):
    # the case the prior case-sensitive design worried about: a link to an existing
    # Foo.MD used to "resolve" as valid while discovery never scanned that file. Now
    # discovery finds Target.MD and rejects it as non-conforming, so a bundle that
    # contains it fails -- the file check and the link check stay in agreement.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD, name="concepts/Target.MD")
    write_concept(b, GOOD.rstrip() + "\n\nSee [target](target.md).\n", name="concepts/c.md")
    rc, out = validate(b)
    assert rc == 1, out
    assert "rename Target.MD to target.md" in out
    assert "write Target.MD" not in out


def test_nonconforming_extension_rename_uses_real_parent_case(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD, name="concepts/Target.MD")
    write_concept(
        b,
        GOOD.rstrip() + "\n\nSee [target](../Concepts/target.md).\n",
        name="concepts/c.md",
    )
    rc, out = validate(b)
    assert rc == 1, out
    assert "rename Target.MD to target.md" in out
    assert "rename Target.MD to ../Concepts/target.md" not in out


def test_nonconforming_extension_rename_normalizes_link_extension(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD, name="concepts/Target.MD")
    write_concept(
        b,
        GOOD.rstrip() + "\n\nSee [target](target.MD).\n",
        name="concepts/c.md",
    )
    rc, out = validate(b)
    assert rc == 1, out
    assert "rename Target.MD to target.md" in out
    assert "rename Target.MD to target.MD" not in out


def test_wrong_case_dangling_symlink_is_reported_as_dangling(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    try:
        (b / "concepts" / "Broken.md").symlink_to("missing.md")
    except OSError as exc:
        pytest.skip(f"symlink unavailable on this filesystem: {exc}")
    write_concept(
        b,
        GOOD.rstrip() + "\n\nSee [broken](broken.md).\n",
        name="concepts/c.md",
    )
    rc, out = validate(b)
    assert rc == 1, out
    assert "dangling link -> broken.md" in out
    assert "write Broken.md" not in out


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
           "okf-wiki/example/SPEC.md drifted from spec/SPEC.md, re-sync the copy"


def test_example_validator_matches_canonical():
    # the example vendors scripts/validate.py; a drifted copy would validate the
    # committed example against stale rules.
    assert (SKILL / "example" / "scripts" / "validate.py").read_text(encoding="utf-8") == \
           (SKILL / "scripts" / "validate.py").read_text(encoding="utf-8"), \
           "okf-wiki/example/scripts/validate.py drifted from scripts/validate.py, re-sync the copy"


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
    # quoting the element protects it, this is the documented fix, so it must pass.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source('source:\n  - "README.md"\n  - "issue #445"'))
    rc, out = validate(b)
    assert rc == 0, out


def test_source_block_hash_no_space_ok(tmp_path):
    # `issue#445` (no space before #) is NOT a YAML comment, it stays intact, so the
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
    # duplicate that drops "#445" must still fail. A duplicate `source:` key is malformed
    # regardless of whether the later value is lossy, the effective source must come from
    # exactly one literal key, so this is rejected as a duplicate, closing the gap where two
    # clean duplicate source keys used to pass silently.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source(
        'source: ["README.md"]\nsource:\n  - issue #445'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "duplicate" in out


def test_source_two_clean_duplicate_keys_rejected(tmp_path):
    # regression: two literal `source:` keys that are BOTH clean used to pass silently,
    # safe_load kept the last and discarded the first with no warning, so a lost provenance
    # list went unreported. The "exactly one source key" invariant now rejects any duplicate,
    # lossy or not.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source(
        'source: ["README.md"]\nsource: ["LICENSE"]'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "duplicate" in out


def test_source_unquoted_with_apostrophe_then_hash_fails(tmp_path):
    # a quote mid plain-scalar (the apostrophe in "Joe's") is literal YAML content, so
    # `- Joe's issue #445` is an unquoted scalar that still drops "#445", the scan must
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


# --- #169: a YAML alias in source defeats the quoting check, so reject it -----

def _concept_with_frontmatter(fm_body):
    # a concept whose whole frontmatter body is given verbatim (for shapes the fixed
    # `source:` slot in _concept_with_source cannot express, e.g. an extra anchor key).
    return f"---\n{fm_body}\n---\n# good\n"


def test_source_alias_drops_comment_now_rejected(tmp_path):
    # #169 false-negative: an aliased block item (`*p`) shares its anchor's node, whose
    # end mark sits at the anchor definition, so the dropped `#445` after the alias was
    # never inspected and the lossy bundle passed. An alias in source is now a hard error.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source("source:\n  - &p README.md\n  - *p #445"))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "alias" in out


def test_source_flow_alias_rejected(tmp_path):
    # #169 false-positive shape: `source: [*p]` reads the same node as the anchor def on
    # another key, so the quoting check flagged that line's comment instead of the real
    # problem. The alias use itself is what's wrong, reject it, with an honest message.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_frontmatter(
        "type: Process\ntitle: good\ndescription: a good concept\n"
        "ptr: &p README.md\nsource: [*p]\n"
        'verified: 2026-06-23\ntimestamp: 2026-06-23\ntags: ["x"]'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "alias" in out


def test_source_anchor_defined_and_aliased_in_source_rejected(tmp_path):
    # an anchor defined and aliased entirely within source is still an alias use.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source('source:\n  - &p "README.md"\n  - *p'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "alias" in out


def test_source_whole_value_alias_rejected(tmp_path):
    # the entire source value can be an alias: `source: *p`. That resolves to a list and
    # would otherwise pass the list/quoting checks, so it must be caught here.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_frontmatter(
        "type: Process\ntitle: good\ndescription: a good concept\n"
        'refs: &p ["README.md"]\nsource: *p\n'
        'verified: 2026-06-23\ntimestamp: 2026-06-23\ntags: ["x"]'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "alias" in out


def test_source_anchor_definition_still_passes(tmp_path):
    # regression guard for the existing contract: an anchor DEFINITION on a literal
    # source element (never aliased) is harmless and must keep passing. Only alias USES
    # are rejected. (Mirrors test_source_anchored_quoted_value_passes.)
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_source('source: [&p "README.md"]'))
    rc, out = validate(b)
    assert rc == 0, out


def test_alias_outside_source_with_clean_source_passes(tmp_path):
    # an anchor/alias used OUTSIDE source must not fail a bundle whose top-level source
    # is clean and literal, the check is scoped to the source value only.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_frontmatter(
        "type: Process\ntitle: good\ndescription: a good concept\n"
        "note: &n reused\nother: *n\n"
        'source: ["README.md"]\n'
        'verified: 2026-06-23\ntimestamp: 2026-06-23\ntags: ["x"]'))
    rc, out = validate(b)
    assert rc == 0, out


def test_source_anchor_shared_with_other_key_rejected(tmp_path):
    # the other direction: an anchor DEFINED in source but aliased elsewhere entangles
    # source with the rest of the frontmatter. source must be self-contained literals, so
    # this is rejected too (the shared node's marks are ambiguous, per #169). Deliberate.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_frontmatter(
        "type: Process\ntitle: good\ndescription: a good concept\n"
        'source: [&p "README.md"]\nother: *p\n'
        'verified: 2026-06-23\ntimestamp: 2026-06-23\ntags: ["x"]'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and ("anchor" in out or "alias" in out)


def test_source_via_merge_key_drops_comment_now_rejected(tmp_path):
    # #169 sibling: `source` supplied through a YAML merge key (`<<`) is materialized by
    # safe_load but leaves no literal `source:` key node, so the quoting scan (which keys
    # on that node) never runs and a dropped `#445` slips through. The merged source must
    # be rejected: OKF source must be a literal top-level list, not merged in.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_frontmatter(
        "type: Process\ntitle: good\ndescription: a good concept\n"
        "refs: &r\n  - issue #445\n<<: {source: *r}\n"
        'verified: 2026-06-23\ntimestamp: 2026-06-23\ntags: ["x"]'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "merge" in out


def test_source_via_merge_key_clean_still_rejected(tmp_path):
    # even a merge-supplied source with no dropped comment is rejected, the indirection
    # itself is invalid, so the check does not depend on the merged value being lossy.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_frontmatter(
        "type: Process\ntitle: good\ndescription: a good concept\n"
        'refs: &r ["README.md"]\n<<: {source: *r}\n'
        'verified: 2026-06-23\ntimestamp: 2026-06-23\ntags: ["x"]'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "merge" in out


def test_source_via_merge_key_with_literal_source_rejected(tmp_path):
    # codex-connector P2: a merge whose mapping carries its own `source` (`<<: {source: ...}`)
    # sitting beside a literal `source:` key used to pass. YAML lets the literal override the
    # merged value, so the top-level scan counted only the literal (len 1) and the merged
    # provenance was silently dropped: the same lost-provenance shape the duplicate-key check
    # rejects. A merge that supplies source is now rejected whether or not a literal source
    # sits beside it (the earlier merge tests only covered merge-supplied source with no literal).
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_frontmatter(
        "type: Process\ntitle: good\ndescription: a good concept\n"
        '<<: {source: ["LICENSE"]}\nsource: ["README.md"]\n'
        'verified: 2026-06-23\ntimestamp: 2026-06-23\ntags: ["x"]'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "merge" in out


def test_source_via_nested_merge_key_with_literal_source_rejected(tmp_path):
    # codex 5.5 round 1: the merge-supplied-source check must look at the merged mapping's
    # EFFECTIVE keys, not just its immediate ones. A merge that imports a mapping whose own
    # `source` arrives through a further nested merge (`defaults: &d {<<: {source: [...]}}`
    # then `<<: *d`) still materializes source in safe_load, and a literal `source:` overrides
    # it, dropping the merged provenance. Recursing through nested merges closes that bypass.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_frontmatter(
        "type: Process\ntitle: good\ndescription: a good concept\n"
        'defaults: &d {<<: {source: ["LICENSE"]}}\n<<: *d\nsource: ["README.md"]\n'
        'verified: 2026-06-23\ntimestamp: 2026-06-23\ntags: ["x"]'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "merge" in out


def test_source_alias_as_key_rejected(tmp_path):
    # #169 sibling (review): an alias in KEY position (`*k` resolving to "source") makes
    # compose reuse the anchor's node, so the key reads as a literal "source" while the real
    # key is an alias. safe_load still materializes source, so this must be rejected like any
    # other non-literal source key, even when the aliased key's value is itself clean.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_frontmatter(
        "type: Process\ntitle: good\ndescription: a good concept\n"
        'source_key: &k source\n*k: ["README.md"]\n'
        'verified: 2026-06-23\ntimestamp: 2026-06-23\ntags: ["x"]'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and ("merge" in out or "alias" in out)


def test_merge_key_outside_source_with_clean_source_passes(tmp_path):
    # scope guard: a merge key that supplies OTHER fields, with a literal clean source,
    # must still pass, the check rejects merged/aliased source only, not every merge key.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_frontmatter(
        "type: Process\ntitle: good\ndescription: a good concept\n"
        "defaults: &d\n  note: x\n<<: *d\nsource: [\"README.md\"]\n"
        'verified: 2026-06-23\ntimestamp: 2026-06-23\ntags: ["x"]'))
    rc, out = validate(b)
    assert rc == 0, out


def test_source_explicit_merge_tag_key_with_clean_source_passes(tmp_path):
    # #169 sibling (review round 2): a key SPELLED "source" but carrying the explicit !!merge
    # tag is a merge directive, not a source key, PyYAML identifies merge by the key's tag,
    # not its scalar spelling. safe_load merges it and the effective mapping has only the
    # separate literal `source:`, so the file is valid. Classifying by spelling alone counts
    # the merge-tagged key as a second "source" key and falsely rejects it.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_frontmatter(
        "type: Process\ntitle: good\ndescription: a good concept\n"
        'defaults: &d {note: x}\n!!merge source: *d\nsource: ["README.md"]\n'
        'verified: 2026-06-23\ntimestamp: 2026-06-23\ntags: ["x"]'))
    rc, out = validate(b)
    assert rc == 0, out


def test_source_explicit_merge_tag_supplies_lossy_source_rejected(tmp_path):
    # #169 sibling (review round 2): the other direction, a merge key written with the
    # explicit !!merge tag but spelled "source" merges a nested source in, so safe_load's
    # effective source is lossy ("issue", #445 dropped) while no literal source key exists.
    # Classifying by spelling counts the merge-tagged key as the one literal source and lets
    # the lossy pointer bypass the scan; the tag must exclude it, so this is rejected.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_frontmatter(
        "type: Process\ntitle: good\ndescription: a good concept\n"
        '!!merge source:\n  source:\n    - issue #445\n'
        'verified: 2026-06-23\ntimestamp: 2026-06-23\ntags: ["x"]'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out


def test_source_literal_then_aliased_duplicate_key_rejected(tmp_path):
    # #169 sibling (review round 2): a clean literal `source:` FIRST, then a second key that
    # is an alias resolving to "source" (`*k`). YAML keeps the last of duplicate keys, so
    # safe_load's effective source is the aliased duplicate ("issue", with #445 dropped), yet
    # the earlier clean literal made the old "at least one clean source key" check pass. The
    # effective source must come from exactly one literal source key, so the duplicate is
    # rejected.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, _concept_with_frontmatter(
        "type: Process\ntitle: good\ndescription: a good concept\n"
        'source: ["README.md"]\nsource_key: &k source\n*k:\n  - issue #445\n'
        'verified: 2026-06-23\ntimestamp: 2026-06-23\ntags: ["x"]'))
    rc, out = validate(b)
    assert rc == 1, out
    assert "source" in out and "duplicate" in out


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


@pytest.mark.parametrize("url,on_editor", [
    # Still on the editor: save has not completed.
    ("https://github.com/owner/repo/wiki/_new", True),
    ("https://github.com/owner/repo/wiki/_new/", True),
    ("https://github.com/owner/repo/wiki/_new?foo=bar", True),
    ("https://github.com/owner/repo/wiki/_new#section", True),
    # Redirected to a saved page: save confirmed.
    ("https://github.com/owner/repo/wiki/Home", False),
    ("https://github.com/owner/repo/wiki/_new-notes", False),
    # The regression: a repo whose NAME contains "_new" still redirects to a
    # saved page, but the old whole-URL substring check read it as a failure.
    ("https://github.com/owner/service_new/wiki/Home", False),
    ("https://github.com/owner/service_new/wiki/service_new", False),
    # ...and that same repo's editor URL is still correctly detected as unsaved.
    ("https://github.com/owner/service_new/wiki/_new", True),
])
def test_still_on_editor_matches_the_editor_path_not_the_substring(url, on_editor):
    assert gh_wiki_bootstrap._still_on_editor(url) is on_editor


def _validate_module():
    """Import validate.py as a module.

    The module-level `validate` in this file is a subprocess runner, not the
    module, so unit-testing a single check has to load the file directly.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("okf_validate", VALIDATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestTimestampAcceptsIsoDatetime:
    """Upstream OKF writes `timestamp` as a full ISO 8601 datetime.

    Rejecting it only forced a truncation pass over every imported bundle, so it
    is accepted and carried. `verified` is this spec's own key and stays
    date-only -- a time of day there is false precision about when a fact was
    confirmed true.
    """

    def _errors(self, key, value, version="0.3", quoted=False):
        mod = _validate_module()
        scalar = f'"{value}"' if quoted or value == "" else value
        raw_fm = f"{key}: {scalar}\n"
        try:
            fm = mod.yaml.safe_load(raw_fm)
        except ValueError:
            # The CLI reports an invalid YAML timestamp constructor cleanly
            # before check_dates; keep this unit helper focused on the checker.
            fm = {key: value}
        errors = []
        mod.check_dates("f.md", fm, raw_fm, version, errors)
        return errors

    @pytest.mark.parametrize("value", [
        "2026-05-28",
        "2026-05-28T14:30:00Z",
        "2026-05-28T14:30:00+00:00",
        "2026-05-28T14:30:00-04:00",
        "2026-05-28T14:30:00",
        "2026-05-28T14:30:00.123456Z",
        "2026-05-28 14:30:00",  # RFC 3339's by-agreement space separator
    ])
    def test_timestamp_accepts_date_and_datetime(self, value):
        assert self._errors("timestamp", value) == []

    def test_verified_stays_date_only(self):
        errors = self._errors("verified", "2026-05-28T14:30:00Z")
        assert len(errors) == 1
        assert "YYYY-MM-DD" in errors[0]
        # The message must not offer the datetime form for a key that rejects it.
        assert "datetime" not in errors[0]

    def test_quoted_datetime_is_accepted(self):
        assert self._errors(
            "timestamp", "2026-05-28T14:30:00Z", quoted=True) == []

    @pytest.mark.parametrize("value", [
        "2026-5-8T4:03:02Z",
        "2026-05-28 14:30:00 Z",
    ])
    def test_timestamp_rejects_yaml_normalised_spelling(self, value):
        # PyYAML constructs both source spellings as datetime objects. Validation
        # must inspect the scalar text instead of accepting datetime.isoformat().
        errors = self._errors("timestamp", value)
        assert len(errors) == 1
        assert value in errors[0]

    @pytest.mark.parametrize("version", ["0.1", "0.2"])
    def test_legacy_version_rejects_datetime(self, version):
        errors = self._errors("timestamp", "2026-05-28T14:30:00Z", version)
        assert len(errors) == 1
        assert "require okf_version 0.3" in errors[0]

    @pytest.mark.parametrize("value", [
        "2026-05-28x14:30:00",  # fromisoformat takes any single separator; ISO does not
        "2026-05-28T",
        "2026-05-2814:30:00",
    ])
    def test_timestamp_rejects_a_non_iso_separator(self, value):
        # The parser is not the contract. fromisoformat parses '...x14:30:00'
        # clean, so the separator is checked before it is called -- otherwise
        # widening to datetimes would quietly accept malformed metadata.
        assert len(self._errors("timestamp", value)) == 1

    @pytest.mark.parametrize("value", ["2026-13-99", "nonsense", "2026/05/28", ""])
    def test_timestamp_still_rejects_garbage(self, value):
        # Widening to datetimes must not turn the check into a rubber stamp.
        assert len(self._errors("timestamp", value)) == 1

    def test_timestamp_error_names_both_accepted_forms(self):
        errors = self._errors("timestamp", "nonsense")
        assert "YYYY-MM-DD" in errors[0] and "ISO 8601 datetime" in errors[0]

    def test_root_level_concept_uses_declared_version_before_index(self, tmp_path):
        scaffold(tmp_path / "kb", "--no-validate")
        bundle = tmp_path / "kb" / "bundle"
        concept = GOOD.replace(
            "timestamp: 2026-06-23", "timestamp: 2026-06-23T14:30:00Z")
        write_concept(bundle, concept, name="a.md")
        rc, out = validate(bundle)
        assert rc == 0, out

    def test_legacy_bundle_rejects_datetime_end_to_end(self, tmp_path):
        scaffold(tmp_path / "kb", "--no-validate")
        bundle = tmp_path / "kb" / "bundle"
        root = bundle / "index.md"
        root.write_text(root.read_text().replace(
            'okf_version: "0.3"', 'okf_version: "0.2"'), encoding="utf-8")
        concept = GOOD.replace(
            "timestamp: 2026-06-23", "timestamp: 2026-06-23T14:30:00Z")
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "require okf_version 0.3" in out


# --- Upstream v0.2 trust/provenance vocabulary (generated, verified, sources,
# status, stale_after, Attested Computation) and the okf_version 0.4 rename of
# 'verified' to 'verified_on' that makes room for the new 'verified' shape. ---

GOOD_V04 = GOOD.replace("verified: 2026-06-23", "verified_on: 2026-06-23")


def _scaffold_v04(tmp_path, name="kb"):
    scaffold(tmp_path / name, "--no-validate", "--trust-signals")
    return tmp_path / name / "bundle"


class TestScaffoldTrustSignalsFlag:
    def test_default_scaffold_still_writes_0_3_and_legacy_verified(self, tmp_path):
        # Pins the revert: adding --trust-signals must not change scaffold's
        # default output for every existing caller.
        rc, out = scaffold(tmp_path / "kb", "--no-validate")
        assert rc == 0, out
        root = (tmp_path / "kb" / "bundle" / "index.md").read_text()
        assert 'okf_version: "0.3"' in root
        example = (tmp_path / "kb" / "bundle" / "concepts" / "example-concept.md").read_text()
        assert "verified:" in example and "verified_on:" not in example
        rc, out = validate(tmp_path / "kb" / "bundle")
        assert rc == 0, out

    def test_trust_signals_flag_writes_0_4_and_verified_on(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        root = (bundle / "index.md").read_text()
        assert 'okf_version: "0.4"' in root
        example = (bundle / "concepts" / "example-concept.md").read_text()
        assert "verified_on:" in example and "verified:" not in example
        rc, out = validate(bundle)
        assert rc == 0, out

    def test_trust_signals_readme_documents_verified_on(self, tmp_path):
        scaffold(tmp_path / "kb", "--no-validate", "--trust-signals")
        readme = (tmp_path / "kb" / "README.md").read_text()
        assert "verified_on" in readme
        assert "source, verified, timestamp" not in readme


class TestVerifiedOnRename:
    def test_legacy_bundle_still_requires_verified_not_verified_on(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.3"\n---\n# kb\n', encoding="utf-8")
        write_concept(bundle, GOOD)  # legacy 'verified', not 'verified_on'
        rc, out = validate(bundle)
        assert rc == 0, out

    def test_legacy_bundle_rejects_verified_on_in_place_of_verified(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.3"\n---\n# kb\n', encoding="utf-8")
        write_concept(bundle, GOOD_V04)  # has verified_on, not verified
        rc, out = validate(bundle)
        assert rc == 1
        assert "missing/empty required frontmatter key 'verified'" in out

    def test_v04_bundle_requires_verified_on_not_verified(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        write_concept(bundle, GOOD)  # legacy 'verified', wrong at 0.4
        rc, out = validate(bundle)
        assert rc == 1
        assert "missing/empty required frontmatter key 'verified_on'" in out

    def test_v04_bundle_accepts_verified_on(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        write_concept(bundle, GOOD_V04)
        rc, out = validate(bundle)
        assert rc == 0, out

    def test_v04_bundle_accepts_datetime_timestamp(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace(
            "timestamp: 2026-06-23",
            "timestamp: 2026-06-23T14:30:00Z")
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 0, out


class TestVerifiedTrustList:
    def test_v04_verified_confirmation_list_passes(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace(
            "tags: [\"x\"]",
            'verified:\n  - { by: "human:kliu@acme", at: 2026-07-01 }\n'
            '  - { by: "agent:reference_agent", at: 2026-06-30 }\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 0, out

    def test_v04_verified_absent_is_fine_unverified(self, tmp_path):
        # Absence of the new 'verified' is not an error -- it just means
        # "unverified" to a consumer deriving a trust tier.
        bundle = _scaffold_v04(tmp_path)
        write_concept(bundle, GOOD_V04)
        rc, out = validate(bundle)
        assert rc == 0, out

    def test_pre_04_bundle_ignores_new_verified_shape_check(self, tmp_path):
        # At 0.3, 'verified' IS the required legacy single-date field -- a list
        # there must fail the legacy date check, not be silently accepted as a
        # trust-confirmation list (that shape only exists at 0.4).
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.3"\n---\n# kb\n', encoding="utf-8")
        concept = GOOD.replace(
            "verified: 2026-06-23",
            'verified:\n  - { by: "human:kliu@acme", at: 2026-07-01 }')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "'verified' must be an ISO date" in out

    @pytest.mark.parametrize("bad_verified,msg", [
        ("verified: []", "non-empty YAML list"),
        ("verified: not-a-list", "non-empty YAML list"),
        ('verified:\n  - { at: 2026-07-01 }', "'verified[0].by'"),
        ('verified:\n  - { by: "human:kliu@acme" }', "'verified[0].at'"),
        ('verified:\n  - { by: "human:kliu@acme", at: nonsense }', "'verified[0].at'"),
        ('verified:\n  - { by: "human:kliu@acme", at: 2026-06-30 4:05:06 }', "'verified[0].at'"),
        ('verified:\n  - "just a string"', "'verified[0]'"),
    ])
    def test_v04_verified_malformed_entries_rejected(self, tmp_path, bad_verified, msg):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace('tags: ["x"]', f'{bad_verified}\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert msg in out

    @pytest.mark.parametrize("written", ["2026-6-3", "!!timestamp 2026-6-3"])
    def test_v04_verified_rejects_yaml_normalized_date_spelling(self, tmp_path, written):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace(
            'tags: ["x"]',
            f'verified:\n  - {{ by: "human:kliu@acme", at: {written} }}\n'
            'tags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "'verified[0].at' must be an ISO date YYYY-MM-DD" in out


class TestGenerated:
    def test_generated_valid_passes_at_v04(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace(
            'tags: ["x"]',
            'generated: { by: "reference_agent/gemini-2.5-pro", at: 2026-06-30T14:00:00Z }\n'
            'tags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 0, out

    def test_generated_accepts_plain_date_too(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace(
            'tags: ["x"]',
            'generated: { by: "human:jsmith@acme", at: 2026-06-30 }\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 0, out

    @pytest.mark.parametrize("bad,msg", [
        ("generated: not-a-mapping", "'generated' must be a mapping"),
        ('generated: { at: 2026-06-30 }', "'generated.by'"),
        ('generated: { by: "x" }', "'generated.at'"),
        ('generated: { by: "x", at: nonsense }', "'generated.at'"),
        ('generated: { by: "", at: 2026-06-30 }', "'generated.by'"),
    ])
    def test_generated_malformed_rejected(self, tmp_path, bad, msg):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace("tags: [\"x\"]", f'{bad}\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert msg in out

    def test_generated_at_rejects_yaml_normalized_datetime_spelling(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace(
            'tags: ["x"]',
            'generated: { by: "x", at: 2026-06-30 4:05:06 }\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "'generated.at' must be an ISO date or a full ISO 8601 datetime" in out


class TestTrustSignalVersionGate:
    @pytest.mark.parametrize("version", ["0.1", "0.2", "0.3"])
    @pytest.mark.parametrize("extra", [
        "generated: not-a-mapping",
        "sources: not-a-list",
        "status: not-a-status",
        "stale_after: not-a-date",
    ])
    def test_pre_04_bundle_ignores_trust_signal_extra_keys(self, tmp_path, version, extra):
        scaffold(tmp_path / "kb", "--no-validate")
        bundle = tmp_path / "kb" / "bundle"
        root = bundle / "index.md"
        root.write_text(
            root.read_text(encoding="utf-8").replace(
                'okf_version: "0.3"', f'okf_version: "{version}"'),
            encoding="utf-8")
        concept = GOOD.replace("tags: [\"x\"]", f'{extra}\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 0, out


class TestNullTrustSignals:
    @pytest.mark.parametrize("field", [
        "generated",
        "verified",
        "sources",
        "status",
        "stale_after",
    ])
    def test_v04_rejects_explicitly_null_trust_signal(self, tmp_path, field):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace(
            'tags: ["x"]',
            f"{field}: null\ntags: [\"x\"]")
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert f"'{field}'" in out


class TestSourcesPlural:
    def test_sources_valid_full_shape_passes(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace(
            'tags: ["x"]',
            "sources:\n"
            '  - id: "warehouse-schema"\n'
            '    resource: "https://wiki.acme.internal/data/warehouse/schemas/sales"\n'
            '    title: "Acme Retail warehouse schema"\n'
            '    author: "team:data-platform"\n'
            "    usage_count: 1240\n"
            "    last_modified: 2026-06-15\n"
            'tags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 0, out

    def test_sources_minimal_shape_passes(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace(
            'tags: ["x"]',
            'sources:\n  - id: "a"\n    resource: "README.md"\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 0, out

    def test_sources_resource_rejects_yaml_comment_truncation(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace(
            'tags: ["x"]',
            'sources:\n  - id: "a"\n    resource: issue #445\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "'sources[0].resource' has an unquoted '#'" in out

    @pytest.mark.parametrize("written", ["2026-6-3", "!!timestamp 2026-6-3"])
    def test_sources_last_modified_rejects_yaml_normalized_date_spelling(
            self, tmp_path, written):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace(
            'tags: ["x"]',
            'sources:\n  - id: "a"\n    resource: "README.md"\n'
            f'    last_modified: {written}\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "'sources[0].last_modified' must be an ISO date YYYY-MM-DD" in out

    def test_sources_duplicate_id_rejected(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace(
            'tags: ["x"]',
            'sources:\n  - id: "a"\n    resource: "one.md"\n'
            '  - id: "a"\n    resource: "two.md"\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "duplicates an earlier entry" in out

    @pytest.mark.parametrize("bad,msg", [
        ("sources: []", "non-empty YAML list"),
        ('sources:\n  - resource: "x.md"', "'sources[0].id'"),
        ('sources:\n  - id: "a"', "'sources[0].resource'"),
        ('sources:\n  - id: "a"\n    resource: "x.md"\n    usage_count: -1', "usage_count"),
        ('sources:\n  - id: "a"\n    resource: "x.md"\n    usage_count: "many"', "usage_count"),
        ('sources:\n  - id: "a"\n    resource: "x.md"\n    last_modified: nonsense', "last_modified"),
    ])
    def test_sources_malformed_rejected(self, tmp_path, bad, msg):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace("tags: [\"x\"]", f'{bad}\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert msg in out


class TestStatusAndStaleAfter:
    @pytest.mark.parametrize("status", ["draft", "stable", "deprecated"])
    def test_status_allowed_values_pass(self, tmp_path, status):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace("tags: [\"x\"]", f'status: {status}\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 0, out

    def test_status_invalid_value_rejected(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace("tags: [\"x\"]", 'status: "wip"\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "'status' must be one of" in out

    def test_stale_after_valid_date_passes(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace("tags: [\"x\"]", 'stale_after: 2026-12-31\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 0, out

    def test_stale_after_invalid_date_rejected(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace("tags: [\"x\"]", 'stale_after: not-a-date\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "'stale_after' must be an ISO date" in out

    @pytest.mark.parametrize("written", ["2026-6-3", "!!timestamp 2026-6-3"])
    def test_stale_after_rejects_yaml_normalized_date_spelling(self, tmp_path, written):
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace(
            'tags: ["x"]',
            f'stale_after: {written}\ntags: ["x"]')
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "'stale_after' must be an ISO date YYYY-MM-DD" in out


ATTESTED_COMPUTATION_GOOD = """---
type: Attested Computation
title: Revenue for a fiscal year
description: Sanctioned computation for fiscal-year revenue.
source: ["policies/revenue-recognition.md"]
verified_on: 2026-06-23
timestamp: 2026-06-23
tags: ["finance"]
runtime: bigquery
parameters:
  - { name: year, type: integer, required: true }
executor:
  resource: "skills/run-on-bq.md"
  receipt: ["job_id", "executed_sql", "result"]
attester:
  resource: "attesters/sql_equality.py"
---
# Computation

SELECT 1;
"""


class TestAttestedComputation:
    def test_valid_attested_computation_passes(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        write_concept(bundle, ATTESTED_COMPUTATION_GOOD)
        rc, out = validate(bundle)
        assert rc == 0, out
        assert "Attested Computation=1" in out

    def test_type_in_allowed_vocab(self, tmp_path):
        # A bare-minimum concept of this type with no of the extra keys must
        # fail on the extra keys, not on an unrecognised type.
        bundle = _scaffold_v04(tmp_path)
        concept = GOOD_V04.replace("type: Process", "type: Attested Computation")
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "not in the spec vocab" not in out
        assert "requires a non-empty 'runtime'" in out

    @pytest.mark.parametrize("version", ["0.1", "0.2", "0.3"])
    def test_type_rejected_before_v04(self, tmp_path, version):
        scaffold(tmp_path / "kb", "--no-validate")
        bundle = tmp_path / "kb" / "bundle"
        root = bundle / "index.md"
        root.write_text(
            root.read_text(encoding="utf-8").replace(
                'okf_version: "0.3"', f'okf_version: "{version}"'),
            encoding="utf-8")
        concept = GOOD.replace("type: Process", "type: Attested Computation")
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "type 'Attested Computation' not in the spec vocab" in out

    def test_missing_runtime_rejected(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = ATTESTED_COMPUTATION_GOOD.replace("runtime: bigquery\n", "")
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "requires a non-empty 'runtime'" in out

    def test_missing_parameters_rejected(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = ATTESTED_COMPUTATION_GOOD.replace(
            "parameters:\n  - { name: year, type: integer, required: true }\n", "")
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "requires a 'parameters' list" in out

    def test_empty_parameters_list_allows_fixed_computation(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = ATTESTED_COMPUTATION_GOOD.replace(
            "parameters:\n  - { name: year, type: integer, required: true }\n",
            "parameters: []\n")
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 0, out

    def test_parameter_missing_required_flag_rejected(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = ATTESTED_COMPUTATION_GOOD.replace(
            "{ name: year, type: integer, required: true }", "{ name: year, type: integer }")
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "'parameters[0].required'" in out

    def test_parameter_undeclared_key_rejected(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = ATTESTED_COMPUTATION_GOOD.replace(
            "{ name: year, type: integer, required: true }",
            "{ name: year, type: integer, required: true, default: 2026 }")
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "'parameters[0]' has undeclared keys ['default']" in out

    def test_missing_executor_rejected(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = ATTESTED_COMPUTATION_GOOD.replace(
            'executor:\n  resource: "skills/run-on-bq.md"\n  receipt: ["job_id", "executed_sql", "result"]\n',
            "")
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "requires an 'executor' mapping" in out

    def test_executor_empty_receipt_rejected(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = ATTESTED_COMPUTATION_GOOD.replace(
            'receipt: ["job_id", "executed_sql", "result"]', "receipt: []")
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "'executor.receipt'" in out

    def test_missing_attester_rejected(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = ATTESTED_COMPUTATION_GOOD.replace(
            'attester:\n  resource: "attesters/sql_equality.py"\n', "")
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "requires an 'attester' mapping" in out

    def test_attester_missing_resource_rejected(self, tmp_path):
        bundle = _scaffold_v04(tmp_path)
        concept = ATTESTED_COMPUTATION_GOOD.replace(
            'attester:\n  resource: "attesters/sql_equality.py"', "attester:\n  resource: \"\"")
        write_concept(bundle, concept)
        rc, out = validate(bundle)
        assert rc == 1
        assert "'attester.resource'" in out


def test_skill_authoring_workflow_is_version_aware():
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert '`verified` for `okf_version` `0.1` through `0.3`' in skill
    assert '`verified_on` for `okf_version` `0.4`' in skill


def test_wrong_case_link_names_the_real_file(tmp_path):
    # The link resolves on macOS and Windows, where the filesystem answers
    # case-insensitively, and dangles on Linux. Reporting it as "dangling" leaves
    # the author of the mac-side bundle reading a CI failure about a file they can
    # see on their own disk, so name the real path instead.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD, name="concepts/target.md")
    write_concept(b, GOOD.rstrip() + "\nSee [x](Target.md).\n", name="concepts/c.md")
    rc, out = validate(b)
    assert rc == 1
    assert "link case does not match" in out
    # Relative to the linking file, so it can be pasted straight into the link.
    assert "write target.md" in out
    # The unhelpful wording must not also fire for the same link.
    assert "dangling link -> Target.md" not in out


def test_wrong_case_link_fix_preserves_fragment(tmp_path):
    # The diagnostic promises a replacement that can be pasted into the link.
    # Correcting path casing must not discard the section the author targeted.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD, name="concepts/target.md")
    write_concept(
        b,
        GOOD.rstrip() + "\nSee [x](Target.md#usage).\n",
        name="concepts/c.md",
    )
    rc, out = validate(b)
    assert rc == 1
    assert "link case does not match" in out
    assert "write target.md#usage" in out


def test_wrong_case_directory_in_link_caught(tmp_path):
    # Every component is walked, not just the filename: a mac-side bundle can get
    # the directory wrong just as easily.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD, name="concepts/target.md")
    write_concept(b, GOOD.rstrip() + "\nSee [x](../Concepts/target.md).\n", name="concepts/c.md")
    rc, out = validate(b)
    assert rc == 1 and "link case does not match" in out


def test_missing_file_is_still_reported_as_dangling(tmp_path):
    # A link matching nothing on disk, case or no case, keeps the plain wording.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD.rstrip() + "\nSee [x](nowhere.md).\n")
    rc, out = validate(b)
    assert rc == 1 and "dangling link -> nowhere.md" in out
    assert "link case does not match" not in out


def test_exact_case_link_passes(tmp_path):
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    write_concept(b, GOOD, name="concepts/target.md")
    write_concept(b, GOOD.rstrip() + "\nSee [x](target.md).\n", name="concepts/c.md")
    rc, out = validate(b)
    assert rc == 0, out


def test_real_case_path_reports_the_on_disk_name(tmp_path):
    # Unit-level: the walk answers with the real name, so the caller can name it.
    real_case_path = _validate_module().real_case_path
    (tmp_path / "concepts").mkdir()
    (tmp_path / "concepts" / "target.md").write_text("x", encoding="utf-8")
    assert real_case_path(tmp_path / "concepts" / "target.md", tmp_path) \
        == tmp_path / "concepts" / "target.md"
    assert real_case_path(tmp_path / "Concepts" / "TARGET.md", tmp_path) \
        == tmp_path / "concepts" / "target.md"
    assert real_case_path(tmp_path / "concepts" / "nowhere.md", tmp_path) is None
    # A file where a directory is expected is not a resolvable parent.
    assert real_case_path(tmp_path / "concepts" / "target.md" / "deeper.md", tmp_path) is None


def test_two_case_variants_report_dangling_not_a_guess(tmp_path):
    # A Linux checkout of a bundle that went through a case-rename on macOS holds
    # both spellings. There is no way to say which the link meant, and picking
    # whichever os.listdir returned first would be an order-dependent guess.
    scaffold(tmp_path / "kb", "--no-validate")
    b = tmp_path / "kb" / "bundle"
    probe = tmp_path / "case-sensitivity-probe"
    probe.mkdir()
    (probe / "lower").write_text("x", encoding="utf-8")
    if (probe / "LOWER").exists():
        pytest.skip("filesystem cannot represent two names that differ only by case")
    write_concept(b, GOOD, name="concepts/target.md")
    write_concept(b, GOOD, name="concepts/Target.md")
    write_concept(b, GOOD.rstrip() + "\nSee [x](TARGET.md).\n", name="concepts/c.md")
    rc, out = validate(b)
    assert rc == 1 and "dangling link -> TARGET.md" in out
    assert "link case does not match" not in out
