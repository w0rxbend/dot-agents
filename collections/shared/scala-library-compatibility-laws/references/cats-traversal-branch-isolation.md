# Cats: traversal fast paths that keep branch-local isolation and composed state

Library: typelevel/cats (`Traverse`, `TraverseFilter`, collection instances, `Composed`; sbt). Evidence ledger: [evidence/scala-cats-traversal-branch-isolation.json](evidence/scala-cats-traversal-branch-isolation.json) (claims `cats-c-branch-isolation`, `cats-c-strict-accumulate`).

## Scope

Use for changes to `Traverse`, `TraverseFilter`, collection instances or composed `mapAccumulate` implementations that add mutation, extract shared helper, or pick implementation from runtime effect instance. Review algorithm and the assumptions selecting it. Refactoring procedure, not collection-selection tutorial.

Not for: ordinary application `List.map` code with no changed abstraction boundary. Do not infer Cats Effect cancellation, FS2 scope ownership, parallel execution or IO recovery contracts from Cats core. Do not replace project's existing effect model or sbt build with different style or tool. Published generic signature changes belong to [cats-erased-runtime-compatibility.md](cats-erased-runtime-compatibility.md).

## Version anchors

Read target checkout's instructions, `build.sbt`, `project/build.properties`, plugins and instance definitions. Record Cats version, Scala compiler, platform, actual `G` instance.

- Historical anchors are PR 4209 (2022) and PR 4498 (2023-2024), not a promise about every release.
- Scala 2.12 collection APIs differ from 2.13/3; `Seq` and `IndexedSeq` names do not prove strict evaluation.
- `Eval` is lazy/trampolined Cats core ([Eval.scala L48](https://github.com/typelevel/cats/blob/5c84daa942693d03882f0f22c31a07620b9dc262/core/src/main/scala/cats/Eval.scala#L48-L48)), not Cats Effect IO. These sources establish no effect-runtime version.

Before editing, identify `F` (input container), `G` (effect), accumulator ownership, evaluation timing, runtime dispatch.

## Workflow

1. Trace public operation through default, collection overrides, composed instances and helper. Tabulate branch predicate, implementation, accumulator, tests. Inspect `Map` separately: PR 4498's shared-helper repair initially missed its special-cased mutable builder ([map.scala L49-L51](https://github.com/typelevel/cats/blob/6cb787db2579b957c009a7e2929d656c9f08709f/core/src/main/scala/cats/instances/map.scala#L49-L51)).
2. For pure strict-map helper, prove mapping completes before returning final state, visits in required traversal order, and does not expose local state reference. PR 4209's private helper ([StaticMethods.scala L42-L46](https://github.com/typelevel/cats/blob/bc33be342afdb474bc2bfd0533000377ab386d4d/core/src/main/scala/cats/instances/StaticMethods.scala#L42-L46)) takes a `Functor`, but its safe callers supply extra strictness/order facts not encoded by `Functor`.
3. For builder held *inside* generic `G`, ask whether a continuation can run more than once with same accumulator reference. Sequential evaluation does not prove single-use ownership. Prefer immutable accumulators carried through `map2`; PR 4498 uses `Chain` and separate immutable `Map` path. Do not merely move one shared builder into `G.pure`.
4. For nested `mapAccumulate`, compose the operations themselves: pass outer step's state into inner traversal and return that inner final state ([Composed.scala L129](https://github.com/typelevel/cats/blob/bc33be342afdb474bc2bfd0533000377ab386d4d/core/src/main/scala/cats/Composed.scala#L129-L129)). Do not restart each inner structure from `init` or replace composition with generic strict-map shortcut.
5. Exercise every runtime branch deliberately. Historical `ListSuite` registers both Option and Eval laws ([ListSuite.scala L57](https://github.com/typelevel/cats/blob/6cb787db2579b957c009a7e2929d656c9f08709f/tests/shared/src/test/scala/cats/tests/ListSuite.scala#L57-L57)); Option-only suite could miss `StackSafeMonad` path ([list.scala L125](https://github.com/typelevel/cats/blob/6cb787db2579b957c009a7e2929d656c9f08709f/core/src/main/scala/cats/instances/list.scala#L125-L125)). Reconfirm marker membership on target version. Historical fake `StackSafeMonad[List]` is diagnostic routing trick, not lawful production instance or evidence of general stack safety. Remove its focused `.only` marker when turning diagnostic into real regression suite.
6. Keep existing specialization hooks; evaluate performance only after correctness. Keep benchmark baseline and candidate SHAs, input sizes, success/failure workloads and toolchains explicit. Faster success case does not prove faster early failure. Historical reviewers corrected their benchmark interpretation ([comment](https://github.com/typelevel/cats/pull/4498#issuecomment-2088548540)); do not treat tentative Vector exception as final policy.

## Checks

Invariants: independent effect branches produce independent outputs; state flows across all inner containers; final state and output both match reference traversal; fallback and optimized paths obey same observable laws. Preserve laziness where promised, but do not promise finite `mapAccumulate` returning final state becomes lazy on infinite input.

False positives:
- Encapsulated strict `List.map` state variable can be correct.
- Temporary input buffer fully built before entering `G` is not the same ownership problem as output builder shared across effect branches.
- Conversely, immutable reference to mutable builder is still shared mutable state.
- Do not call demonstrated branching defect a reproduced concurrent race.

## Validation

In separately authorized disposable checkout, inspect build scripts before invoking sbt: loading a build executes code. Discover projects with `sbt projects` and compiler versions with `sbt 'show crossScalaVersions'`. Inspected builds define `tests` cross-project and these suite classes; confirm loaded IDs before running:

- `sbt 'testsJVM/testOnly cats.tests.TraverseListSuite cats.tests.TraverseListSuiteUnderlying cats.tests.ListSuite'`
- Run target version's corresponding Map, Vector, Queue and TraverseFilter tests for every touched override; record nonzero discovery, not just exit status.
- Add branch-isolation reproducer alongside lawful supported stack-safe instance. Assert output per alternative, not only total length. Add nested state-sensitive case; compare both tuple components against existing fold/State specification ([TraverseSuite.scala L48](https://github.com/typelevel/cats/blob/bc33be342afdb474bc2bfd0533000377ab386d4d/tests/shared/src/test/scala/cats/tests/TraverseSuite.scala#L48-L48)).
- Check empty, singleton, multiple-inner and large finite inputs. Run JS/Native only with separately verified toolchains; report those results independently.

Research ran no upstream build, Scala compilation, performance measurement or regression. Historical benchmark command: `bench/jmh:run -i 10 -wi 10 -f 2 -t 1 cats.bench.TraverseBench`; inspect plugin/task syntax before any reuse. Do not invoke broad formatting aliases as read-only validation.

## Examples

**Good.** PR 4498's direct path folds immutable `Chain` within `G`; each `map2` callback returns new accumulator value ([Traverse.scala L289-L297](https://github.com/typelevel/cats/blob/6cb787db2579b957c009a7e2929d656c9f08709f/core/src/main/scala/cats/Traverse.scala#L289-L297)). Its List override dispatches to this helper only for `StackSafeMonad`. PR 4209 composes `F.mapAccumulate` with `G.mapAccumulate` instead of assuming composed maps are strict. Observed historical implementations; today's checks must reopen both definitions and their law registrations.

**Broken and correction.** Proposed fast path seeds `G.pure(List.newBuilder[B])`, appends inside each continuation, returns `result`. One input with two alternatives can reuse same builder, contaminating branch outputs. Correction: carry immutable per-branch accumulation through effect; convert at boundary. Test two independent singleton outputs; make test actually enter changed fast path. Regression commit: [2210d82](https://github.com/typelevel/cats/commit/2210d8271792a14c20b5b25b7b54b82f464779f6).

Nested accumulation that resets every inner container to original state is also broken. Correction: thread previous inner final state forward. Use multiple nonempty inner containers and state-sensitive function; test observing only state-insensitive mapped values cannot detect the reset.

**Negative.** Private state variable updated during proven strict List map, then returned with completed List, does not trigger builder-aliasing finding. Preserve it if state/value reference test passes. Reusing that helper for arbitrary `Seq` without proving strictness does trigger review; interface alone is insufficient.

## Case-specific output fields

Affected runtime branch, violated invariant, smallest counterexample, scoped correction, regression test. Separate observed historical behavior from current-version inference. Report selected compiler/platform cells and actual test discovery/results; mark unrun commands and unresolved ownership assumptions explicitly.

## Limitations

Establishes specific failure mechanisms, not exhaustive Cats history or universal bans on mutation. Laws do not prove all performance properties. Benchmark claims need fresh measurements.

## Sources

- [Branching counterexample and correction, PR 4498](https://github.com/typelevel/cats/pull/4498#issuecomment-1806479051).
- [Composition concern, PR 4209](https://github.com/typelevel/cats/pull/4209#discussion_r879777925).
- [Strictness boundary, PR 4209](https://github.com/typelevel/cats/pull/4209#discussion_r879782750).
