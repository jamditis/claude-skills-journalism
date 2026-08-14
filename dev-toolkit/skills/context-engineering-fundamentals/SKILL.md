---
name: context-engineering-fundamentals
description: Understand how Claude manages attention and when context degrades. Activate for long sessions, complex tasks, or when Claude seems to "forget" information.
---

# Context Engineering Fundamentals

Context engineering is the practice of managing an LLM's limited attention budget. This skill helps you understand why Claude sometimes "forgets" things and how to work within context limitations.

## When to activate

- Working on long, multi-step tasks
- Claude seems to forget earlier instructions or context
- Debugging "why didn't Claude use the information I gave it?"
- Planning how to structure complex prompts
- Optimizing for token efficiency

## Core concept

**Context windows are constrained by attention mechanics, not just token capacity.** A 200K token window doesn't mean 200K tokens of useful information. Attention degrades, especially in the middle of long contexts.

## The lost-in-middle effect

Research shows information position dramatically affects recall:

| Position | Recall Accuracy |
|----------|----------------|
| Beginning | High (~90%) |
| Middle | Low (50-70%) |
| End | High (~85%) |

**Implication:** Put critical information at the start or end, not buried in the middle.

## Context degradation patterns

### 1. Lost-in-middle
Information in the middle of long context gets lower attention weight.

**Mitigation:** Structure with explicit sections. Put critical constraints at start AND end.

### 2. Context poisoning
Errors compound when incorrect information enters context (from tool outputs, summaries, or earlier mistakes).

**Mitigation:** Validate intermediate outputs. Don't blindly trust previous responses.

### 3. Context distraction
Irrelevant information forces attention allocation away from relevant content. Models can't "skip" irrelevant context.

**Mitigation:** Be selective about what goes into context. More isn't better.

### 4. Context confusion
Multiple task types or conflicting instructions create ambiguous responses.

**Mitigation:** One task per interaction when possible. Clear task boundaries.

### 5. Context clash
Contradictory information from multiple sources causes derailing conflicts.

**Mitigation:** Resolve contradictions explicitly before asking Claude to use the information.

## Practical degradation thresholds

These bands are illustrative heuristics, not model-independent guarantees. The transition points move with the model, its version, and the retrieval or reasoning task: a short context is not always reliable, and a long one is not always lossy. Measure recall on your own model and workload before you treat a threshold as a hard cutoff for discarding or summarizing context.

| Context Size | Expected Behavior |
|--------------|-------------------|
| < 8K tokens | Full attention, reliable recall |
| 8-32K tokens | Good performance, some middle-loss |
| 32-100K tokens | Noticeable degradation, need explicit structure |
| > 100K tokens | Significant loss, use summarization/chunking |

## Mitigation strategies

### Write externally
Don't rely on Claude to remember across turns. Write important state to files, but agree the path with the user first and prefer a gitignored workspace so you never overwrite project-owned content:
```
With the user's approval, after each major step write progress to an agreed scratch file (for example a gitignored PROGRESS.md or a path they choose)
Before starting, read that file back to restore context
```

### Select carefully
Filter irrelevant context before loading:
```
Instead of: "Here are all 50 files, find the bug"
Do: "Here are the 3 files involved in the error"
```

### Compress strategically
Summarize while maintaining signal:
```
Instead of: Full 1000-line file
Do: Key functions and their signatures, with context on the specific area
```

### Isolate contexts
For complex tasks, use sub-agents with focused contexts rather than one agent with everything.

## Signs of context degradation

| Symptom | Likely Cause |
|---------|--------------|
| Ignores earlier instructions | Lost-in-middle or context too long |
| Contradicts itself | Context confusion or clash |
| Repeats information you gave | Attention not reaching that content |
| Misses obvious details | Context distraction |
| Gets progressively worse | Context poisoning from errors |

## References

- "Lost in the Middle" (Liu et al., 2023) - Position effects in long context
- "Needle in a Haystack" benchmark - Context retrieval testing
- RULER benchmark - Multi-hop reasoning over long context
