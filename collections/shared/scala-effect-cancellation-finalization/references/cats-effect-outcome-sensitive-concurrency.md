# Cats Effect 3: outcome-sensitive concurrency (originally scala-cats-effect-outcome-sensitive-concurrency)

Evidence: [evidence/scala-cats-effect-outcome-sensitive-concurrency.json](evidence/scala-cats-effect-outcome-sensitive-concurrency.json)
(claims `ce-claim-cancellation-outcomes`, `ce-claim-startup-ownership`, `ce-claim-ce2-boundary`).

## Scope

CE3 kernel/runtime changes that share race implementations, alter memoized evaluation state, or wrap `Fiber.cancel`.
Review outcome table before simplifying implementation. Canceled computation is not ordinary failed value.

Not for general Resource acquisition/registration, FS2 scope leases, ZIO cancel-token evaluation, or ordinary Future
completion. Do not transplant CE3 `Outcome` or `Poll` into CE2. Preserve project's effect library, syntax, sbt build.
Unresolved Resource poll/map proposal intentionally excluded.

## Version and source boundaries

- **memoize:** pre-release Cats Effect 3 at `000758b0b5e1ae12161845dc472bf148459ca237` (PR1552, merged revision); not
  specification of every CE3 release.
- **race:** PR3232 head `f6917cccc1e2956982cd17f80696c7d220074ccb` is **unmerged**; its `raceOutcomeBoth` is proposal,
  not API to import.
- **forceStart:** PR3123 is **unmerged**; final patch does not resolve cancelability objection.
- **CE2 comparison** at `1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e` (base version 2.6; Scala 2.12.15 / 2.13.8 / 3.0.2;
  Scala.js 1.7.1, crossproject 1.2.0 per `ce2-build-versions`, `ce2-build-platform`): `Fiber[F,A].join: F[A]`
  ([source](https://github.com/typelevel/cats-effect/blob/1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e/core/shared/src/main/scala/cats/effect/Fiber.scala#L55-L76)),
  subscriber-counted memoization ([source](https://github.com/typelevel/cats-effect/blob/1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e/core/shared/src/main/scala/cats/effect/Concurrent.scala#L467-L486)),
  `ExitCase` and `ContextShift`; no CE3 outcome-returning join. Use comparison to stop invalid port, not to claim
  equivalence.

Read target commit's build, kernel API, concrete IO overrides, test definitions; record Scala, Cats Effect, platform
versions.

## Review history (attributed)

- PR1552 memoize: RaasAhsan, [interleaving](https://github.com/typelevel/cats-effect/pull/1552#discussion_r549487584):
  "The first fetch actually terminates before it observes cancellation, so it caches the result." djspiewak,
  [error parametricity](https://github.com/typelevel/cats-effect/pull/1552#discussion_r549487047): "given that we don't
  know `E`, I'm not sure how we could do that here." djspiewak,
  [state machine](https://github.com/typelevel/cats-effect/pull/1552#issuecomment-752161323): "If evaluation completes
  with `Canceled`, then allow that to propagate through and release one of the blocked callers to attempt evaluation on
  *their* fiber". Author [reports implementing it](https://github.com/typelevel/cats-effect/pull/1552#issuecomment-755377643);
  pinned source ([transition](https://github.com/typelevel/cats-effect/blob/000758b0b5e1ae12161845dc472bf148459ca237/kernel/shared/src/main/scala/cats/effect/kernel/GenConcurrent.scala#L48-L66))
  and re-enabled law give independent context, not evidence this research executed the tests.
- PR3232 race: author, [false generalization](https://github.com/typelevel/cats-effect/pull/3232#issuecomment-1306535113):
  "`raceOutcome` and `race` vary in how they deal with the scenario that the winning fiber completed in cancelation."
  durban, [cancel gap](https://github.com/typelevel/cats-effect/pull/3232#discussion_r1059691576): "if one is canceled,
  and then the race is canceled while trying the join the other, then the other will not be canceled." armanbilge,
  [response](https://github.com/typelevel/cats-effect/pull/3232#discussion_r1059693032): "this needs an
  `.onCancel(f.cancel)`. And same below." Head source contains the handlers
  ([GenSpawn](https://github.com/typelevel/cats-effect/blob/f6917cccc1e2956982cd17f80696c7d220074ccb/kernel/shared/src/main/scala/cats/effect/kernel/GenSpawn.scala#L313-L330)).
- PR3123 forceStart: durban, [objection](https://github.com/typelevel/cats-effect/pull/3123#discussion_r942473327):
  "This creates a fiber with a cancelable `cancel`, which is not allowed." djspiewak,
  [states](https://github.com/typelevel/cats-effect/pull/3123#issuecomment-1250643900): "Fibers are, fundamentally,
  three state objects: **unstarted**, **started**, and **completed**." Waiting for startup only changes liveness.

Attribute each participant's actual reasoning, not merge/approval status or assumed lead-maintainer role.

## Workflow

1. **Locate the semantic owner.** Trace syntax to typeclass default and any IO override. Does caller receive value,
   `Outcome`, or live loser fiber? Record who must cancel or join that fiber after combinator returns.
2. **Build the outcome table.** Both operand orders: success, error, self-cancellation, parent cancellation. Reviewed
   CE3 contract: `raceOutcome` cancels loser even when winner canceled; `race` instead waits for other result there.
   `racePair` transfers live fiber handle. Share only implementation steps whose policies agree.
3. **Trace interrupted waits.** At each polled loser join, cancel parent after wait starts. Check remaining child gets
   canceled on both symmetric branches. Local `onCancel(f.cancel)` repair fixes that ownership hole; it cannot fix
   wrong canceled-winner policy.
4. **Model memoize transitions.** States unevaluated, evaluating, finished; evaluation owner; subscriber bookkeeping;
   waiter wakeup. Interleave cancellation request, actual cancellation observation, second get, late completion.
   Require one consistent cached success/error, no abandoned waiters, target version's retry semantics. Do not
   manufacture `Throwable` when error parameter is arbitrary `E`.
5. **Inspect startup separately.** Mask inside child does not prove child starts before cancellation. For custom
   `cancel = gate.get *> child.cancel`, inspect cancellation while gate closed. Masking that wait may restore
   uncancelability but add indefinite waiting; do not present it as complete repair. Prefer existing higher-level
   owner over adding forceStart to hide unstarted state.
6. **Design a discriminating regression before changing code.** Use repository's virtual scheduler or explicit
   barriers, not lucky sleep. Keep original public contracts; report unresolved schedules, do not call them proved.

## Checks

Preserve: cancellation stays distinguishable from error; canceled-winner behavior matches each operator; parent
cancellation cleans up owned children; memoize construction stays lazy; completed cache values stay consistent;
canceled evaluation releases waiters; custom cancellation keeps target-version contract.

False positives:

- Legitimate `racePair` caller may deliberately retain loser.
- Later memoize may legitimately use internal fiber; 2021 caller-fiber design is not universal ban.
- Uncancelable child or finalizer can make cancellation itself wait forever; `never/canceled` oracle assumes
  cancelable loser, not arbitrary uninterruptible work.

## Validation

Run only in separately authorized upstream checkout: loading sbt executes build code. Inspect `build.sbt`,
`project/build.properties`, plugins, test packages; then `sbt projects`. At memoize SHA, `tests` is JVM/JS
cross-project separate from `core` ([build](https://github.com/typelevel/cats-effect/blob/000758b0b5e1ae12161845dc472bf148459ca237/build.sbt#L224-L234)):

- `sbt 'testsJVM/testOnly cats.effect.MemoizeSpec'`
- `sbt 'testsJS/testOnly cats.effect.MemoizeSpec'`

At unmerged race SHA `f6917cccc1e2956982cd17f80696c7d220074ccb`, locate
`laws/shared/src/test/scala/cats/effect/laws/GenSpawnSpec.scala`; confirm `lawsJVM` before running
`sbt 'lawsJVM/testOnly cats.effect.laws.GenSpawnSpec'`. Its "raceOutcome should not hang" property
([source](https://github.com/typelevel/cats-effect/blob/f6917cccc1e2956982cd17f80696c7d220074ccb/laws/shared/src/test/scala/cats/effect/laws/GenSpawnSpec.scala#L27-L36))
is intended oracle, **not a reported pass for that proposal**.

Oracles: `raceOutcome(never, canceled)` and reversal, then parent cancellation while joining live loser. Memoize: no
evaluation on outer allocation, repeated successful reads, self-cancellation, cancel/retry, late completion.
Historical [retry test](https://github.com/typelevel/cats-effect/blob/000758b0b5e1ae12161845dc472bf148459ca237/tests/shared/src/test/scala/cats/effect/MemoizeSpec.scala#L160-L178)
expects two starts, one completion; [identity property](https://github.com/typelevel/cats-effect/blob/000758b0b5e1ae12161845dc472bf148459ca237/tests/shared/src/test/scala/cats/effect/MemoizeSpec.scala#L93-L95)
checks `memoize(fa).flatten`. Where abstraction supports it, use non-Throwable error model as well as IO. CE2
Resource interruption context: [interpreter](https://github.com/typelevel/cats-effect/blob/1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e/core/shared/src/main/scala/cats/effect/Resource.scala#L117-L134),
[test](https://github.com/typelevel/cats-effect/blob/1b51cb1411adcfec5daf8dc1a9557d3e554bbe4e/laws/shared/src/test/scala/cats/effect/ResourceTests.scala#L175-L197).

No upstream compilation or tests ran to author this case.

## Examples

- **Good.** Reviewer keeps `race` and `raceOutcome` policies separate, then examines shared low-level helper. Memoize
  at 2021 revision: cancellation resets evaluation state and releases latch; success/error publishes stable result.
  Review requires both identity property and cancel/retry observations.
- **Broken and correction.** Helper waits for loser whenever first result is canceled; both public race methods
  delegate to it. With cancelable never-ending loser, `raceOutcome` hangs. Cancellation handlers on both joins are
  useful **partial correction**, not semantic fix. Restore separate canceled-winner handling, keep handlers where
  joining is correct, test both operand orders plus parent interruption. Do not copy rejected `raceOutcomeBoth`
  implementation as solution.
- **Negative.** CE2 change keeps subscriber-counted memoizer and `Fiber.join: F[A]`. Do not demand CE3 `Outcome`
  return type or caller-fiber algorithm. Do not flag internal fiber in modern CE3 without first showing observable
  mismatch with that version's contract.

## Output

Target SHA/version/platform, changed outcome table, ownership trace; per finding **file:line**, **severity**,
**evidence**, discriminating **test**. Separate confirmed semantic regressions, suspected schedules, benchmark
concerns. State which commands ran; proposed tests are not passes.

## Limitations

Historical reviews support decision procedure, not proof of all schedules.
