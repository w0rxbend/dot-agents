# Cats Effect IO: cleanup-error provenance (originally scala-cats-effect-cleanup-error-provenance)

Evidence: [evidence/scala-cats-effect-cleanup-error-provenance.json](evidence/scala-cats-effect-cleanup-error-provenance.json) (claim `ce-claim-error-provenance`).

## Scope

Use when changing IO error-combination helpers, finalizer recovery, cancellation sequences or parallel/race error
reporting. Review **two channels**: failure returned to caller, secondary failures sent to runtime reporter. Correct
returned error alone does not prove correct cleanup.

Not general logging policy, not ban on immutable domain-error aggregation. Do not prescribe stderr for all effect
implementations. Distinct from cancellation ownership: asks which failures stay observable and whether reusable
exceptions get mutated, not how dynamically acquired resources enter owner map.

## Version and source boundaries

- Original repair: CE1 at `c6d7dd5e8c454baf242ab24487a9dc9aa4b6e8fa`. Scala default 2.12.6, cross builds
  2.11.12 / 2.12.7 / 2.13.0-M5 (evidence `ce-code-build-2019`), Cats 1.5.0, JVM and Scala.js.
- CE2 source at `1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e` independently keeps same `ReleaseRecover` policy and IO
  regression (`ce2-error-recover`, `ce2-error-test`, MUnit-style assertions instead of CE1 ScalaTest syntax). Its
  finalizer synchronization evolved (`ce2-release-progress`).
- Neither snapshot establishes CE3 current reporter behavior. Re-read modern CE3 before proposing changes.
- PR394 review (alexandru, `ce-polymorphic-errors`) covers release function that **throws before producing its
  effect**: "It's undefined only from the point of view of polymorphic code making use of the `Bracket` type class."
  Do not conflate with effect that fails later. Do not extrapolate to "Bracket has no error laws". Author revised
  documentation; IO regression test is not law for every effect.

Read IO implementation and tests, relevant `Bracket` contract, call graph of changed helper.

## Workflow

1. **Classify failure origin.** Failed acquisition, failed use, effectful failed release, impure release function
   throwing, failure while canceling sibling. Record concrete policy per origin; no invented generic law.
2. **Write the failure matrix.** Cases: successful use/release, use-only failure, release-only failure, simultaneous
   failures. For each, identify returned result, reporter output, finalizer progress, object mutation. Pinned CE1/CE2
   IO: simultaneous use/release failure returns original use throwable, reports release failure
   separately ([CE1 `IOBracket.ReleaseRecover`](https://github.com/typelevel/cats-effect/blob/c6d7dd5e8c454baf242ab24487a9dc9aa4b6e8fa/core/shared/src/main/scala/cats/effect/internals/IOBracket.scala#L169-L180),
   [CE2 `ReleaseRecover`](https://github.com/typelevel/cats-effect/blob/1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e/core/shared/src/main/scala/cats/effect/internals/IOBracket.scala#L179-L188)).
3. **Trace all helper callers.** PR458 review (alexandru, `ce-error-siblings`: "usage of `composeErrors` needs to be
   reviewed. If there are no other uses of it, we should just delete it") expanded scope from `IOBracket.ReleaseRecover`
   to `composeErrors` users, cancellation utilities, parallel mapping, racing, JVM/JS implementations. Final patch
   changes all. Search definitions and usages before deleting helper. Fix semantic bug class; no unrelated refactors.
4. **Audit reuse and retention.** If throwable is reusable, adding suppressed errors per evaluation mutates shared
   observable state and can retain unrelated cleanup failures. Preserve identity and initial suppressed-array
   contents. Do not silently discard secondary errors as workaround.
5. **Retain cleanup synchronization.** Error-reporting changes must not reorder registration/removal, bypass
   release-once guard, or skip later finalizers. CE2 also waits for already-running release via Promise and
   `IOFromFuture` (`ce2-release-progress`,
   [source](https://github.com/typelevel/cats-effect/blob/1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e/core/shared/src/main/scala/cats/effect/internals/IOBracket.scala#L144-L162));
   do not regress that by copying older CE1 frame.
6. **Choose a platform-valid observation point.** Use target runtime reporter when available. Historical tests
   capture `System.err`; CE1 build serializes tests because that sink is global (`parallelExecution in Test := false`,
   `ce-code-build-serial`; not advice to disable parallelism in modern suites). JVM `UncaughtExceptionHandler` does not
   validate Scala.js (`ce-error-test-platform`,
   [discussion](https://github.com/typelevel/cats-effect/pull/458#discussion_r244108413)). Restore any global sink even
   on test failure. Wait for relevant finalizers before ending capture.

## Checks

Preserve: secondary cleanup error neither replaces promised primary result nor disappears; exception identity;
unchanged preexisting suppressed entries; release completion; later finalizer execution. Check symmetric racing and
parallel branches independently.

False positives:

- Immutable aggregation with documented domain policy is not reusable-Throwable mutation.
- New exception deliberately owned by adapter may allow suppression under different contract.
- Historical tests start with empty suppressed arrays. Repeated-use / unchanged-array check is **inferred hardening
  extension**, not claim those tests already covered it.

## Validation

Run builds only with explicit permission, in isolated matching upstream checkout. Before invoking sbt, discover
`build.sbt`, `project/build.properties`, `project/plugins.sbt` and test package names; confirm IDs with
`sbt projects`. At CE1 revision, explicit projects support:

- `sbt 'lawsJVM/testOnly cats.effect.IOTests'`
- `sbt 'coreJVM/testOnly cats.effect.internals.CancelUtilsTests'`
- `sbt 'lawsJS/testOnly cats.effect.IOTests'`
- `sbt 'coreJS/testOnly cats.effect.internals.CancelUtilsTests'`

CE2 `lawsJVM`/`lawsJS` still contain `cats.effect.IOTests`; use that revision's toolchain, not CE1 dependencies.

Test oracles:

- [CE1 IOTests "bracket signals the error in use and logs the error from release"](https://github.com/typelevel/cats-effect/blob/c6d7dd5e8c454baf242ab24487a9dc9aa4b6e8fa/laws/shared/src/test/scala/cats/effect/IOTests.scala#L677-L691)
  and [CE2 equivalent](https://github.com/typelevel/cats-effect/blob/1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e/laws/shared/src/test/scala/cats/effect/IOTests.scala#L720-L738)
  assert primary failure, visible secondary error, no suppressed mutations.
- [CancelUtilsTests](https://github.com/typelevel/cats-effect/blob/c6d7dd5e8c454baf242ab24487a9dc9aa4b6e8fa/core/shared/src/test/scala/cats/effect/internals/CancelUtilsTests.scala#L70-L81)
  inspects both channels and empty suppressed lists. Multi-error test checks errors, leaves progress flags
  unasserted; separate one-error case asserts them. Close that oracle gap; do not claim multiple-failure test proves
  progress.
- Add: repeated evaluation with same primary throwable; finalizer after multiple failed cleanup actions. Verify
  primary identity, visible secondary failure, unchanged suppressed state, last finalizer execution. Run each supported
  platform independently.

No upstream Scala build or regression ran during authoring.

## Examples

- **Good.** Pinned IO revision: use fails with `eUse`, release fails with `eRelease`. Recovery reports `eRelease`,
  raises original `eUse`. Regression observes both channels, asserts same primary object and unchanged suppressed
  arrays, includes later finalizer marker in cancellation sequence.
- **Broken and correction.** Cleanup refactor calls `eUse.addSuppressed(eRelease)` then returns `eUse`; test only
  checks `Left(eUse)`. Primary assertion passes while repeated evaluations mutate shared exception. Correction: restore
  target IO reporter path without replacing primary error; update bracket, cancellation, racing and parallel siblings;
  add repeated-use and multi-finalizer-progress assertions.
- **Negative.** Custom `Bracket` implementation intentionally returns immutable aggregate of domain errors. Do not
  reject it because CE1 IO reports secondary throwable to stderr; check that effect's laws and public contract.
  Throwing release function needs own concrete implementation analysis.

## Output

Failure matrix, helper call sites, affected platforms. Each finding: **file:line**, **severity**, **evidence**,
**test** oracle covering both channels. Separate confirmed lost/mutated error from missing assertion. Report executed
commands apart from proposed hardening tests.

## Limitations

Grounded in CE1, independently checked against CE2 snapshot. No claim about universal throwable aggregation,
security-safe logging, leak magnitude, or measured effectiveness versus baseline agent. Discussion quotes attributed to
participants, not inferred from current GitHub association.

## Sources

- [PR458 whole-helper review](https://github.com/typelevel/cats-effect/pull/458#pullrequestreview-188034431)
- [PR394 concrete implementation versus polymorphic behavior](https://github.com/typelevel/cats-effect/pull/394#discussion_r235616800)
- [CE1 build versions](https://github.com/typelevel/cats-effect/blob/c6d7dd5e8c454baf242ab24487a9dc9aa4b6e8fa/build.sbt#L61-L64),
  [CE1 serial tests](https://github.com/typelevel/cats-effect/blob/c6d7dd5e8c454baf242ab24487a9dc9aa4b6e8fa/build.sbt#L104-L109)
