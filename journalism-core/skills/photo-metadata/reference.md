# Photo metadata — full reference

Detail behind `SKILL.md`. Load when you need the exact tag, a byte limit, the Digital Source Type vocabulary, the licensing/Creative Commons field set, the C2PA tooling, or the caption recipe.

This is the full hand-write reference for `exiftool`. `embed.py` in this directory automates the subset of these fields exposed in its JSON manifest (see `SKILL.md`); the rest — `By-lineTitle`, `Source`, `ObjectName`, the AI-system fields, and any other tag without a manifest key — you write by hand.

Current as of the **IPTC Photo Metadata Standard 2025.1** (Nov 2025; Core schema 1.5, Extension schema 1.9) and **exiftool 13.5x** (mid-2026). The AI-system fields (below) need exiftool ≥ 13.40; everything else here works on older builds. Standards move — re-check `iptc.org/standards/photo-metadata/` and `exiftool.org` when precision matters.

## Why three metadata layers, and which one wins

A JPEG can carry the same fact in three places. Write all three; `exiftool` keeps them consistent. Modern software **reads XMP first**, IIM second, EXIF only for date/GPS — but legacy wire intake still parses IIM, so on JPEG/TIFF you write both.

- **XMP** — the modern XML layer (Adobe, accessibility, licensing, Creative Commons, the AI/Digital-Source-Type and region fields). No length limits, always UTF-8. The canonical store; every field below has an XMP form.
- **IPTC-IIM** — the legacy newsroom block. Photo Mechanic and wire intake still read it, so write it as a compatibility copy — but it is byte-limited (below), not UTF-8 by default (needs `-codedcharacterset=utf8`), and **not defined at all in HEIC/AVIF/WebP/PNG** (see the format table). On those formats, write XMP + EXIF only.
- **EXIF** — written by the camera (shot time, model, exposure). Survives tools that strip everything else. Holds `Artist`, `Copyright`, `ImageDescription`, and the authoritative `DateTimeOriginal`.

To write all three consistently in one shot without listing each tag, exiftool's **MWG composite tags** apply the Metadata Working Group reconciliation rules: `-MWG:Description=`, `-MWG:Creator=`, `-MWG:Copyright=`, `-MWG:Keywords=`, `-MWG:City=` etc. each update the IIM, XMP, and EXIF copies together. Handy for scripts; the explicit per-layer tags below give you finer control.

## Field map

| Role | IPTC (IIM) | XMP | EXIF |
|------|-----------|-----|------|
| Photographer | `IPTC:By-line` | `XMP-dc:Creator` | `EXIF:Artist` |
| Photographer title | `IPTC:By-lineTitle` | `XMP-photoshop:AuthorsPosition` | — |
| Credit (org / full) | `IPTC:Credit` (org, max 32) | `XMP-photoshop:Credit` (full name / org) | — |
| Source | `IPTC:Source` | `XMP-photoshop:Source` | — |
| Caption / description | `IPTC:Caption-Abstract` | `XMP-dc:Description` | `EXIF:ImageDescription` |
| Alt text (accessibility) | — | `XMP-iptcCore:AltTextAccessibility` | — |
| Extended description (accessibility) | — | `XMP-iptcCore:ExtDescrAccessibility` | — |
| Digital source type (AI / origin) | — | `XMP-iptcExt:DigitalSourceType` | — |
| AI system used | — | `XMP-iptcExt:AISystemUsed`, `AISystemVersionUsed` | — |
| AI prompt | — | `XMP-iptcExt:AIPromptInformation`, `AIPromptWriterName` | — |
| Headline | `IPTC:Headline` | `XMP-photoshop:Headline` | — |
| Title / object name | `IPTC:ObjectName` | `XMP-dc:Title` | — |
| Keywords | `IPTC:Keywords` (repeatable) | `XMP-dc:Subject` (list) | — |
| Copyright notice | `IPTC:CopyrightNotice` | `XMP-dc:Rights` | `EXIF:Copyright` |
| Rights marked | — | `XMP-xmpRights:Marked` | — |
| Usage terms | `IPTC:SpecialInstructions` | `XMP-xmpRights:UsageTerms` | — |
| Web statement of rights | — | `XMP-xmpRights:WebStatement` | — |
| Licensor (Google "Get this image") | — | `XMP-plus:LicensorName`, `XMP-plus:LicensorURL` | — |
| License URL (CC, legacy) | — | `XMP-cc:License` | — |
| Attribution name | — | `XMP-cc:AttributionName` | — |
| Sub-location | `IPTC:Sub-location` | `XMP-iptcCore:Location` | — |
| City | `IPTC:City` | `XMP-photoshop:City` | — |
| State / province | `IPTC:Province-State` | `XMP-photoshop:State` | — |
| Country | `IPTC:Country-PrimaryLocationName` | `XMP-photoshop:Country` | — |
| Country code | `IPTC:Country-PrimaryLocationCode` | `XMP-iptcCore:CountryCode` | — |
| Date created | `IPTC:DateCreated` (+ `TimeCreated`) | `XMP-photoshop:DateCreated` | `EXIF:DateTimeOriginal` |

Copy the date from the camera rather than typing it:

```bash
exiftool "-IPTC:DateCreated<EXIF:DateTimeOriginal" "-IPTC:TimeCreated<EXIF:DateTimeOriginal" "-XMP-photoshop:DateCreated<EXIF:DateTimeOriginal" photo.jpg
```

## IPTC-IIM byte limits

IIM fields are byte-capped; exiftool truncates silently unless you pass `-m` (and even then it warns). XMP has no limit, so put the short form in IPTC and the full form in XMP.

| Field | Max bytes |
|-------|-----------|
| `By-line` | 32 |
| `By-lineTitle` | 32 |
| `Credit` | 32 |
| `Source` | 32 |
| `City` | 32 |
| `Province-State` | 32 |
| `Sub-location` | 32 |
| `Country-PrimaryLocationName` | 64 |
| `Country-PrimaryLocationCode` | 3 |
| `ObjectName` (title) | 64 |
| `Headline` | 256 |
| `SpecialInstructions` | 256 |
| `CopyrightNotice` | 128 |
| `Caption-Abstract` | 2000 |
| `Keywords` (per record) | 64 |

The trap: a credit like `Jane Smith / Center for Cooperative Media` is 40+ characters. In `IPTC:Credit` it gets cut. Put the organization alone in `IPTC:Credit` (under 32) and the full `name / org` in `XMP-photoshop:Credit`.

Use `-codedcharacterset=utf8` so accented names and curly quotes survive in the IPTC layer.

## Digital Source Type — how the image was made

`XMP-iptcExt:DigitalSourceType` holds a **full URI** from the IPTC "Digital Source Type" NewsCodes controlled vocabulary. exiftool stores it as an unvalidated string — it will not expand a shorthand or catch a typo — so you write the whole URI: `http://cv.iptc.org/newscodes/digitalsourcetype/<id>` (the `http://` form is canonical; `https://` also resolves).

| `<id>` | Meaning |
|--------|---------|
| `digitalCapture` | Straight capture from a digital camera — the news default, worth stating explicitly |
| `computationalCapture` | In-camera multi-frame merge (HDR, night mode); **non-generative** |
| `negativeFilm` / `positiveFilm` / `print` | Scanned from film negative / transparency / print |
| `humanEdits` | Human retouch/toning with **non-generative** tools |
| `algorithmicallyEnhanced` | Sharpening, denoise — no content change |
| `digitalCreation` | Human-made with non-generative software (replaced `digitalArt`) |
| `dataDrivenMedia` | Visual representation of data (a rendered dataset) |
| `compositeCapture` | Composite whose elements are **all** real captures |
| `composite` | Composite of elements, any of which may or may not be AI |
| `compositeSynthetic` | Composite with **at least one** generative-AI element |
| `compositeWithTrainedAlgorithmicMedia` | Existing media **edited with generative AI** (inpaint / outpaint / generative fill) |
| `trainedAlgorithmicMedia` | **Fully AI-generated** by a model trained on captured content |
| `algorithmicMedia` | Pure algorithm, **no** training data (a fractal, a procedural render) |
| `screenCapture` | Capture of a screen |
| `virtualRecording` | Recording of a virtual event (may mix capture and generative AI) |

The three to know cold: fully AI → `trainedAlgorithmicMedia`; a real photo AI-edited → `compositeWithTrainedAlgorithmicMedia`; a real capture with an AI element dropped in → `compositeSynthetic`.

**Retired terms — do not write** (they still resolve when reading legacy files): `minorHumanEdits` (→ `humanEdits`), `digitalArt` (→ `digitalCreation`), `softwareImage` (dropped as too vague).

Who acts on it: **Meta** (Facebook/Instagram/Threads) and **Google** read `DigitalSourceType` (and C2PA carrying the same value) to apply AI-content labels; generators like OpenAI, Adobe Firefly, and Google's image tools write it at creation. The same vocabulary appears inside C2PA manifests, so a value written here matches the signed one. The EU AI Act (Article 50) makes machine-readable AI disclosure a legal duty with enforcement from **August 2026**.

### AI system and prompt fields (IPTC 2025.1, exiftool ≥ 13.40)

For AI-generated or AI-assisted images, four companion fields record the tool and prompt:

```bash
exiftool \
  -XMP-iptcExt:DigitalSourceType="http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia" \
  -XMP-iptcExt:AISystemUsed="Adobe Firefly" \
  -XMP-iptcExt:AISystemVersionUsed="Image 4" \
  -XMP-iptcExt:AIPromptInformation="a wide shot of an empty newsroom at dawn" \
  -XMP-iptcExt:AIPromptWriterName="Jane Smith" \
  illustration.jpg
```

`AIPromptWriterName` is the person who wrote the prompt — explicitly *not* an author/creator claim over the image.

## Licensing metadata (Creative Commons and commercial)

Plain-text "CC BY 4.0" in a copyright note is not machine-readable. The **XMP Rights** namespace is what every tool, and Google, understand — use it for both Creative Commons and commercial licensing:

```bash
exiftool \
  -XMP-xmpRights:Marked=True \
  -XMP-xmpRights:WebStatement="https://creativecommons.org/licenses/by/4.0/" \
  -XMP-xmpRights:UsageTerms="Licensed CC BY 4.0. Required credit: Jane Smith/Example News." \
  -XMP-cc:License="https://creativecommons.org/licenses/by/4.0/" \
  -XMP-cc:AttributionName="Jane Smith / Example News" \
  -XMP-cc:AttributionURL="https://example.org" \
  photo.jpg
```

- `XMP-xmpRights:Marked` — `True` = rights reserved / licensed; `False` = public domain. Set it either way; leaving it unset is a missing signal.
- `XMP-xmpRights:WebStatement` — the URL of the rights/license page (or the CC deed URL). **This is the field Google keys on**, and the one people wrongly put in `dc:Rights`.
- `XMP-cc:License` and the other `cc:` fields still work but are effectively legacy: there is **no maintained Creative Commons XMP spec**, so prefer `xmpRights:WebStatement` (with the CC deed URL) as the primary machine-readable signal and add `cc:License` only for older CC-aware readers.

CC deed URLs: `by/4.0`, `by-sa/4.0`, `by-nc/4.0`, `by-nc-sa/4.0`, `by-nd/4.0`, `by-nc-nd/4.0`, or `publicdomain/zero/1.0/` for CC0.

### Google Images "Licensable" badge and PLUS licensor fields

Google Images shows a "Licensable" badge and a "Get this image on …" link when the file carries a web statement plus a licensor. Confirmed active in 2025–2026.

```bash
exiftool \
  -XMP-xmpRights:Marked=True \
  -XMP-xmpRights:WebStatement="https://example.org/license/photo123" \
  -XMP-plus:LicensorName="Example Photo Agency" \
  -XMP-plus:LicensorURL="https://example.org/buy/photo123" \
  -XMP-dc:Creator="Jane Doe" -IPTC:Credit="Example Photo Agency" \
  -XMP-dc:Rights="© 2026 Example Photo Agency" -IPTC:CopyrightNotice="© 2026 Example Photo Agency" \
  photo123.jpg
```

- `WebStatement` is **required** to trigger the badge; `LicensorURL` powers the purchase link.
- The PLUS namespace (`XMP-plus:`, from the Picture Licensing Universal System) has more: `LicensorName`/`LicensorURL`/`LicensorID`/`LicensorEmail`, and the supplier and owner structures `ImageSupplierName`/`ImageSupplierID`, `ImageCreatorName`, `CopyrightOwnerName`. The flattened tag writes the first list element, which is what publishers need.
- On-page **schema.org `ImageObject`** structured data (`license`, `acquireLicensePage`, `creator`, `creditText`, `copyrightNotice`) is the alternative signal; if the embedded and on-page data disagree, **Google uses the structured data**.

## AP-style caption recipe

A wire caption should stand on its own: scene, place, date, credit. One reliable shape:

```
<what is visible>, <weekday>, <Month D, YYYY>, in <City>, <State abbr>. (<Photographer>/<Organization>)
```

Example:
```
A crowd holds signs outside the county courthouse, Friday, June 19, 2026, in Trenton, N.J. (Dana Rivera/Example News Collective)
```

Notes:
- AP abbreviates most state names in datelines (`N.J.`, `Calif.`, `Pa.`); the period in `N.J.` is the sentence terminator — do not add a second one.
- Present tense for what the photo shows.
- Verify the weekday against the date; do not guess it.
- The credit goes in parentheses at the end, photographer first, then the organization.

## Caption, alt text, and extended description — three distinct fields

IPTC keeps these separate on purpose: the caption states facts and is shown on the page; the alt text is hidden in the HTML and read aloud by a screen reader. **Do not copy one into the other.**

- **Caption** (`IPTC:Caption-Abstract` / `XMP-dc:Description`): the publishable wire caption — scene, place, date, credit. Shown as a visible cutline.
- **Alt text** (`XMP-iptcCore:AltTextAccessibility`): one short sentence for a screen-reader user — the single most important thing in the frame. Keep it short (a target of ~250 characters; software flags longer). No date, credit, or place (those are announced elsewhere), and no keyword stuffing — IPTC is explicit that alt text is not for SEO.
- **Extended description** (`XMP-iptcCore:ExtDescrAccessibility`): a longer accessible description for a **complex** image (a chart, an infographic, a map) — used only when the alt text plus surrounding page text can't convey it. It should **not** repeat the alt text, and it is **not** the caption. Most news photos don't need one.

Both accessibility fields arrived in IPTC 2021.1 and are `lang-alt` (language-tagged), so they can carry translations.

## Labeling people — examples

| Visible in frame | Write | Do not write |
|------------------|-------|--------------|
| Vest reads "POLICE ICE" | "an ICE officer" | "an agent" (too vague) or a name you are guessing |
| Generic camo, no insignia | "officers in tactical gear" | "ICE agents" (not shown) |
| Person in facility uniform behind a barrier | "a person in a facility uniform" | "a detainee" (a legal-status claim) |
| Person at a podium with a name placard | read the placard | a name from memory |

Describe expressions and actions only when clearly visible. Do not infer emotion, motive, or relationship.

## Content Credentials (C2PA) — the signed provenance layer

C2PA ("Content Credentials," the "Cr" pin) is a cryptographically signed manifest bound to the pixels by a content hash, stored in a **JUMBF** box (in JPEG, the APP11 segment). It is separate from IPTC/XMP and answers a different question: *who signed this asset, in what tool, with what edits and AI involvement, and has it changed since*. A C2PA manifest can also carry a signed copy of the IPTC metadata as a `stds.iptc.photo-metadata` assertion, and it uses the **same** Digital Source Type vocabulary as above.

**exiftool reads it, cannot write it, and can delete it:**

```bash
exiftool -G1 -a -jumbf:all incoming.jpg     # report the manifest as data (NO signature check)
exiftool -jumbf:all= -overwrite_original file.jpg   # strip the credential (know that it's this easy)
```

exiftool shows the manifest contents but does **not** validate the signature, the trust chain, or the hash binding — so it tells you a credential is *present and says X*, not that it is *valid*. For a real verification, use:

- **verify.contentauthenticity.org** — drag in a file; it validates the signature and shows the signer, edits, and ingredients. The human-facing check.
- **c2patool** (`brew install c2patool`) or **`pip install c2pa-python`** (Python ≥ 3.10) — read, validate, and **sign/add** manifests. Signing uses an external signer so private keys never pass through the tool. These are the CAI/Adobe reference tools; exiftool is not a substitute.

Cautions to state plainly to any newsroom:

- **Editing metadata invalidates the credential.** The hard binding hashes the asset, metadata included, so any `exiftool` write to a signed file — including the tagging and GPS-stripping in this skill — leaves the manifest embedded but no longer valid. Preserving the JUMBF box is not enough. Keep the signed original untouched and do metadata work on a derivative you re-sign with `c2patool`, or state that the embedded credential no longer validates. Do not tag a signed original and call its credential good.
- **A valid credential proves a signature and a chain, not truth.** A camera will sign a photo of a screen; a manifest can be forged with a mis-issued cert; certificate revocation checking is optional in the spec and validators have disagreed in practice (e.g., a revoked Nikon signing cert in late 2025). Verify the *signer identity*, not merely that a credential exists.
- **Adoption is emerging, not universal.** Cameras (Leica M11-P, Nikon Z6III via firmware + Nikon's authenticity service, Sony Alpha via Camera Verify, Canon) and agencies (AFP, AP, BBC pilots) are shipping it, but claims that wire services "require" signed credentials on all images are overstated — treat provenance as a growing practice.
- **Durability.** Because platforms strip the embedded manifest, "Durable Content Credentials" add an invisible watermark (Digimarc, in the C2PA spec since 2.1) and a content fingerprint so a stripped credential can be recovered from a manifest store. Don't count on the embedded manifest alone surviving a trip through social media.

## Location privacy — stripping GPS

GPS is the highest-risk tag in a news file. Strip it from the published derivative while keeping the editorial metadata:

```bash
# EXIF GPS IFD + the whole XMP GPS set; leaves caption/credit/copyright/source-type intact
exiftool -gps:all= "-xmp:GPS*=" -overwrite_original photo.jpg
exiftool -a -G1 -gps:all "-xmp:GPS*" photo.jpg   # verify: must print nothing
```

Clear the whole XMP GPS set with the `-xmp:GPS*=` wildcard, not just `GPSLatitude`/`GPSLongitude`/`GPSAltitude`: exiftool's EXIF→XMP GPS mapping can also populate `GPSDestLatitude`/`GPSDestLongitude` and `GPSImgDirection`, and a destination coordinate left behind still leaks a location. The `*` is quoted so the shell passes it to exiftool rather than globbing it.

Keep a full-GPS archival master, locked internally, where coordinates are editorial evidence (geolocation, verification, accountability). Publish the stripped copy. `embed.py --strip-gps` applies this to every file in a tagged folder. Note that a blunt `exiftool -all=` also removes the ICC color profile (colors shift), the EXIF orientation (image may display rotated), and any C2PA credential — for a targeted scrub prefer `-gps:all=`; for a full strip that keeps color, add `--icc_profile:all=` back: `exiftool -all= --icc_profile:all= -overwrite_original photo.jpg`.

## Formats: where IIM, XMP, and EXIF live

| Format | EXIF | XMP | IPTC-IIM | Write editorial metadata as |
|--------|:----:|:---:|:--------:|-----------------------------|
| JPEG | ✓ | ✓ | ✓ | IIM **and** XMP (+ EXIF) |
| TIFF / DNG | ✓ | ✓ | ✓ | IIM **and** XMP (+ EXIF) |
| HEIC / HEIF (iPhone) | ✓ | ✓ | **✗** | **XMP + EXIF only** (no IIM slot) |
| AVIF | ✓ | ✓ | **✗** | **XMP + EXIF only** |
| WebP | ✓ | ✓ | **✗** | **XMP + EXIF only** (confirm downstream reads WebP XMP) |
| PNG | ✓ (eXIf) | ✓ | limited | **XMP + EXIF**; IIM not standard |

exiftool reads and writes all of these. On the no-IIM formats, an `-IPTC:*` write is silently dropped (exiftool writes only the XMP copy) — so target the `XMP-*` equivalents. `embed.py` writes both blocks and, on read-back, accepts the IIM tag *or* its XMP twin for byline, caption, and keywords: a valid XMP-only write on HEIC/AVIF/WebP passes rather than false-failing, while a tag that landed in neither layer still fails.

## Social platforms strip metadata

Most platforms re-encode on upload and strip EXIF, GPS, IPTC, XMP, **and** C2PA from the copy other users download: Instagram, X/Twitter, Facebook, LinkedIn, TikTok, Reddit, Threads, Bluesky. A few preserve everything — **iMessage** and WhatsApp/Telegram *document/file* mode keep full metadata **including GPS** (a leak vector to warn about), while photo-hosting sites (Flickr, SmugMug) preserve and display IPTC/EXIF. The takeaway for the round-trip discipline in `SKILL.md`: after publishing to a platform, assume the embedded metadata and any Content Credential are gone unless you have verified otherwise on that platform.
