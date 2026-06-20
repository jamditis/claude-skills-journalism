# Photo metadata — full reference

Detail behind `SKILL.md`. Load when you need the exact tag, a byte limit, the Creative Commons field set, or the caption recipe.

This is the full hand-write reference for `exiftool`. `embed.py` in this directory automates the subset of these fields exposed in its JSON manifest (see `SKILL.md`); the rest — `By-lineTitle`, `Source`, `ObjectName`, and any other tag without a manifest key — you write by hand.

## Why three metadata layers

A JPEG can carry the same fact in three places. Write all three; `exiftool` keeps them consistent.

- **EXIF** — written by the camera (shot time, model, exposure). Survives tools that strip everything else. Holds `Artist`, `Copyright`, `ImageDescription`, and the authoritative `DateTimeOriginal`.
- **IPTC-IIM** — the legacy newsroom standard. Photo Mechanic and most wire intake systems still index it first. Byte-limited (below).
- **XMP** — the modern XML layer (Adobe, accessibility, Creative Commons). No length limits. Newer CMSs prefer it.

## Field map

| Role | IPTC (IIM) | XMP | EXIF |
|------|-----------|-----|------|
| Photographer | `IPTC:By-line` | `XMP-dc:Creator` | `EXIF:Artist` |
| Photographer title | `IPTC:By-lineTitle` | `XMP-photoshop:AuthorsPosition` | — |
| Credit (org / full) | `IPTC:Credit` (org, max 32) | `XMP-photoshop:Credit` (full name / org) | — |
| Source | `IPTC:Source` | `XMP-photoshop:Source` | — |
| Caption / description | `IPTC:Caption-Abstract` | `XMP-dc:Description`, `XMP-iptcCore:ExtDescrAccessibility` | `EXIF:ImageDescription` |
| Alt text (accessibility) | — | `XMP-iptcCore:AltTextAccessibility` | — |
| Headline | `IPTC:Headline` | `XMP-photoshop:Headline` | — |
| Title / object name | `IPTC:ObjectName` | `XMP-dc:Title` | — |
| Keywords | `IPTC:Keywords` (repeatable) | `XMP-dc:Subject` (list) | — |
| Copyright notice | `IPTC:CopyrightNotice` | `XMP-dc:Rights` | `EXIF:Copyright` |
| Rights marked | — | `XMP-xmpRights:Marked` | — |
| Usage terms | `IPTC:SpecialInstructions` | `XMP-xmpRights:UsageTerms` | — |
| License URL (machine) | — | `XMP-cc:License`, `XMP-xmpRights:WebStatement` | — |
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

## Creative Commons fields (machine-readable license)

Plain-text "CC BY 4.0" in a copyright note is not machine-readable. Add the Creative Commons and XMP Rights namespaces so a rights-management system or a search crawler can detect the license:

```bash
exiftool \
  -XMP-xmpRights:Marked=True \
  -XMP-xmpRights:WebStatement="https://creativecommons.org/licenses/by/4.0/" \
  -XMP-cc:License="https://creativecommons.org/licenses/by/4.0/" \
  -XMP-cc:AttributionName="Jane Smith / Example News" \
  -XMP-cc:AttributionURL="https://example.org" \
  -XMP-xmpRights:UsageTerms="Licensed CC BY 4.0. Required credit: Jane Smith/Example News." \
  photo.jpg
```

License URLs: `by/4.0`, `by-sa/4.0`, `by-nc/4.0`, `by-nc-sa/4.0`, `by-nd/4.0`, `by-nc-nd/4.0`, or `publicdomain/zero/1.0/` for CC0. For all-rights-reserved, set `XMP-xmpRights:Marked=True` and leave `cc:License` unset.

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

## Alt text vs caption

They serve different readers and go in different fields.

- **Alt text** (`XMP-iptcCore:AltTextAccessibility`): one short sentence for a screen-reader user — the single most important thing in the frame. ~125 characters. No date, credit, or place (those are announced elsewhere).
- **Extended description** (`XMP-iptcCore:ExtDescrAccessibility`): a longer accessible description for a complex image; often the same text as the caption.
- **Caption** (`IPTC:Caption-Abstract`): the publishable wire caption above — scene, place, date, credit.

## Labeling people — examples

| Visible in frame | Write | Do not write |
|------------------|-------|--------------|
| Vest reads "POLICE ICE" | "an ICE officer" | "an agent" (too vague) or a name you are guessing |
| Generic camo, no insignia | "officers in tactical gear" | "ICE agents" (not shown) |
| Person in facility uniform behind a barrier | "a person in a facility uniform" | "a detainee" (a legal-status claim) |
| Person at a podium with a name placard | read the placard | a name from memory |

Describe expressions and actions only when clearly visible. Do not infer emotion, motive, or relationship.
