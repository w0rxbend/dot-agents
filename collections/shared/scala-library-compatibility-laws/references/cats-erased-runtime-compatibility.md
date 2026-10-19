# Cats: old bytecode on a new runtime, erased signatures and inherited trait fields

Library: typelevel/cats (Scala 2.12/2.13/3, sbt). Originally `scala-cats-erased-runtime-compatibility`. Evidence ledger: [evidence/scala-cats-erased-runtime-compatibility.json](evidence/scala-cats-erased-runtime-compatibility.json) (claims `cats-c-runtime-compat`, `cats-c-trait-accessors`).

## Scope

Use when a public generic API is narrowed without changing its erased descriptor, a refactor removes apparently redundant value conversion, or a cached instance adds a field to an inherited public Scala 2 trait. Two concrete failure probes: **old values reaching new casts**, and **new synthetic trait members reaching old implementers**.

Not for: a generic dependency-upgrade checklist; private helpers with no published consumer boundary; an explicitly approved breaking release that intentionally rejects old callers. Do not import JVM bytecode conclusions into Scala.js or Native without separate platform evidence. Do not prescribe runtime migrations, effects or a new build tool.

## Version anchors

- PR 4352 exact head `b96d97136cba46c0b324a7db47af6b19105a3ea6` declares Scala 2.12.17/2.13.10/3.2.1, sbt 1.8.0, sbt-typelevel 0.4.17, Scala.js 1.11.0 and Native 0.4.7; CI Java declarations include Temurin 8/17 and GraalVM 11. Historical declarations, not executed coverage.
- That head's `binCompatTest` compiles against Cats **2.0.0 for Scala 2** and **2.6.1 for Scala 3**, via Provided, and uses current `core.jvm` in Test. Do not confuse Cats 2.x with Scala 2.x.
- PR 4352 was **closed unmerged**: its narrowed API and regression are experimental evidence, not a shipped feature.
- PR 3392 (2020 build, `cats-build-2020`) produced inherited abstract setter/accessor errors despite dropping Scala 2.11.

## Workflow

1. Write the source signature, erased signature and runtime assumptions before and after the change. Enumerate values legal for already-compiled callers. A new `A => G[Unit]` annotation does not turn old `G[String]` values into Unit at runtime.
2. Trace dispatch through syntax wrappers, the typeclass default, List/Vector and other specialized overrides. A repair only to the default is insufficient when old bytecode selects an override. In PR 4352, that omission explained why an attempted restoration still failed.
3. Preserve the historical value-discarding implementation where compatibility requires it. Inspect where `void` or equivalent conversion occurs before code starts treating the payload as Unit (pinned: [list.scala L159-L160](https://github.com/typelevel/cats/blob/b96d97136cba46c0b324a7db47af6b19105a3ea6/core/src/main/scala/cats/instances/list.scala#L159-L160), [vector.scala L165-L166](https://github.com/typelevel/cats/blob/b96d97136cba46c0b324a7db47af6b19105a3ea6/core/src/main/scala/cats/instances/vector.scala#L165-L166)). Do not remove it solely from the new source type. Do not assume a cast-based adapter is a safe correction.
4. Build a two-phase consumer probe: compile once against the supported old artifact, then execute those unchanged class files with the candidate runtime. Keep compile outputs and dependency/classpath evidence. Test non-Unit payloads, not merely the newly accepted Unit case. Recompiling the consumer against the candidate defeats this test. Historical fixture: [MimaExceptions.scala L58](https://github.com/typelevel/cats/blob/b96d97136cba46c0b324a7db47af6b19105a3ea6/binCompatTest/src/main/scala-2/catsBC/MimaExceptions.scala#L58-L58), runner [MimaExceptionsTest.scala L27-L29](https://github.com/typelevel/cats/blob/b96d97136cba46c0b324a7db47af6b19105a3ea6/binCompatTest/src/test/scala-2/catsBC/MimaExceptionsTest.scala#L27-L29).
5. Separately inspect synthetic members for new public-trait cached instances. PR 3392 produced inherited abstract setter/accessor errors despite dropping Scala 2.11. For a newly introduced instance, a concrete `def` delegating to a private cached value avoided putting new storage into the inherited trait ([partialFunction.scala L6-L7](https://github.com/typelevel/cats/blob/4fd89272ba41cf5ed989c840262ce3076a8df80a/core/src/main/scala/cats/instances/partialFunction.scala#L6-L7)). Verify the generated result; do not assume every `def` addition is safe.
6. Keep source compatibility, linker compatibility and runtime behavior as separate findings. Run the actual MiMa baselines as well as runtime probes. Never add exclusions just because source-level signatures look harmless. If an API narrowing lacks sufficient benefit or coverage, retaining the API or proposing opt-in linting is a legitimate outcome, not a failed refactor.

## Checks

Invariant: previously supported binaries execute with their old legal values, not just link. Preserve generic and specialized behavior together. For cached instances, preserve supported implicit resolution, instance reuse and old mixin compatibility without new inherited abstract obligations.

False positives:
- A private object `val` is not a newly inherited public trait field.
- A public forwarding `def` need not allocate a fresh instance.
- Conversely, converting an already-published `val` wholesale may itself alter contracts; the historical new-member repair is not authority for that rewrite.
- An intentional major-version source break does not excuse an accidental runtime break in a release that still promises binary compatibility.

## Validation

Only in an explicitly authorized disposable checkout, after inspecting build scripts and prerequisites, discover with `sbt projects` and `sbt 'show crossScalaVersions'`. For the confirmed historical project:

- `sbt 'show binCompatTest/Compile/dependencyClasspath' 'show binCompatTest/Test/fullClasspath'` verifies old compile versus new runtime selection.
- `sbt 'binCompatTest/test'` runs the old-compiled fixture through `catsBC.MimaExceptionsTest`. Verify discovery and classpath, not just the suggestive test name.
- Discover compatibility tasks with `sbt 'inspect coreJVM/mimaReportBinaryIssues'` and run the confirmed task against the repository's actual nonempty baselines. Include laws/syntax modules if their published signatures changed.
- Inspect generated class members with the target JDK's `javap` on the actual compiled trait and old implementing class; record concrete class paths rather than guessing an output directory.
- Run the target checkout's PartialFunction law/serialization suite for a trait-instance change, and default plus List/Vector runtime regressions for a traversal change.

No upstream code or build was executed during research. Commands are future validation steps grounded in inspected build definitions ([build.sbt L280-L290](https://github.com/typelevel/cats/blob/b96d97136cba46c0b324a7db47af6b19105a3ea6/build.sbt#L280-L290)) and the historical `binCompatTest/test` discussion. Static MiMa checks do not execute old clients; JVM tests do not prove JS/Native behavior.

## Examples

**Good.** An old-compiled caller supplies `Either` values containing Strings to `traverse_`. The candidate preserves value-discarding behavior in every dispatch path and the old-classfile probe is run against the candidate runtime. Separately, a new PartialFunction instance accessor forwards via `def` to a private cached instance. These match the historical test design and accepted trait repair, subject to current-version verification.

**Broken and correction.** A narrowed callback type says `G[Unit]`; the author removes `G.void` from List and Vector and cites a passing MiMa run. PR 4352's review reported a String-to-BoxedUnit `ClassCastException` despite compatible erased linkage. Correction: restore conversion in both specialized overrides and the default as appropriate, then execute the *old-compiled* non-Unit fixture. Do not declare success by compiling only new Unit callers.

For the trait variant, suppressing inherited synthetic setter errors because Scala 2.11 is no longer supported is broken. Correction: for this new member, evaluate a forwarding `def` plus private cache, inspect generated members and rerun compatibility gates.

**Negative.** A private companion already caches an instance in a `val`, and the public trait exposes a compatible concrete forwarding `def`. Do not report a public-trait-field defect or demand allocation on each access. A wholly internal operation with no old consumer promise does not need a fabricated old-artifact harness.

## Case-specific output fields

Compatibility dimension, old legal input, affected dispatch paths, old compile coordinates, candidate SHA, compiler/platform, immutable consumer output and runtime classpath. Distinguish reported historical failures, current reproduced failures and unexecuted checks.

## Limitations

Does not establish blanket source compatibility or prove compiler behavior for untested versions. PR 4352 shows why an appealing change was risky, not endorsement of a final narrowed API. Historical reviewer participation is verified; formal lead-maintainer titles are not assumed.

## Sources

- [MiMa versus old-client execution](https://github.com/typelevel/cats/pull/4352#discussion_r1028520174).
- [Old generic payloads survive erasure](https://github.com/typelevel/cats/pull/4352#discussion_r1028505880).
- [Trait field correction](https://github.com/typelevel/cats/pull/3392#issuecomment-643148810).
- [Exact historical harness build](https://github.com/typelevel/cats/blob/b96d97136cba46c0b324a7db47af6b19105a3ea6/build.sbt#L280-L290).
- [Evidence and claims](evidence/scala-cats-erased-runtime-compatibility.json), including the old caller, runtime runner and source repairs.
