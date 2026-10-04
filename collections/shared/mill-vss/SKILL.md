---
name: mill-vss
description: Build VirtusLab Scala Stack applications with Mill as the preferred tool while retaining direct-style Scala Ox and synchronous Tapir guidance and translating Scala CLI or sbt examples.
license: MIT
---

# VirtusLab Scala Stack with Mill

For this user, **Mill is the preferred build tool for new VSS projects**. Scala CLI remains available for explicit requests and existing workflows. The VSS website's Scala CLI starter command and the upstream skill's sbt setup are examples to translate, not defaults to apply here.

Read [vss-with-mill.md](references/vss-with-mill.md) for dependencies, toolchain, project models, starter conversion, and the official skill integration. Preserve existing Scala CLI/sbt builds unless migration is requested. Use the official globally installed `direct-style-scala` skill for the relevant Ox/Tapir/domain chapter, with the local tooling preference override.

Keep direct-style application decisions separate from build syntax. A programmable Mill build can use ordinary build-file Scala syntax; it need not follow every application-code style rule. Prefer available project-aware Scala tools when useful, with `./mill` compile/test/format commands as the fallback. Do not invent unavailable `compile-module` or `find-dep` tools.

Current VSS guidance targets Scala 3 / Java 25 / Ox / synchronous Tapir. Verify compatible stable library versions using canonical Maven metadata and pin the chosen versions. Keep older-runtime contract/Spark modules separate when a monorepo requires them. Do not replace an explicitly requested effect-based stack merely because VSS offers direct style.

Pick YAML for simple VSS settings, a Mill script for a tiny reproducer/utility, and programmable modules for generated OpenAPI/schema clients, resource pipelines, shared conventions, or a mixed JVM monorepo. Verify compilation, relevant tests, application startup, and packaged behavior before reporting completion.
