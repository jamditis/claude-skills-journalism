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
said, and can we prove it. Two facts, written alongside every transcript, answer
it:

- the exact engine and model build that ran: the engine and version (for example
  `whisper.cpp 1.7.x` or `openai-whisper <version>`) and the model file including
  its quantization, since a `base.en` at `q5_0` and the same model at `f16` decode
  differently, so the model name alone is not enough, and
- a hash of the source media (for example the `sha256` of the input file).

Write them as a sidecar next to the transcript, `<name>.transcript.meta.json`,
not buried in a log. The sidecar also records the decode parameters, so a re-run
reproduces the same timestamps and not just the same words:

```json
{
  "engine": "whisper.cpp",
  "engine_build": "1.7.6 (b0a5b0c)",
  "model": "base.en",
  "model_quantization": "q5_0",
  "source_sha256": "9f2b8c1d...c41a",
  "decode": {
    "beam_size": 5,
    "temperature": 0,
    "no_speech_threshold": 0.6,
    "compression_ratio_threshold": 2.4,
    "threads": 4
  }
}
```

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

Fix the decode parameters (beam size, temperature, and the no-speech and
compression thresholds) and the thread count rather than leaving them at library
defaults that can shift between versions or hosts. With those pinned, the
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
