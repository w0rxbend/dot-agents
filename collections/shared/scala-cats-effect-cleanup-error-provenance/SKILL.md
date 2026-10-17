---
name: scala-cats-effect-cleanup-error-provenance
description: Use when hardening Cats Effect IO cleanup-error handling that combines use, release, cancellation, or parallel failures and may mutate or hide exceptions.
license: MIT
---

# Preserve cleanup-error provenance

## When to Use

Use when changing IO's error-combination helpers, finalizer recovery, cancellation sequences or parallel/race error reporting. Review **two channels**: the failure returned to the caller and secondary failures sent to the runtime reporter. A correct returned error alone does not prove correct cleanup.

## When Not to Use

Do not use as a general logging policy or a prohibition on immutable domain-error aggregation. Do not prescribe stderr for all effect implementations. This is distinct from cancellation ownership: it investigates which failures remain observable and whether reusable exceptions are mutated, not how dynamically acquired resources enter an owner map.

## Prerequisites

Pin the implementation, Scala versions, effect version and platforms before applying a historical expectation. The original repair is CE1 at `c6d7dd5e8c454baf242ab24487a9dc9aa4b6e8fa`: Scala 2.11/2.12/2.13 milestone cross-builds, Cats 1.5.0 and JVM/Scala.js. CE2 source at `1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e` independently retains the same `ReleaseRecover` policy and IO regression, while its finalizer synchronization has evolved. Neither snapshot establishes CE3's current reporter behavior.

Read the concrete IO implementation and tests, the relevant `Bracket` contract and the call graph of the changed helper. PR394's review specifically concerns a release function that throws before producing its effect. Do not conflate that case with an effect that later fails, or extrapolate the comment into a claim that Bracket has no error laws.

## Workflow

1. **Classify failure origin.** Distinguish failed acquisition, failed use, effectful failed release, an impure release function throwing, and failure while canceling a sibling. Record the concrete policy for each rather than imposing an invented generic law.
2. **Write the failure matrix.** For successful use/release, use-only failure, release-only failure and simultaneous failures, identify returned result, reporter output, finalizer progress and object mutation. At the pinned CE1/CE2 IO implementation, a simultaneous use/release failure returns the original use throwable and reports the release failure separately.
3. **Trace all helper callers.** PR458's review expanded from `IOBracket.ReleaseRecover` to `composeErrors` users, cancellation utilities, parallel mapping, racing and JVM/JS implementations. Search definitions and usages before deleting a helper. Fix the semantic class of bug without unrelated refactors.
4. **Audit reuse and retention.** If a throwable can be reused, adding suppressed errors during every evaluation changes shared observable state and can retain unrelated cleanup failures. Preserve identity and the initial suppressed-array contents. Do not silently discard secondary errors as a workaround.
5. **Retain cleanup synchronization.** Error reporting changes must not reorder registration/removal, bypass the release-once guard, or skip later finalizers. The CE2 implementation additionally waits for an already-running release through a promise; do not regress that behavior by copying the older CE1 frame.
6. **Choose a platform-valid observation point.** Use the target runtime's reporter when available. The historical tests capture `System.err`, and their build serializes tests because it is global. A JVM `UncaughtExceptionHandler` does not validate Scala.js. Restore any global sink even if the test fails, and wait for relevant finalizers before ending capture.

## Review and Refactoring Checks

Preserve the invariant that a secondary cleanup error does not replace the promised primary result or disappear. Preserve exception identity, unchanged preexisting suppressed entries, release completion and subsequent finalizer execution. Check the symmetric branches of racing and parallel evaluation independently.

False positives: immutable aggregation with a documented domain policy is not reusable-Throwable mutation. A new exception deliberately owned by an adapter may support suppression under a different contract. The historical tests start with empty suppressed arrays; the stronger repeated-use/unchanged-array check here is an inferred hardening extension, not a claim that those tests already covered it.

## Validation

Only run builds with explicit permission in an isolated, matching upstream checkout. Discover `build.sbt`, `project/build.properties`, `project/plugins.sbt` and test package names before invoking sbt; then confirm IDs with `sbt projects`. At the CE1 revision the explicit projects support:

- `sbt 'lawsJVM/testOnly cats.effect.IOTests'`
- `sbt 'coreJVM/testOnly cats.effect.internals.CancelUtilsTests'`
- `sbt 'lawsJS/testOnly cats.effect.IOTests'`
- `sbt 'coreJS/testOnly cats.effect.internals.CancelUtilsTests'`

The CE2 `lawsJVM`/`lawsJS` projects still contain `cats.effect.IOTests`; use that revision's toolchain, not CE1 dependencies. Add repeated evaluation with the same primary throwable, plus a finalizer after multiple failed cleanup actions. The old multi-error CancelUtils test checks errors but leaves progress flags unasserted; the separate one-error case asserts them. Close that oracle gap rather than claiming the multiple-failure test proves progress.

Verify primary identity, visible secondary failure, unchanged suppressed state and execution of the last finalizer. Run supported platforms independently. No upstream Scala build or regression was executed during authoring.

## Examples

### Good

At the pinned IO revision, use fails with `eUse` and release fails with `eRelease`. Recovery reports `eRelease` and raises the original `eUse`. A regression observes both channels, asserts the same primary object and unchanged suppressed arrays, and includes a later finalizer marker in a cancellation sequence.

### Broken and Correction

A cleanup refactor calls `eUse.addSuppressed(eRelease)` then returns `eUse`; its test only checks `Left(eUse)`. The primary assertion passes while repeated evaluations mutate the shared exception. Correction: restore the target IO reporter path without replacing the primary error; update bracket, cancellation, racing and parallel siblings. Add repeated-use and multi-finalizer-progress assertions, not merely another returned-error check.

### Negative

A custom `Bracket` implementation intentionally returns an immutable aggregate of domain errors. Do not reject it simply because CE1 IO reports a secondary throwable to stderr. Check that effect's laws and public contract. Likewise, a throwing release function needs its own concrete implementation analysis, not an assertion that every effect handles it identically.

## Output Contract

Report the failure matrix, helper call sites and affected platforms. Each finding includes **file:line**, **severity**, **evidence**, and a **test** oracle covering both channels. Distinguish a confirmed lost/mutated error from a missing assertion. Report executed commands and results separately from proposed hardening tests.

## Limitations

The procedure is historically grounded in CE1 and independently checked against a CE2 snapshot. Modern CE3 reporting must be re-read before proposing changes. No claim is made about universal throwable aggregation, security-safe logging, leak magnitude, or effectiveness measured against a baseline agent.

## Sources

- [PR458 whole-helper review](https://github.com/typelevel/cats-effect/pull/458#pullrequestreview-188034431) and [platform-specific test discussion](https://github.com/typelevel/cats-effect/pull/458#discussion_r244108413).
- [PR394 concrete implementation versus polymorphic behavior](https://github.com/typelevel/cats-effect/pull/394#discussion_r235616800).
- [Pinned source, tests, version evidence and claim boundaries](references/evidence.json). Discussion quotes are attributed to participants, not inferred from their current GitHub association.
