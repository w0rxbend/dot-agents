# http4s (http4s/http4s): stateful middleware factory acquisition — originally `scala-http4s-stateful-factory-acquisition`

Evidence: [evidence/scala-http4s-stateful-factory-acquisition.json](evidence/scala-http4s-stateful-factory-acquisition.json),
claims `c-factory-state-lifetime`, `c-factory-entrypoint-migration`, `c-temporal-test-oracle`,
`c-middleware-oracle-boundaries`.

Scope: suspending middleware/client construction, moving nonce or throttle state, adding effectful factory beside legacy
API, or reviewing tests meant to prove persistent state and timed transitions. Decisive distinction: constructing an
effect, executing factory acquisition, executing individual requests.

Not for: stateless handlers, pure immutable configuration copies, general Cats Effect cancellation internals (see
`scala-effect-cancellation-finalization`), arbitrary compatibility changes (see `scala-library-compatibility-laws`).
Not a Digest authentication security certification or password-storage recommendation. Do not migrate existing Cats
Effect library to direct style, Ox or ZIO to apply this procedure.

## Prerequisites and version fences

Read actual factory, state allocator, request closures, synchronization scope, time source, relevant test fixtures.
Take Scala, http4s branch, effect-library, FS2 versions from build, not PR's calendar year.

| PR | Status | Scala | Cats Effect | FS2 | Notes |
|---|---|---|---|---|---|
| OkHttp #1851 | closed/superseded | 2.12.6 default | 0.10.1 (pre-CE1) | 0.10.4 | Java builder allocation |
| DigestAuth #6077 | superseded | — | — | — | per-request allocation correction, source-compat discussion |
| DigestAuth #6138 | adopted | 2.12.15/2.13.8/3.0.2 | 2.5.4 | 2.5.10 | CE2 maintenance; Blocker, Timer, ContextShift |
| Throttle #6469 | adopted | 2.12.16/2.13.8/3.1.2 | 3.3.12 | 3.2.8 | CE3; Temporal/TestControl |

Separate versioned examples, not one migration recipe. CE2 Clock API differs from CE3.

## Workflow

1. Classify each allocation: pure configuration, acquisition-local state, request-local state, or explicitly shared
   application service. Check Java builders too: in #1851 author reported builder construction already created shared
   executor/pool internals, reversing reviewer's initial purity assumption.
2. Write lifecycle oracle before moving code: constructing deferred factory allocates nothing; executing it creates one
   service state; requests through that acquired service share it; separate acquisition has independent state unless
   sharing is deliberate. Do not conflate reusing an `F` description with memoizing its result.
3. Suspend allocation at that acquisition boundary, then capture allocated value in reusable request function. In
   #6077, moving `new NonceKeeper` into Kleisli request callback fixed eagerness but recreated keeper per request.
   #6138 instead allocates NonceKeeperF in F, maps it into challenge Kleisli. Use Resource only where actual release
   ownership requires it; use target version's constructors.
4. Preserve maintenance-release callers. For new `F[AuthMiddleware]` factory, inspect old public signature, defaults,
   concrete IO overload resolution. Historical fix used distinct `applyF` and kept deprecated entrypoints; changing
   only typeclass constraints did not make default-argument overloads source-compatible. Check actual implementation
   constraints before publishing speculative API (#6077 review rejected a speculative API). Deliberate incompatible
   major-version migration may remove old entrypoints.
5. Test shared state with one acquisition: challenge then authenticated follow-up, duplicate counter use, concurrent
   replay. Test second acquisition separately. Concurrent first-counter test does not establish arbitrary counter
   progression, expiry, cancellation release or randomness isolation.
6. Timed state: use monotonic elapsed time (#6138 review) and target runtime's deterministic clock facility.
   Nonblocking token operation needs unavailable/available state assertions around refill threshold, not timestamp
   proving sleep advanced (#6469 review). Keep generator durations positive and representable at pinned runtime's
   resolution; avoid rejection sampling that can exhaust on narrow bounds.
7. Audit the assertion itself. Returned Boolean mapped to Unit does not prove cancellation. If intended property is
   finalization, arrange observable finalizer signal, await it within bounded test, assert it. Do not treat
   `TestControl.executeEmbed` or a test's name as an oracle.

## Review checks

One acquired state across requests participating in protocol; independence across separately acquired services.
Preserve chosen compatibility boundary, mutable-state serialization, existing resource owners; adding `F.delay`
everywhere is not the invariant.

Historical exemplar caveats (source-only observations at #6138/#6469, not verified present-day vulnerabilities):
- `NonceF.gen` accepts but does not use its Blocker; threading an argument is not execution isolation.
- NonceKeeperF's expiry comparison and `lastNc + 1` update require fresh/stale and nonconsecutive-counter regressions.
  Do not copy them as verified repairs or claim a current vulnerability from historical inspection.
- Historical TimeoutSuite discarded its cancellation flag, so virtual-time conversion alone does not prove loser
  cancellation.
- Narrow allocation fix can intentionally leave documented unrelated expiry follow-up; report that gap separately; do
  not claim the patch introduced every pre-existing weakness.

## False positives

- Sharing immutable settings is fine; immutable configuration with no owned executor, pool or mutable authentication
  state need not be delayed.
- Request-local scratch state is not automatically a lifetime defect; intentionally request-local counter is not
  middleware-wide state.
- Virtual time does not control foreign sockets or blocking executors.
- `val` holding a clock effect can be rerun; not necessarily a cached timestamp.
- Intentional application-scoped sharing of dedicated blocking service is acceptable. First verify resource is truly
  pure configuration; historical OkHttp Builder was not.

## Validation

Read checkout's `build.sbt` and test declarations first. In separately authorized isolated checkout use
`sbt projects` and `sbt 'server / Test / definedTests'`. For #6138 source-derived selectors are
`sbt 'server / testOnly org.http4s.server.middleware.authentication.AuthenticationSuite' 'server / mimaReportBinaryIssues'`.
For #6469 use `sbt 'server / testOnly org.http4s.server.middleware.ThrottleSuite org.http4s.server.middleware.TimeoutSuite'`.
Check nonzero test discovery. Confirm current selectors and Scala/platform cells; do not assume `serverJVM` exists or
invoke a release-bearing CI alias. (Note: #6469 sources live under `server/shared/`, suggesting cross-built project;
`server /` selector there is unverified, must be rediscovered with `sbt projects`.)

Add focused tests: no eager allocation, two acquisitions, multiple requests on one acquisition, competing replays,
state before/after time thresholds. Compile concrete IO and effect-polymorphic call sites with defaults, and run
promised binary gate. For each new test name a mutation it rejects: allocation moved inside callback, permanently
unavailable tokens, or removed finalizer. Keep real socket/executor checks separate. This research authored procedures
and fixtures but did not execute Scala builds or these tests.

## Examples

- Good: at #6138 head, `NonceKeeperF(...).map` creates reusable challenge function. Concurrent replay test acquires
  DigestAuth once, obtains a challenge, sends competing authenticated requests, asserts exactly one Ok response.
  Evidence for acquisition-local sharing and that narrow replay oracle, not for every authentication property.
- Broken and correction: refactor allocates nonce keeper inside `Kleisli { request => ... }` and calls result pure
  because allocation is delayed. Next request cannot rely on challenge's state. Correction: allocate in factory effect,
  return closure over that keeper; preserve old API separately where required. For timed state, replace sleep-only
  timestamp assertion with unavailable-before/available-after observations on same bucket; permanently unavailable
  implementation must fail.

## Case-specific output

Allocation classification; construction/acquisition/request timeline; source- versus binary-compatibility obligations;
exact selectors; untested state boundaries; historical implementation caveats reported independently of newly
introduced regressions.

## Limitations

Derived from closed/superseded #1851/#6077 and adopted #6138/#6469, not general implementation of Resource or
cancellation. Reviewer formal maintainer rank remains unverified. No security, timing or performance effectiveness
experimentally established.

## Sources

- [Per-request allocation correction](https://github.com/http4s/http4s/pull/6077#discussion_r816443611) and
  [source compatibility](https://github.com/http4s/http4s/pull/6077#issuecomment-1069447411).
- [Factory source](https://github.com/http4s/http4s/blob/11ef78bee0d730a24c42a22f5d32f05db97839c0/server/src/main/scala/org/http4s/server/middleware/authentication/DigestAuth.scala#L164-L179).
- [Test oracle correction](https://github.com/http4s/http4s/pull/6469#discussion_r899155432) and
  [actual availability assertions](https://github.com/http4s/http4s/blob/d04cf43f349a86564ff4475d5ab13e58d0d55203/server/shared/src/test/scala/org/http4s/server/middleware/ThrottleSuite.scala#L63-L75).
- #1851 builder discussion, #6138 compat adapter and monotonic review, #6469 before/after and generator reviews, and
  effect-version pins in evidence file.
