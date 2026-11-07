# Frameworks, discovery, and suite boundaries

Nested test module extends enclosing language tests trait, so it compiles in correct source layout and against production code. Then it mixes in framework trait or supplies `testFramework` plus required libraries. Scala uTest: tested mixed template uses `ScalaTests`, `mvn"com.lihaoyi::utest:0.9.1"` and `utest.runner.Framework`. Java/Kotlin JUnit 5 needs actual JUnit engine and compatible JVM test-interface runner, not only assertion classes on classpath.

Mill supports common Scala runners such as uTest, MUnit, ScalaTest, Specs2, Weaver and ZIO Test, plus JUnit/TestNG integrations. Keep project's selected stack: Ox/Tapir VSS application does not imply rewriting requested ZIO application's tests. Kotlin Kotest runs through its supported JUnit/platform integration; pick runner coordinates matching Kotlin/Kotest version. In mixed build, `mill.javalib.TestModule.Junit5` and `mill.scalalib.TestModule.Utest` make intent clear.

## Running and selecting

`./mill service.test` runs default test command. `./mill service.test.testOnly 'example.ServiceTests'` selects classes when framework supports it. Extra case filtering is framework-specific: inspect help, pass arguments deliberately, do not copy another framework's syntax. `testForked` is explicit forked execution path. Resolve selector when nested module/default task is unclear.

Inspect discovered test classes and result counts. Migration can keep tests compiling but lose runner, annotations, naming conventions or engine dependency. If discovery evidence is uncertain, temporarily add intentionally failing assertion in isolated test fixture to verify runner behavior, then restore it. Prefer observable suite execution over tests that only assert a `testFramework` string exists.

## Dependencies and fixtures

Tests inherit production parent through language tests traits. Extra test libraries go in test module's `mvnDeps`. Extend test `moduleDeps` with `super.moduleDeps ++ Seq(testSupport)` to keep defaults when needed. Another module's tests can supply fixtures, but dedicated fixture library is clearer when several teams reuse helpers. Running those helpers does not make other suite a prerequisite, unless explicitly designed that way.

Keep unit fixtures as tracked sources/resources. File assumed in checkout root may fail under Mill test sandboxing. Model it through source task and pass returned absolute path in `forkEnv` or test configuration, or package it as classpath resource. Do not disable sandboxing for all tests because one suite's working-directory assumption is wrong.

Integration modules need owned lifecycle: start service/container for suite, discover or allocate unique port, wait for readiness with finite timeout, clean up on failure. Share fixture only with clear synchronization and lifetime. Environment-dependent tests may need full CI runs even if source-task selective execution excludes them.

## Forks and concurrency

Mill can parallelize independent tasks. `testParallelism`, `testForkGrouping` and framework-level threads control different layers. `testForkGrouping = discoveredTestClasses().grouped(n).toSeq` trades process startup cost against isolation and memory. For thousands of small tests, do not choose one class per process automatically. Group stateful/flaky suites deliberately. Investigate shared mutable state rather than merely serializing entire build.

Runner with eight Mill jobs and several test forks per module can exceed memory/database connection budgets, even if each knob looks modest. Measure peak usage, set explicit CI limits, keep test reports. Batch-framework options are version/framework-specific; verify current Java testing API before enabling them across Scala/Kotlin repository.

## Selective testing and coverage

Affected tests must follow dependency graph and prepared baseline. Changing input of Kotlin library used by Scala service should select service suite; separate module should stay unaffected. Changes to shared generator, runtime policy or fixture should reach all real consumers. Real consumer not selected means missing graph input, not reason to add directory-name filter.

Coverage is distinct instrumented workflow. Scoverage is Scala-specific; Kover integrates Kotlin; Java coverage typically uses its supported tool/plugin. Mixed languages need compatible instrumentation/report aggregation. Exclude generated sources where coverage policy justifies it. Avoid interpreting aggregate percentages without module ownership. Use linting references for compatibility/coverage wiring.

Sources: [Scala testing](https://mill-build.org/mill/scalalib/testing.html), [Java testing](https://mill-build.org/mill/javalib/testing.html), [Kotlin testing](https://mill-build.org/mill/kotlinlib/testing.html), [selective execution](https://mill-build.org/mill/large/selective-execution.html), [sandboxing](https://mill-build.org/mill/depth/sandboxing.html).
