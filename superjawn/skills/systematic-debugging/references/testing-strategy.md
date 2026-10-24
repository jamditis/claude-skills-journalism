# Testing strategy

When to read this: Use this reference when choosing, writing, changing, removing, or quarantining tests.

## Choose by proof

Do not choose a test by its label.
Choose it by the fact it proves and the failure it can explain.

Keep a test when both statements are true:

1. The test records a fact that the code cannot tell you by itself.
2. A failure points to a real and specific problem.

## Match the test to the contract

| Need to prove | Useful evidence |
| --- | --- |
| Two systems agree on an API, schema, file format, or stored data | Contract or integration test with real serialization |
| A critical user flow works | Small end-to-end smoke test with deterministic data |
| Logic works across many inputs | Golden examples or property-based tests around pure logic |
| A fixed bug stays fixed | One focused regression test when recurrence or impact justifies it |
| A refactor preserves current behavior | A labeled characterization test created before the refactor |

Use a real database or an official emulator when database behavior is part of the contract.
Fake only at a system boundary, such as a network, process, clock, random source, or filesystem.

## Keep the oracle independent

The expected result must come from a source other than the new code.
Use:

- A specification or accepted requirement.
- A real example with private data removed.
- A recorded response checked against the provider's schema.
- A failure observed before the fix.
- A property or invariant.

Do not run new code and paste its output into the expected file.
That proves only that the code reproduces itself.
A characterization test of existing behavior is the exception.
Label the test and inspect its output before accepting it.

## Tests not to write

Do not add tests that:

- Assert internal function calls or their order when those calls are not the contract.
- Mock modules owned by the same repository.
- Test getters, constants, wiring, or framework behavior.
- Store snapshots that reviewers do not inspect.
- Exist only to increase coverage.
- Repeat an existing test at a different layer without adding evidence.

A call can be part of the contract when the side effect is the behavior, such as sending exactly one notification.

## Protect existing tests

Do not delete, skip, weaken, or change an expected value merely to make a change pass.
Change an existing test only when the requirement changed or the test was wrong.
Record the source of that decision.
List each changed test and its reason in the review handoff.

A new skip, retry, expected failure, or longer timeout needs a documented reason and owner.

## Use the right loop

At the start, find the relevant test command and establish current state.
While editing, run the smallest fast and deterministic set that covers the change.
Before review, run the checks required for the affected area.
Run user-flow tests after changes to those flows, not after every small edit.

## Handle flaky tests

A flaky test passes and fails on the same code.
Do not add sleeps, retries, or larger timeouts to hide the failure.
Check common causes:

- Shared mutable state.
- Fixed ports.
- Clock or time-zone assumptions.
- Test-order dependence.
- Live network calls.
- Resource contention.

Quarantine only after evidence shows a pass and a failure on the same commit.
Use the project's quarantine process.
Keep a linked owner and removal condition.
Without that evidence, keep the failure blocking and report the limit.

## Measure test effectiveness

Coverage shows which code ran.
It does not show whether assertions can detect incorrect behavior.
Mutation testing can provide stronger evidence.
It makes small code changes and checks whether tests fail.

Run mutation testing only when the repository already supports it and the change warrants the cost.
Limit it to changed logic.
Inspect surviving mutants and exclude changes that do not alter behavior.
Treat the result as evidence, not an automatic gate.

## Keep a regression test when it matters

Keep a new regression test when at least one condition applies:

- The failure is likely to recur.
- The bug affects a stable public contract.
- The logic is non-obvious.
- The impact is high.
- The test protects an invariant that other checks do not cover.

For a static text edit or an obvious low-risk fix, direct inspection can be enough.

## Final check

- What fact does this test prove?
- Is its oracle independent of the new code?
- Does it test a contract instead of internal wiring?
- Can a failure identify a specific problem?
- Did you avoid hiding flakiness?
- Does the test provide lasting value?

## Sources

- Kent C. Dodds, ["The Testing Trophy and Testing Classifications"](https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications).
- Martin Fowler, ["On the Diverse And Fantastical Shapes of Testing"](https://martinfowler.com/articles/2021-test-shapes.html).
- Google Testing Blog, ["Just Say No to More End-to-End Tests"](https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html).
- Hora and Robbes, ["Are Coding Agents Generating Over-Mocked Tests?"](https://arxiv.org/abs/2602.00409).
- Petrović et al., ["Practical Mutation Testing at Scale"](https://research.google/pubs/practical-mutation-testing-at-scale-a-view-from-google/).
