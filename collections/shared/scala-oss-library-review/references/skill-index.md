# Routing index

Generated from the promotion ledger; do not edit by hand. Pick the narrowest skill whose
trigger matches the code under change. Several may apply to one PR.

## Development

| Skill | Repository | Use when |
| --- | --- | --- |
| `scala-ammonite-static-script-dependency-propagation` | com-lihaoyi/Ammonite | Use when adding Ammonite import-hook metadata or refactoring BSP script dependency resolution. |
| `scala-cats-law-backed-instance-surface` | typelevel/cats | Use when adding Cats algebra instances, derived typeclass operations, or public implicit construction helpers. |
| `scala-fs2-sink-emission-cardinality` | typelevel/fs2 | Use when changing an FS2 sink result type or sequencing after a draining pipe. |
| `scala-http4s-uri-segment-representation` | http4s/http4s | Use when changing http4s URI path encoding, segment constructors, normalization, or String-to-Path equality. |

## Review

| Skill | Repository | Use when |
| --- | --- | --- |
| `scala-cats-effect-outcome-sensitive-concurrency` | typelevel/cats-effect | Use when reviewing Cats Effect race, memoize, or Fiber.cancel refactors that change cancellation outcomes, waiter cleanup, or startup behavior. |
| `scala-cats-effect-runtime-benchmark-review` | typelevel/cats-effect | Use when reviewing Cats Effect scheduler placement or runtime array-copy optimizations whose benchmarks may exercise the wrong path, callback origin, or representation. |
| `scala-cats-erased-runtime-compatibility` | typelevel/cats | Use when reviewing Cats erased generic signature changes or new cached instances in inherited Scala 2 traits. |
| `scala-fastparse-diagnostic-mode-review` | com-lihaoyi/fastparse | Use when changing Fastparse Fail labels, verbose failure reporting, or failure trace replay. |
| `scala-fastparse-hot-path-cost-review` | com-lihaoyi/fastparse | Use when reviewing allocation, closure or bytecode-size changes in Fastparse ParsingRun helpers, inline/macro combinators, or diagnostic-message construction. |
| `scala-fs2-per-element-scope-propagation` | typelevel/fs2 | Use when reviewing FS2 scope propagation across prefetch, channels or parEvalMap. |
| `scala-sourcecode-args-capture-review` | com-lihaoyi/sourcecode | Use when reviewing sourcecode.Args macro changes. |
| `scala-zio-diagnostic-reader-progress` | zio/zio | Use when changing ZIO fiber diagnostic reads. |

## Refactoring

| Skill | Repository | Use when |
| --- | --- | --- |
| `scala-acyclic-whole-run-compiler-adapters` | com-lihaoyi/acyclic | Use when refactoring Acyclic compiler adapters. |
| `scala-ammonite-symbol-derived-closure-capture` | com-lihaoyi/Ammonite | Use when refactoring Ammonite REPL class wrappers, used-command tracking, or serialized closure capture. |
| `scala-cask-route-trie-validation-order` | com-lihaoyi/cask | Use when refactoring Cask route-trie construction, method maps, duplicate-route validation, or default 404/405 dispatch. |
| `scala-castor-platform-mixin-dispatch-accounting` | com-lihaoyi/castor | Use when refactoring Castor Context platform mixins or reviewing their inherited JVM/JS/Native API boundary. |
| `scala-cats-traversal-branch-isolation` | typelevel/cats | Use when optimizing Cats Traverse or mapAccumulate with builders, strict-map helpers, or runtime-selected fast paths. |
| `scala-fastparse-shared-run-combinator-extraction` | com-lihaoyi/fastparse | Use when refactoring Fastparse higher-order parsers, sequence or repetition macros, or reusable whitespace cuts. |
| `scala-fs2-foreign-callback-lanes` | typelevel/fs2 | Use when refactoring FS2 foreign request/cancel callbacks or restartable server streams. |
| `scala-http4s-stateful-factory-acquisition` | http4s/http4s | Use when refactoring http4s stateful middleware factories or their nonce and token-bucket tests. |
| `scala-play-partial-startup-shutdown-completion` | playframework/playframework | Use when refactoring Play ApplicationLifecycle, development startup hooks, or coordinated server shutdown. |
| `scala-zio-canceler-evaluation-owner` | zio/zio | Use when refactoring ZIO cancel-token bridges. |
| `scala-zio-http-middleware-execution-boundaries` | zio/zio-http | Use when refactoring ZIO HTTP middleware placement. |

## Hardening

| Skill | Repository | Use when |
| --- | --- | --- |
| `scala-cats-effect-cleanup-error-provenance` | typelevel/cats-effect | Use when hardening Cats Effect IO cleanup-error handling that combines use, release, cancellation, or parallel failures and may mutate or hide exceptions. |
| `scala-http4s-http1-bodyless-connection-framing` | http4s/http4s | Use when changing http4s Ember HTTP/1 HEAD handling, drain metadata, response remainders, or connection reuse. |
| `scala-play-cors-csrf-policy-matrix` | playframework/playframework | Use when reviewing or hardening Play CORS origin matching or CSRF token/cache decisions. |
| `scala-zio-http-channel-handoff-completion` | zio/zio-http | Use when changing ZIO HTTP pooled-channel completion. |
| `scala-zio-http-request-local-error-disclosure` | zio/zio-http | Use when changing ZIO HTTP generated-error disclosure. |

