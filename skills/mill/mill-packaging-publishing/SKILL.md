---
name: mill-packaging-publishing
description: Build and verify Mill JVM jars, assemblies, native images, distributions, Docker images, and multimodule publishing metadata for Scala Java Kotlin projects. Use when packaging or publishing artifacts from a Mill build.
license: MIT
---

# Mill packaging and publication

Read [artifacts.md](references/artifacts.md) to choose and test deployable form. Read [publishing.md](references/publishing.md) for multimodule coordinates, POMs, signing, repositories, release staging.

Pick artifact by consumer need: thin library jar, executable assembly, launcher/classpath distribution, framework repackage, native image, or jlink/jpackage bundle. Passing `run` does not prove packaged artifact works. Inspect contents; run actual result on supported runtime.

Libraries: use `PublishModule` with correct language/platform artifact identities. Keep source/docs/POM metadata complete, with local module dependencies as published coordinates. Do not put deployable application's shaded dependencies into library jar merely to avoid resolution work.

Generate and verify release artifacts before external publication. Use concrete version, explicit module set. Keep credentials out of source/task logs. Releases, repository uploads, image pushes and version-control operations need user's actual authorization. Setting up publishing task does not by itself require running it.

Pin framework/plugin/toolchain versions; check version-matching APIs. Current docs list Sonatype Central's newer publisher beside legacy flows. Do not mix authentication/endpoints or promise removed service.
