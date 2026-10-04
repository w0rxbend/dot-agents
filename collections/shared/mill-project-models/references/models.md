# Three configuration models and their tradeoffs

## Decision table

| Situation | Starting model | Why | Change the model when |
| --- | --- | --- | --- |
| One ordinary Scala application or library | Declarative YAML | Versions, sources, dependencies, tests, and compiler options are values | Generating code or resources needs computation |
| Several ordinary libraries with simple edges | Declarative YAML per module | Settings stay close to source directories | Repeated policy needs a reusable trait or custom task |
| One small maintenance utility or issue reproduction | Mill single-file script | Code and dependency/toolchain configuration travel together | Multiple source files, reusable libraries, or separate lifecycle need modules |
| Mixed Scala/Java/Kotlin backend with shared policies | Programmable | Neutral interfaces, typed edges, conventions, and test variants remain explicit | Split build files as owners and compilation cost grow |
| Generated API clients, protobuf/schema compilation, frontend resources | Programmable module or YAML extending a custom module | The producer output becomes a tracked dependency | Move reusable implementation into a tested plugin/precompiled module |
| Hundreds of almost identical modules | YAML plus shared programmable conventions; consider precompiled modules | Owners edit values while platform engineers maintain logic | Measure build-definition compilation before using experimental precompilation |

Choose by required behavior and maintenance ownership. YAML can contain `moduleDeps`; it is not restricted to single-module builds. Programmable does not mean every setting needs a custom task. Scripts still compile to modules and support packaging and tests; small scripts are not an excuse to abandon reproducible versions.

## Declarative configuration

The tested `assets/declarative` template contains a root `build.mill.yaml`, `src/Main.scala`, an explicit main class, and managed JDK. Its keys include `mill-version: 1.1.10`, `extends: ScalaModule`, `scalaVersion`, `jvmVersion`, and `mainClass`. Copy the asset into a new directory, add the 1.1.10 bootstrap launcher, and execute `./mill run`.

For a two-module build, a minimal root YAML can hold only global header configuration. Put `extends: ScalaModule`, `scalaVersion`, and `mvnDeps` in `api/package.mill.yaml` and `service/package.mill.yaml`; the latter can use `moduleDeps: [api]`. The module's sources live in its `src/`. Use fully qualified `mill.javalib.JavaModule`, `mill.scalalib.ScalaModule`, and `mill.kotlinlib.KotlinModule` in mixed-language YAML to avoid ambiguous convenience imports.

A test module's `extends` combines its enclosing module's tests trait and a framework, for example `[build.service.ScalaTests, mill.scalalib.TestModule.Utest]`. `object test:` allows a submodule inside the parent's YAML when its logical name does not correspond to a separate directory. YAML `!append` adds to inherited lists; an ordinary list replaces them. This matters for resources, test module dependencies, compiler options, and BOM policy. Inspect the resulting task instead of guessing whether a superclass list survived.

Keep simple configuration in YAML. Do not hide a shell script in a string field to work around the absence of custom logic. Use a supported programmable trait or convert the relevant module when behavior requires computation. Root and package files may mix declarative and programmable definitions; verify discovery and qualified names for the chosen Mill version.

## Single-file scripts

`assets/script/Hello.scala` demonstrates `//| scalaVersion` and `//| jvmVersion` with an ordinary main method. A `.mill-version` pins the launcher selection. Run `./mill Hello.scala Mill`, `./mill Hello.scala:compile`, or `./mill show Hello.scala:assembly`. Script headers use **Mill** keys: `mvnDeps`, `moduleDeps`, `jvmVersion`, and `extends`; Scala CLI `//> using` directives do not configure Mill.

A script may reference another script (`moduleDeps: [Helper.scala]`) or a project module. References are relative to the script unless using a documented workspace-relative form such as `//path/Helper.scala`. A test script can extend `mill.script.ScalaModule.Utest` and depend on the script under test. `./mill resolve 'Hello.scala:_'` reveals available tasks. Top-level `main` methods can integrate with MainArgs; ordinary `def main(args: Array[String]): Unit` keeps argument behavior explicit.

Use scripts for a dependency-aware repository utility, a support reproduction, or a small batch job. Avoid accumulating a graph of many mutually dependent scripts, duplicating configuration across them, or hiding resource-generation conventions in custom script classes. When the utility becomes a library/application with several sources and separately owned tests, move source code into module directories and transfer headers to YAML or programmable settings. Preserve observable command arguments and output during that move.

## Programmable configuration

The tested `mill-build-logic/assets/codegen` build reads a `Task.Source`, generates Java in `Task.dest`, and appends that directory to `generatedSources`. This is a concrete reason to select programmable configuration. Reading an input file outside a tracked task and writing generated files into `src/` would defeat the benefit.

Use `package build`, `import mill.*`, and the relevant language imports. For explicit class imports in a mixed-language build, also import `mill.javalib.DepSyntax` to enable `mvn"..."`; importing only `JavaModule`/`ScalaModule` does not bring that extension into scope. Methods returning task values can be concise for literal configuration, while computed file-producing steps should use `Task { ... }` and `PathRef`.

Choose names and source paths deliberately. `object app extends ScalaModule` normally reads `app/src`; a root module named backticked `package` reads root `src`. Compatibility modules preserve `src/main/scala`, `src/main/java`, and test layouts. Converting YAML to Scala should preserve these paths, module names, inherited values, runtime flags, and main-class behavior, not just dependency versions.

For a team's decision record, state the source layout, expected custom operations, convention ownership, selected format, pinned Mill/JDK versions, and the compile/test/run commands. Record a trigger to reconsider the format, such as a generated client or shared release convention. Avoid choosing a programmable monorepo template for a one-file reproducer merely because it is available.

Sources: [stable Scala introduction](https://mill-build.org/mill/1.1.x/scalalib/intro.html), [Scala module configuration](https://mill-build.org/mill/scalalib/module-config.html), [Scala scripts](https://mill-build.org/mill/scalalib/script.html), [modules](https://mill-build.org/mill/fundamentals/modules.html), [precompiled modules](https://mill-build.org/mill/large/pre-compiled-modules.html).
