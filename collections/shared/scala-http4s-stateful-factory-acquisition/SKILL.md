---
name: scala-http4s-stateful-factory-acquisition
description: Use when refactoring http4s stateful middleware factories or their nonce and token-bucket tests. Preserve acquisition-local state sharing, compatible effectful entrypoints, and domain-state timing assertions.
license: MIT
---

# Keep middleware state at the acquisition boundary

## When to Use

Use when suspending middleware/client construction, moving nonce or throttle state, adding an effectful factory alongside a legacy API, or reviewing tests intended to prove persistent state and timed transitions. The decisive distinction is construction of an effect, execution of a factory acquisition, and execution of individual requests.

## When Not to Use

Do not trigger for stateless handlers, pure immutable configuration copies, general Cats Effect cancellation internals, or arbitrary compatibility changes. This is not a Digest authentication security certification or recommendation for password storage. Do not migrate an existing Cats Effect library to direct style, Ox or ZIO to apply the procedure.

## Prerequisites

Read the actual factory, state allocator, request closures, synchronization scope, time source and relevant test fixtures. Identify Scala, http4s branch, effect-library and FS2 versions from the build, not the PR's calendar year.

The OkHttp #1851 example predates CE1 (Scala 2.12.6 default, CE 0.10.1, FS2 0.10.4). DigestAuth #6138 is CE2 maintenance work (Scala 2.12.15/2.13.8/3.0.2, CE 2.5.4, FS2 2.5.10): it uses Blocker, Timer and ContextShift. Throttle #6469 is CE3 (Scala 2.12.16/2.13.8/3.1.2, CE 3.3.12, FS2 3.2.8) and uses Temporal/TestControl. These are separate versioned examples, not one migration recipe.

## Workflow

1. Classify each allocation: pure configuration, acquisition-local state, request-local state, or explicitly shared application service. Check Java builders too: in #1851 the author reported that builder construction already created shared executor/pool internals, reversing the reviewer's initial purity assumption.
2. Write the lifecycle oracle before moving code: constructing a deferred factory performs no allocation; executing it creates one service state; requests through that acquired service share it; a separate acquisition has independent state unless sharing is deliberate. Do not conflate reusing an `F` description with memoizing its result.
3. Suspend allocation at that acquisition boundary, then capture the allocated value in the reusable request function. In #6077, moving `new NonceKeeper` into the Kleisli request callback fixed eagerness but recreated the keeper per request. #6138 instead allocates NonceKeeperF in F and maps it into the challenge Kleisli. Use Resource only where actual release ownership requires it; use the target version's constructors.
4. Preserve maintenance-release callers. For a new `F[AuthMiddleware]` factory, inspect the old public signature, defaults and concrete IO overload resolution. The historical fix used a distinct `applyF` while retaining deprecated entrypoints; changing only typeclass constraints did not make default-argument overloads source-compatible. Check actual implementation constraints before publishing a speculative API.
5. Test shared-state behavior with one acquisition: challenge then authenticated follow-up, duplicate counter use, and concurrent replay. Test a second acquisition separately. A concurrent first-counter test does not establish arbitrary counter progression, expiry, cancellation release or randomness isolation.
6. For timed state, use monotonic elapsed time and the target runtime's deterministic clock facility. A nonblocking token operation needs unavailable/available state assertions around the refill threshold, not a timestamp proving sleep advanced. Keep generator durations positive and representable at the pinned runtime's resolution; avoid rejection sampling that can exhaust on narrow bounds.
7. Audit the assertion itself. A returned Boolean mapped to Unit does not prove cancellation. If the intended property is finalization, arrange an observable finalizer signal, await it within a bounded test, and assert it. Do not treat `TestControl.executeEmbed` or a test's name as an oracle.

## Review and Refactoring Checks

Preserve the invariant of one acquired state across the requests that participate in the protocol, and independence across separately acquired services. Preserve the chosen compatibility boundary, mutable-state serialization and existing resource owners; adding `F.delay` everywhere is not the invariant.

False positives: sharing immutable settings is fine. Request-local scratch state is not automatically a lifetime defect. Virtual time does not control foreign sockets or blocking executors. A `val` holding a clock effect can be rerun; it is not necessarily a cached timestamp.

The historical nonce implementation remains a limited exemplar. NonceF.gen accepts but does not use its Blocker; threading an argument is not execution isolation. NonceKeeperF's expiry comparison and `lastNc + 1` update require fresh/stale and nonconsecutive-counter regressions. Do not copy them as verified repairs or claim a current vulnerability from historical inspection.

## Validation

Read the checkout's `build.sbt` and test declarations first. In a separately authorized isolated checkout use `sbt projects` and `sbt 'server / Test / definedTests'`. For #6138 the source-derived selectors are `sbt 'server / testOnly org.http4s.server.middleware.authentication.AuthenticationSuite' 'server / mimaReportBinaryIssues'`. For #6469 use `sbt 'server / testOnly org.http4s.server.middleware.ThrottleSuite org.http4s.server.middleware.TimeoutSuite'`. Check nonzero test discovery. Confirm current selectors and Scala/platform cells; do not assume `serverJVM` exists or invoke a release-bearing CI alias.

Add focused tests for no eager allocation, two acquisitions, multiple requests on one acquisition, competing replays, and state before/after time thresholds. Compile concrete IO and effect-polymorphic call sites with defaults as well as running the promised binary gate. For each new test identify a mutation it rejects: allocation moved inside the callback, permanently unavailable tokens, or removed finalizer. Keep real socket/executor checks separate. This research authored procedures and fixtures but did not execute Scala builds or these tests.

## Examples

### Good

At the #6138 head, `NonceKeeperF(...).map` creates the reusable challenge function; the concurrent replay test acquires DigestAuth once, obtains a challenge, then sends competing authenticated requests and asserts exactly one Ok response. This is evidence for acquisition-local sharing and that narrow replay oracle, not for every authentication property.

### Broken and Correction

A refactor allocates a nonce keeper inside `Kleisli { request => ... }` and calls the result pure because allocation is delayed. The next request cannot rely on the challenge's state. Correction: allocate in the factory effect and return a closure over that keeper, preserving the old API separately where required. When verifying timed state, replace a sleep-only timestamp assertion with unavailable-before/available-after observations on the same bucket; a permanently unavailable implementation must fail.

### Negative

Two services reuse an immutable timeout configuration but separately acquire their own mutable state and owned pools. Do not require effect-wrapped configuration copying or reject intentional application-scoped sharing of a dedicated blocking service. Verify the resource really is pure configuration before applying this exception; the historical OkHttp Builder was not.

## Output Contract

Return `file:line`, severity, allocation classification, construction/acquisition/request timeline, violated invariant, evidence ID, bounded repair and discriminating test. State Scala/effect/branch versions, source- versus binary-compatibility obligations, exact selectors, observed execution results and untested state boundaries. Report historical implementation caveats independently of newly introduced regressions.

## Limitations

Derived from closed/superseded #1851/#6077 and adopted #6138/#6469, not a general implementation of Resource or cancellation. Reviewer formal maintainer rank remains unverified. The historical TimeoutSuite discarded its cancellation flag, so a virtual-time conversion alone is not proof of loser cancellation. No security, timing or performance effectiveness has been experimentally established for this skill.

## Sources

See [evidence and claims](references/evidence.json): `c-factory-state-lifetime`, `c-factory-entrypoint-migration`, `c-temporal-test-oracle`, and `c-middleware-oracle-boundaries`.

- [Per-request allocation correction](https://github.com/http4s/http4s/pull/6077#discussion_r816443611) and [source compatibility](https://github.com/http4s/http4s/pull/6077#issuecomment-1069447411).
- [Factory source](https://github.com/http4s/http4s/blob/11ef78bee0d730a24c42a22f5d32f05db97839c0/server/src/main/scala/org/http4s/server/middleware/authentication/DigestAuth.scala#L164-L179).
- [Test oracle correction](https://github.com/http4s/http4s/pull/6469#discussion_r899155432) and [actual availability assertions](https://github.com/http4s/http4s/blob/d04cf43f349a86564ff4475d5ab13e58d0d55203/server/shared/src/test/scala/org/http4s/server/middleware/ThrottleSuite.scala#L63-L75).
