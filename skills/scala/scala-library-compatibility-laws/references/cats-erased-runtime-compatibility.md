# Cats: old bytecode on a new runtime, erased signatures and inherited trait fields

Library: typelevel/cats (Scala 2.12/2.13/3, sbt). Evidence ledger: [evidence/scala-cats-erased-runtime-compatibility.json](evidence/scala-cats-erased-runtime-compatibility.json) (claims `cats-c-runtime-compat`, `cats-c-trait-accessors`).

## Scope

Use when public generic API is narrowed without changing erased descriptor, refactor removes seemingly redundant value conversion, or cached instance adds field to inherited public Scala 2 trait. Two concrete failure probes: **old values reaching new casts** and **new synthetic trait members reaching old implementers**.

Not for: generic dependency-upgrade checklist; private helpers with no published consumer boundary; explicitly approved breaking release that intentionally rejects old callers. Do not apply JVM bytecode conclusions to Scala.js or Native without separate platform evidence. Do not prescribe runtime migrations, effects or new build tool.

## Version anchors

- PR 4352 exact head `b96d97136cba46c0b324a7db47af6b19105a3ea6` declares Scala 2.12.17/2.13.10/3.2.1, sbt 1.8.0, sbt-typelevel 0.4.17, Scala.js 1.11.0, Native 0.4.7; CI Java declarations include Temurin 8/17 and GraalVM 11. Historical declarations, not executed coverage.
- That head's `binCompatTest` compiles against Cats **2.0.0 for Scala 2** and **2.6.1 for Scala 3** via Provided; Test uses current `core.jvm`. Do not confuse Cats 2.x with Scala 2.x.
- PR 4352 **closed unmerged**: narrowed API and regression are experimental evidence, not shipped feature.
- PR 3392 (2020 build, `cats-build-2020`) produced inherited abstract setter/accessor errors despite dropping Scala 2.11.

## Workflow

1. Write source signature, erased signature and runtime assumptions before and after change. Enumerate values legal for already-compiled callers. New `A => G[Unit]` annotation does not turn old `G[String]` values into Unit at runtime.
2. Trace dispatch through syntax wrappers, typeclass default, List/Vector and other specialized overrides. Repairing only the default is insufficient when old bytecode selects an override; in PR 4352 that omission explained why attempted restoration still failed.
3. Keep historical value-discarding implementation where compatibility requires it. Find where `void` or equivalent conversion happens before code treats payload as Unit (pinned: [list.scala L159-L160](https://github.com/typelevel/cats/blob/b96d97136cba46c0b324a7db47af6b19105a3ea6/core/src/main/scala/cats/instances/list.scala#L159-L160), [vector.scala L165-L166](https://github.com/typelevel/cats/blob/b96d97136cba46c0b324a7db47af6b19105a3ea6/core/src/main/scala/cats/instances/vector.scala#L165-L166)). Do not remove it solely because of new source type. Do not assume cast-based adapter is safe correction.
4. Build two-phase consumer probe: compile once against supported old artifact, then run those unchanged class files on candidate runtime. Keep compile outputs and dependency/classpath evidence. Test non-Unit payloads, not only newly accepted Unit case. Recompiling consumer against candidate defeats the test. Historical fixture: [MimaExceptions.scala L58](https://github.com/typelevel/cats/blob/b96d97136cba46c0b324a7db47af6b19105a3ea6/binCompatTest/src/main/scala-2/catsBC/MimaExceptions.scala#L58-L58), runner [MimaExceptionsTest.scala L27-L29](https://github.com/typelevel/cats/blob/b96d97136cba46c0b324a7db47af6b19105a3ea6/binCompatTest/src/test/scala-2/catsBC/MimaExceptionsTest.scala#L27-L29).
5. Separately inspect synthetic members for new public-trait cached instances. For newly introduced instance, concrete `def` delegating to private cached value avoided new storage in inherited trait ([partialFunction.scala L6-L7](https://github.com/typelevel/cats/blob/4fd89272ba41cf5ed989c840262ce3076a8df80a/core/src/main/scala/cats/instances/partialFunction.scala#L6-L7)). Verify generated result; do not assume every `def` addition is safe.
6. Keep source compatibility, linker compatibility and runtime behavior as separate findings. Run actual MiMa baselines plus runtime probes. Never add exclusions only because source-level signatures look harmless. If API narrowing lacks enough benefit or coverage, keeping the API or proposing opt-in linting is legitimate, not a failed refactor.

## Checks

Invariant: previously supported binaries run with their old legal values, not just link. Preserve generic and specialized behavior together. For cached instances, preserve supported implicit resolution, instance reuse and old mixin compatibility without new inherited abstract obligations.

False positives:
- Private object `val` is not a newly inherited public trait field.
- Public forwarding `def` need not allocate a fresh instance.
- Conversely, converting already-published `val` wholesale may itself alter contracts; historical new-member repair is not authority for that rewrite.
- Intentional major-version source break does not excuse accidental runtime break in a release still promising binary compatibility.

## Validation

Only in explicitly authorized disposable checkout, after inspecting build scripts and prerequisites, discover with `sbt projects` and `sbt 'show crossScalaVersions'`. For confirmed historical project:

- `sbt 'show binCompatTest/Compile/dependencyClasspath' 'show binCompatTest/Test/fullClasspath'` verifies old compile versus new runtime selection.
- `sbt 'binCompatTest/test'` runs old-compiled fixture through `catsBC.MimaExceptionsTest`. Verify discovery and classpath, not just suggestive test name.
- Discover compatibility tasks with `sbt 'inspect coreJVM/mimaReportBinaryIssues'`; run confirmed task against repository's actual nonempty baselines. Include laws/syntax modules if their published signatures changed.
- Inspect generated class members with target JDK's `javap` on actual compiled trait and old implementing class; record concrete class paths, do not guess output directory.
- Trait-instance change: run target checkout's PartialFunction law/serialization suite. Traversal change: run default plus List/Vector runtime regressions.

Research ran no upstream code or build. Commands are future validation steps based on inspected build definitions ([build.sbt L280-L290](https://github.com/typelevel/cats/blob/b96d97136cba46c0b324a7db47af6b19105a3ea6/build.sbt#L280-L290)) and historical `binCompatTest/test` discussion. Static MiMa checks do not execute old clients; JVM tests do not prove JS/Native behavior.

## Examples

**Good.** Old-compiled caller passes `Either` values containing Strings to `traverse_`. Candidate keeps value-discarding behavior in every dispatch path; old-classfile probe runs on candidate runtime. Separately, new PartialFunction instance accessor forwards via `def` to private cached instance. Matches historical test design and accepted trait repair, pending current-version verification.

**Broken and correction.** Narrowed callback type says `G[Unit]`; author removes `G.void` from List and Vector, cites passing MiMa run. PR 4352's review reported String-to-BoxedUnit `ClassCastException` despite compatible erased linkage. Correction: restore conversion in both specialized overrides and default as appropriate, then run *old-compiled* non-Unit fixture. Do not declare success by compiling only new Unit callers.

Trait variant: suppressing inherited synthetic setter errors because Scala 2.11 is no longer supported is broken. Correction: for this new member, evaluate forwarding `def` plus private cache, inspect generated members, rerun compatibility gates.

**Negative.** Private companion already caches instance in `val`; public trait exposes compatible concrete forwarding `def`. Do not report public-trait-field defect or demand allocation per access. Wholly internal operation with no old consumer promise needs no fabricated old-artifact harness.

## Case-specific output fields

Compatibility dimension, old legal input, affected dispatch paths, old compile coordinates, candidate SHA, compiler/platform, immutable consumer output, runtime classpath. Distinguish reported historical failures, current reproduced failures and unexecuted checks.

## Limitations

Does not establish blanket source compatibility or prove compiler behavior for untested versions. PR 4352 shows why an appealing change was risky; it does not endorse a final narrowed API. Historical reviewer participation verified; formal lead-maintainer titles not assumed.

## Sources

- [MiMa versus old-client execution](https://github.com/typelevel/cats/pull/4352#discussion_r1028520174).
- [Old generic payloads survive erasure](https://github.com/typelevel/cats/pull/4352#discussion_r1028505880).
- [Trait field correction](https://github.com/typelevel/cats/pull/3392#issuecomment-643148810).
