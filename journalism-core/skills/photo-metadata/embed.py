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
        "web_statement": "https://example.org/license/123", // license-details page (Google)
        "licensor_name": "Example News",                 // "Get this image on ..." (Google)
        "licensor_url": "https://example.org/buy/123",
        "attribution_name": "Dana Rivera / Example News",
        "attribution_url": "https://example.org",
        "usage_terms": "Licensed CC BY 4.0. Credit: Dana Rivera/Example News.",
        "headline": "Editorial framing goes here, not in the caption",
        "digital_source_type": "digitalCapture",         // how the image was made (see below)
        "sub_location": "Courthouse steps",
        "city": "Trenton", "state": "New Jersey",
        "country": "United States", "country_code": "USA"
      },
      "images": {
        "test-001.jpg": {
          "alt": "A crowd holding signs stands on courthouse steps.",
          "caption": "A crowd holds signs ... (Dana Rivera/Example News)",
          "ext_description": "Longer screen-reader description for a complex image.",
          "keywords": ["protest", "courthouse", "Trenton"],
          "digital_source_type": "trainedAlgorithmicMedia" // per-image override of the constant
        }
      }
    }

All keys are optional; only fields that are present get written, and the read-back
check only requires the fields a given image actually asked for.

`digital_source_type` records how the image was made, using the IPTC "Digital Source
Type" controlled vocabulary. Pass a known shorthand (below) or a full CV URI; anything
else is warned and skipped rather than written as a broken value. A per-image value
overrides the constant. Newsroom-relevant values:

    digitalCapture                       straight photo from a camera (the news default)
    computationalCapture                 in-camera stack, e.g. HDR / night mode (non-AI)
    humanEdits                           human retouch/toning with non-generative tools
    algorithmicallyEnhanced              sharpen / denoise, no content change
    compositeCapture                     composite whose elements are all real captures
    compositeSynthetic                   composite with at least one generative-AI element
    compositeWithTrainedAlgorithmicMedia real media edited with generative AI (inpaint/outpaint)
    trainedAlgorithmicMedia              fully AI-generated (a trained model)
    algorithmicMedia                     pure algorithm, no training data (e.g. a fractal)

Usage:
    python3 embed.py --dir ./photos --manifest manifest.json
    python3 embed.py --dir ./photos --manifest manifest.json --out ./tagged
    python3 embed.py --dir ./photos --manifest manifest.json --in-place
    python3 embed.py --dir ./photos --manifest manifest.json --strip-gps
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

# constant manifest key -> list of exiftool tags it writes to.
# license_url is listed before web_statement so that if both are set, the more specific
# web_statement wins the shared WebStatement tag (build_args dedups by tag, last wins).
CONST_TAGS = {
    "by_line": ["-IPTC:By-line=", "-XMP-dc:Creator=", "-EXIF:Artist="],
    "creator": ["-XMP-dc:Creator=", "-EXIF:Artist="],
    "credit": ["-IPTC:Credit="],
    "credit_full": ["-XMP-photoshop:Credit="],
    "copyright": ["-IPTC:CopyrightNotice=", "-XMP-dc:Rights=", "-EXIF:Copyright="],
    "license_url": ["-XMP-cc:License=", "-XMP-xmpRights:WebStatement="],
    "web_statement": ["-XMP-xmpRights:WebStatement="],
    "licensor_name": ["-XMP-plus:LicensorName="],
    "licensor_url": ["-XMP-plus:LicensorURL="],
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
# The caption is the publishable cutline. It is NOT the accessibility extended
# description (XMP-iptcCore:ExtDescrAccessibility), IPTC keeps those distinct, so the
# caption is not routed there; use the per-image "ext_description" field for that.
CAPTION_TAGS = [
    "-IPTC:Caption-Abstract=", "-XMP-dc:Description=", "-EXIF:ImageDescription=",
]

# IPTC "Digital Source Type" controlled vocabulary (http://cv.iptc.org/newscodes/
# digitalsourcetype/). exiftool writes DigitalSourceType as an unvalidated string, so a
# typo is silently accepted, we expand a known shorthand to the full URI, pass a full
# URL through, and refuse anything else. Retired terms (minorHumanEdits, digitalArt,
# softwareImage) are intentionally excluded. See reference.md for the full vocabulary.
DST_BASE = "http://cv.iptc.org/newscodes/digitalsourcetype/"
DST_IDS = {
    "digitalCapture", "computationalCapture", "negativeFilm", "positiveFilm",
    "print", "humanEdits", "compositeWithTrainedAlgorithmicMedia",
    "algorithmicallyEnhanced", "digitalCreation", "dataDrivenMedia",
    "trainedAlgorithmicMedia", "algorithmicMedia", "screenCapture",
    "virtualRecording", "composite", "compositeCapture", "compositeSynthetic",
}
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
# We confirm PRESENCE (the tag is non-empty), not equality, byte-capped IIM fields
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
    "web_statement":    ("-XMP-xmpRights:WebStatement", "XMP-xmpRights:WebStatement"),
    "licensor_name":    ("-XMP-plus:LicensorName", "XMP-plus:LicensorName"),
    "licensor_url":     ("-XMP-plus:LicensorURL", "XMP-plus:LicensorURL"),
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


def effective_dst(constants, per_image):
    """The digital_source_type in force for one image: per-image overrides constant."""
    return per_image.get("digital_source_type") or constants.get("digital_source_type")


def resolve_dst(value):
    """Return the canonical Digital Source Type CV URI for a value, or None.

    Accepts a known CV shorthand (`digitalCapture`) or a full IPTC CV URI in either
    the `http://` or `https://` form; a full URI is reduced to its trailing ID and
    validated against the vocabulary, so a non-IPTC URL or a typo'd ID (e.g.
    `.../trainedAlgorithmicMedi`) returns None and the caller warns and skips it
    rather than embedding a broken value. The result is always the canonical
    `http://` form regardless of how it was written.
    """
    if not value:
        return None
    v = str(value).strip()
    for scheme in (DST_BASE, DST_BASE.replace("http://", "https://", 1)):
        if v.startswith(scheme):
            v = v[len(scheme):]      # reduce a full CV URI to its bare ID
            break
    if v in DST_IDS:
        return DST_BASE + v
    return None


def build_args(constants, per_image, dst_uri=None):
    """Return the list of exiftool tag arguments for one image.

    `dst_uri` is the already-resolved Digital Source Type URI (or None); it is resolved
    by the caller so the same value drives both the write and the read-back check.
    """
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

    # Extended accessibility description, a longer screen-reader text for a complex
    # image (a chart, an infographic). Distinct from both the alt text and the caption.
    ext = per_image.get("ext_description")
    if ext:
        args.append(f"-XMP-iptcCore:ExtDescrAccessibility={ext}")

    if dst_uri:
        args.append(f"-XMP-iptcExt:DigitalSourceType={dst_uri}")

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


def verify(path, const_keys, per_image, dst_uri=None):
    """Read every requested field back from the written file. Returns (ok, problems).

    `const_keys` are the constant manifest keys that were actually written; this
    image's caption/alt/ext_description/keywords and its resolved Digital Source Type
    are checked too. Presence (the tag is non-empty), not equality, so a deliberately
    truncated IIM field is not a false failure, but a silently dropped or skipped tag
    (e.g. a non-writable spelling) does fail.
    """
    # Each check is (label, [json_keys]); it passes if ANY of the keys is non-empty.
    # by_line/caption/keywords list both the IIM tag and its XMP twin, because
    # HEIC/AVIF/WebP have no IIM slot, there exiftool writes only the XMP copy, so a
    # valid write would false-fail if we demanded the IIM tag. On JPEG both are present.
    read_args, checks = [], []
    for key in const_keys:
        if key == "by_line":
            read_args += ["-IPTC:By-line", "-XMP-dc:Creator"]
            checks.append(("by_line", ["IPTC:By-line", "XMP-dc:Creator"]))
        elif key in VERIFY_TAGS:
            arg, json_key = VERIFY_TAGS[key]
            read_args.append(arg)
            checks.append((key, [json_key]))
    if per_image.get("caption"):
        read_args += ["-IPTC:Caption-Abstract", "-XMP-dc:Description"]
        checks.append(("caption", ["IPTC:Caption-Abstract", "XMP-dc:Description"]))
    if per_image.get("alt"):
        read_args.append("-XMP-iptcCore:AltTextAccessibility")
        checks.append(("alt", ["XMP-iptcCore:AltTextAccessibility"]))
    if per_image.get("ext_description"):
        read_args.append("-XMP-iptcCore:ExtDescrAccessibility")
        checks.append(("ext_description", ["XMP-iptcCore:ExtDescrAccessibility"]))
    if dst_uri:
        read_args.append("-XMP-iptcExt:DigitalSourceType")
        checks.append(("digital_source_type", ["XMP-iptcExt:DigitalSourceType"]))
    want_keywords = per_image.get("keywords") or []
    if want_keywords:
        read_args += ["-IPTC:Keywords", "-XMP-dc:Subject"]
    # The date copy is always attempted, so confirm it. Under -G1, DateTimeOriginal is
    # grouped as ExifIFD. (A file with no shot date is fine, there is nothing to copy.)
    read_args += ["-EXIF:DateTimeOriginal", "-IPTC:DateCreated",
                  "-IPTC:TimeCreated", "-XMP-photoshop:DateCreated"]

    out = subprocess.run(
        ["exiftool", "-G1", "-j", *read_args, "--", str(path)],
        capture_output=True, text=True,
    )
    if out.returncode != 0 or not out.stdout.strip():
        return False, ["could not read file back"]
    data = json.loads(out.stdout)[0]
    problems = [f"missing {label}" for label, json_keys in checks
                if not any(data.get(k) for k in json_keys)]
    if want_keywords:
        got = []
        for k in ("IPTC:Keywords", "XMP-dc:Subject"):     # union of both layers
            v = data.get(k)
            got += [v] if isinstance(v, str) else (v or [])
        missing = [k for k in want_keywords if k not in got]
        if missing:
            problems.append("missing keywords: " + ", ".join(missing))
    if data.get("ExifIFD:DateTimeOriginal"):
        # XMP-photoshop:DateCreated is the format-agnostic proof the copy ran. The IPTC
        # date/time split only exists where there is an IIM block; require both there
        # (the bug this guards), but do not demand them on a no-IIM format.
        if not data.get("XMP-photoshop:DateCreated"):
            problems.append("shot date present but XMP-photoshop:DateCreated not copied")
        if data.get("IPTC:DateCreated") or data.get("IPTC:TimeCreated"):
            for json_key in ("IPTC:DateCreated", "IPTC:TimeCreated"):
                if not data.get(json_key):
                    problems.append(f"shot date present but {json_key} not copied")
    return (not problems), problems


def strip_gps(path):
    """Remove GPS coordinates from a file, keeping every editorial tag. Returns True on
    success. Clears the whole EXIF GPS IFD (`-gps:all=`) and the entire XMP GPS set
    (`-xmp:GPS*=`), the wildcard catches destination and image-direction fields
    (`GPSDestLatitude`, `GPSImgDirection`, …), not just the three main coordinates, so
    a publish-safe derivative cannot leak a location through a field left behind. Other
    metadata, caption, credit, copyright, Digital Source Type, is untouched.
    """
    out = subprocess.run(
        ["exiftool", "-m", "-overwrite_original",
         "-gps:all=", "-xmp:GPS*=",
         "--", str(path)],
        capture_output=True, text=True,
    )
    return out.returncode == 0


def main():
    ap = argparse.ArgumentParser(
        description="Batch-embed wire metadata into photos with exiftool.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--dir", required=True, help="folder of source images")
    ap.add_argument("--manifest", required=True, help="JSON manifest path")
    ap.add_argument("--out", help="output folder (default: <dir>/tagged)")
    ap.add_argument("--in-place", action="store_true",
                    help="overwrite originals instead of writing copies")
    ap.add_argument("--strip-gps", action="store_true",
                    help="remove GPS from each tagged file (keeps editorial metadata) "
                         ", for a publish-safe derivative that won't leak a location")
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

        # Resolve the Digital Source Type once (per-image overrides constant); a value
        # that is neither a known shorthand nor a URL is warned and skipped, not written.
        dst_raw = effective_dst(constants, per_image)
        dst_uri = resolve_dst(dst_raw)
        if dst_raw and dst_uri is None:
            print(f"  warning: {name} digital_source_type '{dst_raw}' is not a known "
                  f"shorthand or URL; skipped (see reference.md)", file=sys.stderr)

        target = source if args.in_place else out_dir / name
        if not args.in_place:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        # `--` ends option parsing so a filename beginning with "-" (e.g. "-foo.jpg"
        # reached via "--dir . --in-place") is treated as a path, not an exiftool option.
        cmd = ["exiftool", "-m", "-overwrite_original"]
        cmd += build_args(constants, per_image, dst_uri)
        cmd += ["--", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  failed: {name}: {result.stderr.strip()}", file=sys.stderr)
            failed += 1
            continue

        # Optional publish-safe step: drop GPS after embedding, keeping editorial tags.
        if args.strip_gps and not strip_gps(target):
            print(f"  failed: {name}: could not strip GPS", file=sys.stderr)
            failed += 1
            continue

        # Verify every constant field that was actually written, plus this image's
        # caption/alt/ext_description/keywords and its Digital Source Type, so a silently
        # dropped or skipped tag fails the run.
        const_keys = [k for k, v in constants.items()
                      if k in VERIFY_TAGS and v not in (None, "")]
        good, problems = verify(target, const_keys, per_image, dst_uri)
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
