---
name: scala-library-compatibility-laws
description: Use when a published Scala library change must stay compatible beyond "it links" (erased generic signatures, inherited trait fields/accessors, old-compiled bytecode on a new runtime, source vs binary compatibility, JVM/JS/Native platform mixins) or must keep a law-backed typeclass surface honest, including traversal fast paths that must preserve branch-local isolation; grounded in Cats and Castor review history. For worxbend's own libraries use scala-library-contracts; for cancellation, streams, HTTP, macros or hot-path diagnostics use the sibling merged skills.
license: MIT
---

# Scala library compatibility and law-backed surfaces

A published library's contract is what already-compiled consumers, existing law suites and every runtime dispatch branch observe, not what the new source signature says. This skill holds the shared model and review procedure; the concrete, version-pinned case material is in `references/`.

**Distinction from scala-library-contracts.** That skill is the house procedure for worxbend's own Scala libraries (derivation macros, redaction, native resource ownership, POM/consumer checks in those repositories). This skill is a review lens derived from upstream OSS history (typelevel/cats, com-lihaoyi/castor) about *mechanisms*: erasure, trait encoding, old-binary execution, platform linking, lawful instances and branch isolation. Use both when a worxbend library hits one of these mechanisms.

## When to Use

- A public generic signature is narrowed or widened while its erased descriptor stays the same, or a refactor removes "redundant" value conversion (`void`, widening) from a public operation.
- A new cached instance, `val` or member is added to an inherited public Scala 2 trait.
- Members move between shared and platform (JVM/JS/Native) source roots, or a JVM-only API is claimed portable.
- A new or strengthened typeclass instance, derived operation (e.g. `mapOrKeep`), discipline law, or public implicit helper is proposed.
- `Traverse`/`mapAccumulate`-style code gains builders, strict-map helpers, shared helpers or runtime-selected fast paths (`StackSafeMonad`-style dispatch).
- Analogous changes in other Scala libraries (ZIO, FS2, http4s, Li Haoyi libraries); apply the transferable checks below, not the Cats/Castor specifics.

## When Not to Use

- Generic dependency upgrades, application code with no published consumer boundary, or private helpers with no changed abstraction boundary.
- An explicitly approved breaking release that intentionally rejects old callers (still record the decision; see invariant I4).
- Build layout cleanup without a platform-boundary change (use the Mill skills), worxbend library house rules (scala-library-contracts), type-level design questions (scala-type-system), general FP idioms (scala-functional-patterns).
- Cancellation/finalization (scala-effect-cancellation-finalization), stream scopes (scala-stream-resource-scoping), HTTP semantics (scala-http-server-semantics), macro/compiler refactors (scala-compiler-macro-refactoring), hot paths and diagnostics (scala-runtime-diagnostics-hot-paths). scala-oss-library-review routes among all of them.
- Do not prescribe a new effect system, build tool or "strongest available algebra"; do not ban local mutation wholesale.

## Prerequisites

- Record the compatibility promise (which release line promises binary compatibility), the old artifact coordinates and MiMa baselines, candidate SHA, Scala versions, JDK, Scala.js/Native versions and the build tool actually in use (Cats: sbt; Castor: Mill).
- Read the actual build: cross versions, source roots per platform, compile vs test classpaths, `mimaPreviousArtifacts` (empty baselines are common and easy to miss), and law/test suite registration.
- Do not confuse library major versions with Scala versions (Cats 2.x is not Scala 2.x), or calendar years with platform support.
- Load only the case reference(s) the change touches (routing table below).

## Shared model: invariants

Each invariant is stated once and tied to the case(s) that demonstrate it. "Transferable" means it applies to any published Scala library; the evidence for it comes only from the cited cases.

**I1. Old binaries must run with their old legal values, not just link.** Erasure means a source-level narrowing (`A => G[Unit]`) leaves old `G[String]` payloads flowing into new code; MiMa passes while the runtime throws (`ClassCastException` String to BoxedUnit in Cats PR 4352). The only oracle is: compile a consumer against the old artifact, then run those *unchanged* class files on the candidate. Recompiling defeats the test. Cases: cats-erased-runtime-compatibility, castor-platform-mixin-dispatch-accounting (old-consumer protocol). Transferable.

**I2. Every dispatch path carries the contract, not just the default.** Old bytecode and runtime instance checks select specialized overrides (List/Vector overrides of `traverse_`; the `StackSafeMonad` branch of List traverse; Cats' special-cased `Map` builder; platform mixins chosen by source root). A repair or test of only the default path is insufficient: PR 4352's attempted restoration missed overrides, and PR 4498's shared-helper repair initially missed `Map`. Build a table: branch predicate, implementation, tests that actually enter it. Cases: erased-runtime, traversal, castor. Transferable.

**I3. Inherited members are part of the ABI even when the owner looks private.** A new `val` in a public Scala 2 trait creates synthetic field/accessor obligations for old implementers (Cats PR 3392, despite dropping Scala 2.11); a `private[castor]` mixin still contributes inherited public methods to `Context`. Inspect generated members (`javap`) on the trait and an old implementer; prefer a concrete `def` forwarding to private cached storage for a *new* member, then verify. Cases: erased-runtime, castor. Transferable to Scala 2 trait encoding; recheck for Scala 3 and JS/Native.

**I4. Source, binary (link), runtime and platform-support compatibility are separate findings.** Castor PR 12's own commit says "NOT binary compatible, but is source compatible" and the release became 0.2.0; Cats PR 4352 was MiMa-clean but runtime-broken. A Native method throwing `NotImplementedError` is not support; a linking smoke test is not delivery. Report each dimension as passed / failed / not run / unsupported. Cases: all four. Transferable.

**I5. Exported algebraic strength must equal observed semantics and the laws actually registered.** Right-biased map union is a Band, not a (commutative) Semilattice (Cats PR 2141); a class named after a law proves nothing without the RuleSet invoked. Pick the smallest counterexample first (equal keys, unequal values). Case: law-backed-instance-surface. Transferable.

**I6. Derived operations need a reference law against existing primitives that kills a plausible compiling mutation.** `mapOrKeep` must equal `map` + `applyOrElse` with identity fallback; `fa.widen` compiles and passes identity-only examples. Case: law-backed. Transferable.

**I7. Law-suite and implicit-helper signatures are published API too.** Do not add type parameters/implicits to discipline rule sets to express a test (PR 4582 reused existing parameters); `A,A` registration does not prove `A1 >: A` widening, so add a separate strict-subtype consumer probe. Do not promote an implementation helper to a typeclass (PR 3541, unmerged) or abruptly hide an already-public one; keep *new* encoding helpers private (PR 2143). Case: law-backed. Transferable.

**I8. Optimizations must preserve branch-local isolation and composed state.** A builder held inside `G` can be reached by more than one continuation (e.g. List-as-effect alternatives); sequential evaluation does not prove single use. Carry immutable accumulators (`Chain`, immutable `Map`) through `map2`. Nested `mapAccumulate` must thread the outer state into the inner traversal and return the inner final state. A strict local `List.map` state variable that is never exposed is fine. Case: traversal-branch-isolation; Castor's per-message token completion (each token completes once, queued work picked up by the next drain) is the same "per-unit accounting survives refactor" invariant for an actor engine. Transferable as a question; the concrete fixes are Cats-specific.

**I9. Platform boundaries isolate only what is platform-dependent.** Keep shared engines (token accounting, Future dispatch, queue handoff) single; put JVM-typed signatures in JVM roots; let JS/Native omit capabilities they do not implement. A JVM type in a public shared trait broke Scala.js linking in Castor PR 12 (reported by its author); an unused import is not the same thing. Leftover shared JVM-typed helpers (`waitForInactivity(Option[java.time.Duration])`) remain unproved for portability. Case: castor. Transferable to any cross-built library; linker behavior must be reproduced on the actual versions.

**I10. Proposal, merged decision and inference stay distinct.** Cats PR 4352 and 3541 and Castor PR 15 were not merged; Castor PR 12's suggested `FiniteDuration` overload did not ship; PR 3962 is discussion only. Historical benchmark interpretations were corrected by reviewers. Never cite an unmerged proposal as policy or a release.

## Routing table

| Change touches | Load |
| --- | --- |
| Cats public generic signature narrowed/widened with same erasure; removed `void`/conversion in `traverse_`, List/Vector instance overrides; `binCompatTest`, MiMa exclusions | [references/cats-erased-runtime-compatibility.md](references/cats-erased-runtime-compatibility.md) |
| New cached instance / `val` in an inherited public Scala 2 trait (e.g. `cats/instances/partialFunction.scala`), synthetic setter/accessor errors | [references/cats-erased-runtime-compatibility.md](references/cats-erased-runtime-compatibility.md) |
| New or strengthened algebra instance (NonEmptyMap Band/Semilattice), `laws/`, `laws/discipline/*Tests`, derived op like `Functor.mapOrKeep`, `SyntaxSuite`, public implicit helper or Newtype/NonEmptyReducible scope | [references/cats-law-backed-instance-surface.md](references/cats-law-backed-instance-surface.md) |
| `Traverse`, `TraverseFilter`, `mapAccumulate`, `Composed`, `StaticMethods` strict-map helper, `instances/list.scala`/`map.scala`/Vector/Queue fast paths, `StackSafeMonad` dispatch, `TraverseBench` | [references/cats-traversal-branch-isolation.md](references/cats-traversal-branch-isolation.md) |
| Castor `Context`, companion, `Context.Impl`, `castor.platform.Context`, `src-jvm`/`src-js-native` roots, `scheduleMsg`, thread pools, `sendAsync`, `Actors.scala` token accounting, `waitForInactivity`, Mill cross/MiMa tasks | [references/castor-platform-mixin-dispatch-accounting.md](references/castor-platform-mixin-dispatch-accounting.md) |
| Analogous change in another library | This file's invariants and checklist; then the closest case above for concrete oracles |

## Workflow

1. **Classify the change** against I1-I9 and load the routed reference(s). Write the compatibility promise for the affected release line.
2. **Write before/after signatures three ways**: source signature, erased/bytecode signature (including inherited synthetic members), and per-platform linkable surface. Enumerate values legal for already-compiled callers.
3. **Build the dispatch table** (I2): defaults, specialized overrides, runtime-selected branches, platform mixins; for each, the implementation, accumulator/state ownership and the tests that actually enter it.
4. **State semantics with the smallest counterexample** before choosing an algebra or optimization (I5, I6, I8): colliding unequal keys; a matching partial function; two effect alternatives; multiple nonempty inner containers with state-sensitive functions; a handler that throws; a failed external Promise.
5. **Fix the narrowest thing**: restore conversion in every path, forward a new member through a `def` to private storage, carry immutable accumulators, thread composed state, move only platform-dependent members. Do not rewrite already-published `val`s, hide public helpers, or add law-suite parameters as collateral cleanup.
6. **Validate per dimension** (I4): source compile of old callers; old-compiled consumer on the candidate runtime; MiMa against nonempty baselines; `javap` on generated members; law/discipline suites; mutation checks; per-branch regressions; per-platform link and asserted runtime behavior.
7. **Decide and record**: if a change lacks benefit or coverage, retaining the old API is a valid outcome. If binary compatibility is broken, state the release consequence explicitly (Castor PR 12 -> 0.2.0) rather than calling it compatible.

## Review and Refactoring Checks

Transferable (any published Scala library):

- [ ] Old-compiled consumer executed on the candidate with old legal, non-new-case values (I1). Not recompiled.
- [ ] Every override, runtime branch and platform mixin listed and covered (I2).
- [ ] New trait members inspected for synthetic fields/accessors; inherited members of "private" mixins counted (I3).
- [ ] Source / binary / runtime / platform results reported separately; MiMa exclusions justified by evidence, never by "signature looks harmless" (I4).
- [ ] Exported instance strength matches semantics and the registered RuleSet (I5).
- [ ] Derived op has a reference law that fails a plausible compiling mutation (I6).
- [ ] Law-suite signatures and public implicit visibility unchanged unless deliberate (I7).
- [ ] No mutable accumulator reachable from more than one continuation; composed state threaded (I8).
- [ ] Shared engines not duplicated per platform; only platform-typed members moved (I9).
- [ ] Every cited precedent labeled observed code / reviewer proposal / merged decision / inference (I10).

Library- or version-specific (verify on the target revision before reuse):

- Cats `binCompatTest` design (Provided Cats 2.0.0 for Scala 2, 2.6.1 for Scala 3; current `core.jvm` in Test) at PR 4352 head.
- Cats List/Vector `void` placement, `StackSafeMonad` dispatch in List traverse, `Map` builder path, `Chain` accumulator (PR 4498), `Composed` mapAccumulate (PR 4209).
- Cats `FunctorTests.functor` parameter list and `mapOrKeep` `A1 >: A` signature (2024).
- Castor `SimpleActor` `finally` completion, `BatchActor` per-token completion, BaseActor synchronized `scheduled` handoff, three `reportSchedule` overloads.
- Castor empty MiMa baselines: Scala 3 in 2022, Native in 2024.

### Consolidated false positives

- A private object/companion `val` is not a newly inherited public trait field; a public forwarding `def` need not allocate per access (erased-runtime).
- Converting an already-published `val` wholesale is not licensed by the new-member `def` repair (erased-runtime).
- An intentional major-version source break does not excuse an accidental runtime break in a binary-compatible line (erased-runtime).
- Lawful set union need not be weakened because right-biased map union is not commutative; repeated per-container value tests are not automatically stronger than a shared law; `A,A` registration does not prove widening; a typeclass-named helper is not a stable abstraction; an already-public helper cannot be hidden just because a reviewer preferred privacy for a *new* one (law-backed).
- An encapsulated strict `List.map` state variable can be correct; a temporary input buffer fully built before entering `G` is not an output builder shared across branches; but an immutable reference to a mutable builder is still shared mutable state; the branching defect is not a reproduced concurrent race (traversal).
- A JVM type in a JVM-only root is legitimate; an empty JS/Native mixin may deliberately omit a capability; an unused JVM import is not a reachable JVM-only method; the shared smoke test proves reachability, not delivery; a JVM-only timer change with unchanged signatures and roots is not a cross-platform defect (castor).
- A wholly internal operation with no old-consumer promise does not need a fabricated old-artifact harness (erased-runtime).

### Version fences

- Scala 2 trait encoding (I3) evidence is from Scala 2.12+/2.13 builds; Scala 3 and JS/Native trait encoding need separate evidence.
- Scala 2.12 collections differ from 2.13/3; `Seq`/`IndexedSeq` names do not prove strictness.
- `Eval` is Cats core, lazy/trampolined, not Cats Effect IO; Cats core laws do not select a Cats Effect version.
- Cats anchors: 2018 (NonEmptyMap/Newtype, ScalaTest style), 2020 (PR 3392, PR 3541), 2022 (PR 4209, PR 4352 head on Scala 2.12.17/2.13.10/3.2.1, sbt 1.8.0, Scala.js 1.11.0, Native 0.4.7), 2023-2024 (PR 4498, PR 4582, MUnit/discipline-munit).
- Castor anchors: 2020 PR #3 (Native on Scala 2.11.12), 2021 PR #12 (Native 0.4.0 Scala 2 only; Scala 3 on JS 1.x only), 2022 Mill 0.10.5 two-axis cross, 2024 Mill 0.12.0 single-axis `build.mill`, Native 0.5.4. Full table in the Castor reference.
- JVM conclusions never transfer to JS/Native without platform evidence; Castor PR 12's author reported Scala.js (not Native) failing to link JVM-typed public trait members.

## Validation

- **Discover, do not assume, targets.** Only in an explicitly authorized disposable checkout, inspect build scripts first (loading sbt/Mill builds executes code). sbt: `sbt projects`, `sbt 'show crossScalaVersions'`, `sbt 'inspect <module>/mimaReportBinaryIssues'`, `show <module>/Compile/dependencyClasspath`. Mill: resolve modules/tasks from the pinned launcher and CI (e.g. `./mill resolve __` style discovery) before narrowing selectors; never transplant old cross-axis selectors.
- **Record discovery, not just exit status**: nonzero tests discovered, nonempty sources and baselines, the runtime classpath actually used.
- **Per-dimension gates**: old-compiled consumer run (I1); MiMa on nonempty baselines (I4); `javap` on generated trait/implementer (I3); law suites plus mutation checks (I5, I6); per-branch and per-platform regressions with asserted outputs (I2, I8, I9).
- Concrete historical commands (`binCompatTest/test`, `testsJVM/testOnly ...`, `./mill -i all __.publishArtifacts __.test`, `./mill -i __.mimaReportBinaryIssues`, the `TraverseBench` JMH line) and oracles are in the references; they are historical discoveries, not results.
- Never invoke publishing tasks or supply credentials; never add MiMa exclusions to turn a check green.
- **No upstream build, compilation, test, benchmark or MiMa run was executed during research for any case.** All case material was evaluated by model-based review of pinned sources and review threads.

## Examples

### Good

A Cats-style PR narrows a callback to `G[Unit]` but keeps `void` in the default and in List/Vector overrides, runs the old-compiled `Either[String, ...]` fixture on the new runtime, and leaves MiMa baselines untouched. A sibling change adds a PartialFunction instance as a `def` forwarding to a private cache and records `javap` output. (erased-runtime)

Castor's JVM-typed `scheduleMsg(java.time.Duration)` lives in the JVM mixin; JS/Native mixins are empty; the shared actor engine is unchanged; an old JVM consumer is run unrecompiled and the binary break is reported with a minor-version bump. (castor)

### Broken and Correction

A traverse fast path seeds `G.pure(List.newBuilder[B])` and appends in each continuation; with List as the effect, two alternatives share the builder. A MiMa-clean, Option-only test suite passes. Correction: immutable per-branch accumulation through `map2`, a regression with two independent singleton outputs that actually enters the `StackSafeMonad` branch, and both Option and Eval law registrations. (traversal, I2 + I8)

A NonEmptyMap union exports Semilattice while running Band laws. Correction: keep Band, add an equal-key/unequal-value test in both operand orders. (law-backed, I5)

### Negative

A private state variable in a proven strict `List.map`, returned with the completed list, is not a branch-isolation finding. A JVM-only timer change with unchanged signature and roots is not a portability defect. A private companion `val` behind a forwarding `def` is not a trait-field defect. Do not report any of these.

## Output Contract

For each finding return:

- `file:line`, severity, invariant (I1-I10) and the case reference used.
- Compatibility dimension(s): source / binary-link / old-binary runtime / platform link / runtime behavior / law, each as passed, failed, not run or unsupported.
- Smallest counterexample or old legal input; affected dispatch branches and platforms.
- Evidence ID or permalink from `references/evidence/*.json`, labeled observed code, reviewer statement, merged decision or inference.
- Scoped correction and a concrete test with expected observation.
- Environment: old artifact coordinates, candidate SHA, Scala/JDK/platform versions, baselines (and any empty/skipped cells), discovered tests.
- Explicit list of unrun commands, uncompiled probes and unresolved assumptions. Never call a source-only review a successful build.

## Limitations

- Evidence covers two libraries (Cats, Castor) and a handful of PRs per case; the invariants are generalized as review questions, not proven universal rules. Castor is one small-library design episode; its accounting procedure is source-derived inference.
- No upstream build, compilation, MiMa run, benchmark or test was executed while authoring any case. Commands and oracles are future validation steps.
- No proof here of cancellation, rejection safety, backpressure or concurrent-race freedom; JVM results do not establish JS/Native behavior.
- Historical reviewer participation is verified; formal lead-maintainer titles are not assumed. Early proposals in threads are not policy.
- Structural skill lint does not establish lawfulness or behavioral effectiveness.

## Sources

Per-case sources, permalinks and pinned SHAs are in each reference; byte-exact evidence ledgers:

- [references/evidence/scala-cats-erased-runtime-compatibility.json](references/evidence/scala-cats-erased-runtime-compatibility.json)
- [references/evidence/scala-cats-law-backed-instance-surface.json](references/evidence/scala-cats-law-backed-instance-surface.json)
- [references/evidence/scala-cats-traversal-branch-isolation.json](references/evidence/scala-cats-traversal-branch-isolation.json)
- [references/evidence/scala-castor-platform-mixin-dispatch-accounting.json](references/evidence/scala-castor-platform-mixin-dispatch-accounting.json)

Key threads: [Cats PR 4352 MiMa vs old-client execution](https://github.com/typelevel/cats/pull/4352#discussion_r1028520174), [Cats PR 3392 trait field correction](https://github.com/typelevel/cats/pull/3392#issuecomment-643148810), [Cats PR 2141 map algebra](https://github.com/typelevel/cats/pull/2141#discussion_r165438090), [Cats PR 4582 compiling-but-wrong Functor](https://github.com/typelevel/cats/pull/4582#discussion_r1550835026), [Cats PR 4498 branching counterexample](https://github.com/typelevel/cats/pull/4498#issuecomment-1806479051), [Castor PR 12 linker constraint](https://github.com/com-lihaoyi/castor/pull/12#issuecomment-919928186).
