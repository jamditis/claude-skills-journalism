---
name: context-engineering-fundamentals
description: Manages attention and evidence in long agent sessions. Use for lost instructions, dropped evidence, or large multi-agent contexts.
---

# Context engineering fundamentals

Context engineering is the practice of managing an LLM's limited attention budget. Use this skill to keep instructions, evidence, and state available during long work.

## Core concept

**Context windows are constrained by attention mechanics, not only token capacity.** A large context limit does not guarantee equal use of every item.

## The lost-in-middle effect

The "Lost in the Middle" experiments show that retrieval quality can change with information position. The result depends on the model, task, context length, and number of documents.

| Position | Common test result |
|----------|--------------------|
| Beginning | Often easier to retrieve |
| Middle | Can be harder to retrieve |
| End | Often benefits from recency |

**Implication:** Keep critical constraints easy to find and repeat them near the decision that uses them. Do not assume position alone predicts recall.

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

## Measure before compressing

Do not use a fixed token threshold to decide when context is reliable. Measure retrieval and reasoning quality on your own model and task. Test representative evidence at several positions, then compare the result before and after summarization.

Compress only when the measured result or the agent's behavior shows a problem. Preserve exact constraints, decisions, source links, unresolved questions, and verification evidence.

## Mitigation strategies

### Write externally
Do not rely on the agent to remember across turns. Write important state to files, but agree the path with the user first. Prefer a gitignored workspace so you never overwrite project-owned content:
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
For complex tasks, use subagents with focused contexts rather than one agent with everything.

## Signs of context degradation

| Symptom | Likely cause |
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
