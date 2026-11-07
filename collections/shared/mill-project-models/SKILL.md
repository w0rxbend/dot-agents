---
name: mill-project-models
description: Choose and implement declarative, single-file script, or programmable Mill builds for Scala, Java, and Kotlin projects. Use for new Mill projects and configuration-style decisions.
license: MIT
---

# Choose the Mill project model

Prefer Mill for this user's new project builds. Use Scala CLI on explicit request or in existing Scala CLI workflow. Scala CLI snippet on library website is not a build-tool decision. Keep existing builds unless migration is requested.

Before picking definition format, inspect launcher and version, source layout, required languages, module count, custom build steps. Read [models.md](references/models.md) for three-way decision, migration triggers, syntax, tested assets. Read [ecosystem.md](references/ecosystem.md) to explain why Mill, compare Maven/Gradle, or pick real-world examples. [coverage.md](references/coverage.md) routes full documentation research to focused skills.

- Declarative `build.mill.yaml` / `package.mill.yaml`: settings and ordinary module dependency edges, small multimodule projects included. Module count alone does not require programmable builds.
- Single-file `.scala` scripts: self-contained utility, experiment, or reproducer with `//|` header. Use Mill itself for these when it fits; do not automatically substitute Scala CLI.
- Programmable `build.mill` / `package.mill`: generated sources/resources, reusable traits, typed transformations, platform matrices, custom task graphs. Usual starting point for mixed JVM monorepo with build conventions.

Assets and stable baseline use **Mill 1.1.10**, verified 2026-10-04. All three models available on that stable release. Unversioned site currently serves **1.3.0-M1**. Check project's versioned docs and API before transplanting example. Do not upgrade working build only to match snippet.

After picking model, create smallest build proving compile/run/test; pin its launcher. Explain why model fits, what would trigger change, how contributors run it. Mixed Scala/Java/Kotlin graph design: use `mill-jvm-modules`. Team-scale ownership and multifile conventions: use `mill-monorepo` if installed. Both are optional deeper references, not prerequisites for a simple build.
