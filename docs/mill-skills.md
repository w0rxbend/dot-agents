# Mill and VirtusLab Scala Stack skills

This collection adds **14 original Mill skills**, about **18,700 words** of instructions and
references, and **six runnable examples**. Mill is the preferred tool for new Scala/JVM projects
in this collection. Scala CLI remains available for explicit requests and existing projects.
The official VirtusLab `direct-style-scala` skill is installed directly from upstream with a local
Mill preference section; its original text is not redistributed here.

## Clone and restore everything available locally

```sh
git clone https://github.com/w0rxbend/dot-agents.git ~/.dot-agents
cd ~/.dot-agents
./install.sh --agents all
python3 scripts/install_vss.py
./install.sh --agents all --include-local
./install.sh --agents all --include-local --check
```

The VSS installer downloads a checksum-verified archive pinned to
[`51eb40a55fa1c2a4c99f2980830d28bbea4a2ac7`](https://github.com/VirtusLab/scala-skill/tree/51eb40a55fa1c2a4c99f2980830d28bbea4a2ac7),
stages it atomically, preserves its frontmatter, and adds
[the local preference](../overlays/direct-style-scala/preferences.md). Its source files live in
`~/.local/share/dot-agents/providers/skills/direct-style-scala`; the collection installer links
that source into agent directories. It is idempotent and refuses to overwrite customization.
Use `--replace` only when you want it to retain a backup and replace a differing installation.
`--home` supports testing a fresh home; `--target` selects a different source skills root.

Existing skills-root symlinks or conflicting files require the normal reviewed `--replace`
workflow described in the README. The other provider-managed skills still require their
respective plugins/accounts; this command restores VSS without bundling their proprietary files.
The new skills are available on the next agent turn; restart an agent if it caches discovery.

## Skill map

| Skill | Guidance |
| --- | --- |
| [mill-project-models](../collections/shared/mill-project-models/SKILL.md) | Declarative YAML, single-file scripts, programmable builds; when to use and change each |
| [mill-cli-and-ide](../collections/shared/mill-cli-and-ide/SKILL.md) | Launcher, flags, queries, headers, IDE/BSP, Maven/Gradle/sbt migration |
| [mill-jvm-modules](../collections/shared/mill-jvm-modules/SKILL.md) | One Scala + Java + Kotlin build, interop boundaries, source roots and JVM targets |
| [mill-dependencies-and-toolchains](../collections/shared/mill-dependencies-and-toolchains/SKILL.md) | Dependency scopes, BOMs, Scala cross artifacts, private repos, compiler/JDK versions |
| [mill-build-logic](../collections/shared/mill-build-logic/SKILL.md) | Tracked tasks, code generation, resources, output ownership and task lifetimes |
| [mill-monorepo](../collections/shared/mill-monorepo/SKILL.md) | Shared traits, module ownership, multifile builds, cross matrices, selective CI and precompilation |
| [mill-testing](../collections/shared/mill-testing/SKILL.md) | Runners, discovery, fixtures, integration suites and concurrency |
| [mill-linting](../collections/shared/mill-linting/SKILL.md) | Format versus check, Scala/Java/Kotlin analyzers, coverage and API compatibility |
| [mill-packaging-publishing](../collections/shared/mill-packaging-publishing/SKILL.md) | Assemblies, native images, containers, coordinates/POMs and releases |
| [mill-scala-platforms](../collections/shared/mill-scala-platforms/SKILL.md) | Scala.js, Scala Native, web resources, Spark and cross-platform variants |
| [mill-plugins](../collections/shared/mill-plugins/SKILL.md) | Imports, contrib/third-party integrations, workers, meta-build and plugin testing |
| [mill-performance](../collections/shared/mill-performance/SKILL.md) | Evaluation phases, caching, parallelism, process architecture, sandbox and diagnostics |
| [mill-polyglot](../collections/shared/mill-polyglot/SKILL.md) | Python, JS/TypeScript, Groovy and experimental Android integration |
| [mill-vss](../collections/shared/mill-vss/SKILL.md) | VSS/Ox/synchronous Tapir with Mill preferred and starter configuration translation |

The [full coverage map](../collections/shared/mill-project-models/references/coverage.md)
addresses every requested documentation area and links the official sources.
[The research manifest](mill-research.json) records 129 retained primary sources from 132
fetches, including stable-version checks and excluding alternate-root/redirect duplicates.
It stores URLs, titles, retrieval hashes and skill routing, without copying the manual.
Research date: **2026-10-04**. Unversioned Mill documentation currently describes **1.3.0-M1**;
the examples use stable **1.1.10**, which supports all three project models.

## Runnable examples and verification

| Example | What it proves |
| --- | --- |
| [Declarative](../collections/shared/mill-project-models/assets/declarative/build.mill.yaml) | Scala YAML settings compile and run |
| [Single-file script](../collections/shared/mill-project-models/assets/script/Hello.scala) | Code and `//\|` configuration run as one Mill script |
| [Programmable generation](../collections/shared/mill-build-logic/assets/codegen/build.mill) | Tracked input produces Java code, remains cached, and invalidates after a change |
| [Mixed JVM](../collections/shared/mill-jvm-modules/assets/mixed-jvm/build.mill) | Java API → Kotlin implementation → Scala service → Java application, interop test and executable assembly |
| [Multifile monorepo](../collections/shared/mill-monorepo/assets/multi-file/build.mill) | The same graph split into root conventions and module-owned `package.mill` files |
| [VSS/Ox](../collections/shared/mill-vss/assets/ox-app/build.mill) | Scala 3 / Java 25 / Ox application starts through Mill |

Copy an asset directory to a project and add the official Mill 1.1.10 bootstrap launcher,
as explained by `mill-cli-and-ide`. Example build headers explicitly use a locally installed
compatible JVM for Mill itself; application toolchains are managed and pinned separately.
The JVM examples use Temurin 21.0.8; VSS uses Temurin 25.0.2; Scala is 3.8.2 and Kotlin 2.2.20.
These are validated fixture versions, not an automatic upgrade policy for existing builds.

To exercise every fixture in isolated temporary copies:

```sh
python3 scripts/check_mill_examples.py
```

Requires a compatible installed build JDK (CI uses Java 21), network access for the pinned
launcher/dependencies/managed JDKs, and Python 3.10+. It runs compilation/startup, the mixed
interop test, actual assembled-jar execution, code-generation cache/change checks, and
selective execution prepared **before** changing a Kotlin source. It also confirms the
unrelated Java module is absent from that selection. Source templates remain untouched.

Android, Python/JS/Groovy, Scala Native, Spark, plugin publication, and full HTTP VSS behavior
are covered by researched references; these fixtures do not claim those external/platform
workflows were executed. The official VSS skill supplies its detailed application chapters.
