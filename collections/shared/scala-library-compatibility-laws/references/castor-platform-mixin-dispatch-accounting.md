# Castor: platform mixins across JVM/JS/Native without changing dispatch contracts

Library: com-lihaoyi/castor (Future/ExecutionContext actors; Mill). Originally `scala-castor-platform-mixin-dispatch-accounting`; its `references/validation.md` is folded in below. Evidence ledger: [evidence/scala-castor-platform-mixin-dispatch-accounting.json](evidence/scala-castor-platform-mixin-dispatch-accounting.json) (claims `castor-claim-platform-boundary`, `castor-claim-compatibility-disposition`, `castor-claim-build-dispatch`, `castor-claim-portable-timer-proposals`, `castor-claim-accounting-invariant`).

## Scope

Use for changes that move Castor `Context`, its companion, or `Context.Impl` members between shared and platform roots; repair JS/Native linking of actor entry points; or claim a formerly JVM-only scheduling API is portable. Review the inherited public surface and the unchanged shared dispatch engine together.

Not for: generic Mill layout cleanup, ordinary actor application design, or unrelated backpressure algorithms (generic build procedures belong to the Mill skills). A JVM-only timer change without a changed platform boundary does not justify moving the timer into shared code. Do not migrate this Future/ExecutionContext library to Ox, Cats Effect or ZIO.

## Version map

Read the target revision's build, launcher/version pin, source roots, public `Actor` and `Context`, platform traits, and tests. Record Scala, Mill, JDK, Scala.js/Native, sourcecode, uTest, and compatibility-baseline versions. Do not use calendar year as a platform selector.

| Anchor | Language/platform/testing boundary |
| --- | --- |
| PR #3, `6665317383b0fe1c75a0a087d1e5cc65cefdf09b` (2020-03-05) | JVM/JS Scala 2.12.10 and 2.13.1; Native Scala 2.11.12 with Native 0.3.9/0.4.0-M2. JS 0.6.32/1.0.0. Sourcecode 0.2.1, uTest 0.7.4. Fixes source roots and platform test inheritance; explicit Runnable/Callable supports the Scala 2.11 floor. |
| PR #12 final head, `6fa845bae0e852d57f57b49a450396583c3494bc` (2021-09-15) | Scala 2.11.12/2.12.13/2.13.4/3.0.0; JS 0.6.33/1.5.1 with Scala 3 only on JS 1.x; Native 0.4.0 on Scala 2 only. Sourcecode 0.2.7, uTest 0.7.10, MiMa plugin 0.0.4 built for Mill 0.9. No exact launcher pin is inferred from that plugin suffix. |
| `ae2ba2fe72c930999251d04aaef57cbef808f89b` (2022-07-09) | Mill 0.10.5; Scala 2.11.12/2.12.16/2.13.8/3.1.3; JS 1.10.1; Native 0.4.5; sourcecode 0.2.8; uTest 0.8.0. CI JDK 8/17. Scala 3 MiMa previous artifacts explicitly empty. |
| `189e2c869be8f750c94802c5a2ea7b65a03ee821` (2024-10-24) | Mill 0.12.0; build.mill/package build; Scala 2.12.19/2.13.13/3.3.3; JS 1.16.0; Native 0.5.4; sourcecode 0.4.1; uTest 0.8.3. One Scala-version cross axis. CI JDK 11/17 is not an established published bytecode floor. Native MiMa previous artifacts empty pending first 0.5 release. |

No Cats Effect, ZIO or Ox runtime is used in these builds. Preserve Castor's eager Future/ExecutionContext design. A by-name argument to `Context.future` executes later on the executor; it does not turn the returned Future into a reusable lazy effect.

## Workflow

1. **Write a capability table before moving files.** For each target, list the owners and signatures of `scheduleMsg`, `scheduler`, thread-pool factories/classes, `Simple.global`, `future`, and test quiescence. Include inherited members: `private[castor]` on a mixin does not make its inherited public methods ABI-irrelevant.
2. **Trace the actual linkable entry point.** Follow `Actor.sendAsync` through `BaseActor`, implicit `Context`, `Simple.executionContext`, and the platform adapter. Inspect public signatures as well as implementation references. PR #12's author reported that retaining `java.time`/`java.util.concurrent` methods in public traits made the Scala.js linker complain (while stating Scala Native linked) ([comment](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919928186)). Reproduce that constraint on the chosen versions; do not infer failure from an unused import.
3. **Move only platform-dependent members.** Keep shared token creation, Future dispatch and actor queue handling in one implementation. Ensure the selected roots define exactly one compatible `castor.platform.Context`, `ContextImpl`, companion mixin and adapter. PR #12 changed a duplicated implementation into this boundary ([JVM mixin](https://github.com/com-lihaoyi/castor/blob/6fa845bae0e852d57f57b49a450396583c3494bc/castor/src-jvm/castor/platform/Context.scala), [empty JS/Native mixin](https://github.com/com-lihaoyi/castor/blob/6fa845bae0e852d57f57b49a450396583c3494bc/castor/src-js-native/Context.scala)); it did not ship the reviewer-suggested portable `FiniteDuration` overload ([proposal](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919857735)).
4. **Audit what remains shared.** In the 2022 and 2024 sources, `TestBase.waitForInactivity` still accepts `Option[java.time.Duration]` and uses blocking `Await` ([Context.scala L121-L128](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/castor/src/Context.scala#L121-L128)). List it as a separate unproved portable capability. Do not claim the entire Context API is portable because `sendAsync` links. Avoid this helper in shared async tests.
5. **Preserve dispatch accounting while extracting.** Trace message tokens separately from executor-runnable and `Context.future` tokens. Preserve `SimpleActor`'s per-message `finally`, `BatchActor`'s completion for every batch token, and BaseActor's synchronized queue/`scheduled` handoff ([Actors.scala](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/castor/src/Actors.scala)). For normal handlers, accepting executors and nonthrowing hooks, compare delivery, completion and quiescence before/after. Treat rejection or throwing instrumentation as separate fault boundaries, not already-proven behavior.
6. **Make compatibility and support claims independently.** Compile old JVM source calls, including `java.time.Duration`, against the candidate; separately run an unchanged old-compiled consumer against it. Inspect inherited class/member changes and MiMa exclusions. PR #12's final revision explicitly traded binary compatibility for shared code (commit [02c1c6f](https://github.com/com-lihaoyi/castor/commit/02c1c6f54e230ebf73dc86429cf814fd8f397d89): "NOT binary compatible, but is source compatible") and the reviewer agreed to tag 0.2.0 ([comment](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919974891)). Its initial patch-release description is not the final disposition. A Native method throwing `NotImplementedError` (unmerged PR #15, [ContextImpl.scala](https://github.com/com-lihaoyi/castor/blob/85ac5ae0b4fc3eaf185cefd56a00c2d5896625e0/castor/src-native/ContextImpl.scala)) is not implemented support; that PR's replacement of `java.time.Duration` with `scala.concurrent.duration.Duration` ([JVM Context](https://github.com/com-lihaoyi/castor/blob/85ac5ae0b4fc3eaf185cefd56a00c2d5896625e0/castor/src-jvm/castor/platform/Context.scala)) is not the additive overload discussed earlier; an unmerged proposal is not a release. PR #15's closure rationale is unknown.

## Checks

Testable invariants within the stated executor/hook assumptions:

- Each scheduled message token completes once, including a handler that throws and is reported; runnable tokens are accounted independently.
- Messages queued during a batch are picked up by the next drain; becoming idle allows a later send to schedule again. Do not replace the synchronization protocol as incidental cleanup.
- `sendAsync` success sends a value; failed Futures report failure without inventing a delivered message. A pending external Future is not necessarily tracked by Castor before its callback runs ([Actors.scala L23-L29](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/castor/src/Actors.scala#L23-L29)): temporary inactivity is not proof of delivery.
- The JVM retains its advertised duration/thread-pool calls unless a deliberate migration is approved; other platforms expose only capabilities actually implemented and linked.

False positives: a JVM type in a JVM-only root is legitimate; an empty JS/Native scheduling mixin can deliberately omit an unavailable capability. The shared smoke test is useful for reachability but insufficient for delivery. Neither the release approval nor modern Native linking establishes a universal historical design preference.

## Reachability audit (2022 shared `Context.scala`)

- Lines 12, 40, 72 and 132 inherit platform Context, companion, Simple companion and implementation members. Check signatures inherited through all four, not just the public trait body.
- Lines 121-128 retain `waitForInactivity(timeout: Option[java.time.Duration])` with `Await.result`. Its default-argument path and calling conventions are separate from `sendAsync` linking. Do not delete or relocate it without consumer analysis; do not invoke it as a portable event-loop test helper.
- Line 3 has a leftover JVM import. An unused import is not equivalent to a reachable JVM-only method. Check compiler/linker output before diagnosing it.
- `ActorsTest.scala:16-23` ([file](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/castor/test/src/ActorsTest.scala)) does call the async entry point, but returns Unit and has an empty handler. It cannot prove delivery, exactly-once processing or quiescence.
- The JVM debounce test ([JvmActorsTest.scala](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/castor/test/src-jvm/JvmActorsTest.scala)) consumes the retained `java.time` API; keep JVM timer integration separate.

For a new target, produce one row per entry point with signature types, implementation owner, source-root resolution, consumer that reaches it, link status and observed behavior. An intentionally omitted `scheduleMsg` is different from a method present but throwing.

## Controlled dispatch oracle

Use a manually drained ExecutionContext that queues Runnable values and fails after a finite number of steps. Keep the recorder separate from `TestBase` so the test does not import its blocking helper. Track token identity and category through all three `reportSchedule` overloads and `reportComplete`. Assert duplicate or unknown completion as well as missing completion.

1. Schedule `actor.sendAsync(context.future(7))`; before draining, the body and handler have not run. Drain; assert one body evaluation, one delivered 7, no failures, no active tokens. Count Send tokens separately from executor/Future tokens; do not demand a compiler-version-independent total number of Runnables.
2. Have the first handler enqueue another message to itself. Assert the second delivery occurs and all tokens finish. After the queue becomes empty, send again and drain; this catches a `scheduled` flag left permanently true.
3. Throw an ordinary RuntimeException from a SimpleActor handler. Assert the same exception is reported once and the message token completes; send another message to establish subsequent progress. Repeat a BatchActor handler failure, expecting completion for every message token in the batch.
4. Fail an external Promise. Assert failure reporting and no message-delivery token; before Promise completion, zero active tokens can be legitimate. Do not equate inactivity with completion of an unresolved external source.

A finite queue drain proves only the controlled schedule. It is not a multithreaded race or rejection test. Add a real-platform async test that returns the assertion-bearing Future to uTest, with an external test-run deadline. Use a Promise fulfilled by the handler and assertions mapped using the platform execution context; do not block a JS event loop. Such a delivery test still does not prove all tokens completed; retain the separate accounting oracle.

## Old-consumer protocol

Use a fixed Scala binary version and JDK supported by both baseline and candidate. Discover the baseline artifact from the actual tag/history and MiMa configuration; do not silently switch to a newer baseline.

Compile an external-package consumer against the baseline. It should call `Context.scheduleMsg(actor, message, java.time.Duration.ofMillis(...))`, instantiate the public thread-pool helper if that surface moved, and exercise real delivery. Save its class files and compile classpath. Run the exact saved classes with only Castor's artifact replaced by the candidate; do not recompile the consumer or leave both Castor versions on the runtime classpath. Class-load/linkage failure is an ABI result distinct from a source compiler error. Then separately recompile the same source against the candidate. Record both outcomes, rather than guessing which descriptor moved from private-mixin visibility.

Keep any scheduling runtime probe deadline-bounded and clean up consumer-owned executors. A method-only consumer fixture can expose the signature at compile time, but needs a harness to invoke it before it is a runtime ABI test. Prefer the repository's actual compatibility tasks where available; never invent a pre-existing consumer target.

## Build gates and validation

In an authorized disposable checkout, inspect its pinned launcher/build before execution. The actual 2022 CI commands ([actions.yml](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/.github/workflows/actions.yml)) are `./mill -i all __.publishArtifacts __.test` and, separately with full history for last-tag discovery, `./mill -i __.mimaReportBinaryIssues`. PR #10's addition of `all` ([d8cc9c3](https://github.com/com-lihaoyi/castor/commit/d8cc9c386e4ad24fd05222d6eafca4b724a8ca2c)) repairs the prior invocation that did not run tests. `publishArtifacts` prepares artifacts; do not invoke publishing tasks or supply credentials. These commands are historical discoveries, not execution results.

Resolve real module/source/test tasks from that checkout before narrowing selectors. PR #3 ([build.sc](https://github.com/com-lihaoyi/castor/blob/6665317383b0fe1c75a0a087d1e5cc65cefdf09b/build.sc)) had to repair source-root resolution and test inheritance after a cross-module layout change. Verify nonempty shared/platform sources and recorded test discovery; do not transplant the old two-axis selectors ([2022 build.sc](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/build.sc)) into the 2024 single-axis build ([build.mill](https://github.com/com-lihaoyi/castor/blob/189e2c869be8f750c94802c5a2ea7b65a03ee821/build.mill)). Report every skipped/no-baseline compatibility cell (2022 Scala 3; 2024 Native in the examined snapshots).

Record source count, artifact contents, discovered/ran tests, link/runtime status, baseline coordinate, skipped cells and consumer results per target. If Node, Native linker/compiler, matching JDK, artifacts or permissions are missing, mark that gate not run. Do not download or run arbitrary historical launchers merely to turn a source review green. A task exit without test discovery or a nonempty compatibility baseline is not a validated matrix. A source fixture alone proves no compilation, ABI result or race freedom.

## Examples

**Good.** Extract JVM `scheduleMsg(java.time.Duration)` and thread-pool machinery into the JVM platform mixins, leave token/Future/queue behavior shared, and select empty scheduling mixins on JS/Native. Exercise `sendAsync` there with a returned delivery assertion, then run an old JVM caller without recompiling it. Report a binary break explicitly if observed. This follows PR #12's final direction without falsely claiming portable timers or that its historical smoke test already asserted delivery.

**Broken and correction.** A refactor copies Context three times, adds a public JVM-duration method to the shared trait, then cites `foo.sendAsync(Future(()))` returning Unit as proof of full portability and delivery. Correction: isolate platform signatures, verify the selected mixins and actual linker reachability, and preserve the shared actor engine. Replace the test's empty handler with a delivery assertion and observe token completion after a bounded drain. Retain the separate `waitForInactivity` portability warning. If the move changes inherited ABI, test the old binary and document the release consequence instead of relying on source compilation.

**Negative.** A patch changes only a JVM timer implementation while keeping its `java.time.Duration` signature, source roots and shared actor engine unchanged. Do not report a cross-platform defect merely because JS lacks that timer. Review the actual JVM timer behavior normally; do not demand new effects, immutability rewrites or synthetic Native stubs.

## Case-specific output fields

A target/version/capability table; violated invariant; concrete test with expected observation. Record source-compatibility, old-binary, link, runtime-delivery and quiescence results separately as passed/failed/not run/unsupported. State which baselines or targets were skipped and what remains unproved; do not call a source-only review a successful build.

## Limitations

One small-library design episode, supplemented by build repairs and later snapshots, not a repeated multi-year maintainer policy. The accounting procedure is source-derived inference. There is no historical proof here of cancellation, rejection safety, bounded backpressure or arbitrary concurrent-race freedom. Current platform support must be rechecked; research did not execute upstream builds or compile the proposed tests. Attribute only each PR participant's own text, not forwarded email; formal maintainer rank of the PR #12 author is unverified.

## Sources

- [Evidence and claim mapping](evidence/scala-castor-platform-mixin-dispatch-accounting.json): platform boundary, compatibility disposition, build dispatch, timer-proposal distinction and accounting preservation.
- [PR #12 duplication concern](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919783061), [linker constraint and revised tradeoff](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919928186), and [release decision](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919974891).
- [Shared actor engine](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/castor/src/Actors.scala) and [shared smoke test](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/castor/test/src/ActorsTest.scala).
