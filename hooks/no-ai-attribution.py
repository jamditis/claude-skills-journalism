#!/usr/bin/env python3
"""PreToolUse(Bash) hook: block AI authorship credit before it enters the record.

Reads the Claude Code PreToolUse payload on stdin. When the Bash command is a
`git commit`, `gh pr create`, `gh pr edit`, `gh pr comment`, `gh issue comment`,
or `gh pr review`, it inspects the text that command would write into the project
record (commit message, PR/issue body or title, comment or review body, and any
file those name) plus the commit's author and trailer fields, and denies (exit 2,
reason on stderr) if it finds a tool/model authorship credit. Anything else exits
0 and passes straight through.

This is the executable behind hooks/no-ai-attribution.md. It closes the four
flag-level bypasses that the markdown spec could only describe: git commit
--author / --trailer, gh pr create --template, and the whole gh pr edit subcommand.

Two detectors, applied to different surfaces, because the surfaces differ in kind:
- Free prose (message / body / title / named-file contents) legitimately names
  tools as the subject of the work ("document the Claude API client"), so it uses
  the nuanced contains_attribution: an attribution phrase, emoji, or Co-Authored-By
  trailer, NOT a bare mention.
- Authorship fields (git commit --author, --trailer, and a Co-Authored-By value)
  are authorship by definition, so they use the strict value_names_tool: any
  model/tool token or bot email blocks.

Fails open on anything it cannot read (malformed payload, unbalanced quotes it
cannot tokenize, an unreadable named file): it never wedges a session, but it
never silently disables itself either -- on an internal error it says so on stderr,
then allows.
"""
import json
import os
import re
import shlex
import stat
import sys
from pathlib import Path

HOOK_NAME = "no-ai-attribution"
ROBOT_EMOJI = "\U0001F916"  # the sign-off emoji used as an AI byline

# Tokens that name an AI tool, model, or vendor. Used with word boundaries.
_TOOL_TOKENS = (
    r"claude|chatgpt|gpt(?:-?[0-9][a-z0-9]*)?|codex|copilot|gemini|anthropic|openai|"
    r"cursor|bard|llama|language model|large language model|llm"
)
# Attribution verbs that, paired with with/by and a tool token, form a byline.
_ATTR_VERBS = (
    r"generated|created|written|authored|made|built|produced|assisted|co-authored|"
    r"powered"
)
# Byline tool tokens: the named tools above plus a standalone "AI", so a generic-AI
# credit ("Generated with AI", "Written by AI") blocks. The negative lookahead keeps it
# to a bare "AI" token and out of the adjective "AI-<noun>" of subject matter ("Built
# with AI-powered search"), which is not a byline. Kept separate from _TOOL_TOKENS so the
# strict author-field check (value_names_tool) does not trip on a human named "Ai".
_BYLINE_TOOL_TOKENS = _TOOL_TOKENS + r"|ai(?![\w-])"
# Optional "AI-"/"AI " prefix on the attribution verb, so "AI-assisted by Claude" and
# "AI-generated with GPT" anchor as bylines like the bare verb forms. It only adds a match
# that also carries a with/by/using/via + named tool, so "add AI-assisted analysis" (no
# trailing tool credit) still reads as subject matter and passes.
_AI_VERB_PREFIX = r"(?:ai[-\s])?"

# "AI-generated"/"AI-assisted" as a byline: a line whose whole content is the tag
# (optionally with sign-off punctuation), not the phrase embedded in a sentence. This
# blocks a standalone "AI-assisted" sign-off but allows "detect AI-generated images",
# which is subject matter, not authorship. re.M so ^ and $ bind per line. The leading
# and trailing classes use space/tab, not \s: under re.M an \s* that can eat newlines
# scans across every line from each ^, which is quadratic on blank-line-heavy input.
_AI_BYLINE_RE = re.compile(
    r"(?im)^[ \t>*•:#=-]*ai[-\s]?(?:assisted|generated|authored|written)\b[ \t.!)*_-]*$"
)
# The same phrase anywhere on a line, used only to tell a robot-emoji byline from a
# decorative or subject-matter emoji (an emoji sharing a line with this phrase is a
# byline; one embedded in ordinary prose is not).
_AI_INLINE_RE = re.compile(r"\bai[-\s]?(?:assisted|generated|authored|written)\b", re.I)
# The leading class is space/tab, not \s: under re.M an ^\s* eats newlines from every
# line anchor and, on input with no matching trailer, rescans O(n^2) (a blank-line-heavy
# clean message hangs the hook). A trailer line has only spaces or tabs before it anyway.
_COAUTHOR_LINE_RE = re.compile(r"^[ \t]*co-authored-by\s*:\s*(?P<value>.+)$", re.I | re.M)
# verb ... (with|by|using|via) ... tool, within one line. Bounded, newline-free gaps
# so there is no catastrophic backtracking. Used to confirm a robot-emoji byline line.
_VERB_TOOL_RE = re.compile(
    r"\b" + _AI_VERB_PREFIX + r"(?:" + _ATTR_VERBS
    + r")\b[^.\n]{0,40}?\b(?:with|by|using|via)\b[^.\n]{0,40}?\b(?:"
    + _BYLINE_TOOL_TOKENS
    + r")\b",
    re.I,
)
# The same phrase but anchored at the start of a line (after optional sign-off markers),
# which is where a credit line sits ("Generated with Claude Code"). Anchoring keeps a
# mid-sentence mention as subject matter ("handle summaries generated by Claude") from
# reading as a byline. This is the general prose check; the emoji line already has its
# own strong cue, so it uses the unanchored form above.
_VERB_TOOL_BYLINE_RE = re.compile(
    r"(?im)^[ \t>*•:#_=-]*" + _AI_VERB_PREFIX + r"(?:" + _ATTR_VERBS
    + r")\b[^.\n]{0,40}?\b(?:with|by|using|via)\b"
    r"[^.\n]{0,40}?\b(?:" + _BYLINE_TOOL_TOKENS + r")\b"
)
_TOOL_TOKEN_RE = re.compile(r"\b(?:" + _TOOL_TOKENS + r")\b", re.I)
# Bot identities in an authorship field: a bot email, a [bot] suffix, or a known
# assistant no-reply. A human GitHub no-reply (NNN+user@users.noreply.github.com)
# deliberately does not match.
_BOT_MARKER_RE = re.compile(r"\bbot@|\[bot\]|noreply@anthropic|noreply@openai", re.I)


# ANSI-C ($'...') escapes bash decodes before running the command. shlex keeps them as
# literal backslash sequences, so `-m $'x\n\nGenerated with Claude'` reaches the record
# with a real newline (a leading byline) while the hook sees a single literal line.
_C_ESCAPES = {
    "n": "\n", "t": "\t", "r": "\r", "f": "\f", "v": "\v",
    "a": "\a", "b": "\b", "\\": "\\", "'": "'", '"': '"',
}


def _decode_c_escapes(text):
    """Decode the common ANSI-C ($'...') backslash escapes so the line-anchored byline
    check sees the same lines the shell will write. Only the common escapes are decoded;
    an unknown escape is left as-is. Returns text unchanged when it holds no backslash."""
    if "\\" not in text:
        return text
    out = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "\\" and i + 1 < n and text[i + 1] in _C_ESCAPES:
            out.append(_C_ESCAPES[text[i + 1]])
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _shell_message_variants(text):
    """Yield the forms of a message argument to scan for a byline.

    shlex leaves an ANSI-C ($'...') quote as a literal leading `$` on the token and keeps
    its escapes raw, so `-m $'Generated with Claude'` reaches the hook as `$Generated with
    Claude` (the `$` defeats the line-start byline anchor) while bash writes `Generated with
    Claude`. Yield the raw token, the token with a leading ANSI-C `$` removed, and the
    decoded form of each, so a byline the quoting hides is still seen. Stripping a leading
    `$` off a non-ANSI-C token (a `$VAR`, a literal `$5`) only adds a scan of harmless text
    and never causes a false block.
    """
    seen = set()
    bases = (text, text[1:]) if text.startswith("$") else (text,)
    for base in bases:
        for form in (base, _decode_c_escapes(base)):
            if form not in seen:
                seen.add(form)
                yield form


def value_names_tool(text):
    """Strict: does this authorship-field value name a tool/model or a bot identity?"""
    return bool(_TOOL_TOKEN_RE.search(text) or _BOT_MARKER_RE.search(text))


def contains_attribution(text):
    """Nuanced: does this free-prose text carry an AI authorship credit?

    Fires on the robot-emoji byline, an "AI-assisted/generated" phrase, a
    Co-Authored-By trailer whose value names a tool, or an attribution verb tied to
    a tool token by with/by. A bare tool mention as the subject of the work does not
    fire.
    """
    if not text:
        return False
    # Robot-emoji byline: it leads a line (a sign-off marker position) or shares a line
    # with an attribution cue. A robot emoji embedded in prose ("fix 🤖 rendering") is
    # subject matter and does not fire.
    for line in text.splitlines():
        if ROBOT_EMOJI in line:
            if line.lstrip().startswith(ROBOT_EMOJI):
                return True
            if _AI_INLINE_RE.search(line) or _VERB_TOOL_RE.search(line):
                return True
    if _AI_BYLINE_RE.search(text):
        return True
    for m in _COAUTHOR_LINE_RE.finditer(text):
        if value_names_tool(m.group("value")):
            return True
    if _VERB_TOOL_BYLINE_RE.search(text):
        return True
    return False


# --- command parsing -------------------------------------------------------

# Tokens that separate one command from the next, or wrap a grouped command. A
# command word right after any of these starts a fresh segment, so attribution in a
# chained or grouped command (`a && git commit ...`, `(git commit ...)`) is still seen.
_OPERATORS = {"&&", "||", ";", ";;", "|", "&", "|&", "(", ")", "{", "}"}
# shlex(punctuation_chars=True) glues a run of adjacent operator characters into one
# token, so a subshell close plus a separator arrives as `);`, not `)` then `;`. Any
# token made only of these characters is a command boundary, including a glued run not
# enumerated above (`);`, `)&&`, `|&`); otherwise `(cd x); git commit ...` collapses into
# one segment and the commit after the glued token is never seen.
_OPERATOR_CHARS = set("();<>|&")
_GIT_GLOBAL_ARG_OPTS = {
    "-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env",
}


def _tokenize(command):
    """Tokenize a shell command, keeping operators separate even without spaces.

    Uses shlex with punctuation_chars so `a&&b` splits into `a`, `&&`, `b` (which
    plain shlex.split does not), while operators and `#` inside quotes stay part of
    their token. Raises ValueError on unbalanced quoting, which the caller handles.
    """
    lex = shlex.shlex(command, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""  # a commit message is not a script; do not treat # as a comment
    return list(lex)


def _logical_lines(command):
    """Split a command on unquoted, unescaped newlines, as the shell separates commands
    written on separate lines. A newline inside quotes, or one escaped as a line
    continuation, does not split, so a multi-line quoted message stays a single line.

    shlex drops an unquoted newline as whitespace, erasing the separator, so a segment
    scan alone would miss `printf ok<newline>git commit -m "..."`. Splitting here first
    restores the boundary while keeping quoted newlines (a multi-line commit body) whole.
    """
    lines, buf = [], []
    quote = None      # "'" or '"' while inside that quote
    escaped = False   # the previous char was a backslash outside single quotes
    for ch in command:
        if escaped:
            escaped = False
            if ch == "\n":
                if buf and buf[-1] == "\\":
                    buf.pop()  # backslash-newline is a line continuation: drop both
                continue
            buf.append(ch)
            continue
        if quote == "'":
            buf.append(ch)
            if ch == "'":
                quote = None
            continue
        if ch == "\\" and quote != "'":
            buf.append(ch)
            escaped = True
            continue
        if quote == '"':
            if ch == '"':
                quote = None
            buf.append(ch)
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            continue
        if ch == "\n":
            lines.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    lines.append("".join(buf))
    return lines
# A leading `NAME=value` token is a shell environment assignment that prefixes the
# command (`GH_TOKEN=x gh pr create ...`), not an argument. These must be stepped
# over to find the real command word, or the whole invocation reads as unwatched.
_ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# Env vars that set commit authorship: the environment twin of `git commit --author`.
_GIT_IDENTITY_ENV = {
    "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL",
    "EMAIL",
}
# git config keys that set commit identity, settable per-command with `git -c key=value`.
# git config keys are case-insensitive, so compare lowercased.
_GIT_IDENTITY_CONFIG = {
    "user.name", "user.email", "author.name", "author.email",
    "committer.name", "committer.email",
}
# `env` options that take a separate value, so its argument is not mistaken for the
# command word when peeling an `env NAME=value ... cmd` wrapper. `-S`/`--split-string`
# (its value is expanded) and `-C`/`--chdir` (its value is captured as the run dir) are
# handled separately.
_ENV_ARG_OPTS = {"-u", "--unset"}
_MAX_FILE_BYTES = 1_000_000  # cap a named-file read so a huge file cannot exhaust memory

# Full set of `git commit` long-option names, used only to resolve unambiguous prefix
# abbreviations the way git's parse-options does: git accepts `--au` for --author when
# no other option shares that prefix, and rejects an ambiguous prefix (`--a`) outright.
# Kept complete (not just the tracked options) so ambiguity is judged correctly -- an
# abbreviation git itself would reject as ambiguous must not resolve here either. gh
# uses cobra/pflag, which does not prefix-match, so only the git spec opts in via
# 'long_opts'.
_GIT_COMMIT_LONG_OPTS = frozenset({
    "ahead-behind", "all", "allow-empty", "allow-empty-message", "amend", "author",
    "branch", "cleanup", "date", "dry-run", "edit", "file", "fixup", "gpg-sign",
    "include", "interactive", "long", "message", "no-post-rewrite", "no-verify",
    "null", "only", "patch", "pathspec-file-nul", "pathspec-from-file", "porcelain",
    "quiet", "reedit-message", "reset-author", "reuse-message", "short", "signoff",
    "squash", "status", "template", "trailer", "untracked-files", "verbose",
})

# Per-subcommand flag spec. 'text' -> scanned with contains_attribution; 'file' ->
# contents read and scanned; 'field' -> scanned with value_names_tool. 'short' maps
# a value-taking short-option letter to its kind, for git-style clusters (-am, -F).
# 'long_opts', when present, enables git-style unambiguous prefix abbreviation.
_GIT_COMMIT = {
    "text": {"-m", "--message"},
    # -t/--template preloads the message editor with a file whose contents become the
    # commit if kept, so it is a named message-file surface like -F/--file (and matches
    # how gh's --template is already read).
    "file": {"-F", "--file", "-t", "--template"},
    "field": {"--author", "--trailer"},
    "short": {"m": "text", "F": "file", "t": "file"},
    "long_opts": _GIT_COMMIT_LONG_OPTS,
}
_GH_PR_CREATE = {
    "text": {"-b", "--body", "-t", "--title"},
    "file": {"-F", "--body-file", "-T", "--template"},
    "field": set(),
    "short": {"b": "text", "t": "text", "F": "file", "T": "file"},
}
_GH_BODY_ONLY = {  # gh pr comment / issue comment / pr review: body only, no title
    "text": {"-b", "--body"},
    "file": {"-F", "--body-file"},
    "field": set(),
    "short": {"b": "text", "F": "file"},
}
_GH_EDIT = {  # gh pr edit / gh issue edit: title and body are both editable
    "text": {"-b", "--body", "-t", "--title"},
    "file": {"-F", "--body-file"},
    "field": set(),
    "short": {"b": "text", "t": "text", "F": "file"},
}


def _is_boundary(t):
    """True if a token separates command segments: a listed operator, or any token made
    entirely of shell operator characters (so a glued run like `);` or `)&&` still splits)."""
    return bool(t) and (t in _OPERATORS or all(ch in _OPERATOR_CHARS for ch in t))


def _segments(tokens):
    """Split a token list into command segments on shell operators."""
    segs, cur = [], []
    for t in tokens:
        if _is_boundary(t):
            if cur:
                segs.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        segs.append(cur)
    return segs


# Shell control keywords that can immediately precede a command word that then runs
# (`if ok; then git commit ...`, `while git commit ...`, `time git commit ...`). After a
# split on `;`, a segment can start with one of these, hiding the command word from
# classification. Peel them so the command is still seen. A keyword appearing mid-segment
# is an ordinary argument (a word in a commit message) and is left untouched.
_SHELL_KEYWORDS = {"if", "elif", "then", "else", "while", "until", "do", "!", "time"}


def _strip_leading_keywords(seg):
    """Drop any leading shell control keywords from a segment, returning the remainder."""
    i = 0
    while i < len(seg) and seg[i] in _SHELL_KEYWORDS:
        i += 1
    return seg[i:]


def _git_subcommand(tokens):
    """Return (subcommand, index) for a `git ...` segment, skipping global options."""
    i = 1
    while i < len(tokens):
        t = tokens[i]
        if t.startswith("-"):
            name = t.split("=", 1)[0]
            if name in _GIT_GLOBAL_ARG_OPTS and "=" not in t:
                i += 2  # this global option consumes the next token as its value
            else:
                i += 1
        else:
            return t, i
    return None, i


def _git_config_identity_hit(core, stop):
    """True if a `git -c <identity-key>=<tool>` before the subcommand sets an AI name.

    `git -c user.name=Claude -c user.email=bot@example.com commit` sets the commit
    identity inline, the same authorship surface as --author, so the identity config
    values are read like an author field. Scans only the global options (core[1:stop]).
    """
    i = 1
    while i < stop:
        t = core[i]
        cfg = None
        if t == "-c" and i + 1 < stop:
            cfg = core[i + 1]
            i += 2
        elif t.startswith("-c") and not t.startswith("--") and len(t) > 2:
            cfg = t[2:]  # attached form: -cuser.name=Claude
            i += 1
        else:
            i += 1
            continue
        name, sep, val = cfg.partition("=")
        if sep and name.strip().lower() in _GIT_IDENTITY_CONFIG and value_names_tool(val):
            return True
    return False


def _resolve_git_long(name, opts):
    """Canonical git long-option for a `--`-stripped token, mirroring git parse-options:
    an exact match wins; otherwise a prefix of exactly one known option resolves to it;
    an ambiguous (>1) or unknown (0) prefix resolves to None, because git itself rejects
    those before running -- so the matcher neither over-blocks nor claims coverage git
    would refuse to give."""
    if name in opts:
        return name
    matches = [o for o in opts if o.startswith(name)]
    return matches[0] if len(matches) == 1 else None


def _classify(spec, name):
    if name in spec["text"]:
        return "text"
    if name in spec["file"]:
        return "file"
    if name in spec["field"]:
        return "field"
    # git accepts unambiguous long-option abbreviations (--au -> --author). Resolve only
    # for specs that opt in via 'long_opts' (git); gh/pflag requires exact names. The
    # exact-match cases above already covered a spelled-out option, so only a shorter
    # abbreviation that lands on a *tracked* option adds anything here.
    opts = spec.get("long_opts")
    if opts and name.startswith("--"):
        canon = _resolve_git_long(name[2:], opts)
        if canon is not None:
            full = "--" + canon
            if full in spec["text"]:
                return "text"
            if full in spec["file"]:
                return "file"
            if full in spec["field"]:
                return "field"
    return None


def _collect(tokens, spec):
    """Collect flag values from a segment's argument tokens per the spec.

    Handles `--flag=value`, `--flag value`, `-f value`, attached `-fvalue`, and
    git-style short clusters (`-am value`, `-amvalue`). Returns
    {'text': [...], 'file': [...], 'field': [...]}.
    """
    out = {"text": [], "file": [], "field": []}
    i = 0
    n = len(tokens)
    while i < n:
        t = tokens[i]
        if t == "--":
            break  # end-of-options: every following token is a pathspec/positional, not a
            # flag value, so a byline-looking filename after `--` must not be scanned.
        if t.startswith("--"):
            if "=" in t:
                name, val = t.split("=", 1)
                kind = _classify(spec, name)
                if kind:
                    out[kind].append(val)
            else:
                kind = _classify(spec, t)
                if kind and i + 1 < n:
                    out[kind].append(tokens[i + 1])
                    i += 1
            i += 1
        elif t.startswith("-") and len(t) > 1:
            letters = t[1:]
            j = 0
            consumed_next = False
            while j < len(letters):
                ch = letters[j]
                kind = spec["short"].get(ch)
                if kind:
                    rest = letters[j + 1:]
                    if rest:
                        # A short option keeps a leading `=` as part of its value: git
                        # parse-options and gh/pflag both read `-F=MSG` as the filename
                        # `=MSG` and `-m=x` as the message `=x` (only a long `--flag=x`
                        # splits on `=`). Do not strip it: the byline anchors accept a
                        # leading `=` marker, and a file is read under the name git reads.
                        out[kind].append(rest)
                    elif i + 1 < n:
                        out[kind].append(tokens[i + 1])
                        consumed_next = True
                    break  # a value-taking letter consumes the remainder of the token
                j += 1
            if consumed_next:
                i += 1
            i += 1
        else:
            i += 1
    return out


def _strip_env_prefix(seg):
    """Peel any env-setting prefix off a segment: return (assignments, core, chdir).

    Handles both a bare `NAME=value ... cmd` prefix and an `env [opts] NAME=value ... cmd`
    wrapper, so authorship set through the environment (`env GIT_AUTHOR_NAME=Claude git
    commit`) reaches the same identity check as a bare prefix. `env -S`/`--split-string`
    (in the spaced, attached, or `=` form) packs the command into one re-split string,
    which is expanded and reprocessed. `env -C <dir>`/`--chdir <dir>` is returned as
    chdir so a relative message file resolves against the directory the command runs in.
    """
    assigns = []
    chdir = None
    i = 0
    while i < len(seg) and _ENV_ASSIGN_RE.match(seg[i]):
        assigns.append(seg[i])
        i += 1
    if i >= len(seg) or seg[i] != "env":
        return assigns, seg[i:], chdir

    rest = list(seg[i + 1:])  # tokens after `env`; mutated in place to inline `-S`
    j = 0
    while j < len(rest):
        t = rest[j]
        if t == "--":
            # -- ends option parsing, but env still reads the NAME=value operands after
            # it as assignments (env -- GIT_AUTHOR_NAME=Claude git commit), so keep
            # collecting them before the command word.
            j += 1
            while j < len(rest) and _ENV_ASSIGN_RE.match(rest[j]):
                assigns.append(rest[j])
                j += 1
            break
        if t.startswith("-"):
            # env -S packs the whole command into one string it re-splits; inline that
            # string's tokens so its assignments and command are seen. Accept the spaced
            # (`-S str`), attached (`-Sstr`), and `--split-string=str` forms.
            sval = None
            step = 1
            if t in ("-S", "--split-string"):
                sval = rest[j + 1] if j + 1 < len(rest) else ""
                step = 2
            elif t.startswith("--split-string="):
                sval = t.split("=", 1)[1]
            elif t.startswith("-S") and not t.startswith("--") and len(t) > 2:
                sval = t[2:]
            if sval is not None:
                try:
                    inner = _tokenize(sval)
                except ValueError:
                    inner = []
                rest[j:j + step] = inner
                continue  # reprocess: inner may hold more assignments then the command
            # env -C <dir> / --chdir <dir> / -C<dir> attached: capture the run directory
            # (last one wins). The attached short form mirrors -S<str> above.
            if t.startswith("-C") and not t.startswith("--") and len(t) > 2:
                chdir = t[2:]
                j += 1
                continue
            name = t.split("=", 1)[0]
            if name in ("-C", "--chdir"):
                if "=" in t:
                    chdir = t.split("=", 1)[1]
                    j += 1
                elif j + 1 < len(rest):
                    chdir = rest[j + 1]
                    j += 2
                else:
                    j += 1
                continue
            if name in _ENV_ARG_OPTS and "=" not in t:
                j += 2
            else:
                j += 1
        elif _ENV_ASSIGN_RE.match(t):
            assigns.append(t)
            j += 1
        else:
            break  # the command word
    return assigns, rest[j:], chdir


# Command-runner wrappers that execute the command word following them, hiding it from
# the "first token is git/gh" check. Bare forms run the command (`command git commit`,
# `exec git commit`, `nohup git commit`, `setsid git commit`); these four take no
# value-bearing option in normal use (bar `exec -a <name>`, handled below), so they peel
# cleanly. Value-arg scheduling wrappers (sudo, timeout, nice, ionice, stdbuf) are out of
# scope on purpose: each needs its own option grammar, an incomplete one would turn a
# skipped value into a fake command word (a miss), and prefixing an attributed commit with
# one is a contrived path the global commit guard and human review still cover.
_CMD_WRAPPERS = {"command", "exec", "nohup", "setsid"}


def _strip_command_wrappers(core):
    """Peel leading command-runner wrappers so the real command word is exposed. Skips each
    wrapper's own leading option flags (`command -p`, `setsid -w`), and the value of
    `exec -a <name>`. Leaves `command -v`/`-V <name>` unpeeled: that looks a command up
    rather than running it, so no commit happens and the segment must stay unwatched."""
    while core and core[0] in _CMD_WRAPPERS:
        w = core[0]
        k = 1
        while k < len(core) and core[k].startswith("-") and core[k] != "--":
            if w == "command" and core[k] in ("-v", "-V"):
                return core  # lookup form, not a run
            if w == "exec" and core[k] == "-a" and k + 1 < len(core):
                k += 2  # -a <name> renames argv[0]; skip its value too
                continue
            k += 1
        if k < len(core) and core[k] == "--":
            k += 1
        core = core[k:]  # k >= 1 always, so this terminates
    return core


def _watched_spec(core):
    """Return the flag spec for a watched command (env-prefix already stripped), or None."""
    if not core:
        return None, 0
    if core[0] == "git":
        sub, idx = _git_subcommand(core)
        if sub == "commit":
            return _GIT_COMMIT, idx + 1
        return None, 0
    if core[0] == "gh":
        spec = _gh_spec(core)
        if spec is not None:
            # Scan every token after `gh`: the body/title/file flags are extracted
            # wherever they sit, and the group, subcommand, and global-flag values are
            # ignored as positionals. So the command word need not be at a fixed index.
            return spec, 1
    return None, 0


def _gh_spec(core):
    """Return the flag spec for a watched `gh` write command, by token membership.

    A gh write command is identified by the presence of its group and subcommand
    tokens (`pr` + `create`, `pr` + `edit`/`comment`/`review`, `issue` + `create`/
    `comment`), not by their position, so any global flags before the command group
    (`gh -R o/r pr create`, `gh --hostname h pr create`) are irrelevant. Quoted bodies
    survive tokenization as a single token, so a body word cannot pose as a subcommand.
    """
    toks = set(core[1:])
    if "pr" in toks:
        if "create" in toks:
            return _GH_PR_CREATE
        if "edit" in toks:
            return _GH_EDIT  # pr edit rewrites title and body, not only body
        if toks & {"comment", "review"}:
            return _GH_BODY_ONLY
    if "issue" in toks:
        if "create" in toks:
            return _GH_PR_CREATE  # issue create carries title + body like pr create
        if "edit" in toks:
            return _GH_EDIT
        if "comment" in toks:
            return _GH_BODY_ONLY
    return None


def _read_named_file(name, cwd):
    """Read a file a command names, relative to cwd. Return its text, or None.

    A '-' argument is stdin (unreadable pre-command) and returns None, as does any
    file that cannot be read: the caller treats None as nothing to scan (fail open).
    Only regular files are read, and only up to a byte cap: a FIFO or device would
    block the read before the command runs, and an unbounded read of a huge file could
    exhaust memory, either of which would wedge the session the hook must never wedge.
    """
    if name == "-":
        return None
    try:
        p = Path(name)
        if not p.is_absolute():
            p = Path(cwd) / p
        if not stat.S_ISREG(p.stat().st_mode):
            return None  # FIFO, device, directory, socket: not a message file
        with p.open("r", encoding="utf-8", errors="replace") as fh:
            return fh.read(_MAX_FILE_BYTES)
    except OSError:
        return None


def _resolve_dir(base, target):
    """Resolve a possibly-relative directory against base."""
    if os.path.isabs(target):
        return target
    return os.path.normpath(os.path.join(base, target))


def _apply_cd(core, eff_cwd):
    """Return the effective directory after a `cd` segment.

    A relative message file resolves against the shell's current directory, so a
    preceding `cd repo` must move the base a `git commit -F MSG` reads MSG from. `cd -`
    (previous dir) is unknowable and leaves the base unchanged; a bare `cd` goes home.
    """
    target = None
    for t in core[1:]:
        if t == "--" or (t.startswith("-") and t != "-"):
            continue
        target = t  # last positional is the destination
    if target is None:
        return os.path.expanduser("~")
    if target == "-":
        return eff_cwd
    return _resolve_dir(eff_cwd, target)


def _git_effective_dir(core, stop, base):
    """Apply any `git -C <dir>` global options (left to right) to base.

    `git -C repo commit -F MSG` reads MSG from repo/, so the -C directories compose onto
    the base the same way the shell's cwd would. Scans only the globals (core[1:stop]).
    """
    d = base
    i = 1
    while i < stop:
        t = core[i]
        if t == "-C" and i + 1 < stop:
            d = _resolve_dir(d, core[i + 1])
            i += 2
            continue
        name = t.split("=", 1)[0]
        if name in _GIT_GLOBAL_ARG_OPTS and "=" not in t:
            i += 2
        else:
            i += 1
    return d


def find_attribution(command, cwd):
    """Return a short reason string if the command would write AI attribution, else None.

    Walks the command's logical lines (so a newline-separated command is seen), then the
    segments of each, tracking the effective directory across `cd` so relative message
    files resolve where the command would read them.
    """
    eff_cwd = cwd
    exported_identity = {}  # exported identity var -> latest value (shell last-wins)
    for line in _logical_lines(command):
        try:
            tokens = _tokenize(line)
        except ValueError:
            # Unbalanced quotes on this line: cannot tokenize, but the attribution may
            # still be plain in the raw text, so scan that as a best effort.
            if contains_attribution(line):
                return "attribution in command text (unparseable quoting)"
            continue

        for seg in _segments(tokens):
            seg = _strip_leading_keywords(seg)
            if not seg:
                continue
            assigns, core, env_chdir = _strip_env_prefix(seg)
            if not core:
                continue
            core = _strip_command_wrappers(core)
            if not core:
                continue
            if core[0] == "cd":
                eff_cwd = _apply_cd(core, eff_cwd)
                continue
            if core[0] == "export":
                # `export GIT_AUTHOR_NAME=Claude; git commit` sets the identity in this
                # shell for the later commit, the same authorship surface as an inline
                # `GIT_AUTHOR_NAME=Claude git commit` prefix. Track the latest value per
                # name (a re-export overwrites, an `unset` below clears) so a later clean
                # value is not shadowed by an earlier flagged one. (A bare `export NAME`
                # with no value, or an export inside a subshell, is best-effort at worst.)
                for t in core[1:]:
                    if _ENV_ASSIGN_RE.match(t):
                        name, _, val = t.partition("=")
                        exported_identity[name] = val
                continue
            if core[0] == "unset":
                # `unset GIT_AUTHOR_NAME` clears an earlier export before the commit, so
                # the commit is clean; drop the name (skip -f/-v flags, keep the operands).
                for t in core[1:]:
                    if not t.startswith("-"):
                        exported_identity.pop(t, None)
                continue
            base = eff_cwd if env_chdir is None else _resolve_dir(eff_cwd, env_chdir)
            spec, start = _watched_spec(core)
            if spec is None:
                continue
            seg_cwd = base
            if spec is _GIT_COMMIT:
                # -C composes onto the base, so a relative -F file resolves correctly.
                seg_cwd = _git_effective_dir(core, start - 1, base)
                # `GIT_AUTHOR_NAME=Claude git commit ...` sets authorship via the
                # environment, the same as --author. Effective identity = exported vars,
                # then the inline prefix overriding them (both last-wins), matching what
                # the shell hands git. Read those identity vars as fields.
                effective = dict(exported_identity)
                for a in assigns:
                    name, _, val = a.partition("=")
                    effective[name] = val
                for name, val in effective.items():
                    if name in _GIT_IDENTITY_ENV and value_names_tool(val):
                        return "tool or bot named in a git identity environment variable"
                # `git -c user.name=Claude commit ...` sets identity via config;
                # core[start-1] is the `commit` token, so globals are core[1:start-1].
                if _git_config_identity_hit(core, start - 1):
                    return "tool or bot named in a git -c identity config value"
            found = _collect(core[start:], spec)
            for text in found["text"]:
                # Scan the raw token and its ANSI-C variants (leading `$` removed, escapes
                # decoded): `-m $'Generated with Claude'` and `-m $'x\n\nGenerated ...'` both
                # commit a byline the raw token hides behind the `$'...'` quoting.
                if any(contains_attribution(v) for v in _shell_message_variants(text)):
                    return "attribution in message/body text"
            for field in found["field"]:
                if value_names_tool(field):
                    return "tool or bot named in an author/trailer field"
            # Resolve a relative file against both the tracked dir and the payload cwd, and
            # block on either. cd tracking is a best effort (a subshell `(cd x)` does not
            # persist, a failed `cd` does not move) so the shell's real cwd can differ from
            # the tracked one; reading both makes a wrong guess a false positive, never a miss.
            read_dirs = [seg_cwd] if seg_cwd == cwd else [seg_cwd, cwd]
            for name in found["file"]:
                # Read the name as written (resolved against the tracked dir and the payload
                # cwd) and, for a leading ~, its home-expanded form too. shlex discards
                # whether the ~ was quoted, so both interpretations are read and either
                # blocks: a wrong guess is a false positive, never a missed byline (the same
                # safe-direction tradeoff the cd/dir tracking above makes).
                candidates = [name]
                expanded = os.path.expanduser(name)
                if expanded != name:
                    candidates.append(expanded)
                for cand in candidates:
                    for read_dir in read_dirs:
                        content = _read_named_file(cand, read_dir)
                        if content is not None and contains_attribution(content):
                            return f"attribution in the file '{name}'"
    return None


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0  # cannot read the payload: do not wedge the session

    tool_name = data.get("tool_name")
    if tool_name and tool_name != "Bash":
        return 0

    command = (data.get("tool_input") or {}).get("command")
    if not command or not isinstance(command, str):
        return 0

    cwd = data.get("cwd") or os.getcwd()
    reason = find_attribution(command, cwd)
    if reason is None:
        return 0

    sys.stderr.write(
        f"{HOOK_NAME}: blocked. This command would put AI authorship credit into the "
        f"record ({reason}). The published record should name people, not tools.\n"
        "Fix: remove the credit line, trailer, author, or emoji sign-off, then rerun. "
        "A Co-Authored-By trailer naming a real person is fine and stays.\n"
    )
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - last-resort guard around the whole hook
        # Never wedge a session on a hook error, but never silently disable the gate
        # either. (SystemExit from a normal return is not an Exception, so a real
        # block still propagates.)
        sys.stderr.write(
            f"{HOOK_NAME}: unexpected hook error ({exc!r}); allowing this action so the "
            "session is not blocked.\n"
        )
        sys.exit(0)
