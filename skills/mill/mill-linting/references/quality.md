# Formatting, static checks, coverage, and compatibility

## Scala

ScalaFmt is built in. With pinned `.scalafmt.conf`: format via `./mill mill.scalalib.scalafmt/`, check via `./mill mill.scalalib.scalafmt/checkFormatAll`. Scala 3/braceless application code: set `runner.dialect = scala3`. Docs `scala213` example is not a universal setting. Module-scoped formatting can select sources. Quote selectors and check command signature before passing mixed-language source lists.

Scalafix needs compatible integration such as `com.goyeau.mill.scalafix.ScalafixModule`, imported into build classpath. Configure rules in `.scalafix.conf`. Semantic rules may need SemanticDB and compiler support; syntactic and semantic workflows differ. Verify plugin Mill binary suffix and Scala/compiler compatibility before adopting docs coordinate. `__.fix` rewrites files; do not assume it is CI check mode. Inspect plugin options; use its non-writing mode where available.

Acyclic docs configure a Scala 2 full-version plugin through compiler/compile dependencies and options. Acyclic detects source-file cycles within one module. It does not replace acyclic inter-module design. Do not apply that Scala 2 plugin to Scala 3 without verified support. MiMa/binary compatibility checks also need released baseline artifact and correct Scala/platform naming.

VSS Scala 3 modules: keep useful warnings such as `-Wunused:all`, `-Wvalue-discard`, `-Wnonunit-statement` where chosen compiler supports them. Tune build-definition code separately. Fix warnings at source; suppress only in narrow, explained cases. Treat upgrade that changes warning behavior as convention change affecting consumers.

## Java

Current docs: `./mill mill.javalib.palantirformat/` is built-in Palantir formatting path. Spotless orchestrates multiple formats/file groups. ErrorProne: mix `mill.javalib.errorprone.ErrorProneModule` into Java module. Checkstyle and PMD have own modules/configuration. ErrorProne is compiler integration; validate JDK and flags before applying it to all module families.

Keep warning policy deliberate. Docs show `-XepAllErrorsAsWarnings` as illustration, not necessarily desired CI policy. Checkstyle needs owned configuration and relevant source roots. Do not blindly run Java analyzers on generated code or Kotlin source files. Revapi can compare Java API against released artifact; define compatibility baseline and expected break policy.

## Kotlin

KtFmt: `mill.kotlinlib.ktfmt/` or module's `KtfmtModule`. Documented `ktfmt --format=false` checks without writing. KtLint: `KtlintModule`, `ktlint --check true` for failing check, `--format true` for repairs. Some defaults warn without failing. Report presence does not prove CI gate rejects violations.

Detekt needs `mill.kotlinlib.detekt.DetektModule`, not ErrorProne. Current docs prose has copy/paste reference to ErrorProne; YAML example correctly selects Detekt. Use module/API as evidence. Configure baseline only as reviewed gradual-adoption policy, not to suppress newly introduced problems. Rules requiring type resolution need matching Kotlin compiler/plugin versions.

Kover supplies Kotlin coverage workflows. Mixed JVM build may combine Java/Kotlin bytecode in its instrumentation boundary. Verify aggregation and class exclusions; do not assume Scoverage and Kover reports are directly interchangeable.

## Repository-wide policy

Version-control formatter versions and rules. Select only intended source/file groups. Spotless supports multiple languages and ratcheting against a baseline. Ratcheting can help established repositories adopt formatting without sweeping unrelated rewrites. It needs defined revision and CI policy so changed files get checked consistently.

Expose documented local fix workflow and separate CI check workflow. Let contributors run same checks. Prefer targeted changes when working on one module. Fixes must not modify generated sources whose task output would be regenerated, vendor code, or published examples with separate provenance.

Scoverage needs instrumented Scala module plus its tests/report aggregation. Its compiler support constrains versions. Aggregate by meaningful module families; publish reports only as requested. Compatibility checks use actual previous artifacts: MiMa for supported Scala binaries, Revapi for Java APIs, suitable verified approach for Kotlin public ABI. API compatibility and coverage answer different questions than test assertions and lint rules.

Sources: [Scala linting](https://mill-build.org/mill/scalalib/linting.html), [Java linting](https://mill-build.org/mill/javalib/linting.html), [Kotlin linting](https://mill-build.org/mill/kotlinlib/linting.html), [Scoverage](https://mill-build.org/mill/contrib/scoverage.html), [Java publishing/API compatibility](https://mill-build.org/mill/javalib/publishing.html), [third-party plugins](https://mill-build.org/mill/extending/thirdparty-plugins.html).
