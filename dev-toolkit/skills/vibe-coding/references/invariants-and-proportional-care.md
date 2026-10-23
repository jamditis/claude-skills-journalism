# Invariants and proportional care

When to read this: Use this reference when a change affects state, trust boundaries, error recovery, or a reported bug.

## Apply care in proportion to risk

Use the smallest action that preserves the relevant safeguard.
A one-line text change does not need an architecture review.
A change to stored data, authentication, publication, or recovery needs stronger evidence.
Do not use `temporary`, `internal`, or `one-time` as a reason to skip a real risk.

Scale the work by:

- Impact if the change is wrong.
- Uncertainty about the affected path.
- Cost of recovery.
- Number of consumers.
- Sensitivity of the data or permission boundary.

## State the invariant

An invariant is a condition that must remain true across every valid state transition.
Write the invariant before you add defensive branches.
Put enforcement at the earliest boundary that owns the state.

Examples:

- Every published record has a stable source identifier.
- A completed payment cannot return to pending.
- An unauthenticated request cannot reach private data.
- A queue item is either available or leased, never both.

## Make invalid state hard to create

Prefer types, constructors, parsers, schema constraints, and explicit state machines.
Reject invalid input before it enters stored or shared state.
Use a tolerant reader only when compatibility requirements make invalid legacy state unavoidable.
Keep that compatibility path explicit and bounded.

Before adding a fallback, ask:

1. Where did the invalid state enter?
2. Which component owns that boundary?
3. Can the boundary reject or normalize it once?
4. Must existing invalid records still be read?
5. How will the fallback be removed?

## Fix the shared source

When several consumers need the same workaround, inspect the producer or shared component.
Fix the source when you own it and the evidence supports the change.
If you do not own it, report the source defect and bound the local workaround.
Do not silently duplicate the workaround across consumers.

## Treat generated claims as hypotheses

An automated diagnosis, issue summary, or review finding is not evidence by itself.
Verify it against the code, data path, and actual behavior.
Lead issue reports with observed facts.
Put speculative causes in a labeled section or follow-up comment.

Use this report shape:

```text
Action: <what ran>
Expected: <required result>
Actual: <observed result>
Evidence: <error, log, or artifact>
Hypothesis: <optional, clearly labeled>
```

## Establish failure before fixing

For a bug, establish the failure with the cheapest faithful evidence.
Use an existing test, a focused command, a log, or a new failing test.
Fix the cause.
Run the same evidence again to prove the fix.

Keep a new regression test only when it protects a likely repeat failure, an important contract, non-obvious logic, or high-impact behavior.
Use the superjawn `systematic-debugging` skill, if installed, when the cause is not already established.

## Sweep the verified bug class

A confirmed defect can reveal sibling defects in the same changed scope.
Search the affected path for the same pattern.
Verify each candidate before changing it.
Stop at clear ownership and scope boundaries.
Prefer one invariant that prevents the class over many local patches.

## Protect the important boundary

Do not simplify away:

- Authentication or authorization checks.
- Data-loss protection.
- Input validation at trust boundaries.
- Required error handling.
- Accessibility requirements.
- Transaction and concurrency controls.
- Explicit user or project constraints.

Complexity that enforces a real boundary may be necessary.
Make its purpose visible instead of deleting it to improve a score.

## Final check

- What invariant does this change preserve?
- Is enforcement at the boundary that owns the state?
- Did you verify the reported cause from source and behavior?
- Did you fix the shared cause instead of one symptom?
- Are the checks proportional to impact and recovery cost?
- Did you keep required safeguards intact?

## Sources

- Yaron Minsky, ["Effective ML Revisited"](https://blog.janestreet.com/effective-ml-revisited/), on making invalid states unrepresentable.
- Alexis King, ["Parse, don't validate"](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/), on converting input into trusted structure at the boundary.
- IETF, ["Maintaining Robust Protocols"](https://datatracker.ietf.org/doc/rfc9413/), on protocol decay caused by tolerant receivers.
