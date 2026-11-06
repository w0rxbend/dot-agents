# Integration catalog and custom language examples

Contrib plugins live in Mill's repository; third-party plugins have independent maintainers/releases. Both need compatibility checks. Prefer built-in capability when it supplies actual behavior. Do not pick older third-party Kotlin plugin when pinned Mill has suitable built-in Kotlin modules.

| Integration family | Researched contrib entries | Practical decision |
| --- | --- | --- |
| Repository publication | Artifactory, CodeArtifact, GitLab, Sonatype Central | Confirm destination authentication, release/snapshot URLs, current publisher |
| Metadata/releases | BuildInfo, versionfile | Keep values reproducible; commit/tag/push need explicit authorization |
| Packaging/deployment | Docker, ProGuard | Test merged/shrunk artifact behavior; don't copy old image defaults |
| Database operations | Flyway | Build migration inputs separately; migrate action changes a database |
| Performance/quality | JMH, Scoverage, OWASP Dependency Check, SBOM | Match compiler/runtime support and data/report scope |
| Generated/web code | ScalaPB, Twirl, Play | Track schemas/templates/routes and generator versions |
| Test frameworks | TestNG | Use real runner; confirm test discovery |

SBOM describes dependencies, not vulnerability remediation. OWASP dependency scans may need updated external database and network/API settings; keep scan data separate from deterministic compilation. Do not copy illustrative API key or hardcoded database password from examples. JMH benchmarks need own isolated run policy and warm-up; ordinary test timing is no meaningful microbenchmark substitute.

Third-party list includes wrappers/completions, Antlr, AspectJ, native-image, Jib/universal packaging, OpenAPI, MDoc, MiMa, JaCoCo, Scalafix, dependency discipline tools and more. Before use, check its source/release support for selected Mill line, artifact coordinate and required JDK. Old catalog examples do not prove a current compatible release exists.

## TypeScript extension example

Official example builds illustrative `TypeScriptModule` from ordinary tasks: install tool, track sources, typecheck/compile, run, model module dependencies, gather declaration/output paths, bundle. Explicitly not production TypeScript integration. Reuse technique for teaching or integrating new languages; prefer current built-in `javascriptlib` when it matches the real project.

Key transfer: tool installation is a task with pinned inputs; source walking uses tracked source task; compilation returns output `PathRef`s; downstream modules consume them via `Task.traverse`; runtime is a command. Handle lockfiles/private registry credentials. Avoid mutable untracked `node_modules` shared across parallel tasks.

## Python extension example

Official custom Python module example creates virtual environment/tool task, tracks sources, type-checks with mypy, runs via command, then models module dependencies and bundled pip libraries. For real use, prefer supported `pythonlib.PythonModule` when it fits; do not ship the demonstration unchanged.

Model interpreter/tool version, requirements/constraints, source roots, relevant environment. Outputs/venvs live in task destinations. Consider platform-dependent executable paths and compiled wheels: `venv/bin/python3` is not automatically Windows-compatible. Reusable module should expose these requirements and preserve upstream sources/dependencies without writing into them.

Sources: [contrib catalog](https://mill-build.org/mill/extending/contrib-plugins.html), [third-party catalog](https://mill-build.org/mill/extending/thirdparty-plugins.html), [TypeScript extension example](https://mill-build.org/mill/extending/example-typescript-support.html), [Python extension example](https://mill-build.org/mill/extending/example-python-support.html), [SBOM](https://mill-build.org/mill/contrib/sbom.html), [OWASP](https://mill-build.org/mill/contrib/owaspdependencycheck.html), [JMH](https://mill-build.org/mill/contrib/jmh.html), [Flyway](https://mill-build.org/mill/contrib/flyway.html), [ScalaPB](https://mill-build.org/mill/contrib/scalapblib.html), [Twirl](https://mill-build.org/mill/contrib/twirllib.html), [Play](https://mill-build.org/mill/contrib/playlib.html), [ProGuard](https://mill-build.org/mill/contrib/proguard.html), [BuildInfo](https://mill-build.org/mill/contrib/buildinfo.html), [TestNG](https://mill-build.org/mill/contrib/testng.html).
