# Scala.js, Native, web applications, and Spark

## Scala.js and shared sources

A Scala.js module extends `ScalaJSModule` with an explicit Scala.js version and platform-aware dependencies; use its JS test trait. A backend remains a JVM `ScalaModule`. Common code can live in platform-sharing modules with JVM and JS variants, while each consumer depends on the correct variant. `PlatformScalaModule` and cross-platform examples demonstrate shared versus platform-specific source roots and artifact naming.

Share pure models/validation/serialization only where their dependencies support both platforms. Java libraries and JVM-only reflection/I/O are not automatically available in a browser. Scala.js linker tasks such as fast/full linking produce artifacts consumed by a frontend/backend resource task; verify version-specific output structure and module kind. Copy linked files and maps needed for development/deployment explicitly rather than scanning a stale `out/` tree.

For server packaging, call the client link/bundle task inside the backend resource computation, copy output into `Task.dest`, and append that resource root to `super.resources()`. This makes a frontend edit invalidate backend packaging. If web resources use content hashes/cache busting, generate the filename mapping and files together, and exercise the shipped resource URLs in an integration test.

The official web examples include Cask, http4s, TodoMVC, shared JVM/JS code, platform publication, and a WebAssembly example. These illustrate build patterns. Respect the application's framework choice: VSS requests generally use Ox/synchronous Tapir, while an existing http4s application should retain its chosen model unless migration is requested. WebAssembly support has platform/version limits; do not infer that every Scala.js library or browser supports a given wasm build.

## Scala Native

A `ScalaNativeModule` requires a supported Scala/Scala Native version, platform artifacts, native compiler/linker, and any C/system dependencies. Its tests use Scala Native's test module, not a JVM fork. A multimodule Native application depends on Native-compatible upstream modules; JVM classfiles do not become native dependencies merely because the API signatures match.

Put C interop behind deliberate bindings and configure native linking options/search paths as tracked inputs when they influence outputs. Pin CI OS/toolchain and build target architecture. Release modes trade build time, binary size, and runtime behavior; verify the actual intended release mode instead of shipping a debug link. Native incremental compilation and work-directory options are version-specific.

Scala Native and GraalVM native-image are different approaches. Scala Native uses its Scala/native runtime and compatible ecosystem; native-image processes a JVM application under GraalVM with reachability constraints. Choose based on actual dependencies and runtime needs, and test resource/dynamic behavior on the delivered binary.

## Cross publication and compatibility

A cross-build module selects Scala binary/full version and platform. Consumer edges should pick the matching variant. Keep published identities distinct for JVM/JS/Native and avoid copying a JVM-only `mvnDeps` list into every variant. Libraries using compiler internals need full-version cross artifacts rather than binary-only naming. Limit the compatibility matrix to advertised combinations and verify each selected variant's tests.

## Spark and PySpark

Start with the target Spark distribution/cluster contract: Scala binary version, Spark/Hadoop release, supported JDK, deployment mode, provided libraries, and `spark-submit` arguments. The current documented Spark 3.5 example uses Scala 2.12 and calls out Java 24+ incompatibility in its bundled Hadoop security API path; pin a compatible JDK for that module. Treat that as an example-specific compatibility warning, not a blanket rule for all Spark versions.

For cluster jobs, distinguish dependencies provided by Spark from libraries the job must package. Avoid embedding conflicting Spark/Hadoop copies in the assembly without a deliberate deployment reason. A plain jar without the executable shell prefix may be required by submission tooling. Test local execution and representative `spark-submit` behavior separately; local mode cannot prove distributed file/network/resource behavior.

PySpark builds use `PythonModule` with Python dependencies and a separate Python runner. Keep its Spark/JVM environment aligned with the Scala side when one repository contains both. If a VSS service on Java 25 submits jobs to a Java 21 Spark cluster, the build should preserve those independent runtime policies.

Sources: [Scala web/JS examples](https://mill-build.org/mill/scalalib/web-examples.html), [Scala Native examples](https://mill-build.org/mill/scalalib/native-examples.html), [Spark examples](https://mill-build.org/mill/scalalib/spark.html), [cross builds](https://mill-build.org/mill/fundamentals/cross-builds.html), [Scala packaging](https://mill-build.org/mill/scalalib/packaging.html), [Scala dependencies](https://mill-build.org/mill/scalalib/dependencies.html).
