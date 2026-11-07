---
name: mill-testing
description: Configure and debug Mill test modules for Scala Java Kotlin, framework discovery, fixtures, fork grouping, integration suites, and affected-test execution. Use when adding, configuring or debugging tests in a Mill build.
license: MIT
---

# Mill test modules and execution

Read [testing.md](references/testing.md) for framework wiring, suite selection, shared fixtures and concurrency. Use enclosing language's `JavaTests`, `ScalaTests` or `KotlinTests`. Qualify framework helpers in mixed-language build files. Mill tests are ordinary modules with dependencies, not special dependency scope.

Inspect existing framework and test discovery before changing libraries. Keep tested parent dependency when extending `moduleDeps`. Match compiler/framework/runner versions; verify actual tests execute. Command that passes but discovers zero tests proves nothing.

Pitfalls observed on Mill 1.1.9: `JavaTests` forwards `jvmId` from enclosing module (`zio.test.jvmId` honours `MILL_JVM_ID` override with no local definition), so test module need not duplicate override. Test module extending plain `ScalaTests` inherits none of sibling trait's `forkArgs`/`testForkGrouping`; mix isolation trait in explicitly. In nested `object test extends ScalaTests`, `moduleDir` is `<outer>/test`. `forkArgs` or `Task.Source` path for outer module's sources needs `moduleDir / os.up / ...` (verify with `./mill show <mod>.test.forkArgs`). Forked test JVMs see client's environment through daemon only if daemon was started with it. When test reads `sys.env`, run `./mill --no-server`. No per-module `reformat` task in 1.1.x; scope reformat with `./mill mill.scalalib.scalafmt.ScalafmtModule/reformatAll <module>.sources`. Join distinct goals with `+`. After `--no-server` runs, daemon-mode run in same workspace can fail with `SubprocessZincApi ... Connection refused` until `./mill shutdown`. Trait mixing `TestModule.Munit` (or any `TestModule`) with `ScalafixModule` must itself `override def defaultTask(): String = "testForked"`. `ScalafixModule extends ScalaModule`, so `JavaModule.defaultTask` and `TestModule.defaultTask` conflict in trait. Concrete `ScalaTests` object has no conflict: it inherits `JavaTests`' override (mill 1.1.9, mill-scalafix 0.6.2). Scalafix `OrganizeImports` may merge two imports of one package into braced multi-line group; scalafmt then wants it on one line. Run `checkFormatAll` after `fix`.

Separate unit and integration modules when resources or lifecycle differ. Pass tracked fixture paths instead of assuming repository-root working directory. Budget Mill jobs, test fork groups and framework threads separately. Isolate ports/files for concurrent tests.

For ordinary edit, run relevant suite and downstream boundary tests. For monorepo selective CI, prepare valid baseline and inspect affected selectors before running; see `mill-monorepo` if installed. Keep full checks where environment changes fall outside tracked graph. Do not rewrite or add tests merely to mirror build settings.
