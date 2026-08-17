#!/usr/bin/env python3
"""REFERENCE IMPLEMENTATION, read it, adapt it, do NOT run it as-is.

The verifier. After a session ends, it confirms the receipt token actually landed
in a commit, a pull request, or an issue comment, proof the work was this
session's and not a human's or another job's. If the token is nowhere, the run is
reported "unverified" rather than quietly assumed good (invariant 8).

This is deliberately simple: presence of the token in an expected surface is the
signal. Your agent can make it stricter (check the PR targets a non-protected
branch, the diff stayed inside scope, etc.). Standard library + `gh` + `git`.
"""
import json
import subprocess


def token_in_recent_commits(repo_dir, token, max_commits=20):
    """True if the token appears in any of the last N commit messages."""
    out = subprocess.run(
        ["git", "-C", repo_dir, "log", f"-{max_commits}", "--format=%H%n%B%n==="],
        capture_output=True, text=True).stdout
    return token in out


def token_in_open_prs(repo, token):
    """True if the token appears in the body of any open PR. Returns the PR
    number when found, so the caller can link it in the summary."""
    out = subprocess.run(
        ["gh", "pr", "list", "--repo", repo, "--state", "open",
         "--json", "number,body", "--limit", "30"],
        capture_output=True, text=True).stdout
    for pr in json.loads(out or "[]"):
        if token in (pr.get("body") or ""):
            return pr["number"]
    return None


def token_in_recent_comments(repo, token, since_issues=30):
    """True if the token appears in a recent issue/PR comment. Comments are how a
    blocked-or-decomposed session leaves its receipt when it didn't commit."""
    out = subprocess.run(
        ["gh", "search", "issues", "--repo", repo, token, "--json", "number", "--limit", "5"],
        capture_output=True, text=True).stdout
    return len(json.loads(out or "[]")) > 0


def verify(repo, repo_dir, token):
    """Classify the run. 'confirmed' if the token is in any expected surface;
    'unverified' if it's nowhere, which is a real, reportable outcome, not an
    error to swallow."""
    pr = token_in_open_prs(repo, token)
    found = (
        token_in_recent_commits(repo_dir, token)
        or pr is not None
        or token_in_recent_comments(repo, token)
    )
    return {
        "token": token,
        "verdict": "confirmed" if found else "unverified",
        "pr": pr,
    }


if __name__ == "__main__":
    # Illustrative only.
    result = verify("owner/repo-a", "/home/you/projects/repo-a", "wake-20260530T1405-a1b2c3")
    print(json.dumps(result, indent=2))
