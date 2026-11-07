---
name: mill-scala-platforms
description: Design Mill Scala JVM JS Native cross builds, web resource pipelines, and Spark projects with correct platform dependencies, source sharing, and runtime constraints. Use when a Mill build targets Scala.js, Scala Native, cross platforms or Spark.
license: MIT
---

# Scala platforms and specialized applications

Read [platforms.md](references/platforms.md) for Scala.js, Scala Native, cross-platform source sharing, JVM native-image distinctions, Spark. Use version-supported platform module and matching test trait.

JVM, JS, Native and Spark classpaths/toolchains are not interchangeable. Cross-platform dependencies need platform artifacts and compatible compiler/runtime versions. Share portable domain/source code deliberately. Keep platform APIs in platform-specific roots/modules.

Represent frontend bundles and generated assets as typed task edges into backend resources. Keep compiler/generator output in task destinations. Test both platform library and packaged application boundary.

For Spark, match actual cluster's Scala binary/JDK/Spark release and packaging contract. Current example avoids Java 24+ for its older Spark/Hadoop combination. This does not override Java 25 VSS modules elsewhere. Do not apply repository-wide default toolchain to incompatible workloads.
