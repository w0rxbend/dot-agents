# Structuring a team-scale Mill build

## Partition by ownership and change propagation

A useful JVM monorepo can have `contracts` (Java/JVM-neutral APIs), language-specific implementation libraries, domain services, generated clients, frontend tools, test support, and deployable applications. Keep production edges acyclic and directed toward stable interfaces. An application composes implementations; libraries should not depend on deployment modules. A shared fixture is a library with explicit users, not an excuse to make production modules depend on tests.

Module granularity affects compilation, selective test breadth, release artifacts, and ownership. Split where policy, reuse, or change independence improves. Avoid both one giant module and a module per source file. Examine fan-out: a frequently edited catch-all dependency can force most of the repository to rebuild. Move highly shared stable contracts apart from volatile implementation details where behavior permits.

## Conventions as code

Use a small common JVM trait for relevant JDK/release policy, then Scala/Kotlin/Java-specific traits for compiler/test defaults. Orthogonal capabilities such as code generation, publishing, or a framework belong in narrowly scoped traits. A neutral API module should not inherit server dependencies, Docker packaging, or integration test startup simply because a platform trait combines everything.

Centralize version values without injecting the entire dependency list into every module. Keep defaults overridable and distinguish mandatory compatibility from team convention. In method overrides, appending to `super` preserves prior settings; replacing them may be intentional but should be reviewable. Build-definition code is compiled Scala; ordinary trait composition and visibility apply. Avoid I/O in constructors/top-level vals and global mutable registries collecting modules.

The runnable `assets/multi-file` fixture implements the same Java/Kotlin/Scala graph using a root convention trait and one `package.mill` per source owner. Run `./mill app.run + scalaService.test` to verify discovery and cross-package references.

## Multifile discovery

A root `build.mill` can define shared traits. A module folder's `package.mill` uses its package, for example `package build.service`, and `object package extends build.ServiceModule`. Use backticks around the Scala keyword `package` as the root object name. It becomes the module `service`, not `service.package`. A named object inside that package file adds another segment.

Package files are discovered in direct subfolders of a build/package directory. For `platform/services/order/package.mill`, retain intermediary package files in `platform/` and `platform/services/` even if they only declare a package. Their absence can make the leaf disappear from task resolution. Resolve the final graph after splitting a build rather than assuming filesystem paths imply module paths.

Helper `.mill` files can hold versions, traits, and small definitions in the appropriate package. A nested `build.mill` is a separate root/build context with distinct alias and namespace behavior; use it for independently maintained nested builds only after reading the documented limitations. A normal multi-team monorepo usually needs package files, not an unrelated build root for every team.

## Cross builds

`Cross[MyModule](supportedVersions)` creates variants with typed cross values. A consumer of another cross module must select the matching variant explicitly (`other(crossScalaVersion)` for Scala crosses), or intentionally use a configured default. The default variant is not automatically compatible with every consumer. Quote bracket selectors in shells.

Separate axes with meaning: Scala binary versions for a library, JVM runtime compatibility tests, JS/Native platforms, or deployment feature variants. Limit the supported matrix. Align artifact names/suffixes and source directories with publication policy; cross variants can share common source roots while using version/platform-specific roots where appropriate. Do not publish two incompatible variants under identical coordinates.

## Precompiled modules

The official API describes `PrecompiledModule` classes available from meta-build sources or published JVM artifacts. YAML `extends` can instantiate the compiled class with its `Config`, using version-specific discovery machinery and the explicit experimental enablement key. This avoids generating/compiling separate build definitions for many nearly identical modules.

Use it when measured build-definition compilation is a bottleneck and configuration patterns are regular. Maintain a small version-compatible fixture before spreading it across the monorepo. Reuse/testing/IDE visibility and diagnostics must remain adequate. Ordinary shared traits plus package files are a simpler baseline; precompilation does not fix an overcoupled module graph or undeclared task inputs.

## Adoption and verification

Split a representative module family first and compare resolved selectors, source roots, compile/test behavior, and artifact contents. Document source owners and convention owners in the repository's existing ownership process. Changes to shared compiler flags, BOMs, generators, or runtime policy warrant representative downstream validation. Preserve predictable commands for each team and aggregate workflows without replacing typed edges with shell sequencing.

Sources: [large builds](https://mill-build.org/mill/large/large.html), [multifile builds](https://mill-build.org/mill/large/multi-file-builds.html), [modules](https://mill-build.org/mill/fundamentals/modules.html), [cross builds](https://mill-build.org/mill/fundamentals/cross-builds.html), [precompiled modules](https://mill-build.org/mill/large/pre-compiled-modules.html), [multilanguage builds](https://mill-build.org/mill/large/multi-language-builds.html).
