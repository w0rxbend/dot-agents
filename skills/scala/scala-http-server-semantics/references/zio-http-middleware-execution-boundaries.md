# ZIO HTTP middleware execution boundaries

> Library: ZIO HTTP (middleware / handler aspects).

Classify what middleware transforms before moving it. Returning Forbidden after protected handler ran is not rejecting request. Transforming selected handler is not transforming routing input.

## When to Use

Changing ZIO HTTP middleware lifting, composition operators, request-transform placement or rejection branches. Refactors that move checks around handler, unify handler/routing abstractions, or replace special cases with generic fallback.

## When Not to Use

Not complete CSRF/CORS security specification or routine routing tutorial. Never demand route-set preservation from middleware explicitly meant to add, remove or observe routes. Never force historical `Http` names onto modern `Routes` APIs or switch ZIO to another effect model.

## Prerequisites

Trace target operator to definition and callers, not just name. Read exact build, middleware implementation, regression suites. Historical examples span incompatible APIs:

- #542: ZIO 1.0.13, Scala 2.12.15/2.13.7/3.1.0, Netty 4.1.72.Final, sbt 1.6.1; package `zhttp`, project **`zhttp`** (not directory name `zio-http`, not `zioHttp`).
- #1916: ZIO 2.0.6, Scala 2.12.16/2.13.8/3.2.1, Netty 4.1.87.Final, sbt 1.7.3; package `zio.http`, project `zioHttp`.

Keep local syntax and dependencies. Modern handler aspects may encode same boundary differently: rediscover, do not copy 2023 implementation.

## Workflow

1. **Classify transformation.** Record whether it changes route selection, wraps selected handler, rejects before protected work, or observes unmatched requests. Name alone does not tell. State intended routing changes before judging equivalence.
2. **Draw execution path.** Original request, match decision, selected handler, pre-action, protected effects, post-action, response. Locate rejection branch before protected handler invocation. Check body and headers, not only status: success contents must not survive status-only rewrite.
3. **Instrument non-execution.** Adapt #542's retained Ref-backed flag/counter, mutated only when protected handler is evaluated. Missing or mismatched tokens must reject with zero protected executions; matching input must still execute once. Distinctive protected body/header sentinel detects leakage independently of status assertion.
4. **Preserve handler-only lifting.** #1916 `HandlerMiddleware` evaluates `route.run(in)` before applying aspect to resulting handler, preserving `Http.Empty`. Moving request transform before that operation may turn unmatched input into matched request. Restore selection boundary unless route transformation is requested semantic change.
5. **Test fallback by category.** Separate unmatched input, selected handler's typed failure, defect/interruption. Pinned test composes empty, failing, succeeding alternatives; expects selected failure, not later success. No catch-all recovery merely to simplify composition.
6. **Preserve observable order.** Record before/handler/after event sequence. Inspect operator's actual nesting; never assume left-to-right execution from spelling alone. Keep unrelated public renames and abstraction experiments out of semantic repair.

## Review and Refactoring Checks

Invariants: rejected requests run no protected effects and return none of their content; handler-only transformation does not alter match selection; unmatched fallback is distinct from typed-error recovery; before/handler/after order stays intentional.

False positives (explicit routing roles per #1916 discussion, not defects): CORS adding OPTIONS handling, trailing-slash normalization expanding accepted paths, allow/allowZIO restricting routing, metrics observing misses. Public error responses may intentionally carry bodies; #542 body-leak concern does not ban all failure bodies. Author-reported test addition is weaker than inspecting retained oracle: final CSRF suite retains non-execution, not earlier suggested standalone empty-body test.

## Validation

Read revision's `build.sbt`, dependency/compiler definitions, `project/build.properties`, CI JDK configuration, suite declarations. In separately authorized checkout: inspect build/plugin side effects, use installed compatible toolchain, discover projects/tests with `sbt projects` and `show <project> / Test / definedTests` before running.

Source-derived selectors, not executed research results:

- #542: `sbt 'zhttp/testOnly zhttp.middleware.MiddlewareSpec'`.
- #1916: `sbt 'zioHttp/testOnly zio.http.HttpSpec zio.http.MiddlewareSpec'`.

Require nonzero executed tests. Matrix: matched/unmatched input, accepted/rejected guard, selected typed failure, defect, interruption. Per cell assert handler count, selected route, status/body/header policy, event order where meaningful. Add separate CORS preflight or normalization case so review does not reject intentional routing middleware. Record user-requested semantic changes as new expectations, not disguised equivalent refactors.

## Examples

### Good

Rejected request selects constant Forbidden application before protected handler: counter stays zero, body/header sentinel absent. Accepted input: counter is one. Handler-only request transformer runs only after original input selected handler; unmatched input stays unmatched. Combines two historical boundaries, not one unchanged API across ZIO versions.

### Broken and Correction

Refactor invokes application unconditionally, overwrites status to Forbidden on token mismatch. Status-only test passes though protected effects ran. Correction: branch before invocation; add counter and response-content checks. Separately, if generic fallback catches selected typed failure and tries next successful handler, restore unmatched-only fallback and assert original typed failure survives.

### Negative

CORS deliberately handles OPTIONS request application did not match. Routing middleware, not handler-aspect route-set violation. Verify its policy and that ordinary requests keep documented behavior; do not move CORS after route selection merely to satisfy overly broad rule.

## Output Contract

Return `file:line`, severity, middleware category, before/after execution order, violated invariant, historical evidence IDs/URLs, minimal correction, discriminating test. Name exact compiler/ZIO/project tuple; separate observed source from proposed current-version checks. For intentional route changes, explain why no preservation finding applies; list new behavior needing validation.

## Limitations

Explicit synthesis of #542 and #1916, not universal maintainer preference. Does not establish modern CSRF token strength, cookie policy, origin validation or complete middleware laws. No upstream suite was executed here. Lifecycle changes need separate investigation; status/counter tests alone cannot prove correct transport cancellation.

## Sources

See [claim and evidence records](evidence/scala-zio-http-middleware-execution-boundaries.json), especially `c-middleware-semantics`.

- [Body-leak review concern](https://github.com/zio/zio-http/pull/542#discussion_r775559278).
- [Retained non-execution regression](https://github.com/zio/zio-http/blob/9d5873feed82a6cbac67c542ff2e23a9fcb31d25/zio-http/src/test/scala/zhttp/middleware/MiddlewareSpec.scala#L205-L211).
- [Routing middleware exceptions](https://github.com/zio/zio-http/pull/1916#discussion_r1068100429).
- [Handler-only lifting](https://github.com/zio/zio-http/blob/5bee815db9bb37aa2a2f99fc1a0262b8bce271b8/zio-http/src/main/scala/zio/http/HandlerMiddleware.scala#L30-L39).
