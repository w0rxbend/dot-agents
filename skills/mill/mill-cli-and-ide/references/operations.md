# Launcher and CLI operations

## Reproducible installation

New stable example:

```sh
u=https://repo.maven.apache.org/maven2/com/lihaoyi/mill-dist/1.1.10/mill-dist-1.1.10-mill.sh
curl -fL "$u" -o mill.new
curl -fL "$u.sha1" -o mill.sha1
echo "$(cat mill.sha1)  mill.new" | sha1sum -c - && chmod +x mill.new && mv mill.new mill && rm mill.sha1
./mill --version
```

Verify checksum (or `.asc` signature) and skim script before first run. Commit verified launcher as executable. On Windows use matching official `mill.bat`. Pin Mill version in build header or `.mill-version`. On requested Mill upgrade, update launcher too so bootstrapping stays compatible. Global Mill install is convenient but should not override project pin. Avoid silently downloading milestone because unversioned install page points there.

`build.mill` headers use `//|` comments before Scala code; declarative YAML uses top-level keys. `mill-version`, `mill-jvm-version`, `mill-jvm-opts`, repositories and default Mill options are launcher/build-runtime settings. Module values like `jvmVersion`, `forkArgs`, `mvnDeps` have different scope. Header `mvnDeps` imports libraries for **build logic**; module `mvnDeps` adds libraries to **application code**. YAML meta-build configuration uses documented `mill-build:` section for build dependencies. Keep these scopes visible in reviews.

For intentional local JDK use, set `mill-jvm-version: system`; loses managed runtime reproducibility. Pin distribution/version for team/CI consistency. Managed module JDK is separate pin. If observed version is unexpected, inspect `.mill-version`, `.config/mill-version`, headers, environment overrides, launcher defaults. Avoid relying on conflicting pins.

## Command selection

| Goal | Command shape |
| --- | --- |
| List all task/module selectors | `./mill resolve '__'` |
| List compilation tasks recursively | `./mill resolve '__.compile'` |
| Inspect one task's definition and prerequisites | `./mill inspect app.compile` |
| Print value or artifact location | `./mill show app.assembly` |
| Show named results | `./mill showNamed '{api,app}.compile'` |
| Show needed work | `./mill plan app.assembly` |
| Inspect graph connection / graph images | Discover `path`, `visualize`, `visualizePlan` signatures for pinned version |
| Run distinct commands, separate arguments | `./mill app.run Alice + tool.run Bob` |
| Watch relevant inputs | `./mill -w app.compile` |
| Limit build parallelism | `./mill -j 2 '__.compile'` |
| Continue independent work after failures | `./mill -k '__.test'` |
| Diagnostic isolated/non-server run | `./mill --no-daemon app.compile` |
| Remove one task's cached output | `./mill clean app.compile` |
| Stop stuck daemon | `./mill shutdown` |

`_` matches one task-path segment; `__` matches any depth. `{api,app}` enumerates choices; quote it so shell does not expand it first. Quote `library[3.8.2].test` and matrix wildcards, especially in zsh. Newer/current APIs support type-filtered queries that select module kinds. Discover exact supported syntax before using them in heterogeneous repository. `+` separates selectors; escape literal plus passed to task as documented.

`compile` may be cached; `run` and test commands have execution semantics, not simple file caching. Resolve before removing caches or building selectors from filesystem guesses. `clean` can stop associated background runs; keep it targeted in ordinary debugging.

## IDE and BSP

Use Mill's official BSP install plus chosen IDE's BSP import. Familiar command: `./mill mill.bsp.BSP/install`; discover/verify it for project's version. IntelliJ can import BSP build; its generated IDEA XML support is alternate integration that behaves differently. Metals/VSCode mainly use BSP for Scala. Android Studio support is separate and experimental. Generated project files do not imply all Gradle-specific Android IDE features exist.

Diagnose in order: launcher/version, direct CLI compilation, source roots and language plugins, BSP configuration, IDE logs. Reimport after build configuration changes. If CLI succeeds but IDE fails, inspect `.bsp` configuration and IDE version instead of rewriting application source. BSP can use separate output directory via `mill-separate-bsp-output-dir`. Prevents accidental contention; also explains why IDE and CLI caches differ.

## CI and evidence

Run checked-in launcher. Cache Coursier downloads and optionally `out/`, with keys covering OS, architecture, JVM/tool versions, build-definition changes. Avoid treating cached `out/` as portable distribution artifact. Upload test reports and `mill-chrome-profile.json` when useful, also after failed build. Keep secrets out of archived task metadata/logs. Offline builds need dependencies and toolchains already available; configuration alone cannot make clean machine offline-capable.

Sources: [installation and IDE setup](https://mill-build.org/mill/1.1.x/cli/installation-ide.html), [flags](https://mill-build.org/mill/cli/flags.html), [built-in commands](https://mill-build.org/mill/cli/builtin-commands.html), [queries](https://mill-build.org/mill/cli/query-syntax.html), [build headers](https://mill-build.org/mill/cli/build-header.html).
