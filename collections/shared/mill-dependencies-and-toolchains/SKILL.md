---
name: mill-dependencies-and-toolchains
description: Manage Mill module and Maven dependencies, Scala cross artifacts, BOMs, compiler plugins, private repositories, and JVM versions in mixed Scala Java Kotlin builds. Use when adding, upgrading or debugging dependencies or JDK/Scala versions in a Mill build.
license: MIT
---

# Dependencies and JVM toolchains

Read [dependencies.md](references/dependencies.md) for scopes, artifact suffixes, BOMs, repositories, resolution failures. Read [toolchains.md](references/toolchains.md) for aligning build/runtime JVMs, compiler targets, matrix variants.

Distinguish project `moduleDeps`, module `mvnDeps`, build-header imports. Tests are separate modules with ordinary dependencies. Use compile-only/runtime-only tasks deliberately, keeping inherited lists where appropriate. Do not let BOM/dependency-management convention put every library on every module's classpath.

Keep project's pinned versions unless upgrade requested. New dependency: verify coordinates and stable version from canonical Maven metadata or upstream release. Do not treat old documentation example versions as current. Match Scala binary/full/compiler and JS/Native suffixes to consuming module.

Inspect `showMvnDepsTree`, resolved classpaths, POM output before forcing/excluding versions. Document why each constraint exists. Keep private repository credentials in environment/configuration inputs; avoid logging their values. Working local cache does not prove fresh-machine resolution.

Align compiler targets independently of JVM running Mill. Keep lower-runtime libraries when one service uses Java 25/VSS. Verify assembled application on advertised runtime. Record platform requirements for Native, Spark, Android, compiler plugins.
