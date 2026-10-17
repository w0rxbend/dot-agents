# Temporal contracts: evidence and discriminating oracles

## What was observed

- **2018, PR 8406:** gmethvin challenged cleanup that requires an already-constructed Application. ignasi35 revised toward an independently reachable lifecycle and explained that partial ActorSystem allocation was still a concern. This is a dependency/ownership constraint, not proof of universal leak freedom. The final [ApplicationLifecycle](https://github.com/playframework/playframework/blob/6059f791124fd979084567014e281b71780f648e/framework/src/play/src/main/scala/play/api/inject/ApplicationLifecycle.scala#L94-L134) uses a deque, CAS and a shared Promise. Its [tests](https://github.com/playframework/playframework/blob/6059f791124fd979084567014e281b71780f648e/framework/src/play/src/test/scala/play/api/inject/DefaultApplicationLifecycleSpec.scala#L19-L71) cover order, ordinary synchronous/asynchronous failure continuation and repeated calls, not barrier-controlled concurrent callers.
- **2020, PR 9970:** binding termination replaces unbind-only stopping. Timeout fallback uses `cs.timeout(PhaseServiceUnbind)` instead of trying to reproduce default resolution in configuration. The [scripted test](https://github.com/playframework/playframework/blob/5b4eaf91caa1aa17ef5aca5f54a21067385bf2f6/dev-mode/sbt-plugin/src/sbt-test/play-sbt-plugin/shutdown-happy-path/test#L104-L120) records a slow request across SIGTERM; its staging sleeps are not an interleaving proof. The server source still puts logger/user-hook tasks in one phase; it must not be cited as implementing every earlier ordering request.
- **2023 review / 2024 surviving source, PR 12210:** mkurz's substantive approved review identifies lost lazy timing; ihostage acknowledges the mistake. The rebased [Java source](https://github.com/playframework/playframework/blob/15cf5d6b8552c82f6cb07303eeb57c050af1d7fb/dev-mode/play-run-support/src/main/java/play/runsupport/DevServerRunner.java#L125-L163) places beforeStarted before user loader and eager reloader construction. Do not date this surviving source to the 2023 review. `PlayRunHookSpec` checks wrapped original causes, not watcher ordering.

## New regression designs, not historical execution claims

### Pending completion across simultaneous callers

Use the project's existing Specs2 and Future facilities, not a new effect dependency. Prepare a lifecycle whose last-to-be-invoked hook signals `entered` and returns an unreleased `gate.future`. Register earlier hooks to record a synchronized event trace. Release two worker calls to `stop()` from a common start barrier; collect both returned Futures without awaiting their completion. Await `entered`, assert each returned stop Future is still pending, assert the gated hook has run once, then release the gate. Await both with finite test timeouts and assert one complete LIFO trace. Use a thread-safe trace if callers/hooks run on different threads; a racy test buffer is not an oracle.

Mutations this must kill: returning immediate success to the losing caller; starting all hooks eagerly before sequencing their Futures; completing the Promise before the final hook. Also separately fail a hook synchronously and asynchronously and assert later cleanup occurs. Do not conflate fatal VM errors with recoverable hook failure.

The implementation's exact Future object identity is observable in the historical code; at minimum preserve the public completion outcome and timing. Do not reject an equivalent adapter merely because it returns a different wrapper Future unless identity itself is part of the target's contract.

### Partial startup and language-port timing

Record `beforeStarted-enter`, `beforeStarted-exit`, `assets-loader`, `watcher-start`, and `afterStarted`. Assert no assets-loader/watcher event before beforeStarted succeeds. Inject failure in beforeStarted and verify no watcher starts. Independently inject failure after an owned resource is acquired but before Application is returned; the retained cleanup owner must still close that resource. This latter oracle requires tracing all partial acquisitions and is not satisfied just by the historical event order.

### Drain and shutdown graph

Use a controllable slow response and an explicit request-start signal, not a sleep as evidence of admission. Trigger shutdown only after admission. Verify body completion before deadline in one case and bounded termination in an over-deadline case. Inspect HTTP-only, HTTPS-only and combined bindings where supported. A phase timeout and a per-binding timeout are distinct budgets. Verify the configured fallback and observable diagnostics without assuming every backend exposes the same API.

For dependent phase tasks, hold consumer cleanup and prove its provider remains usable until release. For independent tasks, concurrency is acceptable. Shared ActorSystem self-waits and separate development ActorSystems need different graphs.

## Build-era boundaries

The [2020 build](https://github.com/playframework/playframework/blob/37c10fab4938cd77d8bc939e9b115dc4058d8701/build.sbt) and [2022 build](https://github.com/playframework/playframework/blob/97df2e2ca7d8f4bad3e9549c35b63ffae12eb38b/build.sbt) have `Play`, `Sbt-Plugin` and `Play-Integration-Test`; integration uses `IntegrationTest`/`It`, not ordinary Test. The [2024 build](https://github.com/playframework/playframework/blob/99a7ea6ba74971c89af64dbd7a1f075fe4d51d63/build.sbt) uses Test for integration and Pekko backend naming. These are discovery examples, not a command proven on an arbitrary checkout.

Version inheritance was inspected, not guessed from calendar years:

- December 2020 pins sbt 1.4.6 and Interplay 3.0.0. That plugin's [versions](https://github.com/playframework/interplay/blob/07d559a14272b42bab5ce33929d28cdedeabedcf/src/main/scala/interplay/Versions.scala) define 2.12.10/2.13.1; its [library defaults](https://github.com/playframework/interplay/blob/07d559a14272b42bab5ce33929d28cdedeabedcf/src/main/scala/interplay/PlayLibraryBase.scala#L22-L30) choose 2.13.1 unless `scala.version` overrides it and cross-build with 2.12.10. Play sets Scala JVM 1.8 target; CI has Java 11 and Java 8 compatibility jobs. Akka/Akka HTTP snapshot defaults: 2.6.10/10.1.13.
- December 2022 pins sbt 1.7.2 and Interplay 3.1.0-RC6. The [plugin](https://github.com/playframework/interplay/blob/c708b2975edb7d9360d5dec76e28aabc69e2d7b8/src/main/scala/interplay/PlayLibraryBase.scala#L23-L34) chooses Scala 2.13.10 by default; cross versions contain the selected version, not 2.12.17 merely because the meta-build uses it. Scala 3.2.1-RC4 is selectable; its presence and a separate compilation CI job do not establish full Scala 3 runtime-test coverage. JVM release 11; runtime CI Java 11/17. Akka/Akka HTTP defaults: 2.6.20/10.2.10.
- December 2024 declares Scala 2.13.15/3.3.4 and sbt-related 2.12.20, sbt 1.10.6, release 17, CI Java 17/21, Pekko 1.0.3/Pekko HTTP 1.0.1. Verify each project's selected compiler and overrides before execution.

No historical artifact is currently installed or compiled by these instructions. A source-declared selector is a plan until actual discovery and execution confirm it.
