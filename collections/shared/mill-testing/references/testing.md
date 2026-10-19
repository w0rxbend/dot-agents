# Frameworks, discovery, and suite boundaries

A nested test module extends the enclosing language tests trait so it compiles in the correct source layout and against production code. It then mixes in a framework trait or supplies `testFramework` plus the required libraries. For Scala uTest, the tested mixed template uses `ScalaTests`, `mvn"com.lihaoyi::utest:0.9.1"`, and `utest.runner.Framework`. Java/Kotlin JUnit 5 needs the actual JUnit engine and a compatible JVM test-interface runner, not only assertion classes on the classpath.

Mill supports common Scala runners such as uTest, MUnit, ScalaTest, Specs2, Weaver, and ZIO Test along with JUnit/TestNG integrations. Preserve a project's selected stack; an Ox/Tapir VSS application does not imply rewriting a requested ZIO application's tests. Kotlin Kotest runs through its supported JUnit/platform integration; choose runner coordinates matching the Kotlin/Kotest version. In a mixed build, `mill.javalib.TestModule.Junit5` and `mill.scalalib.TestModule.Utest` make intent clear.

## Running and selecting

Use `./mill service.test` for the default test command and `./mill service.test.testOnly 'example.ServiceTests'` for selected classes when supported by the framework. Additional case filtering is framework-specific; inspect help and pass arguments deliberately rather than copying another framework's syntax. `testForked` is an explicit forked execution path. Resolve the selector when a nested module/default task is unclear.

Inspect discovered test classes and result counts. Migration can retain compiling tests but lose the runner, annotations, naming conventions, or engine dependency. Add an intentionally failing assertion temporarily in an isolated test fixture when verifying runner behavior if discovery evidence is uncertain, then restore it. Prefer observable suite execution over tests that only assert a `testFramework` string exists.

## Dependencies and fixtures

Tests inherit their production parent through language tests traits. Additional libraries go in their `mvnDeps`. Extend test `moduleDeps` with `super.moduleDeps ++ Seq(testSupport)` to retain defaults when needed. Another module's tests can supply fixtures, but a dedicated fixture library is easier to reason about when several teams reuse helpers. Executing those helpers does not mean the other suite should run as a prerequisite unless explicitly designed that way.

Unit fixtures should be tracked sources/resources. A file assumed to live in the checkout root may fail under Mill test sandboxing. Model it through a source task and pass the absolute returned path in `forkEnv` or test configuration, or package it as a classpath resource. Do not disable sandboxing for all tests because one suite's working-directory assumption is wrong.

Integration modules need owned lifecycle: start a service/container for the suite, discover or allocate a unique port, wait for readiness with a finite timeout, and clean up on failure. Share a fixture only with clear synchronization and lifetime. Environment-dependent tests may need full CI runs even if source-task selective execution excludes them.

## Forks and concurrency

Mill can parallelize independent tasks. `testParallelism`, `testForkGrouping`, and framework-level threads control different layers. `testForkGrouping = discoveredTestClasses().grouped(n).toSeq` trades process startup cost against isolation and memory; do not choose one class per process automatically for thousands of small tests. Group stateful/flaky suites deliberately and investigate shared mutable state rather than merely serializing the entire build.

A runner with eight Mill jobs and several test forks per module can exceed memory/database connection budgets even if each knob looks modest. Measure peak usage, choose explicit CI limits, and retain test reports. Batch-framework options are version/framework-specific; verify the current Java testing API before enabling them throughout a Scala/Kotlin repository.

## Selective testing and coverage

Affected tests must follow the dependency graph and a prepared baseline. A Kotlin library used by a Scala service should select the service suite after changing its input; a separate module should remain unaffected. Changes to a shared generator, runtime policy, or fixture should propagate to all real consumers. Failure to select a real consumer points to a missing graph input, not a reason to add a directory-name filter.

Coverage is a distinct instrumented workflow. Scoverage is Scala-specific; Kover integrates Kotlin; Java coverage typically uses its supported tool/plugin, and mixed languages require compatible instrumentation/report aggregation. Exclude generated sources where the coverage policy justifies it and avoid interpreting aggregate percentages without module ownership. Use the linting references for compatibility/coverage wiring.

Sources: [Scala testing](https://mill-build.org/mill/scalalib/testing.html), [Java testing](https://mill-build.org/mill/javalib/testing.html), [Kotlin testing](https://mill-build.org/mill/kotlinlib/testing.html), [selective execution](https://mill-build.org/mill/large/selective-execution.html), [sandboxing](https://mill-build.org/mill/depth/sandboxing.html).
