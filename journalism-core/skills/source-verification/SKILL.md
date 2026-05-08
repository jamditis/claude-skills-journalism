---
name: source-verification
description: Journalism source verification and fact-checking workflows. Use when verifying claims, checking source credibility, investigating social media accounts, reverse image searching, detecting AI-generated content, or building verification trails. For reporters, fact-checkers, and researchers working with unverified information.
---

# Source verification methodology

Systematic approaches for verifying sources, claims, and digital content in journalism and research.

## Verification framework

### The SIFT method

**S - Stop**: Don't immediately share or use unverified information
**I - Investigate the source**: Who is behind the information?
**F - Find better coverage**: What do other reliable sources say?
**T - Trace claims**: Find the original source of the claim

### Source credibility checklist

```markdown
## Source evaluation template

### Basic identification
- [ ] Full name/organization identified
- [ ] Contact information verifiable
- [ ] Professional credentials checkable
- [ ] Online presence consistent across platforms

### Expertise assessment
- [ ] Relevant expertise for the claim being made
- [ ] Track record in this subject area
- [ ] Recognized by peers in the field
- [ ] No history of spreading misinformation

### Motivation analysis
- [ ] Potential conflicts of interest identified
- [ ] Financial stake in the outcome?
- [ ] Political or ideological motivation?
- [ ] Personal grievance involved?

### Corroboration
- [ ] Can claims be independently verified?
- [ ] Do other credible sources confirm?
- [ ] Is documentary evidence available?
- [ ] Are there contradicting sources?
```

## Digital verification techniques

### Social media account analysis

For deeper open-source intelligence and platform-specific account-analysis techniques, use the **social-media-intelligence** skill. The notes here cover the verification-context subset — specifically what triggers a "verify before quoting" decision.

```markdown
## Account verification checklist

### Account age and history
- Creation date (older accounts more credible)
- Posting frequency and patterns
- Gaps in activity (dormant then suddenly active?)
- Language consistency over time

### Network analysis
- Follower/following ratio
- Quality of followers (real accounts vs. bots)
- Interaction patterns (who engages with them?)
- Mutual connections with verified accounts

### Content patterns
- Original content vs. reshares only
- Topics discussed consistently
- Geographic indicators in posts
- Time zone of posting activity

### Red flags
- Recently created account making bold claims
- Sudden pivot in topics or tone
- Coordinated behavior with other accounts
- Stock photo profile picture
- Generic bio with no specifics
```

### Reverse image search workflow

```markdown
## Image verification process

### Step 1: Reverse image search
Tools to use:
- Google Images (images.google.com)
- TinEye (tineye.com)
- Yandex Images (yandex.com/images) - best for faces
- Bing Visual Search

### Step 2: Check metadata (EXIF)
- Original capture date/time
- Camera/device information
- GPS coordinates (if available)
- Software used to edit

Tools:
- Jeffrey's EXIF Viewer (exif.regex.info)
- FotoForensics (fotoforensics.com)
- InVID verification plugin

### Step 3: Analyze image content
- Weather conditions (match reported date?)
- Shadows (consistent with time of day?)
- Signage/text (correct language for location?)
- Architecture (matches claimed location?)
- Clothing (seasonal appropriateness?)

### Step 4: Find original source
- Earliest appearance online
- Original photographer/source
- Context of first publication
- Has it been used in other contexts?
```

### Video verification

```markdown
## Video verification checklist

### Technical analysis
- [ ] Resolution consistent throughout
- [ ] Audio sync matches video
- [ ] No visible editing artifacts
- [ ] Lighting consistent across frames
- [ ] Shadows behave naturally

### Content analysis
- [ ] Location identifiable and verifiable
- [ ] Time indicators (sun position, shadows)
- [ ] Weather matches historical records
- [ ] Background details consistent
- [ ] People's clothing appropriate for context

### Metadata check
- [ ] Upload date vs. claimed event date
- [ ] Original source identified
- [ ] Chain of custody traceable
- [ ] Multiple angles available?

### Tools
- InVID/WeVerify browser extension
- YouTube DataViewer (citizenevidence.amnestyusa.org)
- Frame-by-frame analysis tools
```

## Detecting AI-generated and synthetic media

By 2026, naked-eye detection of high-end synthetic media is no longer reliable. The Columbia Journalism Review's 2025 guide is blunt: detection tools "have largely not kept up with diffusion models." Treat any single tool's verdict as one input, not a ruling.

The verification stack now has two layers — **provenance** (was this content cryptographically signed when created?) and **detection** (does it look or sound generated?). Provenance is the stronger signal when present, but its absence doesn't mean fake.

### Layer 1 — Content Credentials (C2PA) provenance check

The Coalition for Content Provenance and Authenticity (C2PA) standard ships cryptographic manifests inside image, audio, and video files describing their origin and edit history. Specification 2.2 was released in April–May 2025; the C2PA Conformance Program and Trust List launched mid-2025 and the legacy ingredient trust list was frozen January 1, 2026.

**Production adoption (verified May 2026):**

- **Image generators.** OpenAI DALL-E 3 (since 2023) and Sora 2 video write Credentials by default; Sora 2 also includes a visible moving watermark. Adobe Photoshop, Lightroom, and Firefly write Credentials across Creative Cloud. Microsoft Bing Image Creator, Designer, Copilot, and Azure OpenAI write Credentials. Google Gemini and Nano Banana Pro images carry C2PA plus SynthID.
- **Cameras (capture-side signing).** Leica M11-P (October 2023, first to ship), SL3-S; Sony Alpha 1 II, Alpha 9 III, PXW-Z300; Canon EOS R1 and R5 Mark II via firmware (July 2025); Google Pixel 10 (in-camera, integrated with Google Photos).
- **Cameras with known issues.** Nikon Z6 III's C2PA service was suspended in 2025 after a signing-key vulnerability and revoked certificates; not restored as of early 2026. Treat Nikon Z6 III credential claims with caution.
- **Newsrooms.** BBC, NYT, AP, and Reuters are CAI/C2PA members; production-pipeline integration is uneven across the industry.

**Verification tool:** drop any file at **`contentcredentials.org/verify`** to read its manifest, capture device, edit history, and any AI-tool involvement. Adobe's Content Authenticity Inspector and the Digimarc C2PA browser extension provide the same in plugin form.

**Hard binding vs soft binding.** Hard binding embeds a SHA-256 hash of the content in the signed manifest — any pixel change invalidates it (strong integrity, brittle to re-encoding). Soft binding stores a perceptual fingerprint or invisible watermark in a manifest repository — survives screenshots and transcoding but offers weaker integrity guarantees. Soft binding lets you *recover* a manifest after metadata stripping.

**Known limitations.**

- Screenshots strip hard-binding manifests entirely.
- Most social platforms strip metadata on upload. TikTok and Meta have started preserving Credentials on some surfaces; coverage is partial.
- Absence of Credentials does **not** mean fake. Most camera and phone images in circulation today are unsigned.
- Signing-key compromise is a real attack vector (Nikon 2025). A "valid signature" can be undermined by upstream breaches.

### Layer 2 — Automated detection tools

| Tool | Status (May 2026) | Pricing | Use |
|---|---|---|---|
| **Hive AI** (`thehive.ai`) | Operational | Demo + paid API | Image, video, audio. Strong for high volume |
| **Reality Defender** (`realitydefender.com`) | Operational | Free tier: 50 audio/image scans/month | Image, video, audio, text in one API |
| **AI or Not** (`aiornot.com`) | Operational | Free tier + paid | Fast image triage. First-pass, not authoritative |
| **Sensity AI** (`sensity.ai`) | Operational | Enterprise-priced, forensic-grade | Government/legal use; not journalist-budget-friendly |
| **DeepFake-o-Meter** (U. Buffalo) | Operational | Free, academic | Listed in CJR's recommended journalist set |
| **Adobe Content Authenticity Inspector** | Operational | Free | C2PA manifest reading only — no detection |
| **TrueMedia.org** | **Shut down January 14, 2025** | n/a | Tech open-sourced on GitHub; do not link out to the dead service |
| **Microsoft Video Authenticator** | No longer publicly offered | n/a | Skip |
| **Intel FakeCatcher** | Active research, not publicly available | n/a | Research/enterprise tier only |
| **Optic** | Unverified live status — last known still operating in 2025 CJR guide | Free | Use as one input among others; don't rely on as authoritative |
| **Deepware Scanner** | Domain active, live functionality unverified | Free web | Confirm responding before relying |

**Single-tool verdicts are not enough.** Run at least two detectors and treat disagreement as a signal to escalate to deeper analysis or source contact.

### Layer 3 — Detection by eye and ear (2026 calibration)

Older artifact tells — extra fingers, weird ears, asymmetric pupils — are largely gone in current diffusion and Sora-2-class video output. What still leaks in May 2026:

- **Boundary regions.** Hairlines, ear edges, tooth boundaries, glasses-to-skin transitions — sub-pixel inconsistency on careful inspection.
- **Lighting and shadow physics.** Highlights that don't match scene light direction; cast shadows missing or contradictory.
- **Eye reflection mismatches.** Left and right catchlights inconsistent with the scene.
- **Audio-video desync.** Phoneme-to-lip alignment drifts over multi-second clips.
- **Skin texture.** Waxy or over-smooth in places; noise pattern uniform across the frame instead of varying with surface.
- **Voice clones.** Breath placement, plosive consonants, and room tone are the remaining giveaways. Fortune (December 2025) reports voice cloning has crossed the indistinguishable threshold for casual listeners — assume voice-only verification fails.

Detection-by-eye is **unreliable on its own**. Use it for triage and to decide whether to escalate, never as the final ruling.

### The verification workflow for suspect media

1. **Check Content Credentials first.** Drop the file at `contentcredentials.org/verify`. A valid manifest from a known signer is a strong positive provenance signal. Absence proves nothing.
2. **Reverse image search.** Google Lens, TinEye, Yandex (still strongest for faces). Find earliest known appearance.
3. **Run two automated detectors.** Hive + Reality Defender for image; AI or Not for fast triage. Disagreement between detectors means escalate.
4. **Frame-by-frame and audio analysis.** For video, check boundary artifacts and lip sync. For audio, examine spectrogram, breath patterns, and room-tone uniformity.
5. **Reach the source.** Direct contact remains the highest-confidence step. C2PA tells you who *signed*; it doesn't tell you who *witnessed*.

## Document verification

### PDF and document analysis

```markdown
## Document verification steps

### Metadata examination
- Creation date and modification history
- Author information
- Software used to create
- Embedded fonts and images

### Visual inspection
- Consistent formatting throughout
- Font matching (no spliced text)
- Alignment of text and images
- Quality consistent across pages
- Signatures appear authentic

### Content verification
- Dates internally consistent
- Names spelled correctly throughout
- Reference numbers valid
- Contact information verifiable
- Letterhead matches known examples

### Provenance
- How was document obtained?
- Chain of custody documented?
- Original vs. copy?
- Can source provide additional context?
```

## Building a verification trail

### Documentation template

```markdown
## Verification record

**Claim being verified:**
[State the specific claim]

**Source of claim:**
- Name/account:
- Platform:
- Date first seen:
- URL (archived):

**Verification steps taken:**

### Step 1: [Description]
- Action taken:
- Tool/method used:
- Result:
- Screenshot/evidence saved: [filename]

### Step 2: [Description]
- Action taken:
- Tool/method used:
- Result:
- Screenshot/evidence saved: [filename]

[Continue for each step]

**Corroborating sources:**
1. [Source 1] - [What it confirms]
2. [Source 2] - [What it confirms]
3. [Source 3] - [What it confirms]

**Contradicting information:**
1. [Source] - [What it contradicts]

**Confidence assessment:**
- [ ] Verified true
- [ ] Likely true (high confidence)
- [ ] Unverified (insufficient evidence)
- [ ] Likely false (contradicting evidence)
- [ ] Verified false

**Reasoning:**
[Explain your conclusion based on evidence]

**Verification completed by:**
**Date:**
```

## Archiving evidence

### Web archiving best practices

For full archiving workflows (rate limits, batch jobs, recovery from broken archives), use the **web-archiving** skill. The snippet here covers the minimum journalist-usable pattern: archive the same URL to Wayback Machine and Archive.today simultaneously so a single archive going down doesn't lose the evidence.

```python
import requests
from urllib.parse import quote

def archive_url(url: str, perma_cc_api_key: str | None = None) -> dict:
    """Archive a URL to Wayback Machine and Archive.today.

    Returns a dict with the archived URL (or error) for each service.
    Pass perma_cc_api_key to also archive to Perma.cc (requires an account).
    """
    results = {}

    # Internet Archive Wayback Machine
    try:
        response = requests.get(
            f'https://web.archive.org/save/{quote(url, safe="")}',
            timeout=60,
            allow_redirects=True,
        )
        if response.status_code == 200:
            results['wayback'] = response.url
        else:
            results['wayback_error'] = f'HTTP {response.status_code}'
    except requests.RequestException as e:
        results['wayback_error'] = str(e)

    # Archive.today — POST to /submit/, the archived URL appears in the
    # Refresh header (or the Location header on a 302).
    try:
        response = requests.post(
            'https://archive.ph/submit/',
            data={'url': url},
            timeout=120,
            allow_redirects=False,
            headers={'User-Agent': 'Mozilla/5.0 (verification archive bot)'},
        )
        archived = response.headers.get('Refresh', '').split('url=')[-1] \
            or response.headers.get('Location', '')
        if archived:
            results['archive_today'] = archived
        else:
            results['archive_today_error'] = f'no archived URL returned (HTTP {response.status_code})'
    except requests.RequestException as e:
        results['archive_today_error'] = str(e)

    # Perma.cc (optional, requires API key from a Perma account)
    if perma_cc_api_key:
        try:
            response = requests.post(
                'https://api.perma.cc/v1/archives/',
                json={'url': url},
                headers={'Authorization': f'ApiKey {perma_cc_api_key}'},
                timeout=60,
            )
            if response.status_code == 201:
                results['perma_cc'] = f"https://perma.cc/{response.json()['guid']}"
            else:
                results['perma_cc_error'] = f'HTTP {response.status_code}'
        except requests.RequestException as e:
            results['perma_cc_error'] = str(e)

    return results
```

Run on every primary-source URL the moment you decide it might appear in the story. Pages disappear, get edited, or go behind paywalls. An archive captured at the moment of reporting is the difference between a defensible quote and one that evaporates before publication.

### Screenshot documentation

```markdown
## Screenshot best practices

1. **Full page capture**: Use browser extensions for full-page screenshots
2. **Include URL bar**: Shows the source URL
3. **Include timestamp**: System clock visible or add manually
4. **Save metadata**: Note when and how captured
5. **Multiple formats**: Save as PNG (lossless) and PDF
6. **Secure storage**: Hash files and store securely

Recommended tools:
- Hunchly (hunch.ly) - automatic capture and logging
- Screenpresso - full page with annotations
- Browser print-to-PDF - includes URL and date
```

## Interview verification

### Pre-interview source check

```markdown
## Source background check

### Public records
- [ ] Professional licenses verified
- [ ] Court records checked
- [ ] Business registrations confirmed
- [ ] Property records (if relevant)
- [ ] Campaign finance records (if political)

### Professional background
- [ ] LinkedIn profile reviewed
- [ ] Employer confirmed
- [ ] Previous employers contacted
- [ ] Published work reviewed
- [ ] Conference appearances verified

### Social media audit
- [ ] All platforms identified
- [ ] Post history reviewed
- [ ] Connections/followers analyzed
- [ ] Previous statements on topic
- [ ] Any deleted content found?

### Media appearances
- [ ] Previous interviews found
- [ ] Consistency with current claims
- [ ] Other journalists' assessments
- [ ] Any retractions or corrections?
```

### During interview verification

```markdown
## Real-time verification techniques

### Document requests
- Ask for documentation during interview
- Verify documents aren't altered
- Request originals, not copies when possible
- Note document condition and provenance

### Specific detail probing
- Ask for specific dates, names, locations
- Request corroborating witnesses
- Ask "How do you know that?"
- Follow up on vague answers

### Consistency checks
- Note initial version of story
- Return to key points later
- Compare details across tellings
- Flag inconsistencies for follow-up

### Recording best practices
- Get consent (check local laws)
- Use reliable recording equipment
- Backup recording in real-time
- Note non-verbal cues separately
```

## Verification resources

### Tools

| Tool | Purpose | URL |
|------|---------|-----|
| InVID / WeVerify | Video verification browser plugin | `weverify.eu` |
| TinEye | Reverse image search | `tineye.com` |
| Yandex Images | Reverse image search (best for faces) | `yandex.com/images` |
| Wayback Machine | Web archives | `web.archive.org` |
| Archive.today | Web archives (covers sites that block Wayback) | `archive.ph` |
| Meta Content Library | Meta public-content research (replaces CrowdTangle, sunset Aug 2024) | `transparency.meta.com/researchtools/meta-content-library` |
| Hoaxy | Claim spread visualization | `hoaxy.osome.iu.edu` |
| OpenCorporates | Company records | `opencorporates.com` |
| OCCRP Aleph | Document and entity search | `aleph.occrp.org` |
| FotoForensics | Image error-level analysis | `fotoforensics.com` |

**About CrowdTangle.** Meta sunset CrowdTangle on August 14, 2024. The replacement, the Meta Content Library, requires institutional affiliation (qualifying academic, journalist with a verified .edu/.org/.gov institution) and offers slower, less-feature-rich access. Skill content elsewhere on the web that still treats CrowdTangle as available is out of date.

**About Media Bias/Fact Check.** This site is one observer's editorial classification, not a peer-reviewed authority. Use it as one input among several when assessing an unfamiliar outlet, not as a definitive ruling.

### Training resources

- Bellingcat guides — `bellingcat.com/resources`
- Google News Initiative — `newsinitiative.withgoogle.com`
- Verification Handbook — `verificationhandbook.com`
- SPJ ethics resources — `spj.org/ethics`
- First Draft News — `firstdraftnews.org` (note: First Draft was wound down in 2022; the site remains a useful archive but is not actively maintained)

## Related skills

- **fact-check-workflow** — Structured claim verification and rating workflows
- **social-media-intelligence** — Deeper open-source intelligence on accounts and platforms
- **interview-prep** — Verifying source backgrounds before interviews
- **interview-transcription** — Verifying quotes against the original recording
- **web-archiving** — Full archiving workflows (Wayback, Archive.today, Perma.cc)
- **crisis-communications** — Time-pressure verification during breaking news
- **foia-requests** — Obtaining primary-source documents to support verification

---

## Skill metadata

| Field | Value |
|-------|-------|
| version | 1.1.0 |
| created | 2025-12-26 |
| updated | 2026-05-08 |
| author | Joe Amditis |
| domain | journalism, verification |
| complexity | intermediate |
