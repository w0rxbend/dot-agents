# Why Mill and how to use the example catalog

Mill models work as named tasks and modules with visible dependency edges. Caching, task inspection, parallel evaluation, and reusable Scala traits cover custom work, not only compilation. Fits repositories mixing JVM libraries, applications, code generation, and deployable frontend resources: build expresses producer/consumer relationships directly.

Official Maven comparison stresses less launcher/JDK setup and concise declarative settings. Gradle comparison stresses typed task computations and ordinary inheritance instead of mutable configuration. These are Mill project's arguments, not neutral measurements of every competing build. Existing Maven/Gradle project may already have required integrations configured. Assess those integrations and migration effort. Do not replace them solely because this environment prefers Mill for new work.

Performance comparison separates sequential/parallel clean builds, one-module builds, incremental changes, no-op execution. Its figures are workload-dependent. To evaluate a real repository, compare equivalent tests, compiler flags, dependency caches, machine/JDK, daemon warm-up, output artifacts. Measure build-definition compilation and external downloads separately. No-op result on one project does not prove all projects improve by same factor.

## Select a relevant example instead of copying all of it

| Official examples | Useful pattern | Review before adapting |
| --- | --- | --- |
| Scala Acyclic | Full Scala compiler-version cross build | Compiler plugin binary compatibility; Scala 2 versus Scala 3 support |
| Scala Fansi / larger Ammonite and Coursier builds | Shared conventions, cross-platform libraries | Platform artifacts, source roots, plugin compatibility |
| Java JimFS / Commons IO / C3P0 | Maven layout, annotation processors, suites, publishing | Processor paths, Java release targets, tests relying on repository working directories |
| Scala Cask/TodoMVC and http4s | Web resources, caching, integration tests | Framework-specific runtime and test behavior; VSS prefers direct-style Ox/Tapir when requested |
| Java Spring Boot / Jetty / Micronaut / Quarkus | Server startup, generated metadata, AOT/native variants | BOMs, processors, plugin support, GraalVM reachability, runtime tests |
| Kotlin Ktor / Spring / Micronaut / KotlinJS | Main-class naming, Kotlin compiler plugins, browser/server sharing | Kotlin version/plugins, `FooKt` entrypoints, platform target boundaries |
| Scala Native / Spark | Toolchain- and environment-specific builds | Native library availability or Spark's Scala/JDK compatibility |

Scala examples include building the **Scala CLI implementation** with Mill. That is Mill building a Scala project, not a recommendation of Scala CLI as this user's default build tool.

For unfamiliar APIs, read version-matching API reference and source via links on the task's documentation. Changelog tells whether a method was added, renamed, experimental, or deprecated. Talks/blog posts explain historical design and benchmarks; for implementation they rank below current module APIs. A 0.12 blog snippet with older `build.sc`, `ivyDeps`, or `T` conventions needs migration review before use in a 1.x build.

Sources: [why Mill](https://mill-build.org/mill/index.html), [Maven comparison](https://mill-build.org/mill/comparisons/maven.html), [Gradle comparison](https://mill-build.org/mill/comparisons/gradle.html), [performance comparison](https://mill-build.org/mill/comparisons/performance.html), [Scala examples](https://mill-build.org/mill/scalalib/build-examples.html), [Java examples](https://mill-build.org/mill/javalib/build-examples.html), [Kotlin web examples](https://mill-build.org/mill/kotlinlib/web-examples.html), [API reference](https://mill-build.org/api/latest/mill.html), [changelog](https://github.com/com-lihaoyi/mill/blob/main/changelog.adoc), [talks and blog posts](https://mill-build.org/mill/reference/talks-blog-posts.html).
