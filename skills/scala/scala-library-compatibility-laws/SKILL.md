---
name: scala-library-compatibility-laws
description: Use when a published Scala library change must stay compatible beyond "it links" (erased generic signatures, inherited trait fields/accessors, old-compiled bytecode on a new runtime, source vs binary compatibility, JVM/JS/Native platform mixins) or must keep a law-backed typeclass surface honest, including traversal fast paths that must preserve branch-local isolation; grounded in Cats and Castor review history. For worxbend's own libraries use scala-library-contracts; for cancellation, streams, HTTP, macros or hot-path diagnostics use the sibling merged skills.
license: MIT
---

# Scala library compatibility and law-backed surfaces

Published library's contract: what already-compiled consumers, existing law suites and every runtime dispatch branch observe, not what new source signature says. This skill holds shared model and review procedure; version-pinned case material lives in `references/`.

**Distinction from scala-library-contracts.** That skill: house procedure for worxbend's own Scala libraries (derivation macros, redaction, native resource ownership, POM/consumer checks in those repositories). This skill: review lens on *mechanisms* from upstream OSS history (typelevel/cats, com-lihaoyi/castor): erasure, trait encoding, old-binary execution, platform linking, lawful instances and branch isolation. Use both when a worxbend library hits one of these mechanisms.

## When to Use

- Public generic signature narrowed or widened with erased descriptor unchanged, or refactor removes "redundant" value conversion (`void`, widening) from public operation.
- New cached instance, `val` or member added to inherited public Scala 2 trait.
- Members move between shared and platform (JVM/JS/Native) source roots, or JVM-only API claimed portable.
- New or strengthened typeclass instance, derived operation (e.g. `mapOrKeep`), discipline law, or public implicit helper proposed.
- `Traverse`/`mapAccumulate`-style code gains builders, strict-map helpers, shared helpers or runtime-selected fast paths (`StackSafeMonad`-style dispatch).
- Analogous changes in other Scala libraries (ZIO, FS2, http4s, Li Haoyi libraries): apply transferable checks below, not Cats/Castor specifics.

## When Not to Use

- Generic dependency upgrades, application code with no published consumer boundary, or private helpers with no changed abstraction boundary.
- Explicitly approved breaking release that intentionally rejects old callers (still record decision; see invariant I4).
- Build layout cleanup without platform-boundary change (use Mill skills), worxbend library house rules (scala-library-contracts), type-level design questions (scala-type-system), general FP idioms (scala-functional-patterns).
- Cancellation/finalization (scala-effect-cancellation-finalization), stream scopes (scala-stream-resource-scoping), HTTP semantics (scala-http-server-semantics), macro/compiler refactors (scala-compiler-macro-refactoring), hot paths and diagnostics (scala-runtime-diagnostics-hot-paths). scala-oss-library-review routes among all of them.
- Do not prescribe new effect system, build tool or "strongest available algebra". Do not ban local mutation wholesale.

## Prerequisites

- Record compatibility promise (release line promising binary compatibility), old artifact coordinates and MiMa baselines, candidate SHA, Scala versions, JDK, Scala.js/Native versions and build tool actually in use (Cats: sbt; Castor: Mill).
- Read build itself: cross versions, source roots per platform, compile vs test classpaths, `mimaPreviousArtifacts` (empty baselines common, easy to miss), law/test suite registration.
- Do not confuse library major versions with Scala versions (Cats 2.x is not Scala 2.x), or calendar years with platform support.
- Load only case reference(s) the change touches (routing table below).

## Shared model: invariants

"Transferable": applies to any published Scala library; evidence comes only from cited cases.

**I1. Old binaries must run with their old legal values, not just link.** Erasure lets source-level narrowing (`A => G[Unit]`) pass old `G[String]` payloads into new code. MiMa passes while runtime throws (`ClassCastException` String to BoxedUnit in Cats PR 4352). Only oracle: compile consumer against old artifact, then run those *unchanged* class files on candidate. Recompiling defeats test. Cases: cats-erased-runtime-compatibility, castor-platform-mixin-dispatch-accounting (old-consumer protocol). Transferable.

**I2. Every dispatch path carries contract, not just default.** Old bytecode and runtime instance checks select specialized overrides (List/Vector overrides of `traverse_`; `StackSafeMonad` branch of List traverse; Cats' special-cased `Map` builder; platform mixins chosen by source root). Repairing or testing only default path is not enough. PR 4352's attempted restoration missed overrides. PR 4498's shared-helper repair initially missed `Map`. Build table: branch predicate, implementation, tests that actually enter it. Cases: erased-runtime, traversal, castor. Transferable.

**I3. Inherited members are part of ABI even when owner looks private.** New `val` in public Scala 2 trait creates synthetic field/accessor obligations for old implementers (Cats PR 3392, despite dropping Scala 2.11). `private[castor]` mixin still contributes inherited public methods to `Context`. Inspect generated members (`javap`) on trait and on an old implementer. For a *new* member, prefer concrete `def` forwarding to private cached storage, then verify. Cases: erased-runtime, castor. Transferable to Scala 2 trait encoding; recheck for Scala 3 and JS/Native.

**I4. Source, binary (link), runtime and platform-support compatibility are separate findings.** Castor PR 12's own commit says "NOT binary compatible, but is source compatible"; release became 0.2.0. Cats PR 4352 was MiMa-clean but runtime-broken. Native method throwing `NotImplementedError` is not support. Linking smoke test is not delivery. Report each dimension as passed / failed / not run / unsupported. Cases: all four. Transferable.

**I5. Exported algebraic strength must equal observed semantics and laws actually registered.** Right-biased map union is a Band, not a (commutative) Semilattice (Cats PR 2141). Class named after a law proves nothing without its RuleSet invoked. Pick smallest counterexample first (equal keys, unequal values). Case: law-backed-instance-surface. Transferable.

**I6. Derived operations need reference law against existing primitives that kills a plausible compiling mutation.** `mapOrKeep` must equal `map` + `applyOrElse` with identity fallback. `fa.widen` compiles and passes identity-only examples. Case: law-backed. Transferable.

**I7. Law-suite and implicit-helper signatures are published API too.** Do not add type parameters/implicits to discipline rule sets to express a test (PR 4582 reused existing parameters). `A,A` registration does not prove `A1 >: A` widening; add separate strict-subtype consumer probe. Do not promote implementation helper to typeclass (PR 3541, unmerged). Do not abruptly hide an already-public helper. Keep *new* encoding helpers private (PR 2143). Case: law-backed. Transferable.

**I8. Optimizations must preserve branch-local isolation and composed state.** Builder held inside `G` can be reached by more than one continuation (e.g. List-as-effect alternatives). Sequential evaluation does not prove single use. Carry immutable accumulators (`Chain`, immutable `Map`) through `map2`. Nested `mapAccumulate` must thread outer state into inner traversal and return inner final state. Strict local `List.map` state variable never exposed is fine. Case: traversal-branch-isolation. Castor's per-message token completion (each token completes once, queued work picked up by next drain) is same "per-unit accounting survives refactor" invariant for an actor engine. Transferable as a question; concrete fixes are Cats-specific.

**I9. Platform boundaries isolate only what is platform-dependent.** Keep shared engines (token accounting, Future dispatch, queue handoff) single. Put JVM-typed signatures in JVM roots. Let JS/Native omit capabilities they do not implement. JVM type in public shared trait broke Scala.js linking in Castor PR 12 (reported by its author). Unused import is not same thing. Leftover shared JVM-typed helpers (`waitForInactivity(Option[java.time.Duration])`) remain unproved for portability. Case: castor. Transferable to any cross-built library; reproduce linker behavior on actual versions.

**I10. Proposal, merged decision and inference stay distinct.** Cats PR 4352 and 3541 and Castor PR 15 were not merged. Castor PR 12's suggested `FiniteDuration` overload did not ship. PR 3962 is discussion only. Reviewers corrected historical benchmark interpretations. Never cite unmerged proposal as policy or release.

## Routing table

| Change touches | Load |
| --- | --- |
| Cats public generic signature narrowed/widened with same erasure; removed `void`/conversion in `traverse_`, List/Vector instance overrides; `binCompatTest`, MiMa exclusions | [references/cats-erased-runtime-compatibility.md](references/cats-erased-runtime-compatibility.md) |
| New cached instance / `val` in inherited public Scala 2 trait (e.g. `cats/instances/partialFunction.scala`), synthetic setter/accessor errors | [references/cats-erased-runtime-compatibility.md](references/cats-erased-runtime-compatibility.md) |
| New or strengthened algebra instance (NonEmptyMap Band/Semilattice), `laws/`, `laws/discipline/*Tests`, derived op like `Functor.mapOrKeep`, `SyntaxSuite`, public implicit helper or Newtype/NonEmptyReducible scope | [references/cats-law-backed-instance-surface.md](references/cats-law-backed-instance-surface.md) |
| `Traverse`, `TraverseFilter`, `mapAccumulate`, `Composed`, `StaticMethods` strict-map helper, `instances/list.scala`/`map.scala`/Vector/Queue fast paths, `StackSafeMonad` dispatch, `TraverseBench` | [references/cats-traversal-branch-isolation.md](references/cats-traversal-branch-isolation.md) |
| Castor `Context`, companion, `Context.Impl`, `castor.platform.Context`, `src-jvm`/`src-js-native` roots, `scheduleMsg`, thread pools, `sendAsync`, `Actors.scala` token accounting, `waitForInactivity`, Mill cross/MiMa tasks | [references/castor-platform-mixin-dispatch-accounting.md](references/castor-platform-mixin-dispatch-accounting.md) |
| Analogous change in another library | This file's invariants and checklist, then closest case above for concrete oracles |

## Workflow

1. **Classify change** against I1-I9; load routed reference(s). Write compatibility promise for affected release line.
2. **Write before/after signatures three ways**: source signature, erased/bytecode signature (including inherited synthetic members), per-platform linkable surface. Enumerate values legal for already-compiled callers.
3. **Build dispatch table** (I2): defaults, specialized overrides, runtime-selected branches, platform mixins. For each: implementation, accumulator/state ownership, tests that actually enter it.
4. **State semantics with smallest counterexample** before choosing algebra or optimization (I5, I6, I8): colliding unequal keys; matching partial function; two effect alternatives; multiple nonempty inner containers with state-sensitive functions; handler that throws; failed external Promise.
5. **Fix narrowest thing**: restore conversion in every path, forward new member through `def` to private storage, carry immutable accumulators, thread composed state, move only platform-dependent members. Do not rewrite already-published `val`s, hide public helpers, or add law-suite parameters as collateral cleanup.
6. **Validate per dimension** (I4): source compile of old callers; old-compiled consumer on candidate runtime; MiMa against nonempty baselines; `javap` on generated members; law/discipline suites; mutation checks; per-branch regressions; per-platform link and asserted runtime behavior.
7. **Decide and record**: if change lacks benefit or coverage, keeping old API is a valid outcome. If binary compatibility is broken, state release consequence explicitly (Castor PR 12 -> 0.2.0) instead of calling it compatible.

## Review and Refactoring Checks

Transferable (any published Scala library):

- [ ] Old-compiled consumer executed on candidate with old legal, non-new-case values (I1). Not recompiled.
- [ ] Every override, runtime branch and platform mixin listed and covered (I2).
- [ ] New trait members inspected for synthetic fields/accessors; inherited members of "private" mixins counted (I3).
- [ ] Source / binary / runtime / platform results reported separately; MiMa exclusions justified by evidence, never by "signature looks harmless" (I4).
- [ ] Exported instance strength matches semantics and registered RuleSet (I5).
- [ ] Derived op has reference law that fails a plausible compiling mutation (I6).
- [ ] Law-suite signatures and public implicit visibility unchanged unless deliberate (I7).
- [ ] No mutable accumulator reachable from more than one continuation; composed state threaded (I8).
- [ ] Shared engines not duplicated per platform; only platform-typed members moved (I9).
- [ ] Every cited precedent labeled observed code / reviewer proposal / merged decision / inference (I10).

Library- or version-specific (verify on target revision before reuse):

- Cats `binCompatTest` design (Provided Cats 2.0.0 for Scala 2, 2.6.1 for Scala 3; current `core.jvm` in Test) at PR 4352 head.
- Cats List/Vector `void` placement, `StackSafeMonad` dispatch in List traverse, `Map` builder path, `Chain` accumulator (PR 4498), `Composed` mapAccumulate (PR 4209).
- Cats `FunctorTests.functor` parameter list and `mapOrKeep` `A1 >: A` signature (2024).
- Castor `SimpleActor` `finally` completion, `BatchActor` per-token completion, BaseActor synchronized `scheduled` handoff, three `reportSchedule` overloads.
- Castor empty MiMa baselines: Scala 3 in 2022, Native in 2024.

### Consolidated false positives

- Private object/companion `val` is not a newly inherited public trait field. Public forwarding `def` need not allocate per access (erased-runtime).
- New-member `def` repair does not license converting an already-published `val` wholesale (erased-runtime).
- Intentional major-version source break does not excuse accidental runtime break in a binary-compatible line (erased-runtime).
- Lawful set union need not be weakened because right-biased map union is not commutative. Repeated per-container value tests are not automatically stronger than a shared law. Typeclass-named helper is not a stable abstraction. Already-public helper cannot be hidden merely because a reviewer preferred privacy for a *new* one (law-backed).
- Encapsulated strict `List.map` state variable can be correct. Temporary input buffer fully built before entering `G` is not an output builder shared across branches. But immutable reference to a mutable builder is still shared mutable state. Branching defect is not a reproduced concurrent race (traversal).
- JVM type in JVM-only root is legitimate. Empty JS/Native mixin may deliberately omit a capability. Unused JVM import is not a reachable JVM-only method. Shared smoke test proves reachability, not delivery. JVM-only timer change with unchanged signatures and roots is not a cross-platform defect (castor).
- Wholly internal operation with no old-consumer promise does not need a fabricated old-artifact harness (erased-runtime).

### Version fences

- Scala 2 trait encoding (I3) evidence comes from Scala 2.12+/2.13 builds. Scala 3 and JS/Native trait encoding need separate evidence.
- Scala 2.12 collections differ from 2.13/3. `Seq`/`IndexedSeq` names do not prove strictness.
- `Eval` is Cats core, lazy/trampolined, not Cats Effect IO. Cats core laws do not select a Cats Effect version.
- Cats anchors: 2018 (NonEmptyMap/Newtype, ScalaTest style), 2020 (PR 3392, PR 3541), 2022 (PR 4209, PR 4352 head on Scala 2.12.17/2.13.10/3.2.1, sbt 1.8.0, Scala.js 1.11.0, Native 0.4.7), 2023-2024 (PR 4498, PR 4582, MUnit/discipline-munit).
- Castor anchors: 2020 PR #3 (Native on Scala 2.11.12), 2021 PR #12 (Native 0.4.0 Scala 2 only; Scala 3 on JS 1.x only), 2022 Mill 0.10.5 two-axis cross, 2024 Mill 0.12.0 single-axis `build.mill`, Native 0.5.4. Full table in Castor reference.
- JVM conclusions never transfer to JS/Native without platform evidence. Castor PR 12's author reported Scala.js (not Native) failing to link JVM-typed public trait members.

## Validation

- **Discover, do not assume, targets.** Only in an explicitly authorized disposable checkout, inspect build scripts first (loading sbt/Mill builds executes code). sbt: `sbt projects`, `sbt 'show crossScalaVersions'`, `sbt 'inspect <module>/mimaReportBinaryIssues'`, `show <module>/Compile/dependencyClasspath`. Mill: resolve modules/tasks from pinned launcher and CI (e.g. `./mill resolve __` style discovery) before narrowing selectors. Never transplant old cross-axis selectors.
- **Record discovery, not just exit status**: nonzero tests discovered, nonempty sources and baselines, runtime classpath actually used.
- Concrete historical commands (`binCompatTest/test`, `testsJVM/testOnly ...`, `./mill -i all __.publishArtifacts __.test`, `./mill -i __.mimaReportBinaryIssues`, the `TraverseBench` JMH line) and oracles live in references: historical discoveries, not results.
- Never invoke publishing tasks or supply credentials. Never add MiMa exclusions to turn a check green.
- **No upstream build, compilation, test, benchmark or MiMa run was executed during research for any case.** All case material evaluated by model-based review of pinned sources and review threads.

## Examples

### Good

Cats-style PR narrows callback to `G[Unit]` but keeps `void` in default and in List/Vector overrides, runs old-compiled `Either[String, ...]` fixture on new runtime, and leaves MiMa baselines untouched. Sibling change adds PartialFunction instance as `def` forwarding to private cache and records `javap` output. (erased-runtime)

Castor's JVM-typed `scheduleMsg(java.time.Duration)` lives in JVM mixin. JS/Native mixins are empty. Shared actor engine unchanged. Old JVM consumer runs unrecompiled; binary break reported with minor-version bump. (castor)

### Broken and Correction

Traverse fast path seeds `G.pure(List.newBuilder[B])` and appends in each continuation. With List as effect, two alternatives share the builder. MiMa-clean, Option-only test suite passes. Correction: immutable per-branch accumulation through `map2`; regression with two independent singleton outputs that actually enters `StackSafeMonad` branch; both Option and Eval law registrations. (traversal, I2 + I8)

NonEmptyMap union exports Semilattice while running Band laws. Correction: keep Band; add equal-key/unequal-value test in both operand orders. (law-backed, I5)

### Negative

Private state variable in a proven strict `List.map`, returned with the completed list, is not a branch-isolation finding. JVM-only timer change with unchanged signature and roots is not a portability defect. Private companion `val` behind forwarding `def` is not a trait-field defect. Do not report any of these.

## Output Contract

For each finding return:

- `file:line`, severity, invariant (I1-I10) and case reference used.
- Compatibility dimension(s): source / binary-link / old-binary runtime / platform link / runtime behavior / law, each as passed, failed, not run or unsupported.
- Smallest counterexample or old legal input; affected dispatch branches and platforms.
- Evidence ID or permalink from `references/evidence/*.json`, labeled observed code, reviewer statement, merged decision or inference.
- Scoped correction and concrete test with expected observation.
- Environment: old artifact coordinates, candidate SHA, Scala/JDK/platform versions, baselines (and any empty/skipped cells), discovered tests.
- Explicit list of unrun commands, uncompiled probes and unresolved assumptions. Never call a source-only review a successful build.

## Limitations

- Evidence covers two libraries (Cats, Castor) and a handful of PRs per case. Invariants are generalized review questions, not proven universal rules. Castor is one small-library design episode; its accounting procedure is source-derived inference.
- No proof here of cancellation, rejection safety, backpressure or concurrent-race freedom.
- Historical reviewer participation verified; formal lead-maintainer titles not assumed.
- Structural skill lint does not establish lawfulness or behavioral effectiveness.

## Sources

Per-case sources, permalinks and pinned SHAs live in each reference. Byte-exact evidence ledgers:

- [references/evidence/scala-cats-erased-runtime-compatibility.json](references/evidence/scala-cats-erased-runtime-compatibility.json)
- [references/evidence/scala-cats-law-backed-instance-surface.json](references/evidence/scala-cats-law-backed-instance-surface.json)
- [references/evidence/scala-cats-traversal-branch-isolation.json](references/evidence/scala-cats-traversal-branch-isolation.json)
- [references/evidence/scala-castor-platform-mixin-dispatch-accounting.json](references/evidence/scala-castor-platform-mixin-dispatch-accounting.json)

Key threads: [Cats PR 4352 MiMa vs old-client execution](https://github.com/typelevel/cats/pull/4352#discussion_r1028520174), [Cats PR 3392 trait field correction](https://github.com/typelevel/cats/pull/3392#issuecomment-643148810), [Cats PR 2141 map algebra](https://github.com/typelevel/cats/pull/2141#discussion_r165438090), [Cats PR 4582 compiling-but-wrong Functor](https://github.com/typelevel/cats/pull/4582#discussion_r1550835026), [Cats PR 4498 branching counterexample](https://github.com/typelevel/cats/pull/4498#issuecomment-1806479051), [Castor PR 12 linker constraint](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919928186).
