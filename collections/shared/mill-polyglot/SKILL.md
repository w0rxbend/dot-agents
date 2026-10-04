---
name: mill-polyglot
description: Integrate Mill Python JavaScript TypeScript Groovy and experimental Android modules with JVM monorepos using typed artifact edges and platform-specific toolchains.
license: MIT
---

# Polyglot and experimental platforms

Read [languages.md](references/languages.md) for Python, JS/TypeScript, Groovy, and heterogeneous artifact edges. Read [android.md](references/android.md) for experimental SDK/IDE/testing/release support.

Keep language-specific module dependencies separate from cross-language artifact dependencies. JVM libraries connect through compatible `moduleDeps`; a Python executable or frontend bundle connects through a producer task output consumed by a JVM resource/package task. One build coordinates multiple toolchains; it does not make their runtime artifacts interchangeable.

The site groups Android/Python/JavaScript/Groovy support under experimental platforms. Verify availability and supported APIs on the pinned release before promising production suitability. The runnable pack fixtures validate JVM Scala/Java/Kotlin and configuration models; these other platforms have researched guidance, not a claim of executed platform tests.

Pin interpreters/Node/SDK/compiler dependencies, track lock/requirements files, and isolate task destinations. Preserve existing package-manager metadata and runtime contracts where they remain required. Never automatically accept Android licenses, sign releases, upload packages, or push images just because an example does so.
