---
name: mill-cli-and-ide
description: Set up Mill launchers, versioned build headers, CLI queries, IDE/BSP integration, and migrations from Maven, Gradle, or sbt. Use for Mill setup and command troubleshooting.
license: MIT
---

# Mill setup, CLI, IDE, and migration

Read [operations.md](references/operations.md) for launcher installation, header scopes, task queries, flags, IDEs, and diagnostics. Read [migration.md](references/migration.md) before importing an existing build.

Prefer a checked-in project bootstrap launcher, then use `./mill` consistently in developer instructions and CI. Inspect the actual project version before selecting documentation. The tested examples use stable 1.1.10; unversioned docs can point to a milestone. Mill is preferred for new projects here; preserve an existing sbt/Gradle/Maven build unless migration is part of the request.

Quote wildcard, brace, and cross selectors in shell commands. Discover task names using `resolve` and task documentation/dependencies using `inspect`; do not substitute a guessed flag or an old 0.x snippet. Keep Mill flags before task selectors, and distinguish task arguments after selectors. A new selector with separate arguments starts after `+`.

Use BSP/IDE support corresponding to the project's version and languages. Separate build-server problems from compiler failures by compiling with the launcher first. `mill-jvm-version` controls the build runtime; module `jvmVersion` controls module toolchains. Do not alter a user's global JDK merely to satisfy a module.

For migration, generate scaffolding in an isolated checkout or reviewed working tree, preserve source layout with compatibility modules, compare behavior and artifacts, and retire the previous build only after requested parity is achieved. `init` is a starting point rather than proof of equivalent behavior.
