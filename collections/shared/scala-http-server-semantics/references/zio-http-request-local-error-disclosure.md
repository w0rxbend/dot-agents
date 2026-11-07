# ZIO HTTP request-local error disclosure

> Library: ZIO HTTP (`Response` error rendering).

Review generated diagnostic content separately from HTTP status. Correct status does not authorize exception messages or stack traces. Matching renderer's own string template is not serialization oracle.

## When to Use

Refactoring exception/cause-to-response rendering, body/stack flags, debug middleware, FiberRef access or renderer optimizations. Also when cutting fiber allocation could change which request's policy is observed, or when exception text enters JSON or HTML.

## When Not to Use

Not for banning intentionally public domain-error bodies, redesigning endpoint error types, or replacing application's chosen effect stack. Separately authenticated diagnostic endpoint may intentionally expose approved details: assess its authorization and rendering, do not automatically strip its body. CORS/CSRF policy configuration belongs elsewhere.

## Prerequisites

Locate every caller of target renderer, plus policy store, route middleware, Netty runtime bridge, tests. Record exact versions; separate default configuration from request overrides.

Principal observed implementation: #3050 at `ab9fdf7a8778ab233046d7565a1b4517d440809e` (ZIO 2.1.8, Netty 4.1.112.Final, Scala 2.12.19/2.13.14/3.3.3, sbt 1.10.0). APIs shared, but inspected `ResponseSpec` is JVM-only. 2022 static-file discussion #850 is earlier disclosure/nullability concern, not proof its unverified successor shipped a fix.

## Workflow

1. **Inventory information crossing boundary.** Classify status, public domain data, exception message, stack trace, internal cause diagnostics. Mark each field's trust level and authorized audience. Follow both `fromThrowable` and `fromCause`; never infer one from other.
2. **Write policy matrix.** Defaults, body enabled/disabled, stack enabled/disabled, bounded/unbounded trace depth, format selection, null messages, explicit domain `Response` values. #3050 defaults disable generated body and stack; configured format stays Html despite plaintext review proposal. Accept negotiation and configured fallback are not synonymous.
3. **Trace request-local context.** Record where FiberRef is set and read, fiber inheritance, restoration or request lifetime, captured runtime defaults. Author explicitly wanted per-route/request overrides. Swapping FiberRef for global Ref or route-keyed map is not equivalent optimization without isolation proof. Low-level callback holding only captured runtime may see defaults, not later request override: test actual path, do not assert universal propagation.
4. **Keep omission separate from mapping.** Suppressing details must not silently change Forbidden/NotFound/BadRequest/InternalServerError selection. Preserve explicitly returned public responses. Before changing stack handling, inspect cause-only rendering: historical `fromCause` fallback uses `prettyPrint` when body disclosure is enabled; Throwable rendering has explicit stack/depth gates. Uniform controls are proposed policy change unless target behavior already promises them.
5. **Replace self-confirming serialization tests.** Historical JSON renderer interpolates message and stack strings; its test repeats that template. Require parsing and value round trips for quotes, backslashes, newlines, control characters, Unicode, multiline traces. Check HTML text escaping separately; JSON safety does not establish HTML safety. Use encoder already in target build; do not invent serializer dependency.
6. **Review optimizations against policy.** Avoid starting fiber merely to read configuration when same correctly owned context is available. Never cache request-specific decision globally or eagerly capture it at route construction. Keep null-safe message handling; avoid computing stacks selected path omits.

## Review and Refactoring Checks

Invariant: one request cannot enable diagnostics for another. Test concurrent opposite policies, successive requests on reused execution infrastructure, nested overrides, failure cleanup. Assert status separately from body absence and stack absence.

False positives: typed public error is not necessarily secret; guard may already prevent disclosure; reviewer proposal is not final default. Conversely, request-local storage is not authorization: untrusted client header enabling debug stays unsafe unless independently verified access-control policy permits it.

## Validation

Discover build via `build.sbt`, `project/{Dependencies.scala,BuildHelper.scala,build.properties}`, CI JDK settings, `ResponseSpec`'s package. After separately authorizing upstream execution and checking plugins/dependency availability, use `sbt projects` and `sbt 'show zioHttpJVM / Test / definedTests'` for #3050 layout. Require actual test discovery, then `sbt 'zioHttpJVM/testOnly zio.http.ResponseSpec'`. Commands are source-derived; none ran during research. Rediscover names for any other revision.

Add parser-based response suite with target's real decoder. Assert: parsed message equals input, media type matches supported format, default generated body is empty, disclosure switches leave status unchanged. Exercise separately: Throwable, cause-only diagnostics, typed Response passthrough, transport failure. Overlap public/default and authorized-debug requests with barriers; prove no cross-request message/stack leakage. Exact-template test may stay for formatting but cannot replace these oracles.

## Examples

### Good

Authorized request enables JSON diagnostic body; overlapping public request keeps defaults. Both return intended status; only authorized body contains its message. Parser round-trips message with quote and newline; separate assertions check trace depth. Applicable target-version test design, not executed historical result.

### Broken and Correction

Renderer substitutes exception text directly into quoted JSON field; test compares output to same interpolated expected string. Both can agree on malformed JSON. Correction: use project's real encoder, parse response in regression test, include hostile message and trace characters. Keep request-local policy and status unchanged. Do not fix serialization by enabling all debug bodies or adding process-wide flag.

### Negative

Domain endpoint intentionally returns documented public error response. Do not strip it merely because status is 4xx: #3050's `fromCause` preserves existing `Response`.

## Output Contract

Per finding report `file:line`, severity, data exposed or malformed, policy/context path, preserved invariant, evidence ID and source URL, minimal change, test oracle. State whether finding is observed historical code, explicit reviewer concern, or current-version inference needing reproduction. List build/version/platform and exactly what ran; never label source inspection as compilation.

## Limitations

Parser-based hostile-message testing and concurrent isolation probes are hardening inferences from #3050, not tests that PR proved. Does not assert present-day vulnerability, universal FiberRef propagation, HTML safety or uniform Cause trace-depth behavior. #850 closed without direct merge; successor #1024 not verified. Request-local debug policy alone is not complete security design.

## Sources

Read [claim and evidence records](evidence/scala-zio-http-request-local-error-disclosure.json), especially `c-error-disclosure`.

- [Earlier message disclosure/nullability concern](https://github.com/zio/zio-http/pull/850#discussion_r791937290).
- [Per-route/request intent](https://github.com/zio/zio-http/pull/3050#discussion_r1733161810).
- [Pinned renderer disclosure gate and JSON construction](https://github.com/zio/zio-http/blob/ab9fdf7a8778ab233046d7565a1b4517d440809e/zio-http/shared/src/main/scala/zio/http/Response.scala#L259-L311).
