# Validation boundaries and concrete oracles

These are source-derived validation procedures, not historical test results. Read the compact [evidence map](evidence.json) for provenance. Execute only in an authorized disposable checkout with inspected tooling; the research session does not run upstream code.

## Version map

| Anchor | Language/platform/testing boundary |
| --- | --- |
| PR #3, `6665317383b0fe1c75a0a087d1e5cc65cefdf09b` (2020-03-05) | JVM/JS Scala 2.12.10 and 2.13.1; Native Scala 2.11.12 with Native 0.3.9/0.4.0-M2. JS 0.6.32/1.0.0. Sourcecode 0.2.1, uTest 0.7.4. Fixes source roots and platform test inheritance; explicit Runnable/Callable supports the Scala 2.11 floor. |
| PR #12 final head, `6fa845bae0e852d57f57b49a450396583c3494bc` (2021-09-15) | Scala 2.11.12/2.12.13/2.13.4/3.0.0; JS 0.6.33/1.5.1 with Scala 3 only on JS 1.x; Native 0.4.0 on Scala 2 only. Sourcecode 0.2.7, uTest 0.7.10, MiMa plugin 0.0.4 built for Mill 0.9. No exact launcher pin is inferred from that plugin suffix. |
| `ae2ba2fe72c930999251d04aaef57cbef808f89b` (2022-07-09) | Mill 0.10.5; Scala 2.11.12/2.12.16/2.13.8/3.1.3; JS 1.10.1; Native 0.4.5; sourcecode 0.2.8; uTest 0.8.0. CI JDK 8/17. Scala 3 MiMa previous artifacts explicitly empty. |
| `189e2c869be8f750c94802c5a2ea7b65a03ee821` (2024-10-24) | Mill 0.12.0; build.mill/package build; Scala 2.12.19/2.13.13/3.3.3; JS 1.16.0; Native 0.5.4; sourcecode 0.4.1; uTest 0.8.3. One Scala-version cross axis. CI JDK 11/17 is not an established published bytecode floor. Native MiMa previous artifacts empty pending first 0.5 release. |

No Cats Effect, ZIO or Ox runtime is used in these builds. Preserve Castor's eager Future/ExecutionContext design. A by-name argument to `Context.future` executes later on the executor; it does not turn the returned Future into a reusable lazy effect.

## Reachability audit

At the 2022 shared `Context.scala`:

- Lines 12, 40, 72 and 132 inherit platform Context, companion, Simple companion and implementation members. Check signatures inherited through all four, not just the public trait body.
- Lines 121–128 retain `waitForInactivity(timeout: Option[java.time.Duration])` with `Await.result`. Its default-argument path and calling conventions are separate from `sendAsync` linking. Do not delete or relocate it without consumer analysis; do not invoke it as a portable event-loop test helper.
- Line 3 has a leftover JVM import. An unused import is not equivalent to a reachable JVM-only method. Check compiler/linker output before diagnosing it.
- `ActorsTest.scala:16–23` does call the async entry point, but returns Unit and has an empty handler. It cannot prove delivery, exactly-once processing or quiescence.

For a new target, produce one row per entry point with signature types, implementation owner, source-root resolution, consumer that reaches it, link status and observed behavior. An intentionally omitted `scheduleMsg` is different from a method present but throwing.

## Controlled dispatch oracle

Use a manually drained ExecutionContext that queues Runnable values and fails after a finite number of steps. Keep the recorder separate from `TestBase` so the test does not import its blocking helper. Track token identity and category through all three reportSchedule overloads and reportComplete. Assert duplicate or unknown completion as well as missing completion.

Cases to implement against the target API:

1. Schedule `actor.sendAsync(context.future(7))`; before draining, the body and handler have not run. Drain; assert one body evaluation, one delivered 7, no failures, no active tokens. Count Send tokens separately from executor/Future tokens; do not demand a compiler-version-independent total number of Runnables.
2. Have the first handler enqueue another message to itself. Assert the second delivery occurs and all tokens finish. After the queue becomes empty, send again and drain; this catches a `scheduled` flag left permanently true.
3. Throw an ordinary RuntimeException from a SimpleActor handler. Assert the same exception is reported once and the message token completes; send another message to establish subsequent progress. Repeat a BatchActor handler failure, expecting completion for every message token in the batch.
4. Fail an external Promise. Assert failure reporting and no message-delivery token; before Promise completion, zero active tokens can be legitimate. Do not equate inactivity with completion of an unresolved external source.

A finite queue drain proves only the controlled schedule. It is not a multithreaded race or rejection test. Add a real-platform async test that returns the assertion-bearing Future to uTest, with an external test-run deadline. Use a Promise fulfilled by the handler and assertions mapped using the platform execution context; do not block a JS event loop. Such a delivery test still does not prove all tokens completed—retain the separate accounting oracle.

## Old-consumer protocol

Use a fixed Scala binary version and JDK supported by both baseline and candidate. Discover the baseline artifact from the actual tag/history and MiMa configuration; do not silently switch to a newer baseline.

Compile an external-package consumer against the baseline. It should call `Context.scheduleMsg(actor, message, java.time.Duration.ofMillis(...))`, instantiate the public thread-pool helper if that surface moved, and exercise real delivery. Save its class files and compile classpath. Run the exact saved classes with only Castor's artifact replaced by the candidate; do not recompile the consumer or leave both Castor versions on the runtime classpath. Class-load/linkage failure is an ABI result distinct from a source compiler error. Then separately recompile the same source against the candidate. Record both outcomes, rather than guessing which descriptor moved from private-mixin visibility.

Keep any scheduling runtime probe deadline-bounded and clean up consumer-owned executors. A method-only consumer fixture can expose the signature at compile time, but needs a harness to invoke it before it is a runtime ABI test. Prefer the repository's actual compatibility tasks where available; never invent a pre-existing consumer target.

## Build gates and reporting

Discover `sources`, platform `test` modules, launcher pin and actual CI from the selected checkout. Historical 2022 CI uses `./mill -i all __.publishArtifacts __.test` and separately `./mill -i __.mimaReportBinaryIssues`; the latter uses full history for last-tag discovery. PR #10's addition of `all` repairs the prior invocation. A task exit without test discovery or a nonempty compatibility baseline is not a validated matrix.

Record source count, artifact contents, discovered/ran tests, link/runtime status, baseline coordinate, skipped cells and consumer results per target. If Node, Native linker/compiler, matching JDK, artifacts or permissions are missing, mark that gate not run. Do not download or run arbitrary historical launchers merely to turn a source review green.
