# Local build preference for this installation

This section reflects the user's explicit preference and takes precedence over
the upstream tooling and new-project setup defaults below and in its chapters.

- Prefer **Mill** for new Scala/VSS projects. Use declarative Mill configuration
  for simple settings, Mill single-file scripts for small self-contained programs,
  and programmable Mill for custom logic, mixed JVM modules, and monorepos.
- Scala CLI remains available when explicitly requested or already used by the
  project. Do not choose it as the default because the VSS website's starter
  prompt uses it. Preserve an existing sbt/Gradle/Maven/Scala CLI build unless
  migration is requested.
- On Mill projects, compile and test with the project's pinned `./mill` launcher
  and its real module selectors. Use available project-aware Scala tools when
  useful; if unavailable, use Mill CLI commands instead of inventing tools.
  Run sbt-specific import/compile/format commands only in an actual sbt project.
- Format Scala with the project's Mill ScalaFmt workflow and Scala 3 dialect.
  Apply application compiler options to the appropriate Mill Scala module,
  not to a nonexistent `build.sbt`. Build definitions can use ordinary syntax
  supported by their Mill version; application style rules should not break them.
- Read the local `mill-vss` skill for translating Scala CLI/sbt configuration
  and the `mill-project-models`, `mill-jvm-modules`, and `mill-monorepo` skills
  when those tasks apply. If not installed, apply the same preference directly
  with the version-matching official Mill documentation.
- Retain upstream direct-style/Ox/Tapir application guidance for the relevant
  task. Keep intentional JVM interoperability and explicitly chosen existing
  effect-based application stacks within the user's scope.

The upstream new-project chapter's sbt skeleton and website's Scala CLI starter
are source examples to translate for a new Mill project in this environment.
