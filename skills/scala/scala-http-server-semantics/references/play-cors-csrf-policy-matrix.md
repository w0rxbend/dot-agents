# Review Play filter policy with explicit matrices

> Library: Play (filters: CORS and CSRF). Formerly `scala-play-cors-csrf-policy-matrix` skill, merged into `scala-http-server-semantics`. Evidence: [evidence/scala-play-cors-csrf-policy-matrix.json](evidence/scala-play-cors-csrf-policy-matrix.json).

Green replacement test can hide security regression. Keep old negative cases; separate intentional policy migrations from compatibility repairs. Scope: Play's CORS origin-to-header decision and CSRF shared-cache/token predicate, not general HTTP security advice.

## When to Use

Changes to `CORSConfig.allowedForOrigin`, normal/preflight policy paths, `CSRFActionHelper` cache decisions, or their configuration readers and tests. Also helper extraction, visibility narrowing, public method renames, case-insensitive directive parsing.

## When Not to Use

Not for URI normalization, HTTP/1 framing, query binders, generic error rendering or cache TTL adapters. Explicitly authorized restriction of unsafe CORS policy is a migration, not automatically compatibility bug. Do not use this procedure to endorse historical permissive defaults for new deployments.

## Prerequisites

Identify Play, Scala/compiler/JDK versions, backend, exact source SHA; inspect real sbt project definitions and test consumers. Read configuration reader, not only case class: inspected 2020 source maps configuration `null` to `Origins.All`, while case-class default is `Origins.None`. Literal origin string `"null"` is a third input. Never collapse these meanings.

Use [policy matrices and version boundaries](#policy-matrices-and-historical-limits) and [evidence](evidence/scala-play-cors-csrf-policy-matrix.json). 2019/2020 implementation: Scala 2, Akka-era APIs. December 2024 build: different filter project IDs, Pekko. Validate current versions; do not transplant old selector or policy. Upstream builds/browser probes need separate authorization and isolated environment; none ran during this research.

## Workflow

1. **Classify intent and protected behavior.** State whether patch preserves compatibility or deliberately changes policy. Name consequence: user token shared through cache, credentialed cross-origin access widened, or existing applications unexpectedly denied. Intentional tightening needs migration note and explicit expected failures.
2. **Trace configuration to response headers.** Follow `fromUnprefixedConfiguration` → `Origins` → `allowedForOrigin` → both normal and preflight consumers. Build CORS matrix before editing: null-config/All; wildcard-only; specific match; wildcard plus matching or nonmatching specific origin; no match; credentials enabled/disabled. Record ACAO, ACAC, status, Vary independently. Returning 'allowed' is insufficient: reflection and `*` differ observably.
3. **Preserve matching precedence.** Historical helper: All reflects only with credential support; explicit match precedes wildcard fallback. Wildcard list does not become All merely because its predicate accepts `*`. Exercise both request paths; do not reimplement subtly different matchers in each.
4. **Trace the CSRF decision separately.** Hold token-creation eligibility constant, then vary absent Cache-Control, `public, max-age=3600`, `private`, `no-store`, `no-cache`, capitalization, whitespace. Keep public-cache GET negative assertion and historical absent-header branch. Then vary method and HTML acceptance with existing fixture. Do not infer that every response without the header is uncacheable, or that CSRF checks should be bypassed because token creation was suppressed.
5. **Normalize the intended grammar only.** Check locale-independent normalization (`Locale.ROOT`), comma splitting, trimming against observed directives. Do not turn small historical helper into claimed complete RFC parser. Parameterized directives, duplicate headers, intermediary behavior need separately established expectations.
6. **Refactor at the real boundary.** Keep decision helper `private[play]` if that suffices for existing callers. Keep public compatibility bridges such as deprecated `isCached` forwarding to `isCacheableBySharedCache`. Do not bundle Vary-header optimization with origin-matching repairs; if requested, prove its cache semantics separately.
7. **Compare old tests with new tests.** Review deleted assertions, not just added green cases. If public-cache test flipped from 'cookies empty' to 'cookies present', demand justified policy change, or restore assertion and repair implementation. Record which matrix rows patch actually covers.

## Review and Refactoring Checks

Invariant: unchanged policy gives same origin response, credential header, token creation and compatibility surface per matrix row. Explicit-origin priority and missing-value behavior must survive helper extraction. Historical public-cache GET fixture: no CSRF cookie must be added.

False positives: `Access-Control-Allow-Credentials: true` with ACAO `*` in historical server test does not prove browsers permit credentialed reads; do not invent such exploit from headers alone. Keeping `Vary: Origin` on wildcard response was accepted conservative behavior, not automatic bug. Deprecated public forwarding method is not dead code merely because internal callers moved. Intentional secure-policy migration may break legacy rows with explicit approval.

## Validation

Read `build.sbt` and CI before selecting suite. After separate build authorization, use `sbt 'projects'` and discovered project's `Test / definedTests`; require nonzero discovery. Concrete CSRF selector: inspected 2020/2022 layouts `sbt 'Filters-Helpers/testOnly play.filters.csrf.CSRFFilterSpec'`; December 2024 layout `sbt 'Play-Filters-Helpers/testOnly play.filters.csrf.CSRFFilterSpec'`, if that class still exists.

`CORSCommonSpec` is shared trait, not automatically runnable suite. Discover and run its concrete consumers, or use verified filter project's full `test` task. Cover normal/preflight cases, credentials on/off, specific-match precedence. Exercise locale-sensitive input in isolated test; if test changes default locale, restore it in `finally`. Do not race other suites through global locale mutation.

Compare actual ACAO/ACAC/Vary/status and token cookie outcomes, not only status. To claim browser enforcement, separately test allowed and disallowed origins with credential modes in current browser; distinguish request transmission from script access to response. Mark network/browser/deployment-cache coverage untested when not executed.

## Examples

### Good

Historical configuration `["*", "https://trusted.example"]`: matching trusted origin is reflected; other origin falls back to `*`. Credentials on/off are separate rows; preflight path is separate consumer. CSRF: keep 'public cache means no token cookie' while adding `private` and `NO-STORE ` rows. Follows accepted PR 10146 and PR 8363 implementation boundaries; not a recommendation to enable wildcard policy.

### Broken and Correction

Simplification merges null configuration and explicit wildcard list into one allow-all value, always reflecting origin when credentials are enabled. Erases distinction PR 10146 explicitly preserved. Correction: return precise ACAO decision from scoped helper; restore explicit-match-before-wildcard precedence. Separately, if directive-parser patch flips public-cache assertion to allow cookies, restore negative test and correct parsing/default handling; do not redefine success.

### Negative

Approved deployment migration replaces permissive null configuration with explicit trusted-origin list, documents newly rejected origins. Do not reject it for violating historical compatibility; check its stated new matrix instead. Pure predicate rename keeping public forwarding method and unchanged rows also needs no semantic-defect finding. Cache expiration units and query-component encoding belong to other procedures.

## Output Contract

Per finding: `file:line`, severity, exact before/after matrix row, threat or compatibility consequence, evidence ID, current-source evidence, minimal correction, discriminating test. Separate historical observation from current-version inference. Report covered and missing rows plus execution mode; explicit no-finding is valid when behavior is preserved. Never label server-header test as browser or CDN security proof.

## Limitations

Historical rules cover examined Play filter behavior, not every cache directive, malformed origin, policy combination or intermediary. Preserved defaults can be unsafe deployment choices. Original synthesis of short attributed review excerpts and pinned code/tests; reviewer ranks unknown. No upstream compilation, browser probe or behavioral effectiveness study ran during authoring.

## Policy matrices and historical limits

### CORS: observed 2020 decision, not a deployment recommendation

At [43d1852](https://github.com/playframework/playframework/blob/43d1852a1cfe3ec2d827659b343cdaf5fb739223/web/play-filters-helpers/src/main/scala/play/filters/cors/CORSConfig.scala#L63-L69), `allowedForOrigin` returns exact ACAO value or None. For cross-origin requests passing other policy checks:

| Configuration representation | credentials supported | Request-origin match | ACAO decision |
|---|---|---|---|
| config null → Origins.All | true | any | reflect origin |
| config null → Origins.All | false | any | `*` |
| explicit origins list | either | specific origin matches | reflect origin |
| list containing `*` | either | no specific origin matches | `*` |
| list without matching origin or `*` | either | none | None |

`Origins.None` is nonmatching predicate; case-class constructor default is not configuration-file null default. Missing application override may inherit reference configuration; missing merged configuration is not automatically same as explicit null. Serialized origin string `"null"` is not config null; do not casually add it to an allowlist.

[Server tests](https://github.com/playframework/playframework/blob/43d1852a1cfe3ec2d827659b343cdaf5fb739223/web/play-filters-helpers/src/test/scala/play/filters/cors/CORSCommonSpec.scala#L406-L448) explicitly show ACAC true with wildcard ACAO and specific-match reflection. Do not rewrite observed headers in prose to fit an assumed 'cleaner' implementation. Do not equate permitted request, browser-sent request and script-exposed response.

Record Vary separately. [gmethvin declined](https://github.com/playframework/playframework/pull/10146#discussion_r403435387) special-casing uniform wildcard Vary in this semantic change; not a general ban on measured cache optimization. Test OPTIONS preflight and ordinary requests separately, plus fixture's non-CORS/same-origin pass-through controls.

### CSRF: observed 2019 shared-cache predicate

Hold token-creation eligibility constant (existing HTML-accepting GET fixture, no token). [Helper](https://github.com/playframework/playframework/blob/fa51a161b3948bfa53422a9b0dea6a6521f982f6/web/play-filters-helpers/src/main/scala/play/filters/csrf/CSRFActions.scala#L541-L558) normalizes with Locale.ROOT, splits commas, trims, returns false for absent header.

| Cache-Control input | Historical shared-cache predicate | Fixture's token-cookie outcome |
|---|---|---|
| absent | false | cookie added |
| `public, max-age=3600` | true | no cookie |
| `private` | false | cookie added |
| `no-store` | false | cookie added |
| `no-cache` | false | cookie added |
| `PRIVATE ` / `NO-STORE ` | false | same as normalized directive |
| `must-revalidate, private` | false | cookie added |

Predicate is library heuristic, not complete CDN/browser caching model. Do not infer absent Cache-Control prevents caching, or that `no-cache` literally means response can never be stored. New hardening expectations need current standards and deployment checks, not invented historical fix.

[Tests](https://github.com/playframework/playframework/blob/fa51a161b3948bfa53422a9b0dea6a6521f982f6/web/play-filters-helpers/src/test/scala/play/filters/csrf/CSRFFilterSpec.scala#L39-L110) also distinguish POST/PUT/DELETE and HTML acceptance and include HEAD-positive cases: do not turn a named 'non GET' test into claim that all non-GET requests can never obtain tokens. Keep creation/check distinctions and existing-token behavior.

### Review disposition and false positives

PR 8363's author implemented initial parser suggestions; later review caught inverted security assertion and flipped missing-header default. mkurz revised implementation/tests, kept renamed method's deprecated bridge. Concrete case of correcting behavior instead of weakening regression oracle.

PR 10146's author first asked why null and wildcard should differ; gmethvin explained credential distinction, helper was corrected, final code kept `private[play]`. This private scope does not justify hiding unrelated documented extension points.

Dedicated hardening migration may change these matrices deliberately. Require declared old/new rows plus compatibility/security rationale; do not preserve unsafe configuration only to imitate history. Unrelated cache-TTL adapter discussion is no filter-policy implementation precedent.

### Build discovery and versions

2020/2022 build ID is `Filters-Helpers`; 2024 ID is `Play-Filters-Helpers`. `CSRFFilterSpec` is concrete. Integration uses `It` in 2020/2022, `Test` in December 2024. Inspect backend naming.

December 2020 build imports Interplay 3.0.0; pinned [version constants](https://github.com/playframework/interplay/blob/07d559a14272b42bab5ce33929d28cdedeabedcf/src/main/scala/interplay/Versions.scala) and [library plugin](https://github.com/playframework/interplay/blob/07d559a14272b42bab5ce33929d28cdedeabedcf/src/main/scala/interplay/PlayLibraryBase.scala#L22-L30) set default Scala 2.13.1 plus 2.12.10 cross-build, subject to `scala.version` overrides. sbt 1.4.6; Play targets JVM 1.8; CI includes Java 11/8. Snapshot defaults, not asserted PR-head versions.

December 2022 Interplay 3.1.0-RC6 [plugin](https://github.com/playframework/interplay/blob/c708b2975edb7d9360d5dec76e28aabc69e2d7b8/src/main/scala/interplay/PlayLibraryBase.scala#L23-L34) defaults runtime to 2.13.10, with only selected version in crossScalaVersions. Separately selectable 3.2.1-RC4 does not prove full runtime-test support. sbt 1.7.2, release 11, Java 11/17 CI are distinct from Scala 2.12.17 meta-build.

December 2024: Scala 2.13.15/3.3.4, sbt 1.10.6, release 17, Java 17/21 CI. Backend dependency defaults moved from Akka 2.6.10/HTTP 10.1.13 (2020) through Akka 2.6.20/HTTP 10.2.10 (2022) to Pekko 1.0.3/HTTP 1.0.1 (2024). Keep target's Future/stream APIs; no CE/ZIO/Ox conversion follows from these rules.

All build statements come from source inspection; no upstream build, browser or CDN test ran during authoring.

## Sources

[Evidence records and claims](evidence/scala-play-cors-csrf-policy-matrix.json) resolve `c-filter-defaults`, `c-filter-boundaries` and build discovery. See [inverted CSRF test caught in review](https://github.com/playframework/playframework/pull/8363#discussion_r321166635), [absent-header compatibility decision](https://github.com/playframework/playframework/pull/8363#discussion_r322029941), [CORS null versus wildcard](https://github.com/playframework/playframework/pull/10146#discussion_r400447026), [scoped helper guidance](https://github.com/playframework/playframework/pull/10146#discussion_r399911912), and [pinned CORS decision implementation](https://github.com/playframework/playframework/blob/43d1852a1cfe3ec2d827659b343cdaf5fb739223/web/play-filters-helpers/src/main/scala/play/filters/cors/CORSConfig.scala#L63-L69).
