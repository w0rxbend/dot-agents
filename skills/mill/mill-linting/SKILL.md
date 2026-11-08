---
name: mill-linting
description: Configure Mill formatting, linting, coverage, and binary compatibility checks across Scala Java Kotlin modules, with separate fix and CI check workflows. Use when setting up or running format, lint, coverage or MiMa checks in a Mill build.
license: MIT
---

# Mill code quality workflows

Read [quality.md](references/quality.md) for language-specific integrations, task forms, adoption policy, compatibility checks. Before applying docs snippets, inspect pinned Mill/plugin APIs. Some prose examples mismatch names; cross-check configuration and module API.

Separate developer fix commands from CI check commands. Successful formatter rewrite is not a formatting check. Scope operations to owned source roots; deliberately exclude generated/vendor outputs. Scala 3 formatting needs Scala 3 dialect. Do not copy Scala 2 formatter setting into VSS code.

Scala: ScalaFmt/Scalafix. Java: Java formatters and analyzers. Kotlin: KtFmt/KtLint/Detekt. Do not wire Kotlin Detekt through ErrorProne; docs prose mentions it by mistake. Semantic and compiler plugins need matching compiler/version artifacts.

Large repositories: share owned configs; use gradual adoption/ratcheting when appropriate. Do not relax all warnings for one generated library. Check coverage and binary compatibility at correct module/platform boundary. Neither is interchangeable with ordinary tests.
