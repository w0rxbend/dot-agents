---
name: mill-scala-platforms
description: Design Mill Scala JVM JS Native cross builds, web resource pipelines, and Spark projects with correct platform dependencies, source sharing, and runtime constraints.
license: MIT
---

# Scala platforms and specialized applications

Read [platforms.md](references/platforms.md) for Scala.js, Scala Native, cross-platform source sharing, JVM native-image distinctions, and Spark. Use a version-supported platform module and its corresponding test trait.

Do not treat JVM, JS, Native, and Spark classpaths/toolchains as interchangeable. Cross-platform dependencies need platform artifacts and compatible compiler/runtime versions. Share portable domain/source code deliberately and keep platform APIs in platform-specific roots/modules.

Represent frontend bundles and generated assets as typed task edges into backend resources. Keep compiler/generator output in task destinations. Test both the platform library and the packaged application boundary.

For Spark, match the actual cluster's Scala binary/JDK/Spark release and packaging contract. The current example explicitly avoids Java 24+ for its older Spark/Hadoop combination; this does not override Java 25 VSS modules elsewhere. Do not apply a repository-wide default toolchain to incompatible workloads.
