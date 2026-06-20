#!/usr/bin/env python3
"""Black-box tests for embed.py — run with `python3 -m unittest` from this dir.

Needs exiftool on PATH and Pillow (for generating fixture JPEGs). Each test runs
embed.py as a CLI against a throwaway temp folder, then reads the result back with
exiftool, so the tests exercise the real write/verify path rather than internals.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
EMBED = HERE / "embed.py"


def have(cmd):
    return shutil.which(cmd) is not None


def make_jpeg(path, size=(48, 32)):
    from PIL import Image
    Image.new("RGB", size, (200, 60, 60)).save(path, "JPEG")


def read_back(path):
    out = subprocess.run(
        ["exiftool", "-j", "-IPTC:By-line", "-IPTC:Caption-Abstract",
         "-XMP-iptcCore:AltTextAccessibility", "-IPTC:Keywords", path],
        capture_output=True, text=True,
    )
    return json.loads(out.stdout)[0] if out.returncode == 0 and out.stdout.strip() else {}


def run_embed(*args, cwd=None):
    return subprocess.run([sys.executable, str(EMBED), *args],
                          capture_output=True, text=True, cwd=cwd)


@unittest.skipUnless(have("exiftool"), "exiftool not installed")
class EmbedCLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "photos"
        self.src.mkdir()
        make_jpeg(self.src / "a.jpg")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def write_manifest(self, manifest):
        p = self.tmp / "manifest.json"
        p.write_text(json.dumps(manifest))
        return p

    def test_minimal_write_and_verify(self):
        m = self.write_manifest({
            "constants": {"by_line": "Dana Rivera", "credit_full": "Dana Rivera / Example"},
            "images": {"a.jpg": {"caption": "A red rectangle.", "alt": "A solid red rectangle.",
                                 "keywords": ["test", "fixture"]}},
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        self.assertEqual(r.returncode, 0, r.stderr)
        data = read_back(str(self.src / "tagged" / "a.jpg"))
        self.assertEqual(data.get("By-line"), "Dana Rivera")
        self.assertEqual(data.get("AltTextAccessibility"), "A solid red rectangle.")

    def test_optional_fields_only_alt_is_success(self):
        # Manifest sets only alt text — no byline, no caption. The write succeeds,
        # so the run must report success (verify must not demand fields nobody asked for).
        m = self.write_manifest({
            "constants": {},
            "images": {"a.jpg": {"alt": "A solid red rectangle."}},
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")
        data = read_back(str(self.src / "tagged" / "a.jpg"))
        self.assertEqual(data.get("AltTextAccessibility"), "A solid red rectangle.")

    def test_creator_only_manifest_is_success(self):
        # `creator` without `by_line` writes Creator/Artist but no IPTC By-line; the
        # run must still succeed (verify the field that was actually written).
        m = self.write_manifest({
            "constants": {"creator": "Dana Rivera"},
            "images": {"a.jpg": {"caption": "A red rectangle."}},
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")

    def test_in_place_and_out_are_mutually_exclusive(self):
        m = self.write_manifest({"constants": {}, "images": {"a.jpg": {"alt": "x"}}})
        r = run_embed("--dir", str(self.src), "--manifest", str(m),
                      "--in-place", "--out", str(self.tmp / "out"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("mutually exclusive", (r.stderr + r.stdout).lower())

    def test_manifest_path_traversal_is_rejected(self):
        # A valid JPEG sits OUTSIDE the source folder; a manifest name escapes to it.
        outside = self.tmp / "outside.jpg"
        make_jpeg(outside)
        m = self.write_manifest({
            "constants": {"by_line": "Mallory"},
            "images": {"../outside.jpg": {"caption": "should not be written"}},
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m), "--in-place")
        self.assertNotEqual(r.returncode, 0)
        # the file outside the folder must be untouched
        self.assertEqual(read_back(str(outside)).get("By-line"), None)

    def test_exif_datetime_copies_to_iptc_date_and_time(self):
        # A real EXIF shot time must land in BOTH IPTC DateCreated and TimeCreated,
        # not just the date (IPTC splits the two fields).
        subprocess.run(["exiftool", "-overwrite_original",
                        "-EXIF:DateTimeOriginal=2026:06:19 14:30:00",
                        "--", str(self.src / "a.jpg")], capture_output=True, text=True)
        m = self.write_manifest({"constants": {"by_line": "Dana"},
                                 "images": {"a.jpg": {"caption": "A red rectangle."}}})
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        self.assertEqual(r.returncode, 0, r.stderr)
        out = subprocess.run(["exiftool", "-G1", "-j", "-IPTC:DateCreated",
                              "-IPTC:TimeCreated", "-XMP-photoshop:DateCreated",
                              "--", str(self.src / "tagged" / "a.jpg")],
                             capture_output=True, text=True)
        data = json.loads(out.stdout)[0]
        self.assertIn("2026:06:19", data.get("IPTC:DateCreated", ""))   # date
        self.assertIn("14:30:00", data.get("IPTC:TimeCreated", ""))     # time
        self.assertTrue(data.get("XMP-photoshop:DateCreated"))          # XMP date

    def test_country_code_lands_in_both_iptc_and_xmp(self):
        # country_code must write the IPTC code AND a *writable* XMP tag. The
        # XMP-iptcExt spelling is not writable and was silently dropped under -m.
        m = self.write_manifest({
            "constants": {"by_line": "Dana", "country_code": "USA"},
            "images": {"a.jpg": {"caption": "A red rectangle."}},
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        self.assertEqual(r.returncode, 0, r.stderr)
        out = subprocess.run(
            ["exiftool", "-G1", "-j", "-IPTC:Country-PrimaryLocationCode",
             "-XMP-iptcCore:CountryCode", "--", str(self.src / "tagged" / "a.jpg")],
            capture_output=True, text=True)
        data = json.loads(out.stdout)[0]
        self.assertEqual(data.get("IPTC:Country-PrimaryLocationCode"), "USA")
        self.assertEqual(data.get("XMP-iptcCore:CountryCode"), "USA")

    def test_full_constant_set_all_fields_land(self):
        # Every constant field must be written with a writable tag and survive the
        # round-trip. This also audits CONST_TAGS for non-writable tags (the class
        # the country_code bug belonged to). Values stay under the IIM byte caps.
        consts = {
            "by_line": "Dana Rivera", "creator": "Dana Rivera",
            "credit": "Example News", "credit_full": "Dana Rivera / Example News",
            "copyright": "(c) 2026 Example News. CC BY 4.0.",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "attribution_name": "Dana Rivera / Example News",
            "attribution_url": "https://example.org",
            "usage_terms": "Licensed CC BY 4.0.",
            "headline": "Editorial framing here",
            "sub_location": "Courthouse steps", "city": "Trenton",
            "state": "New Jersey", "country": "United States", "country_code": "USA",
        }
        m = self.write_manifest({"constants": consts,
                                 "images": {"a.jpg": {"caption": "A red rectangle."}}})
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")
        tagged = str(self.src / "tagged" / "a.jpg")
        g1_keys = [
            "IPTC:By-line", "XMP-dc:Creator", "IPTC:Credit", "XMP-photoshop:Credit",
            "IPTC:CopyrightNotice", "XMP-dc:Rights", "XMP-cc:License",
            "XMP-xmpRights:WebStatement", "XMP-cc:AttributionName",
            "XMP-cc:AttributionURL", "XMP-xmpRights:UsageTerms",
            "IPTC:SpecialInstructions", "IPTC:Headline", "XMP-photoshop:Headline",
            "IPTC:Sub-location", "XMP-iptcCore:Location", "IPTC:City",
            "XMP-photoshop:City", "IPTC:Province-State", "XMP-photoshop:State",
            "IPTC:Country-PrimaryLocationName", "XMP-photoshop:Country",
            "IPTC:Country-PrimaryLocationCode", "XMP-iptcCore:CountryCode",
        ]
        out = subprocess.run(["exiftool", "-G1", "-j", *[f"-{k}" for k in g1_keys],
                              "--", tagged], capture_output=True, text=True)
        data = json.loads(out.stdout)[0]
        for key in g1_keys:
            self.assertTrue(data.get(key), f"missing {key}: {data}")
        # by_line and creator both touch dc:Creator; it must not be written twice.
        self.assertEqual(data.get("XMP-dc:Creator"), "Dana Rivera")
        # EXIF tags use IFD group names under -G1, so read them plainly.
        exif = subprocess.run(["exiftool", "-s3", "-EXIF:Artist", "-EXIF:Copyright",
                               "--", tagged], capture_output=True, text=True)
        self.assertIn("Dana Rivera", exif.stdout)
        self.assertIn("Example News", exif.stdout)

    def test_overlong_byte_limited_fields_warn(self):
        # Every byte-capped field build_args() writes must warn when overlong, so the
        # warning set matches the write set (quoted keys disambiguate country vs code).
        m = self.write_manifest({
            "constants": {"headline": "H" * 300, "copyright": "C" * 200,
                          "usage_terms": "U" * 300, "sub_location": "S" * 40,
                          "country": "C" * 70, "country_code": "ABCD"},
            "images": {"a.jpg": {"alt": "x"}},
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        warn = r.stderr + r.stdout
        for key in ("'headline'", "'copyright'", "'usage_terms'",
                    "'sub_location'", "'country'", "'country_code'"):
            self.assertIn(key, warn)

    def test_dash_prefixed_filename_is_handled(self):
        # With "--dir . --in-place" the path handed to exiftool is "-dash.jpg", which
        # exiftool would parse as an option unless the command ends options with "--".
        make_jpeg(self.src / "-dash.jpg")
        m = self.write_manifest({
            "constants": {"by_line": "Dana"},
            "images": {"-dash.jpg": {"caption": "A red rectangle."}},
        })
        r = run_embed("--dir", ".", "--manifest", str(m), "--in-place", cwd=str(self.src))
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")
        self.assertEqual(read_back(str(self.src / "-dash.jpg")).get("By-line"), "Dana")


if __name__ == "__main__":
    unittest.main(verbosity=2)
