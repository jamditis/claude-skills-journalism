#!/usr/bin/env python3
"""Validate an OKF (Open Knowledge Format) bundle against OKF spec v1 (see SPEC.md).

An OKF bundle is a tree of small markdown files: one concept per file, each with
YAML frontmatter carrying its provenance. Directory `index.md` files provide
navigation. This validator enforces the contract so a bundle stays machine- and
agent-readable.

Checks:
  1. Every non-reserved .md file has a parseable YAML frontmatter block. A YAML
     parse error is reported (commonly an unquoted colon-space or '#' in a
     string field, quote the value).
  2. Frontmatter carries every required key, non-empty. Through okf_version 0.3:
     type, title, description, source, verified, timestamp, tags. At 0.4:
     the same list with 'verified' renamed to 'verified_on' (see #6).
       - type     is one of the spec type vocab.
       - source   is a non-empty list of non-empty strings (provenance pointers).
                  An unquoted '#' in a block-style element (which YAML would silently
                  drop as a comment, losing the rest) is rejected, quote it.
       - tags     is a list.
       - verified/verified_on parses as an ISO date (YYYY-MM-DD).
       - timestamp parses as an ISO date, or under okf_version 0.3+ as a full
                    ISO 8601 datetime (upstream OKF writes a datetime).
  3. Reserved filenames (index.md, log.md) name no concept and carry no
     frontmatter, except the bundle-root index.md may carry okf_version only.
  4. Internal markdown links resolve. Links must be relative, a root-relative
     ('/'-prefixed) link is rejected. Every link to a .md file inside the bundle
     must point at a file that exists, with the case it has on disk (a
     case-insensitive filesystem would otherwise let a wrong-case link pass on
     macOS and dangle on Linux; see real_case_path for why a Windows author is
     not covered); a link that escapes the bundle root or dangles is a hard
     failure. Optional link titles and <>-wrapped destinations
     are handled. The bundle is validated as one self-contained tree (to validate
     federated content, assemble the bundles into one tree and point --bundle at
     that root).
  5. No file leaks a secret VALUE (private-key blocks, cloud API tokens,
     secret=<blob> assignments). Credential concepts document key NAMES and
     paths, never the values. Heuristic; narrow a pattern if it false-positives,
     do not delete the rule.
  6. At okf_version 0.4, optional upstream-v0.2 trust/provenance fields are
     checked for shape when present (never required): 'generated' ({by, at});
     the new 'verified' (a list of {by, at} confirmations, distinct from the
     required 'verified_on' at that version); 'sources' (plural; structured
     provenance objects, distinct from the required singular 'source'); 'status'
     (draft/stable/deprecated); 'stale_after' (an ISO date). A concept typed
     'Attested Computation' additionally requires 'runtime', 'parameters',
     'executor', and 'attester' to be present and correctly shaped.

Exits non-zero on any hard failure.
Usage: python3 validate.py --bundle DIR
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

REQUIRED_KEYS_LEGACY = ("type", "title", "description", "source", "verified", "timestamp", "tags")
# At TRUST_SIGNALS_VERSION, 'verified' is renamed to 'verified_on' in the required
# set -- it frees the bare name 'verified' for upstream v0.2's own optional field (a
# list of {by, at} confirmations; see check_verified_trust), which is a different
# shape and would otherwise collide with this fork's older single-date field.
REQUIRED_KEYS_V04 = ("type", "title", "description", "source", "verified_on", "timestamp", "tags")
LIST_KEYS = ("source", "tags")
# Keys that may also carry a full ISO 8601 datetime (see check_dates). The
# bundle must explicitly opt into this grammar through okf_version 0.3 so an
# older validator rejects the format at its version gate instead of later on a
# timestamp it does not understand.
DATETIME_KEYS = ("timestamp",)
DATETIME_TIMESTAMP_VERSION = "0.3"
# The version at which 'verified' is renamed to 'verified_on' and the optional
# upstream-v0.2 trust/provenance fields (generated, verified, sources, status,
# stale_after, Attested Computation) become available. See REQUIRED_KEYS_V04 above
# and SPEC.md's "Trust and provenance (upstream v0.2 vocabulary)" section.
TRUST_SIGNALS_VERSION = "0.4"
LEGACY_ALLOWED_TYPES = {
    # Infrastructure / ops (fleet maps, system docs)
    "Machine", "Network", "Service", "Session", "Project",
    "Repo", "Credential", "Path", "Process",
    # Domain-neutral (newsrooms, research atlases, decision logs)
    "Concept", "Decision", "Event", "Person", "Org", "Source",
    # Catch-all
    "Reference",
}
TRUST_SIGNAL_TYPES = {
    # Upstream v0.2: a sanctioned computation plus how to check a run of it
    # (see check_attested_computation). Kept as the literal upstream spelling
    # (with a space), not renamed to fit a no-space convention.
    "Attested Computation",
}
ALLOWED_TYPES = LEGACY_ALLOWED_TYPES | TRUST_SIGNAL_TYPES
ALLOWED_STATUSES = {"draft", "stable", "deprecated"}
RESERVED = {"index.md", "log.md"}
# okf_version values this validator accepts. The last entry is the current format
# version, but it is opt-in, not the scaffold default -- scaffold.py still writes
# "0.3" unless --trust-signals asks for "0.4" (see scaffold.py's own default).
# Older entries stay supported so a newer validator still reads an older bundle.
# Adding allowed types is backward compatible and bumps the format version
# (0.1 -> 0.2). Accepting a datetime in timestamp changes the field grammar and
# bumps it again (0.2 -> 0.3). Renaming 'verified' to 'verified_on' and adopting
# the optional upstream-v0.2 trust fields bumps it once more (0.3 -> 0.4).
SUPPORTED_VERSIONS = ("0.1", "0.2", DATETIME_TIMESTAMP_VERSION, TRUST_SIGNALS_VERSION)
SPEC_VERSION = SUPPORTED_VERSIONS[-1]  # current (opt-in) format version -- see note above


def required_keys_for(bundle_version):
    """The required-key tuple for a declared okf_version.

    Only TRUST_SIGNALS_VERSION ("0.4") renames 'verified' to 'verified_on'; every
    other declared (or missing/unsupported) version keeps the legacy name, so an
    unsupported-version bundle is still checked against a sensible required set
    instead of crashing before the version-gate error is reported.
    """
    return REQUIRED_KEYS_V04 if bundle_version == TRUST_SIGNALS_VERSION else REQUIRED_KEYS_LEGACY


def allowed_types_for(bundle_version):
    """The closed type vocabulary for a declared okf_version."""
    return ALLOWED_TYPES if bundle_version == TRUST_SIGNALS_VERSION else LEGACY_ALLOWED_TYPES


def date_keys_for(bundle_version):
    """The date-checked key names for a declared okf_version (see required_keys_for)."""
    return ("verified_on", "timestamp") if bundle_version == TRUST_SIGNALS_VERSION else ("verified", "timestamp")


def supports_datetime_timestamp(bundle_version):
    """Whether a supported bundle version carries full timestamp precision."""
    try:
        return (
            SUPPORTED_VERSIONS.index(bundle_version)
            >= SUPPORTED_VERSIONS.index(DATETIME_TIMESTAMP_VERSION)
        )
    except ValueError:
        return False


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
#
# The key labels that mark a value as a credential, shared by the generic base64
# assignment pattern and the opt-in entropy scan so the two agree on what counts
# as a labeled secret.
SECRET_LABEL = (
    r"(?:password|passwd|secret|api[_-]?key|apikey|client[_-]?secret"
    r"|access[_-]?token|auth[_-]?token)")

SECRET_PATTERNS = [
    ("Tailscale key", re.compile(r"tskey-(?:api|auth|client)-[A-Za-z0-9]+-[A-Za-z0-9]{10,}")),
    ("private-key block", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[0-9A-Za-z]{36,}\b")),
    ("GitHub fine-grained PAT", re.compile(r"\bgithub_pat_[0-9A-Za-z_]{22,}\b")),
    # More provider tokens with fixed literal prefixes and exact or narrow shapes.
    # Providers whose token bodies allow path-like hyphens and underscores use the
    # entropy-gated patterns below instead.
    ("Stripe secret key", re.compile(r"\b[sr]k_(?:live|test)_[0-9A-Za-z]{24,}\b")),
    ("Stripe organization key", re.compile(r"\bsk_org_[0-9A-Za-z]{24,}\b")),
    ("Stripe webhook secret", re.compile(r"\bwhsec_[0-9A-Za-z]{32,}\b")),
    # GitLab documents this exact cookie label as a token prefix. Keep the value
    # shape narrow enough that its `_gitlab_session=...` documentation placeholder
    # stays clean while an actual serialized cookie is caught.
    ("GitLab session cookie", re.compile(
        r"(?i)\b_gitlab_session\s*=\s*['\"]?"
        r"[0-9A-Za-z%+/_=-]{20,}(?![0-9A-Za-z%+/_=.\-])")),
    ("npm token", re.compile(r"\bnpm_[0-9A-Za-z]{36}\b")),
    ("SendGrid API key", re.compile(r"\bSG\.[0-9A-Za-z_-]{22}\.[0-9A-Za-z_-]{43}")),
    # Legacy personal OpenAI keys carry no project/service segment. `sk-` alone is a
    # weak prefix, so the 40-char solid-base62 run does the signal work; it stays
    # disjoint from the entropy-gated project-key detector below, whose `-` breaks
    # the run.
    ("OpenAI legacy key", re.compile(r"\bsk-[0-9A-Za-z]{40,}\b")),
    ("secret assignment", re.compile(
        r"(?i)" + SECRET_LABEL +
        # Base64-standard value charset only -- deliberately excludes - and _. A
        # credential concept documents key paths like `secret: svc/api/prod-key-path`,
        # and a hyphen/underscore-rich path must not read as a high-entropy value.
        # Structured tokens that use -/_ (fine-grained PATs, Slack, etc.) have their
        # own specific patterns above; the opt-in entropy scan below covers the rest.
        r"\s*[:=]\s*['\"]?[A-Za-z0-9+/]{24,}['\"]?")),
]

# Some provider token bodies allow the same hyphens and underscores used in
# human-readable vault paths. A prefix alone would therefore flag documentation
# such as `openai/sk-proj-production-primary-key-path`. These patterns capture a
# complete base64url-like body. They still run by default because the provider
# prefix is strong, but the entropy gate keeps path documentation clean. OpenAI
# and Anthropic use the generic 4.0 bits/character floor. GitLab accepts 20-char
# bodies, whose repeated characters lower their observable entropy; its narrower
# floor is 88% of the maximum entropy observable at the captured body length,
# capped at 4.0. That is 3.80 bits/character at 20 chars and rises to 4.0 at 24,
# so short tokens are not judged against a longer sample's ceiling while the
# longer path regressions stay clean.
#
# GitLab prefixes are from its token overview (checked 2026-07-23):
# https://docs.gitlab.com/security/tokens/#token-prefixes
PREFIXED_SECRET_PATTERNS = [
    ("GitLab token", re.compile(
        r"\b(?:glpat|gloas|gldt|glrtr?|glcbt|glptt|glft|glimt|glagent|glwt"
        r"|glsoat|glffct)-([0-9A-Za-z_-]{20,})(?![0-9A-Za-z_/-])"), 0.88),
    ("Anthropic API key", re.compile(
        r"\bsk-ant-([0-9A-Za-z_-]{20,})(?![0-9A-Za-z_/-])"), 1.0),
    ("OpenAI project key", re.compile(
        r"\bsk-(?:proj|svcacct)-([0-9A-Za-z_-]{20,})(?![0-9A-Za-z_/-])"), 1.0),
]

# Opt-in entropy scan (--secret-entropy-scan). The generic assignment pattern
# above uses a base64-standard value charset that excludes - and _, so a labeled
# secret whose value is URL-safe (base64url: - _ =) slips past it. Widening that
# charset would re-flag OKF key paths like `secret: svc/api/prod-key-path`, the
# precision an earlier review round asked us to keep. This optional pass instead
# matches only the base64url charset -- base64-standard values with `/` stay the
# generic pattern's job -- and keeps precision two ways. Structurally (the primary
# guard), the captured run must be a complete token: the trailing lookahead rejects
# a run that is followed by another value char (we truncated a longer token) or a
# `/` (it is a path segment, not a standalone value), so a documented key path like
# `secret: prd-usw2-...-key-path/service` cannot leak its first segment as a value.
# Excluding `/` from the class alone did not do this -- it stopped the match at the
# separator but still captured a >=24-char leading segment. Statistically, a
# Shannon-entropy floor backstops the slashless case: a random token scores above a
# short dictionary-and-separator name (measured: 24-char base64url secrets land
# ~4.05-4.4 bits/char, short human-readable names stay under 4.0). The floor is
# imperfect -- a long, varied slashless name can clear it, the acknowledged
# precision-for-recall tradeoff -- which is why the structural check, not this
# threshold, is the primary guard. It is off by default so a normal run keeps the
# narrow, zero-false-positive base64 behavior; the flag trades some precision for
# recall.
SECRET_ENTROPY_RE = re.compile(
    r"(?i)" + SECRET_LABEL + r"\s*[:=]\s*['\"]?([A-Za-z0-9_=-]{24,})"
    r"(?![A-Za-z0-9_=/-])['\"]?")
SECRET_ENTROPY_MIN_BITS = 4.0


def shannon_entropy(s: str) -> float:
    """Shannon entropy of s in bits per character (0.0 for the empty string)."""
    if not s:
        return 0.0
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in Counter(s).values())


def prefixed_secret_labels(text: str):
    """Yield each provider label with a complete, random-looking token body."""
    for label, pattern, max_entropy_fraction in PREFIXED_SECRET_PATTERNS:
        for match in pattern.finditer(text):
            body = match.group(1)
            # A sample of n characters cannot exhibit more than log2(n) bits of
            # entropy per character, even when every character is unique.
            min_entropy = min(
                SECRET_ENTROPY_MIN_BITS,
                max_entropy_fraction * math.log2(len(body)),
            )
            if shannon_entropy(body) >= min_entropy:
                yield label
                break


def entropy_secret_values(text: str):
    """Yield the labeled, high-entropy base64url values in text that the generic
    base64 pattern misses. A value must carry a base64url-only character (- _ =) --
    otherwise the generic pattern already covers it -- and clear the entropy floor,
    so a low-entropy hyphenated name is left alone."""
    for m in SECRET_ENTROPY_RE.finditer(text):
        value = m.group(1)
        if not any(ch in value for ch in "-_="):
            continue  # plain base64/alnum -- already covered by SECRET_PATTERNS
        if shannon_entropy(value) >= SECRET_ENTROPY_MIN_BITS:
            yield value


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


def link_destination(raw: str) -> tuple[str, str]:
    """Pull the path and fragment out of a markdown link's (...) contents: strip
    <...> wrapping and an optional "title"/'title'. Markdown allows
    [text](dest "title") and [text](<dest with spaces>), treating the whole
    contents as the path would falsely flag those as dangling."""
    s = raw.strip()
    if s.startswith("<"):
        end = s.find(">")
        if end != -1:
            destination = s[1:end].strip()
            path, separator, fragment = destination.partition("#")
            return path, separator + fragment
    s = s.split(None, 1)[0] if s else s  # dest ends at first space; rest is a title
    path, separator, fragment = s.partition("#")
    return path, separator + fragment


def resolve_link(target: str, md_file: Path) -> Path:
    """Resolve a relative link destination against the file's directory.
    .resolve() collapses ../ so the bundle-boundary check is not fooled by a path
    like ../../outside.md."""
    return (md_file.parent / target).resolve()


def real_case_path(
    dest: Path, bundle: Path, *, allow_nonconforming_md: bool = False
) -> Path | None:
    """The path on disk that `dest` names, ignoring case, or None if nothing matches.

    Returns `dest` unchanged when every component already matches the real name.

    Path.exists() asks the filesystem, and macOS answers yes for `Concepts/Foo.md`
    when the file is really `concepts/foo.md`. A bundle written there passes
    validation on the author's machine and dangles the first time Linux CI or a
    Linux reader opens it, which is the class of break this validator exists to
    catch before it ships. So walk the components against the real directory
    listings instead of asking whether the path exists.

    The walk doubles as the existence check: a component that matches nothing,
    case or no case, means the link dangles.

    This does not catch a Windows author, and a wrong-cased symlink component can
    escape the local check on case-insensitive macOS. In both cases Path.resolve()
    may replace the link's spelling with the on-disk target before the walk sees
    it. The wrong-case link is still caught later by Linux CI. Fixing it needs a
    lexically normalized path here, which is not the same as the resolved one
    across a symlinked directory, so it is tracked separately rather than bolted on.

    `dest` must be inside `bundle`; the caller checks that first.
    """
    current = bundle
    for part in dest.relative_to(bundle).parts:
        try:
            names = set(os.listdir(current))
        except OSError:
            return None  # not a directory, or unreadable: nothing below it resolves
        if part in names:
            current = current / part
            continue
        # Exactly one case-variant is a mismatch worth naming. Several means a
        # case-sensitive filesystem holding both, and no way to say which was meant.
        # Do not recommend a file with an uppercase .md extension as a link fix: that
        # filename is rejected elsewhere in this validator. The caller can opt into a
        # second lookup solely to give that non-conforming file a rename diagnostic.
        variants = [n for n in names if n.lower() == part.lower()]
        if not allow_nonconforming_md and Path(part).suffix.lower() == ".md":
            variants = [n for n in variants if Path(n).suffix == ".md"]
        if len(variants) != 1:
            return None
        current = current / variants[0]
    return current


def strip_code(text: str) -> str:
    """Blank out fenced code blocks and inline code spans so a link shown as an
    example (e.g. a ```md fence containing [x](sample.md)) is not mistaken for a
    real bundle link. The secret scan still runs on the raw text, a secret in a
    code block is still a leak.

    Heuristic, not a full CommonMark parser: it handles ```/~~~ fences (matching
    the closing fence's char and length, so a longer fence can wrap a shorter one)
    and backtick-run inline spans (``code with a ` inside``). Rare forms, 4-space
    indented code blocks, code spans spanning lines, are out of scope; an OKF
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


def _plain_scalar_dropped_comment(node, raw_fm):
    """True if a YAML comment directly truncated this scalar's provenance.

    `node` is a scalar node from the parsed frontmatter and `raw_fm` the raw text it was
    parsed from. Only a plain (unquoted) scalar can lose data: a quoted or block scalar
    (node.style set to ', ", |, or >) keeps a '#' as string content. For a plain scalar,
    YAML stops the value at the space before an inline '#', so the comment shows up in the
    raw text immediately after the scalar's end mark, on the same line. That is exactly the
    silent-truncation case (`issue #445` -> "issue") the SPEC quoting rule guards against;
    `issue#445` (no space) is one scalar and a '#' on a later line is a standalone comment,
    and neither trips this."""
    if node.style is not None:
        return False
    j = node.end_mark.index
    while j < len(raw_fm) and raw_fm[j] in (" ", "\t"):
        j += 1
    return j < len(raw_fm) and raw_fm[j] == "#"


# PyYAML resolves both `<<` and an explicit `!!merge` tag to this tag; a key carrying it is a
# merge directive regardless of how it is spelled, so it is never a real mapping key.
_MERGE_TAG = "tag:yaml.org,2002:merge"


def _child_ref_counts(root):
    """Map id(node) -> how many times it is referenced as a child across the tree.

    A YAML alias makes the composer reuse the anchor's node object, so an alias TARGET
    is the one node referenced 2+ times. Each unique node is traversed once (guarded by
    a seen set) so a recursive anchor cannot loop; references are still counted with
    multiplicity."""
    counts: dict[int, int] = {}
    seen: set[int] = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        children: list = []
        if isinstance(node, yaml.MappingNode):
            for k, v in node.value:
                children += (k, v)
        elif isinstance(node, yaml.SequenceNode):
            children += list(node.value)
        for c in children:
            counts[id(c)] = counts.get(id(c), 0) + 1
            stack.append(c)
    return counts


def _value_uses_alias(val_node, counts):
    """True if any node in this value's subtree is reached via a YAML alias.

    An alias target is the same node object referenced 2+ times in the whole frontmatter
    (counts), or reached twice while walking this one subtree (a cycle). An unused anchor
    is referenced once, so an anchored literal is not flagged, consistent with allowing
    `source: [&p "x"]`. Rejecting alias USES closes #169: an aliased scalar shares its
    anchor's position marks, so the end-mark quoting check cannot see a comment dropped
    after the alias."""
    seen: set[int] = set()
    stack = [val_node]
    while stack:
        node = stack.pop()
        if id(node) in seen:
            return True  # reached twice within source -> an alias points back into it
        seen.add(id(node))
        if counts.get(id(node), 0) >= 2:
            return True  # shared with another reference -> an alias target
        if isinstance(node, yaml.MappingNode):
            for k, v in node.value:
                stack += (k, v)
        elif isinstance(node, yaml.SequenceNode):
            stack += list(node.value)
    return False


def _mapping_yields_source(node, seen):
    """True if this mapping node's effective keys include 'source', counting keys reached
    through its own (possibly nested) merge keys.

    A merged mapping can itself merge in another mapping ('<<: *d' where d is '<<: {source:
    ...}'), so checking only the immediate keys misses a source that safe_load still
    materializes. Recurse through each merge key's mapping(s). The seen set guards a
    recursive anchor (&d {<<: *d}) from looping."""
    if not isinstance(node, yaml.MappingNode) or id(node) in seen:
        return False
    seen.add(id(node))
    for key, val in node.value:
        if not isinstance(key, yaml.ScalarNode):
            continue
        if key.tag == _MERGE_TAG:
            for merged in (val.value if isinstance(val, yaml.SequenceNode) else [val]):
                if _mapping_yields_source(merged, seen):
                    return True
        elif key.value == "source":
            return True
    return False


def _merge_supplies_source(root):
    """True if a top-level YAML merge key (<<) merges in a mapping that yields its own
    'source' key, directly or through a further nested merge.

    YAML lets a literal 'source:' override a merged one, so a source smuggled in through
    '<<: {source: ...}' (or a chain of merges that resolves to source) beside a literal is
    silently dropped and the top-level source-key scan (which keys on literal 'source'
    nodes) never sees it. A merge value is a mapping, or a sequence of mappings ('<<: [*a,
    *b]'); compose resolves an alias to the shared node, so an aliased merge map is a
    MappingNode here. Detecting it lets a merge-supplied source be rejected whether or not
    a literal source sits beside it."""
    for key, val in root.value:
        if not (isinstance(key, yaml.ScalarNode) and key.tag == _MERGE_TAG):
            continue
        for node in (val.value if isinstance(val, yaml.SequenceNode) else [val]):
            if _mapping_yields_source(node, set()):
                return True
    return False


def check_source_quoting(rel, fm, raw_fm, errors):
    """Enforce the SPEC 'source' quoting rule, where YAML's comment stripping would
    otherwise silently drop part of a provenance pointer.

    Quoting source elements is a hard SPEC rule, but YAML drops an unquoted inline '#'
    comment with no error: `- issue #445` parses to "issue", losing "#445". The parsed
    value alone cannot reveal the loss, so this re-parses the frontmatter into its node
    tree (which carries source position marks) and, for every top-level `source` element,
    checks whether a comment directly truncated a plain scalar (see
    _plain_scalar_dropped_comment). Delegating the lexing to YAML covers every shape,
    block items, single- and multi-line flow lists, wrapped scalars, quoted strings with
    escapes, anchors/tags, and block scalars, without re-implementing the parser. It is
    scoped to the top-level `source` key only (a nested `source:` under other metadata is
    not the OKF provenance list). A real parse error is reported by the schema check.

    `fm` is the safe_load result the caller already parsed. A `source` can enter it through
    a YAML merge key (`<<: {source: *r}`), a whole-node alias, an alias in key position, or a
    duplicate `source` key, each materializes the field, but YAML keeps the LAST of duplicate
    keys, so the value safe_load returns is not necessarily the first clean `source:` the scan
    finds. OKF source must be one literal top-level list, so this requires the effective source
    to come from exactly one literal, unshared `source:` key and rejects every indirection
    (merge, alias, duplicate) up front, which also keeps the node-tree quoting scan total."""
    if not raw_fm:
        return
    try:
        root = yaml.compose(raw_fm, Loader=yaml.SafeLoader)
    except yaml.YAMLError:
        return
    if not isinstance(root, yaml.MappingNode):
        return
    counts = _child_ref_counts(root)
    # YAML keeps the LAST of duplicate keys, so the value safe_load returns for `source` is
    # decided by the last top-level key that resolves to "source", not the first clean one.
    # Collect every such key. An alias in key position (`*k` resolving to "source") makes
    # compose reuse the anchor's node, so the key reads as a "source" scalar while the written
    # key is an alias, count >= 2 marks that sharing, so an aliased key is not unshared. A key
    # SPELLED "source" but carrying the explicit merge tag (`!!merge source:`) is a merge
    # directive, not a source key, PyYAML classifies merge by the tag, not the spelling, so
    # exclude it here: counting it would both falsely reject a file whose only real source is a
    # separate literal, and let a source merged in through it bypass the scan below.
    source_keys = [
        (k, v) for k, v in root.value
        if isinstance(k, yaml.ScalarNode) and k.value == "source"
        and k.tag != _MERGE_TAG
    ]
    unshared = [(k, v) for k, v in source_keys if counts.get(id(k), 0) < 2]
    if fm.get("source") is not None and (
        len(source_keys) != 1 or not unshared or _merge_supplies_source(root)
    ):
        errors.append(
            f"{rel}: 'source' is not a single literal top-level 'source:' key, it enters "
            f"through a YAML merge key (<<), an alias, or a duplicate 'source' key; OKF "
            f"'source' must be one literal top-level list of provenance pointers, declare "
            f"it directly instead of merging, aliasing, or duplicating it")
        return
    for key_node, val_node in source_keys:
        # A YAML anchor/alias that entangles source with the rest of the frontmatter
        # shares node identity and position marks, so the dropped-comment scan below
        # reads the anchor's definition line, not the use site, and can miss a truncated
        # pointer (#169). OKF source is a flat list of literal, self-contained pointers
        # anyway, so any anchor/alias SHARING is invalid here, reject it, which keeps the
        # quoting scan total. An unused anchor definition (`[&p "x"]`) shares nothing and
        # stays allowed.
        if _value_uses_alias(val_node, counts):
            errors.append(
                f"{rel}: a top-level 'source' value shares a YAML anchor/alias (& or *) "
                f"with the rest of the frontmatter; OKF 'source' must be a flat list of "
                f"literal provenance pointers, write each pointer out literally instead "
                f"of anchoring or aliasing it")
            return
        if isinstance(val_node, yaml.SequenceNode):
            scalars = [n for n in val_node.value if isinstance(n, yaml.ScalarNode)]
        elif isinstance(val_node, yaml.ScalarNode):
            scalars = [val_node]
        else:
            scalars = []
        if any(_plain_scalar_dropped_comment(n, raw_fm) for n in scalars):
            errors.append(
                f"{rel}: a top-level 'source' element has an unquoted '#' that YAML "
                f"reads as a comment, dropping the rest of the pointer, quote each "
                f"source element that contains a '#'")
            return  # one report per concept is enough


ISO_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
ISO_DATETIME_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:[.,][0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})?\Z"
)


def _is_iso_date(s):
    """True only for the literal YYYY-MM-DD form required by the SPEC."""
    if not ISO_DATE_RE.fullmatch(s):
        return False
    try:
        dt.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _is_iso_datetime(s):
    """True for the SPEC's full ISO 8601 datetime spelling.

    ``fromisoformat`` checks calendar and clock ranges, but it is deliberately
    not the lexical contract: both it and PyYAML accept wider timestamp forms.
    The regular expression first requires the exact zero-padded source shape.
    A trailing ``Z`` is normalised for Python versions that do not parse it.
    """
    if not ISO_DATETIME_RE.fullmatch(s):
        return False
    try:
        dt.datetime.fromisoformat(s[:-1] + "+00:00" if s.endswith("Z") else s)
    except ValueError:
        return False
    return True


def _literal_scalar_node(raw_fm, *path):
    """Return an unshared literal scalar node along a mapping/sequence path.

    String path components select the effective (last) literal mapping key;
    integer components index a sequence. Aliases are rejected because their
    source marks describe the anchor rather than the use site.
    """
    if not raw_fm or not path:
        return None
    try:
        root = yaml.compose(raw_fm, Loader=yaml.SafeLoader)
    except yaml.YAMLError:
        return None
    if not isinstance(root, yaml.MappingNode):
        return None

    counts = _child_ref_counts(root)
    node = root
    for component in path:
        if isinstance(component, str):
            if not isinstance(node, yaml.MappingNode):
                return None
            candidates = [
                (key_node, val_node)
                for key_node, val_node in node.value
                if isinstance(key_node, yaml.ScalarNode)
                and key_node.value == component
                and key_node.tag != _MERGE_TAG
                and counts.get(id(key_node), 0) < 2
            ]
            if not candidates:
                return None
            _, node = candidates[-1]  # safe_load keeps the last duplicate key
        elif isinstance(component, int):
            if (not isinstance(node, yaml.SequenceNode)
                    or component < 0
                    or component >= len(node.value)):
                return None
            node = node.value[component]
        else:
            return None
        if counts.get(id(node), 0) >= 2:
            return None

    return node if isinstance(node, yaml.ScalarNode) else None


def _raw_mapping_scalar(raw_fm, *path):
    """Return a literal scalar's unnormalised text along a node path, or None.

    ``safe_load`` constructs a broad family of YAML timestamp spellings as
    ``date``/``datetime`` objects. Calling ``isoformat`` on those objects would
    silently turn a malformed source spelling into a conforming value. Compose
    the same frontmatter into a node tree and inspect each effective (last)
    literal key along the path instead. Simple quoted strings remain supported;
    YAML aliases, tags, block scalars, and escape-based spellings are not literal
    date fields.
    """
    node = _literal_scalar_node(raw_fm, *path)
    if node is None:
        return None
    written = raw_fm[node.start_mark.index:node.end_mark.index]
    if node.style is None and written == node.value:
        return written
    if node.style in ("'", '"') and written == node.style + node.value + node.style:
        return node.value
    return None


def _mapping_scalar_dropped_comment(raw_fm, *path):
    """True when a literal scalar at path was truncated by a YAML comment."""
    node = _literal_scalar_node(raw_fm, *path)
    return node is not None and _plain_scalar_dropped_comment(node, raw_fm)


def _raw_top_level_scalar(raw_fm, key):
    """Return a literal top-level scalar's unnormalised text, or None."""
    return _raw_mapping_scalar(raw_fm, key)


def check_dates(rel, fm, raw_fm, bundle_version, errors):
    accepts_datetime = supports_datetime_timestamp(bundle_version)
    for key in date_keys_for(bundle_version):
        val = fm.get(key)
        if val is None:
            continue  # missing/empty already reported by required-key check
        raw = _raw_top_level_scalar(raw_fm, key)
        if raw is not None and _is_iso_date(raw):
            continue
        # `timestamp` is upstream OKF's key and upstream writes it as a full ISO
        # 8601 datetime. Version 0.3 and later accept and carry that precision;
        # older formats remain date-only. `verified` is this spec's own key and
        # always stays date-only because a time of day invites false precision.
        if (key in DATETIME_KEYS
                and accepts_datetime
                and raw is not None
                and _is_iso_datetime(raw)):
            continue
        if key in DATETIME_KEYS and not accepts_datetime:
            expected = (
                f"an ISO date YYYY-MM-DD under okf_version {bundle_version or '<missing>'}; "
                f"full ISO 8601 datetimes require okf_version {DATETIME_TIMESTAMP_VERSION}"
            )
        elif key in DATETIME_KEYS:
            expected = "an ISO date YYYY-MM-DD or a full ISO 8601 datetime"
        else:
            expected = "an ISO date YYYY-MM-DD"
        shown = raw if raw is not None else val
        errors.append(f"{rel}: '{key}' must be {expected}, got {shown!r}")


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


def check_generated(rel, fm, raw_fm, errors):
    """Optional upstream-v0.2 'generated' field: {by, at} -- who/what produced the
    current content and when."""
    if "generated" not in fm:
        return
    val = fm["generated"]
    if not isinstance(val, dict):
        errors.append(f"{rel}: 'generated' must be a mapping {{by, at}}, got {type(val).__name__}")
        return
    by = val.get("by")
    if not isinstance(by, str) or not by.strip():
        errors.append(f"{rel}: 'generated.by' must be a non-empty string")
    at = val.get("at")
    if at is None:
        errors.append(f"{rel}: 'generated.at' is required when 'generated' is present")
        return
    raw = _raw_mapping_scalar(raw_fm, "generated", "at")
    if raw is None or not (_is_iso_date(raw) or _is_iso_datetime(raw)):
        shown = raw if raw is not None else at
        errors.append(f"{rel}: 'generated.at' must be an ISO date or a full ISO 8601 datetime, got {shown!r}")


def check_verified_trust(rel, fm, raw_fm, bundle_version, errors):
    """Optional upstream-v0.2 'verified' field: a list of independent {by, at}
    confirmations, from which a consumer derives a trust tier (unverified /
    machine-confirmed / human-reviewed). Only meaningful at TRUST_SIGNALS_VERSION,
    where 'verified' is not the required key (see REQUIRED_KEYS_V04's
    'verified_on') -- at every earlier version 'verified' IS the required legacy
    single-date field, already checked by check_dates, so this must not also
    re-validate it there under the new shape."""
    if bundle_version != TRUST_SIGNALS_VERSION:
        return
    if "verified" not in fm:
        return  # optional; absence reads as "unverified" to a consumer, not an error
    val = fm["verified"]
    if not isinstance(val, list) or not val:
        errors.append(
            f"{rel}: 'verified' (trust confirmations) must be a non-empty YAML list "
            f"of {{by, at}} mappings when present, got {type(val).__name__}")
        return
    for i, entry in enumerate(val):
        if not isinstance(entry, dict):
            errors.append(f"{rel}: 'verified[{i}]' must be a mapping with 'by' and 'at', got {type(entry).__name__}")
            continue
        by = entry.get("by")
        if not isinstance(by, str) or not by.strip():
            errors.append(f"{rel}: 'verified[{i}].by' must be a non-empty string")
        at = entry.get("at")
        if at is None:
            errors.append(f"{rel}: 'verified[{i}].at' is required")
        else:
            raw = _raw_mapping_scalar(raw_fm, "verified", i, "at")
            if raw is None or not _is_iso_date(raw):
                shown = raw if raw is not None else at
                errors.append(
                    f"{rel}: 'verified[{i}].at' must be an ISO date YYYY-MM-DD, "
                    f"got {shown!r}")


def check_sources_plural(rel, fm, raw_fm, errors):
    """Optional upstream-v0.2 'sources' field (plural) -- structured provenance
    objects, distinct from the required singular 'source' (a flat list of quoted
    pointers). Each entry needs a unique 'id' and a 'resource'; title/author/
    usage_count/last_modified are optional credibility signals. Shape-checked
    only -- this does not cross-check in-body [^id] footnotes against these ids
    (see SPEC.md)."""
    if "sources" not in fm:
        return
    val = fm["sources"]
    if not isinstance(val, list) or not val:
        errors.append(
            f"{rel}: 'sources' must be a non-empty YAML list of provenance objects "
            f"when present, got {type(val).__name__}")
        return
    seen_ids = set()
    for i, entry in enumerate(val):
        if not isinstance(entry, dict):
            errors.append(f"{rel}: 'sources[{i}]' must be a mapping, got {type(entry).__name__}")
            continue
        sid = entry.get("id")
        if not isinstance(sid, str) or not sid.strip():
            errors.append(f"{rel}: 'sources[{i}].id' must be a non-empty string")
        elif sid in seen_ids:
            errors.append(
                f"{rel}: 'sources[{i}].id' {sid!r} duplicates an earlier entry -- "
                f"ids must be unique within 'sources'")
        else:
            seen_ids.add(sid)
        resource = entry.get("resource")
        if not isinstance(resource, str) or not resource.strip():
            errors.append(f"{rel}: 'sources[{i}].resource' must be a non-empty string")
        elif _mapping_scalar_dropped_comment(raw_fm, "sources", i, "resource"):
            errors.append(
                f"{rel}: 'sources[{i}].resource' has an unquoted '#' that YAML "
                f"reads as a comment, dropping the rest of the provenance pointer")
        for opt_key in ("title", "author"):
            v = entry.get(opt_key)
            if v is not None and (not isinstance(v, str) or not v.strip()):
                errors.append(f"{rel}: 'sources[{i}].{opt_key}' must be a non-empty string when present")
        uc = entry.get("usage_count")
        if uc is not None and (not isinstance(uc, int) or isinstance(uc, bool) or uc < 0):
            errors.append(f"{rel}: 'sources[{i}].usage_count' must be a non-negative integer when present, got {uc!r}")
        lm = entry.get("last_modified")
        if lm is not None:
            raw = _raw_mapping_scalar(raw_fm, "sources", i, "last_modified")
            if raw is None or not _is_iso_date(raw):
                shown = raw if raw is not None else lm
                errors.append(
                    f"{rel}: 'sources[{i}].last_modified' must be an ISO date "
                    f"YYYY-MM-DD when present, got {shown!r}")


def check_status(rel, fm, errors):
    """Optional upstream-v0.2 'status' field: draft/stable/deprecated. Absent means
    stable (nothing to check)."""
    if "status" not in fm:
        return
    val = fm["status"]
    if not isinstance(val, str) or val not in ALLOWED_STATUSES:
        errors.append(f"{rel}: 'status' must be one of {sorted(ALLOWED_STATUSES)} when present, got {val!r}")


def check_stale_after(rel, fm, raw_fm, errors):
    """Optional upstream-v0.2 'stale_after' field: an absolute ISO date, deliberately
    not a relative TTL (see SPEC.md)."""
    if "stale_after" not in fm:
        return
    val = fm["stale_after"]
    raw = _raw_mapping_scalar(raw_fm, "stale_after")
    if raw is None or not _is_iso_date(raw):
        shown = raw if raw is not None else val
        errors.append(
            f"{rel}: 'stale_after' must be an ISO date YYYY-MM-DD, got {shown!r}")


def check_attested_computation(rel, fm, errors):
    """Upstream-v0.2 'Attested Computation' type: a sanctioned computation plus the
    means to check that a run of it actually matches. Checks shape only -- this
    validator never executes the computation, the executor, or the attester; that
    is a consumer's runtime job (see SPEC.md)."""
    if fm.get("type") != "Attested Computation":
        return

    runtime = fm.get("runtime")
    if not isinstance(runtime, str) or not runtime.strip():
        errors.append(f"{rel}: 'Attested Computation' requires a non-empty 'runtime' string")

    params = fm.get("parameters")
    if not isinstance(params, list):
        errors.append(f"{rel}: 'Attested Computation' requires a 'parameters' list")
    else:
        for i, p in enumerate(params):
            if not isinstance(p, dict):
                errors.append(f"{rel}: 'parameters[{i}]' must be a mapping {{name, type, required}}, got {type(p).__name__}")
                continue
            extra = sorted(set(p) - {"name", "type", "required"})
            if extra:
                errors.append(f"{rel}: 'parameters[{i}]' has undeclared keys {extra}")
            for key in ("name", "type"):
                v = p.get(key)
                if not isinstance(v, str) or not v.strip():
                    errors.append(f"{rel}: 'parameters[{i}].{key}' must be a non-empty string")
            if not isinstance(p.get("required"), bool):
                errors.append(f"{rel}: 'parameters[{i}].required' must be true or false")

    executor = fm.get("executor")
    if not isinstance(executor, dict):
        errors.append(f"{rel}: 'Attested Computation' requires an 'executor' mapping {{resource, receipt}}")
    else:
        resource = executor.get("resource")
        if not isinstance(resource, str) or not resource.strip():
            errors.append(f"{rel}: 'executor.resource' must be a non-empty string")
        receipt = executor.get("receipt")
        if not isinstance(receipt, list) or not receipt or not all(
                isinstance(r, str) and r.strip() for r in receipt):
            errors.append(f"{rel}: 'executor.receipt' must be a non-empty list of non-empty strings")

    attester = fm.get("attester")
    if not isinstance(attester, dict):
        errors.append(f"{rel}: 'Attested Computation' requires an 'attester' mapping {{resource}}")
    else:
        resource = attester.get("resource")
        if not isinstance(resource, str) or not resource.strip():
            errors.append(f"{rel}: 'attester.resource' must be a non-empty string")


def declared_bundle_version(bundle):
    """Read the root marker for version-dependent field checks.

    This is a non-reporting pre-pass; the main file loop remains responsible for
    all root-index diagnostics. Reading it up front means a root-level concept
    named ``a.md`` receives the right grammar even though it sorts before
    ``index.md``.
    """
    root_index = bundle / "index.md"
    if not root_index.is_file():
        return None
    try:
        fm, _ = parse_frontmatter(root_index.read_text(encoding="utf-8-sig"))
    except (OSError, yaml.YAMLError, ValueError):
        return None
    if not isinstance(fm, dict) or fm.get("okf_version") is None:
        return None
    return str(fm["okf_version"]).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", default="bundle", help="path to the OKF bundle directory (default: bundle)")
    ap.add_argument(
        "--secret-entropy-scan", action="store_true",
        help="also flag a labeled URL-safe/base64url value whose Shannon entropy "
             "clears the secret floor (opt-in; trades some precision for recall on "
             "hyphenated secret values the base64 pattern misses)")
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
    bundle_version = declared_bundle_version(bundle)
    type_counts: Counter = Counter()
    concepts = 0

    for f in md_files:
        rel = f.relative_to(bundle)
        # utf-8-sig strips a leading byte-order mark if present. A BOM (common from
        # Windows editors) would otherwise defeat the startswith("---") frontmatter
        # check, reporting valid frontmatter as missing.
        text = f.read_text(encoding="utf-8-sig")

        # secret scan on every file, including index.md and a non-conforming Foo.MD
        # (a leak is a leak regardless of extension, scan before rejecting below).
        for label, pat in SECRET_PATTERNS:
            if pat.search(text):
                errors.append(
                    f"{rel}: possible secret leak ({label}), remove the value, "
                    f"document the key name/path instead")
        for label in prefixed_secret_labels(text):
            errors.append(
                f"{rel}: possible secret leak ({label}), remove the value, "
                f"document the key name/path instead")
        if args.secret_entropy_scan and next(entropy_secret_values(text), None):
            errors.append(
                f"{rel}: possible secret leak (high-entropy assignment flagged by "
                f"--secret-entropy-scan), remove the value, document the key "
                f"name/path instead")

        # OKF concept and index files use a lowercase .md extension. A non-lowercase
        # extension (Foo.MD) is non-conforming: it was discovered case-insensitively
        # above so its content is still secret-scanned, then rejected here instead of
        # validated as a concept. With the case-insensitive link check below, this
        # closes the bypass where an uppercase-extension file and links to it both
        # escaped validation.
        if f.suffix != ".md":
            errors.append(
                f"{rel}: non-conforming filename, OKF concept files use a lowercase "
                f"'.md' extension, found {f.suffix!r}; rename it to .md")
            continue

        try:
            fm, body = parse_frontmatter(text)
        except (yaml.YAMLError, ValueError) as e:
            # ValueError covers a date-shaped scalar PyYAML auto-constructs and
            # rejects (e.g. an invalid month), which is not a YAMLError subclass.
            errors.append(
                f"{rel}: YAML frontmatter parse error ({e.__class__.__name__}: {e}), "
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
                # okf_version marker, never concept metadata or stray keys.
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
        # increment and the closed-vocabulary membership test, so report it and
        # fall back to "<none>" to keep the rest of this concept's checks running.
        if not isinstance(ctype, str):
            errors.append(f"{rel}: 'type' must be a string, got {type(ctype).__name__}")
            ctype = "<none>"
        type_counts[ctype] += 1

        for key in required_keys_for(bundle_version):
            val = fm.get(key)
            if val is None or (isinstance(val, str) and not val.strip()):
                errors.append(f"{rel}: missing/empty required frontmatter key '{key}'")

        allowed_types = allowed_types_for(bundle_version)
        if ctype not in allowed_types and ctype != "<none>":
            errors.append(f"{rel}: type '{ctype}' not in the spec vocab {sorted(allowed_types)}")

        check_lists(rel, fm, errors)
        raw_fm = frontmatter_block(text)
        check_dates(rel, fm, raw_fm, bundle_version, errors)
        check_source_quoting(rel, fm, raw_fm, errors)
        if bundle_version == TRUST_SIGNALS_VERSION:
            check_generated(rel, fm, raw_fm, errors)
            check_verified_trust(rel, fm, raw_fm, bundle_version, errors)
            check_sources_plural(rel, fm, raw_fm, errors)
            check_status(rel, fm, errors)
            check_stale_after(rel, fm, raw_fm, errors)
            check_attested_computation(rel, fm, errors)

    # Link resolution: every internal link to a .md file must resolve to a file
    # that exists inside the bundle. A link escaping the bundle root or pointing at
    # a missing file is a hard failure, the bundle is validated as one
    # self-contained tree. To validate federated content, assemble the bundles into
    # a single tree and point --bundle at that root.
    for f in md_files:
        if f.suffix != ".md":
            continue  # non-conforming file already reported; don't pile on link errors
        text = strip_code(f.read_text(encoding="utf-8-sig"))
        for m in WIKILINK_RE.finditer(text):
            slug = m.group(1).strip()
            errors.append(
                f"{f.relative_to(bundle)}: '[[{slug}]]' is not an OKF link, use a "
                f"relative markdown link like [text]({slug}.md). The [[slug]] form is "
                f"the auto-memory convention, not OKF.")
        for raw in LINK_RE.findall(text):
            target, fragment = link_destination(raw)
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
            else:
                real = real_case_path(dest, bundle)
                if real is not None and not real.exists():
                    real = None
                if real is None:
                    nonconforming = real_case_path(
                        dest, bundle, allow_nonconforming_md=True
                    )
                    if (nonconforming is not None
                            and nonconforming.exists()
                            and nonconforming.suffix.lower() == ".md"
                            and nonconforming.suffix != ".md"):
                        found = os.path.relpath(nonconforming, f.parent).replace(os.sep, "/")
                        expected_path = nonconforming.parent / Path(dest.name).with_suffix(".md")
                        expected = os.path.relpath(expected_path, f.parent).replace(os.sep, "/")
                        errors.append(
                            f"{f.relative_to(bundle)}: link target exists only as a "
                            f"non-conforming markdown filename -> {target}; rename "
                            f"{found} to {expected}")
                    else:
                        errors.append(f"{f.relative_to(bundle)}: dangling link -> {target}")
                elif real != dest:
                    # Report the fix as a link, relative to the file doing the linking,
                    # so it can be pasted straight in. Bundle-relative would be the
                    # error-line convention but is not what goes between the parens.
                    fix = os.path.relpath(real, f.parent).replace(os.sep, "/") + fragment
                    errors.append(
                        f"{f.relative_to(bundle)}: link case does not match the file on "
                        f"disk -> {target}; write {fix}. Links are case-sensitive "
                        f"on Linux, so this resolves on macOS and breaks in CI.")

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
