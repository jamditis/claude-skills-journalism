# video-toolkit

Four skills that compose into one pipeline for social-video accountability
reporting: collect a subject's public video, transcribe it, look at what is on
screen, and read the whole set together.

Install the plugin to get all four:

```
/plugin install video-toolkit@claude-skills-journalism
```

Or copy a single skill:

```bash
cp -r video-toolkit/skills/video-download ~/.claude/skills/
```

## The pipeline

| Skill | What it does |
|---|---|
| [video-download](./skills/video-download/) | Pull public video from Twitter/X, TikTok, YouTube, Instagram, and Facebook with yt-dlp, falling back to browser automation where the extractors are broken |
| [video-transcribe](./skills/video-transcribe/) | Batch transcribe with Whisper and write a provenance sidecar per transcript so a quote can be traced back to the audio |
| [video-frames](./skills/video-frames/) | Extract frames, composite 3x3 grids, and run vision analysis over on-screen text, setting, and presentation style |
| [video-dashboard](./skills/video-dashboard/) | Aggregate transcripts and frame analysis into topic, tone, and cross-platform views behind a single-page dashboard |

Each stage reads what the previous one wrote, so run them in order the first
time. After that they are independent — re-run `video-frames` alone when you add
clips, and the dashboard picks up the new JSON.

## Security boundaries

Every stage treats social pages, metadata, media, transcripts, on-screen text,
and analysis JSON as untrusted data rather than instructions. The skills do not
pre-approve Bash, browser, write, or agent tools. Public unauthenticated access
is the default; any credentialed browser session requires explicit user approval
and a clean project profile. Media parsing runs with private-network access
blocked and resource limits, and the dashboard uses a committed exact Chart.js
asset with DOM-safe rendering rather than runtime CDN code.

## Transcripts you can defend

`video-transcribe` treats the CPU `whisper.cpp` path as the transcript of record
and the GPU path as an optional accelerator, because a transcript that only runs
on one GPU box cannot be checked by anyone else. Every transcript gets a
`.transcript.meta.json` sidecar recording the engine and model build, a hash of
the source media, and the pinned decode parameters, so a disputed quote has a way
back to the audio. The skill also states plainly what does *not* reproduce:
GPU Whisper is not bit-reproducible run to run, and output is never byte-identical
across engines or model quantizations.

## Requirements

`yt-dlp` and `ffmpeg` for the download and audio stages, `whisper.cpp` (with a
`ggml` model) for the transcript of record, and Python for the analysis stage.
The GPU fast path additionally needs `openai-whisper` and CUDA; nothing in the
pipeline requires it.

Downloading video from social platforms is subject to those platforms' terms and
to local law. These skills collect from public accounts for reporting and
analysis; they are not a scraping-at-scale tool and do not bypass access
controls or authentication.
