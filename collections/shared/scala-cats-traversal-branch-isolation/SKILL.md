---
name: scala-cats-traversal-branch-isolation
description: Use when optimizing Cats Traverse or mapAccumulate with builders, strict-map helpers, or runtime-selected fast paths. Preserve branch-local outputs and composed state without banning safe local mutation.
license: MIT
---

# Preserve Cats traversal specialization semantics

## When to Use

Use for changes to `Traverse`, `TraverseFilter`, collection instances, or composed `mapAccumulate` implementations that introduce mutation, extract a shared helper, or select an implementation from the runtime effect instance. Review both the algorithm and the assumptions selecting it. This is a refactoring procedure, not a collection-selection tutorial.

## When Not to Use

Do not apply to ordinary application `List.map` code with no changed abstraction boundary. Do not infer Cats Effect cancellation, FS2 scope ownership, parallel execution, or IO recovery contracts from Cats core. Do not replace the project's existing effect model or sbt build with a different style or tool.

## Prerequisites

Read the target checkout's instructions, `build.sbt`, `project/build.properties`, plugins and instance definitions. Record Cats version, Scala compiler, platform and the actual `G` instance. The historical anchors are PR 4209 (2022) and PR 4498 (2023–2024), not a promise about every release. Scala 2.12 collection APIs differ from 2.13/3; `Seq` and `IndexedSeq` names do not prove strict evaluation. `Eval` is lazy/trampolined Cats core, not Cats Effect IO. No effect-runtime version is established by these sources.

Identify `F` (input container), `G` (effect), accumulator ownership, evaluation timing and runtime dispatch before editing. Read the [claim and source ledger](references/evidence.json).

## Workflow

1. Trace the public operation through its default, collection overrides, composed instances and helper. Make a table of branch predicate, implementation, accumulator and tests. Inspect `Map` separately: PR 4498's shared-helper repair initially missed its special-cased mutable builder.
2. For a pure strict-map helper, prove that mapping completes before returning the final state, visits in the required traversal order, and does not expose the local state reference. The private helper in PR 4209 has a `Functor` parameter, but its safe callers supply additional strictness/order facts not encoded by `Functor`.
3. For a builder held *inside* generic `G`, ask whether a continuation can run more than once with the same accumulator reference. Sequential evaluation does not prove single-use ownership. Prefer immutable accumulators carried through `map2`; PR 4498 uses `Chain` and a separate immutable `Map` path. Do not merely move one shared builder into `G.pure`.
4. For nested `mapAccumulate`, compose the operations themselves: pass the state supplied by the outer step into the inner traversal and return that inner final state. Do not restart each inner structure from `init`, or replace composition with a generic strict-map shortcut.
5. Exercise every runtime branch deliberately. Historical `ListSuite` registers both Option and Eval laws; an Option-only suite could miss the `StackSafeMonad` path. Reconfirm marker membership on the target version. The historical fake `StackSafeMonad[List]` is a diagnostic routing trick, not a lawful production instance or evidence of general stack safety. Remove its focused `.only` marker when adapting the diagnostic into a real regression suite.
6. Preserve existing specialization hooks and evaluate performance only after correctness. Keep benchmark baseline and candidate SHAs, input sizes, success/failure workloads and toolchains explicit. A faster success case does not establish faster early failure. Historical reviewers corrected their benchmark interpretation; do not treat a tentative Vector exception as the final policy.

## Review and Refactoring Checks

Preserve these invariants: independent effect branches produce independent outputs; state flows across all inner containers; both final state and output match the reference traversal; fallback and optimized paths obey the same observable laws. Preserve laziness where promised, but do not promise that finite `mapAccumulate` returning final state becomes lazy on an infinite input.

False positives: an encapsulated strict `List.map` state variable can be correct; a temporary input buffer completely built before entering `G` is not the same ownership problem as an output builder shared across effect branches. Conversely, an immutable reference to a mutable builder is still shared mutable state. Do not call the demonstrated branching defect a reproduced concurrent race.

## Validation

In a separately authorized disposable checkout, inspect build scripts before invoking sbt: loading a build executes code. Discover projects with `sbt projects` and compiler versions with `sbt 'show crossScalaVersions'`. The inspected builds define the `tests` cross-project and the following suite classes; confirm loaded IDs before running:

- `sbt 'testsJVM/testOnly cats.tests.TraverseListSuite cats.tests.TraverseListSuiteUnderlying cats.tests.ListSuite'`
- Run the target version's corresponding Map, Vector, Queue and TraverseFilter tests for every touched override; record nonzero discovery, not just exit status.
- Add the branch-isolation reproducer alongside a lawful supported stack-safe instance. Assert output per alternative, not only total length. Add a nested state-sensitive case and compare both tuple components against the existing fold/State specification.
- Check empty, singleton, multiple-inner and large finite inputs. Run JS/Native only with separately verified toolchains and report those results independently.

No upstream build, Scala compilation, performance measurement or regression execution was performed while authoring this skill. The historical benchmark command is `bench/jmh:run -i 10 -wi 10 -f 2 -t 1 cats.bench.TraverseBench`; inspect plugin/task syntax before any reuse. Do not invoke broad formatting aliases as read-only validation.

## Examples

### Good

PR 4498's direct path folds an immutable `Chain` within `G`; each `map2` callback returns a new accumulator value. Its List override dispatches to this helper only for `StackSafeMonad`. PR 4209 composes `F.mapAccumulate` with `G.mapAccumulate` instead of assuming the composed maps are strict. These are observed historical implementations; today's checks must reopen both definitions and their law registrations.

### Broken and Correction

A proposed fast path seeds `G.pure(List.newBuilder[B])`, appends inside each continuation and returns `result`. One input with two alternatives can reuse the same builder, contaminating branch outputs. Correction: carry immutable per-branch accumulation through the effect and convert at the boundary. Test two independent singleton outputs; make the test actually enter the changed fast path.

For nested accumulation, resetting every inner container to the original state is also broken. Correction: thread the previous inner final state forward. Use multiple nonempty inner containers and a state-sensitive function; a test observing only state-insensitive mapped values cannot detect the reset.

### Negative

A private state variable updated during a proven strict List map, then returned with the completed List, does not trigger a builder-aliasing finding. Preserve it if the state/value reference test passes. Reusing that helper for arbitrary `Seq` without proving strictness does trigger review; the interface alone is insufficient.

## Output Contract

Return each finding with `file:line`, severity, affected runtime branch, violated invariant, evidence ID/permalink, smallest counterexample, scoped correction and regression test. Separate observed historical behavior from current-version inference. Report selected compiler/platform cells and actual test discovery/results; mark unrun commands and unresolved ownership assumptions explicitly.

## Limitations

The sample establishes specific failure mechanisms, not exhaustive Cats history or universal bans on mutation. The diagnostic fake marker is deliberately limited; laws do not prove all performance properties. Benchmark claims require fresh measurements. Published generic signature changes belong to the separate erased-runtime compatibility workflow.

## Sources

- [Branching counterexample and correction, PR 4498](https://github.com/typelevel/cats/pull/4498#issuecomment-1806479051).
- [Composition concern, PR 4209](https://github.com/typelevel/cats/pull/4209#discussion_r879777925).
- [Strictness boundary, PR 4209](https://github.com/typelevel/cats/pull/4209#discussion_r879782750).
- [Pinned implementation](https://github.com/typelevel/cats/blob/6cb787db2579b957c009a7e2929d656c9f08709f/core/src/main/scala/cats/Traverse.scala#L289-L297).
- [Evidence and claims](references/evidence.json), including actual tests and the sibling Map repair.
