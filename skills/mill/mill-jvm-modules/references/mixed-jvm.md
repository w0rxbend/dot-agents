# A single Mill build for Scala, Java, and Kotlin

## Tested architecture

`assets/mixed-jvm` has five modules. `api`: Java `Greeting` interface. `kotlinImpl`: Kotlin implementation, depends on `api`. `scalaService`: consumes both, exposes regular Scala class with Java-friendly method. `app`: Java, depends on `scalaService`. `unrelated`: separate Java module checking isolation. Scala uTest suite exercises full Java/Kotlin/Scala path.

After adding stable 1.1.10 launcher, run `./mill app.run + scalaService.test + unrelated.compile`. Expected output: `Hello, Mill from Scala`; interop assertion checks same value. Example pins Scala 3.8.2, Kotlin 2.2.20, managed Temurin 21.0.8, bytecode target 21. Launcher header runs build on locally installed JVM. For fully managed build execution, replace `mill-jvm-version: system` with deliberate pinned managed JVM. Interop demonstration only, not VSS Java 25 server template.

```text
api (Java contracts) ──> kotlinImpl (Kotlin)
      │                      │
      └──────────────> scalaService (Scala) ──> app (Java)
                              │
                         scalaService.test
unrelated (Java; no dependency edges to the application)
```

Arrows point from prerequisite to consumer. Consumer declares `moduleDeps`, for example `def moduleDeps = Seq(api, kotlinImpl)` on `scalaService`. Mill schedules prerequisite compilation and propagates classpaths. Do not hand-compile Java before Kotlin in shell loop or collect arbitrary generated jars from `out/`.

## What belongs in one module

`ScalaModule` handles Scala plus Java sources; `KotlinModule` has Java and Kotlin source tasks. If sources reference each other, verify compiler's mixed-source behavior, processing phases, source ordering for actual version. Neither gives `.scala`, `.java`, `.kt` in one directory a general three-language joint compiler. Prefer separate JVM modules for three languages, especially when ownership and public APIs already differ.

Unit: usually one compiler/toolchain policy, coherent purpose. No module per source file. Broad `common` module coupling all teams often bottlenecks selective tests and recompilation. Split stable contract types, language-specific implementations, executable composition when that improves dependency direction.

## Interop boundary choices

Java interfaces and records can give neutral boundary when every participating compiler supports selected Java release. Keep public method signatures accessible from all callers. Java collections, explicitly documented nullability, simple DTOs are often easier shared types than Scala collections, opaque types, path-dependent types or Kotlin suspend functions exposed to Java callers. Boundary decision only; not rule to flatten Scala application's internal domain model.

Kotlin top-level methods compile into file facade classes such as `UtilKt`. `@JvmName` can stabilize facade name; `@JvmStatic` can make selected object/companion entrypoints Java-convenient. Default arguments need deliberate overloads for Java callers. Java platform types are nullability concern: set contract at boundary instead of blindly applying `!!`.

Scala objects, givens, extension methods, union types, Scala-only generic abstractions may be awkward from Java/Kotlin. Small ordinary class or interface adapter can make public binary API explicit. Test from actual foreign-language caller, not only Scala suite with Scala-specific conveniences. Released libraries: inspect public signatures, add language-appropriate binary compatibility checks.

## JVM target alignment

Pin compiler and JVM versions before diagnosing `UnsupportedClassVersionError`, missing Java APIs or Kotlin metadata errors. Java `--release 21` constrains APIs and bytecode. Example: Scala `-release 21`, Kotlin `-jvm-target 21`. Kotlin bytecode target alone does not prove newer JDK APIs cannot leak into public code. Older runtimes: verify Kotlin's supported release/API configuration.

Java 25 application can consume Java 17 contract library; Java 25 implementation cannot run on Java 17. Consumers with different minimum runtimes: make that visible per module, no repository-wide JDK assumption. Avoid shared convention trait silently raising every published library's target when one service adopts VSS.

## Common failures and a useful diagnosis

| Symptom | Investigate | Repair |
| --- | --- | --- |
| `mvn` is not a StringContext member | Narrow imports omitted `DepSyntax` | Import one language's dependency syntax explicitly |
| Kotlin cannot see Java/Scala class | Missing module edge, source path or visibility | Inspect `moduleDeps`, `sources`, `compileClasspath` |
| Duplicate class / conflicting Scala runtime | Duplicate sources or incompatible artifact suffixes | Own each source tree once; inspect resolved dependencies |
| Runtime method/class missing after successful compile | Compile-only dependency, changed runtime version, packaging omissions | Inspect `runClasspath`; run built artifact |
| Cyclic module references | Implementation depends on caller's domain types | Extract stable interface; invert implementation dependency |
| Java caller cannot invoke Scala/Kotlin convenience API | Compiler-generated facade/signature | Add explicit JVM adapter; test from Java |

Use `./mill inspect scalaService.compile`, `./mill show scalaService.moduleDeps`, `./mill show app.runClasspath`, `./mill app.showMvnDepsTree`. Unsure: discover tasks with `resolve`. Keep mixed imports intentional so similarly named test/module helpers do not accidentally select another language's defaults.

Sources: [Java intro](https://mill-build.org/mill/javalib/intro.html), [Scala intro](https://mill-build.org/mill/1.1.x/scalalib/intro.html), [Kotlin intro](https://mill-build.org/mill/1.1.x/kotlinlib/intro.html), [Java configuration](https://mill-build.org/mill/javalib/module-config.html), [Scala configuration](https://mill-build.org/mill/scalalib/module-config.html), [Kotlin configuration](https://mill-build.org/mill/kotlinlib/module-config.html), [managing JVM versions](https://mill-build.org/mill/fundamentals/configuring-jvm-versions.html).
