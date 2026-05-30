#!/usr/bin/env python3
"""REFERENCE IMPLEMENTATION — read it, adapt it, do NOT run it as-is.

The issue picker. It lists open issues across your configured repos, drops the
ones the gates exclude, ranks what's left, and chooses exactly one to work this
session. Your agent should rewrite this for your real config loader and error
handling — this version trades robustness for readability.

Depends only on the `gh` CLI (`gh auth login`) and the Python standard library.
"""
import json
import subprocess
from datetime import datetime, timezone


def list_open_issues(repo, require_labels):
    """Return open issues for one repo as a list of dicts via the gh CLI.

    Repeated --label flags filter at the source. `gh issue list` doesn't formally
    document AND-across-labels the way `gh pr list` does, so passes_gates() below
    re-checks the required labels in Python rather than trust it.
    """
    cmd = ["gh", "issue", "list", "--repo", repo, "--state", "open",
           "--json", "number,title,body,labels,assignees,updatedAt", "--limit", "100"]
    for label in require_labels:
        cmd += ["--label", label]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    issues = json.loads(out)
    for it in issues:                      # carry the repo so the caller can rank across repos
        it["repo"] = repo
    return issues


def passes_gates(issue, require_labels, skip_labels, skip_assigned):
    """A single issue's eligibility. Re-checks require_labels in Python instead of
    trusting gh's --label AND semantics, then applies the skip gates."""
    labels = {l["name"] for l in issue.get("labels", [])}
    if not set(require_labels) <= labels:  # missing a required label -> out
        return False
    if labels & set(skip_labels):          # any skip label present -> out
        return False
    if skip_assigned and issue.get("assignees"):   # a human is already on it
        return False
    return True


# Bias the picker by repo priority. focus_repo, if set, overrides everything by
# drawing only from that repo (handled in shortlist()).
_PRIORITY_WEIGHT = {"high": 0, "normal": 1, "low": 2}


def sort_key(issue, repo_priority, order_by):
    """Lower sorts first. Repo priority is the primary key so a 'high' repo's
    issues lead; order_by breaks ties within a priority band."""
    pri = _PRIORITY_WEIGHT.get(repo_priority.get(issue["repo"], "normal"), 1)
    updated = issue.get("updatedAt", "")
    if order_by == "newest":
        return (pri, _neg_iso(updated))
    if order_by == "least-recently-touched":
        return (pri, updated)              # oldest updatedAt first
    # default "oldest": lowest issue number first (proxy for age of the ask)
    return (pri, issue["number"])


def _neg_iso(iso):
    """Sort an ISO timestamp descending by turning it into a negative epoch."""
    if not iso:
        return 0
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return -dt.replace(tzinfo=timezone.utc).timestamp()


def shortlist(cfg):
    """Return up to shortlist_size eligible issues, best first.

    cfg is the parsed `github:` block plus a repo->priority map your loader builds
    from the repos list (a plain string entry defaults to 'normal').
    """
    focus = cfg.get("focus_repo") or ""
    repos = [focus] if focus else cfg["repos_flat"]   # repos_flat: list of "owner/repo"
    pool = []
    for repo in repos:
        for issue in list_open_issues(repo, cfg.get("require_labels", [])):
            if passes_gates(issue, cfg.get("require_labels", []),
                            cfg.get("skip_labels", []), cfg.get("skip_assigned", True)):
                pool.append(issue)
    pool.sort(key=lambda it: sort_key(it, cfg["repo_priority"], cfg.get("order_by", "oldest")))
    return pool[: cfg.get("shortlist_size", 3)]


def pick_one(cfg):
    """Choose the single issue to work. The shortlist is already ranked, so the
    top entry is the pick; the rest of the shortlist is handed to the session as
    context so it understands what it chose over."""
    candidates = shortlist(cfg)
    if not candidates:
        return None                        # empty pool -> the wake loop exits cleanly
    return {"chosen": candidates[0], "shortlist": candidates}


if __name__ == "__main__":
    # Illustrative only. A real run loads config.yaml; this stub shows the shape.
    demo = {
        "repos_flat": ["owner/repo-a"],
        "repo_priority": {"owner/repo-a": "normal"},
        "require_labels": ["agent-ready"],
        "skip_labels": ["blocked", "wontfix"],
        "skip_assigned": True,
        "shortlist_size": 3,
        "order_by": "oldest",
        "focus_repo": "",
    }
    result = pick_one(demo)
    print(json.dumps(result, indent=2) if result else "no eligible issues")
