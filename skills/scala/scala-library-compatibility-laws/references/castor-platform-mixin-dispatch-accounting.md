# Castor: platform mixins across JVM/JS/Native without changing dispatch contracts

Library: com-lihaoyi/castor (Future/ExecutionContext actors; Mill). Evidence ledger: [evidence/scala-castor-platform-mixin-dispatch-accounting.json](evidence/scala-castor-platform-mixin-dispatch-accounting.json) (claims `castor-claim-platform-boundary`, `castor-claim-compatibility-disposition`, `castor-claim-build-dispatch`, `castor-claim-portable-timer-proposals`, `castor-claim-accounting-invariant`).

## Scope

Use when moving Castor `Context`, its companion or `Context.Impl` members between shared and platform roots, repairing JS/Native linking of actor entry points, or claiming a formerly JVM-only scheduling API is portable. Review inherited public surface together with unchanged shared dispatch engine.

Not for: generic Mill layout cleanup (Mill skills own build procedures), ordinary actor application design, unrelated backpressure algorithms. JVM-only timer change without changed platform boundary does not justify moving timer into shared code. Do not migrate this Future/ExecutionContext library to Ox, Cats Effect or ZIO.

## Version map

Read target revision's build, launcher/version pin, source roots, public `Actor` and `Context`, platform traits, tests. Record Scala, Mill, JDK, Scala.js/Native, sourcecode, uTest and compatibility-baseline versions. Do not use calendar year as platform selector.

| Anchor | Language/platform/testing boundary |
| --- | --- |
| PR #3, `6665317383b0fe1c75a0a087d1e5cc65cefdf09b` (2020-03-05) | JVM/JS Scala 2.12.10 and 2.13.1; Native Scala 2.11.12 with Native 0.3.9/0.4.0-M2. JS 0.6.32/1.0.0. Sourcecode 0.2.1, uTest 0.7.4. Fixes source roots and platform test inheritance; explicit Runnable/Callable supports Scala 2.11 floor. |
| PR #12 final head, `6fa845bae0e852d57f57b49a450396583c3494bc` (2021-09-15) | Scala 2.11.12/2.12.13/2.13.4/3.0.0; JS 0.6.33/1.5.1 with Scala 3 only on JS 1.x; Native 0.4.0 on Scala 2 only. Sourcecode 0.2.7, uTest 0.7.10, MiMa plugin 0.0.4 built for Mill 0.9. No exact launcher pin inferred from plugin suffix. |
| `ae2ba2fe72c930999251d04aaef57cbef808f89b` (2022-07-09) | Mill 0.10.5; Scala 2.11.12/2.12.16/2.13.8/3.1.3; JS 1.10.1; Native 0.4.5; sourcecode 0.2.8; uTest 0.8.0. CI JDK 8/17. Scala 3 MiMa previous artifacts explicitly empty. |
| `189e2c869be8f750c94802c5a2ea7b65a03ee821` (2024-10-24) | Mill 0.12.0; build.mill/package build; Scala 2.12.19/2.13.13/3.3.3; JS 1.16.0; Native 0.5.4; sourcecode 0.4.1; uTest 0.8.3. One Scala-version cross axis. CI JDK 11/17 not an established published bytecode floor. Native MiMa previous artifacts empty pending first 0.5 release. |

No Cats Effect, ZIO or Ox runtime in these builds. Keep Castor's eager Future/ExecutionContext design. By-name argument to `Context.future` runs later on executor; it does not make returned Future a reusable lazy effect.

## Workflow

1. **Write a capability table before moving files.** Per target: owners and signatures of `scheduleMsg`, `scheduler`, thread-pool factories/classes, `Simple.global`, `future`, test quiescence. Include inherited members: `private[castor]` on a mixin does not make its inherited public methods ABI-irrelevant.
2. **Trace the actual linkable entry point.** Follow `Actor.sendAsync` through `BaseActor`, implicit `Context`, `Simple.executionContext`, platform adapter. Inspect public signatures and implementation references. PR #12's author reported `java.time`/`java.util.concurrent` methods in public traits made Scala.js linker complain (Scala Native linked) ([comment](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919928186)). Reproduce on chosen versions; do not infer failure from unused import.
3. **Move only platform-dependent members.** Keep token creation, Future dispatch and actor queue handling in one shared implementation. Selected roots must define exactly one compatible `castor.platform.Context`, `ContextImpl`, companion mixin and adapter. PR #12 turned duplicated implementation into this boundary ([JVM mixin](https://github.com/com-lihaoyi/castor/blob/6fa845bae0e852d57f57b49a450396583c3494bc/castor/src-jvm/castor/platform/Context.scala), [empty JS/Native mixin](https://github.com/com-lihaoyi/castor/blob/6fa845bae0e852d57f57b49a450396583c3494bc/castor/src-js-native/Context.scala)); it did not ship reviewer-suggested portable `FiniteDuration` overload ([proposal](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919857735)).
4. **Audit what remains shared.** In 2022 and 2024 sources, `TestBase.waitForInactivity` still takes `Option[java.time.Duration]` and blocks on `Await` ([Context.scala L121-L128](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/castor/src/Context.scala#L121-L128)). List it as separate unproved portable capability. Do not claim whole Context API portable because `sendAsync` links. Avoid this helper in shared async tests.
5. **Preserve dispatch accounting while extracting.** Trace message tokens separately from executor-runnable and `Context.future` tokens. Preserve `SimpleActor`'s per-message `finally`, `BatchActor`'s completion for every batch token, BaseActor's synchronized queue/`scheduled` handoff ([Actors.scala](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/castor/src/Actors.scala)). For normal handlers, accepting executors and nonthrowing hooks, compare delivery, completion and quiescence before/after. Rejection or throwing instrumentation: separate fault boundaries, not already-proven behavior.
6. **Make compatibility and support claims independently.** Compile old JVM source calls (including `java.time.Duration`) against candidate; separately run unchanged old-compiled consumer against it. Inspect inherited class/member changes and MiMa exclusions. PR #12's final revision explicitly traded binary compatibility for shared code (commit [02c1c6f](https://github.com/com-lihaoyi/castor/commit/02c1c6f54e230ebf73dc86429cf814fd8f397d89): "NOT binary compatible, but is source compatible"); reviewer agreed to tag 0.2.0 ([comment](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919974891)). Its initial patch-release description is not final disposition. Native method throwing `NotImplementedError` (unmerged PR #15, [ContextImpl.scala](https://github.com/com-lihaoyi/castor/blob/85ac5ae0b4fc3eaf185cefd56a00c2d5896625e0/castor/src-native/ContextImpl.scala)) is not implemented support. Same PR replaced `java.time.Duration` with `scala.concurrent.duration.Duration` ([JVM Context](https://github.com/com-lihaoyi/castor/blob/85ac5ae0b4fc3eaf185cefd56a00c2d5896625e0/castor/src-jvm/castor/platform/Context.scala)); that is not the additive overload discussed earlier. Unmerged proposal is not a release. PR #15 closure rationale unknown.

## Checks

Testable invariants under stated executor/hook assumptions:

- Each scheduled message token completes once, even when handler throws and is reported; runnable tokens accounted independently.
- Next drain picks up messages queued during a batch; going idle lets a later send schedule again. Do not replace synchronization protocol as incidental cleanup.
- `sendAsync` success sends a value; failed Futures report failure without inventing a delivered message. Castor may not track pending external Future before its callback runs ([Actors.scala L23-L29](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/castor/src/Actors.scala#L23-L29)): temporary inactivity is not proof of delivery.
- JVM keeps advertised duration/thread-pool calls unless deliberate migration is approved; other platforms expose only capabilities actually implemented and linked.

False positives: JVM type in JVM-only root is legitimate; empty JS/Native scheduling mixin may deliberately omit unavailable capability. Shared smoke test is useful for reachability but insufficient for delivery. Neither release approval nor modern Native linking establishes universal historical design preference.

## Reachability audit (2022 shared `Context.scala`)

- Lines 12, 40, 72 and 132 inherit platform Context, companion, Simple companion and implementation members. Check signatures inherited through all four, not only public trait body.
- Lines 121-128 keep `waitForInactivity(timeout: Option[java.time.Duration])` with `Await.result`. Its default-argument path and calling conventions are separate from `sendAsync` linking. Do not delete or relocate without consumer analysis; do not use as portable event-loop test helper.
- Line 3: leftover JVM import. Unused import is not a reachable JVM-only method. Check compiler/linker output before diagnosing.
- `ActorsTest.scala:16-23` ([file](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/castor/test/src/ActorsTest.scala)) calls async entry point but returns Unit with empty handler. Cannot prove delivery, exactly-once processing or quiescence.
- JVM debounce test ([JvmActorsTest.scala](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/castor/test/src-jvm/JvmActorsTest.scala)) uses retained `java.time` API; keep JVM timer integration separate.

For new target, one row per entry point: signature types, implementation owner, source-root resolution, consumer reaching it, link status, observed behavior. Intentionally omitted `scheduleMsg` differs from method present but throwing.

## Controlled dispatch oracle

Use manually drained ExecutionContext that queues Runnable values and fails after finite steps. Keep recorder separate from `TestBase` so test does not import its blocking helper. Track token identity and category through all three `reportSchedule` overloads and `reportComplete`. Assert duplicate, unknown and missing completion.

1. Schedule `actor.sendAsync(context.future(7))`; before draining, body and handler have not run. Drain; assert one body evaluation, one delivered 7, no failures, no active tokens. Count Send tokens separately from executor/Future tokens; do not demand compiler-version-independent total Runnable count.
2. First handler enqueues another message to itself. Assert second delivery and all tokens finish. After queue empties, send again and drain; catches `scheduled` flag left permanently true.
3. Throw ordinary RuntimeException from SimpleActor handler. Assert same exception reported once and message token completes; send another message to show later progress. Repeat with BatchActor handler failure: every message token in batch completes.
4. Fail external Promise. Assert failure reported and no message-delivery token; before Promise completes, zero active tokens can be legitimate. Do not equate inactivity with completion of unresolved external source.

Finite queue drain proves only the controlled schedule; not a multithreaded race or rejection test. Add real-platform async test returning assertion-bearing Future to uTest, with external test-run deadline. Use Promise fulfilled by handler, assertions mapped on platform execution context; do not block JS event loop. Delivery test still does not prove all tokens completed; keep separate accounting oracle.

## Old-consumer protocol

Fix Scala binary version and JDK supported by both baseline and candidate. Discover baseline artifact from actual tag/history and MiMa configuration; do not silently switch to newer baseline.

Compile external-package consumer against baseline: call `Context.scheduleMsg(actor, message, java.time.Duration.ofMillis(...))`, instantiate public thread-pool helper if that surface moved, exercise real delivery. Save class files and compile classpath. Run exact saved classes with only Castor's artifact swapped for candidate; do not recompile consumer or leave both Castor versions on runtime classpath. Class-load/linkage failure is ABI result, distinct from source compiler error. Then separately recompile same source against candidate. Record both outcomes; do not guess which descriptor moved from private-mixin visibility.

Keep scheduling runtime probes deadline-bounded; clean up consumer-owned executors. Method-only consumer fixture exposes signature at compile time but needs invoking harness before it is runtime ABI test. Prefer repository's actual compatibility tasks where available; never invent pre-existing consumer target.

## Build gates and validation

In authorized disposable checkout, inspect pinned launcher/build before execution. Actual 2022 CI commands ([actions.yml](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/.github/workflows/actions.yml)): `./mill -i all __.publishArtifacts __.test` and, separately with full history for last-tag discovery, `./mill -i __.mimaReportBinaryIssues`. PR #10 added `all` ([d8cc9c3](https://github.com/com-lihaoyi/castor/commit/d8cc9c386e4ad24fd05222d6eafca4b724a8ca2c)), fixing prior invocation that ran no tests. `publishArtifacts` prepares artifacts; do not invoke publishing tasks or supply credentials. Commands are historical discoveries, not execution results.

Resolve real module/source/test tasks from that checkout before narrowing selectors. PR #3 ([build.sc](https://github.com/com-lihaoyi/castor/blob/6665317383b0fe1c75a0a087d1e5cc65cefdf09b/build.sc)) repaired source-root resolution and test inheritance after cross-module layout change. Verify nonempty shared/platform sources and recorded test discovery; do not transplant old two-axis selectors ([2022 build.sc](https://github.com/com-lihaoyi/castor/blob/ae2ba2fe72c930999251d04aaef57cbef808f89b/build.sc)) into 2024 single-axis build ([build.mill](https://github.com/com-lihaoyi/castor/blob/189e2c869be8f750c94802c5a2ea7b65a03ee821/build.mill)). Report every skipped/no-baseline compatibility cell (2022 Scala 3; 2024 Native in examined snapshots).

Per target record source count, artifact contents, discovered/ran tests, link/runtime status, baseline coordinate, skipped cells, consumer results. If Node, Native linker/compiler, matching JDK, artifacts or permissions are missing, mark that gate not run. Do not download or run arbitrary historical launchers just to turn source review green. Task exit without test discovery or nonempty compatibility baseline is not a validated matrix. Source fixture alone proves no compilation, ABI result or race freedom.

## Examples

**Good.** Extract JVM `scheduleMsg(java.time.Duration)` and thread-pool machinery into JVM platform mixins, keep token/Future/queue behavior shared, select empty scheduling mixins on JS/Native. Exercise `sendAsync` there with returned delivery assertion, then run old JVM caller without recompiling. Report binary break explicitly if observed. Follows PR #12's final direction without falsely claiming portable timers or that its historical smoke test already asserted delivery.

**Broken and correction.** Refactor copies Context three times, adds public JVM-duration method to shared trait, cites `foo.sendAsync(Future(()))` returning Unit as proof of full portability and delivery. Correction: isolate platform signatures, verify selected mixins and actual linker reachability, keep shared actor engine. Replace test's empty handler with delivery assertion; observe token completion after bounded drain. Keep separate `waitForInactivity` portability warning. If move changes inherited ABI, test old binary and document release consequence; do not rely on source compilation.

**Negative.** Patch changes only JVM timer implementation; its `java.time.Duration` signature, source roots and shared actor engine stay unchanged. Do not report cross-platform defect merely because JS lacks that timer. Review JVM timer behavior normally; do not demand new effects, immutability rewrites or synthetic Native stubs.

## Case-specific output fields

Target/version/capability table; violated invariant; concrete test with expected observation. Record source-compatibility, old-binary, link, runtime-delivery and quiescence results separately as passed/failed/not run/unsupported. State skipped baselines/targets and what remains unproved; do not call source-only review a successful build.

## Limitations

One small-library design episode plus build repairs and later snapshots, not repeated multi-year maintainer policy. Accounting procedure is source-derived inference. No historical proof here of cancellation, rejection safety, bounded backpressure or arbitrary concurrent-race freedom. Recheck current platform support; research did not run upstream builds or compile proposed tests. Attribute only each PR participant's own text, not forwarded email; PR #12 author's formal maintainer rank unverified.

## Sources

- [PR #12 duplication concern](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919783061), [linker constraint and revised tradeoff](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919928186) and [release decision](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919974891).
