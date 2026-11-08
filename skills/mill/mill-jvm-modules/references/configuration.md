# Source layout and compiler-specific configuration

## Choose a filesystem contract

Default `object service extends ScalaModule` reads `service/src`, `service/resources`; nested `test` reads `service/test/src`. Backticked root `object package` maps tasks and inputs to root module. Nested objects add source-path segments unless module overrides directory behavior.

Maven/Gradle/sbt migration: keep existing source paths via compatibility modules; do not move all sources to fit template. Java: `MavenModule` / `MavenTests`. Scala: `SbtModule` / `SbtTests`. Kotlin: `KotlinMavenModule` / matching test trait. Inspect test source paths, resource directories, extra integration suites. If compatibility module reads several language directories, do not add same directory again in `sources`.

Use `Task.Sources("custom-src")` for tracked source input; when extending convention, append to `super.sources()`. Paths are module-relative; root-relative ones must be deliberate. Absolute workstation paths break on fresh clones. Generated sources belong in producer's task destination, flow via `generatedSources`. Source roots should not include all of `out/`.

## Keep runtime configuration separate

`mainClass`, `forkArgs`, `forkEnv` configure execution; `javacOptions`, `scalacOptions`, `kotlincOptions` configure compilation. Kotlin top-level entrypoint often named `FooKt`. Set main class if several found or executable entrypoint comes from dependency. Verify packaging and `run` both use it.

Logging providers, database drivers: runtime dependencies unless they belong on compilation APIs. Scope framework-specific dependencies to modules needing them. Neutral API module should not inherit web-server dependencies because another module extends shared trait.

## Processors and generated code

Java annotation processing may need specific processor classpath and javac options. Keep processor dependencies apart from runtime libraries where API allows. Java release/JDK changes can alter annotation-processing defaults; example's compiler emits notice when it discovers processors. Real projects: state processing intent explicitly; do not suppress notice indiscriminately.

Kotlin compiler plugins must match Kotlin compiler version; `kotlincPluginMvnDeps` is not interchangeable with application `mvnDeps`. KSP: `mill.kotlinlib.ksp.KspModule` plus version-specific generated-source/test traits. Kapt: own integration. Check which processor technology library supports. Pin processor and compiler versions together, inspect generated Java/Kotlin roots, confirm test processing has own correct configuration.

Scala compiler plugins use `scalacPluginMvnDeps`; some need full compiler version cross artifacts (`:::`), not binary (`::`). Scala 2 plugins such as Acyclic cannot apply automatically to Scala 3. SemanticDB versions and language support matter for IDEs and semantic refactoring tools. Inspect effective options before enabling plugin across mixed-version repository.

## Tests and inheritance

Nested `JavaTests`, `ScalaTests`, `KotlinTests`: language-specific modules testing enclosing module. Pick real runner via framework trait or explicit `testFramework` plus dependencies. Test dependencies go on test module, not Maven-style `test` scope on production module. Overriding test `moduleDeps` and keeping parent/test defaults: append to `super.moduleDeps`. Replacing list can detach tests from code under test.

Share fixtures via deliberate test-support module or another test module only where reuse is intended. Distinguish fixture library from executing another suite. Do not let production APIs depend on fixture modules. Integration suites starting services: separate resource ownership and execution settings.

## Configuration values versus computation

YAML suits strings, lists, paths, ordinary dependencies. `!append` preserves inherited list values. Custom programmable trait can supply code generation while YAML selects settings. Confirm referenced trait is on build classpath and qualified class is compatible with project's Mill version.

Generation using module's own compiled classes risks cycle between `compile` and `generatedSources`. Fix: extract generator into upstream module, run via supported subprocess/isolated classloader, declare its classpath and input schema as explicit dependencies.

Sources: [modules](https://mill-build.org/mill/fundamentals/modules.html), [Scala module configuration](https://mill-build.org/mill/scalalib/module-config.html), [Kotlin module configuration](https://mill-build.org/mill/kotlinlib/module-config.html), [Java module configuration](https://mill-build.org/mill/javalib/module-config.html), [testing Java](https://mill-build.org/mill/javalib/testing.html), [testing Scala](https://mill-build.org/mill/scalalib/testing.html), [testing Kotlin](https://mill-build.org/mill/kotlinlib/testing.html), [migration](https://mill-build.org/mill/migrating/migrating.html).
