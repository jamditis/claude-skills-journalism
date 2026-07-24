# journalism-core

Fourteen core journalism skills for Claude Code — covering reporting, verification, and publishing workflows for working journalists.

## What's in this plugin

| Skill | Purpose |
|---|---|
| **ai-writing-detox** | Eliminate AI-generated writing patterns that erode reader trust |
| **crisis-communications** | Rapid-response and breaking-news verification frameworks |
| **data-journalism** | Dataset analysis, chart and map creation, statistical reasoning, data-driven story structure |
| **editorial-workflow** | Assignment tracking, deadlines, and editorial calendars |
| **fact-check-workflow** | Structured claim verification, evidence gathering, and rating scales |
| **foia-requests** | Federal FOIA and state OPRA request templates with current statutory citations (FOIA Improvement Act 2016, NJ OPRA reform 2024) |
| **interview-prep** | Pre-interview research, question frameworks, and consent scripts |
| **interview-transcription** | Whisper / WhisperX transcription pipelines with speaker diarization |
| **newsletter-publishing** | Email newsletter workflows including 2024-2026 Gmail / Yahoo / Outlook bulk-sender compliance |
| **newsroom-style** | AP Style enforcement for journalism writing |
| **photo-metadata** | Embed caption, byline, credit, alt text, keywords, copyright or Creative Commons license, AI-source labeling (IPTC Digital Source Type), and Google-Images licensing into a photo's IPTC/EXIF/XMP metadata; strip GPS for source protection and read C2PA Content Credentials, for wire and archive use |
| **social-media-intelligence** | Narrative tracking, coordinated-campaign analysis, account authenticity checks, OSINT for digital investigations |
| **source-verification** | Source credibility, image and video verification, deepfake detection (2026), and C2PA Content Credentials |
| **story-pitch** | Pitch templates for daily news, features, investigations, and freelance queries |

## Installation

Install via the `claude-skills-journalism` Marketplace:

```
/plugin marketplace add jamditis/claude-skills-journalism
/plugin install journalism-core@claude-skills-journalism
```

Or install individual skills directly into `~/.claude/skills/` if you prefer not to use the plugin system — see the project README.

## Cross-references to skills outside this bundle

A few skills in this bundle reference siblings in other bundles. The references are advisory ("see also") — the skills work standalone if those bundles aren't installed:

- **source-verification** points to `social-media-intelligence` (deeper account analysis) and `web-archiving` (full archiving workflows)
- **interview-prep** points to `web-archiving` (recovering deleted social media content)
- **foia-requests** does not depend on other bundles

## Maintenance

Skills are updated against current authoritative sources. Substantive content changes are documented per-skill in `.superpowers/skill-design-<skill-slug>.md` files (in the parent repo, not shipped with the plugin).

Notable currency dates:

- **foia-requests** — citations verified May 2026 (FOIA Improvement Act of 2016 codification at 5 U.S.C. § 552(a)(8)(A); NJ OPRA P.L. 2024 c.16 effective September 3, 2024)
- **newsletter-publishing** — Gmail / Yahoo / Outlook bulk-sender requirements verified May 2026 including the November 2025 Gmail enforcement escalation to permanent 5xx rejections
- **source-verification** — C2PA Content Credentials adoption + deepfake detection tooling verified May 2026

## License

MIT — see the parent repo `LICENSE`.
