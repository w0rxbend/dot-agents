---
name: mill-dependencies-and-toolchains
description: Manage Mill module and Maven dependencies, Scala cross artifacts, BOMs, compiler plugins, private repositories, and JVM versions in mixed Scala Java Kotlin builds.
license: MIT
---

# Dependencies and JVM toolchains

Read [dependencies.md](references/dependencies.md) for scopes, artifact suffixes, BOMs, repositories, and resolution failures. Read [toolchains.md](references/toolchains.md) when aligning build/runtime JVMs, compiler targets, and matrix variants.

Distinguish project `moduleDeps`, module `mvnDeps`, and build-header imports. Tests are separate modules with ordinary dependencies. Use compile-only and runtime-only tasks intentionally, preserving inherited lists when appropriate. A dependency management/BOM convention should not put every library on every module's classpath.

Use the project's pinned versions unless an upgrade is requested. For a new dependency, verify coordinates and a stable version from canonical Maven metadata or the upstream release; do not copy old documentation example versions as current recommendations. Match Scala binary/full/compiler and JS/Native suffixes to the consuming module.

Inspect `showMvnDepsTree`, resolved classpaths, and POM output before forcing/excluding versions. Document why a constraint exists. Keep private repository credentials in environment/configuration inputs and avoid logging their values. A working local cache is insufficient proof that a fresh machine can resolve the project.

Align compiler targets independently of the JVM running Mill. Preserve lower-runtime libraries when one service uses Java 25/VSS. Verify the assembled application on its advertised runtime and record platform requirements for Native, Spark, Android, and compiler plugins.
