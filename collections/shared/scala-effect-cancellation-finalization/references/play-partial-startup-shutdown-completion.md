# Play Framework: partial startup and shutdown completion (originally scala-play-partial-startup-shutdown-completion)

Evidence: [evidence/scala-play-partial-startup-shutdown-completion.json](evidence/scala-play-partial-startup-shutdown-completion.json)
(claims `c-lifecycle-temporal`, `c-lifecycle-completion`, `c-shutdown-budget`, `c-build-discovery`).

Review the observable event sequence, not just signatures. Follows Play's Future/Promise lifecycle and Akka-era
shutdown reviews, plus a later Scala-to-Java run-support port. Introduces no effect runtime.

## Scope

Changes to `ApplicationLifecycle`, application loading, `DevServerRunner`, server stop wiring or shutdown-task
ordering — a refactor that moves construction across hooks, changes what `stop()` completion means, or replaces
unbinding with another termination operation.

Not a Cats Effect/ZIO/Ox resource recipe or a reason to migrate Play's sbt build. Pure configuration extraction without
moved callbacks/acquisition is not a lifecycle defect. Listener-only administrative unbinding is not necessarily
whole-server shutdown. Global logger isolation is adjacent research, not guaranteed here.

## Prerequisites

Record target SHA, Play line, Scala/compiler/JDK, server backend, mode and ActorSystem owners. Read the actual
`build.sbt`, `project/build.properties`, build plugins/settings, CI selectors and test classes. Preserve Scala Future,
Java CompletionStage and the established Akka/Pekko namespace. Layouts: 2018 `framework/src`; 2020 `core`/`transport`;
the 2024 run-support implementation is Java while sbt-plugin consumers remain Scala. Historical dependency defaults are
not the versions of every PR in the same calendar year. Obtain separate authorization and an isolated checkout/cache
before executing an upstream build.

## What was observed

- **2018, PR 8406.** gmethvin, [partial startup](https://github.com/playframework/playframework/pull/8406#issuecomment-389230012):
  "`Application#stop()` requires you to have an application instance. If an exception is thrown before the app is
  initialized, you may still have some resources to…" — ignasi35 revised toward an independently reachable lifecycle and
  explained partial ActorSystem allocation was still a concern. A dependency/ownership constraint, not proof of
  universal leak freedom. gmethvin, [dependency direction](https://github.com/playframework/playframework/pull/8406#discussion_r189422684):
  "The Play application depends on the `ActorSystem` … so `Play.stop` should invoke `CoordinatedShutdown` and not the
  other" — later discussion distinguished shared production ActorSystems from separate development systems. TimMoore,
  [same-phase ordering](https://github.com/playframework/playframework/pull/8406#discussion_r193607508): it "shouldn't
  happen concurrently with the `"user-provided-server-stop-hook"` task" — reviewer guidance, not a proven invariant.
  patriknw, [bounded wait](https://github.com/playframework/playframework/pull/8406#discussion_r193638555): "I'd not use
  `Duration.Inf` because that would result in the worst kind error handling … complete silence and hanging process";
  gmethvin later requested an explanatory comment. The five-second margin is historical policy, not universal.
  The final [ApplicationLifecycle](https://github.com/playframework/playframework/blob/6059f791124fd979084567014e281b71780f648e/framework/src/play/src/main/scala/play/api/inject/ApplicationLifecycle.scala#L94-L134)
  uses a deque, CAS (`if (started.compareAndSet(false, true))`) and a shared Promise; hooks chain via `flatMap` with
  recovery of synchronous throws and failed Futures. Its
  [tests](https://github.com/playframework/playframework/blob/6059f791124fd979084567014e281b71780f648e/framework/src/play/src/test/scala/play/api/inject/DefaultApplicationLifecycleSpec.scala#L19-L71)
  cover order (`List(3, 2, 1)`), ordinary synchronous/asynchronous failure continuation and repeated calls, not
  barrier-controlled concurrent callers.
- **2020, PR 9970.** Binding termination replaces unbind-only stopping. Timeout fallback uses
  `cs.timeout(PhaseServiceUnbind)` ([source](https://github.com/playframework/playframework/blob/5b4eaf91caa1aa17ef5aca5f54a21067385bf2f6/transport/server/play-akka-http-server/src/main/scala/play/core/server/AkkaHttpServer.scala#L460-L493))
  instead of reproducing default resolution in configuration. HTTP then HTTPS are awaited sequentially. The
  [scripted test](https://github.com/playframework/playframework/blob/5b4eaf91caa1aa17ef5aca5f54a21067385bf2f6/dev-mode/sbt-plugin/src/sbt-test/play-sbt-plugin/shutdown-happy-path/test#L104-L120)
  records a slow request across SIGTERM (`checkRecordedRequestContains slow-request.txt DONE`); its staging sleeps are
  not an interleaving proof. The server source still puts logger/user-hook tasks in one phase; do not cite it as
  implementing every earlier ordering request.
- **2023 review / 2024 surviving source, PR 12210.** mkurz's substantive (APPROVED-state) [review](https://github.com/playframework/playframework/pull/12210#pullrequestreview-1767427947)
  identifies lost lazy timing ("in original scala code these were lazy vars"); ihostage
  [acknowledges](https://github.com/playframework/playframework/pull/12210#issuecomment-1842924715) "It's my fault while
  migrating from lazy vars". The rebased [Java source](https://github.com/playframework/playframework/blob/15cf5d6b8552c82f6cb07303eeb57c050af1d7fb/dev-mode/play-run-support/src/main/java/play/runsupport/DevServerRunner.java#L125-L163)
  places `RunHooksRunner.run(runHooks, RunHook::beforeStarted)` before user loader and eager reloader construction. Do
  not date this surviving source (March 2024) to the December 2023 review. [`PlayRunHookSpec`](https://github.com/playframework/playframework/blob/15cf5d6b8552c82f6cb07303eeb57c050af1d7fb/dev-mode/sbt-plugin/src/test/scala/play/sbt/PlayRunHookSpec.scala#L37-L37)
  checks wrapped original causes (`re.getCause must haveClass[HookMockException]`) and composite failures, not watcher
  ordering.

Reviewers' project ranks are unverified; substantive comments are attributed to their authors.

## Workflow

1. **Draw the ownership graph.** Loader → lifecycle → application, server → ActorSystem, and every
   `stop`/CoordinatedShutdown call. Separate production's shared system from development's potentially distinct systems
   and embedded/borrowed systems. Mark which owner remains reachable when `ApplicationLoader.load` throws before
   returning an Application. Do not delete that cleanup path because successful startup has `Application.stop`.
2. **Trace activation, not allocation syntax.** List `beforeStarted`, user `assetsClassLoader` invocation,
   watcher/reloader activation, server binding and `afterStarted`. A Scala lazy value translated to an eager Java
   constructor can run user code or start a watcher too early. Keep activation after successful `beforeStarted`;
   instrument both events. Separately inspect acquisition failures after that point: the observed port is not proof that
   every partial failure releases every resource.
3. **Separate once-only execution from completed cleanup.** Follow the `AtomicBoolean` gate, hook deque and memoized
   `Promise.future`. Every stop caller must observe actual final completion; a losing caller must not receive an
   already-successful Future while hooks still run. Preserve delayed hook invocation, LIFO sequence and continuation
   after an ordinary synchronous throw or failed Future.
4. **Make shutdown dependencies explicit.** Trace completion edges, not textual registration order. Tasks in one
   CoordinatedShutdown phase may run concurrently. If cleanup uses logging or another resource, compose the Futures or
   choose dependency-ordered phases. Avoid a task awaiting the same CoordinatedShutdown run that is awaiting that task.
   Do not "fix" a cycle by prematurely reporting external shutdown complete.
5. **Distinguish unbind from drain.** For full server termination, inspect how existing responses, HTTP/HTTPS bindings
   and the ActorSystem complete. Derive the termination timeout fallback through the owning shutdown API; retain an
   observable finite outer wait. Do not copy the five-second margin as universal. Inspect whether sequential binding
   termination can exhaust a phase budget.
6. **Review every consumer layer.** Run-support tests, sbt-plugin unit tests and scripted applications are separate.
   Check exception wrapping and original causes at the Java/Scala boundary. Record the changed invariant, minimal repair,
   retained behavior and missing regression cases before broadening the patch.

## Checks

Preserve: cleanup reachable before successful Application construction; startup hooks precede watcher/user-loader
activation; registered hooks run once in reverse order without overlap; stop completion follows the last hook; normal
hook failure does not skip remaining cleanup; shutdown dependencies have real completion edges.

False positives: internal AtomicBoolean/Promise mutation is part of the observed implementation. Independent same-phase
tasks may intentionally run concurrently. A hook that has genuinely completed may return an already-successful Future.
This does not imply new hook registration concurrent with shutdown is supported — establish that separately. Do not
claim Play historically satisfied every requested invariant: the January 2020 server still registers logger shutdown
and the user hook in the same phase; the historical repeated-stop test is not a simultaneous-stop race proof.

## Validation

Discover targets from the chosen checkout. After build authorization, `sbt 'projects'` and
`sbt 'show Play / Test / definedTests'` establish discovery; require the expected suites and nonzero execution. For a
checkout retaining the inspected core suite: `sbt 'Play/testOnly play.api.inject.DefaultApplicationLifecycleSpec'`.

Java-port consumer: `sbt 'Play-Run-Support/test' 'Sbt-Plugin/testOnly play.sbt.PlayRunHookSpec'`. A broader
`Sbt-Plugin/test` is needed when other plugin tests are affected. `Sbt-Plugin/scripted play-sbt-plugin/shutdown-happy-path`
requires matching locally published artifacts: `scriptedDependencies := (()), // drop Test/compile & publishLocal`
([BuildSettings](https://github.com/playframework/playframework/blob/99a7ea6ba74971c89af64dbd7a1f075fe4d51d63/project/BuildSettings.scala#L361-L361)).
Inspect the repository's publishing/test scripts first; never silently publish into a developer's ordinary cache.
Exercise development, production, embedded ownership, finite deadline expiration and relevant backends. A green schema
check proves none of these runtime properties.

### New regression designs (not historical execution claims)

**Pending completion across simultaneous callers.** Use the project's Specs2 and Future facilities, not a new effect
dependency. The last-to-be-invoked hook signals `entered` and returns an unreleased `gate.future`; earlier hooks record
a synchronized event trace. Release two worker calls to `stop()` from a common start barrier; collect both Futures
without awaiting. Await `entered`, assert both stop Futures are pending and the gated hook ran once, release the gate,
await both with finite timeouts, assert one complete LIFO trace. Use a thread-safe trace; a racy buffer is not an
oracle. Mutations to kill: immediate success to the losing caller; starting all hooks eagerly before sequencing their
Futures; completing the Promise before the final hook. Separately fail a hook synchronously and asynchronously and
assert later cleanup occurs; do not conflate fatal VM errors with recoverable hook failure. Exact Future identity is
observable in the historical code; at minimum preserve completion outcome and timing. Do not reject an equivalent
adapter returning a different wrapper Future unless identity is part of the target's contract.

**Partial startup and language-port timing.** Record `beforeStarted-enter`, `beforeStarted-exit`, `assets-loader`,
`watcher-start`, `afterStarted`. Assert no assets-loader/watcher event before beforeStarted succeeds. Inject failure in
beforeStarted; verify no watcher starts. Independently inject failure after an owned resource is acquired but before
Application is returned; the retained cleanup owner must still close it. This latter oracle requires tracing all
partial acquisitions and is not satisfied by the historical event order.

**Drain and shutdown graph.** Use a controllable slow response and an explicit request-start signal, not a sleep as
admission evidence. Trigger shutdown only after admission. Verify body completion before deadline in one case and
bounded termination in an over-deadline case. Inspect HTTP-only, HTTPS-only and combined bindings where supported. A
phase timeout and a per-binding timeout are distinct budgets. Verify the configured fallback and diagnostics without
assuming every backend exposes the same API. For dependent phase tasks, hold consumer cleanup and prove its provider
remains usable until release; independent tasks may run concurrently. Shared-ActorSystem self-waits and separate
development ActorSystems need different graphs.

### Build-era boundaries

The [2020 build](https://github.com/playframework/playframework/blob/37c10fab4938cd77d8bc939e9b115dc4058d8701/build.sbt)
and [2022 build](https://github.com/playframework/playframework/blob/97df2e2ca7d8f4bad3e9549c35b63ffae12eb38b/build.sbt)
have `Play`, `Sbt-Plugin` and `Play-Integration-Test`; integration uses `IntegrationTest`/`It`, not ordinary Test. The
2020 filter project ID is `Filters-Helpers` (not the Scala val name). The
[2024 build](https://github.com/playframework/playframework/blob/99a7ea6ba74971c89af64dbd7a1f075fe4d51d63/build.sbt)
uses Test for integration, `Play-Filters-Helpers`, Pekko backend naming, and a non-cross-built Java run-support
boundary. These are discovery examples, not commands proven on an arbitrary checkout.

- December 2020: sbt 1.4.6, Interplay 3.0.0. Plugin [versions](https://github.com/playframework/interplay/blob/07d559a14272b42bab5ce33929d28cdedeabedcf/src/main/scala/interplay/Versions.scala)
  2.12.10/2.13.1; [library defaults](https://github.com/playframework/interplay/blob/07d559a14272b42bab5ce33929d28cdedeabedcf/src/main/scala/interplay/PlayLibraryBase.scala#L22-L30)
  choose 2.13.1 unless `scala.version` overrides, cross-build 2.12.10. JVM 1.8 target; CI Java 11 and Java 8 jobs.
  Akka/Akka HTTP 2.6.10/10.1.13.
- December 2022: sbt 1.7.2, Interplay 3.1.0-RC6. The [plugin](https://github.com/playframework/interplay/blob/c708b2975edb7d9360d5dec76e28aabc69e2d7b8/src/main/scala/interplay/PlayLibraryBase.scala#L23-L34)
  defaults Scala 2.13.10; cross versions contain the selected version, not 2.12.17 merely because the meta-build uses
  it. Scala 3.2.1-RC4 selectable; a separate compilation CI job does not establish full Scala 3 runtime-test coverage.
  JVM release 11; CI Java 11/17. Akka/Akka HTTP 2.6.20/10.2.10 (system-property overridable).
- December 2024: Scala 2.13.15/3.3.4 and sbt-related 2.12.20, sbt 1.10.6, release 17, CI Java 17/21, Pekko 1.0.3 /
  Pekko HTTP 1.0.1. Verify each project's selected compiler and overrides before execution.

No historical artifact is installed or compiled by these instructions. No Scala/Java compilation or upstream tests ran
during authoring.

## Examples

- **Good.** In the pinned 2018 lifecycle, a CAS selects the single hook runner and all callers return the stored
  Promise's Future; hooks run inside the previous hook's `flatMap` with failure recovery. Accept an equivalent refactor
  only if a held hook keeps every stop result pending and remaining hooks execute LIFO after release.
- **Broken and correction.** A port constructs `DevServerReloader` and invokes `assetsClassLoader` before
  `beforeStarted`, calling this syntax-only. That recreates PR 12210's timing concern. Restore hook-before-activation
  ordering; test that a failing before-start hook produces no watcher activation. A second defect — returning
  `Future.successful(Done)` to subsequent stop callers — needs the shared pending completion, not an invocation
  counter; test both callers while the last hook is blocked.
- **Negative.** Moving an already-computed immutable port number into a local changes no callback or acquisition
  timing; do not demand a resource wrapper or effect migration. Two independent diagnostic tasks in one phase need no
  sequencing finding unless one demonstrably consumes a resource the other closes.

## Output

Per finding: `file:line`, severity, changed event/completion invariant, target versions/mode/backend, historical
evidence ID, current-source evidence, minimal correction and a discriminating test; state whether the test was executed,
proposed or unavailable. Return an explicit no-finding when the trace is preserved; list uncovered failure paths without
asserting undemonstrated leaks.

## Limitations

Historical review establishes concerns and bounded revisions, not universal leak freedom, cancellation guarantees, or
today's Akka/Pekko behavior. Future concurrency tests are inference-based extensions, not invented historical tests.
