# Three configuration models and their tradeoffs

## Decision table

| Situation | Starting model | Why | Change the model when |
| --- | --- | --- | --- |
| One ordinary Scala application or library | Declarative YAML | Versions, sources, dependencies, tests, compiler options are values | Generating code or resources needs computation |
| Several ordinary libraries with simple edges | Declarative YAML per module | Settings stay near source directories | Repeated policy needs reusable trait or custom task |
| One small maintenance utility or issue reproduction | Mill single-file script | Code and dependency/toolchain configuration travel together | Multiple source files, reusable libraries, or separate lifecycle need modules |
| Mixed Scala/Java/Kotlin backend with shared policies | Programmable | Neutral interfaces, typed edges, conventions, test variants stay explicit | Split build files as owners and compilation cost grow |
| Generated API clients, protobuf/schema compilation, frontend resources | Programmable module or YAML extending a custom module | Producer output becomes tracked dependency | Move reusable implementation into tested plugin/precompiled module |
| Hundreds of almost identical modules | YAML plus shared programmable conventions; consider precompiled modules | Owners edit values; platform engineers maintain logic | Measure build-definition compilation before using experimental precompilation |

Choose by required behavior and maintenance ownership. YAML can hold `moduleDeps`; it is not limited to single-module builds. Programmable does not mean every setting needs a custom task. Scripts still compile to modules and support packaging and tests. Small scripts are no excuse to drop reproducible versions.

## Declarative configuration

Tested `assets/declarative` template holds root `build.mill.yaml`, `src/Main.scala`, explicit main class, managed JDK. Keys include `mill-version: 1.1.10`, `extends: ScalaModule`, `scalaVersion`, `jvmVersion`, `mainClass`. Copy asset into new directory, add 1.1.10 bootstrap launcher, run `./mill run`.

Two-module build: minimal root YAML can hold only global header configuration. Put `extends: ScalaModule`, `scalaVersion`, `mvnDeps` in `api/package.mill.yaml` and `service/package.mill.yaml`. Service module can use `moduleDeps: [api]`. Each module's sources live in its own `src/`. In mixed-language YAML, use fully qualified `mill.javalib.JavaModule`, `mill.scalalib.ScalaModule`, `mill.kotlinlib.KotlinModule` to avoid ambiguous convenience imports.

Test module's `extends` combines enclosing module's tests trait and a framework, for example `[build.service.ScalaTests, mill.scalalib.TestModule.Utest]`. `object test:` allows submodule inside parent's YAML when its logical name does not match a separate directory. YAML `!append` adds to inherited lists; plain list replaces them. Matters for resources, test module dependencies, compiler options, BOM policy. Inspect resulting task; do not guess whether superclass list survived.

Keep simple configuration in YAML. Do not hide shell script in string field to work around missing custom logic. When behavior needs computation, use supported programmable trait or convert relevant module. Root and package files may mix declarative and programmable definitions; verify discovery and qualified names for chosen Mill version.

## Single-file scripts

`assets/script/Hello.scala` shows `//| scalaVersion` and `//| jvmVersion` with ordinary main method. `.mill-version` pins launcher selection. Run `./mill Hello.scala Mill`, `./mill Hello.scala:compile`, or `./mill show Hello.scala:assembly`. Script headers use **Mill** keys: `mvnDeps`, `moduleDeps`, `jvmVersion`, `extends`. Scala CLI `//> using` directives do not configure Mill.

Script may reference another script (`moduleDeps: [Helper.scala]`) or project module. References are relative to script unless using documented workspace-relative form such as `//path/Helper.scala`. Test script can extend `mill.script.ScalaModule.Utest` and depend on script under test. `./mill resolve 'Hello.scala:_'` lists available tasks. Top-level `main` methods can integrate with MainArgs; ordinary `def main(args: Array[String]): Unit` keeps argument behavior explicit.

Use scripts for dependency-aware repository utility, support reproduction, or small batch job. Avoid graphs of many mutually dependent scripts, configuration duplicated across them, or resource-generation conventions hidden in custom script classes. When utility grows into library/application with several sources and separately owned tests, move source into module directories. Transfer headers to YAML or programmable settings. Keep observable command arguments and output unchanged during move.

## Programmable configuration

Tested `mill-build-logic/assets/codegen` build reads `Task.Source`, generates Java in `Task.dest`, appends that directory to `generatedSources`. Concrete reason to pick programmable configuration. Reading input file outside tracked task and writing generated files into `src/` defeats the benefit.

Use `package build`, `import mill.*`, and relevant language imports. With explicit class imports in mixed-language build, also import `mill.javalib.DepSyntax` to enable `mvn"..."`. Importing only `JavaModule`/`ScalaModule` does not bring that extension into scope. Literal configuration can use concise methods returning task values. Computed file-producing steps should use `Task { ... }` and `PathRef`.

Choose names and source paths deliberately. `object app extends ScalaModule` normally reads `app/src`; root module named backticked `package` reads root `src`. Compatibility modules keep `src/main/scala`, `src/main/java`, and test layouts. When converting YAML to Scala, preserve these paths, module names, inherited values, runtime flags, main-class behavior, not just dependency versions.

For team decision record, state source layout, expected custom operations, convention ownership, selected format, pinned Mill/JDK versions, compile/test/run commands. Record trigger to reconsider format, such as generated client or shared release convention. Avoid programmable monorepo template for one-file reproducer merely because it is available.

Sources: [stable Scala introduction](https://mill-build.org/mill/1.1.x/scalalib/intro.html), [Scala module configuration](https://mill-build.org/mill/scalalib/module-config.html), [Scala scripts](https://mill-build.org/mill/scalalib/script.html), [modules](https://mill-build.org/mill/fundamentals/modules.html), [precompiled modules](https://mill-build.org/mill/large/pre-compiled-modules.html).
