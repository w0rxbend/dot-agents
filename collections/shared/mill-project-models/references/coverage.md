# Mill documentation coverage and routing

Research date: 2026-10-04. Stable tested baseline: **1.1.10**. Unversioned documentation: **1.3.0-M1**. All three Scala project models are supported on the tested stable baseline. Match each real project's APIs and version before adapting another page.

The pack contains 14 focused skills with detailed task-specific references. It emphasizes JVM multimodule projects and monorepos; the platform pages are researched guidance, not a claim of executed Android/Native/Spark/Python/JS validation.

| Skill | Main responsibility |
| --- | --- |
| [mill-project-models](../../mill-project-models/SKILL.md) | Three project models, decisions, comparisons, and source routing |
| [mill-cli-and-ide](../../mill-cli-and-ide/SKILL.md) | Launcher, CLI flags/queries/headers, IDE/BSP, and migration |
| [mill-jvm-modules](../../mill-jvm-modules/SKILL.md) | Scala + Java + Kotlin graph, interop, and module configuration |
| [mill-dependencies-and-toolchains](../../mill-dependencies-and-toolchains/SKILL.md) | Dependency scopes, BOMs, versions, compiler/JVM policy |
| [mill-build-logic](../../mill-build-logic/SKILL.md) | Tasks, code generation, resources, output ownership |
| [mill-monorepo](../../mill-monorepo/SKILL.md) | Multimodule architecture, conventions, multifile builds, selective CI |
| [mill-testing](../../mill-testing/SKILL.md) | Frameworks, discovery, fixtures, test grouping, integration suites |
| [mill-linting](../../mill-linting/SKILL.md) | Format/check workflows, analyzers, coverage, compatibility |
| [mill-packaging-publishing](../../mill-packaging-publishing/SKILL.md) | Jars, assemblies, native-image, containers, multimodule releases |
| [mill-scala-platforms](../../mill-scala-platforms/SKILL.md) | Scala.js/Native, web assets, Spark, cross-platform builds |
| [mill-plugins](../../mill-plugins/SKILL.md) | Imports, plugin compatibility, workers, meta-build, language extensions |
| [mill-performance](../../mill-performance/SKILL.md) | Evaluation, caching, parallelism, daemon, sandbox, profiles |
| [mill-polyglot](../../mill-polyglot/SKILL.md) | Python, JavaScript/TypeScript, Groovy, experimental Android |
| [mill-vss](../../mill-vss/SKILL.md) | VirtusLab direct-style Scala with Mill preferred |

## User-requested areas

| Documentation area | Guidance and decisions |
| --- | --- |
| Declarative / single-file / programmable Scala | mill-project-models explains when each fits, transitions, and stable runnable assets |
| Java / Scala / Kotlin builds and module configuration | mill-jvm-modules covers source layout, interop, tests, compilers, and a tested three-language DAG |
| Dependencies and JVM versions | mill-dependencies-and-toolchains covers scope, BOMs, cross artifacts, private repos, and runtime/target separation |
| Testing and linting Scala (plus Java/Kotlin) | mill-testing and mill-linting cover framework discovery, suite grouping, fix/check modes, and quality gates |
| Packaging/publishing Scala (plus Java/Kotlin) | mill-packaging-publishing covers runtime artifacts, POMs, coordinates, signing, staging, and release scope |
| Build/web/Native/Spark examples | mill-project-models ecosystem reference and mill-scala-platforms cover real-project patterns and platform constraints |
| Why Mill / Maven / Gradle / performance comparisons | mill-project-models and mill-performance explain benefits, tradeoffs, and benchmark limits |
| CLI / installation / IDE / flags / built-ins / query / header | mill-cli-and-ide covers version pins, commands, BSP, selectors, and header scopes |
| Migration / automated import | mill-cli-and-ide migration reference covers scaffold generation, limits, and behavioral parity |
| Tasks / modules / out / cross / bundled libraries | mill-build-logic, mill-monorepo, and mill-performance explain graph, ownership, reuse, and diagnostics |
| Large monorepos / selective / multifile / multilanguage / precompiled | mill-monorepo and mill-polyglot cover ownership, baselines, package discovery, typed edges, and experimental status |
| Import libraries / contrib / third-party / dynamic JVM / plugins / meta-build | mill-plugins covers mechanism selection, version compatibility, isolated workers, and real fixture testing |
| TypeScript and Python extension examples | mill-plugins distinguishes instructional implementations from built-in integrations |
| Android / Python / JavaScript / Groovy experimental support | mill-polyglot covers config, dependencies, tests, linting, packaging, SDK/IDE, and release constraints |
| Evaluation / caching / parallelism / processes / sandbox / design / why Scala | mill-performance explains each phase, failure evidence, and practical limits |
| API / changelog / talks and blog posts | mill-plugins and mill-project-models explain version lookup and historical-versus-current evidence |
| VirtusLab Scala Stack | mill-vss preserves direct-style/Ox/Tapir guidance while choosing Mill as this user's default |

## Official source map

The research fetched 132 primary-source pages/files, including stable-version checks. Redirect/alternate-root duplicates are omitted below. Each source has a primary skill; related skills link it where useful. The repository research manifest records URL, retrieval hash, and document title without copying the manual.

| Source | Primary skill |
| --- | --- |
| [Android Initial Setup](https://mill-build.org/mill/android/android-initial-setup.html) | mill-polyglot |
| [Linting Android Projects](https://mill-build.org/mill/android/android-linting.html) | mill-polyglot |
| [Android Native Example](https://mill-build.org/mill/android/android-native-example.html) | mill-polyglot |
| [Android Release Guide](https://mill-build.org/mill/android/android-release.html) | mill-polyglot |
| [Android Jetpack Compose](https://mill-build.org/mill/android/compose-samples.html) | mill-polyglot |
| [Android Hilt Sample](https://mill-build.org/mill/android/hilt-sample.html) | mill-polyglot |
| [Android IDE Support](https://mill-build.org/mill/android/ide.html) | mill-polyglot |
| [Android Java Projects](https://mill-build.org/mill/android/java.html) | mill-polyglot |
| [Koin Androidx Examples](https://mill-build.org/mill/android/koin_androidx_examples.html) | mill-polyglot |
| [Android Kotlin Projects](https://mill-build.org/mill/android/kotlin.html) | mill-polyglot |
| [Android Library Publishing](https://mill-build.org/mill/android/publishing.html) | mill-polyglot |
| [Android Scala Projects](https://mill-build.org/mill/android/scala.html) | mill-polyglot |
| [Build Header Config](https://mill-build.org/mill/cli/build-header.html) | mill-cli-and-ide |
| [Built-in Commands](https://mill-build.org/mill/cli/builtin-commands.html) | mill-cli-and-ide |
| [Mill Command-Line Flags](https://mill-build.org/mill/cli/flags.html) | mill-cli-and-ide |
| [Installation & IDE Setup](https://mill-build.org/mill/cli/installation-ide.html) | mill-cli-and-ide |
| [Task Query Syntax](https://mill-build.org/mill/cli/query-syntax.html) | mill-cli-and-ide |
| [Comparing Mill vs Gradle: Programmable Builds](https://mill-build.org/mill/comparisons/gradle.html) | mill-project-models |
| [Comparing Mill vs Maven: Declarative Builds](https://mill-build.org/mill/comparisons/maven.html) | mill-project-models |
| [Mill Build Performance](https://mill-build.org/mill/comparisons/performance.html) | mill-performance |
| [Artifactory](https://mill-build.org/mill/contrib/artifactory.html) | mill-packaging-publishing |
| [BuildInfo](https://mill-build.org/mill/contrib/buildinfo.html) | mill-build-logic |
| [Codeartifact](https://mill-build.org/mill/contrib/codeartifact.html) | mill-packaging-publishing |
| [Docker](https://mill-build.org/mill/contrib/docker.html) | mill-packaging-publishing |
| [Flyway](https://mill-build.org/mill/contrib/flyway.html) | mill-build-logic |
| [Gitlab](https://mill-build.org/mill/contrib/gitlab.html) | mill-packaging-publishing |
| [JMH](https://mill-build.org/mill/contrib/jmh.html) | mill-plugins |
| [Dependency Check](https://mill-build.org/mill/contrib/owaspdependencycheck.html) | mill-plugins |
| [Play Framework](https://mill-build.org/mill/contrib/playlib.html) | mill-build-logic |
| [Proguard](https://mill-build.org/mill/contrib/proguard.html) | mill-packaging-publishing |
| [Software Bill of Materials (SBOM)](https://mill-build.org/mill/contrib/sbom.html) | mill-plugins |
| [ScalaPB](https://mill-build.org/mill/contrib/scalapblib.html) | mill-build-logic |
| [Scoverage](https://mill-build.org/mill/contrib/scoverage.html) | mill-plugins |
| [Sonatype Central](https://mill-build.org/mill/contrib/sonatypecentral.html) | mill-packaging-publishing |
| [TestNG](https://mill-build.org/mill/contrib/testng.html) | mill-plugins |
| [Twirl](https://mill-build.org/mill/contrib/twirllib.html) | mill-build-logic |
| [Version file](https://mill-build.org/mill/contrib/versionfile.html) | mill-packaging-publishing |
| [Caching in Mill](https://mill-build.org/mill/depth/caching.html) | mill-performance |
| [Mill Design Principles](https://mill-build.org/mill/depth/design-principles.html) | mill-performance |
| [The Mill Evaluation Model](https://mill-build.org/mill/depth/evaluation-model.html) | mill-performance |
| [Parallelism in Mill](https://mill-build.org/mill/depth/parallelism.html) | mill-performance |
| [The Mill Process Architecture](https://mill-build.org/mill/depth/process-architecture.html) | mill-performance |
| [Mill Sandboxing](https://mill-build.org/mill/depth/sandboxing.html) | mill-performance |
| [Why does Mill use Scala?](https://mill-build.org/mill/depth/why-scala.html) | mill-performance |
| [Contrib Plugins](https://mill-build.org/mill/extending/contrib-plugins.html) | mill-plugins |
| [Example: Python Support](https://mill-build.org/mill/extending/example-python-support.html) | mill-plugins |
| [Example: Typescript Support](https://mill-build.org/mill/extending/example-typescript-support.html) | mill-plugins |
| [Import Libraries and Plugins](https://mill-build.org/mill/extending/import-mvn-plugins.html) | mill-plugins |
| [The Mill Meta-Build](https://mill-build.org/mill/extending/meta-build.html) | mill-plugins |
| [Running Dynamic JVM Code](https://mill-build.org/mill/extending/running-jvm-code.html) | mill-plugins |
| [Third-Party Plugins](https://mill-build.org/mill/extending/thirdparty-plugins.html) | mill-plugins |
| [Writing Mill Plugins](https://mill-build.org/mill/extending/writing-plugins.html) | mill-plugins |
| [Bundled Libraries](https://mill-build.org/mill/fundamentals/bundled-libraries.html) | mill-build-logic |
| [Managing JVM Versions](https://mill-build.org/mill/fundamentals/configuring-jvm-versions.html) | mill-dependencies-and-toolchains |
| [Cross Builds](https://mill-build.org/mill/fundamentals/cross-builds.html) | mill-monorepo |
| [Library Dependencies in Mill](https://mill-build.org/mill/fundamentals/library-deps.html) | mill-dependencies-and-toolchains |
| [Modules](https://mill-build.org/mill/fundamentals/modules.html) | mill-monorepo |
| [The Output Directory](https://mill-build.org/mill/fundamentals/out-dir.html) | mill-build-logic |
| [Tasks](https://mill-build.org/mill/fundamentals/tasks.html) | mill-build-logic |
| [Building Groovy with Mill](https://mill-build.org/mill/groovylib/intro.html) | mill-polyglot |
| [Mill: A Better Build Tool for Java, Scala, & Kotlin](https://mill-build.org/mill/index.html) | mill-project-models |
| [Java Build Examples](https://mill-build.org/mill/javalib/build-examples.html) | mill-jvm-modules |
| [Java Library Dependencies](https://mill-build.org/mill/javalib/dependencies.html) | mill-dependencies-and-toolchains |
| [Building Java with Mill](https://mill-build.org/mill/javalib/intro.html) | mill-jvm-modules |
| [Linting Java Projects](https://mill-build.org/mill/javalib/linting.html) | mill-linting |
| [Java Module Configuration](https://mill-build.org/mill/javalib/module-config.html) | mill-jvm-modules |
| [Packaging Java Projects](https://mill-build.org/mill/javalib/packaging.html) | mill-packaging-publishing |
| [Publishing Java Projects](https://mill-build.org/mill/javalib/publishing.html) | mill-packaging-publishing |
| [Java Single-File Scripts](https://mill-build.org/mill/javalib/script.html) | mill-jvm-modules |
| [Spring Boot Projects](https://mill-build.org/mill/javalib/spring-boot.html) | mill-jvm-modules |
| [Testing Java Projects](https://mill-build.org/mill/javalib/testing.html) | mill-testing |
| [Java Web Project Examples](https://mill-build.org/mill/javalib/web-examples.html) | mill-jvm-modules |
| [JavaScript Build Examples](https://mill-build.org/mill/javascriptlib/build-examples.html) | mill-polyglot |
| [Typescript Library Dependencies](https://mill-build.org/mill/javascriptlib/dependencies.html) | mill-polyglot |
| [Building Javascript with Mill](https://mill-build.org/mill/javascriptlib/intro.html) | mill-polyglot |
| [Linting Typescript Projects](https://mill-build.org/mill/javascriptlib/linting.html) | mill-polyglot |
| [Typescript Module Configuration](https://mill-build.org/mill/javascriptlib/module-config.html) | mill-polyglot |
| [Typescript Packaging & Publishing](https://mill-build.org/mill/javascriptlib/publishing.html) | mill-polyglot |
| [Testing Typescript Projects](https://mill-build.org/mill/javascriptlib/testing.html) | mill-polyglot |
| [Kotlin Library Dependencies](https://mill-build.org/mill/kotlinlib/dependencies.html) | mill-dependencies-and-toolchains |
| [Building Kotlin with Mill](https://mill-build.org/mill/kotlinlib/intro.html) | mill-jvm-modules |
| [Linting Kotlin Projects](https://mill-build.org/mill/kotlinlib/linting.html) | mill-linting |
| [Kotlin Module Configuration](https://mill-build.org/mill/kotlinlib/module-config.html) | mill-jvm-modules |
| [Packaging Kotlin Projects](https://mill-build.org/mill/kotlinlib/packaging.html) | mill-packaging-publishing |
| [Publishing Kotlin Projects](https://mill-build.org/mill/kotlinlib/publishing.html) | mill-packaging-publishing |
| [Kotlin Single-File Scripts](https://mill-build.org/mill/kotlinlib/script.html) | mill-jvm-modules |
| [Testing Kotlin Projects](https://mill-build.org/mill/kotlinlib/testing.html) | mill-testing |
| [Kotlin Web Project Examples](https://mill-build.org/mill/kotlinlib/web-examples.html) | mill-jvm-modules |
| [Large Builds and Monorepos](https://mill-build.org/mill/large/large.html) | mill-monorepo |
| [Multi-File Builds](https://mill-build.org/mill/large/multi-file-builds.html) | mill-monorepo |
| [Multi-Language Builds](https://mill-build.org/mill/large/multi-language-builds.html) | mill-polyglot |
| [Pre-Compiled Modules](https://mill-build.org/mill/large/pre-compiled-modules.html) | mill-monorepo |
| [Selective Test Execution](https://mill-build.org/mill/large/selective-execution.html) | mill-monorepo |
| [Automated Migration Tools](https://mill-build.org/mill/migrating/auto-migrating.html) | mill-cli-and-ide |
| [Migrating to Mill](https://mill-build.org/mill/migrating/migrating.html) | mill-cli-and-ide |
| [Python Library Dependencies](https://mill-build.org/mill/pythonlib/dependencies.html) | mill-polyglot |
| [Building Python with Mill](https://mill-build.org/mill/pythonlib/intro.html) | mill-polyglot |
| [Linting Python Projects](https://mill-build.org/mill/pythonlib/linting.html) | mill-polyglot |
| [Python Module Configuration](https://mill-build.org/mill/pythonlib/module-config.html) | mill-polyglot |
| [Python Packaging & Publishing](https://mill-build.org/mill/pythonlib/publishing.html) | mill-polyglot |
| [Testing Python Projects](https://mill-build.org/mill/pythonlib/testing.html) | mill-polyglot |
| [Python Web Project Examples](https://mill-build.org/mill/pythonlib/web-examples.html) | mill-polyglot |
| [Talks & Blog Posts](https://mill-build.org/mill/reference/talks-blog-posts.html) | mill-project-models |
| [Scala Build Examples](https://mill-build.org/mill/scalalib/build-examples.html) | mill-project-models |
| [Scala Library Dependencies](https://mill-build.org/mill/scalalib/dependencies.html) | mill-dependencies-and-toolchains |
| [Building Scala with Mill](https://mill-build.org/mill/scalalib/intro.html) | mill-project-models |
| [Linting Scala Projects](https://mill-build.org/mill/scalalib/linting.html) | mill-linting |
| [Scala Module Configuration](https://mill-build.org/mill/scalalib/module-config.html) | mill-jvm-modules |
| [Scala Native Examples](https://mill-build.org/mill/scalalib/native-examples.html) | mill-scala-platforms |
| [Packaging Scala Projects](https://mill-build.org/mill/scalalib/packaging.html) | mill-packaging-publishing |
| [Publishing Scala Projects](https://mill-build.org/mill/scalalib/publishing.html) | mill-packaging-publishing |
| [Scala Single-File Scripts](https://mill-build.org/mill/scalalib/script.html) | mill-project-models |
| [Spark Examples](https://mill-build.org/mill/scalalib/spark.html) | mill-scala-platforms |
| [Testing Scala Projects](https://mill-build.org/mill/scalalib/testing.html) | mill-testing |
| [Scala Web Project Examples](https://mill-build.org/mill/scalalib/web-examples.html) | mill-scala-platforms |
| [Building Scala with Mill](https://mill-build.org/mill/1.1.x/scalalib/intro.html) | mill-project-models |
| [Scala Single-File Scripts](https://mill-build.org/mill/1.1.x/scalalib/script.html) | mill-project-models |
| [Building Kotlin with Mill](https://mill-build.org/mill/1.1.x/kotlinlib/intro.html) | mill-jvm-modules |
| [Building Java with Mill](https://mill-build.org/mill/1.1.x/javalib/intro.html) | mill-jvm-modules |
| [Tasks](https://mill-build.org/mill/1.1.x/fundamentals/tasks.html) | mill-build-logic |
| [Multi-File Builds](https://mill-build.org/mill/1.1.x/large/multi-file-builds.html) | mill-monorepo |
| [Selective Test Execution](https://mill-build.org/mill/1.1.x/large/selective-execution.html) | mill-monorepo |
| [Linting Scala Projects](https://mill-build.org/mill/1.1.x/scalalib/linting.html) | mill-linting |
| [Build Header Config](https://mill-build.org/mill/1.1.x/cli/build-header.html) | mill-cli-and-ide |
| [Installation & IDE Setup](https://mill-build.org/mill/1.1.x/cli/installation-ide.html) | mill-cli-and-ide |
| [mill](https://mill-build.org/api/latest/mill.html) | mill-plugins |
| [llms.txt](https://vss.virtuslab.com/llms.txt) | mill-vss |
| [LICENSE](https://raw.githubusercontent.com/com-lihaoyi/mill/1.1.10/LICENSE) | mill-project-models |
| [changelog.adoc](https://raw.githubusercontent.com/com-lihaoyi/mill/main/changelog.adoc) | mill-plugins |
