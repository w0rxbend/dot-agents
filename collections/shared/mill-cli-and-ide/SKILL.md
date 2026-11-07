---
name: mill-cli-and-ide
description: Set up Mill launchers, versioned build headers, CLI queries, IDE/BSP integration, and migrations from Maven, Gradle, or sbt. Use for Mill setup and command troubleshooting.
license: MIT
---

# Mill setup, CLI, IDE, and migration

Read [operations.md](references/operations.md) for launcher install, header scopes, task queries, flags, IDEs, diagnostics. Read [migration.md](references/migration.md) before importing existing build.

Prefer checked-in bootstrap launcher; use `./mill` everywhere in developer instructions and CI. Check project's actual version before picking docs. Tested examples use stable 1.1.10; unversioned docs may point to milestone. Mill preferred for new projects here. Keep existing sbt/Gradle/Maven build unless request includes migration.

Quote wildcard, brace and cross selectors in shell. Find task names with `resolve`, task docs/dependencies with `inspect`. Do not substitute guessed flags or old 0.x snippets. Mill flags go before task selectors; task arguments go after. `+` starts new selector with its own arguments.

Match BSP/IDE support to project's version and languages. Compile with launcher first to separate build-server problems from compiler failures. `mill-jvm-version` sets build runtime; module `jvmVersion` sets module toolchains. Do not change user's global JDK merely to satisfy a module.

Migration: generate scaffolding in isolated checkout or reviewed working tree. Keep source layout via compatibility modules. Compare behavior and artifacts. Retire old build only after requested parity. `init` is starting point, not proof of equivalent behavior.
