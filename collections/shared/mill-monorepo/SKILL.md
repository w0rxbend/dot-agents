---
name: mill-monorepo
description: Architect large multimodule Mill builds with shared conventions, multifile definitions, cross builds, dependency ownership, precompiled modules, and selective execution. Use for JVM monorepos.
license: MIT
---

# Large builds and monorepos

Read [architecture.md](references/architecture.md) for module boundaries, convention traits, multifile discovery, precompilation. Read [selective-ci.md](references/selective-ci.md) for affected-task execution, real baseline, reproducibility limits.

Make dependency graph, source and convention ownership explicit. Keep stable contracts apart from language-specific implementations and deployment composition. Use typed module/task edges. Scala/Java/Kotlin modules can share one build without three-language joint compiler. Prefer programmable conventions for custom logic; allow declarative modules where owners only need settings.

Split large definitions into `package.mill` / `package.mill.yaml` near source owners. Keep intermediary package files needed for discovery. Shared definitions go in helper `.mill` files/meta-build code. Do not multiply global mutable state or casually add nested root builds.

Cross-build only supported compatibility axes. Match dependencies to selected cross value, not accidental default variant. Precompiled modules: experimental, need version-specific configuration. Consider after measuring build-definition compilation, not for module count alone.

Selective CI: prepare same selectors on chosen baseline, keep its snapshot while evaluating change, inspect selection, run affected tasks. Do not derive affectedness from directory-name filters alone. Broad convention/toolchain/input changes should propagate through graph. Keep periodic/full validation for environment-dependent behavior selective execution cannot model.
