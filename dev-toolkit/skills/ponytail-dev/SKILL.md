---
name: ponytail-dev
description: Use to implement or review software with minimal code and proportional checks.
license: MIT
---

# Ponytail dev

Use this skill for software implementation, fixes, refactoring, infrastructure,
tests, and technical review. In mixed work, treat the approved design as fixed
input and apply this skill only to implementation.

Do not make or simplify visual, UX, interaction, brand, or editorial design
decisions. Do not reduce design quality to save code.

Understand the affected flow before choosing a change. Prefer an existing
pattern, the standard library, native platform features, or an installed
dependency. Add only the code that the current requirement needs. Avoid
speculative abstractions, compatibility layers, configuration, and extension
points.

For a bug, find the root cause and inspect relevant callers. Fix a shared cause
when the evidence supports that scope.

## Verification

Use the smallest evidence that proves the result. Prefer an existing relevant
test, focused command, build, type check, linter, temporary probe, or direct
behavior check. Run broader checks when the changed scope, risk, repository
rules, or CI behavior requires them.

Add a persistent test when it protects a likely repeat failure, stable public
contract, non-obvious logic, or high-impact behavior. Static and trivial edits
usually need direct inspection only.

## Boundaries

Do not simplify away security controls, trust-boundary validation, data-loss
protection, required error handling, accessibility, or an explicit requirement.
Match the proof to the impact, uncertainty, and recovery cost.

Keep the handoff short. State the change, the evidence, and any known limit
that affects the user's decision.

Related skills: `vibe-coding` (dev-toolkit) covers broader AI-assisted
development, and `verification-before-completion` (superjawn) covers final
proof before a completion claim.

Credit: Adapted from [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)
under the MIT license.
