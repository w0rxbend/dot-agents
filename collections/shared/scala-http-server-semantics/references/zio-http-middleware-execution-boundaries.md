# ZIO HTTP middleware execution boundaries

> Library: ZIO HTTP (middleware / handler aspects). Originally the `scala-zio-http-middleware-execution-boundaries` skill; merged into `scala-http-server-semantics`. Evidence: [evidence/scala-zio-http-middleware-execution-boundaries.json](evidence/scala-zio-http-middleware-execution-boundaries.json).

Classify what a middleware transforms before moving it. Returning Forbidden after executing a protected handler is not equivalent to rejecting the request; transforming a selected handler is not equivalent to transforming routing input.

## When to Use

Use when changing middleware lifting, composition operators, request transformation placement or rejection branches in ZIO HTTP. Apply to refactors that move checks around a handler, unify handler/routing abstractions, or replace special cases with generic fallback logic.

## When Not to Use

Do not use as a complete CSRF/CORS security specification or routine routing tutorial. Do not demand route-set preservation from middleware explicitly intended to add, remove or observe routes. Do not enforce historical `Http` names on modern `Routes` APIs, or convert ZIO into a different effect model.

## Prerequisites

Trace the target operator to its definition and callers, not just its name. Read the exact build, middleware implementation and regression suites. The historical examples span incompatible APIs:

- #542: ZIO 1.0.13, Scala 2.12.15/2.13.7/3.1.0, Netty 4.1.72.Final, sbt 1.6.1; package `zhttp`, project **`zhttp`** (not the directory name `zio-http` and not `zioHttp`).
- #1916: ZIO 2.0.6, Scala 2.12.16/2.13.8/3.2.1, Netty 4.1.87.Final, sbt 1.7.3; package `zio.http`, project `zioHttp`.

Preserve local syntax and dependencies. Modern handler aspects may encode the same boundary differently; rediscover them rather than copying the 2023 implementation.

## Workflow

1. **Classify the transformation.** Record whether it changes route selection, wraps a selected handler, rejects before protected work, or observes unmatched requests. A name such as middleware does not answer this. Make intended routing changes explicit before judging equivalence.
2. **Draw the execution path.** Identify original request, match decision, selected handler, pre-action, protected effects, post-action and response. For rejections, locate the branch before protected handler invocation. Check body and headers as well as status; do not allow a successful response's contents to survive a status-only rewrite.
3. **Instrument non-execution.** Adapt #542's retained Ref-backed flag/counter: the protected handler mutates it only when actually evaluated. Missing or mismatched tokens must reject with zero protected executions. Matching input must still execute once. Use a distinctive protected body/header sentinel to detect leakage independently of the status assertion.
4. **Preserve handler-only lifting.** In #1916 `HandlerMiddleware` evaluates `route.run(in)` before applying the aspect to the resulting handler, and preserves `Http.Empty`. Moving a request transform before that operation may turn unmatched input into a matched request. Repair by restoring the selection boundary, unless route transformation is the requested semantic change.
5. **Test fallback by category.** Distinguish unmatched input from a selected handler's typed failure and from defect/interruption. The pinned test composes empty, failing and succeeding alternatives and expects the selected failure, not the later success. Do not introduce catch-all recovery merely to simplify composition.
6. **Preserve observable order.** Capture an event sequence for before/handler/after. Inspect the operator's actual nesting; never assume left-to-right execution from spelling alone. Keep unrelated public renames and abstraction experiments out of a semantic repair.

## Review and Refactoring Checks

Preserve these invariants: rejected requests do not run protected effects or return their content; a handler-only transformation does not alter match selection; unmatched fallback is distinct from typed-error recovery; before/handler/after order remains intentional.

False positives: CORS may add OPTIONS handling, trailing-slash normalization may expand accepted paths, allow/allowZIO may restrict routing, and metrics may observe misses. Those are explicit routing roles in #1916's discussion, not defects. Public error responses can intentionally contain bodies; the #542 body-leak concern does not prohibit all failure bodies. Likewise an author-reported test addition is weaker than inspecting the retained oracle: the final CSRF suite retains non-execution, not the earlier suggested standalone empty-body test.

## Validation

Read the revision's `build.sbt`, dependency/compiler definitions, `project/build.properties`, CI JDK configuration and suite declarations. In a separately authorized checkout, inspect build/plugin side effects, use an installed compatible toolchain, and discover projects/tests with `sbt projects` and `show <project> / Test / definedTests` before execution.

Actual source-derived selectors, not executed research results:

- #542: `sbt 'zhttp/testOnly zhttp.middleware.MiddlewareSpec'`.
- #1916: `sbt 'zioHttp/testOnly zio.http.HttpSpec zio.http.MiddlewareSpec'`.

Require nonzero executed tests. Build a matrix of matched/unmatched inputs, accepted/rejected guards, selected typed failure, defect and interruption. For each cell assert handler count, selected route, status/body/header policy and event order where meaningful. Add a separate CORS preflight or normalization case to ensure the review does not reject intentional routing middleware. Retain user-requested semantic changes as new expectations rather than disguising them as equivalent refactors.

## Examples

### Good

A rejected request selects a constant Forbidden application before the protected handler. The protected counter stays zero and its body/header sentinel is absent. On accepted input the counter is one. A handler-only request transformer runs only after the original input selected a handler; an unmatched input remains unmatched. These combine two historical boundaries, not one unchanged API across ZIO versions.

### Broken and Correction

A refactor invokes the application unconditionally and overwrites status to Forbidden on token mismatch. Its status-only test passes despite protected effects running. Correction: branch before invocation and add the counter plus response-content checks. Separately, if generic fallback catches a selected typed failure and tries the next successful handler, restore unmatched-only fallback and assert the original typed failure survives.

### Negative

CORS deliberately handles an OPTIONS request that the application did not match. Do not flag that as a handler-aspect route-set violation: it is routing middleware. Verify its policy and that ordinary requests retain their documented behavior instead of moving it after route selection merely to satisfy an overly broad rule.

## Output Contract

Return `file:line`, severity, middleware category, before/after execution order, violated invariant, historical evidence IDs/URLs, minimal correction and a discriminating test. Identify the exact compiler/ZIO/project tuple and distinguish observed source from proposed current-version checks. For intentional route changes, explain why no preservation finding applies and list the new behavior requiring validation.

## Limitations

This is an explicit synthesis of #542 and #1916, not a universal maintainer preference. It does not establish modern CSRF token strength, cookie policy, origin validation or complete middleware laws. No upstream suite was executed here. Lifecycle changes require separate investigation; status/counter tests alone cannot prove correct transport cancellation.

## Sources

See [claim and evidence records](evidence/scala-zio-http-middleware-execution-boundaries.json), especially `c-middleware-semantics`.

- [Body-leak review concern](https://github.com/zio/zio-http/pull/542#discussion_r775559278).
- [Retained non-execution regression](https://github.com/zio/zio-http/blob/9d5873feed82a6cbac67c542ff2e23a9fcb31d25/zio-http/src/test/scala/zhttp/middleware/MiddlewareSpec.scala#L205-L211).
- [Routing middleware exceptions](https://github.com/zio/zio-http/pull/1916#discussion_r1068100429).
- [Handler-only lifting](https://github.com/zio/zio-http/blob/5bee815db9bb37aa2a2f99fc1a0262b8bce271b8/zio-http/src/main/scala/zio/http/HandlerMiddleware.scala#L30-L39).
