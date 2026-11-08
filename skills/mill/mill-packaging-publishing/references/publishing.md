# Multimodule releases

Publishable JVM module extends `PublishModule` alongside its language module, supplying `publishVersion` and `pomSettings`/artifact identity. Supply license, organization, homepage/SCM, description and developer metadata true to actual project. Do not invent organization namespace or reuse example coordinates. Scala binary/platform suffixes distinguish incompatible artifacts. Java/Kotlin JVM artifacts typically need deliberately chosen stable identity, no accidental Scala suffix.

Separate release policy from build ability. Some libraries may release together; independent families may version independently. Shared version-file or VCS-derived version helps only if it matches repository's intended release process. Git-tag versions must reproduce for source archives, shallow clones and CI; otherwise make required VCS state explicit. Avoid generating new timestamp version on every cached task evaluation.

Build publish artifacts locally. Inspect POM/source/doc jars. Verify local module edges become correct published coordinates. `publishLocal` is useful consumption check, but local Ivy/Maven behavior and task names vary; find project's supported local repository commands. Test consumer outside build resolving local artifact, so unpublished `moduleDeps` cannot conceal missing metadata.

## Publishing services

Current docs describe `mill.javalib.SonatypeCentralPublishModule/publishAll` and Central namespace/token/signing requirements, plus older repository-specific flows. Before configuring release, inspect version-matching publisher and destination service's current instructions. Never mix Central token with legacy Sonatype staging endpoints because copied example uses different module.

For generic Maven repositories, use supported Maven publisher with separate release/snapshot URLs and environment credentials, such as documented `MILL_MAVEN_USERNAME` / `MILL_MAVEN_PASSWORD`. Artifactory, CodeArtifact and GitLab have contributed integrations with differing token/header behavior. Pin compatible plugin versions, inspect required fields, verify upload behavior against authorized destination. Successful local package is not authorization to upload publicly.

Prepare signing keys/credentials in release environment. Avoid command-line secrets where process logs or task metadata can expose them. Build CI should have read permissions; publishing jobs get only required write credentials. Do not run dependency-changing or source-rewriting steps after signing. Verify checksums and signed artifacts before final publication.

## Consistency and recovery

Release manifest should list intended module coordinates/version/platforms and artifacts. From fixed commit/tag: run meaningful tests and compatibility checks, build all required variants, then stage/publish reviewed artifact set. With several library families, do not use `__.publish...` casually if it would include tools/examples/internal modules.

If upload partially succeeds, inspect destination state and idempotency rules before retrying. Maven releases generally cannot be overwritten like snapshots. Record published artifacts; stop unsafe blind retry. Versionfile helper tasks can commit/tag/push. Invoking them changes version control and must fit user's requested release scope.

Sources: [Scala publishing](https://mill-build.org/mill/scalalib/publishing.html), [Java publishing](https://mill-build.org/mill/javalib/publishing.html), [Kotlin publishing](https://mill-build.org/mill/kotlinlib/publishing.html), [Artifactory](https://mill-build.org/mill/contrib/artifactory.html), [CodeArtifact](https://mill-build.org/mill/contrib/codeartifact.html), [GitLab](https://mill-build.org/mill/contrib/gitlab.html), [versionfile](https://mill-build.org/mill/contrib/versionfile.html).
