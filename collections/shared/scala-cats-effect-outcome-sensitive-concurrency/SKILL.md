---
name: scala-cats-effect-outcome-sensitive-concurrency
description: Use when reviewing Cats Effect race, memoize, or Fiber.cancel refactors that change cancellation outcomes, waiter cleanup, or startup behavior.
license: MIT
---

# Preserve outcome-sensitive concurrency

## When to Use

Use on CE3 kernel/runtime changes that share race implementations, alter memoized evaluation state, or wrap `Fiber.cancel`. Review the outcome table before simplifying the implementation. A canceled computation is not an ordinary failed value.

## When Not to Use

Do not use for general Resource acquisition/registration, FS2 scope leases, ZIO cancel-token evaluation, or ordinary Future completion. Those have different ownership mechanisms. Do not transplant CE3 `Outcome` or `Poll` into CE2. Preserve the project's effect library, syntax and sbt build.

## Prerequisites

Read the target commit's build, kernel API, concrete IO overrides and test definitions. Record Scala, Cats Effect and platform versions. The memoize case is pre-release Cats Effect 3 at `000758b0b5e1ae12161845dc472bf148459ca237`, not a specification of every CE3 release. The race and forceStart cases are **unmerged** proposals, not APIs to import.

The CE2 comparison at `1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e` has `Fiber[F,A].join: F[A]`, subscriber-counted memoization, `ExitCase` and `ContextShift`; it does not provide the CE3 outcome-returning join. Use that comparison to stop an invalid port, not to claim the two runtimes are equivalent. See [evidence and version boundaries](references/evidence.json).

## Workflow

1. **Locate the semantic owner.** Trace syntax to the typeclass default and any IO override. Identify whether the caller receives a value, an `Outcome`, or a live loser fiber. Write down who must cancel or join that fiber after the combinator returns.
2. **Build the outcome table.** For both operand orders, enumerate success, error, self-cancellation and parent cancellation. In the reviewed CE3 contract, `raceOutcome` cancels the loser even when the winner canceled; `race` instead waits for the other result in that case. `racePair` transfers a live fiber handle. Share only implementation steps whose policies actually agree.
3. **Trace interrupted waits.** At each polled loser join, cancel the parent after entering the wait. Check that the remaining child is canceled on both symmetric branches. A local `onCancel(f.cancel)` repair fixes that ownership hole; it cannot fix the wrong canceled-winner policy.
4. **Model memoize transitions.** Identify unevaluated, evaluating and finished states, the evaluation owner, subscriber bookkeeping and waiter wakeup. Interleave cancellation request, actual cancellation observation, a second get, and late completion. Require one consistent cached success/error, no abandoned waiters, and the target version's retry semantics. Do not manufacture a `Throwable` when the error parameter is arbitrary `E`.
5. **Inspect startup separately.** A mask inside a child does not prove the child starts before cancellation. For a custom `cancel = gate.get *> child.cancel`, inspect cancellation while the gate is closed. Masking that wait may restore uncancelability but introduce indefinite waiting; do not present it as a complete repair. Prefer an existing higher-level owner over adding forceStart to hide the unstarted state.
6. **Design a discriminating regression before changing code.** Use the repository's virtual scheduler or explicit barriers, not a lucky sleep. Retain the original public contracts; report unresolved schedules instead of calling them proved.

## Review and Refactoring Checks

Preserve these invariants: cancellation remains distinguishable from error; canceled-winner behavior matches each operator; parent cancellation cleans up owned children; memoize construction stays lazy; completed cache values stay consistent; canceled evaluation releases waiters; custom cancellation retains its target-version contract.

False positives: a legitimate `racePair` caller may deliberately retain the loser. A later memoize may legitimately use an internal fiber. The 2021 caller-fiber design is not a universal ban. An uncancelable child or finalizer can make cancellation itself wait forever; the `never/canceled` oracle below assumes a cancelable loser, not arbitrary uninterruptible work.

## Validation

Run only in a separately authorized upstream checkout: loading sbt executes build code. First inspect `build.sbt`, `project/build.properties`, plugins and test packages; then use `sbt projects` to confirm generated IDs. At the memoize SHA, `tests` is a JVM/JS cross-project, distinct from `core`:

- `sbt 'testsJVM/testOnly cats.effect.MemoizeSpec'`
- `sbt 'testsJS/testOnly cats.effect.MemoizeSpec'`

At the unmerged race SHA `f6917cccc1e2956982cd17f80696c7d220074ccb`, locate `laws/shared/src/test/scala/cats/effect/laws/GenSpawnSpec.scala`; confirm `lawsJVM` before running `sbt 'lawsJVM/testOnly cats.effect.laws.GenSpawnSpec'`. Treat its non-hanging property as an intended oracle, **not a reported pass for that proposal**.

Test `raceOutcome(never,canceled)` and its reversal, then parent cancellation while joining a live loser. For memoize, test no evaluation on outer allocation, repeated successful reads, self-cancellation, cancel/retry and late completion. The historical retry test expects two starts and one completion; the identity property checks `memoize(fa).flatten`. Use a non-Throwable error model as well as IO where the target abstraction supports it. No upstream compilation or tests were executed to author this skill.

## Examples

### Good

A reviewer keeps `race` and `raceOutcome` policies separate, then examines a shared low-level helper. For memoize at the 2021 revision, cancellation resets evaluation state and releases the latch while success/error publishes a stable result. The review requires both the identity property and cancel/retry observations, rather than accepting value-only tests.

### Broken and Correction

A helper waits for the loser whenever the first result is canceled; both public race methods delegate to it. With a cancelable never-ending loser, `raceOutcome` hangs. Adding cancellation handlers to both joins is a useful **partial correction**, not a semantic fix. Restore separate canceled-winner handling, retain handlers where joining is correct, and test both operand orders plus parent interruption. Do not copy the rejected `raceOutcomeBoth` implementation as the solution.

### Negative

A CE2 change retains its existing subscriber-counted memoizer and `Fiber.join: F[A]`. Do not demand a CE3 `Outcome` return type or caller-fiber algorithm. Similarly, do not flag an internal fiber in modern CE3 without first showing an observable mismatch with that version's contract.

## Output Contract

Return the target SHA/version/platform, changed outcome table, ownership trace and each finding's **file:line**, **severity**, **evidence**, and discriminating **test**. Separate confirmed semantic regressions, suspected schedules and benchmark concerns. State which commands ran and their observed results; proposed tests are not passes.

## Limitations

Historical reviews support the decision procedure, not a proof of all schedules. The unmerged startup proposal never establishes a complete repair. This skill intentionally excludes the unresolved Resource poll/map proposal and does not replace dynamic-resource ownership guidance.

## Sources

- [PR1552 interleaving review](https://github.com/typelevel/cats-effect/pull/1552#discussion_r549487584), followed by the author's revision and pinned source/tests in [references/evidence.json](references/evidence.json).
- [PR3232 false generalization](https://github.com/typelevel/cats-effect/pull/3232#issuecomment-1306535113) and [symmetric cleanup response](https://github.com/typelevel/cats-effect/pull/3232#discussion_r1059693032).
- [PR3123 cancelability objection](https://github.com/typelevel/cats-effect/pull/3123#discussion_r942473327). Attribute each participant's actual reasoning, not merge/approval status or an assumed lead-maintainer role.
