## Detecting AI-generated and synthetic media

By 2026, naked-eye detection of high-end synthetic media is no longer reliable. The Columbia Journalism Review's 2025 guide is blunt: detection tools "have largely not kept up with diffusion models." Treat any single tool's verdict as one input, not a ruling.

The verification stack now has two layers, **provenance** (was this content cryptographically signed when created?) and **detection** (does it look or sound generated?). Provenance is the stronger signal when present, but its absence doesn't mean fake.

### Layer 1, Content Credentials (C2PA) provenance check

The Coalition for Content Provenance and Authenticity (C2PA) standard ships cryptographic manifests inside image, audio, and video files describing their origin and edit history. Specification 2.2 was released in April–May 2025; the C2PA Conformance Program and Trust List launched mid-2025 and the legacy ingredient trust list was frozen January 1, 2026.

**Production adoption (verified May 2026):**

- **Image generators.** OpenAI DALL-E 3 (since 2023) and Sora 2 video write Credentials by default; Sora 2 also includes a visible moving watermark. Adobe Photoshop, Lightroom, and Firefly write Credentials across Creative Cloud. Microsoft Bing Image Creator, Designer, Copilot, and Azure OpenAI write Credentials. Google Gemini and Nano Banana Pro images carry C2PA plus SynthID.
- **Cameras (capture-side signing).** Leica M11-P (October 2023, first to ship), SL3-S; Sony Alpha 1 II, Alpha 9 III, PXW-Z300; Canon EOS R1 and R5 Mark II via firmware (July 2025); Google Pixel 10 (in-camera, integrated with Google Photos).
- **Cameras with known issues.** Nikon Z6 III's C2PA service was suspended in 2025 after a signing-key vulnerability and revoked certificates; not restored as of early 2026. Treat Nikon Z6 III credential claims with caution.
- **Newsrooms.** BBC, NYT, AP, and Reuters are CAI/C2PA members; production-pipeline integration is uneven across the industry.

**Verification tool:** drop any file at **`contentcredentials.org/verify`** to read its manifest, capture device, edit history, and any AI-tool involvement. Adobe's Content Authenticity Inspector and the Digimarc C2PA browser extension provide the same in plugin form.

**Hard binding vs soft binding.** Hard binding embeds a SHA-256 hash of the content in the signed manifest, any pixel change invalidates it (strong integrity, brittle to re-encoding). Soft binding stores a perceptual fingerprint or invisible watermark in a manifest repository, survives screenshots and transcoding but offers weaker integrity guarantees. Soft binding lets you *recover* a manifest after metadata stripping.

**Known limitations.**

- Screenshots strip hard-binding manifests entirely.
- Most social platforms strip metadata on upload. TikTok and Meta have started preserving Credentials on some surfaces; coverage is partial.
- Absence of Credentials does **not** mean fake. Most camera and phone images in circulation today are unsigned.
- Signing-key compromise is a real attack vector (Nikon 2025). A "valid signature" can be undermined by upstream breaches.

### Layer 2, Automated detection tools

| Tool | Status (May 2026) | Pricing | Use |
|---|---|---|---|
| **Hive AI** (`thehive.ai`) | Operational | Demo + paid API | Image, video, audio. Strong for high volume |
| **Reality Defender** (`realitydefender.com`) | Operational | Free tier: 50 audio/image scans/month | Image, video, audio, text in one API |
| **AI or Not** (`aiornot.com`) | Operational | Free tier + paid | Fast image triage. First-pass, not authoritative |
| **Sensity AI** (`sensity.ai`) | Operational | Enterprise-priced, forensic-grade | Government/legal use; not journalist-budget-friendly |
| **DeepFake-o-Meter** (U. Buffalo) | Operational | Free, academic | Listed in CJR's recommended journalist set |
| **Adobe Content Authenticity Inspector** | Operational | Free | C2PA manifest reading only, no detection |
| **TrueMedia.org** | **Shut down January 14, 2025** | n/a | Tech open-sourced on GitHub; do not link out to the dead service |
| **Microsoft Video Authenticator** | No longer publicly offered | n/a | Skip |
| **Intel FakeCatcher** | Active research, not publicly available | n/a | Research/enterprise tier only |
| **Optic** | Unverified live status, last known still operating in 2025 CJR guide | Free | Use as one input among others; don't rely on as authoritative |
| **Deepware Scanner** | Domain active, live functionality unverified | Free web | Confirm responding before relying |

**Single-tool verdicts are not enough.** Run at least two detectors and treat disagreement as a signal to escalate to deeper analysis or source contact.

### Layer 3, Detection by eye and ear (2026 calibration)

Older artifact tells, extra fingers, weird ears, asymmetric pupils, are largely gone in current diffusion and Sora-2-class video output. What still leaks in May 2026:

- **Boundary regions.** Hairlines, ear edges, tooth boundaries, glasses-to-skin transitions, sub-pixel inconsistency on careful inspection.
- **Lighting and shadow physics.** Highlights that don't match scene light direction; cast shadows missing or contradictory.
- **Eye reflection mismatches.** Left and right catchlights inconsistent with the scene.
- **Audio-video desync.** Phoneme-to-lip alignment drifts over multi-second clips.
- **Skin texture.** Waxy or over-smooth in places; noise pattern uniform across the frame instead of varying with surface.
- **Voice clones.** Breath placement, plosive consonants, and room tone are the remaining giveaways. Fortune (December 2025) reports voice cloning has crossed the indistinguishable threshold for casual listeners, assume voice-only verification fails.

Detection-by-eye is **unreliable on its own**. Use it for triage and to decide whether to escalate, never as the final ruling.

### The verification workflow for suspect media

1. **Check Content Credentials first.** Drop the file at `contentcredentials.org/verify`. A valid manifest from a known signer is a strong positive provenance signal. Absence proves nothing.
2. **Reverse image search.** Google Lens, TinEye, Yandex (still strongest for faces). Find earliest known appearance.
3. **Run two automated detectors.** Hive + Reality Defender for image; AI or Not for fast triage. Disagreement between detectors means escalate.
4. **Frame-by-frame and audio analysis.** For video, check boundary artifacts and lip sync. For audio, examine spectrogram, breath patterns, and room-tone uniformity.
5. **Reach the source.** Direct contact remains the highest-confidence step. C2PA tells you who *signed*; it doesn't tell you who *witnessed*.
