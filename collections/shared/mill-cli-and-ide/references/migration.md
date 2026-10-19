# Migration with behavioral parity

Inventory the old build's module graph, source/resource roots, dependencies and scopes, test frameworks, runtime environment, generators, packaging, publishing metadata, profiles, and CI behavior. Choose a representative library and runnable application before attempting a large repository conversion.

The official automated migration uses `./mill init` to detect Maven, Gradle, and sbt builds and generate initial Mill definitions. It may detect Spring Boot or Quarkus conventions as well. Run it where generated changes can be reviewed; retain the original build while comparing results. Unsupported profiles, JPMS/module-path configuration, custom tasks, complex plugins, generated resources, and framework-specific AOT processing commonly require manual work. A successful importer is not a correctness test.

Map subprojects to modules and preserve layout using `MavenModule`, `KotlinMavenModule`, or `SbtModule` plus their language-specific test traits. Compile dependencies become `mvnDeps`; provided/compile-only dependencies become `compileMvnDeps`; runtime-only dependencies become `runMvnDeps`. Test libraries belong to the test submodule. Project edges become `moduleDeps` on the consumer. Match Scala binary/full-version and platform suffixes deliberately.

Compare compiler flags and warnings, main classes, resources inside jars, generated source contents, test discovery/counts, environment variables, fork JVM settings, and dependency resolution. A common migration failure is tests compiling while the new runner discovers zero tests. Another is an assembly running locally because an external dependency is on a developer classpath but missing in the shipped artifact.

Translate a plugin's **behavior**, not merely its name. A build-time JVM library can support a custom tracked task without needing a Mill plugin; a sophisticated integration may require a maintained version-compatible plugin. Capture generators as upstream tasks with explicit inputs and destinations. Do not leave imperative pre-build scripts outside the graph when downstream task caching depends on their output.

For a monorepo, convert a vertical slice, agree convention ownership, and expand by dependency layers. Use a parity checklist per module family and compare representative artifacts in CI. Remove the old build only when the task explicitly includes completing migration and required workflows are covered. If a plugin or platform cannot reach parity, document that specific limitation rather than making an unsupported equivalence claim.

Sources: [migration strategy](https://mill-build.org/mill/migrating/migrating.html), [automated migration and limitations](https://mill-build.org/mill/migrating/auto-migrating.html), [dependency semantics](https://mill-build.org/mill/fundamentals/library-deps.html).
