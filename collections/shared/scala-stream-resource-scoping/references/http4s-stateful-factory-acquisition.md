# http4s (http4s/http4s): stateful middleware factory acquisition — originally `scala-http4s-stateful-factory-acquisition`

Evidence: [evidence/scala-http4s-stateful-factory-acquisition.json](evidence/scala-http4s-stateful-factory-acquisition.json),
claims `c-factory-state-lifetime`, `c-factory-entrypoint-migration`, `c-temporal-test-oracle`,
`c-middleware-oracle-boundaries`.

Scope: suspending middleware/client construction, moving nonce or throttle state, adding an effectful factory alongside a
legacy API, or reviewing tests intended to prove persistent state and timed transitions. The decisive distinction is
construction of an effect, execution of a factory acquisition, and execution of individual requests.

Not for: stateless handlers, pure immutable configuration copies, general Cats Effect cancellation internals (see
`scala-effect-cancellation-finalization`), or arbitrary compatibility changes (see `scala-library-compatibility-laws`).
Not a Digest authentication security certification or recommendation for password storage. Do not migrate an existing
Cats Effect library to direct style, Ox or ZIO to apply the procedure.

## Prerequisites and version fences

Read the actual factory, state allocator, request closures, synchronization scope, time source and relevant test
fixtures. Identify Scala, http4s branch, effect-library and FS2 versions from the build, not the PR's calendar year.

| PR | Status | Scala | Cats Effect | FS2 | Notes |
|---|---|---|---|---|---|
| OkHttp #1851 | closed/superseded | 2.12.6 default | 0.10.1 (pre-CE1) | 0.10.4 | Java builder allocation |
| DigestAuth #6077 | superseded | — | — | — | per-request allocation correction, source-compat discussion |
| DigestAuth #6138 | adopted | 2.12.15/2.13.8/3.0.2 | 2.5.4 | 2.5.10 | CE2 maintenance; Blocker, Timer, ContextShift |
| Throttle #6469 | adopted | 2.12.16/2.13.8/3.1.2 | 3.3.12 | 3.2.8 | CE3; Temporal/TestControl |

These are separate versioned examples, not one migration recipe. CE2 Clock API differs from CE3.

## Workflow

1. Classify each allocation: pure configuration, acquisition-local state, request-local state, or explicitly shared
   application service. Check Java builders too: in #1851 the author reported that builder construction already created
   shared executor/pool internals, reversing the reviewer's initial purity assumption.
2. Write the lifecycle oracle before moving code: constructing a deferred factory performs no allocation; executing it
   creates one service state; requests through that acquired service share it; a separate acquisition has independent
   state unless sharing is deliberate. Do not conflate reusing an `F` description with memoizing its result.
3. Suspend allocation at that acquisition boundary, then capture the allocated value in the reusable request function.
   In #6077, moving `new NonceKeeper` into the Kleisli request callback fixed eagerness but recreated the keeper per
   request. #6138 instead allocates NonceKeeperF in F and maps it into the challenge Kleisli. Use Resource only where
   actual release ownership requires it; use the target version's constructors.
4. Preserve maintenance-release callers. For a new `F[AuthMiddleware]` factory, inspect the old public signature,
   defaults and concrete IO overload resolution. The historical fix used a distinct `applyF` while retaining deprecated
   entrypoints; changing only typeclass constraints did not make default-argument overloads source-compatible. Check
   actual implementation constraints before publishing a speculative API (#6077 review rejected a speculative API). A
   deliberate incompatible major-version migration may remove old entrypoints.
5. Test shared-state behavior with one acquisition: challenge then authenticated follow-up, duplicate counter use, and
   concurrent replay. Test a second acquisition separately. A concurrent first-counter test does not establish arbitrary
   counter progression, expiry, cancellation release or randomness isolation.
6. For timed state, use monotonic elapsed time (#6138 review) and the target runtime's deterministic clock facility. A
   nonblocking token operation needs unavailable/available state assertions around the refill threshold, not a timestamp
   proving sleep advanced (#6469 review). Keep generator durations positive and representable at the pinned runtime's
   resolution; avoid rejection sampling that can exhaust on narrow bounds.
7. Audit the assertion itself. A returned Boolean mapped to Unit does not prove cancellation. If the intended property is
   finalization, arrange an observable finalizer signal, await it within a bounded test, and assert it. Do not treat
   `TestControl.executeEmbed` or a test's name as an oracle.

## Review checks

One acquired state across the requests that participate in the protocol, and independence across separately acquired
services. Preserve the chosen compatibility boundary, mutable-state serialization and existing resource owners; adding
`F.delay` everywhere is not the invariant.

Historical exemplar caveats (source-only observations at #6138/#6469, not verified present-day vulnerabilities):
- `NonceF.gen` accepts but does not use its Blocker; threading an argument is not execution isolation.
- NonceKeeperF's expiry comparison and `lastNc + 1` update require fresh/stale and nonconsecutive-counter regressions.
  Do not copy them as verified repairs or claim a current vulnerability from historical inspection.
- The historical TimeoutSuite discarded its cancellation flag, so a virtual-time conversion alone is not proof of loser
  cancellation.
- A narrow allocation fix can intentionally leave a documented unrelated expiry follow-up; report that gap separately
  rather than claiming the patch introduced every pre-existing weakness.

## False positives

- Sharing immutable settings is fine; immutable configuration with no owned executor, pool or mutable authentication
  state need not be delayed.
- Request-local scratch state is not automatically a lifetime defect; an intentionally request-local counter is not
  middleware-wide state.
- Virtual time does not control foreign sockets or blocking executors.
- A `val` holding a clock effect can be rerun; it is not necessarily a cached timestamp.
- Two services reusing an immutable timeout configuration but separately acquiring their own mutable state and owned
  pools need no effect-wrapped configuration copying; intentional application-scoped sharing of a dedicated blocking
  service is acceptable. Verify the resource really is pure configuration first; the historical OkHttp Builder was not.

## Validation

Read the checkout's `build.sbt` and test declarations first. In a separately authorized isolated checkout use
`sbt projects` and `sbt 'server / Test / definedTests'`. For #6138 the source-derived selectors are
`sbt 'server / testOnly org.http4s.server.middleware.authentication.AuthenticationSuite' 'server / mimaReportBinaryIssues'`.
For #6469 use `sbt 'server / testOnly org.http4s.server.middleware.ThrottleSuite org.http4s.server.middleware.TimeoutSuite'`.
Check nonzero test discovery. Confirm current selectors and Scala/platform cells; do not assume `serverJVM` exists or
invoke a release-bearing CI alias. (Note: #6469 sources live under `server/shared/`, which suggests a cross-built
project; the `server /` selector there is unverified and must be rediscovered with `sbt projects`.)

Add focused tests for no eager allocation, two acquisitions, multiple requests on one acquisition, competing replays, and
state before/after time thresholds. Compile concrete IO and effect-polymorphic call sites with defaults as well as
running the promised binary gate. For each new test identify a mutation it rejects: allocation moved inside the callback,
permanently unavailable tokens, or removed finalizer. Keep real socket/executor checks separate. This research authored
procedures and fixtures but did not execute Scala builds or these tests.

## Examples

- Good: at the #6138 head, `NonceKeeperF(...).map` creates the reusable challenge function; the concurrent replay test
  acquires DigestAuth once, obtains a challenge, then sends competing authenticated requests and asserts exactly one Ok
  response. This is evidence for acquisition-local sharing and that narrow replay oracle, not for every authentication
  property.
- Broken and correction: a refactor allocates a nonce keeper inside `Kleisli { request => ... }` and calls the result pure
  because allocation is delayed. The next request cannot rely on the challenge's state. Correction: allocate in the
  factory effect and return a closure over that keeper, preserving the old API separately where required. When verifying
  timed state, replace a sleep-only timestamp assertion with unavailable-before/available-after observations on the same
  bucket; a permanently unavailable implementation must fail.

## Case-specific output

Allocation classification; construction/acquisition/request timeline; source- versus binary-compatibility obligations;
exact selectors; untested state boundaries; historical implementation caveats reported independently of newly
introduced regressions.

## Limitations

Derived from closed/superseded #1851/#6077 and adopted #6138/#6469, not a general implementation of Resource or
cancellation. Reviewer formal maintainer rank remains unverified. No security, timing or performance effectiveness has
been experimentally established.

## Sources

- [Per-request allocation correction](https://github.com/http4s/http4s/pull/6077#discussion_r816443611) and
  [source compatibility](https://github.com/http4s/http4s/pull/6077#issuecomment-1069447411).
- [Factory source](https://github.com/http4s/http4s/blob/11ef78bee0d730a24c42a22f5d32f05db97839c0/server/src/main/scala/org/http4s/server/middleware/authentication/DigestAuth.scala#L164-L179).
- [Test oracle correction](https://github.com/http4s/http4s/pull/6469#discussion_r899155432) and
  [actual availability assertions](https://github.com/http4s/http4s/blob/d04cf43f349a86564ff4475d5ab13e58d0d55203/server/shared/src/test/scala/org/http4s/server/middleware/ThrottleSuite.scala#L63-L75).
- #1851 builder discussion, #6138 compat adapter and monotonic review, #6469 before/after and generator reviews, and
  effect-version pins are in the evidence file.
