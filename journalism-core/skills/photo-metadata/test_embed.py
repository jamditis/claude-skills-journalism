#!/usr/bin/env python3
"""Black-box tests for embed.py, run with `python3 -m unittest` from this dir.

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
        # Manifest sets only alt text, no byline, no caption. The write succeeds,
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

    def test_digital_source_type_shorthand_expands_to_full_uri(self):
        # A newsroom shorthand must be written as the full IPTC CV URI, exiftool does
        # not validate DigitalSourceType, so the tool is responsible for the URI.
        m = self.write_manifest({
            "constants": {"digital_source_type": "digitalCapture"},
            "images": {"a.jpg": {"caption": "A red rectangle."}},
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")
        out = subprocess.run(["exiftool", "-s3", "-XMP-iptcExt:DigitalSourceType",
                              "--", str(self.src / "tagged" / "a.jpg")],
                             capture_output=True, text=True)
        self.assertEqual(
            out.stdout.strip(),
            "http://cv.iptc.org/newscodes/digitalsourcetype/digitalCapture")

    def test_digital_source_type_ai_value_and_per_image_override(self):
        # A per-image value overrides the constant, so a folder can mix a real photo
        # with an AI illustration and label each honestly.
        make_jpeg(self.src / "ai.jpg")
        m = self.write_manifest({
            "constants": {"digital_source_type": "digitalCapture"},
            "images": {
                "a.jpg": {"caption": "A real photo."},
                "ai.jpg": {"caption": "An AI illustration.",
                           "digital_source_type": "trainedAlgorithmicMedia"},
            },
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")

        def dst(name):
            out = subprocess.run(["exiftool", "-s3", "-XMP-iptcExt:DigitalSourceType",
                                  "--", str(self.src / "tagged" / name)],
                                 capture_output=True, text=True)
            return out.stdout.strip()
        self.assertTrue(dst("a.jpg").endswith("/digitalCapture"))
        self.assertTrue(dst("ai.jpg").endswith("/trainedAlgorithmicMedia"))

    def test_digital_source_type_full_uri_normalizes_to_http(self):
        # An https CV URI is accepted and normalized to the canonical http form.
        m = self.write_manifest({
            "constants": {},
            "images": {"a.jpg": {"caption": "x",
                "digital_source_type":
                    "https://cv.iptc.org/newscodes/digitalsourcetype/compositeSynthetic"}},
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")
        out = subprocess.run(["exiftool", "-s3", "-XMP-iptcExt:DigitalSourceType",
                              "--", str(self.src / "tagged" / "a.jpg")],
                             capture_output=True, text=True)
        self.assertEqual(
            out.stdout.strip(),
            "http://cv.iptc.org/newscodes/digitalsourcetype/compositeSynthetic")

    def test_digital_source_type_typo_and_non_iptc_urls_are_rejected(self):
        # A typo'd CV id or a non-IPTC URL must be warned and skipped, not written as
        # broken provenance that a non-empty read-back would wave through.
        for bad in ("https://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedi",
                    "https://example.com/ai"):
            make_jpeg(self.src / "b.jpg")
            m = self.write_manifest({
                "constants": {},
                "images": {"b.jpg": {"caption": "x", "digital_source_type": bad}},
            })
            r = run_embed("--dir", str(self.src), "--manifest", str(m))
            self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")
            self.assertIn("digital_source_type", (r.stderr + r.stdout))
            out = subprocess.run(["exiftool", "-s3", "-XMP-iptcExt:DigitalSourceType",
                                  "--", str(self.src / "tagged" / "b.jpg")],
                                 capture_output=True, text=True)
            self.assertEqual(out.stdout.strip(), "", f"wrote broken value for {bad!r}")

    def test_strip_gps_clears_destination_coordinates_too(self):
        # A publish-safe strip must clear the whole XMP GPS set, not just the three
        # main coordinates: GPSDest* is also a location and must not survive.
        subprocess.run(["exiftool", "-overwrite_original",
                        "-GPSLatitude=40.7", "-GPSLatitudeRef=N",
                        "-GPSLongitude=74.0", "-GPSLongitudeRef=W",
                        "-XMP-exif:GPSDestLatitude=41.0", "-XMP-exif:GPSDestLongitude=75.0",
                        "--", str(self.src / "a.jpg")], capture_output=True, text=True)
        m = self.write_manifest({"constants": {"by_line": "Dana"},
                                 "images": {"a.jpg": {"caption": "x"}}})
        r = run_embed("--dir", str(self.src), "--manifest", str(m), "--strip-gps")
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")
        gps = subprocess.run(["exiftool", "-a", "-G1", "-gps:all", "-XMP-exif:all",
                              "--", str(self.src / "tagged" / "a.jpg")],
                             capture_output=True, text=True)
        self.assertNotIn("GPS", gps.stdout, f"GPS survived strip: {gps.stdout}")

    def test_webp_no_iim_format_verifies_via_xmp(self):
        # HEIC/AVIF/WebP have no IIM slot: exiftool writes only XMP, so verify must not
        # false-fail a valid XMP-only write by demanding the IPTC read-back tags.
        from PIL import Image
        Image.new("RGB", (48, 32), (20, 80, 20)).save(self.src / "a.webp", "WEBP")
        m = self.write_manifest({
            "constants": {"by_line": "Dana Rivera", "digital_source_type": "digitalCapture"},
            "images": {"a.webp": {"caption": "A green frame.",
                                  "alt": "A solid green rectangle.",
                                  "keywords": ["test", "webp"]}},
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")
        out = subprocess.run(
            ["exiftool", "-G1", "-j", "-XMP-dc:Creator", "-XMP-dc:Description",
             "-XMP-dc:Subject", "-XMP-iptcExt:DigitalSourceType",
             "--", str(self.src / "tagged" / "a.webp")],
            capture_output=True, text=True)
        data = json.loads(out.stdout)[0]
        self.assertEqual(data.get("XMP-dc:Creator"), "Dana Rivera")
        self.assertEqual(data.get("XMP-dc:Description"), "A green frame.")

    def test_unknown_digital_source_type_is_warned_and_skipped(self):
        # A typo must not be embedded as a broken value: warn, skip the tag, still
        # succeed on the fields that did write.
        m = self.write_manifest({
            "constants": {},
            "images": {"a.jpg": {"caption": "x", "digital_source_type": "camera-photo"}},
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")
        self.assertIn("digital_source_type", (r.stderr + r.stdout))
        out = subprocess.run(["exiftool", "-s3", "-XMP-iptcExt:DigitalSourceType",
                              "--", str(self.src / "tagged" / "a.jpg")],
                             capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "")

    def test_google_licensing_fields_land(self):
        # WebStatement (the Licensable trigger) + PLUS Licensor name/URL must round-trip.
        m = self.write_manifest({
            "constants": {
                "web_statement": "https://example.org/license/123",
                "licensor_name": "Example Agency",
                "licensor_url": "https://example.org/buy/123",
            },
            "images": {"a.jpg": {"caption": "x"}},
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")
        out = subprocess.run(
            ["exiftool", "-G1", "-j", "-XMP-xmpRights:WebStatement",
             "-XMP-plus:LicensorName", "-XMP-plus:LicensorURL",
             "--", str(self.src / "tagged" / "a.jpg")],
            capture_output=True, text=True)
        data = json.loads(out.stdout)[0]
        self.assertEqual(data.get("XMP-xmpRights:WebStatement"),
                         "https://example.org/license/123")
        self.assertEqual(data.get("XMP-plus:LicensorName"), "Example Agency")
        self.assertEqual(data.get("XMP-plus:LicensorURL"), "https://example.org/buy/123")

    def test_web_statement_overrides_license_url_web_statement(self):
        # When both license_url and web_statement are set, the more specific
        # web_statement wins the shared WebStatement tag (Google reads the license page).
        m = self.write_manifest({
            "constants": {
                "license_url": "https://creativecommons.org/licenses/by/4.0/",
                "web_statement": "https://example.org/license/123",
            },
            "images": {"a.jpg": {"caption": "x"}},
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")
        out = subprocess.run(["exiftool", "-s3", "-XMP-xmpRights:WebStatement",
                              "-XMP-cc:License", "--", str(self.src / "tagged" / "a.jpg")],
                             capture_output=True, text=True)
        lines = out.stdout.strip().splitlines()
        self.assertEqual(lines[0].strip(), "https://example.org/license/123")  # WebStatement
        self.assertEqual(lines[1].strip(),
                         "https://creativecommons.org/licenses/by/4.0/")        # cc:License

    def test_ext_description_is_distinct_from_caption(self):
        # The caption must NOT be routed into the accessibility extended description;
        # ext_description is its own field (IPTC keeps them distinct).
        m = self.write_manifest({
            "constants": {},
            "images": {"a.jpg": {
                "caption": "A visible cutline about the scene.",
                "ext_description": "A long screen-reader description of the chart.",
            }},
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")
        out = subprocess.run(
            ["exiftool", "-G1", "-j", "-XMP-iptcCore:ExtDescrAccessibility",
             "-IPTC:Caption-Abstract", "--", str(self.src / "tagged" / "a.jpg")],
            capture_output=True, text=True)
        data = json.loads(out.stdout)[0]
        self.assertEqual(data.get("XMP-iptcCore:ExtDescrAccessibility"),
                         "A long screen-reader description of the chart.")
        self.assertEqual(data.get("IPTC:Caption-Abstract"),
                         "A visible cutline about the scene.")

    def test_caption_alone_does_not_write_ext_description(self):
        # A caption with no ext_description leaves ExtDescrAccessibility empty.
        m = self.write_manifest({
            "constants": {}, "images": {"a.jpg": {"caption": "Just a caption."}},
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m))
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")
        out = subprocess.run(["exiftool", "-s3", "-XMP-iptcCore:ExtDescrAccessibility",
                              "--", str(self.src / "tagged" / "a.jpg")],
                             capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "")

    def test_strip_gps_removes_location_but_keeps_editorial_metadata(self):
        # A publish-safe derivative: GPS gone, caption/credit/source-type intact.
        subprocess.run(["exiftool", "-overwrite_original",
                        "-GPSLatitude=40.7", "-GPSLatitudeRef=N",
                        "-GPSLongitude=74.0", "-GPSLongitudeRef=W",
                        "--", str(self.src / "a.jpg")], capture_output=True, text=True)
        m = self.write_manifest({
            "constants": {"by_line": "Dana", "digital_source_type": "digitalCapture"},
            "images": {"a.jpg": {"caption": "A red rectangle."}},
        })
        r = run_embed("--dir", str(self.src), "--manifest", str(m), "--strip-gps")
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout} stderr={r.stderr}")
        tagged = str(self.src / "tagged" / "a.jpg")
        gps = subprocess.run(["exiftool", "-s3", "-GPSLatitude", "-GPSLongitude",
                              "--", tagged], capture_output=True, text=True)
        self.assertEqual(gps.stdout.strip(), "")  # GPS removed
        keep = subprocess.run(["exiftool", "-s3", "-IPTC:By-line",
                               "-XMP-iptcExt:DigitalSourceType", "--", tagged],
                              capture_output=True, text=True)
        self.assertIn("Dana", keep.stdout)
        self.assertIn("digitalsourcetype/digitalCapture", keep.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
