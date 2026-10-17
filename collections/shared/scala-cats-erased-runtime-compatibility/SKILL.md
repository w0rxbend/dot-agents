---
name: scala-cats-erased-runtime-compatibility
description: Use when reviewing Cats erased generic signature changes or new cached instances in inherited Scala 2 traits. Check old bytecode against the new runtime and inspect specialized overrides and synthetic accessors.
license: MIT
---

# Check Cats old-client runtime compatibility

## When to Use

Use when a public generic API is narrowed without changing its erased descriptor, a refactor removes apparently redundant value conversion, or a cached instance adds a field to an inherited public Scala 2 trait. This augments ordinary public-API review with two concrete failure probes: old values reaching new casts, and new synthetic trait members reaching old implementers.

## When Not to Use

Do not use as a generic dependency-upgrade checklist or for private helpers with no published consumer boundary. An explicitly approved breaking release may intentionally reject old callers. Do not import JVM bytecode conclusions into Scala.js or Native without separate platform evidence. Do not prescribe runtime migrations, effects or a new build tool.

## Prerequisites

Record the supported compatibility promise, old artifact coordinates, candidate SHA, Scala compiler and JVM. Read the actual build's compile and test classpaths. PR 4352's exact head `b96d97136cba46c0b324a7db47af6b19105a3ea6` declares Scala 2.12.17/2.13.10/3.2.1, sbt 1.8.0, sbt-typelevel 0.4.17, Scala.js 1.11.0 and Native 0.4.7; CI Java declarations include Temurin 8/17 and GraalVM 11. These are historical declarations, not executed coverage.

That head's `binCompatTest` compiles against Cats **2.0.0 for Scala 2**, **2.6.1 for Scala 3**, via Provided, and uses current `core.jvm` in Test. Do not confuse Cats 2.x with Scala 2.x. PR 4352 was closed unmerged: its narrowed API and regression are experimental evidence, not a shipped feature. Read the [source ledger](references/evidence.json).

## Workflow

1. Write the source signature, erased signature and runtime assumptions before and after the change. Enumerate values legal for already-compiled callers. A new `A => G[Unit]` annotation does not turn old `G[String]` values into Unit at runtime.
2. Trace dispatch through syntax wrappers, the typeclass default, List/Vector and other specialized overrides. A repair only to the default is insufficient when old bytecode selects an override. In PR 4352, that omission explained why an attempted restoration still failed.
3. Preserve the historical value-discarding implementation where compatibility requires it. Inspect where `void` or equivalent conversion occurs before code starts treating the payload as Unit. Do not remove it solely from the new source type. Do not assume a cast-based adapter is a safe correction.
4. Build a two-phase consumer probe: compile once against the supported old artifact, then execute those unchanged class files with the candidate runtime. Keep compile outputs and dependency/classpath evidence. Test non-Unit payloads, not merely the newly accepted Unit case. Recompiling the consumer against the candidate defeats this test.
5. Separately inspect synthetic members for new public-trait cached instances. PR 3392 produced inherited abstract setter/accessor errors despite dropping Scala 2.11. For a newly introduced instance, a concrete `def` delegating to a private cached value avoided putting new storage into the inherited trait. Verify the generated result; do not assume every `def` addition is safe.
6. Keep source compatibility, linker compatibility and runtime behavior as separate findings. Run the actual MiMa baselines as well as runtime probes. Never add exclusions just because source-level signatures look harmless. If an API narrowing lacks sufficient benefit or coverage, retaining the API or proposing opt-in linting is a legitimate outcome, not a failed refactor.

## Review and Refactoring Checks

Preserve the invariant that previously supported binaries execute with their old legal values, not just link. Preserve generic and specialized behavior together. For cached instances, preserve supported implicit resolution, instance reuse and old mixin compatibility without new inherited abstract obligations.

False positives: a private object `val` is not a newly inherited public trait field. A public forwarding `def` need not allocate a fresh instance. Conversely, converting an already-published `val` wholesale may itself alter contracts; the historical new-member repair is not authority for that rewrite. An intentional major-version source break does not excuse an accidental runtime break in a release that still promises binary compatibility.

## Validation

Only in an explicitly authorized disposable checkout, after inspecting build scripts and prerequisites, discover with `sbt projects` and `sbt 'show crossScalaVersions'`. For the confirmed historical project:

- `sbt 'show binCompatTest/Compile/dependencyClasspath' 'show binCompatTest/Test/fullClasspath'` verifies old compile versus new runtime selection.
- `sbt 'binCompatTest/test'` runs the old-compiled fixture through `catsBC.MimaExceptionsTest`. Verify discovery and classpath, not just the suggestive test name.
- Discover compatibility tasks with `sbt 'inspect coreJVM/mimaReportBinaryIssues'` and run the confirmed task against the repository's actual nonempty baselines. Include laws/syntax modules if their published signatures changed.
- Inspect generated class members with the target JDK's `javap` on the actual compiled trait and old implementing class; record concrete class paths rather than guessing an output directory.
- Run the target checkout's PartialFunction law/serialization suite for a trait-instance change, and default plus List/Vector runtime regressions for a traversal change.

No upstream code or build was executed during skill authoring. Commands are future validation steps grounded in inspected build definitions and the historical `binCompatTest/test` discussion. Static MiMa checks do not execute old clients; JVM tests do not prove JS/Native behavior.

## Examples

### Good

An old-compiled caller supplies `Either` values containing Strings to `traverse_`. The candidate preserves value-discarding behavior in every dispatch path and the old-classfile probe is run against the candidate runtime. Separately, a new PartialFunction instance accessor forwards via `def` to a private cached instance. These match the historical test design and accepted trait repair, subject to current-version verification.

### Broken and Correction

A narrowed callback type says `G[Unit]`; the author removes `G.void` from List and Vector and cites a passing MiMa run. PR 4352's review reported a String-to-BoxedUnit `ClassCastException` despite compatible erased linkage. Correction: restore conversion in both specialized overrides and the default as appropriate, then execute the *old-compiled* non-Unit fixture. Do not declare success by compiling only new Unit callers.

For the trait variant, suppressing inherited synthetic setter errors because Scala 2.11 is no longer supported is broken. Correction: for this new member, evaluate a forwarding `def` plus private cache, inspect generated members and rerun compatibility gates.

### Negative

A private companion already caches an instance in a `val`, and the public trait exposes a compatible concrete forwarding `def`. Do not report a public-trait-field defect or demand allocation on each access. Likewise, a wholly internal operation with no old consumer promise does not need a fabricated old-artifact harness.

## Output Contract

For every finding return `file:line`, severity, compatibility dimension, old legal input, affected dispatch paths, evidence ID/permalink, correction and test. Include old compile coordinates, candidate SHA, compiler/platform, immutable consumer output and runtime classpath. Distinguish reported historical failures, current reproduced failures and unexecuted checks.

## Limitations

This workflow does not establish blanket source compatibility or prove compiler behavior for untested versions. PR 4352 demonstrates why an appealing change was risky, not endorsement of a final narrowed API. Historical reviewer participation is verified; formal lead-maintainer titles are not assumed. Use broader library-contract guidance for unrelated publication and dependency concerns.

## Sources

- [MiMa versus old-client execution](https://github.com/typelevel/cats/pull/4352#discussion_r1028520174).
- [Old generic payloads survive erasure](https://github.com/typelevel/cats/pull/4352#discussion_r1028505880).
- [Trait field correction](https://github.com/typelevel/cats/pull/3392#issuecomment-643148810).
- [Exact historical harness build](https://github.com/typelevel/cats/blob/b96d97136cba46c0b324a7db47af6b19105a3ea6/build.sbt#L280-L290).
- [Evidence and claims](references/evidence.json), including the old caller, runtime runner and source repairs.
