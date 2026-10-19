# Choosing and validating artifacts

| Artifact | Useful for | Verify |
| --- | --- | --- |
| `jar` | Library consumption | Classes/resources, stable API, dependency metadata supplied separately |
| `assembly` | JVM executable delivery | Main class, runtime deps, merged services/config, actual `java -jar` behavior |
| `launcher` / classpath distribution | Startup with separate dependency jars | Relative paths and fresh-machine layout |
| Framework repackage | Framework-specific nested-jar executable | Loader, BOOT-INF/layout rules, framework tooling compatibility |
| GraalVM native image | Native executable | Reflection/resources/dynamic initialization and target OS/CPU |
| jlink / jpackage | Runtime/app installation bundle | Module/JDK metadata, platform-specific installers and runtime image |
| Docker/Jib image | Containerized application | Runtime/base image/architecture, entrypoint, ports, user, health behavior |

Use `./mill show app.assembly` to evaluate and find the artifact rather than hardcoding its internal path in another task. The tested mixed-JVM application can be assembled and run with Java 21 or a compatible newer runtime; its runtime classpath includes Scala and Kotlin libraries. Verify the actual shipped jar because `run` executes with Mill's configured classpath and fork settings.

Assemblies flatten dependencies. Configure `assemblyRules` for known duplicate/resource requirements rather than excluding every duplicate. Service-loader entries and framework configuration often require merging. Check that signatures/metadata do not invalidate the resulting jar. A Bash/Batch script prefix can support direct execution, but Spark submit and other consumers may expect a plain jar; disable the prefix deliberately where required.

A thin library jar normally should not embed all transitive dependencies. Its POM/metadata communicates those dependencies, including compile-only/runtime distinctions. Repackaging is a different layout from shading/flattening; framework boot loaders and classpath discovery need the correct module/tool integration. Java/Scala/Kotlin packaging pages describe shared JVM concepts but imports/package aliases can differ, so use the version's API.

Native-image requires a compatible GraalVM and a tested reachability configuration. Java reflection, service loading, dynamic proxies, resources, and runtime classloading can behave differently. Scala Native compiles Scala to a different native toolchain and has different library availability; it is not interchangeable with GraalVM converting a JVM application. Native artifacts and installers are OS/architecture-specific even if the Mill build file is shared.

The contrib Docker integration can support Jib and classic Dockerfile workflows. Choose one based on layering/build customization requirements. Pin a maintained base image and platform; the docs' old `openjdk` examples are examples rather than current deployment recommendations. Build an image locally before pushing; test its actual entrypoint and include source/version metadata without leaking credentials. Image push is an explicit release operation.

For generated frontend or Python resources, make packaging consume producer task outputs. Copy into the current task destination and return tracked resource paths. Test the resulting server artifact finds the bundle from its packaged resource path, rather than relying on source-tree files present only in a checkout.

Sources: [Scala packaging](https://mill-build.org/mill/scalalib/packaging.html), [Java packaging](https://mill-build.org/mill/javalib/packaging.html), [Kotlin packaging](https://mill-build.org/mill/kotlinlib/packaging.html), [Docker](https://mill-build.org/mill/contrib/docker.html), [multilanguage bundles](https://mill-build.org/mill/large/multi-language-builds.html).
