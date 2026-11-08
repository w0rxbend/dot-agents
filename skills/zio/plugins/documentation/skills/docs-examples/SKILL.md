---
name: docs-examples
description: Shared procedure for creating and documenting companion examples. Covers directory structure, file templates, example creation, compilation, linting, and embedding with SourceFile. Used by docs-data-type-ref, docs-module-ref, docs-how-to-guide, and docs-tutorial.
allowed-tools: Read, Glob, Grep, Bash(sbt compile), Bash(sbt check), Bash(sbt fmtChanged), Bash(scalafmt:*), Bash(git add:*), Bash(git status:*), Bash(git diff:*)
---

## Setup Example Sub-module

**Never invent example code.** Every example-file line traces to a code block already on the page
being written. Only allowed additions: package declaration, imports, runnable wrapper, `println` calls
for output the page renders. If page doesn't show it, example doesn't either.

### Preferred: a decoupled examples build, one per documented page

Plain `RootProject` per page directly in root build (below) works for a single one-off example module but
doesn't scale: every later page adds another permanent ROOT build.sbt entry. Prefer nesting: root build
gains exactly ONE addition, ever, however many pages get examples later:

```
root build.sbt          — ONE addition: aggregates <library>-examples, nothing else, ever
<library>-examples/build.sbt
  └─ aggregates one RootProject per documented page (webauthn, lens, prism, ...)
     <library>-examples/<page-id>/build.sbt   — its OWN scalaVersion, its OWN deps
```

```scala
// root build.sbt — the only edit this makes to the main build, ever
lazy val examples = RootProject(file("<library>-examples"))
// include `examples` in the root project's own .aggregate(...)
```

```scala
// <library>-examples/build.sbt — grows by one line per new page, additively
lazy val root = (project in file(".")).aggregate(webauthn, lens)
lazy val webauthn = RootProject(file("webauthn"))
lazy val lens      = RootProject(file("lens"))
```

Each leaf (`<library>-examples/<page-id>/`) is fully independent sbt build. Own `build.sbt`: own
`scalaVersion`, own `libraryDependencies`, depending on library as real user would. Depend via published
coordinates when library publishes them, or `.dependsOn(ProjectRef(file("../.."),
"<rootProjectId>"))` by source for unpublished fixture. Own
`project/build.properties` pinning sbt version (copy main build's value). `RootProject` leaf without
`build.properties` isn't recognized as build. Result: each page's examples pin own Scala version and
dependencies, isolated from main library's cross-build (JVM/JS/Native, multiple Scala versions) and
each other.

### Simpler alternative: a single flat sub-module

For truly one-off example set, no more pages expected to gain examples, add directly to root build:

```scala
lazy val `zio-http-example-webauthn` =
  RootProject(file("zio-http-example-webauthn"))

lazy val root = (project in file("."))
  .aggregate(
    // other sub-modules
    `zio-http-example-webauthn`
  )
```

Inside example project directory, create standard Scala project structure with `build.sbt` listing needed dependencies.


## Creating Example Files

### Step 1: Directory and Package Structure

Create package directory matching this pattern:

```
<examples-module>/src/main/scala/<packagename>/
```

`<examples-module>` is one of:
- `<module>-examples` (module references, e.g., `http-model-examples`)
- `<library-name>-examples` (guides, tutorials, or integration examples spanning multiple modules)

**Name conversion rule**: drop hyphens, e.g.:
- `query-dsl-sql` → `querydsl` (lowercase, hyphens removed)
- `http-model` → `httpmodel`
- `scope-resource-management` → `scoperesourcemanagement`

### Step 2: Example File Structure

Create **one Scala file per major step/concept/use case**, plus final file for complete example. Each file: standalone runnable program, `object` extending `App` or Scala 3 `@main def` function.

**Naming convention depends on document type:**

| Document Type | File Naming |
|---------------|------------|
| How-to guides | `Step1BasicExample.scala`, `Step2AdvancedExample.scala`, ..., `CompleteExample.scala` |
| Tutorials | `Concept1Example.scala`, `Concept2Example.scala`, ..., `CompleteExample.scala` |
| Data type refs | `BasicUsage.scala`, `AdvancedPatterns.scala`, `CompleteExample.scala` (or descriptive names like `CompleteHttpRequest.scala`) |
| Module refs | `MultiTypeComposition.scala`, `CommonPattern1.scala`, ..., `CompleteExample.scala` (titles stress multi-type usage) |

Create 3-5 files total (more if concept count warrants).

### Step 3: Example File Template

Each example file follows this pattern:

For Scala 3:

```scala
package <packagename>

import <requiredImports>

/**
 * <Documentation Title> — Step/Concept/Pattern: <Title>
 *
 * <1-2 sentence description of what this example demonstrates.>
 *
 * Run with: sbt "<examples-module>/runMain <packagename>.<FunctionName>"
 */
@main def <FunctionName>(): Unit = {
   // Example code
}
```

For Scala 2.13:

```scala
package <packagename>

import <requiredImports>

/**
 * <Documentation Title> — Step/Concept/Pattern: <Title>
 *
 * <1-2 sentence description of what this example demonstrates.>
 *
 * Run with: sbt "<examples-module>/runMain <packagename>.<ObjectName>"
 */
object <ObjectName> extends App {
   // Example code
}
```

### Step 4: The Complete Example

Final example file (`CompleteExample.scala` or descriptive equivalent like `CompleteHttpRequest.scala`) must contain **entire "Putting It Together" or most complex code block** from document, wrapped in runnable program (Scala 3 `@main def` function or Scala 2.13 `object` extending `App`). Most important example file.

### Step 5: Verify Examples Compile

Verify all example files compile:

```bash
sbt "<examples-module>/compile"
```

Fix compilation failures before proceeding.

### Step 6: Lint Check (Mandatory Before Integration)

After all examples compile, stage them in git, then run Scalafmt:

```bash
git add <examples-module>/src/main/scala/**/*.scala
sbt fmtChanged
```

If files were reformatted and user agreed to commits, commit only those example files
(never `git add -A`; sweeps in unrelated work):

```bash
git add <examples-module>/src/main/scala
git commit -m "docs(<doc-id>): apply scalafmt to examples"
```

Verify CI lint gate locally:

```bash
sbt check
```

**Success criterion**: zero formatting violations reported.

---

### Step 7: Documenting Examples

#### When Examples Use SourceFile Embedding

Two ways to pull companion file's source into page; not interchangeable. Use whichever project
already has wired up. Check before introducing the other:

- **`SourceFile.print` inside `mdoc:passthrough`** (below) — project-local helper. Use when
  project's docs subproject already defines `docs.SourceFile` (common for established ZIO docs site).
- **`mdoc:embed:<path>`** (see `docs-mdoc-conventions`) — built-in mdoc modifier; docs subproject
  must depend on `"dev.zio" %% "zio-sbt-source"`. Prefer for project with neither convention yet:
  no custom Scala utility to maintain.

Either way, embedded file must exist on disk **before** mdoc runs; both fail outright if named path
is absent. Create every example file (this whole skill) before page's own mdoc verification pass,
never after.

For data type and module references needing detailed example documentation:

Place "Running the Examples" section at end, after all type/module documentation. Use this template:

```
    ## Running the Examples
    
    All code from this guide is available as runnable examples in the `<examples-module>` module.
    
    **1. Clone the repository and navigate to the project:**
    
    ```bash
    git clone https://github.com/zio/<repo-name>.git
    cd <repo-name>
    ```
    
    **2. Run individual examples with sbt:**
    
    ### <Example Title>
    
    <Short description of what this App demonstrates and the use case it covers. For module examples, explain which types work together. For type examples, describe the usage pattern.>
    
    ```scala mdoc:passthrough
    import docs.SourceFile
    
    SourceFile.print("<examples-module>/src/main/scala/<package>/<ObjectName>.scala")
    ```
    
    ([source](https://github.com/zio/<repo-name>/blob/main/<examples-module>/src/main/scala/<package>/<ObjectName>.scala))
    
    ```bash
    sbt "<examples-module>/runMain <package>.<ObjectName>"
    ```
    
    ### <Next Example Title>
    
    <Short description highlighting key patterns or type composition.>
    
    ```scala mdoc:passthrough
    import docs.SourceFile
    
    SourceFile.print("<examples-module>/src/main/scala/<package>/<ObjectName2>.scala")
    ```
    
    ([source](https://github.com/zio/<repo-name>/blob/main/<examples-module>/src/main/scala/<package>/<ObjectName2>.scala))
    
    ```bash
    sbt "<examples-module>/runMain <package>.<ObjectName2>"
    ```
```

**Optional parameters:**
- `lines = Seq((from, to))` — include only specific line ranges (1-indexed)
- `showLineNumbers = true` — render with line numbers
- `showTitle = false` — suppress the file path title

#### When Examples Use Basic Shell Commands

For how-to guides and tutorials where examples are listed simply:

```markdown
    ## Running the Examples
    
    All code from this guide/tutorial is available as runnable examples in the `<examples-module>` module.
    
    **1. Clone the repository and navigate to the project:**
    
    ```bash
    git clone https://github.com/zio/<repo-name>.git
    cd <repo-name>
    ```
    
    **2. Run individual examples with sbt:**
    
    ```bash
    # Step/Concept 1: <brief description>
    sbt "<examples-module>/runMain <packagename>.<Step1ObjectName>"
    
    # Step/Concept 2: <brief description>
    sbt "<examples-module>/runMain <packagename>.<Step2ObjectName>"
    
    # ...additional steps/concepts...
    
    # Complete example
    sbt "<examples-module>/runMain <packagename>.<CompleteObjectName>"
    ```
    
    **3. Or compile all examples at once:**
    
    ```bash
    sbt "<examples-module>/compile"
    ```
```

    
- List **every `App` object** in the examples module, one entry per object
- For each entry: use a `###` heading (simple, concise title), followed by a short descriptive paragraph
- The paragraph explains what the example demonstrates and the use case/pattern it covers
- For modules: emphasize which types compose in each example
- Embed full source with `SourceFile.print` (keeps docs and examples in sync automatically)
- Include source link and run command
- Keep the two numbered steps (clone, run individually) in that order
