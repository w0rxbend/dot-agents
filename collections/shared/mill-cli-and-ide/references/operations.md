# Launcher and CLI operations

## Reproducible installation

For a new stable example:

```sh
curl -fL https://repo.maven.apache.org/maven2/com/lihaoyi/mill-dist/1.1.10/mill-dist-1.1.10-mill.sh -o mill
chmod +x mill
./mill --version
```

Commit the launcher with executable permissions. Use the corresponding official `mill.bat` on Windows. Pin the Mill version in a build header or `.mill-version`; update the launcher alongside a requested Mill upgrade so its bootstrapping behavior remains compatible. A global Mill installation is convenient but should not override a project's pin. Avoid silently downloading a milestone because the unversioned installation page points there.

Build headers on `build.mill` use `//|` comments before Scala code; declarative YAML uses top-level keys. `mill-version`, `mill-jvm-version`, `mill-jvm-opts`, repositories, and default Mill options are launcher/build-runtime settings. Module values such as `jvmVersion`, `forkArgs`, and `mvnDeps` have another scope. Header `mvnDeps` imports libraries for **build logic**; module `mvnDeps` adds libraries to **application code**. In YAML, meta-build configuration uses the documented `mill-build:` section for build dependencies. Keep these scopes visible in reviews.

For intentional local JDK use, set `mill-jvm-version: system`; this sacrifices managed runtime reproducibility. Pin distribution/version for team/CI consistency. A managed module JDK remains a separate pin. Inspect `.mill-version`, `.config/mill-version`, headers, environment overrides, and launcher defaults when the observed version differs from expectations. Avoid relying on conflicting pins.

## Command selection

| Goal | Command shape |
| --- | --- |
| List all task/module selectors | `./mill resolve '__'` |
| List compilation tasks recursively | `./mill resolve '__.compile'` |
| Inspect one task's definition and prerequisites | `./mill inspect app.compile` |
| Print a value or artifact location | `./mill show app.assembly` |
| Show named results | `./mill showNamed '{api,app}.compile'` |
| Display the work needed | `./mill plan app.assembly` |
| Inspect graph connection / graph images | Discover `path`, `visualize`, `visualizePlan` signatures for the pinned version |
| Run distinct commands with separate arguments | `./mill app.run Alice + tool.run Bob` |
| Watch relevant inputs | `./mill -w app.compile` |
| Constrain build parallelism | `./mill -j 2 '__.compile'` |
| Continue independent work after failures | `./mill -k '__.test'` |
| Diagnostic isolated/non-server run | `./mill --no-daemon app.compile` |
| Remove one task's cached output | `./mill clean app.compile` |
| Stop a stuck daemon | `./mill shutdown` |

`_` matches one task-path segment and `__` matches any depth. `{api,app}` enumerates choices; quote it so the shell does not expand it first. Quote `library[3.8.2].test` and matrix wildcards, especially in zsh. Type-filtered queries can select module kinds in newer/current APIs, but discover the exact supported syntax before using them in a heterogeneous repository. `+` separates selectors; escape a literal plus passed to a task as documented.

A `compile` task may be cached; `run` and test commands have execution semantics rather than simple file caching. `inspect` and `show` answer different questions: definition/prerequisites versus evaluated value. Resolve before removing caches or constructing a selector from filesystem guesses. `clean` can terminate associated background runs and should be targeted in ordinary debugging.

## IDE and BSP

Use Mill's official BSP installation and the chosen IDE's BSP import process. The familiar command is `./mill mill.bsp.BSP/install`; discover/verify it for the project's version. IntelliJ can import a BSP build; its generated IDEA XML support is an alternate integration with different behavior. Metals/VSCode primarily use BSP for Scala. Android Studio support remains distinct and experimental; generated project files do not imply all Gradle-specific Android IDE features exist.

Diagnose in this order: launcher/version, direct CLI compilation, source roots and language plugins, BSP configuration, IDE logs. Reimport after build configuration changes. If CLI succeeds but IDE fails, inspect `.bsp` configuration and IDE version instead of rewriting application source. BSP can use a separate output directory configured by `mill-separate-bsp-output-dir`; this prevents accidental contention but also explains why IDE and CLI caches differ.

## CI and evidence

Run the checked-in launcher. Cache Coursier downloads and optionally `out/` with keys covering OS, architecture, JVM/tool versions, and build-definition changes. Avoid treating a cached `out/` tree as a portable distribution artifact. Upload test reports and `mill-chrome-profile.json` when useful, including after a failed build. Keep secrets out of archived task metadata/logs. Offline builds require already available dependencies and toolchains; configuration alone cannot make a clean machine offline-capable.

Sources: [installation and IDE setup](https://mill-build.org/mill/1.1.x/cli/installation-ide.html), [flags](https://mill-build.org/mill/cli/flags.html), [built-in commands](https://mill-build.org/mill/cli/builtin-commands.html), [queries](https://mill-build.org/mill/cli/query-syntax.html), [build headers](https://mill-build.org/mill/cli/build-header.html).
