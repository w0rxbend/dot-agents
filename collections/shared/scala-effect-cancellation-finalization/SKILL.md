---
name: scala-effect-cancellation-finalization
description: Use when a Scala change alters how cancellation, failure and success are distinguished or how cleanup completes - Cats Effect race/memoize/Fiber.cancel outcomes and bracket/finalizer error provenance, ZIO cancel-token bridges and their evaluation executor, Play ApplicationLifecycle partial startup, stop() completion and CoordinatedShutdown draining. Covers outcome and finalization semantics of effect and lifecycle code, not stream scopes, HTTP protocol semantics or binary compatibility.
license: MIT
---

# Cancellation, failure and finalization semantics

Four historically grounded cases (Cats Effect 1/2/3, ZIO 2 RC-era, Play 2.x/3.x lifecycle) share one question: **when a
computation ends by success, failure or cancellation, who observes which outcome, which cleanup still runs, who owns it,
on which thread does it execute, and when does "done" really mean done?** This file is the cross-case model and
procedure. The concrete, version-pinned material — review quotes, commit links, test oracles, sbt selectors — lives in
one reference per case.

## When to Use

- A refactor shares one implementation between combinators whose cancellation policies differ (`race` vs
  `raceOutcome`), changes memoization state, or wraps `Fiber.cancel` / startup gating.
- A change touches error combination during cleanup: bracket release failure, finalizer sequences, cancellation
  utilities, parallel or race error reporting, `addSuppressed`, runtime reporters.
- A bridge converts a foreign/unsafe cancel token into an effect, or a strict vs by-name constructor moves around
  `blocking`, or shutdown hangs on a small compute pool.
- Lifecycle code changes: `ApplicationLifecycle.stop()`, hook ordering, partial-startup cleanup, dev-mode startup hooks
  ported between Scala and Java, CoordinatedShutdown phases, unbind vs terminate/drain.
- Analogous code in another Scala library (Monix, fs2 internals, Ox, Pekko, custom lifecycles) where the same
  invariants apply; use the transferable checks below and mark library-specific claims as unverified.

## When Not to Use

- Stream/resource scope propagation, per-element leases, sink emission cardinality: use
  `scala-stream-resource-scoping`.
- HTTP protocol framing, request-local error disclosure, middleware boundaries, channel hand-off: use
  `scala-http-server-semantics`.
- Binary/source compatibility or typeclass-law surfaces: use `scala-library-compatibility-laws`; general API contracts:
  `scala-library-contracts`.
- Runtime diagnostics and hot-path cost (including ZIO diagnostic-reader progress): use
  `scala-runtime-diagnostics-hot-paths`.
- General resource-management tutorials, logging policy, or migrating a codebase to a different effect system or
  build tool. Do not port CE3 `Outcome`/`Poll` into CE2, or Play's Future lifecycle into an effect runtime.
- Unsure which Scala skill applies: start at `scala-oss-library-review`.

## Prerequisites

1. Pin the target: checkout SHA, library line (CE1/CE2/CE3, ZIO 1/2 and RC vs release, Play 2.6–3.x), Scala compiler,
   JDK, platform (JVM/JS/Native), backend (Akka/Pekko HTTP, Netty), and mode (dev/prod/embedded).
2. Read the concrete implementation **and** the abstract contract separately (e.g. IO override vs `Bracket` /
   `GenSpawn` default; `succeedBlocking` body vs its name; Java port vs the Scala it replaced).
3. Read the existing tests that observe the behavior, including assertions that look unrelated (a logger counter, a
   suppressed-array check, a wrapped-cause check).
4. Load the case reference(s) from the routing table before applying any historical expectation.

## Shared model: invariants that recur across cases

Each invariant names the case(s) that ground it. "Grounded" means observed in pinned source/review; anything else is
labelled inference.

**I1. Three outcomes, not two.** Success, failure and cancellation are distinct and per-operator policies over them
differ. In the reviewed CE3 contract, `raceOutcome` cancels the loser even when the winner canceled, while `race` waits
for the other result; `racePair` hands over a live fiber (outcome case). A canceled memoize evaluation must not be
cached as a value or error, and must not invent a `Throwable` for arbitrary `E` (outcome case). Merging two code paths
is valid only after their outcome tables agree for both operand orders.

**I2. Primary result and secondary cleanup failures travel on separate channels.** At pinned CE1/CE2 IO, a use failure
plus release failure returns the original use throwable (same identity, suppressed array untouched) and reports the
release failure to the runtime reporter (cleanup-provenance case). Play's lifecycle recovers a failed hook and still runs
the remaining hooks (Play case). A secondary failure must neither replace the primary result nor vanish, and must not
mutate a possibly shared exception.

**I3. Completion means cleanup finished, for every observer.** Interrupting the bridged ZIO effect must invoke the
underlying token and wait for finalization, not just end the outer observer (ZIO case). Every `stop()` caller must get a
Future that completes after the last hook — a losing caller must not get immediate success (Play case). A canceled
memoize evaluation must release waiters; a parent canceled while joining a race loser must cancel that loser on both
symmetric branches (outcome case). Once-only *execution* (CAS, release-once guard, invocation counter) is not completed
*cleanup*; CE2 additionally waits for an already-running release via a Promise (cleanup-provenance case).

**I4. Every live child or acquired resource has a reachable owner at every failure point.** Play keeps lifecycle cleanup
reachable when `ApplicationLoader.load` throws before an Application exists (Play case, PR 8406). The loser fiber of a
race has an owner after the combinator returns (outcome case). Partial acquisition after the last observed event is an
open question, not a proven leak or proven safety (Play case).

**I5. The moment of evaluation, and its executor, is part of the contract.** ZIO's blocking canceler was evaluated by a
strict constructor before the `blocking` shift and starved cleanup on a small compute pool; the fix suspends only the
cancel invocation (`blocking(ZIO.succeed(a))`), not the whole workload (ZIO case). Play's Java port turned lazy vals into
eager construction and ran user code / watcher before `beforeStarted` (Play case). Memoize construction must stay lazy
(outcome case). **Counter-rule:** laziness is not automatically safer — an immutable snapshot taken inside its owning
callback can move onto a foreign fiber if deferred (ZIO PR 8819 review). Establish the owner first; choose strictness
second.

**I6. Cancellation and shutdown must themselves make bounded progress.** A `Fiber.cancel` that waits on a startup gate
is a cancelable cancel, which CE3 review rejected; masking the wait can make it hang instead (outcome case, unmerged PR
3123). A synchronous cancel token that waits for cleanup must not occupy the executor cleanup needs (ZIO case). A shutdown
task must not await the CoordinatedShutdown run awaiting it; outer waits stay finite rather than `Duration.Inf`, with
fallback taken from the owning API (`cs.timeout(PhaseServiceUnbind)`) (Play case). An uncancelable child can make any
cancellation wait forever; oracles must assume a cancelable loser (outcome case).

**I7. Ordering is a completion edge, not textual order.** Hooks run LIFO, sequentially, each after the previous one's
Future (Play case). Same-phase CoordinatedShutdown tasks may run concurrently, so a dependency needs Future composition
or a later phase (Play case). Error-reporting fixes must not reorder registration/removal or skip later finalizers
(cleanup-provenance case).

**I8. Concrete implementation vs polymorphic contract.** A CE IO regression is not a `Bracket` law for every effect
(PR 394); CE2 `Fiber.join: F[A]` is not CE3 `Outcome` (outcome case); March-2022 ZIO bridge APIs are not current ZIO
(ZIO case); Play's January 2020 server still places logger and user hook in one phase, so reviewer requests are not
proven repository invariants (Play case). Distinguish observed code, reviewer proposal, merged decision and your
inference in every finding.

## Routing table

| Change touches | Load |
| --- | --- |
| CE `IOBracket` / `ReleaseRecover`, `composeErrors`, `CancelUtils`, parallel/race error reporting, `addSuppressed`, stderr / runtime reporter, `Bracket` release that throws | [references/cats-effect-cleanup-error-provenance.md](references/cats-effect-cleanup-error-provenance.md) |
| CE3 `GenSpawn` `race` / `raceOutcome` / `racePair`, `GenConcurrent.memoize`, `Fiber.cancel` wrappers, startup gates / forceStart, `Outcome`/`Poll`, CE2 vs CE3 port | [references/cats-effect-outcome-sensitive-concurrency.md](references/cats-effect-outcome-sensitive-concurrency.md) |
| ZIO `Runtime.run`, `unsafeRunAsyncCancelable`, `asyncInterrupt`, `succeedBlocking` / `blocking` / `succeedNow` vs `succeed`, ZIOApp interruption, logger-on-failure, compute-pool shutdown hang, eager vs lazy callback snapshot | [references/zio-canceler-evaluation-owner.md](references/zio-canceler-evaluation-owner.md) |
| Play `ApplicationLifecycle` / `DefaultApplicationLifecycle`, `ApplicationLoader.load` failure, `DevServerRunner` / `RunHook.beforeStarted` / `assetsClassLoader` / `DevServerReloader`, `AkkaHttpServer` stop, `CoordinatedShutdown` phases, binding unbind vs terminate | [references/play-partial-startup-shutdown-completion.md](references/play-partial-startup-shutdown-completion.md) |
| Analogous code elsewhere (other effect runtimes, custom lifecycles, Pekko shutdown) | This file's workflow; then the closest reference for its oracles, marked as transferred |

Pinned evidence (byte copies of the originals) is in `references/evidence/`, one JSON per case, linked from each
reference.

## Workflow

1. **Pin and classify.** Record versions/platform/mode (Prerequisites). Classify the change: outcome policy (I1),
   cleanup-error channel (I2), completion meaning (I3), ownership on failure (I4), evaluation timing/executor (I5),
   progress of cancellation itself (I6), ordering (I7). Load the routed reference(s).
2. **Write the outcome × observer table.** Rows: success, failure, self-cancellation, parent/external cancellation,
   failure during cleanup, simultaneous failures; both operand orders for binary combinators. Columns: value returned
   to the caller, reporter/log output, finalizers run and in which order, live children left, completion time of every
   observer (each `stop()` caller, each memoize waiter, the interrupter). Fill it for before and after the change.
3. **Trace the evaluation path.** For every cleanup/cancel action: where it is constructed, where it is invoked, which
   fiber/thread/executor owns invocation, what it waits on. Expand wrappers until strictness is visible (by-name into
   strict constructor; lazy val into eager Java field). Mark actions evaluated during construction.
4. **Trace ownership at each failure point.** For each acquisition/fork, name the owner that cancels/closes it if the
   next step fails, including before the "success object" (Application, joined result) exists.
5. **Trace all siblings of a changed helper.** Search definitions and usages (JVM and JS sources, race and parallel
   paths, neighbouring bridge wrappers, both symmetric branches) before changing or deleting a shared helper.
6. **Check progress and bounds.** Look for waits inside cancel/shutdown paths: gates, `OneShot.get`, self-awaiting
   shutdown tasks, unbounded outer waits, phase budgets consumed by sequential per-binding waits.
7. **Choose the minimal correction.** Fix the owner of the semantics (e.g. `Runtime.run`, not only ZIOApp; separate
   canceled-winner policy, not just extra `onCancel`). Keep existing independent observations (logger test, wrapped
   cause test, suppressed-array check) instead of weakening them.
8. **Design a discriminating regression** with explicit barriers/startup signals or the repository's virtual scheduler,
   not sleeps; finite external deadlines; thread-safe traces. Name the mutation each test must kill.

## Review and Refactoring Checks

Transferable (apply to any Scala effect or lifecycle code):

- [ ] Cancellation stays distinguishable from error at every return type that exposes it (I1).
- [ ] Shared helpers are shared only where per-operator outcome policies agree, for both operand orders (I1).
- [ ] Secondary cleanup errors neither replace the primary result nor disappear; no `addSuppressed` on a possibly shared
      throwable; preexisting suppressed entries unchanged (I2).
- [ ] Every observer's completion follows the last cleanup effect; no early `successful` for losing callers (I3).
- [ ] Once-only guards are not mistaken for completed cleanup; already-running release is awaited where the target does
      so (I3).
- [ ] Parent cancellation during a join/wait cancels the owned child on every branch (I3, I4).
- [ ] Cleanup is reachable when construction fails midway (I4).
- [ ] No cleanup/cancel action evaluated at construction time; blocking cancel waits do not run on the executor that
      cleanup needs (I5).
- [ ] Laziness is not demanded blindly: owner-confined eager snapshots are legitimate (I5 counter-rule).
- [ ] Cancel itself is not cancelable/gated indefinitely; shutdown has no self-wait; outer waits are finite (I6).
- [ ] Dependencies between cleanup tasks are real completion edges, not registration order or same-phase placement (I7).
- [ ] Later finalizers still run after an earlier one fails; LIFO preserved where promised (I2, I7).

Library/version-specific (verify against the pinned target before applying):

- CE1/CE2 IO: release failure goes to the reporter (`System.err` in those snapshots); CE2 release Promise wait. CE3
  reporter behavior not established.
- CE3 (2021 pre-release memoize; unmerged PR 3232 race / PR 3123 forceStart): `raceOutcome` vs `race` canceled-winner
  policy; memoize cancel → reset state and release latch; retry test expects two starts, one completion.
- ZIO `series/2.x` March 2022: `succeedBlocking = blocking(ZIO.succeed(a))`; token invocation waits on `OneShot.get`.
- Play: `DefaultApplicationLifecycle` CAS + deque + shared Promise (2018); `cs.timeout(PhaseServiceUnbind)` fallback and
  binding terminate (2020, Akka HTTP); `beforeStarted` before `assetsClassLoader`/reloader in Java run-support (2024).

## Consolidated false positives

- Immutable domain-error aggregation with a documented policy, or a new adapter-owned exception that collects
  suppressed errors, is not reusable-Throwable mutation (cleanup-provenance).
- A custom `Bracket` returning an aggregate is not wrong because CE1 IO reports to stderr; a throwing release function
  needs its own concrete analysis (cleanup-provenance, PR 394).
- A `racePair` caller may deliberately keep the loser; a later memoize may legitimately use an internal fiber; the 2021
  caller-fiber design is not a universal ban (outcome).
- An uncancelable child can make cancellation wait forever; that is not a race-combinator bug (outcome).
- A CE2 subscriber-counted memoizer with `Fiber.join: F[A]` is not missing CE3 `Outcome` (outcome).
- A cancel token that only schedules nonblocking cancellation, an already-computed immutable value, or an eager snapshot
  inside its legitimate owner is not an eager-evaluation defect; `ensuring` after the guarded effect begins is fine; a
  larger compute pool hiding a hang is not proof of equivalence (ZIO).
- Internal AtomicBoolean/Promise mutation in Play's lifecycle is the observed design; independent same-phase tasks may
  run concurrently; a genuinely completed hook may return an already-successful Future; moving an already-computed port
  number into a local changes no timing (Play).
- An untraced helper is an investigation gap, not a confirmed deadlock or leak (all cases).

## Version fences

| Case | Pinned evidence | Do not assume for |
| --- | --- | --- |
| Cleanup provenance | CE1 `c6d7dd5e` (Scala 2.11.12/2.12.7/2.13.0-M5, default 2.12.6; Cats 1.5.0; JVM+JS); CE2 `1b51cb14` | CE3 reporter behavior; other effects' `Bracket` |
| Outcome concurrency | CE3 pre-release `000758b0` (memoize, merged); `f6917ccc` (race, unmerged); PR 3123 (unmerged); CE2 `1b51cb14` (2.6; Scala 2.12.15/2.13.8/3.0.2; Scala.js 1.7.1) | Every CE3 release; CE2 APIs |
| ZIO canceler | `60d47847` `series/2.x` March 2022, RC-era (sbt 1.6.2; Scala 2.11.12/2.12.15/2.13.8/3.1.1; JDK 17 + 8/11) | Released ZIO 2 `Unsafe` APIs; Native (test = compile) |
| Play lifecycle | 2018 `6059f791`; 2020 `5b4eaf91` (Akka HTTP); 2024 `15cf5d6b` (Java run-support); build eras 2020/2022/2024 (Akka → Pekko, IntegrationTest → Test) | Same-year PRs' dependency versions; today's Akka/Pekko |

## Validation

- **No upstream build or test was executed during research or authoring of any case.** Every command in the references
  is a future instruction for a separately authorized, isolated checkout; loading sbt executes build code.
- **Discover targets first:** read `build.sbt`, `project/build.properties`, `project/plugins.sbt` (and
  `project/BuildHelper.scala` / `BuildSettings.scala` where present), CI selectors, and test package names; then
  `sbt projects` (Play also: `sbt 'show Play / Test / definedTests'`). Test projects are often separate from production
  modules (`lawsJVM`, `testsJVM`, `coreTestsJVM`, `Play-Run-Support`, `Sbt-Plugin`).
- **Require nonzero execution** of the selected suite and the specific cases; a green command with zero tests proves
  nothing. Structural skill/schema checks prove no runtime property.
- **Run each platform independently** (JVM, JS); Native in the ZIO snapshot only compiles.
- **Global sinks and timing:** capture-based tests (e.g. `System.err`) need serialized execution and restoration on
  failure; constrained-executor tests need an external deadline; scripted Play tests need matching locally published
  artifacts without silently publishing into the user's cache.
- Concrete selectors and oracles: see each reference's Validation section.

## Examples

### Good

A PR unifies CE3 race internals. The reviewer writes the outcome table for `race` and `raceOutcome` in both operand
orders, finds the canceled-winner rows differ, keeps those paths separate, and adds parent-cancel-during-join tests for
both branches (I1, I3; outcome reference). The same reviewer, checking a ZIO bridge in the same codebase, confirms the
cancel token is invoked inside `blocking(ZIO.succeed(...))` and that interrupt completion waits for the finalizer flag
(I3, I5; ZIO reference).

### Broken and Correction

A lifecycle refactor (a) returns `Future.successful(Done)` to every `stop()` caller after the first and (b) in cleanup
calls `primary.addSuppressed(hookError)` before rethrowing. Tests check only invocation count and the returned error.
Both are I3/I2 violations hidden by weak oracles. This composite example is illustrative, not a single historical PR.
Correction: share the pending completion Promise across callers; recover the hook failure without mutating the primary
throwable (keep it observable through whatever secondary channel the target already uses) and keep running remaining
hooks LIFO; add a barrier test
holding the last hook while two callers observe pending Futures, and a repeated-evaluation test asserting unchanged
suppressed arrays (Play and cleanup-provenance references).

### Negative

A ZIO callback eagerly reads mutable child state inside its owning fiber and returns an immutable snapshot. A reviewer
cites I5 to demand laziness. Reject the finding: the counter-rule applies — the eager read is owner-confined, and
deferring it would execute on the foreign caller (ZIO reference, PR 8819). Likewise, do not flag a CE2 memoizer for
lacking `Outcome` (I8).

## Output Contract

1. Target: SHA, library line, Scala/JDK, platform, backend/mode.
2. The outcome × observer table (before/after) and the evaluation/ownership trace for touched actions.
3. Findings, each with `file:line`, severity, violated invariant (I1–I8), evidence (pinned citation or evidence ID from
   `references/evidence/`), minimal correction, and a discriminating test naming the mutation it kills.
4. Separate: observed source, reviewer proposal, merged decision, your inference; confirmed defects vs missing
   assertions vs suspected schedules vs investigation gaps.
5. Commands actually executed with results, vs proposed tests, vs blocked by prerequisites. An explicit no-finding when
   the trace is preserved.

## Limitations

- Each case rests on a small set of pinned snapshots and review threads; together they support a decision procedure,
  not a proof over all schedules or universal leak freedom.
- Several grounding proposals are unmerged (CE PR 3232 race helper, PR 3123 forceStart); ZIO PR 8819's design was
  superseded. Their review arguments are used, not their code.
- Newer lines (CE3 releases, released ZIO 2 `Unsafe` APIs, Pekko-era Play) must be re-read before any historical
  expectation is applied.
- Reviewer logins identify participants only; formal maintainer roles were not verified.
- Evaluated by model-based review of source and history; no upstream build, signal delivery or constrained-executor
  experiment was executed, and no effectiveness measurement against a baseline agent exists.

## Sources

- [Cats Effect cleanup-error provenance](references/cats-effect-cleanup-error-provenance.md) — evidence
  [JSON](references/evidence/scala-cats-effect-cleanup-error-provenance.json); PR 458, PR 394.
- [Cats Effect outcome-sensitive concurrency](references/cats-effect-outcome-sensitive-concurrency.md) — evidence
  [JSON](references/evidence/scala-cats-effect-outcome-sensitive-concurrency.json); PR 1552, PR 3232, PR 3123.
- [ZIO canceler evaluation owner](references/zio-canceler-evaluation-owner.md) — evidence
  [JSON](references/evidence/scala-zio-canceler-evaluation-owner.json); PR 6401, PR 8819.
- [Play partial startup and shutdown completion](references/play-partial-startup-shutdown-completion.md) — evidence
  [JSON](references/evidence/scala-play-partial-startup-shutdown-completion.json); PR 8406, PR 9970, PR 12210.
