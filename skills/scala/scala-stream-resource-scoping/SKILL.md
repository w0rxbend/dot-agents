---
name: scala-stream-resource-scoping
description: Use when a Scala stream or effectful factory change moves where a resource, state or execution lane is acquired, owned, used or released - FS2 scope propagation across channels/prefetch/parEvalMap, FS2 foreign callback (Reactive Streams, Dispatcher, accept-loop) lanes and ownership, FS2 sink emission cardinality under drain/append/flatMap, and http4s stateful middleware factories (nonce, throttle) whose state must live at the acquisition boundary. Covers lifetime and ownership topology, not cancellation-outcome/finalizer semantics, HTTP protocol semantics or binary-compatibility law.
license: MIT
---

# Stream and factory resource scoping

Four historical FS2 and http4s cases (2018-2024) share one question: **between which two events does this thing live,
who owns it, and what observable signal proves that?**

## When to Use

- Combinator detaches production from consumption (channel, buffer, prefetch, `parEvalMap`) yet claims resource-backed
  elements stay alive; or scope wrapper changes interruption inheritance.
- Foreign callbacks (Reactive Streams `request`/`cancel`, Dispatcher, socket accept, JS duplex lanes) bridged into
  FS2/Cats Effect; Dispatcher/server-socket lifetime migrated.
- Sink result type or emission changes (`.drain`, `Unit` -> `Nothing`, `evalMap` <-> `foreach`); post-write
  continuation rewritten between `flatMap`, `>>` and `++`.
- Stateful middleware/client factory suspended into `F`/`Resource`; its state moved; effectful entrypoint added beside
  legacy one; tests written to prove shared state or timed transitions.
- Same shapes elsewhere (ZIO streams, Pekko/Akka Streams bridges, custom pools): apply transferable checks; mark
  library-specific ones not carried over.

## When Not to Use

- Pure `map`/value transformations: unchanged cardinality, no acquisition, handoff or interruption change.
- Cancellation outcomes, finalizer error provenance, canceler evaluation: `scala-effect-cancellation-finalization`.
- HTTP framing, routing, middleware execution order, error disclosure: `scala-http-server-semantics`.
- MiMa/binary/source compatibility as policy question, or law-backed instances: `scala-library-compatibility-laws`.
- General public-API contracts: `scala-library-contracts`; type-level encoding: `scala-type-system`; pure FP style:
  `scala-functional-patterns`. Whole-library reviews start at router `scala-oss-library-review`.
- Never a reason to migrate existing Cats Effect/FS2 code to ZIO, Ox or direct style (`direct-style-scala` covers
  code already in that style). Not a Digest auth security certification.

## Prerequisites

1. Versions from actual build (`build.sbt`, `project/build.properties`, plugin pins), not PR or calendar year; see
   Version Fences.
2. Target branch's real source for each lifetime primitive a change names: FS2 `Stream`, `Pull`, `internal/Scope`,
   Dispatcher constructors, `NotNothing`; http4s factory, state allocator, time source, tests.
3. Platform: JVM, Native, JS differ (FS2 socket accept is JVM/Native; JS duplex lanes separate).
4. Repository's effect model. Preserve it.

## Shared Model

CB = foreign callback lanes, SC = per-element scope propagation, CA = sink emission cardinality, FA = stateful factory
acquisition.

**I1. Three moments, not one.** Describing effect, executing acquisition, each use: distinct events. Lifetimes attach
to acquisition, not description or use.
- FA: `new NonceKeeper` inside request Kleisli fixed eagerness but made state per request (#6077); #6138 allocates
  in `F`, maps into reusable Kleisli. Reusing an `F` description is not memoizing its result.
- CB: #3107's `subscribeStream` is effect whose lifetime encloses `StreamSubscription.apply(...).use(_.run)`;
  per-subscription control dispatcher lives inside that run.

**I2. Every live thing has exactly one owner whose release is reachable.** Dispatcher, task, socket, keeper, pool.
- CB: never discard `Resource` release and rely on GC (#3000 GC reply tentative; #3107 TCK fixture's `allocated._1`
  test-only). Outer `Resource` owns listening socket, not restartable inner accept stream (#3063).
- FA: Java builders may already own executors/pools (#1851); classify before calling anything "pure configuration".
- SC: moved finalizer must not create cycle (foreground shutdown waits on producer waits on foreground).

**I3. Lifetime transfer must cover acquisitions that do not exist yet.** Snapshot of current resources is not
subscription to future ones.
- SC: #3512's `Scope.lease` enumerates currently reachable resources (can miss ones already finalizing); later
  bracket-per-element resources close early. Author withdrew after six-element counterexample.
- CB analogue: synchronous handoff bounds pending elements only if producers respect backpressure; repeatedly
  dispatched blocked sends still pile up (#3341 discussion).

**I4. Ordering and progress need separate lanes.** Short ordered control work and long-running data work cannot share
one sequential lane if data waits on control.
- CB: stream waits for demand; demand task waits behind stream (#3000/#3107). One sequential start lane for concurrent
  long-lived subscriptions prevents progress. Terminal-state checks go inside ordered effect.

**I5. Inherited context is part of the lifetime contract.** Wrapper that "enables" something is not a neutral reset.
- SC: explicit interruptibility in #2843 passed local assertion but did not restore parent's inherited mode.
- CB: cancellation stops work without inventing completion; terminal state set before subscriber notification.

**I6. Emission count is observable contract, including `Unit` emissions.** Zero outputs, one completion output, one
output per input: three different APIs.
- CA: `flatMap`/`>>` continue once per output; `take(n)` counts emissions; `++` runs once after successful exhaustion,
  is not a finalizer. `Queue.enqueue` per-element units bound consumption (#1913 kept them).
- FA analogue: one acquisition vs one per request is same count question, for state.

**I7. The oracle must observe the property itself.** Compilation, exit status, test names, elapsed timestamps, Boolean
mapped to `Unit`, `TestControl.executeEmbed`: not oracles.
- CA: precise-`Nothing` witness vs widened `Stream[F, Unit]` runtime probe; continuation counters and round-trip bytes.
- SC: per-element Deferred/use-before-release records, not global finalized flag.
- FA: unavailable-before/available-after on same bucket (#6469); historical TimeoutSuite discarded its cancel flag.
- CB: CancellationSpec waits for subscription resources to close.

## Routing

| Change touches | Load |
|---|---|
| FS2 `reactive-streams` (`StreamSubscription`, `StreamUnicastPublisher`, `subscribeStream`), Dispatcher sequential/parallel choice, `request`/`cancel` ordering, `unsafeRunSync` in callbacks | [references/fs2-foreign-callback-lanes.md](references/fs2-foreign-callback-lanes.md) |
| FS2 `io/net` server socket accept stream, `Resource[F, Stream[F, Socket]]`, inner-consumer restart, `async_` migration, JS read/write/error lanes, callback-driven `Channel.send` backpressure | [references/fs2-foreign-callback-lanes.md](references/fs2-foreign-callback-lanes.md) |
| FS2 `Pull.extendScopeTo`, `Scope.lease`, `parEvalMap`, prefetch/channel handoff of bracketed elements, tracing/`IOLocal` scope wrappers, interruption-mode inheritance | [references/fs2-per-element-scope-propagation.md](references/fs2-per-element-scope-propagation.md) |
| FS2 sink/pipe output type (`Unit` vs `Nothing`), `.drain`, `foreach` vs `evalMap`, `NotNothing`, `flatMap`/`>>`/`++` after a write, Queue/Topic enqueue emissions, `take` after a sink | [references/fs2-sink-emission-cardinality.md](references/fs2-sink-emission-cardinality.md) |
| http4s middleware/client factories with mutable state (DigestAuth `NonceKeeper(F)`, Throttle token bucket, OkHttp builder), `apply` vs `applyF`, deprecated entrypoints, `TestControl`/Clock-based middleware tests | [references/http4s-stateful-factory-acquisition.md](references/http4s-stateful-factory-acquisition.md) |
| Analogous code elsewhere | This file's Workflow and transferable checks; then closest case file for probes |

Raw pinned evidence (SHAs, review permalinks, claims with applicability and counterexamples):
[callback lanes](references/evidence/scala-fs2-foreign-callback-lanes.json),
[scope propagation](references/evidence/scala-fs2-per-element-scope-propagation.json),
[emission cardinality](references/evidence/scala-fs2-sink-emission-cardinality.json),
[factory acquisition](references/evidence/scala-http4s-stateful-factory-acquisition.json).

## Workflow

1. **Pin versions and platform** from build. Load routed case file(s). Note which historical anchor (if any) matches
   target version; rest are only analogies.
2. **Draw the lifetime timeline.** Per resource/state/lane: describe -> acquire -> each use -> release, plus owner and
   release-triggering hook. Include acquisitions that happen only after first pull or first request (I1, I3).
3. **Classify each allocation**: pure configuration, acquisition-local state, request/element-local state, explicitly
   shared application service, or foreign-owned. Verify "pure" claims against source (I2).
4. **Build the lane table** for callbacks or workers: submission order, can-wait-on-whom, owner. Find any lane waiting
   on work queued behind itself (I4).
5. **Write the emission/continuation table** when stream result or continuation changes: empty / one / many inputs,
   per-element vs per-chunk, consumers (`flatMap`, `>>`, `++`, `take`) (I6).
6. **Write the oracle before moving code**, one per invariant; name mutation each rejects (allocation moved into
   callback; lease missing later elements; merged lanes; widened empty bind; permanently unavailable tokens;
   removed finalizer) (I7).
7. **Exercise outcomes**: normal exhaustion, downstream early termination, upstream failure, cancellation with pending
   handoff, shutdown races, second independent acquisition, inherited noninterruptible parent (I5).
8. **Decide**: accept, request specific test, or reject with counterexample. Rejecting superficially passing fix needs
   no invented replacement. Do not propose historically rejected APIs (`extendScopeThrough`, `noInterruptScope`) or
   copy historical exemplars as verified repairs.

## Review and Refactoring Checks

Transferable (any Scala effect/stream library):
- [ ] Construction allocates nothing; one acquisition yields one state shared by its uses; separate acquisitions are
      independent unless sharing is deliberate (I1).
- [ ] Every dispatcher/fiber/socket/pool/keeper has owner and reachable release; no "GC will clean it up" (I2).
- [ ] `acquire(i) < use(i) < release(i)` for each element actually used, including later acquisitions; unused
      acquisitions may be released on cancellation; exactly-once release; bounded shutdown; no retain-everything fix (I3).
- [ ] Ordered control work never queues behind data work it unblocks; terminal checks inside ordered effect; no
      blocking `unsafeRunSync` just to order submissions (I4).
- [ ] Inherited interruption/masking context preserved across new wrappers; compare wrapped vs unwrapped (I5).
- [ ] Output counts, continuation counts, bounded-consumption behavior unchanged unless intentionally migrated, with
      stated binary/source/runtime compatibility policy (I6).
- [ ] Backpressure checked at submitting callback, not only buffer capacity; coalescing only where duplicates are
      protocol-redundant (I3/I4).
- [ ] Every test asserts property, not proxy; deterministic barriers preferred; timeouts only bound hangs (I7).

Library/version-specific (do not carry over without re-reading target source):
- [ ] FS2 `Scope.lease` semantics at target SHA; `Pull.extendScopeTo` path (SC).
- [ ] FS2 Dispatcher sequential vs parallel constructors; shutdown exception suppressed only at its boundary (CB).
- [ ] FS2 `NotNothing` (or successor) presence on `flatMap`/`>>` (CA).
- [ ] http4s `applyF`-style distinct factory name vs constraint-only overloads with defaults (FA, CE2 maintenance).
- [ ] CE3 `TestControl`/`Temporal` vs CE2 `Timer`/`Clock`/`ContextShift`/`Blocker` (FA).
- [ ] JVM vs Native vs JS socket/lane implementations (CB).

## Consolidated False Positives

- Short ordered control work on sequential dispatcher is correct; application-owned parallel dispatcher is not
  inherently a leak (but does not prove per-subscription cleanup). (CB)
- Released handle returned on purpose as failed-publisher test fixture is not a production pattern. (CB)
- Single fixed outer resource needs only one lifetime extension; pure transformed value may no longer borrow its
  source. Require actual borrowing/use path. (SC)
- FS2 stream interruption context is not universal Cats Effect masking; choosing not to alter inherited mode is not a
  missing cancellation feature. (SC)
- `evalMap(_ => action)` then `take(n)` uses units as progress signals; terminal writer that never promised per-byte
  emissions need not invent them; #1913 does not authorize changing current Queue/Topic APIs. (CA)
- Sharing immutable configuration is fine; request-local scratch state is not a lifetime defect; intentional
  application-scoped sharing of dedicated blocking service is acceptable; `val` holding a clock effect is not a cached
  timestamp; virtual time does not control foreign sockets or blocking executors. (FA)
- Narrow fix leaving documented unrelated follow-up (e.g. nonce expiry) did not introduce it; report gap separately.
  (FA)
- Pure queue consumer with no foreign callbacks, or pure integer stream with no acquisition or handoff, does not
  trigger this skill.

## Version Fences

| Case | Anchor | Versions | Status |
|---|---|---|---|
| CB | fs2 #3000 | CE 3.4.0-RC1, two sequential dispatchers | discussion + code |
| CB | fs2 #3107 | CE 3.4.4, Jan 2023, Reactive Streams JVM adapter | merged |
| CB | fs2 #3063 | CE `3.5-4b87497` snapshot `async_` semantics; JVM/Native sockets | source-inspected |
| CB | fs2 #2300, #3341 | contextual discussion only | head diffs excluded |
| SC | fs2 #2843 | CE 3.3.6 (2022) | closed unmerged |
| SC | fs2 #3512 | CE 3.5.7, Scala 2.12.20/2.13.15/3.3.4, sbt 1.10.5 (Dec 2024) | closed unmerged |
| CA | fs2 #1754, #1913 | target FS2 3.0; branch on CE 2.2.0-RC3, Scala 2.13.2/2.12.10, Dotty 0.26.0-RC1 | narrowed revision adopted |
| FA | http4s #1851 | Scala 2.12.6, CE 0.10.1, FS2 0.10.4 | closed/superseded |
| FA | http4s #6077 / #6138 | Scala 2.12.15/2.13.8/3.0.2, CE 2.5.4, FS2 2.5.10 (for #6138) | #6077 superseded, #6138 adopted |
| FA | http4s #6469 | Scala 2.12.16/2.13.8/3.1.2, CE 3.3.12, FS2 3.2.8 | adopted |

Method visible in an unmerged diff is not available in a release. `IOLocal` observations are IO-specific.

## Validation

No upstream build or test ran during research. Commands below are source-derived; run only after authorization, in
isolated checkout.

1. Discover real targets first: read `build.sbt`, `project/build.properties`, plugins, platform requirements; run
   `sbt projects` and `sbt 'show <project> / Test / definedTests'`. Do not assume project names (`io`, `server`,
   `coreJVM`, `serverJVM`) survive across branches; do not invoke release-bearing CI aliases.
2. Run case's historical selectors (in each case file) only at matching SHA. Require nonzero test discovery and
   assertions, not exit status.
3. Add regression probes from Workflow step 6: per-element Deferred brackets with delayed `parEvalMap(2)` use;
   cancel/restart of inner accept stream under retained outer resource; shutdown/callback races with multiple
   subscriptions; empty/nonempty emission and continuation counts, precise-`Nothing` compile failure (specific expected
   error) plus widened empty runtime bind; no-eager-allocation, two-acquisition and concurrent replay tests;
   before/after threshold state under virtual time.
4. Run binary gates (`mimaReportBinaryIssues`) when public factory or sink signature changes, and compile concrete `IO`
   plus effect-polymorphic call sites with defaults.
5. Keep platform evidence separate: JVM test is not evidence for Native or Node; virtual time is not evidence for real
   sockets or blocking pools; TCK and repeated race runs are not proofs over all schedules.

## Examples

### Good

`parEvalMap` refactor reviewed with per-element timeline (I3), six-element Deferred-bracket regression with delayed
consumer, and check under noninterruptible parent (I5). Separately, nonce middleware factory allocates keeper in `F`,
maps it into request Kleisli. One acquisition serves challenge and follow-up; second acquisition is independent;
concurrent replay yields exactly one Ok (I1, I7).

### Broken and Correction

Bridge "simplifies": runs subscription stream and its demand callbacks on one sequential dispatcher, and swaps global
dispatcher for allocated publisher with discarded release. Two violations: I4 (deadlock: stream waits for demand queued
behind it) and I2 (unowned release). Correction: per-subscription ordered control lane inside lifetime-enclosing
subscription effect, parallel start lane, real release hook, test proving progress and cleanup. Likewise,
`drainedWrite ++ readBack` rewritten to `drainedWrite.flatMap(_ => readBack)` silently skips the read (I6); restore
`++` and assert continuation counter.

### Negative

Two services share immutable timeout config while each acquires own state and pools; bridge already has verified
per-subscription control lanes; integer stream changes its arithmetic. None needs a finding: do not demand
effect-wrapped config copies, uniform global dispatcher, leases, or interruption matrix.

## Output Contract

Per finding: `file:line`, severity, case (CB/SC/CA/FA or "analogous"), invariant (I1-I7), version/platform, evidence ID or
URL, concrete interleaving or timeline, relevant table (lane/owner, emission/continuation, or
construction/acquisition/request), proposed bounded correction, discriminating test naming mutation it rejects. State
release hook closing each owner, compatibility policy if signatures change, evidence stage per claim: observed code,
reviewer proposal, author report, merged decision, or model inference. Say whether any repair was only proposed,
compiled, or executed, and which outcomes remain unexercised.

## Limitations

- Derived from model-based review of pinned historical source and maintainer discussion. Several anchors are
  closed/unmerged (#2843, #3512, #1851, #6077); they teach review probes, not repairs.
- Invariants I1-I7 are cross-case synthesis (inference); each case file states what its evidence actually shows.
- Historical exemplars carry caveats (unused Blocker, `lastNc + 1`, discarded TimeoutSuite cancel flag, inconsistent
  #1913 printing docs, #3107 TCK fixture); not present-day vulnerability claims.
- #3107 does not prove every Play/Akka integration migrated correctly. Reviewer formal maintainer roles not
  established. No security, timing or performance effectiveness experimentally established.
