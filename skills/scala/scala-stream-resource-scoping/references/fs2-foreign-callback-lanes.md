# FS2 (typelevel/fs2): foreign callback lanes and server/consumer ownership — originally `scala-fs2-foreign-callback-lanes`

Evidence: [evidence/scala-fs2-foreign-callback-lanes.json](evidence/scala-fs2-foreign-callback-lanes.json), claims
`fs2-claim-callback-ownership` and `fs2-claim-callback-terminal-lifecycle`.

Scope: refactoring FS2 foreign request/cancel callbacks or restartable server streams. Separate ordered control work,
subscription execution, resource ownership. Covers Reactive Streams adapters, Dispatcher migrations, callback-backed
accept loops where cancellation or demand must progress independently of data work. Identify ordering contract and
lifetime owner of each execution path.

Not for: generic parallel-dispatcher prescription or Kafka callback-thread recipe; does not replace Cats Effect
cancellation-outcome guidance (see `scala-effect-cancellation-finalization`). Per-element FS2 lease propagation is
separate: [fs2-per-element-scope-propagation.md](fs2-per-element-scope-propagation.md). Synchronous foreign API needing
callbacks on a specific thread needs own contract; Dispatcher does not preserve caller-thread affinity.

## Prerequisites and version fences

Identify foreign protocol, callback threading/reentrancy guarantees, FS2/Cats Effect versions, platform. Read both
callback entrypoints and resource factories. Preserve chosen effect model.

- #3000 uses CE 3.4.0-RC1 and two sequential dispatchers.
- #3107's January 2023 CE 3.4.4 source (merged) moves control ownership inside each subscription; parallel start
  dispatcher serves concurrent subscriptions. Reactive Streams JVM adapter only; current code must rediscover its
  actual subscribe API.
- #3063 tests an `async_` semantic change against CE `3.5-4b87497` (snapshot), not a released-version promise.
  Preserve target version's cancellation semantics; no textual `async_` replacement. Its socket code is JVM/Native;
  JS read/write/error lanes are separate implementation, not covered by JVM tests for Node.
- #2300 and #3341: supplemental contextual discussion only; current head diffs excluded.

## Workflow

1. Make lane table: submission order, whether work can wait on another callback, resource owner. Requests and
   cancellation from one synchronous caller need ordering. Subscription may wait indefinitely for requests and cannot
   monopolize that same sequential lane. JS duplex read/write/error lanes may each be sequential but must stay
   independent.
2. Put terminal-state checks inside ordered submitted effect. Caller-side `if (!done)` then dispatch is a check/use
   race (can race dispatcher shutdown). Do not add `unsafeRunSync` merely to order synchronous `cancel(); request()`
   submissions: #3107's reviewer explains sequential dispatcher already preserves that order without blocking calling
   thread.
3. Trace terminal outcomes: normal exhaustion signals completion, failure signals error, cancellation stops work
   without inventing completion. Set terminal state before notifying subscriber. Validate late request/cancel after
   per-subscription dispatcher shut down. Only suppress documented shutdown exception at that boundary; never swallow
   arbitrary callback failures.
4. Audit ownership end-to-end. #3107's `subscribeStream` returns effect whose lifetime encloses
   `StreamSubscription.apply(...).use(_.run)`. Application-owned parallel dispatcher may run those effects;
   application shutdown and subscriber cancellation must actually terminate them. Do not allocate publisher resource,
   discard its release and assert GC cleans up. If host framework exposes no usable lifetime hook, report unresolved
   integration boundary; do not recommend leak-prone migration.
5. For `Resource` returning accept stream, separate listening socket from inner consumer. #3063 puts acceptance in
   outer-resource-owned background task with synchronous handoff and explicit cleanup of unconsumed sockets. Test
   cancel/restart of inner stream with outer resource retained, then final outer release. Closing server socket to
   cancel only inner accept-stream consumer destroys restartability; no-op cancel token can leave real work unowned.
   Do not claim this automatically solves every accepted-connection transfer scenario; #2300's historical follow-up
   stayed a discussion.
6. Check backpressure at submitting callback, not just channel capacity. Foreign callback repeatedly starting blocked
   sends can pile up tasks even on synchronous channel. #3341 discussion rejects assuming zero buffered elements
   implies bounded memory: synchronous handoff bounds pending elements only if producers respect backpressure. Coalesce
   only when event protocol makes duplicates redundant; do not drop payloads or blindly swap event counters for
   booleans.

## Review checks

Preserve: ordered synchronous cancel/request becomes no-op after cancellation; control work can progress while data work
waits; every live dispatcher/task/socket has owner; terminal callbacks obey actual protocol. Concurrent subscriptions
need independent runs and fitting start lane, not accidental sharing of one stream execution. One sequential start lane
for concurrent long-lived subscriptions prevents progress.

## False positives

- Sequential dispatcher is correct for short ordered control work.
- Application-owned parallel dispatcher is not inherently a leak. Conversely, its existence does not prove
  per-subscription cleanup.
- Resource handle intentionally returned after release suits failed-publisher test, not production lifecycle. #3107's
  TCK fixture discards an allocation release action (`allocated._1`); must not be copied as ownership guidance.
- Bridge already using independent per-subscription control lanes plus application-owned parallel start dispatcher,
  with verified cancellation and shutdown, needs no global sequential dispatcher for stylistic consistency. Pure queue
  consumer with no foreign callbacks or ownership change does not trigger this workflow.

## Validation

After permission to run upstream builds, inspect exact build, plugins, toolchain. Discover with `sbt projects` and
`sbt 'show reactiveStreams / Test / definedTests'`. At #3107 run
`sbt 'reactiveStreams/testOnly fs2.interop.reactivestreams.CancellationSpec'` and
`sbt 'reactiveStreams/testOnly fs2.interop.reactivestreams.StreamUnicastPublisherSpec'`; the latter integrates
Reactive Streams TCK via TestNG. Require test discovery and results, not just compilation.

Revised CancellationSpec waits for subscription resources to close before asserting; does not flag mandatory
`onSubscribe` as illicit data signal. Extend with shutdown/callback races and multiple subscriptions. Sockets: discover
actual I/O platform suite; add loopback cancel/restart and queued-socket-release tests. JVM adapter test is not evidence
that Native or Node accept path works. Repeated race tests and TCK coverage help but are not proofs over all schedules.
No upstream tests ran during this research.

## Examples

- Good: at #3107 boundary, parallel application start dispatcher runs subscription effect. That effect owns sequential
  control dispatcher, releases it on termination. `cancel` and subsequent `request` submit to same control lane;
  request checks canceled state inside its effect. Long-running data stream cannot prevent control processing. Verify
  ownership and ordering in target version; do not copy obsolete constructors.
- Broken and correction: refactor merges stream execution and demand processing onto one sequential dispatcher. Stream
  waits for demand; demand task waits behind stream. Correction: separate execution from ordered control, bind both to
  explicit owners, test progress. If repair also swaps global dispatcher for allocated publisher, keep real release hook
  or use version-supported lifetime-enclosing subscription effect. Never drop finalizer for signature convenience.

## Case-specific output

Lane/owner table; which shutdown exception is intentionally handled; which lifecycle hook closes each owner; whether
suggested migrations are source-verified or still speculative; model reasoning vs compiled/executed adapter and platform
tests.

## Limitations

#3107 follow-up gives concrete per-subscription lifecycle design, not proof every Play/Akka integration migrated
correctly. #3000 GC reply was tentative, not a cleanup guarantee. Socket finalization and platform behavior still need
runtime verification and independent review.

## Sources

- [#3000 independent lanes](https://github.com/typelevel/fs2/pull/3000#discussion_r984074090) and
  [consumer migration objection](https://github.com/typelevel/fs2/pull/3000#discussion_r1067094793).
- [#3107 ordering correction](https://github.com/typelevel/fs2/pull/3107#discussion_r1069996129) and
  [owned subscription implementation](https://github.com/typelevel/fs2/blob/ec155c7a50fb16646ab4ea3335b31b3706da50c3/reactive-streams/src/main/scala/fs2/interop/reactivestreams/StreamSubscription.scala#L142-L167).
- [#3063 server/consumer boundary](https://github.com/typelevel/fs2/pull/3063#discussion_r1028826801) and
  [#3341 synchronous-queue misconception](https://github.com/typelevel/fs2/pull/3341#discussion_r1404601115).
- Further pinned review comments (#3107 race, test fix, compatibility; #2300 lifetime) and code SHAs in evidence file.
