# Cats: law-backed instance surface and public implicit helpers

Library: typelevel/cats (core, `laws`, `laws/discipline`, `tests`; sbt). Evidence ledger: [evidence/scala-cats-law-backed-instance-surface.json](evidence/scala-cats-law-backed-instance-surface.json) (claims `cats-c-law-strength`, `cats-c-reference-laws`, `cats-c-private-helper`).

## Scope

Use for stronger algebra instances, new derived operations such as `mapOrKeep`, or proposals exposing implementation helpers as implicit abstractions. Review public capability, its laws, actual rule-set registration and consumer syntax together. Compiling implementation or class named after a law is not sufficient evidence.

Not for: routine application helper adding no reusable typeclass API. Do not prescribe strongest algebra merely because available, make every helper private, or replace direct-style/ZIO/Cats Effect choices. Mutable accumulation inside effects belongs to [cats-traversal-branch-isolation.md](cats-traversal-branch-isolation.md); old generic payloads and trait fields belong to [cats-erased-runtime-compatibility.md](cats-erased-runtime-compatibility.md).

## Version anchors

Inspect Scala/Cats versions, actual imports, source-generation conventions, build, public instance hierarchy, `laws` and `laws/discipline`, and suites registering those rules. Anchors span **2018** NonEmptyMap/Newtype, **2020** NonEmptyReducible discussion and **2024** Functor evolution: different API eras.

- 2024 `mapOrKeep` implementation ([Functor.scala L191](https://github.com/typelevel/cats/blob/a2931f5961ad31a95b55c87f1bb3fb7c9a486c74/core/src/main/scala/cats/Functor.scala#L191-L191)) has `A1 >: A`; its discipline registration ([FunctorTests.scala L45](https://github.com/typelevel/cats/blob/a2931f5961ad31a95b55c87f1bb3fb7c9a486c74/laws/src/main/scala/cats/laws/discipline/FunctorTests.scala#L45-L45)) uses `A,A`. Do not assume equal-type tests validate strict subtype widening.
- 2018 suite used ScalaTest-style assertions; later snapshots use MUnit/discipline-munit. Follow target repository's conventions; do not copy old syntax.
- Cats core laws do not require selecting a Cats Effect version.

## Workflow

1. Before choosing algebra, state operation's semantics with smallest counterexample. Right-biased map union: two maps sharing a key with distinct values distinguish operand order. Nonemptiness and idempotence do not imply commutativity. Compare exported instance with exact RuleSet invoked, not only its class name ([NonEmptyMapImpl.scala L316](https://github.com/typelevel/cats/blob/60327b1963cfc1a69f453c9a071a2c2ced9d5c2d/core/src/main/scala/cats/data/NonEmptyMapImpl.scala#L316-L316), [NonEmptyMapSuite.scala L32](https://github.com/typelevel/cats/blob/60327b1963cfc1a69f453c9a071a2c2ced9d5c2d/tests/src/test/scala/cats/tests/NonEmptyMapSuite.scala#L32-L32)).
2. Express derived operation with existing primitives. `mapOrKeep` keeps unmatched values and structure; its reference is `map` with `PartialFunction.applyOrElse` and identity fallback, not `collect` ([FunctorLaws.scala L37](https://github.com/typelevel/cats/blob/a2931f5961ad31a95b55c87f1bb3fb7c9a486c74/laws/src/main/scala/cats/laws/FunctorLaws.scala#L37-L37)). Design a law that fails plausible compiling mutation such as returning unchanged `fa.widen`.
3. Register law in shared discipline suite; trace actual instances exercising it. Avoid duplicating same value-level property across containers when common suite already reaches them. Keep specialized tests covering distinct dispatch paths or observable behavior.
4. Treat discipline API as published API. Do not append new type parameter, generator or implicit argument only to express widening tests; PR 4582 used existing type parameters for its equivalence law. Add separate subtype/syntax consumer probes with genuine subtype relation, not the erroneous assumption that Scala `Int` extends Java `Number` ([review boundary](https://github.com/typelevel/cats/pull/4582#discussion_r1565170097)).
5. Classify proposed public helper: supported capability with lawful operations, or merely convenience for implementing another typeclass? PR 3541's low-priority implicit arrangement did not establish that `NonEmptyReducible` should become a typeclass. Document already-public implementation helper; do not abruptly hide or deprecate it. For new encoding helper ([Newtype.scala L8](https://github.com/typelevel/cats/blob/b7097730ebe422ab73b6884e49ced05b1186f61f/core/src/main/scala/cats/data/Newtype.scala#L8-L8)), private scope avoids unnecessary public commitment.
6. Keep revision outcomes explicit. PR 2141 changed proposed semilattice to Band with matching tests; PR 4582 added reference law. PR 3541 unmerged; its discussion favored clarification. PR 3962 gives only in-window discussion about helper scope ([comment](https://github.com/typelevel/cats/pull/3962#discussion_r750883239)), not evidence its later-observed proposal shipped.

## Checks

Invariant: exported algebraic strength matches actual collision/evaluation semantics and registered laws. Preserve container shape and unmatched values for map-or-keep. Preserve existing law-suite signatures and intentional consumer visibility. Keep private construction machinery separate from public implicit capability.

False positives:
- Lawful set union need not be weakened because right-biased map union is not commutative.
- Repeating List/Option/Map value tests is not automatically stronger than a shared law.
- Conversely, `A,A` registration does not prove widening; typeclass name on implementation helper does not establish a stable abstraction.
- Already-public helper cannot safely be hidden merely because historical reviewer preferred privacy for a new helper.

## Validation

In explicitly authorized disposable checkout, inspect build files before loading sbt ([build.sbt L17-L19](https://github.com/typelevel/cats/blob/a2931f5961ad31a95b55c87f1bb3fb7c9a486c74/build.sbt#L17-L19)). Run `sbt projects` and `sbt 'show crossScalaVersions'`; confirm `tests` cross-project and suite paths for that revision. After confirming IDs:

- `sbt 'testsJVM/testOnly cats.tests.NonEmptyMapSuite cats.tests.ListSuite'` for map-instance and law-registration paths.
- `sbt 'testsJVM/Test/compile'` for syntax-only consumer probes.
- Select corresponding affected instance suites; do not assume one suite covers every instance.

Mutation and consumer oracles:
- Reference law must reject override ignoring a matching partial function.
- Use colliding unequal map values to reject false commutativity claim.
- Add strict-subtype consumer with both direct `Functor[F].mapOrKeep` and extension syntax, explicit `F[Super]` result, matched/unmatched cases.
- Compile existing discipline callers unchanged; run discovered compatibility tasks for published law modules.

Exact PR 4582 `SyntaxSuite` inspected ([L339](https://github.com/typelevel/cats/blob/a2931f5961ad31a95b55c87f1bb3fb7c9a486c74/tests/shared/src/test/scala/cats/tests/SyntaxSuite.scala#L339-L339)): its `testFunctor` covers existing operations but has no `mapOrKeep` call. So separate widening probe is proposed current-version validation requirement, not historical test claimed to pass. Research compiled no Scala and ran no upstream suite.

## Examples

**Good.** Implementation delegates map-or-keep to `map` plus `applyOrElse`; shared law compares against that specification, registers without widening published `FunctorTests.functor` parameter list. Separate consumer probe uses sealed supertype and case-class subtype to check widening. Historical evidence establishes first two decisions; extra consumer probe closes validation gap, still needs compilation.

**Broken and correction.** NonEmptyMap union keeps right value on duplicate keys, but PR exports Semilattice while running only Band laws. Correction: keep Band unless deliberately changing semantics; assert both operand orders on equal keys with unequal values; register laws matching public instance.

Optimized `mapOrKeep` returning only `fa.widen` also compiles but is wrong for matching case. Correction: restore partial-function dispatch with identity fallback; require equality to primitive specification. Identity-only examples cannot kill this mutation.

**Negative.** Documented public typeclass has real consumers and law-backed capabilities. Do not hide it because its implementation is short. Private Newtype construction helper can stay private without removing public nonempty data API.

## Case-specific output fields

Proposed capability, semantic counterexample, exported versus tested laws, rule-set registration path, supported compiler/platform cells. Label source observations, historical reviewer statements and inferred current-version tests separately; list uncompiled consumer probes and unresolved compatibility obligations.

## Limitations

Specific review-derived procedures, not complete algebra design method. Historical discussions contain disagreements and corrected suggestions; quote final relevant reasoning, not every early proposal as policy. No formal lead-maintainer status assumed. Shared law can still miss unsupported generators or branches. Structural skill lint does not establish lawfulness or behavioral effectiveness.

## Sources

- [Map algebra challenge](https://github.com/typelevel/cats/pull/2141#discussion_r165438090).
- [Compiling-but-wrong Functor implementation](https://github.com/typelevel/cats/pull/4582#discussion_r1550835026).
- [Discipline signature and duplicate-test discussion](https://github.com/typelevel/cats/pull/4582#discussion_r1565182368).
- [Implementation helper versus typeclass](https://github.com/typelevel/cats/pull/3541#pullrequestreview-464264988).
- [New encoding helper scope](https://github.com/typelevel/cats/pull/2143#discussion_r173659302).
