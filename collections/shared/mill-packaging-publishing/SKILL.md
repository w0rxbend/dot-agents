---
name: mill-packaging-publishing
description: Build and verify Mill JVM jars, assemblies, native images, distributions, Docker images, and multimodule publishing metadata for Scala Java Kotlin projects.
license: MIT
---

# Mill packaging and publication

Read [artifacts.md](references/artifacts.md) for choosing and testing the deployable form. Read [publishing.md](references/publishing.md) for multimodule coordinates, POMs, signing, repositories, and release staging.

Choose artifacts from consumer needs: thin library jar, executable assembly, launcher/classpath distribution, framework repackage, native image, or jlink/jpackage bundle. A normal successful `run` does not prove a packaged artifact works. Inspect contents and execute the actual result on the supported runtime.

Use `PublishModule` and correct language/platform artifact identities for libraries. Keep source/docs/POM metadata complete and local module dependencies represented in published coordinates. Do not put a deployable application's shaded dependencies into a library jar merely to avoid resolution work.

Generate and verify release artifacts before external publication. Use a concrete version and explicit module set; keep credentials outside source/task logs. Follow the user's actual authorization for releases, repository uploads, image pushes, and version-control operations. Setting up a publishing task does not by itself require running it.

Pin framework/plugin/toolchain versions and check version-matching APIs. Current docs describe Sonatype Central's newer publisher alongside legacy flows; do not mix authentication/endpoints or promise a removed service.
