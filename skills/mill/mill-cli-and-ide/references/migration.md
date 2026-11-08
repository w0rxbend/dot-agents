# Migration with behavioral parity

Inventory old build: module graph, source/resource roots, dependencies and scopes, test frameworks, runtime environment, generators, packaging, publishing metadata, profiles, CI behavior. Pick representative library and runnable application before large repository conversion.

`./mill init` is official automated migration. Detects Maven, Gradle and sbt builds; generates initial Mill definitions. May also detect Spring Boot or Quarkus conventions. Run where generated changes get reviewed; keep original build while comparing. Manual work commonly needed for unsupported profiles, JPMS/module-path configuration, custom tasks, complex plugins, generated resources, framework-specific AOT processing. Successful import is not correctness test.

Map subprojects to modules. Keep layout with `MavenModule`, `KotlinMavenModule` or `SbtModule` plus matching language-specific test traits. Compile dependencies become `mvnDeps`; provided/compile-only become `compileMvnDeps`; runtime-only become `runMvnDeps`. Test libraries go in test submodule. Project edges become consumer's `moduleDeps`. Match Scala binary/full-version and platform suffixes deliberately.

Compare compiler flags and warnings, main classes, resources in jars, generated source contents, test discovery/counts, environment variables, fork JVM settings, dependency resolution. Common failure: tests compile, but new runner discovers zero tests. Another: assembly runs locally because external dependency is on developer classpath, yet missing from shipped artifact.

Translate plugin's **behavior**, not merely its name. Build-time JVM library can back custom tracked task, no Mill plugin needed. Sophisticated integration may need maintained version-compatible plugin. Model generators as upstream tasks with explicit inputs and destinations. Do not leave imperative pre-build scripts outside graph when downstream task caching depends on their output.

Monorepo: convert vertical slice, agree convention ownership, expand by dependency layers. Keep parity checklist per module family; compare representative artifacts in CI. Remove old build only when task explicitly includes completing migration and required workflows are covered. If plugin or platform cannot reach parity, document that specific limitation; do not claim unsupported equivalence.

Sources: [migration strategy](https://mill-build.org/mill/migrating/migrating.html), [automated migration and limitations](https://mill-build.org/mill/migrating/auto-migrating.html), [dependency semantics](https://mill-build.org/mill/fundamentals/library-deps.html).
