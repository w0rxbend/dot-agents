# Keep VSS application guidance, choose Mill for the build

The official skill is `VirtusLab/scala-skill` at `direct-style-scala/skills/direct-style-scala`. It includes use-case chapters for resources, background processes, configuration, compile-time dependency injection, code organization, inter-thread state, subprocesses, error handling, HTTP/auth/versioning/OpenAPI, SOAP, JSON/inputs, persistence/email/Kafka, HTTP tests, and observability. Read the chapter relevant to the concrete application task; do not load every chapter automatically.

The website's starter prompt selects Scala CLI, while the installed skill's tooling/new-project chapter currently favors sbt. The local installation adds an explicit preference section before upstream instructions: Mill for new projects, version-correct Mill compile/test/format tasks, available semantic tools when useful, and existing-build preservation. The original chapters remain available for application guidance. That override changes tooling preference, not resource ownership or direct-style concurrency principles.

## Selecting a model

For a simple server with dependencies/main class/tests only, declarative YAML can extend ScalaModule with explicit Scala/JDK versions and dependencies. For a small support utility, a Mill `.scala` script can carry `//|` configuration. For services with generated clients/OpenAPI resources, shared conventions, Kotlin/Java components, or multiple deployment modules, programmable `build.mill` / `package.mill` normally supplies the useful task graph. Explain the required custom logic rather than treating every HTTP service as a monorepo.

`assets/ox-app` is a minimal Mill/Ox application with Scala 3.8.2, Ox 1.0.9, and a Java 25 toolchain. These versions were checked against canonical metadata on 2026-10-04. It is a small startup/toolchain fixture, not a complete production server or a claim that every VSS component is installed. Add only the libraries required by the application's features.

## Translate build configuration

| Source example | Mill module equivalent |
| --- | --- |
| Scala CLI `//> using scala VERSION` | `scalaVersion` |
| Scala CLI `//> using jvm VERSION` | module `jvmVersion`; choose build `mill-jvm-version` separately |
| Scala CLI dependency or sbt `group %% artifact % version` | `mvn"group::artifact:version"` in module `mvnDeps` |
| sbt Java-style `%` artifact | `mvn"group:artifact:version"` |
| Scala compiler options | `scalacOptions` |
| Test dependency/scope | Nested ScalaTests module's dependencies/framework |
| JVM arguments/env | `forkArgs` / `forkEnv` |
| `src/main/scala` scaffold | `SbtModule` / `SbtTests` or deliberately adapted tracked source roots |
| sbt-scalafmt | Mill's ScalaFmt commands and Scala 3 `.scalafmt.conf` |

Mill script headers use `//|`, not Scala CLI `//> using`. Do not leave Scala CLI directives in a file and claim Mill will honor them. Transfer all directives, including resource paths/test settings/Java options; remove or document unused ones after verified migration.

For a fresh project, commit a pinned Mill bootstrap launcher. Use stable Mill 1.1.10 unless the user/project needs another version. The minimal fixture pins a Java 25 patch release; choose a currently available managed distribution/patch and deployment minimum for a real service. Set useful supported Scala warnings and configure Scala 3 formatting. Keep these service defaults from unnecessarily raising a neutral shared library's runtime minimum.

## HTTP and starter conversion

For synchronous Tapir use the supported direct-style server integration, such as `tapir-netty-server-sync`, plus the JSON/documentation/testing modules actually required. Verify the dependency versions and API from the relevant upstream chapter. The checked canonical metadata reported Tapir sync 1.13.32 at research time; don't mix unrelated Tapir versions in one module family.

Do not assume Adopt Tapir supports a `Mill` builder field without checking its current schema/API. If a chosen supported starter emits sbt/Scala CLI, translate its source/dependency/test/resource configuration into Mill, preserve the generated endpoint/server logic, then verify it. A documentation request or skills installation is not a request to create or run a new external starter project.

For a real HTTP task, test in-process endpoint behavior with the supported direct-style tests, then start the server with an owned lifetime, finite readiness timeout, chosen local port, and cleanup. Verify documentation endpoints only when enabled. Package resources and OpenAPI metadata through tracked tasks so an assembly works outside the source checkout. Code generation belongs in a separate upstream task/module when it would otherwise create a compile cycle.

## Concurrency and mixed-language boundaries

Preserve structured Ox scopes and resource ownership from the official use-case chapters. Bridge foreign asynchronous/blocking APIs deliberately; using Java/Kotlin libraries in a Mill graph does not by itself make them follow Ox lifetime rules. Keep internal Scala ADTs/opaque types while exposing an intentional JVM-friendly interface where Java/Kotlin consumers need one. VSS's direct-style preference applies to the requested VSS application, not an automatic migration of every existing Scala service.

## Restore on another machine

The public dot-agents repo supplies its own Mill skills and an installer that downloads the official VSS skill from a pinned upstream commit, then applies the local preference section. Upstream redistribution permission has not been established, so its text is not vendored into the public snapshot. Read the repo's VSS install documentation for the exact command and verified provenance. Provider plugins/semantic tools are separate optional installations; a skill file does not fabricate those tools.

Sources: [VSS stack and starter prompt](https://vss.virtuslab.com/llms.txt), [official skill](https://github.com/VirtusLab/scala-skill), [Scala models](https://mill-build.org/mill/1.1.x/scalalib/intro.html), [Scala configuration](https://mill-build.org/mill/scalalib/module-config.html), [Mill ScalaFmt](https://mill-build.org/mill/scalalib/linting.html), [canonical Ox metadata](https://repo.maven.apache.org/maven2/com/softwaremill/ox/core_3/maven-metadata.xml), [canonical Tapir metadata](https://repo.maven.apache.org/maven2/com/softwaremill/sttp/tapir/tapir-netty-server-sync_3/maven-metadata.xml).
