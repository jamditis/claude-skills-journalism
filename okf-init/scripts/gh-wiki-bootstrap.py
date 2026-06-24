#!/usr/bin/env python3
"""gh-wiki-bootstrap.py — create the FIRST page of an empty GitHub wiki.

Why this exists: a repo with the wiki feature enabled but zero pages has no
`<repo>.wiki.git` repo yet. `git clone`/`git push` both fail with "Repository
not found," and GitHub exposes no REST API for wiki content. The only way to
create the first page is the web UI. After that one page exists, the wiki is a
normal git repo: clone it, add pages, push.

So this script does the minimum web-UI step — create one page (default "Home")
via Playwright using the saved GitHub web session — and prints the wiki URL.
Everything after (real content, multiple pages) should go through git.

Auth: reuses the saved Playwright storageState at ~/.cache/gh_state.json, the
same session kept alive by gh-session-keepwarm.py. The github PAT does NOT work
for this — wiki pages are a web-UI-only surface.

Usage:
  gh-wiki-bootstrap.py owner/repo
  gh-wiki-bootstrap.py owner/repo --title Home --body "Initializing wiki."
  gh-wiki-bootstrap.py owner/repo --headed   # watch it run, for debugging

Exit codes: 0 ok, 2 not authenticated, 3 body editor not found,
4 save button not found, 5 bad arguments, 6 save not confirmed.

Then:  git clone https://github.com/owner/repo.wiki.git
"""
import argparse
import os
import re
import sys

DEFAULT_STATE = os.path.expanduser("~/.cache/gh_state.json")


def parse_args():
    ap = argparse.ArgumentParser(description="Create the first page of an empty GitHub wiki.")
    ap.add_argument("repo", help="target repo as owner/name, e.g. jamditis/ccm")
    ap.add_argument("--title", default="Home", help="first page title (default: Home)")
    ap.add_argument("--body", default="Initializing wiki.", help="first page body text")
    ap.add_argument("--state", default=DEFAULT_STATE, help="Playwright storageState json (default: ~/.cache/gh_state.json)")
    ap.add_argument("--headed", action="store_true", help="run with a visible browser (debugging)")
    ap.add_argument("--screenshot-dir", default=None, help="if set, save before/after screenshots here")
    args = ap.parse_args()
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", args.repo):
        ap.error("repo must look like owner/name")
    if not os.path.exists(args.state):
        ap.error(f"session state not found: {args.state} (run gh-session-keepwarm.py or re-auth)")
    return args


def shot(page, screenshot_dir, name):
    if screenshot_dir:
        os.makedirs(screenshot_dir, exist_ok=True)
        page.screenshot(path=os.path.join(screenshot_dir, name))


def main():
    args = parse_args()
    # Imported here so --help works without playwright installed.
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    new_url = f"https://github.com/{args.repo}/wiki/_new"
    wiki_url = f"https://github.com/{args.repo}/wiki"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        ctx = browser.new_context(storage_state=args.state)
        page = ctx.new_page()
        page.goto(new_url, wait_until="domcontentloaded", timeout=45000)
        url = page.url
        print("landed on:", url)
        if "/login" in url:
            print("error: not authenticated (redirected to login); refresh the session", file=sys.stderr)
            browser.close()
            sys.exit(2)

        # Wait for the editor to actually render rather than sleeping a fixed
        # interval, so a slow page load is not mistaken for a missing control.
        title_sel = "input#wiki_page_title, input[name='wiki[name]'], input[name='wiki[title]']"
        try:
            page.wait_for_selector(title_sel, state="visible", timeout=20000)
        except PWTimeout:
            pass  # editor never appeared; the body-editor check below reports it
        shot(page, args.screenshot_dir, "wiki_01_new.png")

        # Title field (often prefilled with "Home" on the first page).
        for sel in ["input#wiki_page_title", "input[name='wiki[name]']", "input[name='wiki[title]']"]:
            if page.locator(sel).count():
                page.fill(sel, args.title)
                print("title set via", sel)
                break

        # Body: plain textarea (classic gollum editor) first, then CodeMirror.
        body_filled = False
        if page.locator("textarea#gollum-editor-body").count():
            page.fill("textarea#gollum-editor-body", args.body)
            body_filled = True
            print("body filled via textarea#gollum-editor-body")
        else:
            for sel in [".CodeMirror textarea", ".cm-content", "div[contenteditable='true']", "textarea[name='wiki[content]']"]:
                if page.locator(sel).count():
                    page.click(sel)
                    page.keyboard.type(args.body)
                    body_filled = True
                    print("body typed via", sel)
                    break

        shot(page, args.screenshot_dir, "wiki_02_filled.png")
        if not body_filled:
            print("error: could not locate the wiki body editor", file=sys.stderr)
            browser.close()
            sys.exit(3)

        # Save.
        clicked = False
        for sel in ["button:has-text('Save Page')", "button[name='commit']", "input[type='submit'][value*='Save']", "button:has-text('Save')"]:
            if page.locator(sel).count():
                page.locator(sel).first.click()
                clicked = True
                print("clicked save via", sel)
                break
        if not clicked:
            print("error: could not find the Save button", file=sys.stderr)
            browser.close()
            sys.exit(4)

        # On success GitHub redirects away from the editor (.../_new) to the
        # created page. Wait for that navigation rather than a fixed sleep, so a
        # slow-but-successful save is not mistaken for a failure.
        saved = True
        try:
            page.wait_for_url(lambda u: "_new" not in u, timeout=20000)
        except PWTimeout:
            saved = False
        final_url = page.url
        shot(page, args.screenshot_dir, "wiki_03_saved.png")
        print("final url:", final_url)
        browser.close()

    # If we never left the editor, the save was rejected (no wiki write access,
    # bad title, inline validation error) — do not report success.
    if not saved or "_new" in final_url:
        print(f"error: wiki editor never redirected to a created page ({final_url}) — "
              "save not confirmed. Check the saved session has wiki write access and "
              "the title is valid.", file=sys.stderr)
        sys.exit(6)

    print("wiki bootstrapped. next:")
    print(f"  git clone https://github.com/{args.repo}.wiki.git")
    print(f"  open: {wiki_url}")


if __name__ == "__main__":
    main()
