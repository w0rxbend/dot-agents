# Integration catalog and custom language examples

Contrib plugins live in Mill's repository; third-party plugins have independent maintainers/releases. Either still needs compatibility checking. Prefer a built-in capability when it supplies the actual behavior; do not select an older third-party Kotlin plugin when the pinned Mill has suitable built-in Kotlin modules.

| Integration family | Researched contrib entries | Practical decision |
| --- | --- | --- |
| Repository publication | Artifactory, CodeArtifact, GitLab, Sonatype Central | Confirm destination authentication, release/snapshot URLs, and current publisher |
| Metadata/releases | BuildInfo, versionfile | Keep reproducible values and explicit commit/tag/push authorization |
| Packaging/deployment | Docker, ProGuard | Test merged/shrunk artifact behavior; don't copy old image defaults |
| Database operations | Flyway | Build migration inputs separately; a migrate action changes a database |
| Performance/quality | JMH, Scoverage, OWASP Dependency Check, SBOM | Match compiler/runtime support and data/report scope |
| Generated/web code | ScalaPB, Twirl, Play | Track schemas/templates/routes and generator versions |
| Test frameworks | TestNG | Select a real runner and confirm test discovery |

SBOM describes dependencies, not vulnerability remediation. OWASP dependency scans may require an updated external database and network/API settings; distinguish scan data from deterministic compilation. Do not copy an illustrative API key or a hardcoded database password from examples. JMH benchmarks need their own isolated run policy and warm-up; ordinary test timing is not a meaningful microbenchmark substitute.

The third-party list includes wrappers/completions, Antlr, AspectJ, native-image, Jib/universal packaging, OpenAPI, MDoc, MiMa, JaCoCo, Scalafix, dependency discipline tools, and more. Before using one, inspect its source/release support for the selected Mill line, the artifact coordinate, and required JDK. Old catalog examples are not proof a current compatible release exists.

## TypeScript extension example

The official example builds an illustrative `TypeScriptModule` from ordinary tasks: install the tool, track sources, typecheck/compile, run, model module dependencies, gather declaration/output paths, and bundle. It explicitly is not the production TypeScript integration. Reuse the technique when teaching or integrating a new language; prefer the current built-in `javascriptlib` capability when it matches the real project.

Important transfer: tool installation is a task with pinned inputs; source walking is based on a tracked source task; compilation returns output `PathRef`s; downstream modules consume those outputs via `Task.traverse`; runtime is a command. Handle lockfiles/private registry credentials and avoid a mutable untracked `node_modules` shared across parallel tasks.

## Python extension example

The official custom Python module example creates a virtual environment/tool task, tracks sources, type-checks with mypy, runs via a command, and later models module dependencies and bundled pip libraries. It illustrates how module abstractions grow from a small pipeline. Prefer the supported `pythonlib.PythonModule` for real use when it fits rather than shipping the demonstration unchanged.

Model the interpreter/tool version, requirements/constraints, source roots, and relevant environment. Outputs/venvs live in task destinations. Consider platform-dependent executable paths and compiled wheels; an example using `venv/bin/python3` is not automatically Windows-compatible. A reusable module should expose these requirements and preserve upstream sources/dependencies without writing into them.

Sources: [contrib catalog](https://mill-build.org/mill/extending/contrib-plugins.html), [third-party catalog](https://mill-build.org/mill/extending/thirdparty-plugins.html), [TypeScript extension example](https://mill-build.org/mill/extending/example-typescript-support.html), [Python extension example](https://mill-build.org/mill/extending/example-python-support.html), [SBOM](https://mill-build.org/mill/contrib/sbom.html), [OWASP](https://mill-build.org/mill/contrib/owaspdependencycheck.html), [JMH](https://mill-build.org/mill/contrib/jmh.html), [Flyway](https://mill-build.org/mill/contrib/flyway.html), [ScalaPB](https://mill-build.org/mill/contrib/scalapblib.html), [Twirl](https://mill-build.org/mill/contrib/twirllib.html), [Play](https://mill-build.org/mill/contrib/playlib.html), [ProGuard](https://mill-build.org/mill/contrib/proguard.html), [BuildInfo](https://mill-build.org/mill/contrib/buildinfo.html), [TestNG](https://mill-build.org/mill/contrib/testng.html).
