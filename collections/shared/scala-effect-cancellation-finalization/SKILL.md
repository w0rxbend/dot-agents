---
name: scala-effect-cancellation-finalization
description: Use when a Scala change alters how cancellation, failure and success are distinguished or how cleanup completes - Cats Effect race/memoize/Fiber.cancel outcomes and bracket/finalizer error provenance, ZIO cancel-token bridges and their evaluation executor, Play ApplicationLifecycle partial startup, stop() completion and CoordinatedShutdown draining. Covers outcome and finalization semantics of effect and lifecycle code, not stream scopes, HTTP protocol semantics or binary compatibility.
license: MIT
---

# Cancellation, failure and finalization semantics

Four historically grounded cases (Cats Effect 1/2/3, ZIO 2 RC-era, Play 2.x/3.x lifecycle) share one question: **when
computation ends by success, failure or cancellation, who observes which outcome, which cleanup still runs, who owns it,
on which thread it runs, and when is "done" truly done?** Version-pinned material (review quotes, commit links, test
oracles, sbt selectors) lives in one reference per case.

## When to Use

- Refactor shares one implementation across combinators with differing cancellation policies (`race` vs
  `raceOutcome`), changes memoization state, or wraps `Fiber.cancel` / startup gating.
- Change touches error combination during cleanup: bracket release failure, finalizer sequences, cancellation
  utilities, parallel or race error reporting, `addSuppressed`, runtime reporters.
- Bridge converts foreign/unsafe cancel token into effect, strict vs by-name constructor moves around `blocking`, or
  shutdown hangs on small compute pool.
- Lifecycle changes: `ApplicationLifecycle.stop()`, hook ordering, partial-startup cleanup, dev-mode startup hooks
  ported between Scala and Java, CoordinatedShutdown phases, unbind vs terminate/drain.
- Analogous code in other Scala libraries (Monix, fs2 internals, Ox, Pekko, custom lifecycles) with same invariants:
  use transferable checks below, mark library-specific claims unverified.

## When Not to Use

- Stream/resource scope propagation, per-element leases, sink emission cardinality: use
  `scala-stream-resource-scoping`.
- HTTP protocol framing, request-local error disclosure, middleware boundaries, channel hand-off: use
  `scala-http-server-semantics`.
- Binary/source compatibility or typeclass-law surfaces: use `scala-library-compatibility-laws`; general API contracts:
  `scala-library-contracts`.
- Runtime diagnostics and hot-path cost (including ZIO diagnostic-reader progress): use
  `scala-runtime-diagnostics-hot-paths`.
- General resource-management tutorials, logging policy, migrating to another effect system or build tool. Do not port
  CE3 `Outcome`/`Poll` into CE2, or Play's Future lifecycle into an effect runtime.
- Unsure which Scala skill applies: start at `scala-oss-library-review`.

## Prerequisites

1. Pin target: checkout SHA, library line (CE1/CE2/CE3, ZIO 1/2 and RC vs release, Play 2.6–3.x), Scala compiler, JDK,
   platform (JVM/JS/Native), backend (Akka/Pekko HTTP, Netty), mode (dev/prod/embedded).
2. Read concrete implementation **and** abstract contract separately (e.g. IO override vs `Bracket` / `GenSpawn`
   default; `succeedBlocking` body vs its name; Java port vs replaced Scala).
3. Read existing tests observing the behavior, even unrelated-looking assertions (logger counter, suppressed-array
   check, wrapped-cause check).
4. Load case reference(s) from routing table before applying any historical expectation.

## Shared model: invariants that recur across cases

Each invariant names its grounding case(s). "Grounded" means observed in pinned source/review; all else is labelled
inference.

**I1. Three outcomes, not two.** Success, failure and cancellation are distinct; per-operator policies differ. Reviewed
CE3 contract: `raceOutcome` cancels loser even when winner canceled; `race` waits for other result; `racePair` hands
over a live fiber (outcome case). Canceled memoize evaluation must not be cached as value or error, and must not invent
a `Throwable` for arbitrary `E` (outcome case). Merge two code paths only after their outcome tables agree for both
operand orders.

**I2. Primary result and secondary cleanup failures travel on separate channels.** Pinned CE1/CE2 IO, on use failure
plus release failure, returns original use throwable (same identity, suppressed array untouched); release failure goes
to runtime reporter (cleanup-provenance case). Play's lifecycle recovers failed hook, still runs remaining hooks (Play
case). Secondary failure must not replace primary result, must not vanish, must not mutate a possibly shared exception.

**I3. Completion means cleanup finished, for every observer.** Interrupting bridged ZIO effect must invoke underlying
token and await finalization, not only end outer observer (ZIO case). Every `stop()` caller must get a Future completing
after last hook; losing caller must not get immediate success (Play case). Canceled memoize evaluation must release
waiters. Parent canceled while joining race loser must cancel that loser on both symmetric branches (outcome case).
Once-only *execution* (CAS, release-once guard, invocation counter) is not completed *cleanup*. CE2 also awaits
already-running release via Promise (cleanup-provenance case).

**I4. Every live child or acquired resource has a reachable owner at every failure point.** Play keeps lifecycle
cleanup reachable when `ApplicationLoader.load` throws before an Application exists (Play case, PR 8406). Race loser
fiber has an owner after combinator returns (outcome case). Partial acquisition after last observed event: open
question, not proven leak or proven safety (Play case).

**I5. The moment of evaluation, and its executor, is part of the contract.** ZIO's blocking canceler, evaluated by
strict constructor before `blocking` shift, starved cleanup on small compute pool. Fix suspends only cancel invocation
(`blocking(ZIO.succeed(a))`), not whole workload (ZIO case). Play's Java port turned lazy vals into eager construction,
running user code / watcher before `beforeStarted` (Play case). Memoize construction must stay lazy (outcome case).
**Counter-rule:** laziness is not automatically safer. Immutable snapshot taken inside its owning callback can move
onto foreign fiber if deferred (ZIO PR 8819 review). Establish owner first, strictness second.

**I6. Cancellation and shutdown must themselves make bounded progress.** `Fiber.cancel` waiting on startup gate is a
cancelable cancel; CE3 review rejected it. Masking that wait can make cancel hang instead (outcome case, unmerged PR
3123). Synchronous cancel token awaiting cleanup must not occupy the executor cleanup needs (ZIO case). Shutdown task
must not await the CoordinatedShutdown run awaiting it. Outer waits stay finite, not `Duration.Inf`, with fallback from
owning API (`cs.timeout(PhaseServiceUnbind)`) (Play case). Uncancelable child can make any cancellation wait forever;
oracles must assume cancelable loser (outcome case).

**I7. Ordering is a completion edge, not textual order.** Hooks run LIFO, sequentially, each after previous hook's
Future (Play case). Same-phase CoordinatedShutdown tasks may run concurrently, so dependency needs Future composition or
later phase (Play case). Error-reporting fixes must not reorder registration/removal or skip later finalizers
(cleanup-provenance case).

**I8. Concrete implementation vs polymorphic contract.** CE IO regression is not a `Bracket` law for every effect (PR
394). CE2 `Fiber.join: F[A]` is not CE3 `Outcome` (outcome case). March-2022 ZIO bridge APIs are not current ZIO (ZIO
case). Play's January 2020 server still places logger and user hook in one phase, so reviewer requests are not proven
repository invariants (Play case). In every finding, distinguish observed code, reviewer proposal, merged decision and
your inference.

## Routing table

| Change touches | Load |
| --- | --- |
| CE `IOBracket` / `ReleaseRecover`, `composeErrors`, `CancelUtils`, parallel/race error reporting, `addSuppressed`, stderr / runtime reporter, throwing `Bracket` release | [references/cats-effect-cleanup-error-provenance.md](references/cats-effect-cleanup-error-provenance.md) |
| CE3 `GenSpawn` `race` / `raceOutcome` / `racePair`, `GenConcurrent.memoize`, `Fiber.cancel` wrappers, startup gates / forceStart, `Outcome`/`Poll`, CE2 vs CE3 port | [references/cats-effect-outcome-sensitive-concurrency.md](references/cats-effect-outcome-sensitive-concurrency.md) |
| ZIO `Runtime.run`, `unsafeRunAsyncCancelable`, `asyncInterrupt`, `succeedBlocking` / `blocking` / `succeedNow` vs `succeed`, ZIOApp interruption, logger-on-failure, compute-pool shutdown hang, eager vs lazy callback snapshot | [references/zio-canceler-evaluation-owner.md](references/zio-canceler-evaluation-owner.md) |
| Play `ApplicationLifecycle` / `DefaultApplicationLifecycle`, `ApplicationLoader.load` failure, `DevServerRunner` / `RunHook.beforeStarted` / `assetsClassLoader` / `DevServerReloader`, `AkkaHttpServer` stop, `CoordinatedShutdown` phases, binding unbind vs terminate | [references/play-partial-startup-shutdown-completion.md](references/play-partial-startup-shutdown-completion.md) |
| Analogous code elsewhere (other effect runtimes, custom lifecycles, Pekko shutdown) | This file's workflow, then closest reference's oracles, marked transferred |

Pinned evidence (byte copies of originals): `references/evidence/`, one JSON per case, linked from each reference.

## Workflow

1. **Pin and classify.** Record versions/platform/mode (Prerequisites). Classify change: outcome policy (I1),
   cleanup-error channel (I2), completion meaning (I3), ownership on failure (I4), evaluation timing/executor (I5),
   cancellation's own progress (I6), ordering (I7). Load routed reference(s).
2. **Write the outcome × observer table.** Rows: success, failure, self-cancellation, parent/external cancellation,
   failure during cleanup, simultaneous failures; both operand orders for binary combinators. Columns: value returned to
   caller, reporter/log output, finalizers run and order, live children left, completion time per observer (each
   `stop()` caller, each memoize waiter, interrupter). Fill before and after change.
3. **Trace the evaluation path.** Per cleanup/cancel action: where constructed, where invoked, which
   fiber/thread/executor owns invocation, what it waits on. Expand wrappers until strictness shows (by-name into strict
   constructor; lazy val into eager Java field). Mark actions evaluated during construction.
4. **Trace ownership at each failure point.** Per acquisition/fork, name owner that cancels/closes it if next step
   fails, including before the "success object" (Application, joined result) exists.
5. **Trace all siblings of a changed helper.** Before changing or deleting a shared helper, search definitions and
   usages (JVM and JS sources, race and parallel paths, neighbouring bridge wrappers, both symmetric branches).
6. **Check progress and bounds.** Find waits inside cancel/shutdown paths: gates, `OneShot.get`, self-awaiting shutdown
   tasks, unbounded outer waits, phase budgets eaten by sequential per-binding waits.
7. **Choose the minimal correction.** Fix the semantics' owner (e.g. `Runtime.run`, not only ZIOApp; separate
   canceled-winner policy, not only extra `onCancel`). Keep existing independent observations (logger test, wrapped
   cause test, suppressed-array check); do not weaken them.
8. **Design a discriminating regression** with explicit barriers/startup signals or repository's virtual scheduler, not
   sleeps; finite external deadlines; thread-safe traces. Name mutation each test must kill.

## Review and Refactoring Checks

Transferable (any Scala effect or lifecycle code):

- [ ] Cancellation stays distinguishable from error at every return type exposing it (I1).
- [ ] Helpers shared only where per-operator outcome policies agree, both operand orders (I1).
- [ ] Secondary cleanup errors neither replace primary result nor disappear; no `addSuppressed` on possibly shared
      throwable; preexisting suppressed entries unchanged (I2).
- [ ] Every observer's completion follows last cleanup effect; no early `successful` for losing callers (I3).
- [ ] Once-only guards not mistaken for completed cleanup; already-running release awaited where target does so (I3).
- [ ] Parent cancellation during join/wait cancels owned child on every branch (I3, I4).
- [ ] Cleanup reachable when construction fails midway (I4).
- [ ] No cleanup/cancel action evaluated at construction time; blocking cancel waits do not run on the executor
      cleanup needs (I5).
- [ ] Laziness not demanded blindly: owner-confined eager snapshots are legitimate (I5 counter-rule).
- [ ] Cancel itself not cancelable/gated indefinitely; shutdown has no self-wait; outer waits finite (I6).
- [ ] Cleanup-task dependencies are real completion edges, not registration order or same-phase placement (I7).
- [ ] Later finalizers still run after earlier one fails; LIFO preserved where promised (I2, I7).

Library/version-specific (verify against pinned target before applying):

- CE1/CE2 IO: release failure goes to reporter (`System.err` in those snapshots); CE2 release Promise wait. CE3
  reporter behavior not established.
- CE3 (2021 pre-release memoize; unmerged PR 3232 race / PR 3123 forceStart): `raceOutcome` vs `race` canceled-winner
  policy; memoize cancel resets state, releases latch; retry test expects two starts, one completion.
- ZIO `series/2.x` March 2022: `succeedBlocking = blocking(ZIO.succeed(a))`; token invocation waits on `OneShot.get`.
- Play: `DefaultApplicationLifecycle` CAS, deque, shared Promise (2018); `cs.timeout(PhaseServiceUnbind)` fallback and
  binding terminate (2020, Akka HTTP); `beforeStarted` before `assetsClassLoader`/reloader in Java run-support (2024).

## Consolidated false positives

- Immutable domain-error aggregation with documented policy, or new adapter-owned exception collecting suppressed
  errors: not reusable-Throwable mutation (cleanup-provenance).
- Custom `Bracket` returning aggregate is not wrong because CE1 IO reports to stderr; throwing release function needs
  own concrete analysis (cleanup-provenance, PR 394).
- `racePair` caller may deliberately keep loser; later memoize may legitimately use internal fiber; 2021 caller-fiber
  design is not a universal ban (outcome).
- Uncancelable child can make cancellation wait forever; not a race-combinator bug (outcome).
- CE2 subscriber-counted memoizer with `Fiber.join: F[A]` is not missing CE3 `Outcome` (outcome).
- Not eager-evaluation defects: cancel token only scheduling nonblocking cancellation, already-computed immutable
  value, eager snapshot inside its legitimate owner. `ensuring` after guarded effect begins is fine. Larger compute
  pool hiding a hang is not proof of equivalence (ZIO).
- Internal AtomicBoolean/Promise mutation in Play's lifecycle is observed design. Independent same-phase tasks may run
  concurrently. Genuinely completed hook may return already-successful Future. Moving already-computed port number
  into a local changes no timing (Play).
- Untraced helper is investigation gap, not confirmed deadlock or leak (all cases).

## Version fences

| Case | Pinned evidence | Do not assume for |
| --- | --- | --- |
| Cleanup provenance | CE1 `c6d7dd5e` (Scala 2.11.12/2.12.7/2.13.0-M5, default 2.12.6; Cats 1.5.0; JVM+JS); CE2 `1b51cb14` | CE3 reporter behavior; other effects' `Bracket` |
| Outcome concurrency | CE3 pre-release `000758b0` (memoize, merged); `f6917ccc` (race, unmerged); PR 3123 (unmerged); CE2 `1b51cb14` (2.6; Scala 2.12.15/2.13.8/3.0.2; Scala.js 1.7.1) | Every CE3 release; CE2 APIs |
| ZIO canceler | `60d47847` `series/2.x` March 2022, RC-era (sbt 1.6.2; Scala 2.11.12/2.12.15/2.13.8/3.1.1; JDK 17 + 8/11) | Released ZIO 2 `Unsafe` APIs; Native (test = compile) |
| Play lifecycle | 2018 `6059f791`; 2020 `5b4eaf91` (Akka HTTP); 2024 `15cf5d6b` (Java run-support); build eras 2020/2022/2024 (Akka → Pekko, IntegrationTest → Test) | Same-year PRs' dependency versions; today's Akka/Pekko |

## Validation

- **No upstream build or test ran while researching or authoring any case.** Every command in references is a future
  instruction for separately authorized, isolated checkout; loading sbt executes build code.
- **Discover targets first:** read `build.sbt`, `project/build.properties`, `project/plugins.sbt` (and
  `project/BuildHelper.scala` / `BuildSettings.scala` where present), CI selectors, test package names; then
  `sbt projects` (Play also: `sbt 'show Play / Test / definedTests'`). Test projects often separate from production
  modules (`lawsJVM`, `testsJVM`, `coreTestsJVM`, `Play-Run-Support`, `Sbt-Plugin`).
- **Require nonzero execution** of selected suite and specific cases; green command with zero tests proves nothing.
  Structural skill/schema checks prove no runtime property.
- **Run each platform independently** (JVM, JS); Native in ZIO snapshot only compiles.
- **Global sinks and timing:** capture-based tests (e.g. `System.err`) need serialized execution and restoration on
  failure; constrained-executor tests need external deadline; scripted Play tests need matching locally published
  artifacts without silently publishing into user's cache.
- Concrete selectors and oracles: each reference's Validation section.

## Examples

### Good

PR unifies CE3 race internals. Reviewer writes outcome table for `race` and `raceOutcome` in both operand orders, finds
canceled-winner rows differ, keeps those paths separate, adds parent-cancel-during-join tests for both branches (I1,
I3; outcome reference). Checking a ZIO bridge in same codebase, same reviewer confirms cancel token is invoked inside
`blocking(ZIO.succeed(...))` and interrupt completion waits for finalizer flag (I3, I5; ZIO reference).

### Broken and Correction

Lifecycle refactor (a) returns `Future.successful(Done)` to every `stop()` caller after the first and (b) in cleanup
calls `primary.addSuppressed(hookError)` before rethrowing. Tests check only invocation count and returned error. Both
are I3/I2 violations hidden by weak oracles. Composite illustrative example, not a single historical PR.
Correction: share pending completion Promise across callers. Recover hook failure without mutating primary throwable
(keep it observable through whatever secondary channel target already uses); keep running remaining hooks LIFO. Add
barrier test holding last hook while two callers observe pending Futures, and repeated-evaluation test asserting
unchanged suppressed arrays (Play and cleanup-provenance references).

### Negative

ZIO callback eagerly reads mutable child state inside its owning fiber, returns immutable snapshot. Reviewer cites I5
to demand laziness. Reject: counter-rule applies. Eager read is owner-confined; deferring it would execute on foreign
caller (ZIO reference, PR 8819). Likewise, do not flag a CE2 memoizer for lacking `Outcome` (I8).

## Output Contract

1. Target: SHA, library line, Scala/JDK, platform, backend/mode.
2. Outcome × observer table (before/after) and evaluation/ownership trace for touched actions.
3. Findings, each with `file:line`, severity, violated invariant (I1–I8), evidence (pinned citation or evidence ID from
   `references/evidence/`), minimal correction, discriminating test naming the mutation it kills.
4. Separate: observed source, reviewer proposal, merged decision, your inference; confirmed defects vs missing
   assertions vs suspected schedules vs investigation gaps.
5. Commands actually executed with results, vs proposed tests, vs blocked by prerequisites. Explicit no-finding when
   trace is preserved.

## Limitations

- Each case rests on few pinned snapshots and review threads. Together they support a decision procedure, not proof
  over all schedules or universal leak freedom.
- Several grounding proposals unmerged (CE PR 3232 race helper, PR 3123 forceStart); ZIO PR 8819's design superseded.
  Their review arguments are used, not their code.
- Newer lines (CE3 releases, released ZIO 2 `Unsafe` APIs, Pekko-era Play) must be re-read before applying any
  historical expectation.
- Reviewer logins identify participants only; formal maintainer roles not verified.
- Evaluated by model-based review of source and history; no upstream build, signal delivery or constrained-executor
  experiment ran, and no effectiveness measurement against a baseline agent exists.

## Sources

- [Cats Effect cleanup-error provenance](references/cats-effect-cleanup-error-provenance.md): evidence
  [JSON](references/evidence/scala-cats-effect-cleanup-error-provenance.json); PR 458, PR 394.
- [Cats Effect outcome-sensitive concurrency](references/cats-effect-outcome-sensitive-concurrency.md): evidence
  [JSON](references/evidence/scala-cats-effect-outcome-sensitive-concurrency.json); PR 1552, PR 3232, PR 3123.
- [ZIO canceler evaluation owner](references/zio-canceler-evaluation-owner.md): evidence
  [JSON](references/evidence/scala-zio-canceler-evaluation-owner.json); PR 6401, PR 8819.
- [Play partial startup and shutdown completion](references/play-partial-startup-shutdown-completion.md): evidence
  [JSON](references/evidence/scala-play-partial-startup-shutdown-completion.json); PR 8406, PR 9970, PR 12210.
