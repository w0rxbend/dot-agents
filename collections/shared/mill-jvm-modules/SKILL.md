---
name: mill-jvm-modules
description: Design and debug Scala, Java, and Kotlin modules in one Mill build, including interop, dependency graphs, source layouts, and aligned JVM targets. Use for mixed JVM projects.
license: MIT
---

# Mixed JVM module graphs

Start from real module dependency graph and public binary interfaces. New builds in this user's environment: prefer Mill. Respect existing builds and explicit language/tool choices. Do not promise universal three-language joint compiler in one source module.

[mixed-jvm.md](references/mixed-jvm.md): tested Java → Kotlin → Scala → Java graph, interop boundaries, target alignment, refactoring choices. [configuration.md](references/configuration.md): source layouts, test inheritance, annotation processing, KSP/Kapt, mixed declarative/programmable definitions. `assets/mixed-jvm`: runnable Mill 1.1.10 example.

Compilation units: `JavaModule`, `ScalaModule`, `KotlinModule`. Link with typed `moduleDeps`; do not splice another module's `out/` directory into classpath. Narrow module imports need explicit `DepSyntax` import. Qualify `TestModule` in mixed-language build files.

Align JDK with Java `--release`, Scala release settings, Kotlin JVM target. Mill build JVM, application compiler/toolchain JVM, bytecode target: separate decisions. Check runtime minimum and framework requirements, especially VSS Java 25 versus Java 21 library boundary.

After graph edits: compile downstream application, run cross-boundary tests, inspect application classpath, run packaged artifact. Large graphs: also prove unrelated modules stay independent; use selective execution against prepared baseline. Split interface module from implementations to break cycles. Test helpers should not make production code depend on test modules.
