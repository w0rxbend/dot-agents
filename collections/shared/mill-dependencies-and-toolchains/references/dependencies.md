# Dependency edges, scopes, and resolution

| Requirement | Mill representation | Consequence |
| --- | --- | --- |
| Another local JVM module | `moduleDeps` | Tracked compilation/classpath dependency |
| Ordinary third-party library | `mvnDeps` | Compile and runtime dependency |
| Container/platform-provided library | `compileMvnDeps` | Compile-only; published as provided rather than bundled runtime |
| Logging backend/driver loaded at runtime | `runMvnDeps` | Runtime without unnecessarily exposing a compilation API |
| Testing library | Test module's `mvnDeps` | Separate ordinary module, not a production dependency with test scope |
| Build-time generator/library/plugin | Header/meta-build dependency | Build compilation classpath, separate from application classpath |
| Tracked local jar | `unmanagedClasspath` returning `PathRef` | Contents/path need tracking; distribution and provenance remain explicit |

`mvn"group:artifact:version"` addresses a Java-style artifact. `group::artifact:version` uses Scala binary cross naming; `group:::artifact:version` uses full Scala-version naming. An additional platform cross separator supports Scala.js/Native artifacts under the language module's resolver. Verify the expanded artifact through effective dependencies rather than manually concatenating a guessed `_3` or `_sjs1_3` name.

A test module inherits its parent's tested code/classpath through the enclosing language tests trait. Add fixtures and mock libraries there. Replacing `moduleDeps` with a list can discard inherited edges; use `super.moduleDeps ++ Seq(...)` when extending. Do not pull a complete framework into a neutral API module simply because a shared trait defines it.

## A monorepo dependency policy

Keep a small owned versions definition or dependency constants shared by relevant module families. It centralizes coordinates without broadening classpaths. Use `depManagement` for constraints, external `bomMvnDeps` for vendor platforms, and `bomModuleDeps`/`BomModule` for a deliberately published internal BOM. A BOM controls versions, not the set of application features each module imports. Check how dependency management appears in published POMs and consumers.

Record constraints by reason: security update, binary compatibility, framework-tested platform, or transitive conflict. Do not force every artifact to the latest version to make a conflict disappear. Coursier's resolution can select a version that compiles but fails at runtime, especially across frameworks and Scala/Kotlin metadata versions.

Start diagnosis with `./mill app.showMvnDepsTree`. Use `--whatDependsOn group:artifact` for a focused inverse view without a version, and `./mill show app.resolvedMvnDeps` / `app.runClasspath` for actual files. Exclusions such as `.exclude("group" -> "artifact")` remove particular transitive paths; inspect the graph afterward and prove the replacement supplies the required classes. Forcing/management policies should be visible in one convention rather than scattered unrelated overrides.

## Repository and unmanaged input handling

`repositories` is simple configuration; `repositoriesTask` supports computed repository definitions/credentials where needed. Preserve inherited repositories intentionally. Use canonical repository HTTPS endpoints, scoped authentication, and environment inputs; credentials should not become source code, ordinary cached task values, archive filenames, or console output. Private repositories can differ in authentication support: GitLab headers are not automatically basic-auth interchangeable.

For an unmanaged artifact download, pin a stable URL/version and checksum, write to the task destination, honor offline mode as supported, and return `PathRef`. A cached download of a mutable `latest.jar` URL is not a dependency lock. Prefer Maven-managed artifacts when available so transitive metadata and provenance are preserved.

Inspect dependency update tools against the specific Mill version, including the meta-build when updating plugins. Treat prereleases separately from stable upgrades. Verify compiler/plugin compatibility and application tests before changing central constraints, because a monorepo-wide constraint can invalidate many consumers.

Sources: [general dependencies](https://mill-build.org/mill/fundamentals/library-deps.html), [Scala dependencies](https://mill-build.org/mill/scalalib/dependencies.html), [Java dependencies](https://mill-build.org/mill/javalib/dependencies.html), [Kotlin dependencies](https://mill-build.org/mill/kotlinlib/dependencies.html), [build imports](https://mill-build.org/mill/extending/import-mvn-plugins.html).
