# ZIO HTTP request-local error disclosure

> Library: ZIO HTTP (`Response` error rendering). Originally the `scala-zio-http-request-local-error-disclosure` skill; merged into `scala-http-server-semantics`. Evidence: [evidence/scala-zio-http-request-local-error-disclosure.json](evidence/scala-zio-http-request-local-error-disclosure.json).

Review generated diagnostic content independently from HTTP status. A correct status does not authorize exception messages or stack traces, and matching the renderer's own string template is not a serialization oracle.

## When to Use

Use for refactoring exception/cause-to-response rendering, body/stack flags, debug middleware, FiberRef access or renderer optimizations. Trigger when reducing fiber allocation could change which request's policy is observed, or when exception text is inserted into JSON or HTML.

## When Not to Use

Do not use to ban intentionally public domain-error bodies, redesign endpoint error types, or replace the application's chosen effect stack. A separately authenticated diagnostic endpoint may intentionally expose approved details; assess its authorization and rendering rather than automatically stripping its body. CORS/CSRF policy configuration belongs elsewhere.

## Prerequisites

Locate every caller of the target renderer, the policy store, route middleware, Netty runtime bridge and tests. Record exact versions and distinguish default configuration from request overrides.

The principal observed implementation is #3050 at `ab9fdf7a8778ab233046d7565a1b4517d440809e`: ZIO 2.1.8, Netty 4.1.112.Final, Scala 2.12.19/2.13.14/3.3.3, sbt 1.10.0. APIs are shared but the inspected `ResponseSpec` is JVM-only. The 2022 static-file #850 discussion is an earlier disclosure/nullability concern, not proof that its unverified successor shipped a fix.

## Workflow

1. **Inventory information crossing the boundary.** Classify status, public domain data, exception message, stack trace and internal cause diagnostics. Mark trust level and the authorized audience of each field. Follow both `fromThrowable` and `fromCause`; do not infer one from the other.
2. **Write a policy matrix.** Cover defaults, body enabled/disabled, stack enabled/disabled, bounded/unbounded trace depth, format selection, null messages and explicit domain `Response` values. In #3050 defaults disable generated body and stack; the configured format remains Html despite a plaintext review proposal. Accept negotiation and configured fallback are not synonymous.
3. **Trace request-local context.** Record where the FiberRef is set and read, fiber inheritance, restoration or request lifetime, and any captured runtime defaults. The author explicitly wanted per-route/request overrides. Replacing FiberRef with a global Ref or route-keyed map is not an equivalent optimization without proof of isolation. A low-level callback with only a captured runtime may see defaults rather than a later request override; test the actual path instead of asserting universal propagation.
4. **Keep omission separate from mapping.** Suppressing details must not silently change Forbidden/NotFound/BadRequest/InternalServerError selection. Preserve explicitly returned public responses. Before changing stack handling, inspect cause-only rendering: the historical `fromCause` fallback uses `prettyPrint` when body disclosure is enabled, whereas Throwable rendering has explicit stack/depth gates. Treat uniform controls as a proposed policy change unless target behavior already promises them.
5. **Replace self-confirming serialization tests.** The historical JSON renderer interpolates message and stack strings; its test repeats that template. Require parsing and value round trips for quotes, backslashes, newlines, control characters and Unicode, including multiline traces. Inspect HTML text escaping separately; JSON safety does not establish HTML safety. Choose an encoder already present in the target build rather than inventing a serializer dependency.
6. **Review optimizations against policy.** Avoid starting a fiber merely to read configuration when the same correctly owned context is available. Do not cache a request-specific decision globally or eagerly capture it at route construction. Preserve null-safe message handling and avoid computing stacks when omitted by the selected path.

## Review and Refactoring Checks

Preserve the invariant that one request cannot enable diagnostics for another. Test concurrent opposite policies and successive requests on reused execution infrastructure; also check nested overrides and failure cleanup. Keep status assertions separate from body absence and stack absence.

False positives: a typed public error is not necessarily secret; a guard may already prevent disclosure; a reviewer proposal is not the final default. Conversely, request-local storage is not authorization. An untrusted client header that enables debug remains unsafe unless an independently verified access-control policy permits it.

## Validation

Discover the build with `build.sbt`, `project/{Dependencies.scala,BuildHelper.scala,build.properties}`, CI JDK settings, and `ResponseSpec`'s package. After separately authorizing upstream execution and checking plugins/dependency availability, use `sbt projects` and `sbt 'show zioHttpJVM / Test / definedTests'` for the #3050 layout. Require actual test discovery, then `sbt 'zioHttpJVM/testOnly zio.http.ResponseSpec'`. These commands are source-derived; none was run during research. Rediscover names for any other revision.

Add a parser-based response suite using the target's real decoder. Assert parsed message equals input, output media type matches the supported format, default generated body is empty, and status is unchanged by disclosure switches. Exercise Throwable, cause-only diagnostics, typed Response passthrough and transport failure separately. Use barriers to overlap public/default and authorized-debug requests, then prove no cross-request message/stack leakage. An exact-template test may remain for formatting, but cannot replace these oracles.

## Examples

### Good

An authorized request enables a JSON diagnostic body while an overlapping public request retains defaults. Both return the intended status; only the authorized body contains its message. A parser round-trips a message containing a quote and newline, and separate assertions check trace depth. This is an applicable target-version test design, not an executed historical result.

### Broken and Correction

A renderer substitutes exception text directly into a quoted JSON field and compares output to the same interpolated expected string. Both can agree on malformed JSON. Correction: use the project's real encoder and parse the response in the regression test; include hostile message and trace characters. Keep request-local policy and status unchanged. Do not fix serialization by enabling all debug bodies or adding a process-wide flag.

### Negative

A domain endpoint intentionally returns a documented public error response. Do not strip it merely because its status is 4xx: #3050's `fromCause` preserves an existing `Response`. Also reject a historical finding that plaintext became the default solely because a reviewer suggested it; the pinned configuration says Html.

## Output Contract

For each finding report `file:line`, severity, data exposed or malformed, policy/context path, preserved invariant, evidence ID and source URL, minimal change, and test oracle. State whether the finding is observed historical code, an explicit reviewer concern, or a current-version inference needing reproduction. List build/version/platform and exactly what ran; no source inspection should be labeled compilation.

## Limitations

Parser-based hostile-message testing and concurrent isolation probes are hardening inferences from #3050, not tests proven by that PR. No present-day vulnerability, universal FiberRef propagation, HTML safety or uniform Cause trace-depth behavior is asserted. #850 closed without direct merge; its successor #1024 was not verified. Request-local debug policy alone is not a complete security design.

## Sources

Read [claim and evidence records](evidence/scala-zio-http-request-local-error-disclosure.json), especially `c-error-disclosure`.

- [Earlier message disclosure/nullability concern](https://github.com/zio/zio-http/pull/850#discussion_r791937290).
- [Per-route/request intent](https://github.com/zio/zio-http/pull/3050#discussion_r1733161810).
- [Pinned renderer disclosure gate and JSON construction](https://github.com/zio/zio-http/blob/ab9fdf7a8778ab233046d7565a1b4517d440809e/zio-http/shared/src/main/scala/zio/http/Response.scala#L259-L311).
