# Cats Effect 3: outcome-sensitive concurrency (originally scala-cats-effect-outcome-sensitive-concurrency)

Evidence: [evidence/scala-cats-effect-outcome-sensitive-concurrency.json](evidence/scala-cats-effect-outcome-sensitive-concurrency.json)
(claims `ce-claim-cancellation-outcomes`, `ce-claim-startup-ownership`, `ce-claim-ce2-boundary`).

## Scope

CE3 kernel/runtime changes that share race implementations, alter memoized evaluation state, or wrap `Fiber.cancel`.
Review the outcome table before simplifying the implementation. A canceled computation is not an ordinary failed value.

Not for general Resource acquisition/registration, FS2 scope leases, ZIO cancel-token evaluation, or ordinary Future
completion. Do not transplant CE3 `Outcome` or `Poll` into CE2. Preserve the project's effect library, syntax and sbt
build. The unresolved Resource poll/map proposal is intentionally excluded.

## Version and source boundaries

- **memoize:** pre-release Cats Effect 3 at `000758b0b5e1ae12161845dc472bf148459ca237` (PR1552, merged revision), not a
  specification of every CE3 release.
- **race:** PR3232 head `f6917cccc1e2956982cd17f80696c7d220074ccb` is **unmerged**; `raceOutcomeBoth` there is a
  proposal, not an API to import.
- **forceStart:** PR3123 is **unmerged**; the final patch does not resolve the cancelability objection.
- **CE2 comparison** at `1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e` (base version 2.6; Scala 2.12.15 / 2.13.8 / 3.0.2;
  Scala.js 1.7.1, crossproject 1.2.0 per `ce2-build-versions`, `ce2-build-platform`): `Fiber[F,A].join: F[A]`
  ([source](https://github.com/typelevel/cats-effect/blob/1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e/core/shared/src/main/scala/cats/effect/Fiber.scala#L55-L76)),
  subscriber-counted memoization ([source](https://github.com/typelevel/cats-effect/blob/1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e/core/shared/src/main/scala/cats/effect/Concurrent.scala#L467-L486)),
  `ExitCase` and `ContextShift`; no CE3 outcome-returning join. Use the comparison to stop an invalid port, not to claim
  equivalence.

Read the target commit's build, kernel API, concrete IO overrides and test definitions; record Scala, Cats Effect and
platform versions.

## Review history (attributed)

- PR1552 memoize: RaasAhsan, [interleaving](https://github.com/typelevel/cats-effect/pull/1552#discussion_r549487584):
  "The first fetch actually terminates before it observes cancellation, so it caches the result." djspiewak,
  [error parametricity](https://github.com/typelevel/cats-effect/pull/1552#discussion_r549487047): "given that we don't
  know `E`, I'm not sure how we could do that here." djspiewak,
  [state machine](https://github.com/typelevel/cats-effect/pull/1552#issuecomment-752161323): "If evaluation completes
  with `Canceled`, then allow that to propagate through and release one of the blocked callers to attempt evaluation on
  *their* fiber". The author [reports implementing it](https://github.com/typelevel/cats-effect/pull/1552#issuecomment-755377643);
  the pinned source ([transition](https://github.com/typelevel/cats-effect/blob/000758b0b5e1ae12161845dc472bf148459ca237/kernel/shared/src/main/scala/cats/effect/kernel/GenConcurrent.scala#L48-L66))
  and re-enabled law provide independent context; not evidence that this research executed the tests.
- PR3232 race: the author, [false generalization](https://github.com/typelevel/cats-effect/pull/3232#issuecomment-1306535113):
  "`raceOutcome` and `race` vary in how they deal with the scenario that the winning fiber completed in cancelation."
  durban, [cancel gap](https://github.com/typelevel/cats-effect/pull/3232#discussion_r1059691576): "if one is canceled,
  and then the race is canceled while trying the join the other, then the other will not be canceled." armanbilge,
  [response](https://github.com/typelevel/cats-effect/pull/3232#discussion_r1059693032): "this needs an
  `.onCancel(f.cancel)`. And same below." The head source contains the handlers
  ([GenSpawn](https://github.com/typelevel/cats-effect/blob/f6917cccc1e2956982cd17f80696c7d220074ccb/kernel/shared/src/main/scala/cats/effect/kernel/GenSpawn.scala#L313-L330));
  that local repair does not solve the separate false-generalization problem.
- PR3123 forceStart: durban, [objection](https://github.com/typelevel/cats-effect/pull/3123#discussion_r942473327):
  "This creates a fiber with a cancelable `cancel`, which is not allowed." djspiewak,
  [states](https://github.com/typelevel/cats-effect/pull/3123#issuecomment-1250643900): "Fibers are, fundamentally,
  three state objects: **unstarted**, **started**, and **completed**." Waiting for startup merely changes liveness.

Attribute each participant's actual reasoning, not merge/approval status or an assumed lead-maintainer role.

## Workflow

1. **Locate the semantic owner.** Trace syntax to the typeclass default and any IO override. Identify whether the caller
   receives a value, an `Outcome`, or a live loser fiber. Write down who must cancel or join that fiber after the
   combinator returns.
2. **Build the outcome table.** For both operand orders, enumerate success, error, self-cancellation and parent
   cancellation. In the reviewed CE3 contract, `raceOutcome` cancels the loser even when the winner canceled; `race`
   instead waits for the other result in that case. `racePair` transfers a live fiber handle. Share only implementation
   steps whose policies actually agree.
3. **Trace interrupted waits.** At each polled loser join, cancel the parent after entering the wait. Check that the
   remaining child is canceled on both symmetric branches. A local `onCancel(f.cancel)` repair fixes that ownership
   hole; it cannot fix the wrong canceled-winner policy.
4. **Model memoize transitions.** Unevaluated, evaluating and finished states; evaluation owner; subscriber bookkeeping;
   waiter wakeup. Interleave cancellation request, actual cancellation observation, a second get, and late completion.
   Require one consistent cached success/error, no abandoned waiters, and the target version's retry semantics. Do not
   manufacture a `Throwable` when the error parameter is arbitrary `E`.
5. **Inspect startup separately.** A mask inside a child does not prove the child starts before cancellation. For a
   custom `cancel = gate.get *> child.cancel`, inspect cancellation while the gate is closed. Masking that wait may
   restore uncancelability but introduce indefinite waiting; do not present it as a complete repair. Prefer an existing
   higher-level owner over adding forceStart to hide the unstarted state.
6. **Design a discriminating regression before changing code.** Use the repository's virtual scheduler or explicit
   barriers, not a lucky sleep. Retain the original public contracts; report unresolved schedules instead of calling
   them proved.

## Checks

Preserve: cancellation remains distinguishable from error; canceled-winner behavior matches each operator; parent
cancellation cleans up owned children; memoize construction stays lazy; completed cache values stay consistent;
canceled evaluation releases waiters; custom cancellation retains its target-version contract.

False positives:

- A legitimate `racePair` caller may deliberately retain the loser.
- A later memoize may legitimately use an internal fiber; the 2021 caller-fiber design is not a universal ban.
- An uncancelable child or finalizer can make cancellation itself wait forever; the `never/canceled` oracle assumes a
  cancelable loser, not arbitrary uninterruptible work.

## Validation

Run only in a separately authorized upstream checkout: loading sbt executes build code. Inspect `build.sbt`,
`project/build.properties`, plugins and test packages; then `sbt projects`. At the memoize SHA, `tests` is a JVM/JS
cross-project distinct from `core` ([build](https://github.com/typelevel/cats-effect/blob/000758b0b5e1ae12161845dc472bf148459ca237/build.sbt#L224-L234)):

- `sbt 'testsJVM/testOnly cats.effect.MemoizeSpec'`
- `sbt 'testsJS/testOnly cats.effect.MemoizeSpec'`

At the unmerged race SHA `f6917cccc1e2956982cd17f80696c7d220074ccb`, locate
`laws/shared/src/test/scala/cats/effect/laws/GenSpawnSpec.scala`; confirm `lawsJVM` before running
`sbt 'lawsJVM/testOnly cats.effect.laws.GenSpawnSpec'`. Its "raceOutcome should not hang" property
([source](https://github.com/typelevel/cats-effect/blob/f6917cccc1e2956982cd17f80696c7d220074ccb/laws/shared/src/test/scala/cats/effect/laws/GenSpawnSpec.scala#L27-L36))
is an intended oracle, **not a reported pass for that proposal**.

Oracles: `raceOutcome(never, canceled)` and its reversal, then parent cancellation while joining a live loser. For
memoize: no evaluation on outer allocation, repeated successful reads, self-cancellation, cancel/retry and late
completion. The historical [retry test](https://github.com/typelevel/cats-effect/blob/000758b0b5e1ae12161845dc472bf148459ca237/tests/shared/src/test/scala/cats/effect/MemoizeSpec.scala#L160-L178)
expects two starts and one completion; the [identity property](https://github.com/typelevel/cats-effect/blob/000758b0b5e1ae12161845dc472bf148459ca237/tests/shared/src/test/scala/cats/effect/MemoizeSpec.scala#L93-L95)
checks `memoize(fa).flatten`. Use a non-Throwable error model as well as IO where the abstraction supports it. CE2
Resource interruption context: [interpreter](https://github.com/typelevel/cats-effect/blob/1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e/core/shared/src/main/scala/cats/effect/Resource.scala#L117-L134),
[test](https://github.com/typelevel/cats-effect/blob/1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e/laws/shared/src/test/scala/cats/effect/ResourceTests.scala#L175-L197).

No upstream compilation or tests were executed to author this case.

## Examples

- **Good.** A reviewer keeps `race` and `raceOutcome` policies separate, then examines a shared low-level helper. For
  memoize at the 2021 revision, cancellation resets evaluation state and releases the latch while success/error
  publishes a stable result. The review requires both the identity property and cancel/retry observations.
- **Broken and correction.** A helper waits for the loser whenever the first result is canceled; both public race
  methods delegate to it. With a cancelable never-ending loser, `raceOutcome` hangs. Adding cancellation handlers to
  both joins is a useful **partial correction**, not a semantic fix. Restore separate canceled-winner handling, retain
  handlers where joining is correct, and test both operand orders plus parent interruption. Do not copy the rejected
  `raceOutcomeBoth` implementation as the solution.
- **Negative.** A CE2 change retains its subscriber-counted memoizer and `Fiber.join: F[A]`. Do not demand a CE3
  `Outcome` return type or caller-fiber algorithm. Do not flag an internal fiber in modern CE3 without first showing an
  observable mismatch with that version's contract.

## Output

Target SHA/version/platform, changed outcome table, ownership trace, and each finding's **file:line**, **severity**,
**evidence**, and discriminating **test**. Separate confirmed semantic regressions, suspected schedules and benchmark
concerns. State which commands ran; proposed tests are not passes.

## Limitations

Historical reviews support the decision procedure, not a proof of all schedules. The unmerged startup proposal never
establishes a complete repair. Does not replace dynamic-resource ownership guidance.
