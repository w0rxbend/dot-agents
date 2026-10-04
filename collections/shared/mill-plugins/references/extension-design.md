# Selecting an extension mechanism

| Need | Mechanism | Review |
| --- | --- | --- |
| A small build-time computation from a JVM library | Header `//| mvnDeps` | Build classpath/version distinct from application dependencies |
| Reuse inside one repository | Trait/helper `.mill` file | Task inputs, ownership, compatibility with module families |
| Build compiler/source customization | `mill-build` meta-build | Compilation dependency direction and bootstrapping |
| Conflicting generator/library versions | Subprocess or isolated classloader | Classpath isolation, runtime/JDK, resource cleanup |
| Expensive reusable tool/compiler | Worker/CachedFactory | Correct keys, thread safety, close/teardown |
| Integration shared by several projects | Published Mill plugin | Binary platform suffix, fixture tests, maintenance policy |

Build-header imports can load ordinary Java/Scala libraries; a dedicated plugin is unnecessary for simple HTML/schema processing. Scala cross notation uses the build's Scala version, which can differ from the application compiler version. Plugins integrate with Mill APIs and must match Mill's binary platform. Use documented `$MILL_VERSION` and `$MILL_BIN_PLATFORM` placeholders when supported, rather than copying an old `_mill0.11` coordinate into 1.x.

## Isolated execution and workers

Global header imports share a build classpath. If two generators need conflicting versions, or build code would conflict with a library's transitive dependencies, resolve a tool classpath and execute it in a subprocess or isolated classloader. Pin tool/main class/JDK and record all input paths/options. Subprocess outputs belong to the invoking task's destination and must be returned as tracked paths.

`Task.Worker` caches live in-memory resources such as compilers or classloaders. Worker input changes should invalidate the instance; AutoCloseable/teardown behavior must release files, processes, and classloaders. A bounded CachedFactory can reuse several tool instances keyed by relevant classpath/options without leaking one per module. Verify concurrency before sharing a mutable compiler across parallel tasks.

Avoid reflection-based execution as the default when a small command-line tool works. If using reflection, check argument types, failure reporting, closeable loader lifetime, and parent classloader policy. Keep the generator upstream of the consumer to avoid `compile → generatedSources → compile` cycles.

## The meta-build

Mill compiles build definitions through its own build pipeline. `--meta-level 1` inspects the first meta-build; version-specific commands can show its classpath, compile tasks, and generated sources. Explicit customization uses `mill-build/` with a root `MillBuildRootModule`; a synthetic meta-build exists without custom files. Recursive meta-builds are supported, but each layer adds a maintenance/bootstrapping boundary.

Use meta-build sources to share compiled build classes or supply required generation/configuration for build definitions. Application/build code sharing needs a clear dependency direction; avoid importing the final application compilation into its own build compiler. Debug missing header imports and plugin conflicts at the meta level before adding arbitrary dependencies to application modules.

## Writing a plugin

Compile against the supported Mill library/API version and publish with the documented binary platform identity, for example a 1.x plugin suffix. Expose small capability traits with configurable versions/paths rather than global mutable configuration. Keep task documentation and defaults meaningful because consuming agents can use `inspect` to discover them.

Use Mill's testkit for unit fixtures and real integration builds for classpath/discovery/CLI behavior. Prove the trait generates the intended output, retains inherited resources, invalidates on input changes, and leaves unrelated tasks cached. Verify a published/local artifact can be imported by a fresh consuming build. Do not consider a trait compiling in the plugin's own repository sufficient evidence that header imports and module discovery work for users.

Consult the version-matching API for `Task`, module traits, worker types, `Discover`, evaluator APIs, and precompiled configuration. The latest API may document methods absent from a pinned stable release. Read the changelog for migrations and keep an explicit supported-version fixture matrix.

Sources: [imports](https://mill-build.org/mill/extending/import-mvn-plugins.html), [running JVM code](https://mill-build.org/mill/extending/running-jvm-code.html), [writing plugins](https://mill-build.org/mill/extending/writing-plugins.html), [meta-build](https://mill-build.org/mill/extending/meta-build.html), [API](https://mill-build.org/api/latest/mill.html), [changelog](https://github.com/com-lihaoyi/mill/blob/main/changelog.adoc).
