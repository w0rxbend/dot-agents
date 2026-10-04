---
name: mill-testing
description: Configure and debug Mill test modules for Scala Java Kotlin, framework discovery, fixtures, fork grouping, integration suites, and affected-test execution.
license: MIT
---

# Mill test modules and execution

Read [testing.md](references/testing.md) for framework wiring, suite selection, shared fixtures, and concurrency. Use the enclosing language's `JavaTests`, `ScalaTests`, or `KotlinTests`; qualify framework helpers in mixed-language build files. Mill tests are ordinary modules with dependencies, not a special dependency scope.

Inspect the existing framework and test discovery before changing libraries. Preserve the tested parent dependency when extending `moduleDeps`. Match compiler/framework/runner versions and verify actual tests execute. A successful command discovering zero tests is not useful verification.

Separate unit and integration modules when resources or lifecycle differ. Pass tracked fixture paths instead of assuming repository-root working directories. Budget Mill jobs, test fork groups, and framework threads separately, and isolate ports/files for concurrent tests.

For an ordinary edit, run the relevant suite and downstream boundary tests. For a monorepo's selective CI, prepare a valid baseline and inspect affected selectors before execution; see `mill-monorepo` if installed. Keep full checks where environment changes are outside the tracked graph. Do not rewrite or add tests merely to mirror build settings.
