# FS2 (typelevel/fs2): foreign callback lanes and server/consumer ownership — originally `scala-fs2-foreign-callback-lanes`

Evidence: [evidence/scala-fs2-foreign-callback-lanes.json](evidence/scala-fs2-foreign-callback-lanes.json), claims
`fs2-claim-callback-ownership` and `fs2-claim-callback-terminal-lifecycle`.

Scope: refactoring FS2 foreign request/cancel callbacks or restartable server streams. Separate ordered control work,
subscription execution and resource ownership. Applies to Reactive Streams adapters, Dispatcher migrations and
callback-backed accept loops where cancellation or demand must progress independently of data work. Identify both the
ordering contract and the lifetime owning each execution path.

Not for: a generic parallel-dispatcher prescription, a Kafka callback-thread recipe, or a replacement for Cats Effect
cancellation-outcome guidance (see `scala-effect-cancellation-finalization`). Per-element FS2 lease propagation is a
separate problem ([fs2-per-element-scope-propagation.md](fs2-per-element-scope-propagation.md)). A synchronous foreign
API requiring callbacks on a specific thread needs its own contract; a Dispatcher does not preserve caller-thread affinity.

## Prerequisites and version fences

Identify the foreign protocol, callback threading/reentrancy guarantees, FS2/Cats Effect versions and platform. Read both
callback entrypoints and the resource factories. Preserve the chosen effect model.

- #3000 uses CE 3.4.0-RC1 and two sequential dispatchers.
- #3107's January 2023 CE 3.4.4 source (merged) moves control ownership inside each subscription and uses a parallel
  start dispatcher for concurrent subscriptions. Reactive Streams JVM adapter only; current code must rediscover its
  actual subscribe API.
- #3063 tests an `async_` semantic change against CE `3.5-4b87497` (a snapshot), not a generic released-version promise.
  Preserve the target version's cancellation semantics instead of doing textual `async_` replacement. Its socket code is
  JVM/Native; the JS read/write/error lanes are another implementation, not JVM test coverage for Node.
- #2300 and #3341 are supplemental contextual discussion only; their current head diffs are excluded.

## Workflow

1. Make a lane table: submission order, whether work can wait for another callback, and resource owner. Requests and
   cancellation from one synchronous caller need ordering; the subscription may wait indefinitely for requests and cannot
   monopolize that same sequential lane. JS duplex read/write/error lanes can each be sequential yet must remain
   independent.
2. Put terminal-state checks inside the ordered submitted effect. A caller-side `if (!done)` followed by dispatch is a
   check/use race (it can race dispatcher shutdown). Do not add `unsafeRunSync` merely to order synchronous
   `cancel(); request()` submissions: #3107's reviewer explains why the sequential dispatcher already preserves that order
   without blocking the calling thread.
3. Trace terminal outcomes explicitly: normal exhaustion signals completion, failure signals error, cancellation stops
   work without inventing completion. Set terminal state before notifying the subscriber. Validate late request/cancel
   behavior when the per-subscription dispatcher has shut down. Only suppress the documented shutdown exception at that
   boundary; never swallow arbitrary callback failures.
4. Audit ownership end-to-end. #3107's `subscribeStream` returns an effect whose lifetime encloses
   `StreamSubscription.apply(...).use(_.run)`. An application-owned parallel dispatcher may run those effects, but
   application shutdown and subscriber cancellation must actually terminate them. Do not allocate a publisher resource,
   discard its release action and assert GC will clean it up. If the host framework exposes no usable lifetime hook,
   report the unresolved integration boundary rather than recommending a leak-prone migration.
5. For a `Resource` returning an accept stream, separate the listening socket from the inner consumer. #3063 puts
   acceptance in an outer-resource-owned background task with a synchronous handoff and explicit cleanup of unconsumed
   sockets. Test cancel/restart of the inner stream while retaining the outer resource, then test final outer release.
   Closing a server socket to cancel only an inner accept-stream consumer destroys restartability; a no-op cancel token
   can leave real work unowned. Do not claim this automatically solves every accepted-connection transfer scenario;
   #2300's historical follow-up remained a discussion.
6. Check backpressure at the submitting callback, not just the channel capacity. A foreign callback that repeatedly
   starts blocked sends can accumulate tasks even on a synchronous channel. The #3341 discussion rejects the assumption
   that zero buffered elements implies bounded memory: a synchronous handoff bounds pending elements only if producers
   respect backpressure. Coalesce only when the event protocol makes duplicates redundant; do not drop payloads or blindly
   replace event counters with booleans.

## Review checks

Preserve: ordered synchronous cancel/request becomes a no-op after cancellation; control work can progress while data work
waits; every live dispatcher/task/socket has an owner; terminal callbacks obey the actual protocol. Concurrent
subscription support requires independent runs and an appropriate start lane, not sharing a single stream execution by
accident. One sequential start lane for concurrent long-lived subscriptions prevents progress.

## False positives

- A sequential dispatcher is correct for short ordered control work.
- An application-owned parallel dispatcher is not inherently a leak. Conversely, its existence does not prove
  per-subscription cleanup.
- A resource handle intentionally returned after release is useful as a failed-publisher test, not a production
  lifecycle pattern. The TCK fixture in #3107 discards an allocation release action (`allocated._1`) and must not be
  copied as ownership guidance.
- A bridge that already uses independent per-subscription control lanes plus an application-owned parallel start
  dispatcher, with verified cancellation and shutdown, needs no global sequential dispatcher for stylistic consistency.
  A pure queue consumer with no foreign callbacks or ownership change does not trigger this workflow.

## Validation

After permission to run upstream builds, inspect the exact build, plugins and toolchain. Discover with `sbt projects` and
`sbt 'show reactiveStreams / Test / definedTests'`. At #3107 run
`sbt 'reactiveStreams/testOnly fs2.interop.reactivestreams.CancellationSpec'` and
`sbt 'reactiveStreams/testOnly fs2.interop.reactivestreams.StreamUnicastPublisherSpec'`; the latter integrates the
Reactive Streams TCK through TestNG. Require test discovery and results, not just compilation.

The revised CancellationSpec waits until subscription resources close before asserting, and does not flag mandatory
`onSubscribe` as an illicit data signal. Extend it with shutdown/callback races and multiple subscriptions. For sockets,
discover the actual I/O platform suite and add loopback cancel/restart and queued-socket-release tests; a JVM adapter test
is not evidence that a Native or Node accept path works. Repeated race tests and TCK coverage are useful but not proofs
over all schedules. No upstream tests ran during this research.

## Examples

- Good: at the #3107 boundary, a parallel application start dispatcher runs a subscription effect. That effect owns a
  sequential control dispatcher and releases it on termination. `cancel` and a subsequent `request` submit to the same
  control lane, with the request checking canceled state inside its effect. The long-running data stream cannot prevent
  control processing. Verify this ownership and ordering in the target version rather than copying obsolete constructors.
- Broken and correction: a refactor merges stream execution and demand processing onto one sequential dispatcher. The
  stream waits for demand while the demand task waits behind it. Correction: separate execution from ordered control,
  bind both to explicit owners and test progress. If the repair also replaces a global dispatcher with an allocated
  publisher, retain a real release hook or use the version-supported lifetime-enclosing subscription effect. Never drop
  the finalizer to make the signature convenient.

## Case-specific output

Lane/owner table; which shutdown exception is intentionally handled; which lifecycle hook closes each owner; whether
suggested migrations are source-verified or still speculative; model reasoning vs compiled/executed adapter and platform
tests.

## Limitations

The #3107 follow-up establishes a concrete per-subscription lifecycle design, not proof that every Play/Akka integration
migrated correctly. The #3000 GC reply was tentative and is not a cleanup guarantee. Socket finalization and platform
behavior still need runtime verification and independent review.

## Sources

- [#3000 independent lanes](https://github.com/typelevel/fs2/pull/3000#discussion_r984074090) and
  [consumer migration objection](https://github.com/typelevel/fs2/pull/3000#discussion_r1067094793).
- [#3107 ordering correction](https://github.com/typelevel/fs2/pull/3107#discussion_r1069996129) and
  [owned subscription implementation](https://github.com/typelevel/fs2/blob/ec155c7a50fb16646ab4ea3335b31b3706da50c3/reactive-streams/src/main/scala/fs2/interop/reactivestreams/StreamSubscription.scala#L142-L167).
- [#3063 server/consumer boundary](https://github.com/typelevel/fs2/pull/3063#discussion_r1028826801) and
  [#3341 synchronous-queue misconception](https://github.com/typelevel/fs2/pull/3341#discussion_r1404601115).
- Further pinned review comments (#3107 race, test fix, compatibility; #2300 lifetime) and code SHAs are in the evidence
  file.
