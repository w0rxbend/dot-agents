# A single Mill build for Scala, Java, and Kotlin

## Tested architecture

`assets/mixed-jvm` contains five modules. `api` defines a Java `Greeting` interface. `kotlinImpl` implements it in Kotlin and depends on `api`. `scalaService` consumes that interface and implementation, and exposes a regular Scala class with a Java-friendly method. `app` is Java and depends on `scalaService`. `unrelated` is a separate Java module used to check isolation. A Scala uTest suite exercises the complete Java/Kotlin/Scala path.

Run `./mill app.run + scalaService.test + unrelated.compile` after adding the stable 1.1.10 launcher. Expected application output is `Hello, Mill from Scala`; the interop assertion verifies the same value. The example pins Scala 3.8.2, Kotlin 2.2.20, managed Temurin 21.0.8, and bytecode target 21. The launcher header uses the locally installed JVM for build execution; for a project requiring fully managed build execution, replace `mill-jvm-version: system` with a deliberate pinned managed JVM. This template is an interop demonstration, not a VSS Java 25 server template.

```text
api (Java contracts) ──> kotlinImpl (Kotlin)
      │                      │
      └──────────────> scalaService (Scala) ──> app (Java)
                              │
                         scalaService.test
unrelated (Java; no dependency edges to the application)
```

Arrows indicate prerequisites flowing to consumers. `moduleDeps` is written on the consumer, for example `def moduleDeps = Seq(api, kotlinImpl)` on `scalaService`. Mill schedules prerequisite compilation and propagates classpaths. Do not manually compile Java before Kotlin in a shell loop or collect arbitrary generated jars from `out/`.

## What belongs in one module

A `ScalaModule` supports Scala with Java source handling; a `KotlinModule` has Java and Kotlin source tasks. Verify the compiler's supported mixed-source behavior, processing phases, and source ordering for the actual version when sources refer back to each other. Neither implies that `.scala`, `.java`, and `.kt` in one directory share a general three-language joint compiler. Prefer separate JVM modules for a three-language project, especially when ownership and public APIs already differ.

A unit should usually have one compiler/toolchain policy and coherent purpose. Do not create a module for every source file. Conversely, a broad `common` module coupling all teams often creates a bottleneck for selective tests and recompilation. Split stable contract types, language-specific implementations, and executable composition when those boundaries improve dependency direction.

## Interop boundary choices

Java interfaces and records can provide a neutral boundary when every participating compiler supports the selected Java release. Keep public method signatures accessible from all callers. Java collections, explicitly documented nullability, and simple DTOs are often easier shared types than exposing Scala collections, opaque types, path-dependent types, or Kotlin suspend functions to Java callers. This is a boundary decision, not a rule to flatten the Scala application's internal domain model.

Kotlin top-level methods compile into file facade classes such as `UtilKt`; `@JvmName` can stabilize a facade name, and `@JvmStatic` can make selected object/companion entrypoints convenient for Java. Default arguments need deliberate overloads for Java callers. Treat platform types from Java as a nullability concern; establish the contract at the boundary rather than blindly applying `!!`.

Scala objects, givens, extension methods, union types, and Scala-only generic abstractions may be awkward from Java/Kotlin. A small ordinary class or interface adapter can make the public binary API explicit. Test through the actual foreign-language caller, not only from a Scala suite that can access Scala-specific conveniences. For released libraries, inspect public signatures and add binary compatibility checks appropriate to the language.

## JVM target alignment

Pin compiler and JVM versions before diagnosing `UnsupportedClassVersionError`, missing Java APIs, or Kotlin metadata errors. Java `--release 21` constrains both APIs and bytecode. The example uses Scala `-release 21` and Kotlin `-jvm-target 21`; a Kotlin bytecode target alone is not proof that newer JDK APIs cannot leak into public code. Verify Kotlin's supported release/API configuration when supporting older runtimes.

A Java 17 contract library can be consumed by a Java 25 application, but a Java 25 implementation cannot run on Java 17. If consumers have different minimum runtimes, make that visible per module instead of applying a repository-wide JDK assumption. Avoid a shared convention trait that silently raises every published library's target when one service adopts VSS.

## Common failures and a useful diagnosis

| Symptom | Investigate | Repair |
| --- | --- | --- |
| `mvn` is not a StringContext member | Narrow imports omitted `DepSyntax` | Import one language's dependency syntax explicitly |
| Kotlin cannot see a Java/Scala class | Missing module edge, source path, or visibility | Inspect `moduleDeps`, `sources`, and `compileClasspath` |
| Duplicate class / conflicting Scala runtime | Duplicate sources or incompatible artifact suffixes | Keep each source tree owned once; inspect resolved dependencies |
| Runtime method/class missing after successful compile | Compile-only dependency, changed runtime version, packaging omissions | Inspect `runClasspath` and run the built artifact |
| Cyclic module references | Implementation depends on caller's domain types | Extract a stable interface and invert the implementation dependency |
| Java caller cannot invoke a Scala/Kotlin convenience API | Compiler-generated facade/signature | Add an explicit JVM adapter and test from Java |

Use `./mill inspect scalaService.compile`, `./mill show scalaService.moduleDeps`, `./mill show app.runClasspath`, and `./mill app.showMvnDepsTree`. Discover tasks with `resolve` when uncertain. Keep mixed imports intentional so similarly named test/module helpers do not accidentally select another language's defaults.

Sources: [Java intro](https://mill-build.org/mill/javalib/intro.html), [Scala intro](https://mill-build.org/mill/1.1.x/scalalib/intro.html), [Kotlin intro](https://mill-build.org/mill/1.1.x/kotlinlib/intro.html), [Java configuration](https://mill-build.org/mill/javalib/module-config.html), [Scala configuration](https://mill-build.org/mill/scalalib/module-config.html), [Kotlin configuration](https://mill-build.org/mill/kotlinlib/module-config.html), [managing JVM versions](https://mill-build.org/mill/fundamentals/configuring-jvm-versions.html).
