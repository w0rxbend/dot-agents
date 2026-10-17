---
name: scala-castor-platform-mixin-dispatch-accounting
description: Use when refactoring Castor Context platform mixins or reviewing their inherited JVM/JS/Native API boundary. Preserve shared actor dispatch accounting, distinguish source from binary compatibility, and validate reachable async behavior rather than a smoke-test exit.
license: MIT
---

# Refactor Castor platform mixins without changing dispatch contracts

## When to Use

Use for changes that move Castor `Context`, its companion, or `Context.Impl` members between shared and platform roots; repair JS/Native linking of actor entry points; or claim a formerly JVM-only scheduling API is portable. Review the inherited public surface and the unchanged shared dispatch engine together.

## When Not to Use

Do not use for generic Mill layout cleanup, ordinary actor application design, or unrelated backpressure algorithms. Generic build and compatibility procedures belong to the existing Mill and Scala library skills. A JVM-only timer change without a changed platform boundary does not justify moving the timer into shared code. Do not migrate this Future/ExecutionContext library to Ox, Cats Effect or ZIO.

## Prerequisites

Read the target revision's build, launcher/version pin, source roots, public `Actor` and `Context`, platform traits, and tests. Record Scala, Mill, JDK, Scala.js/Native, sourcecode, uTest, and compatibility-baseline versions. Do not use calendar year as a platform selector.

Historical anchors: PR #12 used Scala 2.11.12/2.12.13/2.13.4 and 3.0.0, JS 0.6.33/1.5.1 (Scala 3 only on JS 1.x), and Native 0.4.0 on Scala 2. The 2022 snapshot uses Mill 0.10.5, JS 1.10.1 and Native 0.4.5; the 2024 build uses Mill 0.12.0 and one-axis cross modules. See [version and validation details](references/validation.md). Preserve supported syntax and eager scheduling, not contemporary application-style defaults.

## Workflow

1. **Write a capability table before moving files.** For each target, list the owners and signatures of `scheduleMsg`, `scheduler`, thread-pool factories/classes, `Simple.global`, `future`, and test quiescence. Include inherited members: `private[castor]` on a mixin does not make its inherited public methods ABI-irrelevant.
2. **Trace the actual linkable entry point.** Follow `Actor.sendAsync` through `BaseActor`, implicit `Context`, `Simple.executionContext`, and the platform adapter. Inspect public signatures as well as implementation references. PR #12's author reported that retaining JVM-type methods in public traits prevented JS linking. Reproduce that constraint on the chosen versions; do not infer failure from an unused import.
3. **Move only platform-dependent members.** Keep shared token creation, Future dispatch and actor queue handling in one implementation. Ensure the selected roots define exactly one compatible `castor.platform.Context`, `ContextImpl`, companion mixin and adapter. PR #12 changed a duplicated implementation into this boundary; it did not ship the suggested portable duration overload.
4. **Audit what remains shared.** In the 2022 and 2024 sources, `TestBase.waitForInactivity` still accepts `Option[java.time.Duration]` and uses blocking `Await`. List it as a separate unproved portable capability. Do not claim the entire Context API is portable because `sendAsync` links. Avoid this helper in shared async tests.
5. **Preserve dispatch accounting while extracting.** Trace message tokens separately from executor-runnable and `Context.future` tokens. Preserve `SimpleActor`'s per-message `finally`, `BatchActor`'s completion for every batch token, and BaseActor's synchronized queue/`scheduled` handoff. For normal handlers, accepting executors and nonthrowing hooks, compare delivery, completion and quiescence before/after. Treat rejection or throwing instrumentation as separate fault boundaries, not already-proven behavior.
6. **Make compatibility and support claims independently.** Compile old JVM source calls, including `java.time.Duration`, against the candidate; separately run an unchanged old-compiled consumer against it. Inspect inherited class/member changes and MiMa exclusions. PR #12's final revision explicitly traded binary compatibility for shared code and discussed 0.2.0. Its initial patch-release description is not the final disposition. A Native method throwing `NotImplementedError` is not implemented support; an unmerged proposal is not a release.

## Review and Refactoring Checks

Preserve these testable invariants within the stated executor/hook assumptions:

- Each scheduled message token completes once, including a handler that throws and is reported; runnable tokens are accounted independently.
- Messages queued during a batch are picked up by the next drain; becoming idle allows a later send to schedule again. Do not replace the synchronization protocol as incidental cleanup.
- `sendAsync` success sends a value; failed Futures report failure without inventing a delivered message. A pending external Future is not necessarily tracked by Castor before its callback runs: temporary inactivity is not proof of delivery.
- The JVM retains its advertised duration/thread-pool calls unless a deliberate migration is approved; other platforms expose only capabilities actually implemented and linked.

False positives: a JVM type in a JVM-only root is legitimate; an empty JS/Native scheduling mixin can deliberately omit an unavailable capability. The shared smoke test is useful for reachability but insufficient for delivery. Neither the release approval nor modern Native linking establishes a universal historical design preference.

## Validation

In an authorized disposable target checkout, inspect its pinned launcher/build before execution. The actual 2022 CI commands are `./mill -i all __.publishArtifacts __.test` and, separately with historical tags available, `./mill -i __.mimaReportBinaryIssues`. `publishArtifacts` prepares artifacts; do not invoke publishing tasks or supply credentials. These commands are historical discoveries, not execution results from this skill's research.

Resolve real module/source/test tasks from that checkout before narrowing selectors. Verify nonempty shared/platform sources and recorded test discovery; do not transplant the old two-axis selectors into the 2024 single-axis build. Report every skipped/no-baseline compatibility cell (2022 Scala 3; 2024 Native in the examined snapshots).

Add asserted tests: drain a controlled executor with a finite step budget to check delivery, failure, reentrant sends, and zero outstanding tokens; also return an assertion-bearing Future from a real-platform async test rather than returning Unit immediately. Run both on intended targets. Keep JVM timer integration separate. Follow the concrete oracles and old-consumer protocol in [validation.md](references/validation.md); a source fixture alone proves no compilation, ABI result or race freedom.

## Examples

### Good

Extract JVM `scheduleMsg(java.time.Duration)` and thread-pool machinery into the JVM platform mixins, leave token/Future/queue behavior shared, and select empty scheduling mixins on JS/Native. Exercise `sendAsync` there with a returned delivery assertion, then run an old JVM caller without recompiling it. Report a binary break explicitly if observed. This follows PR #12's final direction without falsely claiming portable timers or that its historical smoke test already asserted delivery.

### Broken and Correction

A refactor copies Context three times, adds a public JVM-duration method to the shared trait, then cites `foo.sendAsync(Future(()))` returning Unit as proof of full portability and delivery. Correction: isolate platform signatures, verify the selected mixins and actual linker reachability, and preserve the shared actor engine. Replace the test's empty handler with a delivery assertion and observe token completion after a bounded drain. Retain the separate `waitForInactivity` portability warning. If the move changes inherited ABI, test the old binary and document the release consequence instead of relying on source compilation.

### Negative

A patch changes only a JVM timer implementation while keeping its `java.time.Duration` signature, source roots and shared actor engine unchanged. Do not report a cross-platform defect merely because JS lacks that timer. Review the actual JVM timer behavior normally; do not demand new effects, immutability rewrites or synthetic Native stubs to satisfy this workflow.

## Output Contract

Produce a target/version/capability table and bounded findings with **file:line**, **severity**, violated invariant, historical **evidence** ID or citation, proposed correction, and a concrete **test** with expected observation. Separate source observation, reviewer statement and inference. Record source-compatibility, old-binary, link, runtime-delivery and quiescence results separately as passed/failed/not run/unsupported. State which baselines or targets were skipped and what remains unproved; do not call a source-only review a successful build.

## Limitations

This is one small-library design episode, supplemented by build repairs and later snapshots, not a repeated multi-year maintainer policy. The accounting procedure is source-derived inference. There is no historical proof here of cancellation, rejection safety, bounded backpressure or arbitrary concurrent-race freedom. PR #15's closure rationale is unknown. Current platform support must be rechecked; this research did not execute upstream builds or compile the proposed tests.

## Sources

- [Evidence and claim mapping](references/evidence.json): platform boundary, compatibility disposition, build dispatch, timer-proposal distinction and accounting preservation.
- [PR #12 duplication concern](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919783061), [linker constraint and revised tradeoff](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919928186), and [release decision](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919974891). Attribute only each author's own text, not forwarded email.
- [Shared actor engine](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/castor/src/Actors.scala) and [shared smoke test](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/castor/test/src/ActorsTest.scala).
