# Review Play filter policy with explicit matrices

> Library: Play (filters: CORS and CSRF). Originally the `scala-play-cors-csrf-policy-matrix` skill; merged into `scala-http-server-semantics`. Evidence: [evidence/scala-play-cors-csrf-policy-matrix.json](evidence/scala-play-cors-csrf-policy-matrix.json).

A green replacement test can hide a security regression. Preserve the old negative cases and distinguish intentional policy migrations from compatibility repairs. This case is specific to Play's CORS origin-to-header decision and CSRF shared-cache/token predicate, not general HTTP security advice.

## When to Use

Use when changing `CORSConfig.allowedForOrigin`, normal/preflight policy paths, `CSRFActionHelper` cache decisions, or their configuration readers and tests. Also use when extracting these helpers, narrowing visibility, renaming public methods, or making directive parsing case-insensitive.

## When Not to Use

Do not use for URI normalization, HTTP/1 framing, query binders, generic error rendering or cache TTL adapters. An explicitly authorized restriction of unsafe CORS policy is a migration, not automatically a compatibility bug. Do not use this procedure to endorse historical permissive defaults for a new deployment.

## Prerequisites

Identify Play, Scala/compiler/JDK versions, backend and exact source SHA; inspect the real sbt project definitions and test consumers. Read the configuration reader as well as the case class: in the inspected 2020 source, configuration `null` becomes `Origins.All`, while the case-class default is `Origins.None`. The literal origin string `"null"` is yet another input. Never collapse these meanings.

Use [policy matrices and version boundaries](#policy-matrices-and-historical-limits) and [evidence](evidence/scala-play-cors-csrf-policy-matrix.json). The 2019/2020 implementation uses Scala 2 and Akka-era APIs. The December 2024 build uses different filter project IDs and Pekko; validate current versions rather than transplanting the old selector or policy. Upstream builds/browser probes require separate authorization and an isolated environment; none ran during this research.

## Workflow

1. **Classify intent and protected behavior.** State whether the patch preserves compatibility or deliberately changes policy. Identify the consequence: sharing a user token through a cache, expanding credentialed cross-origin access, or unexpectedly denying existing applications. Require a migration note and explicit expected failures for intentional tightening.
2. **Trace configuration to response headers.** Follow `fromUnprefixedConfiguration` → `Origins` → `allowedForOrigin` → both normal and preflight consumers. Build the CORS matrix before editing: null-config/All; wildcard-only; specific match; wildcard plus matching or nonmatching specific origin; no match; credentials enabled/disabled. Record ACAO, ACAC, status and Vary independently. Returning 'allowed' is insufficient because reflection and `*` are observably different.
3. **Preserve matching precedence.** In the historical helper, All reflects only with credential support; an explicit match precedes wildcard fallback. A wildcard list does not become All simply because its predicate accepts `*`. Exercise both request paths and avoid reimplementing subtly different matchers in each.
4. **Trace the CSRF decision separately.** Hold token-creation eligibility constant first, then vary absent Cache-Control, `public, max-age=3600`, `private`, `no-store`, `no-cache`, capitalization and whitespace. Preserve the public-cache GET negative assertion and the historical absent-header branch. Then vary method and HTML acceptance using the existing fixture. Do not infer that every response without a header is really uncacheable, or that CSRF checks should be bypassed because token creation was suppressed.
5. **Normalize the intended grammar only.** Check locale-independent normalization (`Locale.ROOT`), comma splitting and trimming against observed directives. Do not turn the small historical helper into a claimed complete RFC parser. Parameterized directives, duplicate headers and intermediary behavior need separately established expectations.
6. **Refactor at the real boundary.** Keep the decision helper `private[play]` if that is sufficient for existing callers. Preserve public compatibility bridges such as deprecated `isCached` forwarding to `isCacheableBySharedCache`. Do not bundle Vary-header optimization with origin-matching repairs: prove its cache semantics separately if requested.
7. **Compare old tests with new tests.** Review deleted assertions, not just added green cases. If a public-cache test was changed from 'cookies empty' to 'cookies present', demand a justified policy change or restore the assertion and repair the implementation. Record which matrix rows the patch actually adds coverage for.

## Review and Refactoring Checks

Preserve the invariant that an unchanged policy yields the same origin response, credential header, token creation and compatibility surface for each matrix row. Explicit-origin priority and missing-value behavior must survive helper extraction. For the historical public-cache GET fixture, no CSRF cookie must be added.

False positives: `Access-Control-Allow-Credentials: true` alongside ACAO `*` in the historical server test is not proof that a browser permits credentialed reads; do not invent such an exploit from headers alone. Keeping `Vary: Origin` for a wildcard response was accepted conservative behavior, not an automatic bug. A deprecated public forwarding method is not dead code merely because internal callers moved. An intentional secure-policy migration may break legacy rows with explicit approval.

## Validation

Read `build.sbt` and CI before selecting the suite; after separate build authorization use `sbt 'projects'` and the discovered project's `Test / definedTests` to require nonzero discovery. At the inspected 2020/2022 layouts the concrete CSRF selector is `sbt 'Filters-Helpers/testOnly play.filters.csrf.CSRFFilterSpec'`; at the December 2024 layout it is `sbt 'Play-Filters-Helpers/testOnly play.filters.csrf.CSRFFilterSpec'`, conditional on that class still existing.

`CORSCommonSpec` is a shared trait, not automatically a runnable suite. Discover its concrete consumers and run them, or use the verified filter project's full `test` task. Include normal/preflight cases, credentials on/off and specific-match precedence. Exercise locale-sensitive input in an isolated test and restore the default locale in `finally` if the test changes it; do not race other suites through a global locale mutation.

Compare actual ACAO/ACAC/Vary/status and token cookie outcomes, not only status. If claiming browser enforcement, separately test allowed and disallowed origins with credential modes in a current browser and distinguish request transmission from script access to the response. Server-side assertions alone cannot establish browser enforcement. Mark network/browser/deployment-cache coverage untested when not executed.

## Examples

### Good

For historical configuration `["*", "https://trusted.example"]`, the matching trusted origin is reflected; a different origin falls back to `*`. Keep credentials on/off as separate rows and the preflight path as a separate consumer. For CSRF, retain 'public cache means no token cookie' while adding `private` and `NO-STORE ` rows. This follows the accepted PR 10146 and PR 8363 implementation boundaries, not a recommendation to enable wildcard policy.

### Broken and Correction

A simplification treats null configuration and an explicit wildcard list as one allow-all value, always reflecting the origin when credentials are enabled. It erases the distinction explicitly preserved in PR 10146. Correction: return the precise ACAO decision from the scoped helper and restore explicit-match-before-wildcard precedence. Separately, if a directive-parser patch flips the public-cache assertion to allow cookies, restore the negative test and correct parsing/default handling rather than redefining success.

### Negative

An approved deployment migration replaces permissive null configuration with an explicit trusted-origin list and documents newly rejected origins. Do not reject it for violating historical compatibility; check its stated new matrix instead. A pure predicate rename retaining the public forwarding method and unchanged rows also needs no semantic-defect finding. Cache expiration units and query-component encoding belong to different procedures.

## Output Contract

Return each finding with `file:line`, severity, exact before/after matrix row, threat or compatibility consequence, evidence ID, current-source evidence, minimal correction and discriminating test. Separate historical observation from current-version inference. Report covered and missing rows plus execution mode; an explicit no-finding is valid when behavior is preserved. Never label a server-header test as a browser or CDN security proof.

## Limitations

Historical rules cover the examined Play filter behavior, not every cache directive, malformed origin, policy combination or intermediary. Preserved defaults can be unsafe deployment choices. This is original synthesis of short attributed review excerpts and pinned code/tests; reviewer ranks remain unknown. No upstream compilation, browser probe or behavioral effectiveness study was performed during authoring.

## Policy matrices and historical limits

### CORS: observed 2020 decision, not a deployment recommendation

At [43d1852](https://github.com/playframework/playframework/blob/43d1852a1cfe3ec2d827659b343cdaf5fb739223/web/play-filters-helpers/src/main/scala/play/filters/cors/CORSConfig.scala#L63-L69), `allowedForOrigin` returns the exact ACAO value or None. For cross-origin requests that pass the other policy checks:

| Configuration representation | credentials supported | Request-origin match | ACAO decision |
|---|---|---|---|
| config null → Origins.All | true | any | reflect origin |
| config null → Origins.All | false | any | `*` |
| explicit origins list | either | specific origin matches | reflect origin |
| list containing `*` | either | no specific origin matches | `*` |
| list without matching origin or `*` | either | none | None |

A list containing both `*` and a specific origin uses specific match first. `Origins.None` is a nonmatching predicate; the case-class constructor's default is not the configuration-file null default. Missing application override may inherit reference configuration; missing merged configuration is not automatically the same as an explicit null. The serialized origin string `"null"` is not config null and should not be added casually to an allowlist.

The [server tests](https://github.com/playframework/playframework/blob/43d1852a1cfe3ec2d827659b343cdaf5fb739223/web/play-filters-helpers/src/test/scala/play/filters/cors/CORSCommonSpec.scala#L406-L448) explicitly show ACAC true alongside wildcard ACAO and specific-match reflection. Do not rewrite the observed headers in prose to match an assumed 'cleaner' implementation. Browser behavior is a separate assertion: these tests do not demonstrate credentialed access through a wildcard. Do not equate a permitted request, a request sent by a browser and a response exposed to script.

Record Vary separately. [gmethvin declined](https://github.com/playframework/playframework/pull/10146#discussion_r403435387) special-casing uniform wildcard Vary in this semantic change; it was not a general ban on measured cache optimization. Test OPTIONS preflight and ordinary requests separately, plus the fixture's non-CORS/same-origin pass-through controls.

### CSRF: observed 2019 shared-cache predicate

Hold token-creation eligibility constant (the existing HTML-accepting GET fixture with no token). The [helper](https://github.com/playframework/playframework/blob/fa51a161b3948bfa53422a9b0dea6a6521f982f6/web/play-filters-helpers/src/main/scala/play/filters/csrf/CSRFActions.scala#L541-L558) normalizes with Locale.ROOT, splits commas, trims and returns false for an absent header.

| Cache-Control input | Historical shared-cache predicate | Fixture's token-cookie outcome |
|---|---|---|
| absent | false | cookie added |
| `public, max-age=3600` | true | no cookie |
| `private` | false | cookie added |
| `no-store` | false | cookie added |
| `no-cache` | false | cookie added |
| `PRIVATE ` / `NO-STORE ` | false | same as normalized directive |
| `must-revalidate, private` | false | cookie added |

The predicate is a library heuristic, not a complete model of CDN/browser caching. In particular, do not infer that absent Cache-Control prevents caching or that `no-cache` literally means a response can never be stored. Parameterized directives and duplicate headers are outside these demonstrated rows. New hardening expectations require current standards and deployment checks, not an invented historical fix.

The [tests](https://github.com/playframework/playframework/blob/fa51a161b3948bfa53422a9b0dea6a6521f982f6/web/play-filters-helpers/src/test/scala/play/filters/csrf/CSRFFilterSpec.scala#L39-L110) also distinguish POST/PUT/DELETE and HTML acceptance; they include HEAD-positive cases, so do not turn a named 'non GET' test into a claim that all non-GET requests can never obtain tokens. Preserve creation/check distinctions and existing-token behavior.

### Review disposition and false positives

PR 8363's author implemented initial parser suggestions; later review found an inverted security assertion and a flipped missing-header default. mkurz revised the implementation/tests and retained the renamed method's deprecated bridge. This is a concrete example of correcting behavior rather than weakening a regression oracle.

PR 10146's author initially questioned why null and wildcard should differ; gmethvin explained the credential distinction, the helper was corrected, and final code kept `private[play]`. This private scope does not justify hiding unrelated documented extension points.

A dedicated hardening migration may change these matrices deliberately. Require declared old/new rows and a compatibility/security rationale; do not preserve unsafe configuration just to imitate history. Conversely, an unrelated cache-TTL adapter discussion is not a filter-policy implementation precedent.

### Build discovery and versions

The 2020/2022 build ID is `Filters-Helpers`; the 2024 ID is `Play-Filters-Helpers`. `CORSCommonSpec` is a trait: discover concrete consumers, or run the filter project's entire `test` task rather than claiming a trait selector executed tests. `CSRFFilterSpec` is concrete. Integration uses `It` in 2020/2022 and `Test` in December 2024. Require nonzero relevant tests and inspect backend naming.

The December 2020 build imports Interplay 3.0.0; its pinned [version constants](https://github.com/playframework/interplay/blob/07d559a14272b42bab5ce33929d28cdedeabedcf/src/main/scala/interplay/Versions.scala) and [library plugin](https://github.com/playframework/interplay/blob/07d559a14272b42bab5ce33929d28cdedeabedcf/src/main/scala/interplay/PlayLibraryBase.scala#L22-L30) establish default Scala 2.13.1 plus 2.12.10 cross-build, subject to `scala.version` overrides. sbt is 1.4.6; Play targets JVM 1.8 and CI includes Java 11/8. These are snapshot defaults, not asserted PR-head versions.

The December 2022 Interplay 3.1.0-RC6 [plugin](https://github.com/playframework/interplay/blob/c708b2975edb7d9360d5dec76e28aabc69e2d7b8/src/main/scala/interplay/PlayLibraryBase.scala#L23-L34) defaults runtime to 2.13.10, with only the selected version in crossScalaVersions. The separately selectable 3.2.1-RC4 is not proof of full runtime-test support. sbt 1.7.2, release 11 and Java 11/17 CI are distinct from the Scala 2.12.17 meta-build.

December 2024 declares Scala 2.13.15/3.3.4, sbt 1.10.6, release 17 and Java 17/21 CI. The backend dependency defaults changed from Akka 2.6.10/HTTP 10.1.13 (2020), through Akka 2.6.20/HTTP 10.2.10 (2022), to Pekko 1.0.3/HTTP 1.0.1 (2024). Preserve the target's Future/stream APIs; no CE/ZIO/Ox conversion follows from these rules.

All build statements are source inspection. No upstream build, browser or CDN test was executed during authoring.

## Sources

[Evidence records and claims](evidence/scala-play-cors-csrf-policy-matrix.json) resolve `c-filter-defaults`, `c-filter-boundaries` and build discovery. See [the inverted CSRF test caught in review](https://github.com/playframework/playframework/pull/8363#discussion_r321166635), [the absent-header compatibility decision](https://github.com/playframework/playframework/pull/8363#discussion_r322029941), [CORS null versus wildcard](https://github.com/playframework/playframework/pull/10146#discussion_r400447026), [scoped helper guidance](https://github.com/playframework/playframework/pull/10146#discussion_r399911912), and [the pinned CORS decision implementation](https://github.com/playframework/playframework/blob/43d1852a1cfe3ec2d827659b343cdaf5fb739223/web/play-filters-helpers/src/main/scala/play/filters/cors/CORSConfig.scala#L63-L69).
