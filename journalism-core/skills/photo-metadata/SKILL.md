---
name: photo-metadata
description: Use when preparing photos or images for a news wire, publication, photo CMS, or archive — embedding caption, byline, credit, alt text, keywords, copyright or Creative Commons license, AI/synthetic source labeling, and location into a file's IPTC, EXIF, and XMP metadata, batch-tagging a folder of press photos with exiftool, or verifying the C2PA Content Credentials on an inbound image.
---

# Photo metadata

## Overview

Metadata embedded in an image file travels with the file. Photo CMSs (Photo Mechanic, Lightroom, Capture One) and wire intake systems read a photo's caption, credit, and rights from its IPTC and XMP blocks — not from a separate document or the email it arrived in. If the caption, credit, alt text, and license are not *inside* the file, they are gone the moment the photo is downloaded, forwarded, or re-uploaded.

One `exiftool` pass writes the EXIF, IPTC, and XMP layers together and leaves every other tag (camera settings, shot time) untouched. Modern software reads **XMP first**, legacy IPTC-IIM second, EXIF only for date and GPS — so write XMP everywhere and add IIM as a compatibility copy on JPEG/TIFF (HEIC, AVIF, and WebP have no IIM slot at all; see `reference.md`).

Two things changed since this workflow was "caption, credit, copyright." First, **how an image was made now belongs in the metadata**: the IPTC *Digital Source Type* field labels a camera photo versus an AI-generated one, and platforms (Meta, Google) and the EU AI Act increasingly read it. Second, **cryptographic provenance (C2PA / "Content Credentials")** is arriving on wire images and cameras — a signed layer `exiftool` can *read* but not write. Both are covered below.

**A capable model already knows the field names.** The hard part is not the mechanics — it is the judgment below. Lead with that.

## When to use

- Prepping press photos for a wire so partner newsrooms can search, credit, and republish them
- Adding required photographer attribution and a reuse license before publishing or sharing
- Labeling how an image was made — a straight photo, an AI-generated illustration, an AI-edited composite
- Batch-tagging a shoot (a folder of images)
- Making images accessible (embedded alt text) and rights-clear (copyright or Creative Commons)
- Reading and sanity-checking the C2PA Content Credentials on an image that arrived from an agency

**When not to use:** editing pixels (this is metadata only); writing alt text for an HTML `<img>` (use `accessibility-compliance`); preserving web pages as evidence (use `web-archiving`); *signing* a Content Credential (exiftool can't — use `c2patool`, below).

## The discipline (what agents get wrong)

These are the failures a capable agent makes anyway. They matter more than any tag name.

1. **Caption only what is visible.** Describe what the frame shows, not what you were told. Do not infer events, intent, identities, relationships, or legal status you cannot see. "Demonstrators gather to protest a court ruling" is a claim about facts not in the frame; "A crowd holds signs outside a courthouse" is the photo.
2. **Label people from visible evidence.** Name an agency or role only from a visible marking — a labeled vest, a uniform, a badge, a patch. Otherwise write "officers in tactical gear," "a man in a blue shirt." Never assert someone's immigration or legal status (no "detainee," no "undocumented") unless it is unambiguous in the frame.
3. **Always write alt text — it is not the caption.** Write both: a short screen-reader description in `XMP-iptcCore:AltTextAccessibility` and the publishable caption in `IPTC:Caption-Abstract`. IPTC keeps these deliberately distinct — the caption states facts and is shown on the page; the alt text is read aloud by a screen reader — so do not just copy one into the other. Agents routinely write the caption and skip the alt text.
4. **Label how the image was made — and never lie about it.** If an image is AI-generated or AI-edited, say so in `XMP-iptcExt:DigitalSourceType`; if it is a straight photo, `digitalCapture` states that plainly. Do the honest thing and label it; do the diligent thing and, on an *inbound* file, **never strip an existing Digital Source Type or C2PA credential** — that erases a disclosure someone made on purpose.
5. **Strip GPS when the location could endanger someone.** A protester, a source, an abuse survivor, a minor — embedded coordinates can reveal a home or a safe house. Remove GPS from the published derivative (`-gps:all=`) while keeping the caption and credit; keep a full-GPS archival master only where location is editorial evidence. GPS is the single highest-risk tag in the file.
6. **Keep structured fields neutral.** Editorial framing or a contested label belongs in `Headline`, never in `City`, `Caption-Abstract`, or the location fields. Partner newsrooms apply their own language; clean structured fields let them.
7. **Verify the round-trip from source.** Read the metadata back *from the written file*, not from your buffer. After any upload or transfer, re-read it *from the destination* — a 200 response proves the bytes were accepted, not that the metadata survived. Most social platforms re-encode on upload and strip IPTC, XMP, GPS, *and* C2PA (see `reference.md`), so "I embedded it" is not "it arrived."

## Quick reference — the fields that carry the weight

| Role | IPTC (IIM) | XMP | EXIF |
|------|-----------|-----|------|
| Photographer | `By-line` | `dc:Creator` | `Artist` |
| Credit | `Credit` (org, max 32 chars) | `photoshop:Credit` (full name / org) | — |
| Caption | `Caption-Abstract` | `dc:Description` | `ImageDescription` |
| Alt text (short) | — | `iptcCore:AltTextAccessibility` | — |
| Extended description | — | `iptcCore:ExtDescrAccessibility` (complex images; not the caption) | — |
| How it was made | — | `iptcExt:DigitalSourceType` (full CV URI) | — |
| Keywords | `Keywords` (repeatable) | `dc:Subject` | — |
| Copyright | `CopyrightNotice` | `dc:Rights` | `Copyright` |
| License (CC) | — | `xmpRights:Marked`/`WebStatement`/`UsageTerms`, `cc:License` (legacy) | — |
| License / discovery | — | `xmpRights:WebStatement`, `plus:LicensorName`/`LicensorURL` (Google) | — |
| Headline | `Headline` | `photoshop:Headline` | — |
| Location | `Sub-location`/`City`/`Province-State`/`Country-*` | `iptcCore:Location`, `photoshop:City`/`State`/`Country` | — |
| Date | `DateCreated` | `photoshop:DateCreated` | `DateTimeOriginal` (source of truth) |

Digital Source Type values (fully AI → `trainedAlgorithmicMedia`, AI-edited → `compositeWithTrainedAlgorithmicMedia`, straight photo → `digitalCapture`), the full IPTC controlled vocabulary, the IPTC-IIM byte limits, the PLUS/Google-licensing and Creative Commons field sets, the C2PA tooling, and the AP caption recipe: see `reference.md`.

## One pass that writes all three layers

```bash
CAPTION="A crowd holds signs outside the Mercer County Courthouse, Friday, June 19, 2026, in Trenton, N.J. (Dana Rivera/Example News Collective)"
ALT="A crowd of people holding handmade signs stands on the steps of a stone courthouse."
# how the image was made — a full IPTC CV URI (see reference.md for all values)
DST="http://cv.iptc.org/newscodes/digitalsourcetype/digitalCapture"

exiftool -codedcharacterset=utf8 -overwrite_original -P \
  -EXIF:Artist="Dana Rivera" -XMP-dc:Creator="Dana Rivera" -IPTC:By-line="Dana Rivera" \
  -IPTC:Credit="Example News Collective" -XMP-photoshop:Credit="Dana Rivera / Example News Collective" \
  -IPTC:Caption-Abstract="$CAPTION" -XMP-dc:Description="$CAPTION" -EXIF:ImageDescription="$CAPTION" \
  -XMP-iptcCore:AltTextAccessibility="$ALT" \
  -XMP-iptcExt:DigitalSourceType="$DST" \
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

`-P` preserves the file's modification time; drop it if you want the write to touch the timestamp. Extended accessibility descriptions for complex images (charts, infographics) go in `XMP-iptcCore:ExtDescrAccessibility` — a *separate* field from the caption, added only when the alt text plus surrounding text can't convey the image.

Then **verify from the file** (the step agents skip):

```bash
exiftool -G1 -s -IPTC:By-line -IPTC:Caption-Abstract -XMP-iptcCore:AltTextAccessibility \
  -XMP-iptcExt:DigitalSourceType -XMP-cc:License -IPTC:Keywords photo.jpg
```

## Label how an image was made (AI and synthetic)

`XMP-iptcExt:DigitalSourceType` records origin from the IPTC controlled vocabulary. The value is a **full URI** — `exiftool` does not validate it, so a bare word or a typo is silently accepted and useless. The three every newsroom needs:

```bash
BASE="http://cv.iptc.org/newscodes/digitalsourcetype"
# a straight camera photo — worth stating even for real news images
exiftool -XMP-iptcExt:DigitalSourceType="$BASE/digitalCapture" photo.jpg
# fully AI-generated (a trained model produced the whole image)
exiftool -XMP-iptcExt:DigitalSourceType="$BASE/trainedAlgorithmicMedia" ai.jpg
# a real photo edited with generative AI (inpaint / outpaint / generative fill)
exiftool -XMP-iptcExt:DigitalSourceType="$BASE/compositeWithTrainedAlgorithmicMedia" edited.jpg
```

Meta and Google read this field to auto-label AI content, and the EU AI Act's machine-readable-disclosure duty (Article 50, enforcement from August 2026) is pushing it from nice-to-have toward required. IPTC 2025.1 adds companion fields — `AISystemUsed`, `AISystemVersionUsed`, `AIPromptInformation`, `AIPromptWriterName` (exiftool ≥ 13.40). Full vocabulary and the retired terms to avoid: `reference.md`.

## Content Credentials (C2PA): provenance exiftool can read but not sign

A **Content Credential** is a cryptographically signed C2PA manifest bound to the pixels — who made the image, in what tool, and whether AI was involved — increasingly shipped by cameras (Leica M11-P, Nikon Z6III, Sony Alpha) and agencies (AFP, AP, BBC pilots). It is a different layer from IPTC/XMP and answers a different question: not "what does the file claim" but "who signed this, and has it changed since."

`exiftool` **reads** it and **cannot write or verify** it:

```bash
exiftool -G1 -a -jumbf:all incoming.jpg     # report the C2PA/JUMBF manifest (no signature check)
```

That shows the manifest as *data* — it does not validate the signature or the signer. For a real check, drop the file into **verify.contentauthenticity.org** and confirm the signer is the agency you expect. To *create* a credential, use Adobe/CAI tooling — `c2patool` (`brew install c2patool`) or `pip install c2pa-python` — not exiftool.

**Writing metadata to a signed file breaks its credential.** A C2PA hard binding hashes the asset, and that hash covers the embedded metadata, so any `exiftool` write — caption, credit, GPS strip, even the tagging in this skill — leaves the manifest present but *invalid*. "Never strip the credential" is necessary but not sufficient. On an inbound signed file, either leave the original untouched and do your metadata work on a **derivative you will re-sign** with `c2patool`, or accept that the embedded credential no longer validates and say so. Do not embed metadata into a signed original and treat its credential as still good.

Two more cautions worth stating to any newsroom: a valid credential proves a signature and a chain, **not** that the scene is real (a camera will happily sign a photo of a screen), and most social platforms strip the manifest on upload, so on-platform provenance often survives only via "durable" watermark/fingerprint recovery. See `reference.md`.

## Strip GPS for a publish-safe derivative

Remove location without touching the caption, credit, copyright, or source type:

```bash
exiftool -gps:all= "-xmp:GPS*=" -overwrite_original photo.jpg
exiftool -a -G1 -gps:all "-xmp:GPS*" photo.jpg   # verify — this must print nothing
```

Use the `-xmp:GPS*=` wildcard, not just the three main coordinates: destination and image-direction fields (`GPSDestLatitude`, `GPSImgDirection`) are also a location and would otherwise survive. Keep the full-GPS file as a locked archival master where coordinates are editorial evidence (geolocation, verification). Publish the stripped copy. `embed.py --strip-gps` does this for a whole folder after tagging.

## Licensing that shows up in search (Google Images)

To earn the Google Images "Licensable" badge and a working "Get this image" link, set the web statement of rights (the trigger) and the PLUS licensor fields:

```bash
exiftool -XMP-xmpRights:Marked=True \
  -XMP-xmpRights:WebStatement="https://example.org/license/photo123" \
  -XMP-plus:LicensorName="Example News" -XMP-plus:LicensorURL="https://example.org/buy/photo123" \
  photo.jpg
```

The web statement is `xmpRights:WebStatement`, **not** `dc:Rights` — a common and costly mix-up. A Creative Commons license routes through the same `WebStatement` field with the CC deed URL. Details and the full PLUS field set: `reference.md`.

## Batch tagging a folder

For a shoot, drive `exiftool` from a manifest instead of one command per file. `embed.py` in this directory takes a folder plus a JSON manifest (constant credit, license, licensor, and Digital Source Type fields, then per-image alt text, caption, extended description, keywords, and an optional per-image source-type override), writes tagged copies, reads each one back to confirm the metadata landed, and — with `--strip-gps` — removes GPS from the copies. It accepts a Digital Source Type shorthand (`digitalCapture`) or a full URI and refuses anything else rather than embedding a broken value. Run `python3 embed.py --help`.

## Common mistakes (from baseline testing)

| Mistake | Fix |
|---------|-----|
| Wrote a caption, no alt text | Always write `AltTextAccessibility` too — they are different fields |
| Copied the caption into the alt text (or `ExtDescrAccessibility`) | IPTC keeps these distinct; write a real screen-reader sentence, keep `ExtDescr` for complex images only |
| `By-line`/`Credit`/`City` silently truncated | Those IIM fields cap at 32 chars; put the full credit in `XMP-photoshop:Credit` |
| Caption states things not in the frame | Describe only what is visible; move unseeable context out |
| AI-generated image left unlabeled | Set `DigitalSourceType` to `trainedAlgorithmicMedia` (or the right composite value) |
| `DigitalSourceType` set to a bare word | The value must be the full `http://cv.iptc.org/...` URI; exiftool won't validate it |
| Stripped an inbound file's Digital Source Type or C2PA | Never erase a disclosure — preserve provenance on files you receive |
| Published with GPS still embedded | Strip with `-gps:all=` when location could endanger a subject or source |
| `WebStatement` put in `dc:Rights` | The Google/licensing web statement is `xmpRights:WebStatement` |
| Editorial label in `City` or caption | Put framing in `Headline`; keep structured fields neutral |
| Assumed the upload kept the metadata | Re-read from the destination; most social platforms strip IPTC/XMP/GPS/C2PA |
| Keywords as one comma-joined string | Write repeatable `Keywords` records (and a `dc:Subject` list) |
| Set a CC license note in plain text only | Add `xmpRights:WebStatement` (CC deed URL) + `xmpRights:Marked` |

## Real-world impact

Embedded metadata is what lets a partner newsroom find a photo, credit it correctly, and republish it under a clear license without ever contacting the photographer. It is also, now, where an image says whether a human or a model made it, and where a signed Content Credential travels. Strip it, and the same photo is an orphaned file — no credit, no license, no provenance.
