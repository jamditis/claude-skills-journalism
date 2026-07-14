# Video-transcribe reproducibility contract (tier B, issue #115)

Resolves the pre-publish gate the tier B checklist puts on `video-transcribe`:
"Whisper on GPU. Flag the GPU/Whisper dependency in `SKILL.md` and give a CPU or
hosted-API fallback so it runs from a clean checkout without a specific GPU box.
If the contest entry uses this skill, the re-runnability rule applies: an
evaluator must be able to run it without our hardware."

The video quartet is the standout tier B asset and the checklist says to publish
it first, but the skill source lives on the legion GPU box, so the publish itself
stays blocked on that box. The design that removes its hardest risk does not:
the re-runnability contract is engine-and-hardware-independent and can be settled
now, so the eventual publish is a mechanical implementation of what this doc
decides rather than a place to invent it. It folds in the reproducibility
detail [@sophymarine raised on the issue](https://github.com/jamditis/claude-skills-journalism/issues/115#issuecomment-4746674899),
which named the two pieces a newsroom transcript needs.

## The gate, restated

Two rules point at the same skill from different directions:

- The tier B checklist: a clean checkout, on any machine, must be able to run
  `video-transcribe`. A hard dependency on one GPU box fails that.
- The contest code of conduct (jamditis/gain-agent-challenge#17): anything the
  GAIN entry uses must be re-runnable by an evaluator on their own hardware. A
  transcription step that only runs on our GPU cannot be evaluated.

So the skill needs a fallback that runs anywhere, and the transcript it produces
needs enough provenance that a re-run is checkable against the original. Neither
is a code change to the legion source; both are contract decisions.

## Provenance the transcript must carry

A newsroom transcript gets quoted, and sometimes disputed later. When that
happens the question is always the same: does the text match what was actually
said, and can we prove it. The answer is a small set of facts written alongside
every transcript, one for each input that changes the decoded text, so a re-run
that matches the record cannot silently diverge:

- the exact engine and model build that ran: the engine and version (for example
  `whisper.cpp 1.7.x` or `openai-whisper <version>`) and the model file including
  its quantization, since a `base.en` at `q5_0` and the same model at `f16` decode
  differently, so the model name alone is not enough,
- a digest of the model weights themselves (the `sha256` of the model file) plus a
  retrievable source for that exact file (a download URL, the fetch command, or a
  vendored-artifact reference): a re-download from a different mirror or a fresh
  re-quantization can carry the same `base.en` / `q5_0` label yet different weights
  that decode to different text, so the label alone does not pin the model, and the
  digest only verifies a file an evaluator already has rather than telling them
  where to obtain the identical one,
- a hash of the source media (for example the `sha256` of the input file), and
- for any input that is not already the audio Whisper decodes (a video, or audio
  that has to be transcoded), the exact extraction command and tool version plus a
  hash of the normalized audio whisper.cpp actually consumed: two evaluators can
  verify the same MP4 yet feed Whisper different PCM if their ffmpeg version or
  extraction flags differ, so the source hash alone does not pin the decoder input.

Write them as a sidecar next to the transcript, `<name>.transcript.meta.json`,
not buried in a log. The sidecar also records the decode parameters, so a re-run
reproduces the same timestamps and not just the same words:

```json
{
  "engine": "whisper.cpp",
  "engine_build": "1.7.6 (b0a5b0c)",
  "model": "base.en",
  "model_quantization": "q5_0",
  "model_sha256": "5f8c...9d2e",
  "model_source": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en-q5_0.bin",
  "source_sha256": "9f2b8c1d...c41a",
  "audio": {
    "extract_command": "ffmpeg -i input.mp4 -ar 16000 -ac 1 -c:a pcm_s16le audio.wav",
    "tool_version": "ffmpeg 6.1.1",
    "audio_sha256": "3a1e...77bc"
  },
  "decode": {
    "beam_size": 5,
    "temperature": 0,
    "no_fallback": true,
    "no_gpu": true,
    "language": "en",
    "translate": false,
    "entropy_thold": 2.4,
    "logprob_thold": -1.0,
    "no_speech_thold": 0.6,
    "threads": 4
  }
}
```

The `no_fallback` flag is load-bearing, not decoration. whisper.cpp's default
temperature fallback re-decodes a segment at rising temperatures when it trips the
no-speech, entropy, or log-probability checks, so on a hard segment a run that
records `temperature: 0` can still leave the deterministic zero-temperature path,
and two reruns can produce different text while both matching this sidecar. The
transcript-of-record path sets `--no-fallback` so the recorded parameters actually
determine the output; a run that deliberately allows fallback records the full
temperature schedule it used instead.

The decode field names follow whisper.cpp's CLI, not openai-whisper's. whisper.cpp
pins decoder-fail behaviour with `--entropy-thold` and `--logprob-thold` (plus
`--no-speech-thold`) and has no `compression_ratio_threshold`, so the sidecar
records those knobs by their real names. `no_gpu` is required, not optional:
whisper.cpp initializes `use_gpu = true` and runs on CPU only when passed
`--no-gpu`, so without it the transcript of record can be produced with GPU kernels
while the sidecar still says `engine: whisper.cpp`, defeating the clean CPU rerun
this contract promises. `language` and `translate` (and `prompt` or `max_context`
when a clip uses them) pin the text-conditioning that would otherwise change the
output while the rest of the block still matched.

The `audio` block is required only when the decoded audio is not the source file
itself: for a `.wav` fed straight to whisper.cpp, `source_sha256` and `audio_sha256`
are equal and the block can be omitted.

With those facts anyone can re-run the same engine, model, and parameters over the
same verified file and compare the result to the quoted text. The sidecar is the
audit trail; without it a disputed quote has no way back to the source.

## The clean-checkout fallback

Whisper on the GPU stays available as a throughput accelerator for bulk runs, but
the transcript of record, the one a newsroom might quote and an evaluator has to
re-run, is the `whisper.cpp` CPU path with the `small` or `base` model. That is
the engine every machine can run and the only one an auditor without a GPU can
reproduce. It makes no remote calls, so a transcript never leaves the evaluator's
machine and the run does not depend on an API key or a network. On short
accountability clips the `base` model is adequate; `small` trades speed for a
little more accuracy.

Fix the decode parameters (beam size, temperature, and whisper.cpp's entropy,
log-probability, and no-speech thresholds) and the thread count rather than leaving
them at library defaults that can shift between versions or hosts, and pass
`--no-gpu` so the record path runs on CPU even on a GPU-capable box. With those pinned, the
timestamps come out repeatable, which is what lets the later quartet stages point
back to exact clip boundaries: `video-frames` and `video-dashboard` reference
timecodes the transcript produced, so if those move on a re-run the downstream
references break.

A hosted transcription API is a legitimate third option for someone without a
usable CPU path, but it breaks the no-remote-calls guarantee and reintroduces a
key and a network dependency. So the SKILL.md offers it as an explicit opt-in,
not the default, and says plainly that it forfeits the local-only property.

## What "repeatable" means here, and does not

Be honest about the boundary so the contract does not overpromise:

- The `whisper.cpp` CPU path is reproducible when its full state is pinned: the
  same engine build, the same model file including its quantization, greedy or
  temperature-zero decode, the same beam and threshold parameters, and a fixed
  thread count (thread count changes the reduction order and can move the output).
  Pin all of those and the text and timestamps repeat. That is why the transcript
  of record runs on this path.
- The GPU `openai-whisper` fast path is not reliably bit-reproducible, even
  run to run on the same box: CUDA kernel selection and reduction order are not
  guaranteed identical, so the logits, and occasionally the decoded text, can
  shift. It is fine for throughput; it is not the auditable artifact.
- Across engines (GPU `openai-whisper` versus CPU `whisper.cpp`), model sizes, or
  quantizations, the output is not byte-identical at all. Different
  implementations decode differently.

The provenance sidecar bridges this only when the auditor can run the same engine,
which is the reason the transcript of record is the CPU path: an evaluator without
a GPU can always re-run `whisper.cpp` with the recorded model and parameters and
land in the reproducible case. A transcript produced only on the GPU could not be
re-run by that evaluator at all, which would defeat the re-runnability rule. So
the contract's promise is "re-runnable and checkable on the CPU path any evaluator
has," not "one canonical transcript for a clip regardless of engine." The second
is not true of Whisper, and claiming it would mislead anyone who audits a quote.

## What the published SKILL.md must carry

So the legion publish is mechanical, its `SKILL.md` carries:

- a dependency flag: GPU Whisper is an optional throughput accelerator, not a
  requirement, and the `whisper.cpp` CPU path is the transcript of record;
- the pinned `whisper.cpp` decode parameters and thread count, documented, so the
  CPU path reproduces from a clean checkout;
- the hosted-API path as an explicit opt-in, with the note that it forfeits the
  local-only guarantee;
- the provenance sidecar spec (engine and model build including quantization,
  source-media hash, decode parameters and thread count) and where it is written;
- the "what repeatable means" boundary, so a user does not expect cross-engine
  byte-identity;
- an attribution line crediting @sophymarine for the reproducibility design, per
  the contest code of conduct, since this ships before the July 15, 2026
  attribution date.

## Still gating the actual publish (not resolved here)

This settles the re-runnability and provenance contract only. Before
`video-transcribe` (and the quartet around it) ships it still needs:

- the skill source pulled from the legion GPU box, where all four quartet stages
  live and this repo has none of them (confirmed absent on houseofjawn, issue
  #115 comment 2026-06-15);
- the standard SKILL.md description tuned for trigger accuracy;
- the catalog-manifest updates a new plugin requires (README and
  docs/index.html at minimum);
- the whole quartet published as one plugin so the stages compose, per the
  checklist.

Recorded from the tier B publishing pass. The contract here is hardware-free and
lands now; the quartet publish stays blocked on the legion GPU box and is
unaffected by that block being resolved separately.
