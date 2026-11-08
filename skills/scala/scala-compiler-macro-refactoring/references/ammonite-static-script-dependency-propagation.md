# Ammonite (com-lihaoyi/Ammonite): static script dependency propagation

Originally `scala-ammonite-static-script-dependency-propagation`. Evidence: [evidence/scala-ammonite-static-script-dependency-propagation.json](evidence/scala-ammonite-static-script-dependency-propagation.json) (claims `c-static-repos`, `c-isolated-compile`).

## Scope

Use when import hook works interactively but fails through BSP, when extending `Script.Dependencies`, or when sharing dependency-resolution code between Interpreter and static script APIs. Review full path from syntax to dependent script's compiler inputs, not handler alone.

Not for: REPL closure serialization (see [ammonite-symbol-derived-closure-capture.md](ammonite-symbol-derived-closure-capture.md)), generic Mill module graph, ordinary application dependency upgrades. Do not silently migrate stateful Interpreter to isolated BSP semantics. Different runtime classloader topology is not automatically defective. Historical Scala-2-built Scala-3 macro bridge is separate compiler/bootstrap problem, not a reason to rewrite all script artifact suffixes.

## Prerequisites

Read actual build: compiler patch version, BSP/Coursier versions, hook ADT, static processor, resolver, integration harness. PRs 1053/1090 establish this boundary on JVM Scala 2. At June 2020 PR 1090 head, primary build cells: Scala 2.12.11 and 2.13.2, BSP 2.0.0-M6, coursier-interface 0.0.21, uTest 0.7.3, launcher default Mill 0.7.0. CI pairs 2.12.11 with JDK 8/11 and 2.13.2 with JDK 8; not universal supported combinations.

Track injected baseline classpath/repositories separately from script imports. Static inspection is not an effect-free sandbox: hooks can do work, resolution can access network, compilation can run compiler plugins/macros. Keep direct APIs and existing BSP Future/CompletableFuture adapter; do not retrofit CE, ZIO, or Ox.

## Workflow

1. **Draw two consumers.** Map hook syntax to result, then separately to Interpreter mutation and static `Script` metadata. For `$repo`, PR 1090 returns `Result.Repo`; Interpreter updates its repositories while `Script.dependencies` produces `extraRepositories`. Interactive-only fix leaves IDE path incomplete.
2. **Audit every metadata transformation.** Follow block extraction, folding, `Dependencies.+`, `noDuplicates`. Carry repository metadata alongside ordinary dependencies, JARs, plugin dependencies, plugin JARs. Keep ordered combination and deduplication semantics; do not replace sequences with unordered sets only because field sounds set-like.
3. **Follow imported scripts to resolution.** Historically `ScriptProcessor.jarDependencies` merges current script with its dependencies and passes `defaultRepositories ++ deps.extraRepositories` to loader; `jarPluginDependencies` does same for plugin artifacts. Check both sibling paths. Metadata must survive merges without changing which script depends on which.
4. **Separate visibility from execution architecture.** Dependent script receives its imported scripts' dependencies; imported script does not acquire unrelated imports from caller. Keep explicitly configured baseline inputs. BSP proposal deliberately coexisted with old Interpreter; its author disputed that isolated compilation requires a classloader DAG.
5. **Keep public interface narrow.** Before adding public mutation method, check existing API and who consumes result. PR 1090 removed proposed interface expansion but kept private synchronized `addRepository` helper. Do not ban helpers by name or expose mutable session state for static-inspection convenience.
6. **Test dependent target, not only parsing.** Use `main.sc -> lib.sc`, with artifact available only from repository `lib.sc` declares. Assert artifact in BSP target classpath, successful compilation, expected diagnostics. Add inverse case: dependency declared only by `main.sc` must not rescue otherwise invalid `lib.sc`. Inverse case is recommended oracle derived from PR 1053's semantics, not claimed historical test run.
7. **Keep regression independent of ambient caches.** Pin fixture source at tested SHA. For current authorized tests, prefer tiny controlled repository and isolated resolver cache. Remove repository hook and require failure; restore it and require success. If using historical JitPack fixture, first record exact bytes/checksums and availability. Warm cache or mutable remote version must not let missing-hook mutation pass unnoticed.

## Checks

- Repository metadata reaches ordinary and plugin resolution after dependency traversal. Do not confuse having a `Repo` case with consuming it downstream.
- Static dependency discovery runs without evaluating arbitrary script bodies. Historical processor calls hooks through dummy interpreter interface: architectural boundary, not security guarantee for custom hooks.
- Check `ScriptCompiler` compile inputs and BSP `scriptScalacOptions`, not only `Script.scala`. Historical server combines target directories, resolved JARs, injected initial classpath.

## False positives

Stateful REPL execution is intentional. Private helper is not public API widening. Generated inert imports are not the dependency-resolution effect itself. Multi-stage scripts configuring later stages dynamically need separately stated contract, not assumed static parity. Unrelated Interpreter refactor keeping sequential session-dependent resolution, with private `addRepository` helper remaining, does not warrant demanding BSP isolation everywhere or new classloader DAG. Fully qualified ordinary application library import does not trigger this procedure.

## Validation

No upstream build ran during research. In separately authorized checkout, inspect launcher overrides (`MILL_VERSION`, `.mill-version`), build imports, Git tag/master requirements, JDK, network fixtures before running anything. Do not run historical release/publish CI stages.

At SHA `7017cb94d6f95c7405696affd5887d1e43116aaa`, observed CI invokes `./mill -i unitTest`; build reads `TRAVIS_SCALA_VERSION` and dispatches actual cross modules, including `amm(scalaVersion).test.test()()`. With matching toolchain and prerequisites, concrete historical command is `TRAVIS_SCALA_VERSION=2.13.2 ./mill -i unitTest`. Broad unit-test command, not fabricated BSP-only selector. For narrower current run, discover checkout's `amm` test module and uTest filtering syntax before choosing suite.

Inspect `AmmoniteBuildServerTests`' `multi` case and interactive/static resolver tests. Require evidence they execute on supported cells: PR 1090 removed a Scala-2.11 guard precisely because it disabled the regression. Record classpath contents, compile status, diagnostics, and failure after removing hook. Exact historical task-event order is observed oracle, not universal requirement for newly parallelized compiler.

## Examples

**Good.** `lib.sc` declares repository and artifact from it; `main.sc` imports `lib.sc`. Hook yields metadata, composition keeps it, main BSP target resolves artifact before compilation. PR 1090's pinned `lib3.sc` uses `com.github.jupyter:jvm-repr:0.4.0`; its `multi` test checks JitPack classpath suffix, successful compilation, empty diagnostics.

**Broken and correction.** Patch adds REPL handler but ignores `Result.Repo` in `Script.dependencies`, or loses `extraRepositories` in `noDuplicates`. Interactive imports work; IDE cannot compile dependent script. Correction: trace and repair extraction, composition, ordinary/plugin resolution, dependent-target classpath reporting. Remove obsolete `scala2_11` test guard only after identifying supported matrix; prove regression runs and fails with hook removed.

## Output additions

Include path table from hook through extraction/composition/resolution to BSP response. Report compiler/JDK/resolver versions, actual test discovery, external-fixture prerequisites, what remains unexecuted.

## Limitations

Historical fixture pins source and artifact coordinates, not immutable downloaded JAR bytes; remote availability and cache-independent failure not measured. Static isolation allows explicit baseline dependencies; it does not guarantee process isolation or safe execution of untrusted hooks. Scala 3, later BSP APIs and multi-stage semantics need fresh source inspection. 2022 macro artifact swap is not part of this procedure and was gone from inspected 2024 build.

## Sources

- [PR 1053: static versus Interpreter semantics](https://github.com/com-lihaoyi/Ammonite/pull/1053#issuecomment-605952752) and [why a loader DAG is not mandatory](https://github.com/com-lihaoyi/Ammonite/pull/1053#issuecomment-607971851).
- [PR 1090: inherited repository review](https://github.com/com-lihaoyi/Ammonite/pull/1090#issuecomment-638956149), [interface boundary](https://github.com/com-lihaoyi/Ammonite/pull/1090#discussion_r435401057), and [disabled regression](https://github.com/com-lihaoyi/Ammonite/pull/1090#discussion_r435974671).
- [Pinned ordinary/plugin resolution](https://github.com/com-lihaoyi/Ammonite/blob/7017cb94d6f95c7405696affd5887d1e43116aaa/amm/interp/src/main/scala/ammonite/interp/script/ScriptProcessor.scala#L123-L143).
