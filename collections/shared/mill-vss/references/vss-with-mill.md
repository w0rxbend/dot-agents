# Keep VSS application guidance, choose Mill for the build

Official skill: `VirtusLab/scala-skill` at `direct-style-scala/skills/direct-style-scala`. Use-case chapters cover resources, background processes, configuration, compile-time dependency injection, code organization, inter-thread state, subprocesses, error handling, HTTP/auth/versioning/OpenAPI, SOAP, JSON/inputs, persistence/email/Kafka, HTTP tests and observability. Read chapter relevant to concrete application task; do not load every chapter automatically.

Website's starter prompt picks Scala CLI; installed skill's tooling/new-project chapter currently favors sbt. Local installation adds explicit preference section before upstream instructions: Mill for new projects, version-correct Mill compile/test/format tasks, available semantic tools when useful, existing-build preservation. Original chapters stay available for application guidance. Override changes tooling preference, not resource ownership or direct-style concurrency principles.

## Selecting a model

Simple server with dependencies/main class/tests only: declarative YAML can extend ScalaModule with explicit Scala/JDK versions and dependencies. Small support utility: Mill `.scala` script can carry `//|` configuration. Services with generated clients/OpenAPI resources, shared conventions, Kotlin/Java components or multiple deployment modules: programmable `build.mill` / `package.mill` normally supplies useful task graph. Explain required custom logic; do not treat every HTTP service as monorepo.

`assets/ox-app`: minimal Mill/Ox application with Scala 3.8.2, Ox 1.0.9 and Java 25 toolchain, versions checked against canonical metadata on 2026-10-04. Small startup/toolchain fixture, not a complete production server or a claim that every VSS component is installed. Add only libraries application features require.

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

Mill script headers use `//|`, not Scala CLI `//> using`. Do not leave Scala CLI directives in file and claim Mill honors them. Transfer all directives, including resource paths/test settings/Java options. Remove or document unused ones after verified migration.

Fresh project: commit pinned Mill bootstrap launcher. Use stable Mill 1.1.10 unless user/project needs another version. Minimal fixture pins Java 25 patch release; for real service, choose currently available managed distribution/patch and deployment minimum. Set useful supported Scala warnings, configure Scala 3 formatting. Do not let these service defaults needlessly raise neutral shared library's runtime minimum.

## HTTP and starter conversion

Synchronous Tapir: use supported direct-style server integration, such as `tapir-netty-server-sync`, plus only required JSON/documentation/testing modules. Verify dependency versions and API in relevant upstream chapter. Checked canonical metadata showed Tapir sync 1.13.32 at research time. Do not mix unrelated Tapir versions in one module family.

Do not assume Adopt Tapir supports `Mill` builder field without checking its current schema/API. If chosen supported starter emits sbt/Scala CLI, translate its source/dependency/test/resource configuration into Mill, keep generated endpoint/server logic, then verify. Documentation request or skills installation is not a request to create or run new external starter project.

Real HTTP task: test in-process endpoint behavior with supported direct-style tests. Then start server with owned lifetime, finite readiness timeout, chosen local port and cleanup. Verify documentation endpoints only when enabled. Package resources and OpenAPI metadata through tracked tasks so assembly works outside source checkout. Put code generation in separate upstream task/module when it would otherwise create compile cycle.

## Concurrency and mixed-language boundaries

Preserve structured Ox scopes and resource ownership from official use-case chapters. Bridge foreign asynchronous/blocking APIs deliberately. Putting Java/Kotlin libraries in Mill graph does not by itself make them follow Ox lifetime rules. Keep internal Scala ADTs/opaque types; expose intentional JVM-friendly interface where Java/Kotlin consumers need one. VSS direct-style preference covers requested VSS application, not automatic migration of every existing Scala service.

## Restore on another machine

Public dot-agents repo supplies its own Mill skills plus installer that downloads official VSS skill from pinned upstream commit, then applies local preference section. Upstream redistribution permission not established, so upstream text is not vendored into public snapshot. For exact command and verified provenance, read repo's VSS install documentation. Provider plugins/semantic tools are separate optional installations; skill file does not fabricate them.

Sources: [VSS stack and starter prompt](https://vss.virtuslab.com/llms.txt), [official skill](https://github.com/VirtusLab/scala-skill), [Scala models](https://mill-build.org/mill/1.1.x/scalalib/intro.html), [Scala configuration](https://mill-build.org/mill/scalalib/module-config.html), [Mill ScalaFmt](https://mill-build.org/mill/scalalib/linting.html), [canonical Ox metadata](https://repo.maven.apache.org/maven2/com/softwaremill/ox/core_3/maven-metadata.xml), [canonical Tapir metadata](https://repo.maven.apache.org/maven2/com/softwaremill/sttp/tapir/tapir-netty-server-sync_3/maven-metadata.xml).
