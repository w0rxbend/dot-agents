---
name: scala-play-partial-startup-shutdown-completion
description: Use when refactoring Play ApplicationLifecycle, development startup hooks, or coordinated server shutdown. Preserve partial-startup cleanup, lazy activation order, shared Future completion, and bounded response draining.
license: MIT
---

# Preserve Play startup and shutdown contracts

Review the observable event sequence, not just the signatures. This procedure follows Play's Future/Promise lifecycle and Akka-era shutdown reviews, including a later Scala-to-Java run-support port. It does not introduce an effect runtime.

## When to Use

Use for changes to `ApplicationLifecycle`, application loading, `DevServerRunner`, server stop wiring, or shutdown-task ordering. Trigger when a refactor moves construction across hooks, changes what `stop()` completion means, or replaces unbinding with another termination operation.

## When Not to Use

Do not use as a general Cats Effect/ZIO/Ox resource-management recipe or a reason to migrate Play's sbt build. Pure configuration extraction without moved callbacks/acquisition is not a lifecycle defect. Listener-only administrative unbinding is not necessarily whole-server shutdown. Global logger isolation is adjacent research, not a guarantee supplied by this skill.

## Prerequisites

Record the target SHA, Play line, Scala/compiler/JDK versions, server backend, mode, and ActorSystem owners. Read the actual `build.sbt`, `project/build.properties`, build plugins/settings, CI selectors and test classes. Preserve Scala Future, Java CompletionStage and the established Akka/Pekko namespace. The 2018 source uses the `framework/src` layout; 2020 uses `core`/`transport`; the 2024 run-support implementation is Java while sbt-plugin consumers remain Scala.

Read [historical boundaries and test oracles](references/temporal-contracts.md). Historical dependency defaults are not the versions of every PR in the same calendar year. Obtain separate authorization and an isolated checkout/cache before executing an upstream build; these research artifacts did not execute one.

## Workflow

1. **Draw the ownership graph.** Trace loader → lifecycle → application, server → ActorSystem, and every `stop`/CoordinatedShutdown call. Separate production's shared system from development's potentially distinct systems and embedded/borrowed systems. Mark which owner remains reachable when `ApplicationLoader.load` throws before returning an Application. Do not delete that cleanup path merely because successful startup has `Application.stop`.
2. **Trace activation, not allocation syntax.** List `beforeStarted`, user `assetsClassLoader` invocation, watcher/reloader activation, server binding, and `afterStarted`. A Scala lazy value translated to an eager Java constructor can run user code or start a watcher too early. Keep the activation after successful `beforeStarted`; instrument both events. Separately inspect acquisition failures after that point: the observed port is not proof that every partial failure releases every resource.
3. **Separate once-only execution from completed cleanup.** Follow the `AtomicBoolean` gate, hook deque, and memoized `Promise.future` in the default lifecycle. Every stop caller must observe actual final completion; a losing caller must not receive an already-successful Future while hooks still run. Preserve delayed hook invocation, LIFO sequence, and continuation after an ordinary synchronous throw or failed Future.
4. **Make shutdown dependencies explicit.** Trace completion edges, not textual registration order. Tasks in one CoordinatedShutdown phase may run concurrently. If cleanup uses logging or another resource, compose the Futures or choose dependency-ordered phases. Avoid a task awaiting the same CoordinatedShutdown run that is awaiting that task. Do not 'fix' a cycle by prematurely reporting external shutdown complete.
5. **Distinguish unbind from drain.** For full server termination, inspect how existing responses, HTTP/HTTPS bindings and the ActorSystem are completed. Derive the termination timeout fallback through the owning shutdown API; retain an observable finite outer wait. Do not copy the historical five-second margin as a universal value. Inspect whether sequential binding termination can exhaust a phase budget.
6. **Review every consumer layer.** Run-support tests, sbt-plugin unit tests and scripted applications are separate. Check exception wrapping and original causes at the Java/Scala boundary. Record the changed invariant, minimal repair, retained behavior and missing regression cases before broadening the patch.

## Review and Refactoring Checks

Preserve these invariants: cleanup remains reachable before successful Application construction; startup hooks precede watcher/user-loader activation; registered hooks run once in reverse order without overlap; stop completion follows the last hook; normal hook failure does not skip remaining cleanup; shutdown dependencies have real completion edges.

False positives: internal AtomicBoolean/Promise mutation is part of the observed implementation, not inherently a defect. Independent same-phase tasks may intentionally run concurrently. A hook that has genuinely completed may return an already-successful Future. This does not imply that new hook registration concurrent with shutdown is supported—establish that contract separately.

Do not claim Play historically satisfied every requested invariant. The January 2020 server still registers logger shutdown and the user hook in the same phase. The historical repeated-stop test is not a simultaneous-stop race proof.

## Validation

First discover targets from the chosen checkout. After build authorization, `sbt 'projects'` and `sbt 'show Play / Test / definedTests'` establish project/test discovery; require the expected suites and nonzero execution. For a checkout retaining the inspected core suite, use `sbt 'Play/testOnly play.api.inject.DefaultApplicationLifecycleSpec'`.

For the inspected Java-port consumer, discover and run `sbt 'Play-Run-Support/test' 'Sbt-Plugin/testOnly play.sbt.PlayRunHookSpec'`. A broader `Sbt-Plugin/test` remains necessary when other plugin tests are affected. The historical `Sbt-Plugin/scripted play-sbt-plugin/shutdown-happy-path` fixture checks a slow response across shutdown, but requires matching locally published artifacts: `scriptedDependencies` deliberately omits compilation/publication. Inspect the repository's publishing/test scripts before using it; never silently publish into a developer's ordinary cache.

Add the barrier-driven completion and startup-failure oracles in the reference. Exercise development, production, embedded ownership, finite deadline expiration and relevant backends. Report source inspection, authored test plan, actual execution and skipped cells separately; a green schema check proves none of these runtime properties.

## Examples

### Good

In the pinned 2018 default lifecycle, a CAS selects the single hook runner and all callers return the stored Promise's Future. Hooks are invoked inside the previous hook's `flatMap`, with failure recovery. Accept an equivalent refactor only if a held hook keeps every stop result pending and the remaining hooks execute in LIFO order after release.

### Broken and Correction

A port constructs `DevServerReloader` and invokes `assetsClassLoader` before `beforeStarted`, calling this a syntax-only change. That recreates the timing concern in PR 12210. Correction: restore hook-before-activation ordering, then test that a failing before-start hook produces no watcher activation. A second defect—returning `Future.successful(Done)` to subsequent stop callers—requires the shared pending completion, not merely an invocation counter. Test both callers while the last hook is deliberately blocked.

### Negative

Moving an already-computed immutable port number into a local changes no callback or acquisition timing. Do not demand a resource wrapper or effect migration. Likewise, two independent diagnostic tasks in one phase need no sequencing finding unless one demonstrably consumes a resource the other closes.

## Output Contract

For each finding give `file:line`, severity, the changed event/completion invariant, target versions/mode/backend, historical evidence ID, current-source evidence, minimal correction and a discriminating test. State whether the test was executed, merely proposed or unavailable. Return an explicit no-finding when the trace is preserved; list uncovered failure paths without asserting leaks that have not been demonstrated.

## Limitations

Historical review establishes concerns and bounded revisions, not universal leak freedom, cancellation guarantees, or today's Akka/Pekko behavior. No Scala/Java compilation or upstream tests ran during authoring. Reviewers' project ranks are unverified; substantive comments are attributed to their authors, not generalized into creator preferences. Future concurrency tests are inference-based extensions, not invented historical tests.

## Sources

[Evidence records and claims](references/evidence.json) bind this procedure to `c-lifecycle-temporal`, `c-lifecycle-completion`, `c-shutdown-budget` and build discovery. Primary anchors include [partial-startup cleanup, PR 8406](https://github.com/playframework/playframework/pull/8406#issuecomment-389230012), [same-phase ordering concern](https://github.com/playframework/playframework/pull/8406#discussion_r193607508), [lazy-port correction, PR 12210](https://github.com/playframework/playframework/pull/12210#pullrequestreview-1767427947), and [the pinned termination implementation](https://github.com/playframework/playframework/blob/5b4eaf91caa1aa17ef5aca5f54a21067385bf2f6/transport/server/play-akka-http-server/src/main/scala/play/core/server/AkkaHttpServer.scala#L460-L493).
