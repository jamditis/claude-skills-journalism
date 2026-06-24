#!/usr/bin/env python3
"""PreToolUse hook: gate the first action on reading the OKF index.

Blocks the first tool call of a session once (exit 2, reason on stderr), then
unblocks for the rest of the session. The SessionStart hook (okf-anchor.py) has
already placed the index in context; this is the speed bump that forces
orientation before the first action.

Fires only inside an OKF bundle (a bundle/index.md or index.md is present), so it
is inert in any other project. Stateful per (session, project): a marker under the
user's private cache dir is written on the first (blocking) call, so the immediate
retry and everything after it pass. Never wedges a session and never silently
disables the gate: on any error it surfaces the reason on stderr, then allows.

Wired with no matcher in .claude/settings.json, so it sees the first tool call of
any kind (Bash, Read, Edit, a tool from an MCP server, anything). This is one
cross-platform python3 script; only the launch command differs per OS.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

REL_CANDIDATES = ("bundle/index.md", "index.md")


def state_dir():
    """Return the per-user directory that holds orientation markers.

    Deliberately NOT the world-shared system temp root: on a multi-user host another
    user could pre-create a marker there and bypass the gate. The default is the
    user's private cache dir (XDG_CACHE_HOME or ~/.cache), created 0700. Set
    OKF_ORIENT_STATE_DIR to override it (tests point it at a scratch path).
    """
    override = os.environ.get("OKF_ORIENT_STATE_DIR")
    if override:
        base = Path(override)
    else:
        cache = os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
        base = Path(cache) / "okf-orient"
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    return base


def find_index():
    """Resolve the bundle root index.md.

    Order: $CLAUDE_PROJECT_DIR, then this script's install dir (<project>/.claude/
    hooks/), then a walk up from the cwd. The first two pin the root directly. The
    cwd walk climbs upward looking for bundle/index.md, so a launch from inside
    bundle/<section>/ still resolves the root map, not the section's own index.md. A
    bare index.md at the cwd is the bundle-less last resort. The marker key derives
    from this path's parent, so keying stays stable on the root regardless of cwd.
    """
    bases = []
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_dir:
        bases.append(Path(env_dir))
    bases.append(Path(__file__).resolve().parent.parent.parent)  # <project>/.claude/hooks/
    for base in bases:
        for rel in REL_CANDIDATES:
            p = base / rel
            if p.is_file():
                return p
    cwd = Path.cwd().resolve()
    for ancestor in (cwd, *cwd.parents):
        p = ancestor / "bundle" / "index.md"
        if p.is_file():
            return p
    p = cwd / "index.md"
    return p if p.is_file() else None


def main():
    raw = sys.stdin.read()
    data = json.loads(raw) if raw.strip() else {}

    index = find_index()
    if index is None:
        return 0  # not an OKF bundle: do not gate

    session_id = data.get("session_id")
    if not session_id:
        # Without a stable session id, "once per session" cannot be implemented: a
        # constant fallback key would make the gate fire once ever and skip every
        # later session in this project, and blocking without persisting would wedge
        # the session (the retry has no id either). So skip the gate, visibly. The
        # index was still injected at session start.
        sys.stderr.write(
            "OKF orientation gate: no session_id in the hook payload, so per-session "
            "state cannot be tracked; allowing without gating.\n"
        )
        return 0
    # Key the marker on (session, project) so a reused session id in another
    # project does not skip that project's gate. Hash keeps it filesystem-safe.
    key = hashlib.sha256(
        f"{session_id}|{index.resolve().parent}".encode("utf-8")
    ).hexdigest()[:16]

    # Record orientation before blocking, so the immediate retry and the rest of
    # the session pass. If the marker cannot be persisted (state dir unwritable, or
    # its parent already exists as a file), blocking would re-fire on every retry and
    # wedge the session -- so allow instead, but say so on stderr. This is a visible
    # fail-open, not the silent one the outer handler would give.
    try:
        marker = state_dir() / (key + ".oriented")
        if marker.exists():
            return 0  # already oriented this session: allow
        marker.write_text("", encoding="utf-8")  # set now so the immediate retry passes
        try:
            os.chmod(marker, 0o600)  # owner-only; the state dir is already 0700
        except OSError:
            pass  # perms are defense-in-depth; the private dir is the real control
    except OSError as exc:
        sys.stderr.write(
            f"OKF orientation gate: could not record orientation state ({exc}); "
            "allowing this action so the session is not blocked. The bundle index was "
            "still placed in your context at session start.\n"
        )
        return 0

    sys.stderr.write(
        "OKF orientation gate (fires once per session): this is an Open Knowledge "
        "Format knowledge base and this is the first action of the session. The OKF "
        "index was placed in your context at session start (the bundle root index.md). "
        "Confirm you have read it -- briefly note what this bundle covers -- then retry "
        "your action. It will proceed; this gate does not fire again this session.\n"
    )
    return 2  # block this one call


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - last-resort guard around the whole hook
        # Never wedge a session on a hook error, but never silently disable the gate
        # either: surface the failure, then allow the call. (SystemExit from a normal
        # return is not an Exception, so a real block still propagates.)
        sys.stderr.write(
            f"OKF orientation gate: unexpected hook error ({exc!r}); allowing this "
            "action so the session is not blocked.\n"
        )
        sys.exit(0)
