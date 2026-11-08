# Structuring a team-scale Mill build

## Partition by ownership and change propagation

JVM monorepo can hold: `contracts` (Java/JVM-neutral APIs), language-specific implementation libraries, domain services, generated clients, frontend tools, test support, deployable applications. Keep production edges acyclic, directed toward stable interfaces. Applications compose implementations; libraries do not depend on deployment modules. Shared fixture is library with explicit users; production modules still do not depend on tests.

Granularity drives compilation, selective test breadth, release artifacts, ownership. Split where policy, reuse or change independence improves. Avoid both extremes: one giant module, module per source file. Check fan-out: often-edited catch-all dependency can rebuild most of repository. Where behavior permits, separate highly shared stable contracts from volatile implementation details.

## Conventions as code

Small common JVM trait holds JDK/release policy; Scala/Kotlin/Java traits add compiler/test defaults. Orthogonal capabilities (code generation, publishing, framework) get narrow traits. Neutral API module should not inherit server dependencies, Docker packaging or integration test startup from all-in-one platform trait.

Centralize version values; do not inject whole dependency list into every module. Keep defaults overridable. Separate mandatory compatibility from team convention. Overrides appending to `super` keep prior settings; replacing may be intentional but should be reviewable. Build-definition code is compiled Scala: normal trait composition and visibility apply. No I/O in constructors/top-level vals, no global mutable registries collecting modules.

Runnable fixture `assets/multi-file` implements same Java/Kotlin/Scala graph: root convention trait, one `package.mill` per source owner. Run `./mill app.run + scalaService.test` to verify discovery and cross-package references.

## Multifile discovery

Root `build.mill` can define shared traits. Module folder's `package.mill` uses its package (`package build.service`) and `object package extends build.ServiceModule`. Backtick Scala keyword `package` as root object name. Object becomes module `service`, not `service.package`. Named object inside that package file adds another segment.

Package files are discovered in direct subfolders of build/package directory. For `platform/services/order/package.mill`, keep intermediary package files in `platform/` and `platform/services/`, even if they only declare a package. Missing ones can hide leaf from task resolution. Resolve final graph after splitting; do not assume filesystem paths imply module paths.

Helper `.mill` files hold versions, traits, small definitions in matching package. Nested `build.mill` is separate root/build context with distinct alias and namespace behavior. Use it for independently maintained nested builds only after reading documented limitations. Normal multi-team monorepo usually needs package files, not unrelated build root per team.

## Cross builds

`Cross[MyModule](supportedVersions)` creates variants with typed cross values. Consumer of another cross module must pick matching variant explicitly (`other(crossScalaVersion)` for Scala crosses) or deliberately use configured default. Default variant is not automatically compatible with every consumer. Quote bracket selectors in shells.

Keep axes meaningful: Scala binary versions for library, JVM runtime compatibility tests, JS/Native platforms, deployment feature variants. Limit supported matrix. Align artifact names/suffixes and source directories with publication policy. Variants may share common source roots plus version/platform-specific ones. Do not publish two incompatible variants under identical coordinates.

## Precompiled modules

Official API describes `PrecompiledModule` classes from meta-build sources or published JVM artifacts. YAML `extends` can instantiate compiled class with its `Config`, via version-specific discovery machinery and explicit experimental enablement key. Avoids generating/compiling separate build definitions for many near-identical modules.

Use when measured build-definition compilation is bottleneck and configuration patterns are regular. Maintain small version-compatible fixture before spreading across monorepo. Reuse, testing, IDE visibility, diagnostics must stay adequate. Shared traits plus package files: simpler baseline. Precompilation does not fix overcoupled module graph or undeclared task inputs.

## Adoption and verification

Split one representative module family first; compare resolved selectors, source roots, compile/test behavior, artifact contents. Record source and convention owners in repository's existing ownership process. Shared compiler flag, BOM, generator or runtime policy changes need representative downstream validation. Keep predictable per-team and aggregate commands; do not replace typed edges with shell sequencing.

Sources: [large builds](https://mill-build.org/mill/large/large.html), [multifile builds](https://mill-build.org/mill/large/multi-file-builds.html), [modules](https://mill-build.org/mill/fundamentals/modules.html), [cross builds](https://mill-build.org/mill/fundamentals/cross-builds.html), [precompiled modules](https://mill-build.org/mill/large/pre-compiled-modules.html), [multilanguage builds](https://mill-build.org/mill/large/multi-language-builds.html).
