---
name: scala-http-server-semantics
description: Use when changing or reviewing HTTP server/client semantics in Scala libraries (http4s Ember HTTP/1 framing and connection reuse, http4s URI path segments, Cask route-trie validation and 404/405 dispatch, ZIO HTTP pooled-channel handoff, middleware execution boundaries and error disclosure, Play CORS/CSRF filter policy) by treating behavior as an explicit matrix of observable outcomes. Covers protocol and policy decisions at the request/connection boundary; effect cancellation, stream scoping, binary compatibility and hot-path cost belong to the sibling merged skills.
license: MIT
---

# Scala HTTP server semantics as a behavior matrix

Seven historical cases from http4s, Cask, ZIO HTTP and Play share one failure shape. Refactor keeps one visible signal
green (status code, empty body, successful startup, passing replacement test) but silently changes another HTTP
contract dimension (unread socket bytes, segment boundaries, lost duplicate registration, borrower admitted too early,
protected handler still ran, stack trace shown to wrong request, token cookie behind public cache).

Each case derived from pinned 2019-2024 source and maintainer PR review history, then audited. Evaluated by source
inspection and model-based review; **no upstream build, test, socket, or browser probe was executed** during research.

## When to Use

- Diff changes HTTP/1 response framing, HEAD/no-body handling, drain/remainder metadata, or pool reuse decisions.
- Diff changes URI path parsing, rendering, segment constructors, normalization, or String-to-Path equality.
- Diff changes route registration, route-trie construction, ambiguity validation, or missing-path/missing-method status.
- Diff changes pooled-channel completion, close listeners, body last-message callbacks, or request-scope finalizers.
- Diff moves middleware relative to route selection or protected handler, or changes fallback between routes.
- Diff changes exception/cause-to-response rendering, debug flags, or where disclosure policy is stored and read.
- Diff changes CORS origin-to-header decisions or CSRF token/shared-cache predicates, their config readers, or tests.
- Same shapes in another Scala HTTP stack (Akka/Pekko HTTP, Finagle, Tapir interpreters, sttp backends); apply
  transferable checks only and rediscover library facts from source.

## When Not to Use

- HTTP/2 framing, request-smuggling diagnosis, complete URI/RFC conformance audits, full CSRF/CORS security design,
  or browser/CDN behavior claims.
- General effect cancellation, `Resource`/`Scope` finalization or outcome-sensitive concurrency without HTTP
  ownership question: use `scala-effect-cancellation-finalization`. Stream scoping and sink cardinality:
  `scala-stream-resource-scoping`. Public API/binary compatibility and law-backed instances:
  `scala-library-compatibility-laws` or `scala-library-contracts`. Hot-path cost and diagnostic modes:
  `scala-runtime-diagnostics-hot-paths`. Macro/compiler refactors: `scala-compiler-macro-refactoring`.
- Choosing library for new project; use `scala-oss-library-review` router.
- Converting target's effect model. No case justifies moving Cask, Play, http4s or ZIO HTTP to Cats Effect, ZIO,
  FS2, Future or Ox; keep local runtime, syntax and build tool.
- Approving or rejecting intentional, documented policy change as if regression (see False positives).

## Prerequisites

1. Identify library, exact source SHA or version, Scala cross versions, effect runtime version, transport (Netty,
   Undertow, Ember/FS2, Akka/Pekko), JDK, and build tool. Historical anchors differ per case and are **not** current
   targets (see Version fences).
2. Trace each touched operator to definition and callers; names like `Drain`, `middleware`, `isCached`, `Invalid` or
   `normalize` do not establish semantics.
3. Load relevant case reference(s) from routing table before writing findings.

## Shared model: invariants that recur across cases

Case names in parentheses are files under `references/`.

**I1. One green signal is not the contract; enumerate observable dimensions.** Record each dimension independently
before and after change.

- Framing: body exposed to callers, bytes buffered after framing, bytes still unread on socket, connection
  disposition. Empty public body establishes none of other three (`http4s-http1-bodyless-connection-framing`).
- Middleware rejection: status, protected-handler execution count, response body/header content
  (`zio-http-middleware-execution-boundaries`).
- Error rendering: status, generated body presence, stack presence, serialization validity
  (`zio-http-request-local-error-disclosure`).
- CORS: ACAO, ACAC, Vary, status, on normal and preflight paths; CSRF: token-cookie outcome with token-creation
  eligibility held constant (`play-cors-csrf-policy-matrix`).
- Routing: construction success, selected endpoint, wildcard bindings, remaining segments, 404 vs 405
  (`cask-route-trie-validation-order`).

**I2. Absent, unknown and empty are distinct states; never collapse them.**

- `None` (cannot establish reusable completion) vs `Some(Array.emptyByteArray)` (boundary known, nothing buffered);
  `getOrElse(empty)` erases this (`http4s-http1-bodyless-connection-framing`).
- Play CORS: configuration `null` -> `Origins.All`; case-class default `Origins.None`; literal origin string `"null"`;
  list containing `*`. Four meanings (`play-cors-csrf-policy-matrix`).
- Play CSRF: absent `Cache-Control` returns `false` from historical shared-cache predicate; that is not proof response
  is uncacheable (`play-cors-csrf-policy-matrix`).
- ZIO HTTP: unmatched input vs selected handler's typed failure vs defect/interruption are distinct fallback
  categories (`zio-http-middleware-execution-boundaries`); `Invalid` never authorizes reuse
  (`zio-http-channel-handoff-completion`).
- http4s: encoded segment text vs decoded segment text vs whole path (`http4s-uri-segment-representation`).

**I3. No lossy conversion before the decision needing the lost information.**

- Cask PR 52: `values.map(_._2).flatten.toMap` dropped duplicate same-method registrations before trie validation;
  PR 70 keeps sequence, validates per method group, and calls `map(_.toMap)` only after construction
  (`cask-route-trie-validation-order`).
- http4s: decoding `/a%2Fb` to `/a/b` before splitting turns one segment into two
  (`http4s-uri-segment-representation`).
- ZIO HTTP #1916: `HandlerMiddleware` evaluates `route.run(in)` before applying aspect; transforming request first
  can turn unmatched input into match (`zio-http-middleware-execution-boundaries`).

**I4. Decide before effecting, and decide at the right scope.**

- Rejection branches before invoking protected handler; status-only rewrite after execution is not rejection
  (`zio-http-middleware-execution-boundaries`, #542).
- Path resolution precedes method resolution: no path -> 404, path without effective method -> 405 under Cask's
  default policy (`cask-route-trie-validation-order`).
- Ambiguity validation is method-scoped, not path-scoped (`cask-route-trie-validation-order`).
- Disclosure policy is request-local (FiberRef in #3050); global `Ref`, route-keyed map, or construction-time capture
  is not equivalent optimization (`zio-http-request-local-error-disclosure`).
- Play keeps CORS decision helper `private[play]` and deprecated `isCached` bridge forwarding to
  `isCacheableBySharedCache` (`play-cors-csrf-policy-matrix`).

**I5. Handoff only after previous owner can no longer act; cleanup must run even if consumer never pulls.**

- Reusable HTTP/1 connection starts next exchange at known message boundary and retains legitimate buffered
  next-message bytes. If alignment is unknown, retire connection; do not guess
  (`http4s-http1-bodyless-connection-framing`).
- #4348 moved processing from body-stream finalizer to enclosing response `Resource` release: body finalizer does not
  run for unconsumed body (`http4s-http1-bodyless-connection-framing`).
- ZIO HTTP #2924 order: remove reader -> publish completion (`onLastMessage`) -> deliver final body callback.
  #2610: prior-request damage is cleaned up or invalidated before return; external close is use-time failure that
  must settle pending waits (`zio-http-channel-handoff-completion`).
- Transferable rule: completion promise or pool return is permission for another borrower to act. Effect-runtime
  mechanics of finalizers and interruption belong to `scala-effect-cancellation-finalization`.

**I6. Oracles must be independent of implementation they check.**

- JSON error test interpolating same template as renderer (`zio-http-request-local-error-disclosure`).
- Play PR 8363: public-cache CSRF test was inverted to make parser patch pass; review restored it
  (`play-cors-csrf-policy-matrix`).
- Cask: trie construction tests are not lookup oracles (`cask-route-trie-validation-order`).
- Ember: #4348's two-response test is parser-level, not network test (`http4s-http1-bodyless-connection-framing`).
- URI: compare against literals, not another call to changed normalizer (`http4s-uri-segment-representation`).
- ZIO pool: repeated random traffic is supplemental, not deterministic ordering oracle
  (`zio-http-channel-handoff-completion`).

**I7. Intentional policy change is not regression, but must be declared.** Routing middleware (CORS OPTIONS,
trailing-slash normalization, allow/allowZIO, metrics) legitimately changes route sets. Application may normalize
`//` before its own lookup. Deployment may replace permissive CORS config. Ember may deliberately close after HEAD,
trading reuse for simpler framing. Domain endpoint may return documented public error body. Require old/new rows and
rationale; do not rubber-stamp, and do not reject.

## Routing table

| Change touches | Library / anchor files or APIs | Load |
|---|---|---|
| HEAD / status-implied no-body, `discardBody`, drain/remainder `Option[Array[Byte]]`, `ClientHelpers` reuse, response `Resource` release | http4s Ember (`ember-core` Parser, `ember-client` `ClientHelpers`) | [references/http4s-http1-bodyless-connection-framing.md](references/http4s-http1-bodyless-connection-framing.md) |
| `Uri.Path`, `Segment.apply` vs `Segment.encoded`, `normalize`, `pathInfo`/`scriptName`, String-to-Path equality, Path laws | http4s core `Uri.scala`, `PathSuite`, `UriSpec` | [references/http4s-uri-segment-representation.md](references/http4s-uri-segment-representation.md) |
| `Main.prepareDispatchTrie`, `DispatchTrie.construct`/`validateGroup`/`map`, `DefaultHandler` 404/405 | Cask | [references/cask-route-trie-validation-order.md](references/cask-route-trie-validation-order.md) |
| Netty client pool return/invalidation, `onComplete`/`onResponse`, close listener, `AsyncBodyReader.onLastMessage`, `ZClient` request-scope finalizer, retry schedule | ZIO HTTP JVM (`zio.http.netty.client`) | [references/zio-http-channel-handoff-completion.md](references/zio-http-channel-handoff-completion.md) |
| Middleware lifting, `HandlerMiddleware`, CSRF/guard rejection branch, composition/fallback (`Http.Empty`), before/after order | ZIO HTTP (`zhttp` 1.x, `zio.http` 2.x) | [references/zio-http-middleware-execution-boundaries.md](references/zio-http-middleware-execution-boundaries.md) |
| `Response.fromThrowable`/`fromCause`, error body/stack/depth/format config, debug middleware, FiberRef policy | ZIO HTTP `Response.scala`, `ResponseSpec` | [references/zio-http-request-local-error-disclosure.md](references/zio-http-request-local-error-disclosure.md) |
| `CORSConfig.allowedForOrigin`, `fromUnprefixedConfiguration`, preflight path, `CSRFActionHelper` / `isCacheableBySharedCache` | Play `play-filters-helpers` | [references/play-cors-csrf-policy-matrix.md](references/play-cors-csrf-policy-matrix.md) |

Change can match several rows (e.g. ZIO HTTP CSRF middleware that also renders errors): load each. Each case's
evidence is byte copy of its original audit record under `references/evidence/`.

## Workflow

1. **Classify intent.** Compatibility-preserving refactor, bug fix, or declared policy change (I7). For policy
   change, first collect old/new matrix rows and approval/migration note.
2. **Pin target.** Record versions and SHA (Prerequisites). Do not transplant historical API (`zhttp.HttpData`,
   CE2 `Resource` exit cases, `Http` vs `Routes`, Akka vs Pekko) into different line.
3. **Draw boundary path.** From producer to consumer: parse -> represent -> decide -> effect -> respond ->
   release/hand off. Mark every conversion (I3), every decision (I4) and every ownership transfer (I5).
4. **Build matrix.** Rows: input classes (method, status, framing, origin config, cache directive,
   matched/unmatched, accepted/rejected, typed failure/defect/interruption, concurrent opposite policies). Columns:
   observable dimensions from I1. Mark absent/unknown/empty as separate rows (I2). Fill "before" column from source
   and existing tests.
5. **Find first lossy or reordered step.** Compare "after" column. Defect, if any, is usually first point where
   later-needed information is discarded, decision moves after effect, or handoff precedes cleanup.
6. **Choose smallest correction at that boundary.** Restore ordering or representation; do not repair by collapsing
   states (`getOrElse(empty)`, first-wins `distinct`, catch-all fallback, process-wide flag, arbitrary sleep before
   scope exit, reading HEAD's Content-Length).
7. **Write discriminating tests (I6).** At least one row broken version fails and corrected version passes, plus
   legitimate counterexample row that must still pass (GET/POST at same path, `Some(empty)` reuse, CORS OPTIONS
   routing, public domain error body).
8. **Discover and, only if authorized, run real targets.** See Validation. Report unexecuted obligations.

## Review and Refactoring Checks

Transferable checks (any Scala HTTP library):

- [ ] Every observable dimension of touched branch asserted separately (I1); flag status-only tests.
- [ ] No three-valued state collapsed into two (I2); look for `getOrElse`, `toMap`, `distinct`, `orElse`, boolean
      predicates replacing `Option`.
- [ ] No conversion dropping multiplicity, boundaries, or encoding state precedes validation or decision needing it
      (I3).
- [ ] Rejection and selection happen before protected effects; each decision's scope (request, method group,
      selected handler) unchanged (I4).
- [ ] Reuse/handoff published only after previous owner's cleanup and only at known boundary; every terminal path
      (setup failure, remote close, interruption, never-pulled body) settles what it owns (I5).
- [ ] Review deleted or inverted assertions, not only added green tests (I6).
- [ ] Intentional behavior changes declared with old/new rows (I7).
- [ ] Equality changes keep symmetry and hash agreement; no `a.equals(b) != b.equals(a)` migration shim.
- [ ] Unrelated renames, abstraction experiments, Vary-header optimizations and effect-model changes kept out of
      semantic repair.

Library/version-specific checks (verify against target source first):

- [ ] Ember: `None` keeps `DontReuse`; `Some(bytes)` stores remainder before marking reuse; HEAD discard returns pure
      `None` without read in #7369; status-implied emptiness preserves `finalBuffer`.
- [ ] http4s URI: parsed text uses `Segment.encoded`, raw text uses `Segment.apply` (2020 snapshot names).
- [ ] Cask: sequence retained through `prepareDispatchTrie`; `construct(...)(_.map(_._1)).map(_.toMap)` ordering.
- [ ] ZIO HTTP pool: remove reader -> `onLastMessage` -> final callback; `Invalid` before intentional close; reset
      failure -> invalidation; WebSocket channels excluded from historical close listener.
- [ ] ZIO HTTP middleware: `HandlerMiddleware` applies after `route.run(in)` and preserves `Http.Empty`.
- [ ] ZIO HTTP errors: defaults disable generated body and stack; format Html; `fromCause` preserves existing
      `Response` and uses `prettyPrint` when body disclosure is enabled.
- [ ] Play: explicit-origin match before wildcard; All reflects only with credential support; public-cache GET adds
      no CSRF cookie; `Locale.ROOT` normalization; deprecated `isCached` bridge retained.

## Consolidated false positives

- `Some(empty)` after fully consumed response is safe to reuse; absence of buffered next bytes is not a defect.
  Explicit closure after HEAD is not evidence bytes were drained. Reviewer's security concern is not an exploit.
- `Segment.encoded` on previously parsed data is not injection defect; hash collisions between unequal paths do not
  break hash law.
- GET and POST on same Cask path are not duplicates; not every `.toMap` is the bug; deliberately concealed protected
  resource may intentionally not return 405; two annotations on one function is separate macro boundary.
- ZIO HTTP: `Invalid` published before intentional non-keepalive close is not reuse-before-close; open WebSocket is
  not evidence of HTTP request hang; do not demand single callback location without proving every failure reaches
  it. (Opposite error also common: assuming successful `isOpen` guarantees lifetime, or blaming lazy pool
  finalization, which adamgfraser explicitly corrected in #2610.)
- Public error bodies are allowed; #542 body-leak concern does not prohibit them. Author-reported test addition is
  weaker than retained oracle.
- Typed public error is not necessarily secret; reviewer's plaintext proposal is not final default (Html).
  Conversely, request-local storage is not authorization: client header enabling debug is unsafe without access
  control.
- ACAC `true` alongside ACAO `*` in Play's server test is not proof of browser credentialed access; conservative
  `Vary: Origin` on wildcard responses was accepted; deprecated forwarding method is not dead code; approved
  secure-policy migration may break legacy rows.

## Version fences

| Case | Historical anchor(s) | Fence |
|---|---|---|
| Ember framing | #4348 `32893c3` series/0.21: Scala 2.12.13/2.13.4, CE 2.3.1, FS2 2.5.0; #7369 `7e5a974`: Scala 2.12.18/2.13.12/3.3.1, CE 3.5.3, FS2 3.9.4 | CE2 vs CE3 `Resource` exit-case APIs; suite renamed (`ParsingSpec` -> class `ParsingSuite` in `ParserSuite.scala`) |
| URI segments | `7775249` (2020): Scala 2.12.12/2.13.3, CE 2.3.1, FS2 2.5.0 | Constructor names are observed historical APIs; calendar year does not identify release line |
| Cask routing | PR 52 `d7f7d55` (2021), PR 70 `e01c972` (2022), validation snapshot `d5fa6d4`: Scala 2.12.16/2.13.8/3.1.3, Mill 0.10.5, Undertow 2.2.18.Final, Java 8 CI | 2020 and late-2024 builds use different Scala/Mill layouts (`build.mill`); JVM-only server |
| ZIO HTTP pool | #2610: ZIO 2.0.19, Netty 4.1.101.Final, project `zioHttp`; #2924: ZIO 2.1.1, Netty 4.1.109.Final, project `zioHttpJVM` | Not ZIO 1 `zhttp.HttpData`; JVM Netty results do not carry to Scala.js/Native |
| ZIO HTTP middleware | #542: ZIO 1.0.13, package `zhttp`, project `zhttp`; #1916: ZIO 2.0.6, package `zio.http`, project `zioHttp` | `Http` vs modern `Routes`/handler aspects |
| ZIO HTTP errors | #3050 `ab9fdf7`: ZIO 2.1.8, Netty 4.1.112.Final, Scala 2.12.19/2.13.14/3.3.3; `ResponseSpec` JVM-only | #850 (2022) is earlier concern; successor #1024 unverified |
| Play filters | 2019/2020 Scala 2 + Akka (`Filters-Helpers`); Dec 2022 Akka 2.6.20; Dec 2024 Scala 2.13.15/3.3.4 + Pekko 1.0.3 (`Play-Filters-Helpers`) | Project IDs, integration config (`It` vs `Test`) and backend differ per era |

## Validation

Every command below is source-derived; rediscover it on target checkout.

1. Read build first (`build.sbt`, `project/*.scala`, `project/build.properties`, `build.sc`/`build.mill`,
   `.mill-version`, CI JDK settings) and suite's package declaration. Loading sbt or Mill build executes code, and
   Cask Mill wrapper may download an executable: get separate authorization and isolate checkout.
2. Discover before running: `sbt projects` then `sbt 'show <project> / Test / definedTests'`, or
   `./mill resolve '<module>.test'`. Require nonzero discovered tests. Trait (Play `CORSCommonSpec`) is not runnable
   suite: find its concrete consumers or run project's whole `test`.
3. Run narrowest discovered selector. Historical selectors per case live in each reference's Validation section.
4. Add matrix tests per Workflow. Where oracle is runtime ordering (pool handoff, never-pulled body, concurrent
   policies), use controlled barriers, overall deadline, and cleanup after failure. Observe connection or channel
   identity, close/reuse events, handler counts, and promise outcomes.
5. Isolate global state: Cask example fixtures both bind `localhost:8081` (serialize them); locale-sensitive Play tests
   restore default locale in `finally`.
6. Label evidence by layer: source observation, reviewer testimony, parser-/helper-level test, executed transport or
   browser evidence. Server headers are never browser or CDN proof.

## Examples

### Good

Cask cleanup keeps method entries as sequence until `DispatchTrie.construct` validates each method group, then maps
payloads to method maps. Its test pairs rejected duplicate-GET registration (through `prepareDispatchTrie`, asserting
diagnostic reason) with GET/POST reachability at same path, unknown-path 404, and DELETE-on-POST 405. Covers every I1
routing dimension; I7 counterexample still passes.

### Broken and Correction

ZIO HTTP CSRF refactor invokes application unconditionally, then overwrites status to Forbidden on token mismatch. It
renders exception into JSON by string interpolation. Status-only test passes. Correction: branch before invocation
(I4); assert zero protected-execution counter and absent body sentinel (I1). Render with build's real JSON encoder; in
test, parse output with quote/newline/control characters (I6). Keep disclosure policy request-local (I4). Load both
middleware and error-disclosure references.

### Negative

Ember change returns `Some(Array.emptyByteArray)` after fully consumed fixed-length body and marks connection reusable
while next exchange has not started. Do not flag it: boundary is known (I2), and #4348 explicitly distinguishes this
non-pipelined case. Likewise, Play deployment replacing null CORS config with explicit trusted list and documenting
newly rejected origins is declared migration (I7), not compatibility bug.

## Output Contract

For each finding return:

- `file:line`, severity, case reference(s) used, and invariant (I1-I7) violated.
- Exact matrix row(s) before and after: inputs and each observable dimension.
- Evidence: claim IDs from `references/evidence/<source-id>.json` and pinned source/PR URLs.
- Smallest correction at first lossy/reordered boundary, and one legitimate counterexample that must still pass.
- Discriminating test and oracle layer it reaches (parser/helper, in-process HTTP, socket, browser).
- Target version tuple, discovered selectors, commands actually executed with results, and explicit unexecuted
  obligations. Separate source observation, reviewer proposal, merged decision, and current-version inference.

Justified non-finding is valid: name guard, owner, or declared policy making suspicious change safe, and list matrix
rows still untested. Never turn structural pass into safety certification.

## Limitations

- Invariants synthesize seven historical cases; they are not maintainer-stated universal policy. Reviewer statements
  are attributed to their PRs. Merges without retrieved discussion (Cask PR 70, ZIO HTTP #2924's praise-only approval)
  are not design reviews.
- No upstream compilation, test execution, socket trace, race reproduction, browser probe or performance measurement
  performed. No current-version vulnerability or defect asserted.
- Not covered: HTTP/2, request smuggling, complete URI/RFC conformance, CSRF token strength, cookie policy, origin
  validation design, complete cache-directive grammar, WebSocket lifecycles, and Scala.js/Native transports.
- Several historical exemplars carry their own observed gaps (http4s 2020 `normalize` default flags, String split
  trailing-empty handling, Segment equality fallback; Cask shared-children lookup for mixed-method wildcard/subpath
  routes). These limit exemplars; they are not proven current defects.

## Sources

Per-case procedures, PR/commit permalinks and test oracles live in references; each links its evidence record:

- [http4s Ember HTTP/1 bodyless framing](references/http4s-http1-bodyless-connection-framing.md) -
  [evidence](references/evidence/scala-http4s-http1-bodyless-connection-framing.json) (`c-framing-connection-contract`, `c-drain-reuse-state`)
- [http4s URI segment representation](references/http4s-uri-segment-representation.md) -
  [evidence](references/evidence/scala-http4s-uri-segment-representation.json) (`c-uri-representation-laws`)
- [Cask route-trie validation order](references/cask-route-trie-validation-order.md) -
  [evidence](references/evidence/scala-cask-route-trie-validation-order.json)
- [ZIO HTTP channel handoff completion](references/zio-http-channel-handoff-completion.md) -
  [evidence](references/evidence/scala-zio-http-channel-handoff-completion.json) (`c-pool-handoff`, `c-pool-callback-order`)
- [ZIO HTTP middleware execution boundaries](references/zio-http-middleware-execution-boundaries.md) -
  [evidence](references/evidence/scala-zio-http-middleware-execution-boundaries.json) (`c-middleware-semantics`)
- [ZIO HTTP request-local error disclosure](references/zio-http-request-local-error-disclosure.md) -
  [evidence](references/evidence/scala-zio-http-request-local-error-disclosure.json) (`c-error-disclosure`)
- [Play CORS/CSRF policy matrix](references/play-cors-csrf-policy-matrix.md) -
  [evidence](references/evidence/scala-play-cors-csrf-policy-matrix.json) (`c-filter-defaults`, `c-filter-boundaries`, `c-filter-test-discovery`)
