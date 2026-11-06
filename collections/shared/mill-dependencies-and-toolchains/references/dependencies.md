# Dependency edges, scopes, and resolution

| Requirement | Mill representation | Consequence |
| --- | --- | --- |
| Another local JVM module | `moduleDeps` | Tracked compilation/classpath dependency |
| Ordinary third-party library | `mvnDeps` | Compile and runtime dependency |
| Container/platform-provided library | `compileMvnDeps` | Compile-only; published as provided, not bundled |
| Logging backend/driver loaded at runtime | `runMvnDeps` | Runtime, without needlessly exposing compilation API |
| Testing library | Test module's `mvnDeps` | Separate ordinary module, not production dependency with test scope |
| Build-time generator/library/plugin | Header/meta-build dependency | Build compilation classpath, separate from application classpath |
| Tracked local jar | `unmanagedClasspath` returning `PathRef` | Contents/path need tracking; distribution and provenance stay explicit |

`mvn"group:artifact:version"`: Java-style artifact. `group::artifact:version`: Scala binary cross naming. `group:::artifact:version`: full Scala-version naming. Extra platform cross separator gives Scala.js/Native artifacts under language module's resolver. Verify expanded artifact via effective dependencies; do not hand-concatenate guessed `_3` or `_sjs1_3` name.

Test module inherits parent's tested code/classpath via enclosing language tests trait. Add fixtures and mock libraries there. Replacing `moduleDeps` with plain list can drop inherited edges; extend with `super.moduleDeps ++ Seq(...)`. Do not pull full framework into neutral API module only because shared trait defines it.

## A monorepo dependency policy

Keep small owned versions definition or dependency constants, shared by relevant module families. It centralizes coordinates without broadening classpaths. `depManagement` for constraints, external `bomMvnDeps` for vendor platforms, `bomModuleDeps`/`BomModule` for deliberately published internal BOM. BOM controls versions, not which features each module imports. Check how dependency management shows in published POMs and consumers.

Record each constraint's reason: security update, binary compatibility, framework-tested platform, transitive conflict. Do not force every artifact to latest to hide conflict. Coursier can pick version that compiles but fails at runtime, especially across frameworks and Scala/Kotlin metadata versions.

Start diagnosis with `./mill app.showMvnDepsTree`. `--whatDependsOn group:artifact` (no version) gives focused inverse view. `./mill show app.resolvedMvnDeps` / `app.runClasspath` show actual files. Exclusions like `.exclude("group" -> "artifact")` cut specific transitive paths; afterward inspect graph and prove replacement supplies required classes. Keep forcing/management policy in one visible convention, not scattered unrelated overrides.

## Repository and unmanaged input handling

`repositories` for simple configuration; `repositoriesTask` for computed repository definitions/credentials. Preserve inherited repositories intentionally. Use canonical HTTPS repository endpoints, scoped authentication, environment inputs. Credentials should not end up in source code, ordinary cached task values, archive filenames or console output. Private repositories vary in authentication support: GitLab headers are not automatically basic-auth interchangeable.

Unmanaged artifact download: pin stable URL/version and checksum, write to task destination, honor offline mode where supported, return `PathRef`. Cached download of mutable `latest.jar` URL is not a dependency lock. Prefer Maven-managed artifacts when available; they keep transitive metadata and provenance.

Check dependency update tools against specific Mill version, including meta-build when updating plugins. Treat prereleases apart from stable upgrades. Verify compiler/plugin compatibility and application tests before changing central constraints; monorepo-wide constraint can invalidate many consumers.

Sources: [general dependencies](https://mill-build.org/mill/fundamentals/library-deps.html), [Scala dependencies](https://mill-build.org/mill/scalalib/dependencies.html), [Java dependencies](https://mill-build.org/mill/javalib/dependencies.html), [Kotlin dependencies](https://mill-build.org/mill/kotlinlib/dependencies.html), [build imports](https://mill-build.org/mill/extending/import-mvn-plugins.html).
