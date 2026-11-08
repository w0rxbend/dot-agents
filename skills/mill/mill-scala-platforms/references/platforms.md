# Scala.js, Native, web applications, and Spark

## Scala.js and shared sources

Scala.js module extends `ScalaJSModule` with explicit Scala.js version and platform-aware dependencies. Use its JS test trait. Backend stays JVM `ScalaModule`. Common code can live in platform-sharing modules with JVM and JS variants. Each consumer depends on correct variant. `PlatformScalaModule` and cross-platform examples show shared versus platform-specific source roots and artifact naming.

Share pure models/validation/serialization only where their dependencies support both platforms. Java libraries and JVM-only reflection/I/O are not automatically available in browser. Scala.js linker tasks such as fast/full linking produce artifacts for frontend/backend resource task. Verify version-specific output structure and module kind. Copy needed linked files and maps for development/deployment explicitly. Do not scan stale `out/` tree.

For server packaging, call client link/bundle task inside backend resource computation. Copy output into `Task.dest`. Append that resource root to `super.resources()`. Frontend edits then invalidate backend packaging. If web resources use content hashes/cache busting, generate filename mapping and files together. Exercise shipped resource URLs in integration test.

Official web examples (Cask, http4s, TodoMVC, shared JVM/JS code, platform publication, WebAssembly) illustrate build patterns. Respect application's framework choice. VSS requests generally use Ox/synchronous Tapir. Existing http4s application keeps its model unless migration is requested. WebAssembly support has platform/version limits. Do not infer every Scala.js library or browser supports a given wasm build.

## Scala Native

`ScalaNativeModule` needs supported Scala/Scala Native version, platform artifacts, native compiler/linker, any C/system dependencies. Tests use Scala Native's test module, not JVM fork. Multimodule Native application needs Native-compatible upstream modules. JVM classfiles do not become native dependencies merely because API signatures match.

Put C interop behind deliberate bindings. Configure native linking options/search paths as tracked inputs when they influence outputs. Pin CI OS/toolchain and build target architecture. Release modes trade build time, binary size, runtime behavior. Verify actual intended release mode. Do not ship debug link. Native incremental compilation and work-directory options are version-specific.

Scala Native and GraalVM native-image are different approaches. Scala Native uses its Scala/native runtime and compatible ecosystem; native-image processes JVM application under GraalVM with reachability constraints. Choose by actual dependencies and runtime needs. Test resource/dynamic behavior on delivered binary.

## Cross publication and compatibility

Cross-build module selects Scala binary/full version and platform. Consumer edges pick matching variant. Keep published identities distinct for JVM/JS/Native. Avoid copying JVM-only `mvnDeps` list into every variant. Libraries using compiler internals need full-version cross artifacts, not binary-only naming. Limit compatibility matrix to advertised combinations. Verify tests of each selected variant.

## Spark and PySpark

Start from target Spark distribution/cluster contract: Scala binary version, Spark/Hadoop release, supported JDK, deployment mode, provided libraries, `spark-submit` arguments. Current Spark 3.5 example uses Scala 2.12 and flags Java 24+ incompatibility in its bundled Hadoop security API path. Pin compatible JDK for that module. This is example-specific compatibility warning, not blanket rule for all Spark versions.

For cluster jobs, separate Spark-provided dependencies from libraries job must package. Avoid embedding conflicting Spark/Hadoop copies in assembly without deliberate deployment reason. Submission tooling may require plain jar without executable shell prefix. Test local execution and representative `spark-submit` behavior separately. Local mode cannot prove distributed file/network/resource behavior.

PySpark builds use `PythonModule` with Python dependencies and separate Python runner. When one repository contains both, align its Spark/JVM environment with Scala side. If VSS service on Java 25 submits jobs to Java 21 Spark cluster, keep both runtime policies independent in build.

Sources: [Scala web/JS examples](https://mill-build.org/mill/scalalib/web-examples.html), [Scala Native examples](https://mill-build.org/mill/scalalib/native-examples.html), [Spark examples](https://mill-build.org/mill/scalalib/spark.html), [cross builds](https://mill-build.org/mill/fundamentals/cross-builds.html), [Scala packaging](https://mill-build.org/mill/scalalib/packaging.html), [Scala dependencies](https://mill-build.org/mill/scalalib/dependencies.html).
