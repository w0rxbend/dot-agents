---
name: mill-jvm-modules
description: Design and debug Scala, Java, and Kotlin modules in one Mill build, including interop, dependency graphs, source layouts, and aligned JVM targets. Use for mixed JVM projects.
license: MIT
---

# Mixed JVM module graphs

Start with the real module dependency graph and public binary interfaces. Prefer Mill for new builds in this user's environment; respect an existing build and explicit language/tool choices. Do not promise a universal three-language joint compiler inside one source module.

Read [mixed-jvm.md](references/mixed-jvm.md) for the tested Java → Kotlin → Scala → Java graph, interop boundaries, target alignment, and refactoring choices. Read [configuration.md](references/configuration.md) for source layouts, test inheritance, annotation processing, KSP/Kapt, and mixed declarative/programmable definitions. `assets/mixed-jvm` is a runnable Mill 1.1.10 example.

Use `JavaModule`, `ScalaModule`, and `KotlinModule` for appropriate compilation units. Add typed `moduleDeps`; do not splice another module's `out/` directory into a classpath. Import `DepSyntax` explicitly when using narrow module imports, and qualify `TestModule` in mixed-language build files.

Align the chosen JDK with Java `--release`, Scala release settings, and Kotlin JVM target. Mill's build JVM, application compiler/toolchain JVM, and produced bytecode target are separate decisions. Verify the runtime minimum and framework requirements, especially VSS Java 25 versus a Java 21 library boundary.

After editing the graph, compile the downstream application, run tests that cross the interop boundary, inspect its classpath, and run its packaged artifact. For large graphs, also prove unrelated modules remain independent and use selective execution against a prepared baseline. Separate an interface module from implementations to remove cycles; test helpers should not force production code to depend on test modules.
