---
name: mill-linting
description: Configure Mill formatting, linting, coverage, and binary compatibility checks across Scala Java Kotlin modules, with separate fix and CI check workflows.
license: MIT
---

# Mill code quality workflows

Read [quality.md](references/quality.md) for language-specific integrations, exact useful task forms, adoption policy, and compatibility checks. Inspect the pinned Mill/plugin APIs before applying a documentation snippet; some prose examples contain mismatched names, so cross-check the configuration and module API.

Keep developer fix commands separate from CI check commands. A formatter that rewrites files successfully is not a formatting check. Scope operations to owned source roots and exclude generated/vendor outputs deliberately. Scala 3 formatting needs the Scala 3 dialect; do not copy a Scala 2 formatter setting into VSS code.

Use ScalaFmt/Scalafix for Scala, Java formatters and Java analyzers for Java, and KtFmt/KtLint/Detekt for Kotlin. Do not wire Kotlin Detekt through ErrorProne because of a mistaken prose mention. Semantic and compiler plugins require matching compiler/version artifacts.

For a large repository, share owned configs and use gradual adoption/ratcheting when appropriate. Do not relax all warnings to accommodate one generated library. Check coverage and binary compatibility at the correct module/platform boundary; neither is interchangeable with ordinary tests.
