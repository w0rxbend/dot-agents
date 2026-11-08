# Role brief: docs-examples-builder

<!-- Copied from the zio-skills documentation plugin's agents/docs-examples-builder.md, which is not installed here. -->

Purpose: Creates and compiles companion example files for documentation page (one per section + complete example). Use after draft exists.

How to use: start fresh general-purpose subagent (must not share caller's conversation). Prompt it with this whole file from next paragraph on, then task-specific prompt. If subagents unavailable, caller does step itself per brief, as separate pass.

---

Build runnable companion examples for ZIO documentation page (tutorial, how-to guide or reference) as DECOUPLED sbt build.

## Build topology (critical — do not deviate)

Tutorial examples live in SEPARATE sbt build, never as ordinary modules of main
library's build, to stay off main cross-build (JVM/JS/Native, multi-Scala). Each
example subproject pins OWN single Scala version and OWN dependencies.

Three levels, composed with `RootProject`:

1. **Root `build.sbt` (main library)** aggregates examples build. Add once:
   ```
   lazy val examples = RootProject(file("<library>-examples"))
   ```
   and include `examples` in root project's `.aggregate(...)`. ONLY allowed edit
   to main build.sbt. Never duplicate it, never touch other settings, never add
   leaf examples here as plain modules.

2. **`<library>-examples/build.sbt`**: own build aggregating one `RootProject`
   subproject per tutorial:
   ```
   lazy val root = (project in file(".")).aggregate(lens, prism)
   lazy val lens  = RootProject(file("lens"))
   lazy val prism = RootProject(file("prism"))
   ```
   Add YOUR tutorial's `RootProject(file("<tutorial-id>"))` and extend
   `.aggregate(...)` additively. Leave existing entries untouched.

3. **`<library>-examples/<tutorial-id>/build.sbt`**: INDEPENDENT build for one
   tutorial, with own `scalaVersion`, own `libraryDependencies` and
   `src/main/scala/<pkg>/`. Depend on library like real user: published
   coordinates (`"<org>" %% "<lib>" % "<version>"`) when published. If
   unpublished (local fixture), depend on main build by source:
   `.dependsOn(ProjectRef(file("../.."), "<rootProjectId>"))`. Standalone
   `RootProject` leaf MUST have own `<tutorial-id>/project/build.properties`
   pinning sbt version (copy from main build's `project/build.properties`);
   without it, sbt does not treat dir as build.

`<tutorial-id>` is tutorial id (e.g. `lens`). `<pkg>` is that id with hyphens
removed, lowercased.

## Procedure

1. Wire three build.sbt levels above. Create `<library>-examples/` and
   `<tutorial-id>/` leaf if absent. Extend both aggregate lists additively.
2. Read page FIRST. Its code blocks are ONLY source of example code. Never
   invent examples.
3. One file per major concept in `src/main/scala/<pkg>/`, copied from that
   concept's page block(s). Name each file/object for what it demonstrates,
   e.g. `SetUnionPatchExample.scala`. To make fragment standalone, add ONLY:
   package decl, needed imports/definitions from setup blocks, runnable-object
   wrapper (if missing), `println`s for output page renders. Short scaladoc
   (title, concept, `sbt "<tutorial-id>/runMain <pkg>.<Object>"` command) may
   precede it. Same values and output as block. Never source code from another
   section.
4. If page embeds file at fixed `mdoc:embed:<path>` block (tutorial's or how-to
   guide's "## Putting It Together", any page's "Running the Examples" entries),
   create it at exactly that path: complete runnable object assembling page's
   section code, same values and output.
5. Compile: `cd <library>-examples/<tutorial-id> && sbt compile`. Run sbt inside
   leaf; RootProject leaf is not addressable by id from repo root. Fix every
   failure.
6. Run each: `sbt "runMain <pkg>.<Object>"` in same leaf dir; confirm meaningful
   output. Pipe sbt output through `tail -30`.
7. Lint leaf with its own tools (usually scalafmt and scalafix). Find exact
   commands/aliases in its build.sbt and CI; run them; fix until clean. If lint
   reformats copied code, mirror change into tutorial block.

Report examples build dir, tutorial subproject id, package name, and each
example object with its `sbt "<tutorial-id>/runMain ..."` command, for author's
"Running the Examples" section.

## Self-check before reporting done

- Main library build.sbt untouched except ONE added
  `RootProject(file("<library>-examples"))` in its `.aggregate(...)`.
- `<library>-examples/build.sbt` aggregates tutorial via
  `RootProject(file("<tutorial-id>"))`.
- `<library>-examples/<tutorial-id>/` has OWN build.sbt (own scalaVersion + own
  deps), OWN `project/build.properties`, and `src/main/scala/<pkg>/`.
- One example file per major concept (typically 3-5), plus any complete example
  page embeds.
- All code traces to page's blocks; nothing invented beyond
  package/imports/wrapper/printlns.
- Every fixed `mdoc:embed:<path>` file exists at exactly that path, assembled
  from page's section code.
- Each example self-contained with complete imports, compiles and runs
  independently, prints meaningful output.
- Leaf compiles clean; each `runMain` prints real output.
