# Play Framework: partial startup and shutdown completion (originally scala-play-partial-startup-shutdown-completion)

Evidence: [evidence/scala-play-partial-startup-shutdown-completion.json](evidence/scala-play-partial-startup-shutdown-completion.json)
(claims `c-lifecycle-temporal`, `c-lifecycle-completion`, `c-shutdown-budget`, `c-build-discovery`).

Review observable event sequence, not just signatures. Introduces no effect runtime.

## Scope

Changes to `ApplicationLifecycle`, application loading, `DevServerRunner`, server stop wiring or shutdown-task
ordering: refactors moving construction across hooks, changing what `stop()` completion means, or replacing unbinding
with another termination operation.

Not Cats Effect/ZIO/Ox resource recipe, not reason to migrate Play's sbt build. Pure configuration extraction without
moved callbacks/acquisition is not lifecycle defect. Listener-only administrative unbinding is not necessarily
whole-server shutdown. Global logger isolation is adjacent research, not guaranteed here.

## Prerequisites

Record target SHA, Play line, Scala/compiler/JDK, server backend, mode, ActorSystem owners. Read actual `build.sbt`,
`project/build.properties`, build plugins/settings, CI selectors, test classes. Preserve Scala Future, Java
CompletionStage, established Akka/Pekko namespace. Layouts: 2018 `framework/src`; 2020 `core`/`transport`; 2024
run-support implementation in Java, sbt-plugin consumers still Scala. Historical dependency defaults are not versions
of every PR in same calendar year. Get separate authorization and isolated checkout/cache before executing upstream
build.

## What was observed

- **2018, PR 8406.** gmethvin, [partial startup](https://github.com/playframework/playframework/pull/8406#issuecomment-389230012):
  "`Application#stop()` requires you to have an application instance. If an exception is thrown before the app is
  initialized, you may still have some resources to…" — ignasi35 revised toward independently reachable lifecycle,
  explained partial ActorSystem allocation was still concern. Dependency/ownership constraint, not proof of universal
  leak freedom. gmethvin, [dependency direction](https://github.com/playframework/playframework/pull/8406#discussion_r189422684):
  "The Play application depends on the `ActorSystem` … so `Play.stop` should invoke `CoordinatedShutdown` and not the
  other" — later discussion distinguished shared production ActorSystems from separate development systems. TimMoore,
  [same-phase ordering](https://github.com/playframework/playframework/pull/8406#discussion_r193607508): it "shouldn't
  happen concurrently with the `"user-provided-server-stop-hook"` task" — reviewer guidance, not proven invariant.
  patriknw, [bounded wait](https://github.com/playframework/playframework/pull/8406#discussion_r193638555): "I'd not use
  `Duration.Inf` because that would result in the worst kind error handling … complete silence and hanging process";
  gmethvin later requested explanatory comment. Five-second margin is historical policy, not universal.
  Final [ApplicationLifecycle](https://github.com/playframework/playframework/blob/6059f791124fd979084567014e281b71780f648e/framework/src/play/src/main/scala/play/api/inject/ApplicationLifecycle.scala#L94-L134)
  uses deque, CAS (`if (started.compareAndSet(false, true))`) and shared Promise; hooks chain via `flatMap`, recovering
  synchronous throws and failed Futures. Its
  [tests](https://github.com/playframework/playframework/blob/6059f791124fd979084567014e281b71780f648e/framework/src/play/src/test/scala/play/api/inject/DefaultApplicationLifecycleSpec.scala#L19-L71)
  cover order (`List(3, 2, 1)`), ordinary synchronous/asynchronous failure continuation, repeated calls; not
  barrier-controlled concurrent callers.
- **2020, PR 9970.** Binding termination replaces unbind-only stopping. Timeout fallback uses
  `cs.timeout(PhaseServiceUnbind)` ([source](https://github.com/playframework/playframework/blob/5b4eaf91caa1aa17ef5aca5f54a21067385bf2f6/transport/server/play-akka-http-server/src/main/scala/play/core/server/AkkaHttpServer.scala#L460-L493))
  instead of reproducing default resolution in configuration. HTTP then HTTPS awaited sequentially. The
  [scripted test](https://github.com/playframework/playframework/blob/5b4eaf91caa1aa17ef5aca5f54a21067385bf2f6/dev-mode/sbt-plugin/src/sbt-test/play-sbt-plugin/shutdown-happy-path/test#L104-L120)
  records slow request across SIGTERM (`checkRecordedRequestContains slow-request.txt DONE`); its staging sleeps are
  not interleaving proof. Server source still puts logger/user-hook tasks in one phase; do not cite it as implementing
  every earlier ordering request.
- **2023 review / 2024 surviving source, PR 12210.** mkurz's substantive (APPROVED-state) [review](https://github.com/playframework/playframework/pull/12210#pullrequestreview-1767427947)
  identifies lost lazy timing ("in original scala code these were lazy vars"); ihostage
  [acknowledges](https://github.com/playframework/playframework/pull/12210#issuecomment-1842924715) "It's my fault while
  migrating from lazy vars". Rebased [Java source](https://github.com/playframework/playframework/blob/15cf5d6b8552c82f6cb07303eeb57c050af1d7fb/dev-mode/play-run-support/src/main/java/play/runsupport/DevServerRunner.java#L125-L163)
  places `RunHooksRunner.run(runHooks, RunHook::beforeStarted)` before user loader and eager reloader construction. Do
  not date this surviving source (March 2024) to December 2023 review. [`PlayRunHookSpec`](https://github.com/playframework/playframework/blob/15cf5d6b8552c82f6cb07303eeb57c050af1d7fb/dev-mode/sbt-plugin/src/test/scala/play/sbt/PlayRunHookSpec.scala#L37-L37)
  checks wrapped original causes (`re.getCause must haveClass[HookMockException]`) and composite failures, not watcher
  ordering.

Reviewers' project ranks unverified; substantive comments attributed to their authors.

## Workflow

1. **Draw the ownership graph.** Loader → lifecycle → application, server → ActorSystem, every
   `stop`/CoordinatedShutdown call. Separate production's shared system from development's potentially distinct
   systems and embedded/borrowed systems. Mark which owner stays reachable when `ApplicationLoader.load` throws before
   returning Application. Do not delete that cleanup path because successful startup has `Application.stop`.
2. **Trace activation, not allocation syntax.** List `beforeStarted`, user `assetsClassLoader` invocation,
   watcher/reloader activation, server binding, `afterStarted`. Scala lazy value translated to eager Java constructor
   can run user code or start watcher too early. Keep activation after successful `beforeStarted`; instrument both
   events. Separately inspect acquisition failures after that point: observed port does not prove every partial
   failure releases every resource.
3. **Separate once-only execution from completed cleanup.** Follow `AtomicBoolean` gate, hook deque, memoized
   `Promise.future`. Every stop caller must observe actual final completion. Losing caller must not get
   already-successful Future while hooks still run. Preserve delayed hook invocation, LIFO sequence, continuation after
   ordinary synchronous throw or failed Future.
4. **Make shutdown dependencies explicit.** Trace completion edges, not textual registration order. Tasks in one
   CoordinatedShutdown phase may run concurrently. If cleanup uses logging or another resource, compose the Futures or
   pick dependency-ordered phases. Avoid task awaiting same CoordinatedShutdown run that awaits that task. Do not "fix"
   cycle by prematurely reporting external shutdown complete.
5. **Distinguish unbind from drain.** For full server termination, inspect how existing responses, HTTP/HTTPS bindings
   and ActorSystem complete. Derive termination timeout fallback through owning shutdown API; keep observable finite
   outer wait. Do not copy five-second margin as universal. Check whether sequential binding termination can exhaust
   phase budget.
6. **Review every consumer layer.** Run-support tests, sbt-plugin unit tests, scripted applications are separate.
   Check exception wrapping and original causes at Java/Scala boundary. Before broadening patch, record changed
   invariant, minimal repair, retained behavior, missing regression cases.

## Checks

Preserve: cleanup reachable before successful Application construction; startup hooks precede watcher/user-loader
activation; registered hooks run once, reverse order, no overlap; stop completion follows last hook; normal hook
failure does not skip remaining cleanup; shutdown dependencies have real completion edges.

False positives: internal AtomicBoolean/Promise mutation is part of observed implementation. Independent same-phase
tasks may intentionally run concurrently. Genuinely completed hook may return already-successful Future. This does not
imply support for new hook registration concurrent with shutdown; establish that separately. Do not claim Play
historically satisfied every requested invariant: January 2020 server still registers logger shutdown and user hook in
same phase; historical repeated-stop test is not simultaneous-stop race proof.

## Validation

Discover targets from chosen checkout. After build authorization, `sbt 'projects'` and
`sbt 'show Play / Test / definedTests'` establish discovery; require expected suites and nonzero execution. For
checkout keeping inspected core suite: `sbt 'Play/testOnly play.api.inject.DefaultApplicationLifecycleSpec'`.

Java-port consumer: `sbt 'Play-Run-Support/test' 'Sbt-Plugin/testOnly play.sbt.PlayRunHookSpec'`. Broader
`Sbt-Plugin/test` needed when other plugin tests are affected. `Sbt-Plugin/scripted play-sbt-plugin/shutdown-happy-path`
requires matching locally published artifacts: `scriptedDependencies := (()), // drop Test/compile & publishLocal`
([BuildSettings](https://github.com/playframework/playframework/blob/99a7ea6ba74971c89af64dbd7a1f075fe4d51d63/project/BuildSettings.scala#L361-L361)).
Inspect repository's publishing/test scripts first; never silently publish into developer's ordinary cache. Exercise
development, production, embedded ownership, finite deadline expiration, relevant backends. Green schema check proves
none of these runtime properties.

### New regression designs (not historical execution claims)

**Pending completion across simultaneous callers.** Use project's Specs2 and Future facilities, not new effect
dependency. Last-to-be-invoked hook signals `entered`, returns unreleased `gate.future`; earlier hooks record
synchronized event trace. Release two worker calls to `stop()` from common start barrier; collect both Futures without
awaiting. Await `entered`; assert both stop Futures pending and gated hook ran once; release gate; await both with
finite timeouts; assert one complete LIFO trace. Use thread-safe trace; racy buffer is not oracle. Mutations to kill:
immediate success to losing caller; starting all hooks eagerly before sequencing their Futures; completing Promise
before final hook. Separately fail hook synchronously and asynchronously, assert later cleanup occurs; do not conflate
fatal VM errors with recoverable hook failure. Exact Future identity is observable in historical code; at minimum
preserve completion outcome and timing. Do not reject equivalent adapter returning different wrapper Future unless
identity is part of target's contract.

**Partial startup and language-port timing.** Record `beforeStarted-enter`, `beforeStarted-exit`, `assets-loader`,
`watcher-start`, `afterStarted`. Assert no assets-loader/watcher event before beforeStarted succeeds. Inject failure in
beforeStarted; verify no watcher starts. Independently inject failure after owned resource is acquired but before
Application is returned; retained cleanup owner must still close it. This latter oracle requires tracing all partial
acquisitions; historical event order does not satisfy it.

**Drain and shutdown graph.** Use controllable slow response and explicit request-start signal, not sleep as admission
evidence. Trigger shutdown only after admission. Verify body completion before deadline in one case, bounded
termination in over-deadline case. Inspect HTTP-only, HTTPS-only and combined bindings where supported. Phase timeout
and per-binding timeout are distinct budgets. Verify configured fallback and diagnostics without assuming every backend
exposes same API. For dependent phase tasks, hold consumer cleanup and prove its provider stays usable until release;
independent tasks may run concurrently. Shared-ActorSystem self-waits and separate development ActorSystems need
different graphs.

### Build-era boundaries

[2020 build](https://github.com/playframework/playframework/blob/37c10fab4938cd77d8bc939e9b115dc4058d8701/build.sbt)
and [2022 build](https://github.com/playframework/playframework/blob/97df2e2ca7d8f4bad3e9549c35b63ffae12eb38b/build.sbt)
have `Play`, `Sbt-Plugin` and `Play-Integration-Test`; integration uses `IntegrationTest`/`It`, not ordinary Test.
2020 filter project ID is `Filters-Helpers` (not Scala val name).
[2024 build](https://github.com/playframework/playframework/blob/99a7ea6ba74971c89af64dbd7a1f075fe4d51d63/build.sbt)
uses Test for integration, `Play-Filters-Helpers`, Pekko backend naming, non-cross-built Java run-support boundary.
These are discovery examples, not commands proven on arbitrary checkout.

- December 2020: sbt 1.4.6, Interplay 3.0.0. Plugin [versions](https://github.com/playframework/interplay/blob/07d559a14272b42bab5ce33929d28cdedeabedcf/src/main/scala/interplay/Versions.scala)
  2.12.10/2.13.1; [library defaults](https://github.com/playframework/interplay/blob/07d559a14272b42bab5ce33929d28cdedeabedcf/src/main/scala/interplay/PlayLibraryBase.scala#L22-L30)
  choose 2.13.1 unless `scala.version` overrides, cross-build 2.12.10. JVM 1.8 target; CI Java 11 and Java 8 jobs.
  Akka/Akka HTTP 2.6.10/10.1.13.
- December 2022: sbt 1.7.2, Interplay 3.1.0-RC6. The [plugin](https://github.com/playframework/interplay/blob/c708b2975edb7d9360d5dec76e28aabc69e2d7b8/src/main/scala/interplay/PlayLibraryBase.scala#L23-L34)
  defaults Scala 2.13.10; cross versions contain selected version, not 2.12.17 merely because meta-build uses it.
  Scala 3.2.1-RC4 selectable; separate compilation CI job does not establish full Scala 3 runtime-test coverage.
  JVM release 11; CI Java 11/17. Akka/Akka HTTP 2.6.20/10.2.10 (system-property overridable).
- December 2024: Scala 2.13.15/3.3.4 and sbt-related 2.12.20, sbt 1.10.6, release 17, CI Java 17/21, Pekko 1.0.3 /
  Pekko HTTP 1.0.1. Verify each project's selected compiler and overrides before execution.

These instructions install or compile no historical artifact. No Scala/Java compilation or upstream tests ran during
authoring.

## Examples

- **Good.** Pinned 2018 lifecycle: CAS selects single hook runner, all callers return stored Promise's Future; hooks
  run inside previous hook's `flatMap` with failure recovery. Accept equivalent refactor only if held hook keeps every
  stop result pending and remaining hooks execute LIFO after release.
- **Broken and correction.** Port constructs `DevServerReloader` and invokes `assetsClassLoader` before
  `beforeStarted`, calling this syntax-only. That recreates PR 12210's timing concern. Restore hook-before-activation
  ordering; test that failing before-start hook produces no watcher activation. Second defect, returning
  `Future.successful(Done)` to subsequent stop callers, needs shared pending completion, not invocation counter; test
  both callers while last hook is blocked.
- **Negative.** Moving already-computed immutable port number into local changes no callback or acquisition timing; do
  not demand resource wrapper or effect migration. Two independent diagnostic tasks in one phase need no sequencing
  finding unless one demonstrably consumes resource the other closes.

## Output

Per finding: `file:line`, severity, changed event/completion invariant, target versions/mode/backend, historical
evidence ID, current-source evidence, minimal correction, discriminating test; state whether test was executed,
proposed or unavailable. Return explicit no-finding when trace is preserved. List uncovered failure paths without
asserting undemonstrated leaks.

## Limitations

Historical review establishes concerns and bounded revisions, not universal leak freedom, cancellation guarantees, or
today's Akka/Pekko behavior.
