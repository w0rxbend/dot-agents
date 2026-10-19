---
name: mill-testing
description: Configure and debug Mill test modules for Scala Java Kotlin, framework discovery, fixtures, fork grouping, integration suites, and affected-test execution. Use when adding, configuring or debugging tests in a Mill build.
license: MIT
---

# Mill test modules and execution

Read [testing.md](references/testing.md) for framework wiring, suite selection, shared fixtures, and concurrency. Use the enclosing language's `JavaTests`, `ScalaTests`, or `KotlinTests`; qualify framework helpers in mixed-language build files. Mill tests are ordinary modules with dependencies, not a special dependency scope.

Inspect the existing framework and test discovery before changing libraries. Preserve the tested parent dependency when extending `moduleDeps`. Match compiler/framework/runner versions and verify actual tests execute. A successful command discovering zero tests is not useful verification.

Pitfalls observed on Mill 1.1.9: `JavaTests` forwards `jvmId` from the enclosing module (`zio.test.jvmId` honours a `MILL_JVM_ID` override with no local definition), so a test module need not duplicate the override; a test module that extends plain `ScalaTests` inherits none of a sibling trait's `forkArgs`/`testForkGrouping`, so mix the isolation trait in explicitly. Inside a nested `object test extends ScalaTests`, `moduleDir` is `<outer>/test`; a `forkArgs` or `Task.Source` path meant for the outer module's sources needs `moduleDir / os.up / ...` (verify with `./mill show <mod>.test.forkArgs`). Forked test JVMs see the client's environment through the daemon only if the daemon was started with it; when a test reads `sys.env`, run `./mill --no-server`. There is no per-module `reformat` task in 1.1.x; scope a reformat with `./mill mill.scalalib.scalafmt.ScalafmtModule/reformatAll <module>.sources`. Join distinct goals with `+`; after `--no-server` runs, a daemon-mode run in the same workspace can fail with `SubprocessZincApi ... Connection refused` until `./mill shutdown`.

Separate unit and integration modules when resources or lifecycle differ. Pass tracked fixture paths instead of assuming repository-root working directories. Budget Mill jobs, test fork groups, and framework threads separately, and isolate ports/files for concurrent tests.

For an ordinary edit, run the relevant suite and downstream boundary tests. For a monorepo's selective CI, prepare a valid baseline and inspect affected selectors before execution; see `mill-monorepo` if installed. Keep full checks where environment changes are outside the tracked graph. Do not rewrite or add tests merely to mirror build settings.
