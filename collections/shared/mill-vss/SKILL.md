---
name: mill-vss
description: Build VirtusLab Scala Stack applications with Mill as the preferred tool while retaining direct-style Scala Ox and synchronous Tapir guidance and translating Scala CLI or sbt examples. Use when building a VirtusLab Scala Stack (Ox, Tapir) project with Mill.
license: MIT
---

# VirtusLab Scala Stack with Mill

For this user, **Mill is the preferred build tool for new VSS projects**. Scala CLI stays for explicit requests and existing workflows. VSS website's Scala CLI starter command and upstream skill's sbt setup are examples to translate, not defaults.

Read [vss-with-mill.md](references/vss-with-mill.md) for dependencies, toolchain, project models, starter conversion and official skill integration. Keep existing Scala CLI/sbt builds unless migration is requested. For relevant Ox/Tapir/domain chapter, use official globally installed `direct-style-scala` skill, with local tooling preference override.

Keep direct-style application decisions separate from build syntax. Programmable Mill build may use ordinary build-file Scala syntax; it need not follow every application-code style rule. Prefer available project-aware Scala tools when useful; fall back to `./mill` compile/test/format commands. Do not invent unavailable `compile-module` or `find-dep` tools.

Current VSS guidance targets Scala 3 / Java 25 / Ox / synchronous Tapir. Verify compatible stable library versions in canonical Maven metadata; pin them. Keep older-runtime contract/Spark modules separate when monorepo needs them. Do not replace explicitly requested effect-based stack merely because VSS offers direct style.

YAML for simple VSS settings. Mill script for tiny reproducer/utility. Programmable modules for generated OpenAPI/schema clients, resource pipelines, shared conventions or mixed JVM monorepo. Before reporting completion, verify compilation, relevant tests, application startup and packaged behavior.
