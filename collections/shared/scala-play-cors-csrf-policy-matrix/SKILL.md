---
name: scala-play-cors-csrf-policy-matrix
description: Use when reviewing or hardening Play CORS origin matching or CSRF token/cache decisions. Build explicit missing-value, wildcard, credential and shared-cache matrices before changing behavior or regression tests.
license: MIT
---

# Review Play filter policy with explicit matrices

A green replacement test can hide a security regression. Preserve the old negative cases and distinguish intentional policy migrations from compatibility repairs. This skill is specific to Play's CORS origin-to-header decision and CSRF shared-cache/token predicate, not general HTTP security advice.

## When to Use

Use when changing `CORSConfig.allowedForOrigin`, normal/preflight policy paths, `CSRFActionHelper` cache decisions, or their configuration readers and tests. Also use when extracting these helpers, narrowing visibility, renaming public methods, or making directive parsing case-insensitive.

## When Not to Use

Do not use for URI normalization, HTTP/1 framing, query binders, generic error rendering or cache TTL adapters. An explicitly authorized restriction of unsafe CORS policy is a migration, not automatically a compatibility bug. Do not use this procedure to endorse historical permissive defaults for a new deployment.

## Prerequisites

Identify Play, Scala/compiler/JDK versions, backend and exact source SHA; inspect the real sbt project definitions and test consumers. Read the configuration reader as well as the case class: in the inspected 2020 source, configuration `null` becomes `Origins.All`, while the case-class default is `Origins.None`. The literal origin string `"null"` is yet another input. Never collapse these meanings.

Use [policy matrices and version boundaries](references/policy-matrices.md) and [evidence](references/evidence.json). The 2019/2020 implementation uses Scala 2 and Akka-era APIs. The December 2024 build uses different filter project IDs and Pekko; validate current versions rather than transplanting the old selector or policy. Upstream builds/browser probes require separate authorization and an isolated environment; none ran during this research.

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

## Sources

[Evidence records and claims](references/evidence.json) resolve `c-filter-defaults`, `c-filter-boundaries` and build discovery. See [the inverted CSRF test caught in review](https://github.com/playframework/playframework/pull/8363#discussion_r321166635), [the absent-header compatibility decision](https://github.com/playframework/playframework/pull/8363#discussion_r322029941), [CORS null versus wildcard](https://github.com/playframework/playframework/pull/10146#discussion_r400447026), [scoped helper guidance](https://github.com/playframework/playframework/pull/10146#discussion_r399911912), and [the pinned CORS decision implementation](https://github.com/playframework/playframework/blob/43d1852a1cfe3ec2d827659b343cdaf5fb739223/web/play-filters-helpers/src/main/scala/play/filters/cors/CORSConfig.scala#L63-L69).
