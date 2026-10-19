# ZIO HTTP channel handoff completion

> Library: ZIO HTTP (JVM Netty client pool). Originally the `scala-zio-http-channel-handoff-completion` skill; merged into `scala-http-server-semantics`. Evidence: [evidence/scala-zio-http-channel-handoff-completion.json](evidence/scala-zio-http-channel-handoff-completion.json).

Treat a completion promise as permission for another borrower to act, not merely a notification. Separate external channel failure from damage or unfinished cleanup left by the previous request.

## When to Use

Use for changes to the JVM Netty client's pool return/invalidation, `onComplete`/`onResponse` wiring, response-body last-message callbacks, or request-scope finalizers. Also use when apparently successful requests discard healthy connections or a borrowed channel closes and the request hangs.

## When Not to Use

Do not use as a general ZIO resource guide, HTTP framing guide, or nonpooled transport design. WebSocket upgrade and long-lived channel ownership require their own analysis: the January historical close listener deliberately excluded WebSockets. Do not convert the implementation to Cats Effect, Future or Ox.

## Prerequisites

Read the target build, exact dependency pins, driver, pool, body reader, caller and tests before suggesting a fix. Historical anchors differ:

- #2610: ZIO 2.0.19, Netty 4.1.101.Final, Scala 2.12.18/2.13.12/3.3.1; sbt 1.9.7; JVM `zioHttp` project.
- #2924: ZIO 2.1.1, Netty 4.1.109.Final, Scala 2.12.19/2.13.14/3.3.3; sbt 1.10.0; Netty code under JVM sources and project `zioHttpJVM`.

Do not transplant the earlier ZIO 1 `zhttp.HttpData` callback API. Establish the target's cancellation semantics and actual callback thread; a promise or scope name alone is insufficient.

## Workflow

1. **Map owners and signals.** Trace pool acquisition through request setup, response publication, body consumption, last content, reset, invalidation and release. Identify all writers and waiters of both promises, plus listener/fiber lifetimes. Include setup failure and interruption, not only successful responses.
2. **Separate two failure classes.** Prior-request damage requires cleanup or invalidation before returning the resource. External close can occur after any `isOpen` check; the use path must complete or fail pending waits. Do not blame lazy pool finalization for redelivery: adamgfraser explicitly corrected that diagnosis in #2610.
3. **Check each competing winner.** For remote close before response, identify who completes response and lifecycle waits. For intentional non-keepalive close, preserve publication of `Invalid` before the close listener can report interruption. `Invalid` must never authorize reuse. Avoid double completion work by checking which terminal signal won.
4. **Audit the three-event ordering.** In #2924, `AsyncBodyReader` removes itself, invokes `onLastMessage`, then delivers the final body callback. Its client subclass publishes completion in that hook. `ZClient` registers a finalizer that interrupts completion. Moving the callback earlier lets consumer scope closure win; publishing reuse before removing the reader lets another request encounter the old handler. This ordering rule is source-derived inference, not an approval-derived reviewer preference.
5. **Preserve the release protocol.** Trace reset failure into invalidation. Do not move cleanup to an unowned background task merely to return faster. Conversely, do not mechanically replace historical `forkDaemon`/`ensuring`: first identify the surrounding owner and termination signal.
6. **Bound retries without pretending they prove liveness.** #2610 tried fixed retries and reverted after an all-idle-closed-pool case. Its size-based schedule is a historical compromise, not enumeration of all changing pool entries. Preserve use-time failure handling even after retries succeed.

## Review and Refactoring Checks

Preserve these invariants: no reusable handoff while the previous request can mutate its pipeline; every terminal close/setup/cancellation path settles the waits it owns; failed reset prevents reuse; listener lifetime does not outlive its request ownership.

Check both streaming and aggregated body completion, including buffered content delivered after the network already finished. Distinguish response availability from body completion and pool release. False positives include treating `Invalid` before physical close as reusable handoff, assuming a successful `isOpen` guarantees lifetime, or demanding a single callback location without proving every failure reaches it.

## Validation

Read `build.sbt`, `project/Dependencies.scala`, `project/BuildHelper.scala`, `project/build.properties`, CI JDK settings and suite package declarations. In a separately authorized checkout, first use `sbt projects` and the discovered project's `show <project> / Test / definedTests`; require nonzero suite discovery. Review plugin/network side effects and match an installed supported JDK before running anything.

Source-derived selectors, **not executed here**:

- #2610: `sbt 'zioHttp/testOnly zio.http.netty.client.NettyConnectionPoolSpec'`.
- #2924 layout: `sbt 'zioHttpJVM/testOnly zio.http.netty.client.NettyConnectionPoolSpec'` after rediscovery. The PR changed no tests; do not claim this suite proves its particular race fixed.

Retain the January fixed/dynamic pool idle-timeout test with its live clock. Add controlled barriers for close-after-borrow/before-response, immediate scope exit from the final body callback, and immediate reborrow after completion. Observe promise outcomes, channel identity, installed handlers and invalidation counts, with an overall deadline and cleanup after failure. Repeated random traffic is supplemental, not a deterministic ordering oracle. Record runtime versus source-only evidence separately.

## Examples

### Good

A refactor preserves `remove reader -> publish completion -> final body callback`. On unexpected close before response, its owned close listener settles both waits; reset failure marks the channel invalid before return. Test a final callback that immediately ends the request scope and a waiting next borrower, rather than asserting only the returned response bytes.

### Broken and Correction

A simplification deletes the close listener because acquisition checks `isOpen`. A server can close after that check, leaving the response wait suspended. Correction: restore a request-owned terminal-close path and test that precise interleaving. A different simplification moves completion after the final body callback; correct it by restoring the three-event order, not by delaying scope finalization with an arbitrary sleep.

### Negative

The non-keepalive path publishes `Invalid` before intentionally closing the channel. Do not report this as reuse-before-close: it deliberately prevents reuse and avoids losing to the competing close listener. Likewise, a still-open WebSocket is not evidence of the ordinary HTTP request hang; investigate its distinct lifecycle separately.

## Output Contract

Return each finding with `file:line`, severity, triggering interleaving, violated invariant, evidence IDs and pinned source URLs, minimal correction, and regression test with observable terminal outcomes. Include the compiler/ZIO/Netty/project tuple and explicit unexecuted checks. A justified non-finding must state which owner or guard makes the suspicious ordering safe.

## Limitations

The procedure synthesizes #2610 review discussion and #2924 source evolution. #2924's approval is praise, not a design review, and it added no dedicated regression. No Scala compilation, race execution, performance improvement or current-version bug is established by this procedure. Do not generalize JVM Netty results to Scala.js or Native.

## Sources

See [claim and evidence records](evidence/scala-zio-http-channel-handoff-completion.json), especially `c-pool-handoff` and `c-pool-callback-order`.

- [Cleanup before return, #2610](https://github.com/zio/zio-http/pull/2610#issuecomment-1890183986).
- [External close is a use-time failure, #2610](https://github.com/zio/zio-http/pull/2610#issuecomment-1890235745).
- [Last-message order at the #2924 SHA](https://github.com/zio/zio-http/blob/2d323684f7dd3c8ac46739707b6cfd2a44bf312f/zio-http/jvm/src/main/scala/zio/http/netty/AsyncBodyReader.scala#L92-L111).
