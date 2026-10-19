# Cats Effect IO: cleanup-error provenance (originally scala-cats-effect-cleanup-error-provenance)

Evidence: [evidence/scala-cats-effect-cleanup-error-provenance.json](evidence/scala-cats-effect-cleanup-error-provenance.json) (claim `ce-claim-error-provenance`).

## Scope

Use when changing IO's error-combination helpers, finalizer recovery, cancellation sequences or parallel/race error
reporting. Review **two channels**: the failure returned to the caller and secondary failures sent to the runtime
reporter. A correct returned error alone does not prove correct cleanup.

Not a general logging policy, and not a prohibition on immutable domain-error aggregation. Do not prescribe stderr for
all effect implementations. Distinct from cancellation ownership: this case asks which failures remain observable and
whether reusable exceptions are mutated, not how dynamically acquired resources enter an owner map.

## Version and source boundaries

- The original repair is CE1 at `c6d7dd5e8c454baf242ab24487a9dc9aa4b6e8fa`: Scala default 2.12.6, cross builds
  2.11.12 / 2.12.7 / 2.13.0-M5 (evidence `ce-code-build-2019`), Cats 1.5.0, JVM and Scala.js.
- CE2 source at `1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e` independently retains the same `ReleaseRecover` policy and
  IO regression (`ce2-error-recover`, `ce2-error-test`, MUnit-style assertions instead of CE1 ScalaTest syntax), while
  its finalizer synchronization has evolved (`ce2-release-progress`).
- Neither snapshot establishes CE3's current reporter behavior. Re-read modern CE3 before proposing changes.
- PR394's review (alexandru, `ce-polymorphic-errors`) concerns a release function that **throws before producing its
  effect**: "It's undefined only from the point of view of polymorphic code making use of the `Bracket` type class."
  Do not conflate that with an effect that later fails, and do not extrapolate it into "Bracket has no error laws".
  The author revised documentation; an IO regression test is not a law for every effect.

Read the concrete IO implementation and tests, the relevant `Bracket` contract and the call graph of the changed helper.

## Workflow

1. **Classify failure origin.** Failed acquisition, failed use, effectful failed release, an impure release function
   throwing, and failure while canceling a sibling. Record the concrete policy for each rather than imposing an
   invented generic law.
2. **Write the failure matrix.** For successful use/release, use-only failure, release-only failure and simultaneous
   failures, identify returned result, reporter output, finalizer progress and object mutation. At the pinned CE1/CE2
   IO implementation, a simultaneous use/release failure returns the original use throwable and reports the release
   failure separately ([CE1 `IOBracket.ReleaseRecover`](https://github.com/typelevel/cats-effect/blob/c6d7dd5e8c454baf242ab24487a9dc9aa4b6e8fa/core/shared/src/main/scala/cats/effect/internals/IOBracket.scala#L169-L180),
   [CE2 `ReleaseRecover`](https://github.com/typelevel/cats-effect/blob/1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e/core/shared/src/main/scala/cats/effect/internals/IOBracket.scala#L179-L188)).
3. **Trace all helper callers.** PR458's review (alexandru, `ce-error-siblings`: "usage of `composeErrors` needs to be
   reviewed. If there are no other uses of it, we should just delete it") expanded from `IOBracket.ReleaseRecover` to
   `composeErrors` users, cancellation utilities, parallel mapping, racing and JVM/JS implementations; the final patch
   changes all of them. Search definitions and usages before deleting a helper. Fix the semantic class of bug without
   unrelated refactors.
4. **Audit reuse and retention.** If a throwable can be reused, adding suppressed errors during every evaluation
   changes shared observable state and can retain unrelated cleanup failures. Preserve identity and the initial
   suppressed-array contents. Do not silently discard secondary errors as a workaround.
5. **Retain cleanup synchronization.** Error-reporting changes must not reorder registration/removal, bypass the
   release-once guard, or skip later finalizers. CE2 additionally waits for an already-running release through a
   Promise and `IOFromFuture` (`ce2-release-progress`,
   [source](https://github.com/typelevel/cats-effect/blob/1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e/core/shared/src/main/scala/cats/effect/internals/IOBracket.scala#L144-L162));
   do not regress that by copying the older CE1 frame.
6. **Choose a platform-valid observation point.** Use the target runtime's reporter when available. The historical
   tests capture `System.err`, and the CE1 build serializes tests because it is global
   (`parallelExecution in Test := false`, `ce-code-build-serial`; not a recommendation to disable parallelism in
   modern suites). A JVM `UncaughtExceptionHandler` does not validate Scala.js (`ce-error-test-platform`,
   [discussion](https://github.com/typelevel/cats-effect/pull/458#discussion_r244108413)). Restore any global sink
   even if the test fails, and wait for relevant finalizers before ending capture.

## Checks

Preserve: a secondary cleanup error does not replace the promised primary result or disappear; exception identity;
unchanged preexisting suppressed entries; release completion; subsequent finalizer execution. Check the symmetric
branches of racing and parallel evaluation independently.

False positives:

- Immutable aggregation with a documented domain policy is not reusable-Throwable mutation.
- A new exception deliberately owned by an adapter may support suppression under a different contract.
- The historical tests start with empty suppressed arrays; the repeated-use / unchanged-array check is an **inferred
  hardening extension**, not a claim that those tests already covered it.

## Validation

Only run builds with explicit permission in an isolated, matching upstream checkout. Discover `build.sbt`,
`project/build.properties`, `project/plugins.sbt` and test package names before invoking sbt; confirm IDs with
`sbt projects`. At the CE1 revision the explicit projects support:

- `sbt 'lawsJVM/testOnly cats.effect.IOTests'`
- `sbt 'coreJVM/testOnly cats.effect.internals.CancelUtilsTests'`
- `sbt 'lawsJS/testOnly cats.effect.IOTests'`
- `sbt 'coreJS/testOnly cats.effect.internals.CancelUtilsTests'`

The CE2 `lawsJVM`/`lawsJS` projects still contain `cats.effect.IOTests`; use that revision's toolchain, not CE1
dependencies.

Test oracles:

- [CE1 IOTests "bracket signals the error in use and logs the error from release"](https://github.com/typelevel/cats-effect/blob/c6d7dd5e8c454baf242ab24487a9dc9aa4b6e8fa/laws/shared/src/test/scala/cats/effect/IOTests.scala#L677-L691)
  and the [CE2 equivalent](https://github.com/typelevel/cats-effect/blob/1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e/laws/shared/src/test/scala/cats/effect/IOTests.scala#L720-L738)
  assert primary failure, visible secondary error and no suppressed mutations.
- [CancelUtilsTests](https://github.com/typelevel/cats-effect/blob/c6d7dd5e8c454baf242ab24487a9dc9aa4b6e8fa/core/shared/src/test/scala/cats/effect/internals/CancelUtilsTests.scala#L70-L81)
  inspects both channels and empty suppressed lists. The multi-error test checks errors but leaves progress flags
  unasserted; the separate one-error case asserts them. Close that oracle gap rather than claiming the
  multiple-failure test proves progress.
- Add: repeated evaluation with the same primary throwable; a finalizer after multiple failed cleanup actions.
  Verify primary identity, visible secondary failure, unchanged suppressed state and execution of the last finalizer.
  Run supported platforms independently.

No upstream Scala build or regression was executed during authoring.

## Examples

- **Good.** At the pinned IO revision, use fails with `eUse` and release fails with `eRelease`. Recovery reports
  `eRelease` and raises the original `eUse`. A regression observes both channels, asserts the same primary object and
  unchanged suppressed arrays, and includes a later finalizer marker in a cancellation sequence.
- **Broken and correction.** A cleanup refactor calls `eUse.addSuppressed(eRelease)` then returns `eUse`; its test only
  checks `Left(eUse)`. The primary assertion passes while repeated evaluations mutate the shared exception. Correction:
  restore the target IO reporter path without replacing the primary error; update bracket, cancellation, racing and
  parallel siblings; add repeated-use and multi-finalizer-progress assertions.
- **Negative.** A custom `Bracket` implementation intentionally returns an immutable aggregate of domain errors. Do not
  reject it because CE1 IO reports a secondary throwable to stderr; check that effect's laws and public contract. A
  throwing release function needs its own concrete implementation analysis.

## Output

Failure matrix, helper call sites and affected platforms. Each finding: **file:line**, **severity**, **evidence**, and a
**test** oracle covering both channels. Distinguish a confirmed lost/mutated error from a missing assertion. Report
executed commands separately from proposed hardening tests.

## Limitations

Historically grounded in CE1 and independently checked against a CE2 snapshot. No claim about universal throwable
aggregation, security-safe logging, leak magnitude, or measured effectiveness against a baseline agent. Discussion
quotes are attributed to participants, not inferred from their current GitHub association.

## Sources

- [PR458 whole-helper review](https://github.com/typelevel/cats-effect/pull/458#pullrequestreview-188034431)
- [PR458 platform-specific test discussion](https://github.com/typelevel/cats-effect/pull/458#discussion_r244108413)
- [PR394 concrete implementation versus polymorphic behavior](https://github.com/typelevel/cats-effect/pull/394#discussion_r235616800)
- [CE1 build versions](https://github.com/typelevel/cats-effect/blob/c6d7dd5e8c454baf242ab24487a9dc9aa4b6e8fa/build.sbt#L61-L64),
  [CE1 serial tests](https://github.com/typelevel/cats-effect/blob/c6d7dd5e8c454baf242ab24487a9dc9aa4b6e8fa/build.sbt#L104-L109)
