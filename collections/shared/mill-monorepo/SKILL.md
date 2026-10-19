---
name: mill-monorepo
description: Architect large multimodule Mill builds with shared conventions, multifile definitions, cross builds, dependency ownership, precompiled modules, and selective execution. Use for JVM monorepos.
license: MIT
---

# Large builds and monorepos

Read [architecture.md](references/architecture.md) for module boundaries, convention traits, multifile discovery, and precompilation decisions. Read [selective-ci.md](references/selective-ci.md) for affected-task execution with a real baseline and reproducibility limits.

Make the dependency graph, source ownership, and convention ownership explicit. Separate stable contracts from language-specific implementations and deployment composition; use typed module/task edges. Scala/Java/Kotlin modules can coexist in one build without a three-language joint compiler. Prefer programmable conventions for custom logic while allowing declarative modules where owners only need settings.

Split large definitions into `package.mill` / `package.mill.yaml` near source owners. Retain intermediary package files needed for discovery. Use helper `.mill` files/meta-build code for shared definitions; do not multiply global mutable state or introduce another nested root build casually.

Cross-build only supported compatibility axes. Match dependencies to the selected cross value instead of accidentally using the default variant. Precompiled modules are experimental and require version-specific configuration; consider them after measuring build-definition compilation, not simply because the repository has many modules.

For selective CI, prepare the same selectors on the chosen baseline, preserve its snapshot while evaluating the change, inspect the selection, and run affected tasks. Do not implement affectedness using directory-name filters alone. Broad convention/toolchain/input changes should propagate through the graph; retain periodic/full validation for environment-dependent behavior that selective execution cannot model.
