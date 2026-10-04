---
name: mill-project-models
description: Choose and implement declarative, single-file script, or programmable Mill builds for Scala, Java, and Kotlin projects. Use for new Mill projects and configuration-style decisions.
license: MIT
---

# Choose the Mill project model

Prefer Mill for new project builds in this user's environment. Scala CLI remains available for an explicit request or an existing Scala CLI workflow; a Scala CLI snippet on a library website is not a build-tool decision. Preserve existing builds unless migration is requested.

Inspect the launcher and version, source layout, required languages, number of modules, and custom build steps before choosing the definition format. Read [models.md](references/models.md) for the three-way decision, migration triggers, syntax, and tested assets. Read [ecosystem.md](references/ecosystem.md) when explaining why Mill, comparing Maven/Gradle, or selecting real-world examples. [coverage.md](references/coverage.md) routes the complete documentation research to focused skills.

- Declarative `build.mill.yaml` / `package.mill.yaml`: settings and ordinary module dependency edges, including small multimodule projects. Module count alone does not require programmable builds.
- Single-file `.scala` scripts: a self-contained utility, experiment, or reproducer with a `//|` header. Use Mill itself for these when it fits; do not automatically substitute Scala CLI.
- Programmable `build.mill` / `package.mill`: generated sources/resources, reusable traits, typed transformations, platform matrices, and custom task graphs. This is usually the useful starting point for a mixed JVM monorepo with build conventions.

The assets and stable baseline use **Mill 1.1.10**, verified on 2026-10-04. All three models are available on that stable release. The unversioned site currently serves **1.3.0-M1**; consult the project's versioned docs and API before transplanting an example. Do not upgrade a working build merely to match a snippet.

After selecting a model, create the smallest build that proves compile/run/test and pin its launcher. Explain why the model fits, what would trigger changing it, and how contributors execute it. For mixed Scala/Java/Kotlin graph design, use `mill-jvm-modules`; for team-scale ownership and multifile conventions, use `mill-monorepo` if installed. These are optional deeper references, not prerequisites for a simple build.
