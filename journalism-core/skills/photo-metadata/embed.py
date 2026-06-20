#!/usr/bin/env python3
"""Batch-embed IPTC/EXIF/XMP metadata into a folder of photos with exiftool.

Reads a JSON manifest of constant fields (byline, credit, license, location) plus
per-image alt text, caption, and keywords; writes tagged copies (originals are left
untouched by default); then reads each file back to confirm the metadata landed.

No network and no credentials: this operates only on local files. Requires exiftool
on PATH (https://exiftool.org). See reference.md for the field map and byte limits.

Manifest shape:

    {
      "constants": {
        "by_line": "Dana Rivera",
        "creator": "Dana Rivera",
        "credit": "Example News",                       // org only, max 32 chars
        "credit_full": "Dana Rivera / Example News",     // full credit, XMP (no limit)
        "copyright": "(c) 2026 Example News. CC BY 4.0.",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "attribution_name": "Dana Rivera / Example News",
        "attribution_url": "https://example.org",
        "usage_terms": "Licensed CC BY 4.0. Credit: Dana Rivera/Example News.",
        "headline": "Editorial framing goes here, not in the caption",
        "sub_location": "Courthouse steps",
        "city": "Trenton", "state": "New Jersey",
        "country": "United States", "country_code": "USA"
      },
      "images": {
        "test-001.jpg": {
          "alt": "A crowd holding signs stands on courthouse steps.",
          "caption": "A crowd holds signs ... (Dana Rivera/Example News)",
          "keywords": ["protest", "courthouse", "Trenton"]
        }
      }
    }

All keys are optional; only fields that are present get written, and the read-back
check only requires the fields a given image actually asked for.

Usage:
    python3 embed.py --dir ./photos --manifest manifest.json
    python3 embed.py --dir ./photos --manifest manifest.json --out ./tagged
    python3 embed.py --dir ./photos --manifest manifest.json --in-place
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

# constant manifest key -> list of exiftool tags it writes to
CONST_TAGS = {
    "by_line": ["-IPTC:By-line=", "-XMP-dc:Creator=", "-EXIF:Artist="],
    "creator": ["-XMP-dc:Creator=", "-EXIF:Artist="],
    "credit": ["-IPTC:Credit="],
    "credit_full": ["-XMP-photoshop:Credit="],
    "copyright": ["-IPTC:CopyrightNotice=", "-XMP-dc:Rights=", "-EXIF:Copyright="],
    "license_url": ["-XMP-cc:License=", "-XMP-xmpRights:WebStatement="],
    "attribution_name": ["-XMP-cc:AttributionName="],
    "attribution_url": ["-XMP-cc:AttributionURL="],
    "usage_terms": ["-XMP-xmpRights:UsageTerms=", "-IPTC:SpecialInstructions="],
    "headline": ["-IPTC:Headline=", "-XMP-photoshop:Headline="],
    "sub_location": ["-IPTC:Sub-location=", "-XMP-iptcCore:Location="],
    "city": ["-IPTC:City=", "-XMP-photoshop:City="],
    "state": ["-IPTC:Province-State=", "-XMP-photoshop:State="],
    "country": ["-IPTC:Country-PrimaryLocationName=", "-XMP-photoshop:Country="],
    "country_code": ["-IPTC:Country-PrimaryLocationCode=", "-XMP-iptcCore:CountryCode="],
}
CAPTION_TAGS = [
    "-IPTC:Caption-Abstract=", "-XMP-dc:Description=",
    "-EXIF:ImageDescription=", "-XMP-iptcCore:ExtDescrAccessibility=",
]
# IPTC-IIM byte caps for constant fields; exiftool truncates silently without -m.
# One entry per byte-capped key build_args() writes, so the warning set matches the
# write set. (country_code is the 3-byte ISO 3166 alpha-3 code.)
BYTE_LIMITS = {
    "by_line": 32, "credit": 32, "city": 32, "state": 32,
    "sub_location": 32, "country": 64, "country_code": 3,
    "headline": 256, "copyright": 128, "usage_terms": 256,
}
CAPTION_LIMIT = 2000   # IPTC:Caption-Abstract
KEYWORD_LIMIT = 64     # IPTC:Keywords, per record

# verify(): the canonical read-back tag per constant field, with its `-G1` JSON key.
# We confirm PRESENCE (the tag is non-empty), not equality — byte-capped IIM fields
# are expected to truncate (warned up front), so an equality check would false-fail.
# Prefer an uncapped XMP layer where one exists. EXIF tags are skipped here because
# `-G1` names them by IFD (IFD0:Artist), not by the "EXIF" group.
VERIFY_TAGS = {
    "by_line":          ("-IPTC:By-line", "IPTC:By-line"),
    "creator":          ("-XMP-dc:Creator", "XMP-dc:Creator"),
    "credit":           ("-IPTC:Credit", "IPTC:Credit"),
    "credit_full":      ("-XMP-photoshop:Credit", "XMP-photoshop:Credit"),
    "copyright":        ("-XMP-dc:Rights", "XMP-dc:Rights"),
    "license_url":      ("-XMP-cc:License", "XMP-cc:License"),
    "attribution_name": ("-XMP-cc:AttributionName", "XMP-cc:AttributionName"),
    "attribution_url":  ("-XMP-cc:AttributionURL", "XMP-cc:AttributionURL"),
    "usage_terms":      ("-XMP-xmpRights:UsageTerms", "XMP-xmpRights:UsageTerms"),
    "headline":         ("-XMP-photoshop:Headline", "XMP-photoshop:Headline"),
    "sub_location":     ("-XMP-iptcCore:Location", "XMP-iptcCore:Location"),
    "city":             ("-XMP-photoshop:City", "XMP-photoshop:City"),
    "state":            ("-XMP-photoshop:State", "XMP-photoshop:State"),
    "country":          ("-XMP-photoshop:Country", "XMP-photoshop:Country"),
    "country_code":     ("-XMP-iptcCore:CountryCode", "XMP-iptcCore:CountryCode"),
}


def build_args(constants, per_image):
    """Return the list of exiftool tag arguments for one image."""
    args = ["-codedcharacterset=utf8"]
    # Collect constant tags into an ordered map keyed by exiftool tag, so overlapping
    # manifest keys (by_line and creator both touch dc:Creator/Artist) assign each
    # tag once instead of emitting a duplicate value. Iterate CONST_TAGS for a stable
    # order; a later key (creator) overrides an earlier one (by_line) for shared tags.
    const_args = {}
    for key in CONST_TAGS:
        value = constants.get(key)
        if value is None or value == "":
            continue
        for tag in CONST_TAGS[key]:
            const_args[tag] = f"{tag}{value}"
    args += list(const_args.values())

    caption = per_image.get("caption")
    if caption:
        for tag in CAPTION_TAGS:
            args.append(f"{tag}{caption}")

    alt = per_image.get("alt")
    if alt:
        args.append(f"-XMP-iptcCore:AltTextAccessibility={alt}")

    keywords = per_image.get("keywords") or []
    if keywords:
        # clear then add, so re-running is idempotent rather than appending duplicates
        args += ["-IPTC:Keywords=", "-XMP-dc:Subject="]
        for kw in keywords:
            args += [f"-IPTC:Keywords+={kw}", f"-XMP-dc:Subject+={kw}"]

    if constants.get("license_url"):
        args.append("-XMP-xmpRights:Marked=True")

    # copy the real shot date/time from the camera rather than inventing one. IPTC
    # splits date and time, so copy both; XMP photoshop:DateCreated holds the full stamp.
    args += [
        "-IPTC:DateCreated<EXIF:DateTimeOriginal",
        "-IPTC:TimeCreated<EXIF:DateTimeOriginal",
        "-XMP-photoshop:DateCreated<EXIF:DateTimeOriginal",
    ]
    return args


def _too_long(value, limit):
    return value is not None and len(str(value).encode("utf-8")) > limit


def warn_byte_limits(constants):
    """Warn about constant fields that exceed their IPTC-IIM byte cap."""
    for key, limit in BYTE_LIMITS.items():
        value = constants.get(key)
        if _too_long(value, limit):
            n = len(str(value).encode("utf-8"))
            print(f"  warning: '{key}' is {n} bytes (IPTC limit {limit}); "
                  f"it will be truncated in the IPTC layer", file=sys.stderr)


def warn_image_byte_limits(name, per_image):
    """Warn about per-image caption/keywords that exceed their IPTC-IIM byte cap."""
    if _too_long(per_image.get("caption"), CAPTION_LIMIT):
        n = len(str(per_image["caption"]).encode("utf-8"))
        print(f"  warning: {name} caption is {n} bytes (IPTC Caption-Abstract limit "
              f"{CAPTION_LIMIT}); it will be truncated in the IPTC layer", file=sys.stderr)
    for kw in per_image.get("keywords") or []:
        if _too_long(kw, KEYWORD_LIMIT):
            n = len(str(kw).encode("utf-8"))
            print(f"  warning: {name} keyword '{kw}' is {n} bytes (IPTC Keywords limit "
                  f"{KEYWORD_LIMIT}); it will be truncated in the IPTC layer", file=sys.stderr)


def verify(path, const_keys, per_image):
    """Read every requested field back from the written file. Returns (ok, problems).

    `const_keys` are the constant manifest keys that were actually written; this
    image's caption/alt/keywords are checked too. Presence (the tag is non-empty),
    not equality, so a deliberately truncated IIM field is not a false failure — but
    a silently dropped or skipped tag (e.g. a non-writable spelling) does fail.
    """
    read_args, checks = [], []
    for key in const_keys:
        if key in VERIFY_TAGS:
            arg, json_key = VERIFY_TAGS[key]
            read_args.append(arg)
            checks.append((key, json_key))
    if per_image.get("caption"):
        read_args.append("-IPTC:Caption-Abstract")
        checks.append(("caption", "IPTC:Caption-Abstract"))
    if per_image.get("alt"):
        read_args.append("-XMP-iptcCore:AltTextAccessibility")
        checks.append(("alt", "XMP-iptcCore:AltTextAccessibility"))
    want_keywords = per_image.get("keywords") or []
    if want_keywords:
        read_args.append("-IPTC:Keywords")
    # The date copy is always attempted, so always confirm it: if the file carries a
    # shot date it must have landed in all three copy targets (IPTC date + time and
    # the XMP date). Under -G1, DateTimeOriginal is grouped as ExifIFD. (A file with
    # no shot date is fine — there is nothing to copy.)
    read_args += ["-EXIF:DateTimeOriginal", "-IPTC:DateCreated",
                  "-IPTC:TimeCreated", "-XMP-photoshop:DateCreated"]

    out = subprocess.run(
        ["exiftool", "-G1", "-j", *read_args, "--", str(path)],
        capture_output=True, text=True,
    )
    if out.returncode != 0 or not out.stdout.strip():
        return False, ["could not read file back"]
    data = json.loads(out.stdout)[0]
    problems = [f"missing {label}" for label, json_key in checks if not data.get(json_key)]
    if want_keywords:
        got = data.get("IPTC:Keywords")
        got = [got] if isinstance(got, str) else (got or [])
        missing = [k for k in want_keywords if k not in got]
        if missing:
            problems.append("missing keywords: " + ", ".join(missing))
    if data.get("ExifIFD:DateTimeOriginal"):
        for json_key in ("IPTC:DateCreated", "IPTC:TimeCreated", "XMP-photoshop:DateCreated"):
            if not data.get(json_key):
                problems.append(f"shot date present but {json_key} not copied")
    return (not problems), problems


def main():
    ap = argparse.ArgumentParser(
        description="Batch-embed wire metadata into photos with exiftool.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--dir", required=True, help="folder of source images")
    ap.add_argument("--manifest", required=True, help="JSON manifest path")
    ap.add_argument("--out", help="output folder (default: <dir>/tagged)")
    ap.add_argument("--in-place", action="store_true",
                    help="overwrite originals instead of writing copies")
    args = ap.parse_args()

    # --in-place overwrites originals; refuse to pair it with an explicit --out so a
    # stray flag can never turn a safe copy into a destructive overwrite.
    if args.in_place and args.out:
        ap.error("--in-place and --out are mutually exclusive")

    if not shutil.which("exiftool"):
        sys.exit("error: exiftool not found on PATH (https://exiftool.org)")

    src = Path(args.dir)
    if not src.is_dir():
        sys.exit(f"error: --dir is not a folder: {src}")
    src_resolved = src.resolve()

    try:
        manifest = json.loads(Path(args.manifest).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"error: cannot read manifest: {exc}")
    constants = manifest.get("constants", {})
    images = manifest.get("images", {})
    if not isinstance(constants, dict) or not isinstance(images, dict):
        sys.exit("error: manifest 'constants' and 'images' must be objects")
    if not images:
        sys.exit("error: manifest has no images")

    warn_byte_limits(constants)

    out_dir = src if args.in_place else Path(args.out) if args.out else src / "tagged"
    if not args.in_place:
        out_dir.mkdir(parents=True, exist_ok=True)

    ok = failed = missing = 0
    for name, per_image in images.items():
        # Reject manifest keys that escape the source folder (e.g. "../secret.jpg").
        # In --in-place mode this would otherwise let a manifest rewrite arbitrary files.
        try:
            (src / name).resolve().relative_to(src_resolved)
        except (ValueError, OSError):
            print(f"  rejected: {name} (path escapes {src})", file=sys.stderr)
            failed += 1
            continue

        source = src / name
        if not source.is_file():
            print(f"  missing: {name} (not in {src})", file=sys.stderr)
            missing += 1
            continue

        warn_image_byte_limits(name, per_image)

        target = source if args.in_place else out_dir / name
        if not args.in_place:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        # `--` ends option parsing so a filename beginning with "-" (e.g. "-foo.jpg"
        # reached via "--dir . --in-place") is treated as a path, not an exiftool option.
        cmd = ["exiftool", "-m", "-overwrite_original"]
        cmd += build_args(constants, per_image)
        cmd += ["--", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  failed: {name}: {result.stderr.strip()}", file=sys.stderr)
            failed += 1
            continue

        # Verify every constant field that was actually written, plus this image's
        # caption/alt/keywords, so a silently dropped or skipped tag fails the run.
        const_keys = [k for k, v in constants.items()
                      if k in VERIFY_TAGS and v not in (None, "")]
        good, problems = verify(target, const_keys, per_image)
        if good:
            ok += 1
        else:
            failed += 1
            print(f"  verify failed: {name}: {', '.join(problems)}", file=sys.stderr)

    where = "in place" if args.in_place else str(out_dir)
    print(f"done: {ok} tagged ({where}), {failed} failed, {missing} missing")
    sys.exit(1 if (failed or missing) else 0)


if __name__ == "__main__":
    main()
