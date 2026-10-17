---
name: scala-cats-law-backed-instance-surface
description: Use when adding Cats algebra instances, derived typeclass operations, or public implicit construction helpers. Align exported laws, primitive-reference tests and the supported API surface without changing published discipline signatures casually.
license: MIT
---

# Design a law-backed Cats instance surface

## When to Use

Use for stronger algebra instances, new derived operations such as `mapOrKeep`, or proposals to expose implementation helpers as implicit abstractions. Review the public capability, its laws, actual rule-set registration and consumer syntax together. A compiling implementation or a class named after a law is not sufficient evidence.

## When Not to Use

Do not load for a routine application helper that adds no reusable typeclass API. Do not prescribe the strongest algebra merely because it is available, make every helper private, or replace direct-style/ZIO/Cats Effect choices. Use traversal-specialization guidance for mutable accumulation inside effects; use erased-runtime compatibility guidance for old generic payloads and trait fields.

## Prerequisites

Inspect Scala/Cats versions, actual imports and source-generation conventions, the build, public instance hierarchy, `laws` and `laws/discipline`, and suites registering those rules. The anchors span 2018 NonEmptyMap/Newtype, 2020 NonEmptyReducible discussion and 2024 Functor evolution; they are different API eras.

The 2024 `mapOrKeep` implementation has `A1 >: A`; its discipline registration uses `A,A`. Do not assume tests with equal types validate strict subtype widening. The 2018 suite used ScalaTest-style assertions; later snapshots use MUnit/discipline-munit. Preserve the target repository's conventions rather than copying old syntax. Cats core laws do not require selecting a Cats Effect version.

## Workflow

1. State the operation's semantics with the smallest counterexample before choosing the algebra. For right-biased map union, two maps sharing a key but holding distinct values distinguish operand order. Nonemptiness and idempotence do not imply commutativity. Compare the exported instance with the exact RuleSet invoked, not only its class name.
2. For a derived operation, express it using existing primitives. `mapOrKeep` preserves unmatched values and structure; its reference is `map` with `PartialFunction.applyOrElse` and identity fallback, not `collect`. Design a law that fails a plausible compiling mutation such as returning unchanged `fa.widen`.
3. Register the law in the shared discipline suite and trace the actual instances exercising it. Avoid duplicating the same value-level property across containers when the common suite already reaches them. Retain specialized tests when they cover distinct dispatch paths or observable behavior.
4. Treat the discipline API as published API. Do not append a new type parameter, generator or implicit argument simply to express widening tests. PR 4582 used existing type parameters for its equivalence law. Add separate subtype/syntax consumer probes with a genuine subtype relation, not the erroneous assumption that Scala `Int` extends Java `Number`.
5. Classify a proposed public helper: is it a supported capability with lawful operations, or merely a convenience for implementing another typeclass? PR 3541's low-priority implicit arrangement did not establish that `NonEmptyReducible` should become a typeclass. Document an already-public implementation helper rather than abruptly hiding or deprecating it. For a new encoding helper, private scope avoids an unnecessary public commitment.
6. Keep revision outcomes explicit. PR 2141 changed the proposed semilattice to Band with corresponding tests; PR 4582 added the reference law. PR 3541 was unmerged and its discussion favored clarification. PR 3962 supplies only in-window discussion about helper scope, not evidence that its later-observed proposal shipped.

## Review and Refactoring Checks

Preserve the invariant that exported algebraic strength matches actual collision/evaluation semantics and registered laws. Preserve container shape and unmatched values for map-or-keep. Preserve existing law-suite signatures and intentional consumer visibility. Keep private construction machinery separate from public implicit capability.

False positives: lawful set union need not be weakened because right-biased map union is not commutative. Repeating List/Option/Map value tests is not automatically stronger than a shared law. Conversely, `A,A` registration does not prove widening, and a typeclass name on an implementation helper does not establish a stable abstraction. An already-public helper cannot safely be hidden merely because a historical reviewer preferred privacy for a new helper.

## Validation

In an explicitly authorized disposable checkout, inspect build files before loading sbt. Run `sbt projects` and `sbt 'show crossScalaVersions'`; confirm the `tests` cross-project and suite paths for that revision. After confirming IDs, use `sbt 'testsJVM/testOnly cats.tests.NonEmptyMapSuite cats.tests.ListSuite'` for the map-instance and law-registration paths, and `sbt 'testsJVM/Test/compile'` for syntax-only consumer probes. Select the corresponding affected instance suites rather than assuming one suite covers every instance.

Add a mutation check: the reference law must reject an override that ignores a matching partial function. Use colliding unequal map values to reject a false commutativity claim. Add a strict-subtype consumer with both direct `Functor[F].mapOrKeep` and extension syntax, an explicit `F[Super]` result and matched/unmatched cases. Compile existing discipline callers unchanged and run discovered compatibility tasks for published law modules.

The exact PR 4582 `SyntaxSuite` was inspected: its `testFunctor` covers existing operations but contains no `mapOrKeep` call. Therefore the separate widening probe is a proposed current-version validation requirement, not a historical test claimed to pass. No Scala was compiled and no upstream suite was run during authoring.

## Examples

### Good

An implementation delegates map-or-keep to `map` plus `applyOrElse`; its shared law compares against that specification and registers without widening the published `FunctorTests.functor` parameter list. A separate consumer probe uses a sealed supertype and a case-class subtype to check widening. Historical evidence establishes the first two decisions; the additional consumer probe closes a validation gap and still needs compilation.

### Broken and Correction

A NonEmptyMap union keeps the right value on duplicate keys, but the PR exports Semilattice while running only Band laws. Correction: retain Band unless deliberately changing semantics; assert both operand orders on equal keys with unequal values and register the laws matching the public instance.

An optimized `mapOrKeep` returning only `fa.widen` also compiles but is wrong for a matching case. Correction: restore partial-function dispatch with identity fallback and require equality to the primitive specification. Identity-only examples cannot kill this mutation.

### Negative

A documented public typeclass has real consumers and law-backed capabilities. Do not hide it because its implementation is short. A private Newtype construction helper can remain private without removing the public nonempty data API. A lawful set-union semilattice is not invalidated by the map collision counterexample.

## Output Contract

Return `file:line`, severity, proposed capability, semantic counterexample, evidence IDs/permalinks, exported versus tested laws, correction and test. Include the rule-set registration path and supported compiler/platform cells. Label source observations, historical reviewer statements and inferred current-version tests separately; list uncompiled consumer probes and unresolved compatibility obligations.

## Limitations

These are specific review-derived procedures, not a complete algebra design method. Historical discussions contain disagreements and corrected suggestions; quote the final relevant reasoning, not every early proposal as policy. No formal lead-maintainer status is assumed. A shared law can still miss unsupported generators or branches. Structural skill lint does not establish lawfulness or behavioral effectiveness.

## Sources

- [Map algebra challenge](https://github.com/typelevel/cats/pull/2141#discussion_r165438090).
- [Compiling-but-wrong Functor implementation](https://github.com/typelevel/cats/pull/4582#discussion_r1550835026).
- [Discipline signature and duplicate-test discussion](https://github.com/typelevel/cats/pull/4582#discussion_r1565182368).
- [Implementation helper versus typeclass](https://github.com/typelevel/cats/pull/3541#pullrequestreview-464264988).
- [New encoding helper scope](https://github.com/typelevel/cats/pull/2143#discussion_r173659302).
- [Evidence and claims](references/evidence.json), including pinned API, law and test sources.
