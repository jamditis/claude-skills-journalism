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

# Tokens that name an AI tool, model, or vendor. Used with word boundaries. These are
# the strict set: any of them in an author/trailer field blocks, because none is a common
# human name (a person is not named "Anthropic" or "Windsurf"). Coding agents that write
# commits (aider, windsurf) belong here; agents whose names collide with human names
# (devin, cline) do not -- they go in the byline-only set below.
_TOOL_TOKENS = (
    r"claude|chatgpt|gpt(?:-?[0-9][a-z0-9]*)?|codex|copilot|gemini|anthropic|openai|"
    r"cursor|bard|llama|language model|large language model|llm|aider|windsurf"
)
# Agent names that are also common human names (Devin, Cline). They credit an AI only
# inside a byline (an attribution verb tied to the name by with/by), never as a bare
# author-field token, so a real person named Devin Smith still authors a commit. Kept out
# of _TOOL_TOKENS for exactly that reason.
_BYLINE_ONLY_TOKENS = r"devin|cline"
# Attribution verbs that, paired with with/by and a tool token, form a byline.
_ATTR_VERBS = (
    r"generated|created|written|authored|made|built|produced|assisted|co-authored|"
    r"powered"
)
# Byline tool tokens: the strict tools, the human-name-colliding agents, plus a standalone
# "AI", so a generic-AI credit ("Generated with AI", "Written by AI") blocks. The negative
# lookahead keeps it to a bare "AI" token and out of the adjective "AI-<noun>" of subject
# matter ("Built with AI-powered search"), which is not a byline. Kept separate from
# _TOOL_TOKENS so the strict author-field check (value_names_tool) does not trip on a human
# named "Ai" or "Devin".
_BYLINE_TOOL_TOKENS = _TOOL_TOKENS + r"|" + _BYLINE_ONLY_TOKENS + r"|ai(?![\w-])"
# Optional "AI-"/"AI " prefix on the attribution verb, so "AI-assisted by Claude" and
# "AI-generated with GPT" anchor as bylines like the bare verb forms. It only adds a match
# that also carries a with/by/using/via + named tool, so "add AI-assisted analysis" (no
# trailing tool credit) still reads as subject matter and passes.
_AI_VERB_PREFIX = r"(?:ai[-\s])?"

# Leading sign-off / list markers a byline can ride at the start of a line: whitespace,
# blockquote/comment/bullet markers (`> `, `# `, `* `, `+ `, `• `), and an optional
# ordered-list number ("1.", "2)"). A credit line in a PR body or changelog often sits
# behind one of these. The class holds no newline, and the ordered-list group is bounded,
# so anchoring it under re.M stays linear per line (no newline-crossing quadratic scan).
_BYLINE_LEAD = r"[ \t>*•:#_=+-]*(?:\d{1,3}[.)][ \t]*)?"
# The same lead as a standalone anchor, to peel the markers off the front of one line
# before testing whether a robot emoji leads it. A `- 🤖` or `> 🤖` sign-off rides these
# markers exactly as the text bylines do, so the emoji check must strip them too.
_BYLINE_LEAD_RE = re.compile(r"^" + _BYLINE_LEAD)
# "AI-generated"/"AI-assisted" as a byline: a line whose whole content is the tag
# (optionally with sign-off punctuation), not the phrase embedded in a sentence. This
# blocks a standalone "AI-assisted" sign-off but allows "detect AI-generated images",
# which is subject matter, not authorship. re.M so ^ and $ bind per line. The leading
# and trailing classes use space/tab, not \s: under re.M an \s* that can eat newlines
# scans across every line from each ^, which is quadratic on blank-line-heavy input.
_AI_BYLINE_RE = re.compile(
    r"(?im)^" + _BYLINE_LEAD + r"ai[-\s]?(?:assisted|generated|authored|written)\b[ \t.!)*_-]*$"
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
    r"(?im)^" + _BYLINE_LEAD + _AI_VERB_PREFIX + r"(?:" + _ATTR_VERBS
    + r")\b[^.\n]{0,40}?\b(?:with|by|using|via)\b"
    r"[^.\n]{0,40}?\b(?:" + _BYLINE_TOOL_TOKENS + r")\b"
)
_TOOL_TOKEN_RE = re.compile(r"\b(?:" + _TOOL_TOKENS + r")\b", re.I)
# Bot identities in an authorship field: a bot email, a [bot] suffix, or a known
# assistant no-reply. A human GitHub no-reply (NNN+user@users.noreply.github.com)
# deliberately does not match.
_BOT_MARKER_RE = re.compile(r"\bbot@|\[bot\]|noreply@anthropic|noreply@openai", re.I)
# A generic-AI identity in an authorship field: "AI Assistant", "AI Bot", "AI Agent",
# "AI Model", or "artificial intelligence". The separator after "AI" (space/tab/_/-) and
# the required following noun keep it off a human whose given name is "Ai" (an "Ai
# Nakamura" author has no such noun after it, so it passes).
_GENERIC_AI_IDENTITY_RE = re.compile(
    r"\bai[ \t_-](?:assistant|bot|agent|model)\b|\bartificial intelligence\b", re.I
)


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
    return bool(
        _TOOL_TOKEN_RE.search(text)
        or _BOT_MARKER_RE.search(text)
        or _GENERIC_AI_IDENTITY_RE.search(text)
    )


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
            # Peel leading sign-off markers (`- `, `> `, `1. `, whitespace) before asking
            # whether the emoji leads the line, so a marked-up sign-off is caught too.
            if _BYLINE_LEAD_RE.sub("", line, count=1).startswith(ROBOT_EMOJI):
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
# one segment and the commit after the glued token is never seen. Redirection characters
# (`<`, `>`) are deliberately NOT here: a redirect does not start a new command, it
# attaches a stream to the current one, so `>/dev/null git commit ...` is one command with
# git as its word, not two. Redirect operators are stripped from a segment (op plus target,
# plus any leading fd) by _strip_redirects, so the command word and its flags stay intact.
_OPERATOR_CHARS = set("();|&")
# Redirect operator tokens shlex emits (after punctuation gluing): plain and appending
# file redirects, here-docs/here-strings, fd duplications, and bash's combined forms. A
# redirect is `[fd]<op>[ ]<target>`; both the op and its one target token are dropped.
_REDIRECT_OPS = {">", ">>", ">|", "<", "<<", "<<<", ">&", "<&", "&>", "&>>"}
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


def _strip_comment(line):
    """Return the line with any unquoted shell comment removed.

    Bash starts a comment at an unquoted, unescaped `#` that begins a word (the start of
    the line, or right after whitespace or a command separator) and ignores the rest of the
    line. A `#` inside quotes (`"Fix #123"`) or glued mid-word (`issue#123`) is literal and
    stays. Removing the comment matches what the shell runs, so a clean command trailed by
    an attributed example in a comment is not falsely blocked; nothing the shell would
    execute is dropped, so no real byline is lost. shlex is left with commenters off, so a
    surviving quoted/mid-word `#` is still treated as literal text.
    """
    if "#" not in line:
        return line
    quote = None
    escaped = False
    prev = None  # previous raw char, to spot a word-start `#`
    for idx, ch in enumerate(line):
        if escaped:
            escaped = False
            prev = ch
            continue
        if quote == "'":
            if ch == "'":
                quote = None
            prev = ch
            continue
        if ch == "\\" and quote != "'":
            escaped = True
            prev = ch
            continue
        if quote == '"':
            if ch == '"':
                quote = None
            prev = ch
            continue
        if ch in ("'", '"'):
            quote = ch
            prev = ch
            continue
        if ch == "#" and (prev is None or prev in " \t" or prev in _OPERATOR_CHARS):
            return line[:idx]
        prev = ch
    return line
# A leading `NAME=value` token is a shell environment assignment that prefixes the
# command (`GH_TOKEN=x gh pr create ...`), not an argument. These must be stepped
# over to find the real command word, or the whole invocation reads as unwatched.
_ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# A bare shell variable name with no `=`, as in `export GIT_AUTHOR_NAME` (mark for export
# now, assign later). Recording the name lets a subsequent standalone `NAME=value` update
# the exported value the child git process will see.
_ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
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
_MAX_FILE_BYTES = 1_000_000  # cap a named-file read so a huge file cannot exhaust memory
_MAX_STDIN_BYTES = 10_000_000  # cap the payload read: a larger command is not a real one
# Interpreters whose `-c <script>` argument is a full command line to scan recursively.
_SHELL_RUNNERS = {"sh", "bash", "dash", "zsh", "ksh", "ash", "mksh"}
_MAX_SHELL_DEPTH = 5  # bound the `bash -c '...'` recursion so a deep nest cannot run away
# Shell options that take a following value token, so the `-c` script is not the next arg:
# `bash -o pipefail -c '...'`, `bash --rcfile f -c '...'`. Skipping the value keeps the scan
# from stopping at it and missing the script. `--rcfile=`/`--init-file=` glue their value.
_SHELL_C_VALUE_OPTS = {"-o", "+o", "-O", "+O", "--rcfile", "--init-file"}

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

# Full set of `git merge` long-option names, for the same unambiguous-abbreviation
# resolution (`--mess` -> --message). Kept complete so an abbreviation git itself would
# reject as ambiguous does not resolve here either.
_GIT_MERGE_LONG_OPTS = frozenset({
    "abort", "allow-unrelated-histories", "autostash", "cleanup", "commit", "continue",
    "edit", "ff", "ff-only", "file", "gpg-sign", "into-name", "log", "message",
    "no-verify", "overwrite-ignore", "progress", "quiet", "quit", "rerere-autoupdate",
    "signoff", "squash", "stat", "strategy", "strategy-option", "summary", "verbose",
    "verify-signatures",
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
# `git merge` writes a merge commit whose message comes from -m/--message or -F/--file
# (for a non-fast-forward merge), the same record surfaces as a commit. It has no
# --author/--trailer, but its identity still comes from the same env / `git -c` config,
# handled alongside _GIT_COMMIT in find_attribution.
_GIT_MERGE = {
    "text": {"-m", "--message"},
    "file": {"-F", "--file"},
    "field": set(),
    "short": {"m": "text", "F": "file"},
    "long_opts": _GIT_MERGE_LONG_OPTS,
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
_GH_MERGE = {  # gh pr merge: --subject/--body set the merge/squash commit message
    "text": {"-b", "--body", "-t", "--subject"},
    "file": {"-F", "--body-file"},
    # -A/--author-email sets the merge commit author, an authorship surface like
    # git commit --author, so it is read strictly (a tool/vendor/bot email blocks).
    "field": {"-A", "--author-email"},
    # -t is --subject here (text). -m/-s/-r are merge-method flags, not messages, so they
    # are absent from this map and consume no value.
    "short": {"b": "text", "t": "text", "F": "file", "A": "field"},
}
_GH_COMMENT_ONLY = {  # gh pr/issue close and reopen: a -c/--comment body, no title or file
    "text": {"-c", "--comment"},
    "file": set(),
    "field": set(),
    "short": {"c": "text"},
}
# Sentinel for `gh api`: its record text rides in key=value fields (-f/-F/--field/
# --raw-field) or a --input request-body file, a different shape from the flag specs, so
# it is handled by _gh_api_hits rather than _collect.
_GH_API = "gh-api"
# gh api field keys whose value is human-visible record prose that could carry a byline.
# A control field (state=closed, draft=true) is not scanned.
_GH_API_TEXT_KEYS = {"body", "title", "message", "note", "description"}


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


def _strip_redirects(tokens):
    """Drop shell redirections from a segment's tokens, leaving the command and its args.

    A redirection is `[fd]<op> <target>` (`>/dev/null`, `2>err.log`, `1>&2`, `>>log`). It
    does not begin a new command, so it must be removed rather than split on, or a leading
    redirect (`>/dev/null git commit ...`) hides the command word behind the target and an
    interspersed one (`git commit >/dev/null -m msg`) strands the message flag. The op and
    its single target token are dropped together, as is a bare fd digit that precedes the
    op (shlex emits `2>err` as `2`, `>`, `err`)."""
    out = []
    i, n = 0, len(tokens)
    while i < n:
        t = tokens[i]
        # A lone fd number right before a redirect op (`2 > err`): drop fd, op, and target.
        if t.isdigit() and i + 1 < n and tokens[i + 1] in _REDIRECT_OPS:
            i += 3 if i + 2 < n else 2  # fd + op (+ target if present)
            continue
        if t in _REDIRECT_OPS:
            i += 2 if i + 1 < n else 1  # op (+ target if present)
            continue
        out.append(t)
        i += 1
    return out


# Shell control keywords that can immediately precede a command word that then runs
# (`if ok; then git commit ...`, `while git commit ...`, `time git commit ...`). After a
# split on `;`, a segment can start with one of these, hiding the command word from
# classification. Peel them so the command is still seen. A keyword appearing mid-segment
# is an ordinary argument (a word in a commit message) and is left untouched.
_SHELL_KEYWORDS = {"if", "elif", "then", "else", "while", "until", "do", "!", "time"}


def _strip_leading_keywords(seg):
    """Drop any leading shell control keywords from a segment, returning the remainder.

    `time` takes an optional `-p` portability flag before the pipeline
    (`time -p git commit ...`); skip it too, or the command word after it hides behind the
    flag and reads as unwatched. A `-p` not following `time` is left untouched."""
    i = 0
    while i < len(seg) and seg[i] in _SHELL_KEYWORDS:
        kw = seg[i]
        i += 1
        if kw == "time" and i < len(seg) and seg[i] == "-p":
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
    """True if the effective `git -c <identity-key>=<value>` before the subcommand sets an
    AI name.

    `git -c user.name=Claude -c user.email=bot@example.com commit` sets the commit
    identity inline, the same authorship surface as --author, so the identity config
    values are read like an author field. git applies the LAST value for a repeated key,
    so a clean override of an earlier tool name (`-c user.name=Claude -c user.name=Jane`)
    commits as the human and must not block: collect the last value per identity key, then
    check only those. Scans only the global options (core[1:stop]).
    """
    identity = {}  # identity key (lowercased) -> last value, mirroring git last-wins
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
        if sep and name.strip().lower() in _GIT_IDENTITY_CONFIG:
            identity[name.strip().lower()] = val
    return any(value_names_tool(v) for v in identity.values())


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


def _git_commit_is_dry_run(args):
    """True if a `git commit`'s options name --dry-run (or an unambiguous abbreviation).

    A dry-run previews without creating a commit, so no message, author, or identity enters
    the record: an attributed dry-run is harmless and blocking it only denies a preview.
    Stops at `--` (end of options); resolves `--dry` -> --dry-run the way git does, and does
    not match a short cluster (git commit has no short dry-run flag; -n is --no-verify)."""
    for t in args:
        if t == "--":
            break
        if t.startswith("--"):
            name = t[2:].split("=", 1)[0]
            if _resolve_git_long(name, _GIT_COMMIT_LONG_OPTS) == "dry-run":
                return True
    return False


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
    """Peel any env-setting prefix: return (assignments, core, chdir, unsets, ignore_env).

    Handles both a bare `NAME=value ... cmd` prefix and an `env [opts] NAME=value ... cmd`
    wrapper, so authorship set through the environment (`env GIT_AUTHOR_NAME=Claude git
    commit`) reaches the same identity check as a bare prefix. `env -S`/`--split-string`
    (in the spaced, attached, or `=` form) packs the command into one re-split string,
    which is expanded and reprocessed. `env -C <dir>`/`--chdir <dir>` is returned as
    chdir so a relative message file resolves against the directory the command runs in.
    `env -u NAME`/`--unset NAME` names are returned as unsets, so the identity check can
    drop a var an earlier `export` set and this command removes (env -u GIT_AUTHOR_NAME).
    """
    assigns = []
    unsets = []
    chdir = None
    ignore_env = False  # env -i / --ignore-environment: the command starts with an empty env
    i = 0
    while i < len(seg) and _ENV_ASSIGN_RE.match(seg[i]):
        assigns.append(seg[i])
        i += 1
    # Match `env` by basename, so a pathed wrapper (`/usr/bin/env NAME=val cmd`) is peeled the
    # same as a bare `env`, mirroring the basename match the git/gh detection uses.
    if i >= len(seg) or os.path.basename(seg[i]) != "env":
        return assigns, seg[i:], chdir, unsets, ignore_env

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
            # env -u NAME / --unset NAME / -uNAME / --unset=NAME removes NAME from the
            # child environment. Record it so an AI identity an earlier export set, then
            # this command unsets, is not still counted against the commit.
            if t.startswith("-u") and not t.startswith("--") and len(t) > 2:
                unsets.append(t[2:])
                j += 1
                continue
            if t.startswith("--unset="):
                unsets.append(t.split("=", 1)[1])
                j += 1
                continue
            if t in ("-u", "--unset"):
                if j + 1 < len(rest):
                    unsets.append(rest[j + 1])
                j += 2
                continue
            # env -i / --ignore-environment starts the command with an empty environment, so
            # an identity an earlier export set is not inherited by it. Record it so the
            # identity check drops the exported map for this command (its own inline
            # assignments after -i are still passed and still checked).
            if t in ("-i", "--ignore-environment"):
                ignore_env = True
                j += 1
                continue
            j += 1  # any other env option takes no separate value token we track
        elif _ENV_ASSIGN_RE.match(t):
            assigns.append(t)
            j += 1
        else:
            break  # the command word
    return assigns, rest[j:], chdir, unsets, ignore_env


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


def _shell_c_script(core):
    """If core is a shell interpreter run with `-c <script>`, return the script string.

    `bash -c 'git commit -m "..."'` hides a watched command inside a quoted script token,
    which shlex keeps whole, so the outer parse sees only `bash`. Return that inner script
    so find_attribution can recurse into it. The command word is matched by basename
    (`/bin/bash`), and the `c` may sit anywhere in a short cluster (`bash -lc 'script'`),
    where bash reads the next argument as the command string. Returns None when core is not
    a `-c` shell invocation (a bare `bash script.sh` runs a file, out of scope)."""
    if not core or os.path.basename(core[0]) not in _SHELL_RUNNERS:
        return None
    i = 1
    while i < len(core):
        t = core[i]
        if t == "--command" or t == "-c":
            return core[i + 1] if i + 1 < len(core) else None
        # Options that consume the next token as a value, so the script does not start there:
        # `bash -o pipefail -c '...'`, `bash --rcfile f -c '...'`. Skip the option and its value.
        if t in _SHELL_C_VALUE_OPTS:
            i += 2
            continue
        if t.startswith("--rcfile=") or t.startswith("--init-file="):
            i += 1
            continue
        if t.startswith("--"):
            i += 1
            continue
        if t.startswith("-") and len(t) > 1:
            if "c" in t[1:]:  # -c in a cluster (e.g. -lc): the script is the next arg
                return core[i + 1] if i + 1 < len(core) else None
            i += 1
            continue
        return None  # a non-option before any -c: a script-file run, not -c
    return None


def _watched_spec(core):
    """Return the flag spec for a watched command (env-prefix already stripped), or None.

    The command word is matched by basename, so an interpreter invoked by an absolute or
    relative path (/usr/bin/git, ./gh) is still recognized, while a lookalike whose name
    merely ends in git (mygit) is not."""
    if not core:
        return None, 0
    cmd = os.path.basename(core[0])
    if cmd == "git":
        sub, idx = _git_subcommand(core)
        if sub == "commit":
            return _GIT_COMMIT, idx + 1
        if sub == "merge":
            return _GIT_MERGE, idx + 1
        return None, 0
    if cmd == "gh":
        spec = _gh_spec(core)
        if spec is not None:
            # Scan every token after `gh`: the body/title/file flags are extracted
            # wherever they sit, and the group, subcommand, and global-flag values are
            # ignored as positionals. So the command word need not be at a fixed index.
            return spec, 1
        if "api" in core[1:]:
            # gh api writes the record via key=value fields or a --input body file, a
            # different surface from the flag specs (see _gh_api_hits).
            return _GH_API, 1
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
        if "merge" in toks:
            return _GH_MERGE  # pr merge --subject/--body set the merge commit message
        if toks & {"comment", "review"}:
            return _GH_BODY_ONLY
        if toks & {"close", "reopen"}:
            return _GH_COMMENT_ONLY  # close/reopen carry a --comment body
    if "issue" in toks:
        if "create" in toks:
            return _GH_PR_CREATE  # issue create carries title + body like pr create
        if "edit" in toks:
            return _GH_EDIT
        if "comment" in toks:
            return _GH_BODY_ONLY
        if toks & {"close", "reopen"}:
            return _GH_COMMENT_ONLY
    return None


def _gh_api_method(args):
    """Return the explicit HTTP method of a gh api call (upper-cased), or None if unset.

    `-X`/`--method GET` (attached, spaced, or `=`) names the verb. gh defaults to GET with
    no fields and POST once a field is present, so only an explicit method is reported here;
    the caller treats an explicit GET/HEAD as read-only."""
    for i, t in enumerate(args):
        if t in ("-X", "--method") and i + 1 < len(args):
            return args[i + 1].upper()
        if t.startswith("--method="):
            return t.split("=", 1)[1].upper()
        if t.startswith("-X") and not t.startswith("--") and len(t) > 2:
            return t[2:].upper()
    return None


def _gh_api_key_is_prose(key):
    """True if a gh api field key names visible record prose (body/title/...), else False.

    Handles nested/bracketed keys (`input[body]`, `data[attributes][title]`), which gh sends
    as structured parameters and GraphQL turns into variables: the leading segment or any
    bracketed segment naming a prose key makes the value record text."""
    key = key.strip().lower()
    if key in _GH_API_TEXT_KEYS:
        return True
    lead = key.split("[", 1)[0]
    brackets = re.findall(r"\[([^\]]*)\]", key)
    return any(seg in _GH_API_TEXT_KEYS for seg in [lead, *brackets])


def _gh_api_hits(core, read_dirs):
    """Return a reason if a `gh api` call would write AI attribution, else None.

    gh api writes record text through key=value fields or a whole request-body file:
      -f/--raw-field key=value : value is always literal text
      -F/--field key=value     : value is text, or a file when it starts with `@`
      --input file             : the JSON request body is read from a file (or `-` stdin)
    Only value-carrying keys that hold visible prose (body/title/message/...) are scanned;
    a control field like state=closed is ignored. An explicit GET/HEAD makes the fields
    read-only query parameters, not a write body, so nothing is scanned. Files resolve
    against read_dirs; an unreadable file is nothing to scan (fail open)."""
    args = core[1:]
    # An explicit GET/HEAD turns -f/-F into query params (a read), so there is no record
    # text to guard. Only an explicit method skips; the POST-by-default write path stays on.
    if _gh_api_method(args) in ("GET", "HEAD"):
        return None
    i, n = 0, len(args)
    while i < n:
        t = args[i]
        mode, val = None, None
        if t in ("-f", "--raw-field"):
            val, mode = (args[i + 1] if i + 1 < n else None), "raw"
            i += 2
        elif t in ("-F", "--field"):
            val, mode = (args[i + 1] if i + 1 < n else None), "field"
            i += 2
        elif t.startswith("--raw-field="):
            val, mode = t.split("=", 1)[1], "raw"
            i += 1
        elif t.startswith("--field="):
            val, mode = t.split("=", 1)[1], "field"
            i += 1
        elif t.startswith("-f") and not t.startswith("--") and len(t) > 2:
            val, mode = t[2:], "raw"
            i += 1
        elif t.startswith("-F") and not t.startswith("--") and len(t) > 2:
            val, mode = t[2:], "field"
            i += 1
        elif t == "--input" or t.startswith("--input="):
            fname = t.split("=", 1)[1] if "=" in t else (args[i + 1] if i + 1 < n else None)
            i += 1 if "=" in t else 2
            if fname and fname != "-" and _input_file_has_attribution(fname, read_dirs):
                return "attribution in a gh api --input request body file"
            continue
        else:
            i += 1
            continue
        if val is None:
            continue
        key, sep, v = val.partition("=")
        if not sep or not _gh_api_key_is_prose(key):
            continue
        # -F/--field reads a file when the value starts with `@` (@- is stdin, skipped).
        if mode == "field" and v.startswith("@"):
            fname = v[1:]
            if fname and fname != "-" and _named_file_has_attribution(fname, read_dirs):
                return "attribution in a gh api field file"
            continue
        # Scan the value and its ANSI-C variants, the same as a commit/body message: a
        # `-f body=$'Generated with Claude'` decodes to a byline the raw token hides.
        if any(contains_attribution(x) for x in _shell_message_variants(v)):
            return "attribution in a gh api request field"
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


def _named_file_has_attribution(name, read_dirs):
    """True if the file `name` holds an AI attribution byline, else False.

    Resolves the name against each run dir and, for a leading ~, its home-expanded form,
    and blocks if any readable interpretation carries a byline. shlex discards whether a ~
    was quoted and cd tracking is best-effort, so reading every interpretation makes a
    wrong guess a false positive, never a missed byline."""
    candidates = [name]
    expanded = os.path.expanduser(name)
    if expanded != name:
        candidates.append(expanded)
    for cand in candidates:
        for read_dir in read_dirs:
            content = _read_named_file(cand, read_dir)
            if content is not None and contains_attribution(content):
                return True
    return False


def _obj_text_has_attribution(obj, depth=0):
    """True if a parsed gh api --input body names an AI tool in a record-text field.

    The request body is JSON, so a byline sits inside a string value (`{"body": "Generated
    with Claude"}`) where the line-anchored prose check would not see it. Scan the string
    value of each record-text key (body/title/message/...) as prose, recursing into nested
    objects/arrays under a small depth cap."""
    if depth > 4:
        return False
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str) and isinstance(v, str) and k.lower() in _GH_API_TEXT_KEYS:
                if contains_attribution(v):
                    return True
            elif isinstance(v, (dict, list)):
                if _obj_text_has_attribution(v, depth + 1):
                    return True
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)) and _obj_text_has_attribution(item, depth + 1):
                return True
    return False


def _input_file_has_attribution(name, read_dirs):
    """True if a gh api --input JSON request-body file names an AI tool in a record field.

    Parses the file as JSON and scans its record-text values (see _obj_text_has_attribution).
    A file that does not parse as JSON is scanned as raw prose, a best effort that never
    wedges the session."""
    candidates = [name]
    expanded = os.path.expanduser(name)
    if expanded != name:
        candidates.append(expanded)
    for cand in candidates:
        for read_dir in read_dirs:
            content = _read_named_file(cand, read_dir)
            if content is None:
                continue
            try:
                obj = json.loads(content)
            except ValueError:
                if contains_attribution(content):
                    return True
                continue
            if _obj_text_has_attribution(obj):
                return True
    return False


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


def find_attribution(command, cwd, depth=0, inherited=None):
    """Return a short reason string if the command would write AI attribution, else None.

    Walks the command's logical lines (so a newline-separated command is seen), then the
    segments of each, tracking the effective directory across `cd` so relative message
    files resolve where the command would read them. `depth` bounds recursion into a shell
    runner's `-c` script (bash -c '<script>'), so a pathological nest cannot run away.
    `inherited` carries the ambient git-identity vars the OUTER command hands this one when
    recursing into a `bash -c` script; at the top level it is seeded from the process
    environment instead.
    """
    eff_cwd = cwd
    # The starting ambient identity. At the top level, an identity var already exported
    # before the hook runs (GIT_AUTHOR_NAME=Claude set in the parent shell) is inherited by
    # a bare `git commit`, so seed from the process environment. When recursing into a
    # `bash -c` script, take the identity the outer segment actually passes in `inherited`
    # instead -- re-reading os.environ there would resurrect a value the outer `env -i` or
    # `unset` already cleared and falsely block. Either way a later unset/reassign in the
    # command overrides it (last-wins below).
    if depth == 0:
        exported_identity = {
            name: os.environ[name] for name in _GIT_IDENTITY_ENV if name in os.environ
        }
    else:
        exported_identity = dict(inherited or {})  # exported var -> latest value
    for raw_line in _logical_lines(command):
        # Drop an unquoted trailing `#` comment first: the shell never runs it, so a clean
        # command with an attributed example in a comment must not be blocked.
        line = _strip_comment(raw_line)
        try:
            tokens = _tokenize(line)
        except ValueError:
            # Unbalanced quotes on this line: cannot tokenize, but the attribution may
            # still be plain in the raw text, so scan that as a best effort.
            if contains_attribution(line):
                return "attribution in command text (unparseable quoting)"
            continue

        for seg in _segments(tokens):
            seg = _strip_redirects(seg)
            seg = _strip_leading_keywords(seg)
            if not seg:
                continue
            assigns, core, env_chdir, unsets, ignore_env = _strip_env_prefix(seg)
            if not core:
                # A segment that is only assignments (`GIT_AUTHOR_NAME=Claude` on its own).
                # A bare assignment is shell-local and not passed to a later command UNLESS
                # the name is already exported, in which case reassigning it updates the
                # exported value the child sees. So update only names already tracked as
                # exported; a never-exported local assignment is correctly ignored.
                for a in assigns:
                    name, _, val = a.partition("=")
                    if name in exported_identity:
                        exported_identity[name] = val
                continue
            core = _strip_command_wrappers(core)
            if not core:
                continue
            # `bash -c '<script>'` hides a git/gh command in its script argument. Recurse
            # into that script (depth-bounded) so an inline byline is caught the same as a
            # top-level one; the runner itself writes nothing, so stop after recursing.
            script = _shell_c_script(core)
            if script is not None:
                if depth < _MAX_SHELL_DEPTH:
                    # `env -C dir bash -c '...'` runs the script in dir, so a relative file
                    # the inner command reads (git commit -F MSG) resolves there. Recurse
                    # with the env -C-adjusted cwd, not the bare tracked cwd.
                    rec_cwd = eff_cwd if env_chdir is None else _resolve_dir(eff_cwd, env_chdir)
                    # The script inherits this segment's effective environment: the tracked
                    # exported identity, wiped by env -i, minus any env -u unset, plus the
                    # inline `NAME=val bash -c ...` prefix (all last-wins) -- the same fields
                    # the git-commit branch computes. Pass only identity vars so the nested
                    # `git commit` is judged against the identity it would really inherit.
                    rec_env = {} if ignore_env else dict(exported_identity)
                    for u in unsets:
                        rec_env.pop(u, None)
                    for a in assigns:
                        name, _, val = a.partition("=")
                        rec_env[name] = val
                    rec_env = {k: v for k, v in rec_env.items() if k in _GIT_IDENTITY_ENV}
                    inner = find_attribution(script, rec_cwd, depth + 1, inherited=rec_env)
                    if inner is not None:
                        return inner
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
                    elif _ENV_NAME_RE.match(t):
                        # `export NAME` with no value marks NAME for export; a later
                        # standalone `NAME=value` (handled in the no-core branch above)
                        # then reaches git. Record the name, keeping any value already
                        # tracked, so that reassignment is seen and a bare export of a
                        # clean var does not falsely block.
                        exported_identity.setdefault(t, "")
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
            if spec is _GIT_COMMIT and _git_commit_is_dry_run(core[start:]):
                continue  # a dry-run creates no commit, so nothing enters the record
            seg_cwd = base
            if spec is _GIT_COMMIT or spec is _GIT_MERGE:
                # -C composes onto the base, so a relative -F file resolves correctly.
                seg_cwd = _git_effective_dir(core, start - 1, base)
                # `GIT_AUTHOR_NAME=Claude git commit ...` sets authorship via the
                # environment, the same as --author. Effective identity = exported vars
                # (or none under env -i, which starts with an empty environment), minus any
                # env -u unset, then the inline prefix overriding them (all last-wins),
                # matching what the shell hands git. Read those vars as fields.
                effective = {} if ignore_env else dict(exported_identity)
                for u in unsets:
                    effective.pop(u, None)
                for a in assigns:
                    name, _, val = a.partition("=")
                    effective[name] = val
                for name, val in effective.items():
                    if name in _GIT_IDENTITY_ENV and value_names_tool(val):
                        return "tool or bot named in a git identity environment variable"
                # `git -c user.name=Claude commit ...` sets identity via config;
                # core[start-1] is the commit/merge token, so globals are core[1:start-1].
                if _git_config_identity_hit(core, start - 1):
                    return "tool or bot named in a git -c identity config value"
            # cd tracking is best-effort (a subshell `(cd x)` does not persist, a failed cd
            # does not move), so resolve a relative file against both the tracked dir and
            # the payload cwd; a wrong guess is a false positive, never a miss.
            read_dirs = [seg_cwd] if seg_cwd == cwd else [seg_cwd, cwd]
            if spec is _GH_API:
                reason = _gh_api_hits(core, read_dirs)
                if reason is not None:
                    return reason
                continue
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
            for name in found["file"]:
                if _named_file_has_attribution(name, read_dirs):
                    return f"attribution in the file '{name}'"
    return None


def main():
    # Bound the read: a command larger than any real one is truncated, so the JSON no
    # longer parses and the hook fails open fast, instead of spending seconds tokenizing a
    # payload that cannot be a legitimate command. A never-wedge, never-exhaust safeguard.
    raw = sys.stdin.read(_MAX_STDIN_BYTES)
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
