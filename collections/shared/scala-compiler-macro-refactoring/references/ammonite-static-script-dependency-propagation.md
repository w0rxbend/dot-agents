# Ammonite (com-lihaoyi/Ammonite): static script dependency propagation

Originally `scala-ammonite-static-script-dependency-propagation`. Evidence: [evidence/scala-ammonite-static-script-dependency-propagation.json](evidence/scala-ammonite-static-script-dependency-propagation.json) (claims `c-static-repos`, `c-isolated-compile`).

## Scope

Use when an import hook works interactively but fails through BSP, when extending `Script.Dependencies`, or when sharing dependency-resolution code between the Interpreter and static script APIs. Review the complete path from syntax to a dependent script's compiler inputs, rather than the handler alone.

Not for: REPL closure serialization (see [ammonite-symbol-derived-closure-capture.md](ammonite-symbol-derived-closure-capture.md)), a generic Mill module graph, or ordinary application dependency upgrades. Do not silently migrate the stateful Interpreter to isolated BSP semantics. A different runtime classloader topology is not automatically defective. The historical Scala-2-built Scala-3 macro bridge is a separate compiler/bootstrap problem, not a reason to rewrite all script artifact suffixes.

## Prerequisites

Read the actual build and identify compiler patch version, BSP/Coursier versions, hook ADT, static processor, resolver, and integration harness. PRs 1053/1090 establish this boundary on JVM Scala 2. At the June 2020 PR 1090 head, the primary build cells are Scala 2.12.11 and 2.13.2, BSP 2.0.0-M6, coursier-interface 0.0.21, uTest 0.7.3, and a launcher default of Mill 0.7.0. CI pairs 2.12.11 with JDK 8/11 and 2.13.2 with JDK 8; these are not universal supported combinations.

Identify injected baseline classpath/repositories separately from script imports. Static inspection is not an effect-free sandbox: hooks can perform work, resolution can access the network, and compilation can execute compiler plugins/macros. Preserve direct APIs and the existing BSP Future/CompletableFuture adapter; do not retrofit CE, ZIO, or Ox.

## Workflow

1. **Draw the two consumers.** Map hook syntax to its result, then separately to Interpreter mutation and static `Script` metadata. For `$repo`, PR 1090 returns `Result.Repo`; the Interpreter updates its repositories while `Script.dependencies` produces `extraRepositories`. An interactive-only fix leaves the IDE path incomplete.
2. **Audit every metadata transformation.** Follow block extraction, folding, `Dependencies.+`, and `noDuplicates`. Keep repository metadata alongside ordinary dependencies, JARs, plugin dependencies, and plugin JARs. Preserve ordered combination and deduplication semantics; do not replace sequences with unordered sets merely because the field sounds set-like.
3. **Follow imported scripts to resolution.** In the historical implementation, `ScriptProcessor.jarDependencies` merges the current script plus its dependencies and passes `defaultRepositories ++ deps.extraRepositories` to the loader. `jarPluginDependencies` does the same for plugin artifacts. Check both sibling paths and ensure metadata survives merges without changing which script depends on which.
4. **Separate visibility from execution architecture.** A dependent script receives its imported scripts' dependencies; an imported script does not acquire unrelated imports from its caller. Preserve explicitly configured baseline inputs. The BSP proposal deliberately coexisted with the old Interpreter, and its author disputed that isolated compilation requires a classloader DAG.
5. **Keep the public interface narrow.** Before adding a public mutation method, check the existing API and who consumes the result. PR 1090 removed the proposed interface expansion but kept a private synchronized `addRepository` helper. Do not ban helpers by name or expose mutable session state to make static inspection convenient.
6. **Test the dependent target, not only parsing.** Use `main.sc -> lib.sc`, with an artifact available only from the repository declared by `lib.sc`. Assert the artifact in the BSP target classpath, successful compilation, and expected diagnostics. Add an inverse case: a dependency declared only by `main.sc` must not rescue an otherwise invalid `lib.sc`. The latter is a recommended oracle derived from PR 1053's semantics, not a claimed historical test run.
7. **Keep the regression independent of ambient caches.** Pin fixture source at the tested SHA. For current authorized tests, prefer a tiny controlled repository and isolated resolver cache; remove the repository hook and require failure, then restore it and require success. If using the historical JitPack fixture, record exact bytes/checksums and availability first. A warm cache or mutable remote version must not make the missing-hook mutation pass unnoticed.

## Checks

- Repository metadata reaches both ordinary and plugin resolution after dependency traversal. Do not confuse having a `Repo` case with actually consuming it downstream.
- Static dependency discovery happens without evaluating arbitrary script bodies. The historical processor calls hooks through a dummy interpreter interface; that is an architectural boundary, not a security guarantee for custom hooks.
- Check `ScriptCompiler` compile inputs and BSP `scriptScalacOptions`, not only `Script.scala`. The historical server combines target directories, resolved JARs, and injected initial classpath.

## False positives

Stateful REPL execution is intentional; a private helper is not public API widening; generated inert imports are not the dependency-resolution effect itself. Multi-stage scripts that configure later stages dynamically need a separately stated contract, not assumed static parity. An unrelated Interpreter refactor that keeps sequential session-dependent resolution, with a private `addRepository` helper remaining, does not warrant demanding BSP isolation everywhere or a new classloader DAG. A fully qualified ordinary application library import does not trigger this procedure.

## Validation

No upstream build was executed during research. In a separately authorized checkout, inspect launcher overrides (`MILL_VERSION`, `.mill-version`), build imports, Git tag/master requirements, JDK, and network fixtures before running anything. Do not run historical release/publish CI stages.

At SHA `7017cb94d6f95c7405696affd5887d1e43116aaa`, the observed CI invokes `./mill -i unitTest`; the build reads `TRAVIS_SCALA_VERSION` and dispatches the actual cross modules, including `amm(scalaVersion).test.test()()`. With the corresponding toolchain and prerequisites, the concrete historical command is `TRAVIS_SCALA_VERSION=2.13.2 ./mill -i unitTest`. This is a broad unit-test command, not a fabricated BSP-only selector. For a narrower current run, discover the selected checkout's `amm` test module and uTest filtering syntax before choosing a suite.

Inspect `AmmoniteBuildServerTests`' `multi` case and the interactive/static resolver tests. Require evidence that those cases execute on supported cells: PR 1090 removed a Scala-2.11 guard precisely because it disabled the regression. Record classpath contents, compile status, diagnostics, and failure after removing the hook. Exact historical task-event order is an observed oracle, not a universal requirement for a newly parallelized compiler.

## Examples

**Good.** `lib.sc` declares a repository and an artifact from it; `main.sc` imports `lib.sc`. The hook yields metadata, composition retains it, and the main BSP target resolves the artifact before compilation. PR 1090's pinned `lib3.sc` uses `com.github.jupyter:jvm-repr:0.4.0`; its `multi` test checks the JitPack classpath suffix, successful compilation, and empty diagnostics. For a new regression use controlled fixture bytes rather than assuming that remote artifact remains available.

**Broken and correction.** A patch adds the REPL handler but ignores `Result.Repo` in `Script.dependencies`, or loses `extraRepositories` in `noDuplicates`. Interactive imports work while the IDE cannot compile the dependent script. Correction: trace and repair extraction, composition, ordinary/plugin resolution, and dependent-target classpath reporting. Remove an obsolete `scala2_11` test guard only after identifying the supported matrix; prove the regression actually runs and fails with the hook removed.

**Negative.** See false positives above.

## Output additions

Include a path table from hook through extraction/composition/resolution to BSP response. Report compiler/JDK/resolver versions, actual test discovery, external-fixture prerequisites, and what remains unexecuted.

## Limitations

The historical fixture pins source and artifact coordinates, not immutable downloaded JAR bytes; remote availability and cache-independent failure were not measured. Static isolation allows explicit baseline dependencies and does not guarantee process isolation or safe execution of untrusted hooks. Scala 3, later BSP APIs, and multi-stage semantics require fresh source inspection. The 2022 macro artifact swap is not part of this procedure and had disappeared from the inspected 2024 build.

## Sources

- [PR 1053: static versus Interpreter semantics](https://github.com/com-lihaoyi/Ammonite/pull/1053#issuecomment-605952752) and [why a loader DAG is not mandatory](https://github.com/com-lihaoyi/Ammonite/pull/1053#issuecomment-607971851).
- [PR 1090: inherited repository review](https://github.com/com-lihaoyi/Ammonite/pull/1090#issuecomment-638956149), [interface boundary](https://github.com/com-lihaoyi/Ammonite/pull/1090#discussion_r435401057), and [disabled regression](https://github.com/com-lihaoyi/Ammonite/pull/1090#discussion_r435974671).
- [Pinned ordinary/plugin resolution](https://github.com/com-lihaoyi/Ammonite/blob/7017cb94d6f95c7405696affd5887d1e43116aaa/amm/interp/src/main/scala/ammonite/interp/script/ScriptProcessor.scala#L123-L143).
