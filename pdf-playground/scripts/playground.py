#!/usr/bin/env python3
"""Preview helpers for the pdf-playground commands.

The /preview and /proposal commands pre-approve only this script, so it must
do every shell step those commands need: copy the control panel next to a
document, serve that directory on localhost, and remove the copied files.

Usage:
    playground.py setup <html-file> [--template NAME]
    playground.py serve <directory> [--port 8787]
    playground.py clean <html-file>
"""

import argparse
import functools
import http.server
import re
import shutil
import socket
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
CONTROLS = PLUGIN_ROOT / "controls"
CONTROL_FILES = ("control-panel.css", "control-panel.js", "prompt-generator.js")
WRAPPER = "playground-wrapper.html"
COPY_DIR = "playground-controls"
PORT_ATTEMPTS = 20
UPDATE_HINT = (
    "Your PDF Playground plugin is missing the interactive control panel.\n"
    "Update it, then restart Claude Code:\n"
    "  claude plugin update pdf-playground@claude-skills-journalism"
)


def fail(message):
    print(message, file=sys.stderr)
    sys.exit(1)


def html_file(value):
    path = Path(value).resolve()
    if path.suffix.lower() not in (".html", ".htm") or not path.is_file():
        fail(f"Not an HTML file: {value}")
    return path


def setup(args):
    doc = html_file(args.file)
    if not re.fullmatch(r"[a-z0-9-]+", args.template):
        fail(f"Invalid template name: {args.template}")
    template_map = CONTROLS / "template-maps" / f"{args.template}.js"
    sources = [CONTROLS / name for name in CONTROL_FILES] + [CONTROLS / WRAPPER]
    if not all(path.is_file() for path in sources):
        fail(UPDATE_HINT)
    if not template_map.is_file():
        fail(f"No template map named {args.template}")

    target = doc.parent / COPY_DIR
    (target / "template-maps").mkdir(parents=True, exist_ok=True)
    for name in CONTROL_FILES:
        shutil.copy2(CONTROLS / name, target / name)
    shutil.copy2(template_map, target / "template-maps" / template_map.name)
    shutil.copy2(CONTROLS / WRAPPER, doc.parent / WRAPPER)
    print(f"wrapper: {WRAPPER}?doc={doc.name}&template={args.template}")


def free_port(start):
    for port in range(start, start + PORT_ATTEMPTS):
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    fail(f"No free port between {start} and {start + PORT_ATTEMPTS - 1}")


def serve(args):
    root = Path(args.directory).resolve()
    if not root.is_dir():
        fail(f"Not a directory: {args.directory}")
    port = free_port(args.port)
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(root)
    )
    # Bind to loopback only: the preview is for this machine, not the network.
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"Serving http://localhost:{port}/", flush=True)
        server.serve_forever()


def clean(args):
    doc = html_file(args.file)
    shutil.rmtree(doc.parent / COPY_DIR, ignore_errors=True)
    (doc.parent / WRAPPER).unlink(missing_ok=True)
    print("removed playground files")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)

    p_setup = commands.add_parser("setup", help="copy the control panel next to a document")
    p_setup.add_argument("file")
    p_setup.add_argument("--template", default="proposal")
    p_setup.set_defaults(run=setup)

    p_serve = commands.add_parser("serve", help="serve a directory on localhost")
    p_serve.add_argument("directory")
    p_serve.add_argument("--port", type=int, default=8787)
    p_serve.set_defaults(run=serve)

    p_clean = commands.add_parser("clean", help="remove the copied control panel")
    p_clean.add_argument("file")
    p_clean.set_defaults(run=clean)

    args = parser.parse_args(argv)
    args.run(args)


if __name__ == "__main__":
    main()
