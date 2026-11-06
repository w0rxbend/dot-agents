# Choosing and validating artifacts

| Artifact | Useful for | Verify |
| --- | --- | --- |
| `jar` | Library consumption | Classes/resources, stable API, separate dependency metadata |
| `assembly` | JVM executable delivery | Main class, runtime deps, merged services/config, actual `java -jar` behavior |
| `launcher` / classpath distribution | Startup with separate dependency jars | Relative paths, fresh-machine layout |
| Framework repackage | Framework-specific nested-jar executable | Loader, BOOT-INF/layout rules, framework tooling compatibility |
| GraalVM native image | Native executable | Reflection/resources/dynamic initialization, target OS/CPU |
| jlink / jpackage | Runtime/app installation bundle | Module/JDK metadata, platform-specific installers, runtime image |
| Docker/Jib image | Containerized application | Runtime/base image/architecture, entrypoint, ports, user, health behavior |

Evaluate and locate artifact with `./mill show app.assembly` instead of hardcoding its internal path in another task. Tested mixed-JVM application assembles and runs on Java 21 or compatible newer runtime, with Scala and Kotlin libraries on runtime classpath. Verify shipped jar itself: `run` uses Mill's configured classpath and fork settings.

Assemblies flatten dependencies. Set `assemblyRules` for known duplicate/resource needs; do not exclude every duplicate. Service-loader entries and framework configuration often need merging. Check signatures/metadata do not invalidate resulting jar. Bash/Batch script prefix enables direct execution, but Spark submit and other consumers may expect plain jar. Disable prefix deliberately where required.

Thin library jar normally should not embed all transitive dependencies; its POM/metadata declares them, including compile-only/runtime distinctions. Repackaging differs from shading/flattening in layout. Framework boot loaders and classpath discovery need correct module/tool integration. Java/Scala/Kotlin packaging pages share JVM concepts, but imports/package aliases can differ, so use the version's API.

Native-image needs compatible GraalVM and tested reachability configuration. Java reflection, service loading, dynamic proxies, resources and runtime classloading can behave differently. Scala Native compiles Scala to different native toolchain, with different library availability; it is not interchangeable with GraalVM converting a JVM application. Native artifacts and installers are OS/architecture-specific even with shared Mill build file.

Contrib Docker integration supports Jib and classic Dockerfile workflows; pick by layering/build customization needs. Pin maintained base image and platform. Docs' old `openjdk` examples are not current deployment recommendations. Build image locally before pushing. Test actual entrypoint. Include source/version metadata without leaking credentials. Image push is explicit release operation.

For generated frontend or Python resources, make packaging consume producer task outputs: copy into current task destination, return tracked resource paths. Test that server artifact finds bundle via packaged resource path, not source-tree files present only in a checkout.

Sources: [Scala packaging](https://mill-build.org/mill/scalalib/packaging.html), [Java packaging](https://mill-build.org/mill/javalib/packaging.html), [Kotlin packaging](https://mill-build.org/mill/kotlinlib/packaging.html), [Docker](https://mill-build.org/mill/contrib/docker.html), [multilanguage bundles](https://mill-build.org/mill/large/multi-language-builds.html).
