# Policy matrices and historical limits

## CORS: observed 2020 decision, not a deployment recommendation

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

## CSRF: observed 2019 shared-cache predicate

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

## Review disposition and false positives

PR 8363's author implemented initial parser suggestions; later review found an inverted security assertion and a flipped missing-header default. mkurz revised the implementation/tests and retained the renamed method's deprecated bridge. This is a concrete example of correcting behavior rather than weakening a regression oracle.

PR 10146's author initially questioned why null and wildcard should differ; gmethvin explained the credential distinction, the helper was corrected, and final code kept `private[play]`. This private scope does not justify hiding unrelated documented extension points.

A dedicated hardening migration may change these matrices deliberately. Require declared old/new rows and a compatibility/security rationale; do not preserve unsafe configuration just to imitate history. Conversely, an unrelated cache-TTL adapter discussion is not a filter-policy implementation precedent.

## Build discovery and versions

The 2020/2022 build ID is `Filters-Helpers`; the 2024 ID is `Play-Filters-Helpers`. `CORSCommonSpec` is a trait: discover concrete consumers, or run the filter project's entire `test` task rather than claiming a trait selector executed tests. `CSRFFilterSpec` is concrete. Integration uses `It` in 2020/2022 and `Test` in December 2024. Require nonzero relevant tests and inspect backend naming.

The December 2020 build imports Interplay 3.0.0; its pinned [version constants](https://github.com/playframework/interplay/blob/07d559a14272b42bab5ce33929d28cdedeabedcf/src/main/scala/interplay/Versions.scala) and [library plugin](https://github.com/playframework/interplay/blob/07d559a14272b42bab5ce33929d28cdedeabedcf/src/main/scala/interplay/PlayLibraryBase.scala#L22-L30) establish default Scala 2.13.1 plus 2.12.10 cross-build, subject to `scala.version` overrides. sbt is 1.4.6; Play targets JVM 1.8 and CI includes Java 11/8. These are snapshot defaults, not asserted PR-head versions.

The December 2022 Interplay 3.1.0-RC6 [plugin](https://github.com/playframework/interplay/blob/c708b2975edb7d9360d5dec76e28aabc69e2d7b8/src/main/scala/interplay/PlayLibraryBase.scala#L23-L34) defaults runtime to 2.13.10, with only the selected version in crossScalaVersions. The separately selectable 3.2.1-RC4 is not proof of full runtime-test support. sbt 1.7.2, release 11 and Java 11/17 CI are distinct from the Scala 2.12.17 meta-build.

December 2024 declares Scala 2.13.15/3.3.4, sbt 1.10.6, release 17 and Java 17/21 CI. The backend dependency defaults changed from Akka 2.6.10/HTTP 10.1.13 (2020), through Akka 2.6.20/HTTP 10.2.10 (2022), to Pekko 1.0.3/HTTP 1.0.1 (2024). Preserve the target's Future/stream APIs; no CE/ZIO/Ox conversion follows from these rules.

All build statements are source inspection. No upstream build, browser or CDN test was executed during authoring.
