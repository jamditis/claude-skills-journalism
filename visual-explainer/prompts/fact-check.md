---
name: fact-check
description: Verify factual accuracy of a document against actual code and git history
---

Verify factual accuracy of `$ARGUMENTS` against the actual codebase.

## Phase 1: Extract claims

Read the document and identify every verifiable factual claim:
- Quantitative metrics (line counts, file counts, percentages)
- Naming (functions, types, file paths, module names)
- Behavioral descriptions (what code does, how systems interact)
- Structural relationships (dependencies, imports, data flow)
- Temporal facts (when changes were made, git history claims)

Skip subjective judgments, opinions, and analysis.

## Phase 2: Verify against source

For each claim:
- Read the referenced files
- Run git commands to check history
- Compare before/after states
- Validate specifications

Classify each: **confirmed**, **corrected**, or **unverifiable**.

## Phase 3: Correct in place

Make surgical edits to fix incorrect:
- Numbers and counts
- Names and paths
- Behavioral descriptions

Preserve document structure. Only rewrite sections that are fundamentally flawed.

## Phase 4: Add verification summary

Insert a summary section (HTML banner or markdown block) documenting:
- Total claims checked
- Confirmed count
- Specific corrections made
- Flagged unverifiable claims

## Phase 5: Report

Communicate what was checked, what was corrected, and open the file for review.

**This is a fact-checker only** — verify data accuracy. Leave analysis, opinions, and design judgments untouched.
