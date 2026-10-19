# Multimodule releases

A publishable JVM module extends `PublishModule` alongside its language module and supplies `publishVersion` and `pomSettings`/artifact identity. Supply license, organization, homepage/SCM, description, and developer metadata appropriate to the actual project. Do not invent an organization's namespace or reuse example coordinates. Scala binary/platform suffixes distinguish incompatible artifacts; Java/Kotlin JVM artifacts typically need a deliberately chosen stable identity without accidental Scala suffixing.

Separate release policy from build ability. Some libraries may release together; independent families may have independent versions. A shared version-file or VCS-derived version convention is useful only if it matches the repository's intended release process. Git-tag versions must be reproducible for source archives, shallow clones, and CI; otherwise make required VCS state explicit. Avoid generating a different timestamp version on every cached task evaluation.

Build publish artifacts locally, inspect the POM/source/doc jars, and verify the local module edges become the correct published coordinates. `publishLocal` is a useful consumption check, but local Ivy/Maven behavior and task names vary; discover the supported local repository commands for the project. Test a consumer outside the build that resolves the local artifact so unpublished `moduleDeps` do not conceal missing metadata.

## Publishing services

The current docs describe `mill.javalib.SonatypeCentralPublishModule/publishAll` and Central namespace/token/signing requirements. They also retain older repository-specific flows. Inspect the version-matching publisher and current destination service instructions before configuring a release. Never mix a Central token with legacy Sonatype staging endpoints because a copied example uses a different module.

For generic Maven repositories, use the supported Maven publisher with separate release/snapshot URLs and environment credentials, such as the documented `MILL_MAVEN_USERNAME` / `MILL_MAVEN_PASSWORD`. Artifactory, CodeArtifact, and GitLab have contributed integrations and differing token/header behavior. Pin compatible plugin versions, inspect their required fields, and verify upload behavior against the authorized destination. A successful local package is not authorization to upload it publicly.

Prepare signing keys/credentials in the release environment; avoid command-line secrets where process logs or task metadata can expose them. Build CI should have read permissions; publishing jobs receive only the required write credentials. Do not run dependency-changing or source-rewriting steps after signing artifacts. Verify checksums and signed artifacts before final publication.

## Consistency and recovery

A release manifest should enumerate intended module coordinates/version/platforms and artifacts. Execute from a fixed commit/tag, run meaningful tests and compatibility checks, build all required variants, then stage/publish the reviewed artifact set. A repository with several library families should not use `__.publish...` casually if it would include tools/examples/internal modules.

If an upload partially succeeds, inspect the destination's state and idempotency rules before retrying. Maven releases generally cannot be overwritten like snapshots. Record which artifacts were published and stop an unsafe blind retry. Versionfile helper tasks can commit/tag/push; invoking them changes version control and must fit the user's requested release scope.

Sources: [Scala publishing](https://mill-build.org/mill/scalalib/publishing.html), [Java publishing](https://mill-build.org/mill/javalib/publishing.html), [Kotlin publishing](https://mill-build.org/mill/kotlinlib/publishing.html), [Artifactory](https://mill-build.org/mill/contrib/artifactory.html), [CodeArtifact](https://mill-build.org/mill/contrib/codeartifact.html), [GitLab](https://mill-build.org/mill/contrib/gitlab.html), [versionfile](https://mill-build.org/mill/contrib/versionfile.html).
