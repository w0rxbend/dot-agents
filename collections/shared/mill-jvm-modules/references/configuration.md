# Source layout and compiler-specific configuration

## Choose a filesystem contract

A default `object service extends ScalaModule` reads `service/src` and `service/resources`; its nested `test` reads `service/test/src`. A backticked root `object package` maps tasks and inputs to the root module. Nested objects add source-path segments unless the module overrides its directory behavior.

During Maven/Gradle/sbt migration, retain existing source paths with compatibility modules instead of moving all sources to match a template. Use `MavenModule` / `MavenTests` for Java, `SbtModule` / `SbtTests` for Scala, and `KotlinMavenModule` / its corresponding test trait for Kotlin. Inspect test source paths, resource directories, and any additional integration suite. When a compatibility module reads multiple language directories, avoid adding the same directory again in `sources`.

Use `Task.Sources("custom-src")` as a tracked source input and append to `super.sources()` when extending a convention. Paths are relative to the module directory; root-relative references must be deliberate. An absolute workstation path is not portable to a fresh clone. Generated sources belong in their producer's task destination and flow through `generatedSources`; source roots should not include all of `out/`.

## Keep runtime configuration separate

`mainClass`, `forkArgs`, and `forkEnv` configure execution; `javacOptions`, `scalacOptions`, and `kotlincOptions` configure compilation. A Kotlin top-level entrypoint often has a `FooKt` class name. Specify the main class when several are discovered or an executable entrypoint comes from a dependency. Verify packaging picks up that main class as well as `run`.

Use runtime dependencies for logging providers and database drivers when they do not belong on compilation APIs. Scope framework-specific dependencies to the module needing them. A neutral API module should not inherit web-server dependencies because another module extends a shared trait.

## Processors and generated code

Java annotation processing may require a specific processor classpath and javac options. Keep processor dependencies distinct from runtime libraries where the API allows it. Java release/JDK changes can alter annotation-processing defaults; the example's compiler emits a notice when processors are discovered. Make processing intent explicit in a real project instead of suppressing the notice indiscriminately.

Kotlin compiler plugins must match Kotlin's compiler version; `kotlincPluginMvnDeps` is not interchangeable with application `mvnDeps`. KSP uses `mill.kotlinlib.ksp.KspModule` and version-specific generated-source/test traits; Kapt has its own integration. Determine which processor technology the library actually supports. Pin processor and compiler versions together, inspect generated Java/Kotlin roots, and confirm test processing has its own correct configuration.

Scala compiler plugins use `scalacPluginMvnDeps`; some require full compiler version cross artifacts (`:::`) rather than binary cross artifacts (`::`). Scala 2 plugin examples such as Acyclic cannot be applied automatically to Scala 3. SemanticDB versions and language support matter for IDEs and semantic refactoring tools; inspect the effective options before enabling a plugin throughout a mixed-version repository.

## Tests and inheritance

Nested `JavaTests`, `ScalaTests`, and `KotlinTests` are language-specific modules configured to test their enclosing module. Select a real runner through a framework trait or explicit `testFramework` and dependencies. Test dependencies belong to the test module, not a Maven-style `test` scope on the production module. When overriding test `moduleDeps`, append to `super.moduleDeps` if retaining the parent/test defaults; replacing the list can detach tests from the code under test.

Share fixtures through a deliberate test-support module or another test module only where that reuse is intended. Distinguish a fixture library from executing another suite. Do not let production APIs depend on fixture modules. Give integration suites separate resource ownership and execution settings when they start services.

## Configuration values versus computation

YAML is suitable for strings, lists, paths, and ordinary dependencies. `!append` preserves inherited list values. A custom programmable trait can supply code generation while YAML selects settings. This hybrid lets module owners avoid editing build implementation without preventing tracked custom work. Confirm the referenced trait is available on the build's classpath and the qualified class is compatible with the project's Mill version.

When a module's generation uses its own compiled classes, watch for a cycle between `compile` and `generatedSources`. Extract the generator into an upstream module, run it via a supported subprocess/isolated classloader, and make the generator's classpath and input schema explicit dependencies. That structure also makes the tool independently testable.

Sources: [modules](https://mill-build.org/mill/fundamentals/modules.html), [Scala module configuration](https://mill-build.org/mill/scalalib/module-config.html), [Kotlin module configuration](https://mill-build.org/mill/kotlinlib/module-config.html), [Java module configuration](https://mill-build.org/mill/javalib/module-config.html), [testing Java](https://mill-build.org/mill/javalib/testing.html), [testing Scala](https://mill-build.org/mill/scalalib/testing.html), [testing Kotlin](https://mill-build.org/mill/kotlinlib/testing.html), [migration](https://mill-build.org/mill/migrating/migrating.html).
