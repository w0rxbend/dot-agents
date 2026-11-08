# ZIO HTTP channel handoff completion

> Library: ZIO HTTP (JVM Netty client pool). Formerly `scala-zio-http-channel-handoff-completion` skill, merged into `scala-http-server-semantics`. Evidence: [evidence/scala-zio-http-channel-handoff-completion.json](evidence/scala-zio-http-channel-handoff-completion.json).

Completion promise is permission for another borrower to act, not mere notification. Separate external channel failure from damage or unfinished cleanup left by previous request.

## When to Use

JVM Netty client pool return/invalidation, `onComplete`/`onResponse` wiring, response-body last-message callbacks or request-scope finalizers. Also when apparently successful requests discard healthy connections, or borrowed channel closes and request hangs.

## When Not to Use

Not a general ZIO resource guide, HTTP framing guide or nonpooled transport design. WebSocket upgrade and long-lived channel ownership need own analysis: January historical close listener deliberately excluded WebSockets. Do not convert implementation to Cats Effect, Future or Ox.

## Prerequisites

Before suggesting fix, read target build, exact dependency pins, driver, pool, body reader, caller, tests. Historical anchors differ:

- #2610: ZIO 2.0.19, Netty 4.1.101.Final, Scala 2.12.18/2.13.12/3.3.1; sbt 1.9.7; JVM `zioHttp` project.
- #2924: ZIO 2.1.1, Netty 4.1.109.Final, Scala 2.12.19/2.13.14/3.3.3; sbt 1.10.0; Netty code under JVM sources and project `zioHttpJVM`.

Do not transplant earlier ZIO 1 `zhttp.HttpData` callback API. Establish target's cancellation semantics and actual callback thread; promise or scope name alone is insufficient.

## Workflow

1. **Map owners and signals.** Trace pool acquisition through request setup, response publication, body consumption, last content, reset, invalidation, release. Find all writers and waiters of both promises, plus listener/fiber lifetimes. Include setup failure and interruption, not only successful responses.
2. **Separate two failure classes.** Prior-request damage needs cleanup or invalidation before resource returns. External close can happen after any `isOpen` check; use path must complete or fail pending waits. Do not blame lazy pool finalization for redelivery: adamgfraser explicitly corrected that diagnosis in #2610.
3. **Check each competing winner.** Remote close before response: identify who completes response and lifecycle waits. Intentional non-keepalive close: keep publishing `Invalid` before close listener can report interruption. `Invalid` must never authorize reuse. Check which terminal signal won to avoid double completion work.
4. **Audit the three-event ordering.** In #2924, `AsyncBodyReader` removes itself, invokes `onLastMessage`, then delivers final body callback. Client subclass publishes completion in that hook. `ZClient` registers finalizer that interrupts completion. Moving callback earlier lets consumer scope closure win; publishing reuse before reader removal lets another request meet old handler. This ordering rule is source-derived inference, not approval-derived reviewer preference.
5. **Preserve the release protocol.** Trace reset failure into invalidation. Do not move cleanup to unowned background task merely to return faster. Do not mechanically replace historical `forkDaemon`/`ensuring` either: first identify surrounding owner and termination signal.
6. **Bound retries without pretending they prove liveness.** #2610 tried fixed retries, reverted after all-idle-closed-pool case. Its size-based schedule is historical compromise, not enumeration of all changing pool entries. Keep use-time failure handling even after retries succeed.

## Review and Refactoring Checks

Invariants: no reusable handoff while previous request can mutate its pipeline; every terminal close/setup/cancellation path settles waits it owns; failed reset prevents reuse; listener lifetime does not outlive its request ownership.

Check streaming and aggregated body completion, including buffered content delivered after network finished. Distinguish response availability, body completion, pool release. False positives: treating `Invalid` before physical close as reusable handoff; assuming successful `isOpen` guarantees lifetime; demanding single callback location without proving every failure reaches it.

## Validation

Read `build.sbt`, `project/Dependencies.scala`, `project/BuildHelper.scala`, `project/build.properties`, CI JDK settings, suite package declarations. In separately authorized checkout, first run `sbt projects` and discovered project's `show <project> / Test / definedTests`; require nonzero suite discovery. Before running anything, review plugin/network side effects and match an installed supported JDK.

Source-derived selectors, **not executed here**:

- #2610: `sbt 'zioHttp/testOnly zio.http.netty.client.NettyConnectionPoolSpec'`.
- #2924 layout: `sbt 'zioHttpJVM/testOnly zio.http.netty.client.NettyConnectionPoolSpec'` after rediscovery. PR changed no tests; do not claim this suite proves its particular race fixed.

Keep January fixed/dynamic pool idle-timeout test with its live clock. Add controlled barriers for close-after-borrow/before-response, immediate scope exit from final body callback, immediate reborrow after completion. Observe promise outcomes, channel identity, installed handlers, invalidation counts, with overall deadline and cleanup after failure. Repeated random traffic is supplemental, not deterministic ordering oracle. Record runtime and source-only evidence separately.

## Examples

### Good

Refactor keeps `remove reader -> publish completion -> final body callback`. Unexpected close before response: owned close listener settles both waits; reset failure marks channel invalid before return. Test final callback that immediately ends request scope and a waiting next borrower, not just returned response bytes.

### Broken and Correction

Simplification deletes close listener because acquisition checks `isOpen`. Server can close after that check, leaving response wait suspended. Correction: restore request-owned terminal-close path; test that exact interleaving. Another simplification moves completion after final body callback: restore three-event order, do not delay scope finalization with arbitrary sleep.

### Negative

Non-keepalive path publishes `Invalid` before intentionally closing channel. Do not report as reuse-before-close: it deliberately prevents reuse and avoids losing to competing close listener. Still-open WebSocket is not evidence of ordinary HTTP request hang either; investigate its distinct lifecycle separately.

## Output Contract

Per finding: `file:line`, severity, triggering interleaving, violated invariant, evidence IDs and pinned source URLs, minimal correction, regression test with observable terminal outcomes. Include compiler/ZIO/Netty/project tuple and explicit unexecuted checks. Justified non-finding must state which owner or guard makes suspicious ordering safe.

## Limitations

Synthesizes #2610 review discussion and #2924 source evolution. #2924's approval is praise, not design review; it added no dedicated regression. Procedure establishes no Scala compilation, race execution, performance improvement or current-version bug. Do not generalize JVM Netty results to Scala.js or Native.

## Sources

See [claim and evidence records](evidence/scala-zio-http-channel-handoff-completion.json), especially `c-pool-handoff` and `c-pool-callback-order`.

- [Cleanup before return, #2610](https://github.com/zio/zio-http/pull/2610#issuecomment-1890183986).
- [External close is a use-time failure, #2610](https://github.com/zio/zio-http/pull/2610#issuecomment-1890235745).
- [Last-message order at the #2924 SHA](https://github.com/zio/zio-http/blob/2d323684f7dd3c8ac46739707b6cfd2a44bf312f/zio-http/jvm/src/main/scala/zio/http/netty/AsyncBodyReader.scala#L92-L111).
