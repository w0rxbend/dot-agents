---
name: mill-polyglot
description: Integrate Mill Python JavaScript TypeScript Groovy and experimental Android modules with JVM monorepos using typed artifact edges and platform-specific toolchains. Use when a Mill build includes non-JVM modules.
license: MIT
---

# Polyglot and experimental platforms

Read [languages.md](references/languages.md) for Python, JS/TypeScript, Groovy, heterogeneous artifact edges. Read [android.md](references/android.md) for experimental SDK/IDE/testing/release support.

Keep language-specific module dependencies separate from cross-language artifact dependencies. JVM libraries connect via compatible `moduleDeps`. Python executable or frontend bundle connects via producer task output, consumed by JVM resource/package task. One build coordinates many toolchains; it does not make their runtime artifacts interchangeable.

Mill docs list Android/Python/JavaScript/Groovy support as experimental platforms. Verify availability and supported APIs on pinned release before promising production suitability. Runnable pack fixtures validate JVM Scala/Java/Kotlin and configuration models. Other platforms have researched guidance only, not executed platform tests.

Pin interpreters/Node/SDK/compiler dependencies, track lock/requirements files, isolate task destinations. Keep existing package-manager metadata and runtime contracts where still required. Never auto-accept Android licenses, sign releases, upload packages, or push images just because example does.
