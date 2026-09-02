#!/usr/bin/env python3
"""Build the comparison picker, standalone concepts, and asset catalog."""
from __future__ import annotations

import argparse
import html
import json
import mimetypes
import posixpath
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

from _common import (
    SKILL_ROOT,
    copy_contents,
    ensure_clean_dir,
    load_project,
    relative_web_path,
    replace_tokens,
    slugify,
    utc_now,
    write_json,
    write_text,
)

IMAGE_SUFFIXES = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"}
VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".m4v", ".ogg"}

BROWSER_ZIP_JS = r'''
const zipEncoder = new TextEncoder();
const crcTable = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = (c & 1) ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c >>> 0;
  }
  return table;
})();
function crc32(bytes) {
  let c = 0xffffffff;
  for (const byte of bytes) c = crcTable[(c ^ byte) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}
function localHeader(name, data, crc) {
  const nameBytes = zipEncoder.encode(name);
  const out = new Uint8Array(30 + nameBytes.length);
  const view = new DataView(out.buffer);
  view.setUint32(0, 0x04034b50, true); view.setUint16(4, 20, true);
  view.setUint16(6, 0x0800, true); view.setUint16(8, 0, true);
  view.setUint16(10, 0, true); view.setUint16(12, 0x0021, true);
  view.setUint32(14, crc, true); view.setUint32(18, data.length, true);
  view.setUint32(22, data.length, true); view.setUint16(26, nameBytes.length, true);
  view.setUint16(28, 0, true); out.set(nameBytes, 30); return out;
}
function centralHeader(name, data, crc, offset) {
  const nameBytes = zipEncoder.encode(name);
  const out = new Uint8Array(46 + nameBytes.length);
  const view = new DataView(out.buffer);
  view.setUint32(0, 0x02014b50, true); view.setUint16(4, 20, true);
  view.setUint16(6, 20, true); view.setUint16(8, 0x0800, true);
  view.setUint16(10, 0, true); view.setUint16(12, 0, true);
  view.setUint16(14, 0x0021, true); view.setUint32(16, crc, true);
  view.setUint32(20, data.length, true); view.setUint32(24, data.length, true);
  view.setUint16(28, nameBytes.length, true); view.setUint16(30, 0, true);
  view.setUint16(32, 0, true); view.setUint16(34, 0, true);
  view.setUint16(36, 0, true); view.setUint32(38, 0, true);
  view.setUint32(42, offset, true); out.set(nameBytes, 46); return out;
}
async function buildAssetZip(rawPaths, status) {
  const paths = [...new Set(rawPaths)];
  if (!paths.length) throw new Error('No downloadable assets are registered.');
  if (paths.length > 65535) throw new Error('Too many files for the browser ZIP builder.');
  const files = [];
  for (let index = 0; index < paths.length; index++) {
    const path = paths[index];
    status.textContent = `Collecting ${index + 1} of ${paths.length}: ${path}`;
    const response = await fetch(path);
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${path}`);
    const data = new Uint8Array(await response.arrayBuffer());
    files.push({ name: path.replace(/^\.\//, ''), data });
  }
  const locals = [], centrals = [];
  let offset = 0;
  for (const file of files) {
    const crc = crc32(file.data);
    const header = localHeader(file.name, file.data, crc);
    locals.push(header, file.data);
    centrals.push(centralHeader(file.name, file.data, crc, offset));
    offset += header.length + file.data.length;
  }
  const centralOffset = offset;
  const centralSize = centrals.reduce((sum, part) => sum + part.length, 0);
  const end = new Uint8Array(22);
  const view = new DataView(end.buffer);
  view.setUint32(0, 0x06054b50, true); view.setUint16(4, 0, true);
  view.setUint16(6, 0, true); view.setUint16(8, files.length, true);
  view.setUint16(10, files.length, true); view.setUint32(12, centralSize, true);
  view.setUint32(16, centralOffset, true); view.setUint16(20, 0, true);
  return new Blob([...locals, ...centrals, end], { type: 'application/zip' });
}
function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = filename; document.body.appendChild(link);
  link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 30000);
}
async function prepareZip(button, paths, name) {
  const status = document.querySelector('[data-download-status]');
  const original = button.textContent;
  button.disabled = true; button.textContent = 'Building ZIP…';
  try {
    const blob = await buildAssetZip(paths, status);
    triggerDownload(blob, name);
    status.textContent = `Prepared ${[...new Set(paths)].length} files as ${name}.`;
  } catch (error) {
    status.textContent = `Could not build the ZIP: ${error.message}. Serve the site through HTTP rather than file://.`;
  } finally {
    button.disabled = false; button.textContent = original;
  }
}
document.querySelectorAll('[data-download-family]').forEach(button => {
  button.addEventListener('click', () => prepareZip(button, JSON.parse(button.dataset.paths), button.dataset.name));
});
'''


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def validate_directions(directions: list[dict[str, Any]]) -> None:
    keys: set[str] = set()
    files: set[str] = set()
    for direction in directions:
        for field in ("key", "label", "file"):
            if not direction.get(field):
                raise ValueError(f"Every direction requires {field!r}")
        key = str(direction["key"])
        file = relative_web_path(str(direction["file"]))
        if key in keys:
            raise ValueError(f"Duplicate direction key: {key}")
        if file in files:
            raise ValueError(f"Duplicate direction file: {file}")
        keys.add(key)
        files.add(file)


def build_tabs(directions: list[dict[str, Any]], default_key: str) -> str:
    rows = []
    for direction in directions:
        key = esc(direction["key"])
        active = direction["key"] == default_key
        rows.append(
            f'<button class="tab" id="tab-{key}" type="button" role="tab" '
            f'aria-selected="{str(active).lower()}" aria-controls="frame-{key}" '
            f'tabindex="{0 if active else -1}" data-key="{key}">'
            f'<b>{esc(direction["label"])}</b><span>{esc(direction.get("description", ""))}</span></button>'
        )
    return "\n      ".join(rows)


def build_frames(directions: list[dict[str, Any]], default_key: str) -> str:
    rows = []
    for index, direction in enumerate(directions):
        key = esc(direction["key"])
        source = esc(relative_web_path(str(direction["file"])))
        active = direction["key"] == default_key
        loading = "" if active or index == 0 else ' loading="lazy"'
        rows.append(
            f'<iframe id="frame-{key}" class="concept-frame" role="tabpanel" '
            f'aria-labelledby="tab-{key}" data-key="{key}" data-active="{str(active).lower()}" '
            f'aria-hidden="{str(not active).lower()}" src="{source}" '
            f'title="{esc(direction["label"])} website direction"{loading}></iframe>'
        )
    return "\n    ".join(rows)


def relative_from_page(target: str, page: str) -> str:
    page_parent = PurePosixPath(page).parent
    start = str(page_parent) if str(page_parent) != "." else "."
    return posixpath.relpath(target, start=start)


def ensure_direction_metadata(dist: Path, direction: dict[str, Any]) -> None:
    page_rel = relative_web_path(str(direction["file"]))
    page = dist / page_rel
    text = page.read_text(encoding="utf-8")
    if not re.search(r"</head\s*>", text, re.I):
        raise ValueError(f"Direction page has no closing </head>: {page_rel}")
    lower = text.lower()
    key = str(direction["key"])
    favicon_base = relative_web_path(str(direction.get("favicon_base") or f"assets/brand/{key}"))
    additions: list[str] = []
    if "name=\"viewport\"" not in lower and "name='viewport'" not in lower:
        additions.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    if "name=\"robots\"" not in lower and "name='robots'" not in lower:
        additions.append('<meta name="robots" content="noindex,nofollow">')
    if not re.search(r"<link\b[^>]*rel=[\"'][^\"']*icon", text, re.I):
        additions.extend([
            f'<link rel="icon" href="{esc(relative_from_page(favicon_base + "/favicon.svg", page_rel))}" type="image/svg+xml">',
            f'<link rel="icon" href="{esc(relative_from_page(favicon_base + "/favicon.ico", page_rel))}" sizes="any">',
            f'<link rel="apple-touch-icon" href="{esc(relative_from_page(favicon_base + "/favicon-180.png", page_rel))}">',
        ])
    if additions:
        text = re.sub(r"</head\s*>", "  " + "\n  ".join(additions) + "\n</head>", text, count=1, flags=re.I)
        page.write_text(text, encoding="utf-8")


def media_preview(preview: str, alt: str, group: dict[str, Any]) -> str:
    if not preview:
        return '<div class="preview"><span>No preview supplied</span></div>'
    path = urlsplit(preview).path
    suffix = Path(path).suffix.lower()
    preview_class = " ".join(token for token in str(group.get("preview_class", "")).split() if token.replace("-", "").isalnum())
    class_attr = f"preview {preview_class}".strip()
    if suffix in VIDEO_SUFFIXES:
        poster = group.get("poster")
        poster_attr = f' poster="{esc(poster)}"' if poster else ""
        return (
            f'<div class="{class_attr}"><video controls muted playsinline preload="metadata"{poster_attr}>'
            f'<source src="{esc(preview)}" type="{esc(mimetypes.guess_type(preview)[0] or "video/mp4")}">'
            "Your browser cannot play this video.</video></div>"
        )
    if suffix in IMAGE_SUFFIXES:
        return f'<div class="{class_attr}"><img src="{esc(preview)}" alt="{esc(alt)}" loading="lazy"></div>'
    return f'<div class="{class_attr}"><span>{esc(Path(path).name)}</span></div>'


def clean_file_items(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    seen = set()
    for item in files:
        if not isinstance(item, dict) or not item.get("href"):
            continue
        href = relative_web_path(str(item["href"]))
        if href in seen:
            continue
        seen.add(href)
        output.append({**item, "href": href})
    return output


def build_downloads(files: list[dict[str, Any]], family_name: str) -> str:
    files = clean_file_items(files)
    links = []
    for item in files:
        href = str(item["href"])
        label = item.get("label") or item.get("format") or Path(href).suffix.lstrip(".") or "File"
        title_parts = [item.get("format"), item.get("dimensions"), item.get("notes")]
        title = " · ".join(str(part) for part in title_parts if part)
        title_attr = f' title="{esc(title)}"' if title else ""
        links.append(f'<a href="{esc(href)}" download{title_attr}>{esc(label)}</a>')
    if files:
        paths_json = json.dumps([item["href"] for item in files], ensure_ascii=False)
        zip_name = f"{slugify(family_name)}-assets.zip"
        links.append(
            f'<button type="button" data-download-family data-paths="{esc(paths_json)}" '
            f'data-name="{esc(zip_name)}">Family ZIP</button>'
        )
    return "".join(links)


def build_group(group: dict[str, Any], direction_label: str) -> str:
    title = group.get("title", "Untitled asset")
    description = group.get("description", "")
    preview = group.get("preview", "")
    alt = group.get("preview_alt") or f"Preview of {title} for {direction_label}"
    files = clean_file_items(group.get("files") or [])
    meta = group.get("meta", "")
    searchable = " ".join(
        [direction_label, str(title), str(description), str(meta)]
        + [" ".join(str(value) for value in item.values() if value) for item in files]
    )
    downloads = build_downloads(files, f"{direction_label}-{title}")
    return f"""
      <article class="asset-row" data-search="{esc(searchable.lower())}">
        {media_preview(str(preview), str(alt), group)}
        <div class="asset-copy">
          <h3>{esc(title)}</h3>
          {f'<p>{esc(description)}</p>' if description else ''}
          {f'<p class="meta">{esc(meta)}</p>' if meta else ''}
          {f'<div class="downloads" aria-label="Downloads for {esc(title)}">{downloads}</div>' if downloads else '<p class="meta">No downloadable file listed.</p>'}
        </div>
      </article>"""


def build_asset_section(label: str, section_note: str, accent: str, groups: list[dict[str, Any]], section_key: str) -> str:
    group_html = "\n".join(build_group(group, label) for group in groups) if groups else '<p class="empty" data-search="empty">No assets have been added to this section.</p>'
    return f"""
    <section class="direction" id="{esc(section_key)}" style="--accent:{esc(accent)}">
      <header><p>{esc(section_note)}</p><h2>{esc(label)}</h2></header>
      {group_html}
    </section>"""


def build_asset_sections(assets: dict[str, Any], directions: list[dict[str, Any]]) -> str:
    sections = []
    if assets.get("shared"):
        sections.append(build_asset_section("Shared assets", "Common to all directions", "#111315", assets["shared"], "shared-assets"))
    asset_directions = {item.get("key"): item for item in assets.get("directions") or [] if isinstance(item, dict)}
    for index, direction in enumerate(directions):
        item = asset_directions.get(direction["key"], {})
        label = item.get("label") or direction["label"]
        accent = item.get("accent") or direction.get("accent") or "#111315"
        sections.append(build_asset_section(label, f"Concept {index + 1}", accent, item.get("groups") or [], direction["key"]))
    return "\n".join(sections)


def flatten_asset_manifest(project: dict[str, Any], assets: dict[str, Any]) -> dict[str, Any]:
    flattened = []
    seen = set()

    def consume(direction_key: str, direction_label: str, groups: list[dict[str, Any]]) -> None:
        for group in groups:
            for item in clean_file_items(group.get("files") or []):
                href = str(item["href"])
                if href in seen:
                    continue
                seen.add(href)
                flattened.append({
                    "direction": direction_key,
                    "direction_label": direction_label,
                    "group": group.get("title", ""),
                    "name": Path(urlsplit(href).path).stem,
                    "path": href,
                    "format": item.get("format") or Path(urlsplit(href).path).suffix.lstrip("."),
                    "dimensions": item.get("dimensions"),
                    "notes": item.get("notes"),
                })

    consume("shared", "Shared assets", assets.get("shared") or [])
    for direction in assets.get("directions") or []:
        if isinstance(direction, dict):
            consume(str(direction.get("key", "")), str(direction.get("label", "")), direction.get("groups") or [])
    return {"project": project["name"], "slug": project["slug"], "generated_at": utc_now(), "assets": flattened}


def copy_review_favicon_to_root(dist: Path) -> None:
    source = dist / "assets/brand/review/favicon.ico"
    if source.exists():
        shutil.copy2(source, dist / "favicon.ico")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--no-clean", action="store_true", help="Do not clear dist before building")
    args = parser.parse_args()

    root = args.project_dir.resolve()
    project, directions, assets = load_project(root)
    try:
        validate_directions(directions)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    dist = root / "dist"
    if not args.no_clean:
        ensure_clean_dir(dist)
    else:
        dist.mkdir(parents=True, exist_ok=True)

    copy_contents(root / "src/concepts", dist / "concepts")
    copy_contents(root / "src/assets", dist / "assets")
    copy_contents(root / "design-package", dist / "assets/design-package")

    try:
        for direction in directions:
            expected = dist / relative_web_path(str(direction["file"]))
            if not expected.is_file():
                raise ValueError(f"Direction file does not exist after copy: {expected}")
            ensure_direction_metadata(dist, direction)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    default_key = project.get("default_direction") or directions[0]["key"]
    if default_key not in {direction["key"] for direction in directions}:
        default_key = directions[0]["key"]
    default_direction = next(direction for direction in directions if direction["key"] == default_key)

    active_color = project.get("active_color") or default_direction.get("accent") or "#ff5a1f"
    favicon_svg = project.get("review_favicon", "assets/brand/review/favicon.svg")
    favicon_ico = "assets/brand/review/favicon.ico"
    touch_icon = "assets/brand/review/favicon-180.png"
    identity_mark = project.get("identity_mark") or favicon_svg
    identity_html = f'<img src="{esc(identity_mark)}" alt="" aria-hidden="true">'

    picker_template = (SKILL_ROOT / "assets/picker-shell.html").read_text(encoding="utf-8")
    picker = replace_tokens(
        picker_template,
        {
            "LANG": esc(project.get("language", "en")),
            "THEME_COLOR": esc(project.get("theme_color", "#111315")),
            "ROBOTS": esc(project.get("robots", "noindex,nofollow")),
            "PAGE_TITLE": esc(project.get("review_title") or f'{project["name"]}: website design review'),
            "PAGE_DESCRIPTION": esc(project.get("review_description") or f'Compare website directions for {project["name"]}.'),
            "FAVICON_SVG": esc(favicon_svg),
            "FAVICON_ICO": esc(favicon_ico),
            "TOUCH_ICON": esc(touch_icon),
            "ACTIVE_COLOR": esc(active_color),
            "DIRECTION_COUNT": str(len(directions)),
            "IDENTITY_MARK": identity_html,
            "PROJECT_NAME": esc(project["name"]),
            "REVIEW_SUBTITLE": esc(project.get("review_subtitle", "Website direction review")),
            "TABS": build_tabs(directions, default_key),
            "FRAMES": build_frames(directions, default_key),
            "DEFAULT_STANDALONE": esc(relative_web_path(str(default_direction["file"]))),
            "DEFAULT_ANNOUNCEMENT": esc(f'{default_direction["label"]} direction selected.'),
            "DIRECTIONS_JSON": json.dumps([
                {
                    "key": direction["key"],
                    "label": direction["label"],
                    "file": relative_web_path(str(direction["file"])),
                    "accent": direction.get("accent", active_color),
                }
                for direction in directions
            ], ensure_ascii=False).replace("</", "<\\/"),
            "DEFAULT_KEY_JSON": json.dumps(default_key),
        },
    )
    write_text(dist / "index.html", picker)

    asset_manifest = flatten_asset_manifest(project, assets)
    all_asset_paths = [item["path"] for item in asset_manifest["assets"]]
    bundle_name = project.get("asset_zip_name") or f'{project["slug"]}-all-design-assets.zip'
    if all_asset_paths:
        download_action = '<button type="button" data-download-all>Download all</button>'
        all_script = BROWSER_ZIP_JS + (
            "\nconst allAssetPaths=" + json.dumps(all_asset_paths, ensure_ascii=False).replace("</", "<\\/") + ";\n"
            "const downloadAll=document.querySelector('[data-download-all]');\n"
            "downloadAll?.addEventListener('click',()=>prepareZip(downloadAll,allAssetPaths," + json.dumps(bundle_name) + "));\n"
        )
    else:
        download_action = ""
        all_script = BROWSER_ZIP_JS

    asset_template = (SKILL_ROOT / "assets/asset-page.html").read_text(encoding="utf-8")
    asset_page = replace_tokens(
        asset_template,
        {
            "LANG": esc(project.get("language", "en")),
            "ROBOTS": esc(project.get("robots", "noindex,nofollow")),
            "THEME_COLOR": esc(project.get("theme_color", "#111315")),
            "PROJECT_NAME": esc(project["name"]),
            "FAVICON_SVG": esc(favicon_svg),
            "FAVICON_ICO": esc(favicon_ico),
            "TOUCH_ICON": esc(touch_icon),
            "ACTIVE_COLOR": esc(active_color),
            "DOWNLOAD_ALL_ACTION": download_action,
            "DOWNLOAD_ALL_SCRIPT": all_script,
            "LIBRARY_NOTE": esc(project.get("library_note", "Review licensing and production requirements before public use.")),
            "ASSET_SECTIONS": build_asset_sections(assets, directions),
            "YEAR": str(datetime.now().year),
        },
    )
    write_text(dist / "design-assets.html", asset_page)
    write_json(dist / "asset-manifest.json", asset_manifest)
    write_json(dist / "site-manifest.json", {
        "project": project,
        "directions": directions,
        "generated_at": utc_now(),
        "entry": "index.html",
        "asset_library": "design-assets.html",
        "browser_asset_zip": bundle_name,
    })

    webmanifest_template = (SKILL_ROOT / "assets/manifest.webmanifest").read_text(encoding="utf-8")
    webmanifest = replace_tokens(webmanifest_template, {
        "PROJECT_NAME": project["name"],
        "SHORT_NAME": project.get("short_name") or project["name"][:24],
        "THEME_COLOR": project.get("theme_color", "#111315"),
    })
    write_text(dist / "manifest.webmanifest", webmanifest)
    shutil.copy2(SKILL_ROOT / "assets/robots.txt", dist / "robots.txt")
    copy_review_favicon_to_root(dist)

    # Fail early if the catalog promises files that are not in the build.
    missing = [path for path in all_asset_paths if not (dist / path).is_file()]
    if missing:
        print("error: asset manifest references files missing from dist:", file=sys.stderr)
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        return 1

    print(f"Built review site at {dist}")
    print(f"Entry point: {dist / 'index.html'}")
    print(f"Asset library: {dist / 'design-assets.html'} ({len(all_asset_paths)} downloadable files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
