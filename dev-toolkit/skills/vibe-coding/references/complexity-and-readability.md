# Complexity and readability

When to read this: Use this reference for new or heavily edited branching logic, or when the user requests a complexity pass.

## Scope the pass

Inspect the named target first.
If no target is named, inspect only the current change and directly connected code.
Do not turn a complexity pass into a repository-wide refactor.
Do not restructure generated or vendored files.
A no-change result is correct when the current code is clearer than the alternatives.

## Order of priorities

Use this order when two goals conflict:

1. Preserve correctness and required behavior.
2. Match the local style and established patterns.
3. Make control flow and data flow easy to follow.
4. Keep the result easy to verify.
5. Reduce measured or perceived complexity.

Metrics are signals.
They are not the objective.

## Flatten control flow

Use guard clauses for invalid input, authorization failures, empty cases, and errors.
Keep the normal path at the lowest indentation level.
Avoid a final `else` after an earlier branch returns.

Before:

```js
function publish(story) {
  if (story) {
    if (story.isApproved) {
      return save(story);
    }
  }
  return null;
}
```

After:

```js
function publish(story) {
  if (!story) return null;
  if (!story.isApproved) return null;
  return save(story);
}
```

## Watch nesting depth

Most units read best at one or two levels of control-flow nesting.
Depth three needs a clear reason.
A cyclomatic complexity near 10 in one unit is a useful warning point.
Do not turn these anchors into a new automated gate unless the repository already has one.

Declarative indentation is not always control-flow nesting.
Judge conditionals, loops, dispatch, error paths, and template logic.

## Keep functions coherent

Function length alone is not a defect.
A long linear algorithm can be clearer than many tiny functions.
Extract code when the extracted unit has one nameable job.
Keep steps together when they share state and must be read in sequence.

Do not create functions named `helper`, `util`, or `processThing` merely to shorten a file.
Do not move complexity into a caller, configuration file, or hidden global state.

## Name facts and policies

Name a value for the fact it represents.
Use `isEligible`, `hasConsent`, or the local equivalent.
Avoid names that repeat syntax, such as `booleanFlag` or `tempValue`.
Name a complex unit for the policy it implements.
Use a short comment only when the domain reason is not visible in the code.

## Prefer deletion over abstraction

Delete dead branches, unused options, and duplicate paths before adding a pattern.
Use a lookup table or flat dispatch when three or more independent cases already exist.
Add polymorphism, a plug-in layer, or a strategy object only when real variation exists.
Do not add an extension point for a single current case.

## Inspect hidden complexity

Flat code can still be hard to reason about.
Check for:

- Nonlocal mutation.
- Hidden side effects.
- Required call order.
- Implicit state transitions.
- Transaction boundaries.
- Error behavior.
- Concurrent access.
- Performance requirements that callers rely on.

Make data flow and state transitions explicit where practical.

## Measure only when useful

Run the repository's configured complexity check if it has one.
Honor its existing threshold.
Do not add a new metric for a one-time pass.
Use cognitive complexity, cyclomatic complexity, or function length to locate review targets, not to declare quality.
Compare the changed unit before and after.
Then read the code and judge whether the change is easier to understand.

## Final check

- Can you describe the unit's job in one sentence?
- Can you follow the normal path without tracking several nested conditions?
- Did you preserve public interfaces, errors, and side-effect order?
- Did you delete unnecessary logic before adding abstraction?
- Would a teammate recognize this as part of the surrounding code?
- Did the smallest relevant check pass?

## Sources

- Martin Fowler, ["Replace Nested Conditional with Guard Clauses"](https://refactoring.com/catalog/replaceNestedConditionalWithGuardClauses.html).
- Martin Fowler, ["Extract Function"](https://refactoring.com/catalog/extractFunction.html).
- McCabe, [NIST SP 500-235](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication500-235.pdf), on cyclomatic complexity and the threshold of 10.
- SonarSource, ["Cognitive Complexity"](https://www.sonarsource.com/docs/CognitiveComplexity.pdf), on measuring understandability beyond path count.
