---
name: interview-transcription
description: Transcription workflows, recording management, and quote extraction for journalists. Use when processing audio/video recordings, generating transcripts with timestamps, extracting quotes for fact-checking, or building source-and-recording databases. For interview question design and pre-interview preparation, see the interview-prep skill.
---

# Interview transcription and management

Practical workflows for journalists managing interviews from preparation through publication.

## When to activate

- Preparing questions for an interview
- Processing audio/video recordings
- Creating or managing transcripts
- Organizing notes from multiple sources
- Building a source relationship database
- Generating timestamped quotes for fact-checking
- Converting recordings to publishable quotes

## Recording setup for transcription

For pre-interview research, question design, attribution agreements, and consent scripts, use the **interview-prep** skill. The notes here cover only the recording configuration that affects transcription quality.

```python
# Standard recording configuration for clean transcription
RECORDING_SETTINGS = {
    'format': 'wav',           # Lossless for transcription
    'sample_rate': 16000,      # Whisper resamples to 16k anyway; 16k saves disk
    'channels': 1,             # Mono is fine for speech; stereo only if mics are positionally distinct
    'backup': True,            # Always run a backup recorder
}

# File naming convention
# YYYY-MM-DD_source-lastname_topic.wav
# Example: 2026-05-08_smith_budget-hearing.wav
```

**Two-device rule.** Always record on two devices. Phone as backup minimum. If using a wireless lav mic, the recorder built into the lav unit is one device; the phone running a backup app is the second.

**Mono is preferred** unless each speaker has their own dedicated microphone routed to a distinct channel. Stereo with both speakers bleeding into both channels is worse for diarization than clean mono.

## Transcription workflows

### Automated transcription pipeline

Vanilla OpenAI Whisper transcribes audio to text but does **not** assign speaker labels. To get diarized output ("Speaker 1:" / "Speaker 2:" / etc.) you need a tool that combines Whisper with a diarization model — typically **WhisperX** (`m-bain/whisperX`), which wraps faster-whisper transcription with pyannote.audio diarization and produces word-level timestamps with speaker IDs in one pass.

```python
from pathlib import Path
import subprocess
import json

def transcribe_interview(
    audio_path: str,
    output_dir: str = "./transcripts",
    diarize: bool = True,
    hf_token: str | None = None,
    min_speakers: int = 2,
    max_speakers: int = 2,
) -> dict:
    """
    Transcribe an interview using WhisperX (Whisper + pyannote diarization).
    Returns a transcript with word-level timestamps and speaker labels.

    Diarization needs a Hugging Face token with access to the pyannote
    speaker-diarization-3.1 model. Accept the model EULA at
    huggingface.co/pyannote/speaker-diarization-3.1 once, then pass the token.
    """
    Path(output_dir).mkdir(exist_ok=True)

    cmd = [
        'whisperx', audio_path,
        '--model', 'large-v3',
        '--output_format', 'json',
        '--output_dir', output_dir,
        '--language', 'en',
        '--compute_type', 'int8',     # CPU-friendly; use 'float16' on GPU
        '--min_speakers', str(min_speakers),
        '--max_speakers', str(max_speakers),
    ]

    if diarize:
        cmd.append('--diarize')
        if hf_token:
            cmd += ['--hf_token', hf_token]

    subprocess.run(cmd, check=True, capture_output=True)

    json_path = Path(output_dir) / f"{Path(audio_path).stem}.json"
    with open(json_path) as f:
        return json.load(f)

def format_for_editing(transcript: dict) -> str:
    """Convert to journalist-friendly format with timestamps."""
    lines = []
    for segment in transcript.get('segments', []):
        timestamp = format_timestamp(segment['start'])
        text = segment['text'].strip()
        lines.append(f"[{timestamp}] {text}")
    return '\n\n'.join(lines)

def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
```

**Falling back to plain Whisper.** If diarization is overkill or you can't get a Hugging Face token, drop the `--diarize` flag — the model still produces accurate timestamped transcription and you label speakers manually based on context. `faster-whisper` (CTranslate2 backend) is the speed-optimized variant and works the same way at the CLI. `whisper.cpp` is the C++ port for resource-constrained machines (Raspberry Pi, older laptops); it doesn't include diarization but runs the small/medium models on CPU comfortably.

### Manual transcription template

For sensitive interviews or when AI transcription fails:

```markdown
## Transcript: [Source] - [Date]

**Recording file**: [filename]
**Duration**: [XX:XX]
**Transcribed by**: [name]
**Verified against recording**: [ ] Yes / [ ] No

---

[00:00:15] **Q**: [Your question]

[00:00:45] **A**: [Source response - verbatim, including ums, pauses noted as (...)]

[00:01:30] **Q**: [Follow-up]

[00:01:42] **A**: [Response]

---

## Notes
- [Anything not captured in audio: gestures, documents shown, etc.]

## Potential quotes
- [00:01:42] "Quote that stands out" - context: [why it matters]
```

## Quote extraction and verification

### Pull quotes workflow

```python
from dataclasses import dataclass
from typing import Optional
import re

@dataclass
class Quote:
    text: str
    timestamp: str
    speaker: str
    context: str
    verified: bool = False
    used_in: Optional[str] = None

class QuoteBank:
    """Manage quotes from interview transcripts."""

    def __init__(self):
        self.quotes = []

    def extract_quote(self, transcript: str, start_time: str,
                      end_time: str, speaker: str, context: str) -> Quote:
        """Extract and store a quote with metadata."""
        # Pull text between timestamps
        pattern = rf'\[{re.escape(start_time)}\](.+?)(?=\[\d|$)'
        match = re.search(pattern, transcript, re.DOTALL)

        if match:
            text = match.group(1).strip()
            quote = Quote(
                text=text,
                timestamp=start_time,
                speaker=speaker,
                context=context
            )
            self.quotes.append(quote)
            return quote
        return None

    def verify_quote(self, quote: Quote, audio_path: str) -> bool:
        """Mark quote as verified against original recording."""
        # In practice: listen to audio at timestamp, confirm accuracy
        quote.verified = True
        return True

    def export_for_story(self) -> str:
        """Export verified quotes ready for publication."""
        output = []
        for q in self.quotes:
            if q.verified:
                output.append(f'"{q.text}"\n— {q.speaker}\n[Timestamp: {q.timestamp}]')
        return '\n\n'.join(output)
```

### Quote accuracy checklist

Before publishing any quote:

```markdown
- [ ] Listened to original recording at timestamp
- [ ] Quote is verbatim (or clearly marked as paraphrased)
- [ ] Context preserved (not cherry-picked to change meaning)
- [ ] Speaker identified correctly
- [ ] Timestamp documented for fact-checker
- [ ] Source approved quote (if agreement made)
```

## Source management database

### Interview tracking schema

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class SourceStatus(Enum):
    ACTIVE = "active"           # Currently engaged
    DORMANT = "dormant"         # Not recently contacted
    DECLINED = "declined"       # Refused to participate
    OFF_RECORD = "off_record"   # Background only

class InterviewType(Enum):
    ON_RECORD = "on_record"
    BACKGROUND = "background"
    DEEP_BACKGROUND = "deep_background"
    OFF_RECORD = "off_record"

@dataclass
class Source:
    name: str
    organization: str
    contact_info: dict  # email, phone, signal, etc.
    beat: str
    status: SourceStatus = SourceStatus.ACTIVE
    interviews: List['Interview'] = field(default_factory=list)
    notes: str = ""

    # Relationship tracking
    first_contact: Optional[datetime] = None
    trust_level: int = 1  # 1-5 scale

@dataclass
class Interview:
    source: str
    date: datetime
    interview_type: InterviewType
    recording_path: Optional[str] = None
    transcript_path: Optional[str] = None
    story_slug: Optional[str] = None
    key_quotes: List[str] = field(default_factory=list)
    follow_up_needed: bool = False
    notes: str = ""
```

### Quick source lookup

```python
def find_sources_for_story(sources: List[Source], topic: str,
                           beat: str = None) -> List[Source]:
    """Find relevant sources for a new story."""
    matches = []
    for source in sources:
        # Filter by beat if specified
        if beat and source.beat != beat:
            continue
        # Only suggest active sources
        if source.status != SourceStatus.ACTIVE:
            continue
        # Check if they've spoken on similar topics
        for interview in source.interviews:
            if topic.lower() in interview.notes.lower():
                matches.append(source)
                break

    # Sort by trust level
    return sorted(matches, key=lambda s: s.trust_level, reverse=True)
```

## Audio/video processing

### Batch processing multiple recordings

```python
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import json

def batch_transcribe(recordings_dir: str, output_dir: str) -> dict:
    """Process all recordings in a directory."""
    recordings = list(Path(recordings_dir).glob('*.wav')) + \
                 list(Path(recordings_dir).glob('*.mp3')) + \
                 list(Path(recordings_dir).glob('*.m4a'))

    results = {}

    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(transcribe_interview, str(rec), output_dir): rec
            for rec in recordings
        }

        for future in futures:
            rec = futures[future]
            try:
                transcript = future.result()
                results[rec.name] = {
                    'status': 'success',
                    'transcript': transcript
                }
            except Exception as e:
                results[rec.name] = {
                    'status': 'error',
                    'error': str(e)
                }

    return results
```

### Video interview extraction

```python
import subprocess

def extract_audio_from_video(video_path: str, output_path: str = None) -> str:
    """Extract audio track from video for transcription."""
    if output_path is None:
        output_path = video_path.rsplit('.', 1)[0] + '.wav'

    subprocess.run([
        'ffmpeg', '-i', video_path,
        '-vn',  # No video
        '-acodec', 'pcm_s16le',  # WAV format
        '-ar', '44100',  # Sample rate
        '-ac', '1',  # Mono
        output_path
    ], check=True)

    return output_path
```

## Legal and ethical considerations

### Consent documentation

```markdown
## Recording consent record

**Date**:
**Source name**:
**Recording type**: [ ] Audio [ ] Video
**Interview type**: [ ] On record [ ] Background [ ] Off record

### Consent obtained:
- [ ] Verbal consent recorded at start of interview
- [ ] Written consent form signed
- [ ] Email confirmation of consent

### Jurisdiction notes:
- Interview location state/country:
- One-party or two-party consent jurisdiction:
- Any specific restrictions agreed:

### Agreed terms:
- [ ] Full attribution allowed
- [ ] Organization attribution only
- [ ] Anonymous source
- [ ] Review quotes before publication
- [ ] Embargo until [date]:
```

### Recording-consent jurisdiction

For the per-state breakdown of one-party vs. all-party consent, hidden-recording rules, and federal preemption, use the **interview-prep** skill (which points to the Reporters Committee for Freedom of the Press *Reporter's Recording Guide* — the authoritative continuously-updated source).

**Always get explicit consent on recording** regardless of jurisdiction. Note the consent verbatim at the head of every transcript file (timestamp, speaker, response). This protects you legally everywhere and gives the fact-checker a clean starting point.

## Tools and resources

| Tool | Purpose | Notes |
|------|---------|-------|
| OpenAI Whisper | Local transcription, no diarization | Free, runs offline. `large-v3` is the current best model |
| WhisperX | Whisper + speaker diarization | `m-bain/whisperX`. Free. Word-level timestamps with speaker IDs. Needs a Hugging Face token for the pyannote model |
| faster-whisper | Speed-optimized Whisper | CTranslate2 backend. ~4x faster than vanilla Whisper at the same accuracy. Used internally by WhisperX |
| whisper.cpp | CPU-friendly Whisper port | C++ implementation. Runs the small/medium models on a Raspberry Pi |
| pyannote.audio | Standalone speaker diarization | Use directly when you already have transcripts from another source |
| MacWhisper / Buzz | GUI wrappers for Whisper | macOS / cross-platform GUIs for journalists who don't want a CLI |
| Otter.ai | Cloud transcription, real-time | Verify privacy posture before using with sensitive sources — Otter Pilot has historically joined meetings unannounced and indexed transcripts; check current settings |
| Descript | Edit audio like text | Good for pulling clips. Cloud-hosted |
| Rev (human + AI) | Human transcription for sensitive material | Slower, more accurate. Cloud-hosted |
| Trint | Journalist-focused, collaboration | Cloud-hosted. Has team features |
| oTranscribe | Free web-based manual transcription aid | Local-only (browser); no upload. Good for off-the-record material you can't hand to a cloud service |

## Related skills

- **interview-prep** — Pre-interview research, question design, consent scripts, and recording-law jurisdiction
- **source-verification** — Verify source credentials before interview
- **fact-check-workflow** — Verify quotes against the recording before publication
- **foia-requests** — Get documents to inform interview questions
- **data-journalism** — Analyze data sources mentioned in interviews
- **newsroom-style** — Convert verbatim quotes into AP-style copy for publication

---

## Skill metadata

| Field | Value |
|-------|-------|
| version | 1.0.0 |
| created | 2025-12-26 |
| updated | 2026-05-08 |
| author | Joe Amditis |
| domain | journalism, research |
| complexity | intermediate |
