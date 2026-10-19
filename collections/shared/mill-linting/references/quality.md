# Formatting, static checks, coverage, and compatibility

## Scala

ScalaFmt is built in. With a pinned `.scalafmt.conf`, use `./mill mill.scalalib.scalafmt/` to format and `./mill mill.scalalib.scalafmt/checkFormatAll` to check. Set `runner.dialect = scala3` for Scala 3/braceless application code; a documented example using `scala213` describes its example, not a universal setting. Module-scoped formatting can select sources; quote selectors and discover the command signature before feeding a mixed-language source list.

Scalafix requires a compatible integration such as `com.goyeau.mill.scalafix.ScalafixModule`, imported into the build's classpath. Configure the actual rules in `.scalafix.conf`. Semantic rules may need SemanticDB and compiler support; syntactic and semantic workflows are distinct. Verify the plugin's Mill binary suffix and Scala/compiler compatibility before adopting the docs' coordinate. `__.fix` is a rewriting command, so do not assume it is the CI check mode; inspect plugin options and use its non-writing mode where available.

Acyclic's documented configuration uses compiler/compile dependencies and options for a Scala 2 full-version plugin. It detects source-file cycles within a module; it does not replace an acyclic inter-module design. Do not apply that Scala 2 plugin to Scala 3 without verified support. MiMa/binary compatibility checks similarly require the released baseline artifact and correct Scala/platform naming.

For VSS Scala 3 modules, preserve useful warnings such as `-Wunused:all`, `-Wvalue-discard`, and `-Wnonunit-statement` where supported by the chosen compiler; tune build-definition code separately. Fix warnings at source and reserve suppressions for narrow explained cases. Treat an upgrade that changes warning behavior as a convention change affecting consumers.

## Java

`./mill mill.javalib.palantirformat/` is the built-in Palantir formatting path in current docs. Spotless offers multi-format/file-group orchestration. ErrorProne integrates by mixing `mill.javalib.errorprone.ErrorProneModule` into the Java module; Checkstyle and PMD have their own modules/configuration. ErrorProne is a compiler integration, so validate the JDK and flags before applying it to all module families.

Keep warning policy deliberate. The docs show `-XepAllErrorsAsWarnings` for illustration; that is not necessarily the desired CI policy. Checkstyle requires an owned configuration and relevant source roots; do not blindly run Java analyzers against generated code or Kotlin source files. Revapi support can compare a Java API against a released artifact; define the compatibility baseline and expected break policy.

## Kotlin

KtFmt is available through `mill.kotlinlib.ktfmt/` or a module's `KtfmtModule`; documented `ktfmt --format=false` checks without writing. KtLint has `KtlintModule`, with `ktlint --check true` for a failing check and `--format true` for repairs. Some defaults warn without failing, so a report's presence is not proof the CI gate rejects violations.

Detekt requires `mill.kotlinlib.detekt.DetektModule`, not ErrorProne. Current docs contain a prose copy/paste reference to ErrorProne while the YAML example correctly selects Detekt; use the module/API as evidence. Configure a baseline only as a reviewed gradual-adoption policy, not to suppress newly introduced problems. Match Kotlin compiler/plugin versions for rules requiring type resolution.

Kover supplies Kotlin coverage workflows. A mixed JVM build may combine Java/Kotlin bytecode in its instrumentation boundary; verify aggregation and class exclusions rather than assuming Scoverage and Kover reports are directly interchangeable.

## Repository-wide policy

Keep formatter versions and rules in version control. Select only intended source/file groups. Spotless supports multiple languages and ratcheting against a baseline, which can help an established repository adopt formatting without a sweeping unrelated rewrite. Ratcheting requires a defined revision and CI policy so changed files are consistently checked.

Expose a documented local fix workflow and a separate CI check workflow; make contributors able to run the same checks. Prefer targeted changes when working on one module. Ensure fixes do not modify generated sources whose task output would be regenerated, vendor code, or published examples with separate provenance.

Scoverage requires an instrumented Scala module and its corresponding tests/report aggregation; its compiler support constrains versions. Aggregate by meaningful module families and publish reports only as requested. Compatibility checks use actual previous artifacts: MiMa for supported Scala binaries, Revapi for Java APIs, and a suitable verified approach for Kotlin public ABI. API compatibility and coverage answer different questions from test assertions and lint rules.

Sources: [Scala linting](https://mill-build.org/mill/scalalib/linting.html), [Java linting](https://mill-build.org/mill/javalib/linting.html), [Kotlin linting](https://mill-build.org/mill/kotlinlib/linting.html), [Scoverage](https://mill-build.org/mill/contrib/scoverage.html), [Java publishing/API compatibility](https://mill-build.org/mill/javalib/publishing.html), [third-party plugins](https://mill-build.org/mill/extending/thirdparty-plugins.html).
