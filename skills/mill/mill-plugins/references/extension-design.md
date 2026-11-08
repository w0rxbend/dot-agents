# Selecting an extension mechanism

| Need | Mechanism | Review |
| --- | --- | --- |
| Small build-time computation from JVM library | Header `//| mvnDeps` | Build classpath/version distinct from application dependencies |
| Reuse inside one repository | Trait/helper `.mill` file | Task inputs, ownership, compatibility with module families |
| Build compiler/source customization | `mill-build` meta-build | Compilation dependency direction, bootstrapping |
| Conflicting generator/library versions | Subprocess or isolated classloader | Classpath isolation, runtime/JDK, resource cleanup |
| Expensive reusable tool/compiler | Worker/CachedFactory | Correct keys, thread safety, close/teardown |
| Integration shared by several projects | Published Mill plugin | Binary platform suffix, fixture tests, maintenance policy |

Build-header imports load ordinary Java/Scala libraries; simple HTML/schema processing needs no dedicated plugin. Scala cross notation uses build's Scala version, which may differ from application compiler version. Plugins integrate with Mill APIs, so must match Mill's binary platform. When supported, use documented `$MILL_VERSION` and `$MILL_BIN_PLATFORM` placeholders. Do not copy old `_mill0.11` coordinate into 1.x.

## Isolated execution and workers

Global header imports share one build classpath. If two generators need conflicting versions, or build code clashes with a library's transitive dependencies, run resolved tool classpath in subprocess or isolated classloader. Pin tool, main class, JDK; record all input paths/options. Subprocess outputs go in invoking task's destination and must be returned as tracked paths.

`Task.Worker` caches live in-memory resources (compilers, classloaders). Changed worker inputs should invalidate instance. AutoCloseable/teardown must release files, processes and classloaders. Bounded CachedFactory reuses several tool instances keyed by relevant classpath/options, without leaking one per module. Verify concurrency before sharing mutable compiler across parallel tasks.

Avoid defaulting to reflection-based execution when a small command-line tool works. With reflection, check argument types, failure reporting, closeable loader lifetime, parent classloader policy. Keep generator upstream of consumer to avoid `compile → generatedSources → compile` cycles.

## The meta-build

Mill compiles build definitions through own build pipeline. `--meta-level 1` inspects first meta-build; version-specific commands can show its classpath, compile tasks and generated sources. Customize explicitly via `mill-build/` with root `MillBuildRootModule`; without custom files, a synthetic meta-build exists. Recursive meta-builds work; each layer adds maintenance/bootstrapping boundary.

Use meta-build sources to share compiled build classes or supply generation/configuration that build definitions require. Application/build code sharing needs clear dependency direction. Avoid importing final application compilation into its own build compiler. Debug missing header imports and plugin conflicts at meta level before adding arbitrary dependencies to application modules.

## Writing a plugin

Compile against supported Mill library/API version. Publish with documented binary platform identity, e.g. 1.x plugin suffix. Expose small capability traits with configurable versions/paths, not global mutable configuration. Keep task documentation and defaults meaningful; consuming agents discover them via `inspect`.

Use Mill's testkit for unit fixtures, real integration builds for classpath/discovery/CLI behavior. Prove trait generates intended output, keeps inherited resources, invalidates on input changes and leaves unrelated tasks cached. Verify fresh consuming build can import published/local artifact. Trait compiling in plugin's own repository does not prove header imports and module discovery work for users.

Check version-matching API for `Task`, module traits, worker types, `Discover`, evaluator APIs and precompiled configuration. Latest API may document methods missing from pinned stable release. Read changelog for migrations; keep explicit supported-version fixture matrix.

Sources: [imports](https://mill-build.org/mill/extending/import-mvn-plugins.html), [running JVM code](https://mill-build.org/mill/extending/running-jvm-code.html), [writing plugins](https://mill-build.org/mill/extending/writing-plugins.html), [meta-build](https://mill-build.org/mill/extending/meta-build.html), [API](https://mill-build.org/api/latest/mill.html), [changelog](https://github.com/com-lihaoyi/mill/blob/main/changelog.adoc).
