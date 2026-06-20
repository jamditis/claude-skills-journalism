---
name: photo-metadata
description: Use when preparing photos or images for a news wire, publication, photo CMS, or archive — embedding caption, byline, credit, alt text, keywords, copyright or Creative Commons license, and location into a file's IPTC, EXIF, and XMP metadata, or batch-tagging a folder of press photos with exiftool.
---

# Photo metadata

## Overview

Metadata embedded in an image file travels with the file. Photo CMSs (Photo Mechanic, Lightroom, Capture One) and wire intake systems read a photo's caption, credit, and rights from its IPTC and XMP blocks — not from a separate document or the email it arrived in. If the caption, credit, alt text, and license are not *inside* the file, they are gone the moment the photo is downloaded, forwarded, or re-uploaded.

One `exiftool` pass writes the EXIF, IPTC, and XMP layers together and leaves every other tag (camera settings, shot time) untouched.

**A capable model already knows the field names.** The hard part is not the mechanics — it is the judgment below. Lead with that.

## When to use

- Prepping press photos for a wire so partner newsrooms can search, credit, and republish them
- Adding required photographer attribution and a reuse license before publishing or sharing
- Batch-tagging a shoot (a folder of images)
- Making images accessible (embedded alt text) and rights-clear (copyright or Creative Commons)

**When not to use:** editing pixels (this is metadata only); writing alt text for an HTML `<img>` (use `accessibility-compliance`); preserving web pages as evidence (use `web-archiving`).

## The discipline (what agents get wrong)

These are the failures a capable agent makes anyway. They matter more than any tag name.

1. **Caption only what is visible.** Describe what the frame shows, not what you were told. Do not infer events, intent, identities, relationships, or legal status you cannot see. "Demonstrators gather to protest a court ruling" is a claim about facts not in the frame; "A crowd holds signs outside a courthouse" is the photo.
2. **Label people from visible evidence.** Name an agency or role only from a visible marking — a labeled vest, a uniform, a badge, a patch. Otherwise write "officers in tactical gear," "a man in a blue shirt." Never assert someone's immigration or legal status (no "detainee," no "undocumented") unless it is unambiguous in the frame.
3. **Always write alt text — it is not the caption.** Write both: a short screen-reader description in `XMP-iptcCore:AltTextAccessibility` and the publishable caption in `IPTC:Caption-Abstract`. Agents routinely write the caption and skip the alt text.
4. **Keep structured fields neutral.** Editorial framing or a contested label belongs in `Headline`, never in `City`, `Caption-Abstract`, or the location fields. Partner newsrooms apply their own language; clean structured fields let them.
5. **Verify the round-trip from source.** Read the metadata back *from the written file*, not from your buffer. After any upload or transfer, re-read it *from the destination* — a 200 response proves the bytes were accepted, not that the metadata survived.

## Quick reference — the fields that carry the weight

| Role | IPTC (IIM) | XMP | EXIF |
|------|-----------|-----|------|
| Photographer | `By-line` | `dc:Creator` | `Artist` |
| Credit | `Credit` (org, max 32 chars) | `photoshop:Credit` (full name / org) | — |
| Caption | `Caption-Abstract` | `dc:Description`, `iptcCore:ExtDescrAccessibility` | `ImageDescription` |
| Alt text (short) | — | `iptcCore:AltTextAccessibility` | — |
| Keywords | `Keywords` (repeatable) | `dc:Subject` | — |
| Copyright | `CopyrightNotice` | `dc:Rights` | `Copyright` |
| License (CC) | — | `cc:License`, `xmpRights:Marked`/`WebStatement`/`UsageTerms` | — |
| Headline | `Headline` | `photoshop:Headline` | — |
| Location | `Sub-location`/`City`/`Province-State`/`Country-*` | `iptcCore:Location`, `photoshop:City`/`State`/`Country` | — |
| Date | `DateCreated` | `photoshop:DateCreated` | `DateTimeOriginal` (source of truth) |

Full tag list, the IPTC-IIM byte limits, the Creative Commons field set, and the AP caption recipe: see `reference.md`.

## One pass that writes all three layers

```bash
CAPTION="A crowd holds signs outside the Mercer County Courthouse, Friday, June 19, 2026, in Trenton, N.J. (Dana Rivera/Example News Collective)"
ALT="A crowd of people holding handmade signs stands on the steps of a stone courthouse."

exiftool -codedcharacterset=utf8 -overwrite_original \
  -EXIF:Artist="Dana Rivera" -XMP-dc:Creator="Dana Rivera" -IPTC:By-line="Dana Rivera" \
  -IPTC:Credit="Example News Collective" -XMP-photoshop:Credit="Dana Rivera / Example News Collective" \
  -IPTC:Caption-Abstract="$CAPTION" -XMP-dc:Description="$CAPTION" \
    -EXIF:ImageDescription="$CAPTION" -XMP-iptcCore:ExtDescrAccessibility="$CAPTION" \
  -XMP-iptcCore:AltTextAccessibility="$ALT" \
  -IPTC:Keywords="protest" -IPTC:Keywords+="Trenton" \
    -XMP-dc:Subject="protest" -XMP-dc:Subject+="Trenton" \
  -EXIF:Copyright="(c) 2026 Example News Collective. Licensed CC BY 4.0." \
    -IPTC:CopyrightNotice="(c) 2026 Example News Collective. CC BY 4.0." \
    -XMP-dc:Rights="(c) 2026 Example News Collective. Licensed CC BY 4.0." \
  -XMP-xmpRights:Marked=True \
    -XMP-xmpRights:WebStatement="https://creativecommons.org/licenses/by/4.0/" \
    -XMP-xmpRights:UsageTerms="Licensed CC BY 4.0. Credit: Dana Rivera / Example News Collective." \
    -XMP-cc:License="https://creativecommons.org/licenses/by/4.0/" \
    -XMP-cc:AttributionName="Dana Rivera / Example News Collective" \
  -IPTC:City="Trenton" -IPTC:Province-State="New Jersey" \
    -IPTC:Country-PrimaryLocationName="United States" -IPTC:Country-PrimaryLocationCode="USA" \
  "-IPTC:DateCreated<EXIF:DateTimeOriginal" "-IPTC:TimeCreated<EXIF:DateTimeOriginal" \
    "-XMP-photoshop:DateCreated<EXIF:DateTimeOriginal" \
  photo.jpg
```

Then **verify from the file** (the step agents skip):

```bash
exiftool -G1 -s -IPTC:By-line -IPTC:Caption-Abstract \
  -XMP-iptcCore:AltTextAccessibility -XMP-cc:License -IPTC:Keywords photo.jpg
```

## Batch tagging a folder

For a shoot, drive `exiftool` from a manifest instead of one command per file. `embed.py` in this directory takes a folder plus a JSON manifest (constant credit and license fields, then per-image alt text, caption, and keywords), writes tagged copies, and reads each one back to confirm the metadata landed. Run `python3 embed.py --help`.

## Common mistakes (from baseline testing)

| Mistake | Fix |
|---------|-----|
| Wrote a caption, no alt text | Always write `AltTextAccessibility` too — they are different fields |
| `By-line`/`Credit`/`City` silently truncated | Those IIM fields cap at 32 chars; put the full credit in `XMP-photoshop:Credit` |
| Caption states things not in the frame | Describe only what is visible; move unseeable context out |
| Editorial label in `City` or caption | Put framing in `Headline`; keep structured fields neutral |
| Assumed the upload kept the metadata | Re-read the metadata from the destination file |
| Keywords as one comma-joined string | Write repeatable `Keywords` records (and a `dc:Subject` list) |
| Set a CC license note in plain text only | Add the machine-readable `cc:License` and `xmpRights:Marked` fields |

## Real-world impact

Embedded metadata is what lets a partner newsroom find a photo, credit it correctly, and republish it under a clear license without ever contacting the photographer. Strip it, and the same photo is an orphaned file.
