#!/usr/bin/env python3
"""Validate an OKF (Open Knowledge Format) bundle against OKF spec v1 (see SPEC.md).

An OKF bundle is a tree of small markdown files: one concept per file, each with
YAML frontmatter carrying its provenance. Directory `index.md` files provide
navigation. This validator enforces the contract so a bundle stays machine- and
agent-readable.

Checks:
  1. Every non-reserved .md file has a parseable YAML frontmatter block. A YAML
     parse error is reported (commonly an unquoted colon-space or '#' in a
     string field — quote the value).
  2. Frontmatter carries every required key, non-empty:
     type, title, description, source, verified, timestamp, tags.
       - type     is one of the spec type vocab.
       - source   is a non-empty list of non-empty strings (provenance pointers).
                  An unquoted '#' in a block-style element (which YAML would silently
                  drop as a comment, losing the rest) is rejected — quote it.
       - tags     is a list.
       - verified, timestamp parse as ISO dates (YYYY-MM-DD).
  3. Reserved filenames (index.md, log.md) name no concept and carry no
     frontmatter — except the bundle-root index.md may carry okf_version only.
  4. Internal markdown links resolve. Links must be relative — a root-relative
     ('/'-prefixed) link is rejected. Every link to a .md file inside the bundle
     must point at a file that exists; a link that escapes the bundle root or
     dangles is a hard failure. Optional link titles and <>-wrapped destinations
     are handled. The bundle is validated as one self-contained tree (to validate
     federated content, assemble the bundles into one tree and point --bundle at
     that root).
  5. No file leaks a secret VALUE (private-key blocks, cloud API tokens,
     secret=<blob> assignments). Credential concepts document key NAMES and
     paths, never the values. Heuristic; narrow a pattern if it false-positives,
     do not delete the rule.

Exits non-zero on any hard failure.
Usage: python3 validate.py --bundle DIR
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

REQUIRED_KEYS = ("type", "title", "description", "source", "verified", "timestamp", "tags")
LIST_KEYS = ("source", "tags")
DATE_KEYS = ("verified", "timestamp")
ALLOWED_TYPES = {
    # Infrastructure / ops (fleet maps, system docs)
    "Machine", "Network", "Service", "Session", "Project",
    "Repo", "Credential", "Path", "Process",
    # Domain-neutral (newsrooms, research atlases, decision logs)
    "Concept", "Decision", "Event", "Person", "Org", "Source",
    # Catch-all
    "Reference",
}
RESERVED = {"index.md", "log.md"}
# okf_version values this validator accepts. The last entry is the current format
# version (what scaffold writes for a new bundle); older entries stay supported so a
# newer validator still reads an older bundle. Adding allowed types is backward
# compatible and bumps the format version (0.1 -> 0.2).
SUPPORTED_VERSIONS = ("0.1", "0.2")
SPEC_VERSION = SUPPORTED_VERSIONS[-1]  # current format version, written by new scaffolds
# Inline markdown link. The destination group allows one level of balanced
# parens so a filename like `missing(v2).md` is still captured (a plain [^)]+
# would stop at the first ')' and skip the link entirely).
LINK_RE = re.compile(r"\[[^\]]*\]\(((?:[^()]|\([^()]*\))*)\)")
# OKF links are relative markdown links only. The [[slug]] wikilink idiom (from the
# auto-memory system) is not OKF, so a typo'd or deleted [[ref]] would otherwise pass
# the link check unseen. It is reported as an error. Checked against strip_code output,
# so a [[x]] shown inside a code fence is illustrative, not flagged.
WIKILINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")

# Secret-value detectors. These match credential VALUES, not the key names/paths
# a credential concept is allowed to document. The generic assignment pattern
# requires a separator (`:`/`=`) directly before a high-entropy blob, so a
# documented key name like `service/api/...-secret` does not trip it.
SECRET_PATTERNS = [
    ("Tailscale key", re.compile(r"tskey-(?:api|auth|client)-[A-Za-z0-9]+-[A-Za-z0-9]{10,}")),
    ("private-key block", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[0-9A-Za-z]{36,}\b")),
    ("GitHub fine-grained PAT", re.compile(r"\bgithub_pat_[0-9A-Za-z_]{22,}\b")),
    ("secret assignment", re.compile(
        r"(?i)(?:password|passwd|secret|api[_-]?key|apikey|client[_-]?secret|access[_-]?token|auth[_-]?token)"
        # Base64-standard value charset only -- deliberately excludes - and _. A
        # credential concept documents key paths like `secret: svc/api/prod-key-path`,
        # and a hyphen/underscore-rich path must not read as a high-entropy value.
        # Structured tokens that use -/_ (fine-grained PATs, Slack, etc.) have their
        # own specific patterns above.
        r"\s*[:=]\s*['\"]?[A-Za-z0-9+/]{24,}['\"]?")),
]


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


def parse_frontmatter(text: str):
    """Return (frontmatter_dict_or_None, body). Raises yaml.YAMLError on bad YAML."""
    if not text.startswith("---"):
        return None, text
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def frontmatter_block(text: str) -> str | None:
    """Return the raw YAML frontmatter text (between the --- fences), or None. Used to
    enforce rules on the source text before YAML strips comments (see
    check_source_quoting)."""
    if not text.startswith("---"):
        return None
    m = FRONTMATTER_RE.match(text)
    return m.group(1) if m else None


def link_destination(raw: str) -> str:
    """Pull the destination out of a markdown link's (...) contents: strip <...>
    wrapping, an optional "title"/'title', and any #anchor. Markdown allows
    [text](dest "title") and [text](<dest with spaces>) — treating the whole
    contents as the path would falsely flag those as dangling."""
    s = raw.strip()
    if s.startswith("<"):
        end = s.find(">")
        if end != -1:
            return s[1:end].split("#", 1)[0].strip()
    s = s.split(None, 1)[0] if s else s  # dest ends at first space; rest is a title
    return s.split("#", 1)[0]


def resolve_link(target: str, md_file: Path) -> Path:
    """Resolve a relative link destination against the file's directory.
    .resolve() collapses ../ so the bundle-boundary check is not fooled by a path
    like ../../outside.md."""
    return (md_file.parent / target).resolve()


def strip_code(text: str) -> str:
    """Blank out fenced code blocks and inline code spans so a link shown as an
    example (e.g. a ```md fence containing [x](sample.md)) is not mistaken for a
    real bundle link. The secret scan still runs on the raw text — a secret in a
    code block is still a leak.

    Heuristic, not a full CommonMark parser: it handles ```/~~~ fences (matching
    the closing fence's char and length, so a longer fence can wrap a shorter one)
    and backtick-run inline spans (``code with a ` inside``). Rare forms — 4-space
    indented code blocks, code spans spanning lines — are out of scope; an OKF
    concept that needs those can wrap the example in a fence."""
    out = []
    fence = None  # (char, length) of the open fence, or None
    for line in text.splitlines():
        stripped = line.lstrip()
        if fence is None:
            m = re.match(r"(`{3,}|~{3,})", stripped)
            if m:
                fence = (stripped[0], len(m.group(1)))
                out.append("")
            else:
                out.append(re.sub(r"(`+)(.+?)\1", "", line))  # drop inline code spans
        else:
            ch, length = fence
            m = re.match(r"(`{3,}|~{3,})\s*$", stripped)
            if m and stripped[0] == ch and len(m.group(1)) >= length:
                fence = None
            out.append("")
    return "\n".join(out)


SOURCE_KEY_RE = re.compile(r"^source\s*:(.*)$")  # top-level (column 0) only


def _strip_source_structure(line, is_key_line):
    """Reduce a source-region line to its raw element text: drop indentation and YAML
    structure — the `source:` key on the first line, leading block '-' markers, and a
    leading flow '['. What remains is scanned for an inline comment."""
    s = SOURCE_KEY_RE.match(line).group(1) if is_key_line else line
    s = s.strip()
    while s.startswith("-"):
        s = s[1:].lstrip()
    return s.lstrip("[")


# A YAML inline comment drops no data when it follows a value that already closed -- a
# quote, a flow bracket/brace, or a separator. It truncates data only when it interrupts
# an unquoted scalar, where the char before it is ordinary content.
_VALUE_COMPLETE = {'"', "'", "]", "}", "[", "{", ","}
# A quote opens a quoted scalar only at a value boundary -- the start of the value or
# right after a flow opener/separator. Elsewhere (e.g. the apostrophe in "Joe's") it is a
# literal character inside a plain scalar.
_SCALAR_OPENERS = {"[", "{", ","}


def _has_truncating_comment(text):
    """True if `text` holds a YAML inline comment that truncates content: a whitespace-
    preceded, unquoted '#' that interrupts an unquoted scalar. Quote-aware (a '#' inside
    '...'/"..." is protected) and structure-aware: a comment after a completed value
    (`["a"] # why`, `- "a" # note`) or a whole-line comment drops no data and is not
    flagged. A quote is only treated as a string delimiter at a value boundary, so a
    plain scalar with an inner apostrophe (`Joe's issue #445`) is still scanned and its
    truncating '#' caught. The first such '#' decides the line — in YAML everything after
    it is the comment."""
    in_single = in_double = False
    seen_content = False
    last_nonspace = ""
    prev = ""
    for ch in text:
        if in_single:
            if ch == "'":
                in_single = False
            last_nonspace = ch
        elif in_double:
            if ch == '"':
                in_double = False
            last_nonspace = ch
        elif ch == "#" and prev in (" ", "\t"):
            # YAML comment start. Data is lost only if it cut into an unquoted scalar.
            return seen_content and last_nonspace not in _VALUE_COMPLETE
        elif ch in ("'", '"') and (not seen_content or last_nonspace in _SCALAR_OPENERS):
            if ch == "'":
                in_single = True
            else:
                in_double = True
            seen_content = True
            last_nonspace = ch
        elif not ch.isspace():
            seen_content = True
            last_nonspace = ch
        prev = ch
    return False


def check_source_quoting(rel, raw_fm, errors):
    """Enforce the SPEC 'source' quoting rule on the raw frontmatter, where YAML's
    comment stripping would otherwise silently drop part of a provenance pointer.

    Quoting source elements is a hard SPEC rule, but YAML drops an unquoted inline '#'
    comment with no error: `- issue #445` parses to "issue", losing "#445". The parsed
    value cannot reveal the loss, so this scans the raw text of the top-level `source`
    value for an unquoted, content-truncating '#'. It covers every list shape — block
    items, single- and multi-line flow lists, and wrapped plain scalars — because in all
    of them such a '#' means dropped data. It is quote-aware (a '#' inside quotes is
    fine) and scoped to the top-level `source` key only: a nested `source:` inside other
    allowed metadata is not the OKF provenance list and must not trip the check. Every
    top-level `source` occurrence is scanned, not just the first: YAML keeps the last of
    duplicate keys, so a later one is the value that actually parsed. A bare '#'-first
    item (null) and a colon-space mapping item are left to check_lists."""
    if not raw_fm:
        return
    lines = raw_fm.splitlines()
    starts = [i for i, ln in enumerate(lines) if SOURCE_KEY_RE.match(ln)]
    # absence of source is reported by the required-key check; nothing to scan here
    for start in starts:
        # The source value region: the key line plus following blank, indented, or
        # block-item ('-') lines, up to the next top-level key. This spans block lists,
        # multi-line flow lists, and wrapped scalars without re-parsing YAML.
        region = [lines[start]]
        for ln in lines[start + 1:]:
            if ln.strip() == "" or ln[:1].isspace() or ln.lstrip().startswith("-"):
                region.append(ln)
            else:
                break
        for idx, ln in enumerate(region):
            if _has_truncating_comment(_strip_source_structure(ln, idx == 0)):
                errors.append(
                    f"{rel}: a top-level 'source' element has an unquoted '#' that YAML "
                    f"reads as a comment, dropping the rest of the pointer — quote each "
                    f"source element that contains a '#'")
                return  # one report per concept is enough


def check_dates(rel, fm, errors):
    for key in DATE_KEYS:
        val = fm.get(key)
        if val is None:
            continue  # missing/empty already reported by required-key check
        s = val.isoformat() if isinstance(val, dt.date) else str(val)
        try:
            dt.datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            errors.append(f"{rel}: '{key}' must be an ISO date YYYY-MM-DD, got {val!r}")


def check_lists(rel, fm, errors):
    for key in LIST_KEYS:
        val = fm.get(key)
        if val is None:
            continue  # required-key check handles absence
        if not isinstance(val, list):
            errors.append(f"{rel}: '{key}' must be a YAML list, got {type(val).__name__}")
            continue
        if key == "source" and not val:
            errors.append(f"{rel}: 'source' must be a non-empty list of provenance pointers")
        for el in val:
            if not isinstance(el, str) or not el.strip():
                errors.append(f"{rel}: '{key}' has a non-string/empty element {el!r}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", default="bundle", help="path to the OKF bundle directory (default: bundle)")
    args = ap.parse_args()
    bundle = Path(args.bundle).resolve()

    if not bundle.exists():
        print(f"FAIL: bundle not found at {bundle}")
        return 1
    if not bundle.is_dir():
        print(f"FAIL: bundle path is not a directory: {bundle}")
        return 1

    # Discover markdown files case-insensitively (suffix .lower() == ".md") so a
    # non-conforming Foo.MD cannot hide from validation behind a case-sensitive glob;
    # it is found here and rejected below. rglob("*") also yields a directory named
    # like "archive.md"; reading one raises IsADirectoryError, so keep only real files
    # and report any .md-suffixed path that is a directory rather than crashing.
    md_entries = sorted(p for p in bundle.rglob("*") if p.suffix.lower() == ".md")
    md_files = [p for p in md_entries if p.is_file()]
    errors: list[str] = [
        f"{p.relative_to(bundle)}: a '*.md' path must be a file, not a directory"
        for p in md_entries if not p.is_file()
    ]
    # A bundle must have a root index.md. The okf_version gate below only runs when
    # that file exists, so without this check a bundle that simply omits the root
    # index (or an empty directory) would validate clean and bypass version gating.
    if not (bundle / "index.md").is_file():
        errors.append("index.md: bundle-root index is required and must declare okf_version")
    type_counts: Counter = Counter()
    concepts = 0

    for f in md_files:
        rel = f.relative_to(bundle)
        # utf-8-sig strips a leading byte-order mark if present. A BOM (common from
        # Windows editors) would otherwise defeat the startswith("---") frontmatter
        # check, reporting valid frontmatter as missing.
        text = f.read_text(encoding="utf-8-sig")

        # secret scan on every file, including index.md and a non-conforming Foo.MD
        # (a leak is a leak regardless of extension — scan before rejecting below).
        for label, pat in SECRET_PATTERNS:
            if pat.search(text):
                errors.append(
                    f"{rel}: possible secret leak ({label}) — remove the value, "
                    f"document the key name/path instead")

        # OKF concept and index files use a lowercase .md extension. A non-lowercase
        # extension (Foo.MD) is non-conforming: it was discovered case-insensitively
        # above so its content is still secret-scanned, then rejected here instead of
        # validated as a concept. With the case-insensitive link check below, this
        # closes the bypass where an uppercase-extension file and links to it both
        # escaped validation.
        if f.suffix != ".md":
            errors.append(
                f"{rel}: non-conforming filename — OKF concept files use a lowercase "
                f"'.md' extension, found {f.suffix!r}; rename it to .md")
            continue

        try:
            fm, body = parse_frontmatter(text)
        except (yaml.YAMLError, ValueError) as e:
            # ValueError covers a date-shaped scalar PyYAML auto-constructs and
            # rejects (e.g. an invalid month), which is not a YAMLError subclass.
            errors.append(
                f"{rel}: YAML frontmatter parse error ({e.__class__.__name__}: {e}) — "
                f"quote any string field that holds a YAML-significant character. "
                f"Common triggers: a colon-space (': ') anywhere in description, title, "
                f"or a source element; a bare '#' in a source element; an invalid date "
                f"in verified/timestamp.")
            continue

        # Past this point fm is either None or a mapping. Syntactically valid YAML
        # that is a list/scalar (e.g. a stray top-level list) would otherwise crash
        # the later fm.get(...) calls; report it as a clean failure instead.
        if fm is not None and not isinstance(fm, dict):
            errors.append(f"{rel}: frontmatter must be a YAML mapping, got {type(fm).__name__}")
            continue

        if f.name in RESERVED:
            if str(rel) == "index.md":
                # the bundle-root index.md may carry frontmatter, but only the
                # okf_version marker — never concept metadata or stray keys.
                keys = set(fm) if fm else set()
                if "okf_version" not in keys:
                    errors.append("index.md: bundle-root index must declare okf_version in frontmatter")
                else:
                    version = str(fm.get("okf_version")).strip()
                    if version not in SUPPORTED_VERSIONS:
                        errors.append(
                            f"index.md: okf_version {fm.get('okf_version')!r} is not supported "
                            f"(this validator supports {', '.join(SUPPORTED_VERSIONS)})")
                extra = sorted(keys - {"okf_version"})
                if extra:
                    errors.append(f"index.md: bundle-root index may carry only okf_version, found {extra}")
            elif fm is not None:
                # any other reserved file (subdir index.md, log.md) carries no frontmatter.
                errors.append(f"{rel}: reserved file should not carry frontmatter")
            continue

        if fm is None:
            errors.append(f"{rel}: missing YAML frontmatter")
            continue

        concepts += 1
        ctype = fm.get("type", "<none>")
        # type must be a scalar string. A list/dict (a plausible YAML typo like
        # `type: [Reference]`) is unhashable and would crash both the Counter
        # increment and the `in ALLOWED_TYPES` membership test, so report it and
        # fall back to "<none>" to keep the rest of this concept's checks running.
        if not isinstance(ctype, str):
            errors.append(f"{rel}: 'type' must be a string, got {type(ctype).__name__}")
            ctype = "<none>"
        type_counts[ctype] += 1

        for key in REQUIRED_KEYS:
            val = fm.get(key)
            if val is None or (isinstance(val, str) and not val.strip()):
                errors.append(f"{rel}: missing/empty required frontmatter key '{key}'")

        if ctype not in ALLOWED_TYPES and ctype != "<none>":
            errors.append(f"{rel}: type '{ctype}' not in the spec vocab {sorted(ALLOWED_TYPES)}")

        check_lists(rel, fm, errors)
        check_dates(rel, fm, errors)
        check_source_quoting(rel, frontmatter_block(text), errors)

    # Link resolution: every internal link to a .md file must resolve to a file
    # that exists inside the bundle. A link escaping the bundle root or pointing at
    # a missing file is a hard failure — the bundle is validated as one
    # self-contained tree. To validate federated content, assemble the bundles into
    # a single tree and point --bundle at that root.
    for f in md_files:
        if f.suffix != ".md":
            continue  # non-conforming file already reported; don't pile on link errors
        text = strip_code(f.read_text(encoding="utf-8-sig"))
        for m in WIKILINK_RE.finditer(text):
            slug = m.group(1).strip()
            errors.append(
                f"{f.relative_to(bundle)}: '[[{slug}]]' is not an OKF link — use a "
                f"relative markdown link like [text]({slug}.md). The [[slug]] form is "
                f"the auto-memory convention, not OKF.")
        for raw in LINK_RE.findall(text):
            target = link_destination(raw)
            if not target:
                continue
            low = target.lower()
            # External/anchor links are out of scope. Lower-case the scheme test so an
            # uppercase scheme (HTTPS://...) is still recognized and skipped, not
            # resolved as a local path (which would falsely fail as escaping/dangling).
            if low.startswith(("http://", "https://", "mailto:", "#", "tel:")):
                continue
            # Match .md case-insensitively, the same way discovery now does, so a link
            # to an uppercase-extension file (ghost.MD) is checked for dangling/escape
            # instead of silently skipped. If such a target file exists it is separately
            # rejected as non-conforming above, so the two checks stay in agreement.
            if ".md" not in low:
                continue
            if target.startswith("/"):
                errors.append(f"{f.relative_to(bundle)}: root-relative link not allowed "
                              f"(use a relative path) -> {target}")
                continue
            dest = resolve_link(target, f)
            inside = dest == bundle or bundle in dest.parents
            if not inside:
                errors.append(f"{f.relative_to(bundle)}: link escapes bundle root -> {target}")
            elif not dest.exists():
                errors.append(f"{f.relative_to(bundle)}: dangling link -> {target}")

    # report
    print(f"Bundle: {bundle}")
    print(f"Markdown files: {len(md_files)}  |  concepts: {concepts}")
    print("Concept types: " + ", ".join(f"{t}={n}" for t, n in type_counts.most_common()))
    if errors:
        print(f"\nFAIL: {len(errors)} problem(s):")
        for e in errors[:60]:
            print(f"  - {e}")
        if len(errors) > 60:
            print(f"  ... and {len(errors) - 60} more")
        return 1
    print("\nPASS: bundle conforms to OKF spec v1 "
          "(schema, dates, lists, links, secret scan).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
