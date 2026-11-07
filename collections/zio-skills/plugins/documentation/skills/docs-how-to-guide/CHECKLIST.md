# How-To Guide Review Checklist

After writing, verify every item:

## Content Quality

- [ ] Clear, stated goal in introduction
- [ ] "Problem" section concretely states problem solved
- [ ] Problem section explains why it matters (real consequences)
- [ ] Problem section shows the pain (code or concrete scenario)
- [ ] Reader following every step ends with working result
- [ ] Every section introduces exactly one new concept or capability
- [ ] No section is pure prose without code example (Introduction, The Problem's prose, and Going Further are prose by design)
- [ ] Running example realistic and relatable
- [ ] Types and APIs introduced only when needed (no front-loaded theory dumps)
- [ ] Introduction has no conceptual preamble, no theory. Guide opening by explaining what a type is has become tutorial; fail this item, not the type explanation
- [ ] The Problem's "before" example is `mdoc:compile-only` block (default: real, compiling, non-library code reader writes today), or plain `scala` pseudocode fence only when problem is architectural. It does NOT use API of documented library. Fail when it does: "before" written with the tool the guide sells has no contrast
- [ ] "Before" example genuinely verbose or error-prone, not code reader would happily keep; otherwise problem isn't real
- [ ] No heading contains template's own vocabulary or supplied ordinal: no "Step", "Capability", "Section", "Concept", no leading digit. Heading names what section delivers, in reader's words
- [ ] "Putting It Together" is complete, self-contained, copy-paste-ready example, delivered as EMPTY block fenced `scala mdoc:embed:<path-to-CompleteExample.scala>` (or project's `SourceFile.print` equivalent). Never code inlined in page. Examples build compiles embedded file; inlining ships code no build verified as standalone
- [ ] "Going Further" (if present) links only to existing pages. Mention page in prose, unlinked, when it doesn't exist yet; never accept stub written to make link resolve

## Technical Accuracy

- [ ] All method signatures and type names match source code
- [ ] All code examples use correct mdoc modifiers and would compile. Runnable block in plain `scala` fence fails: compiler never saw it
- [ ] Imports complete and correct in every code block
- [ ] sbt dependency in Prerequisites correct
- [ ] No deprecated methods or outdated patterns
- [ ] Steps follow order types actually compose in
- [ ] Run `sbt "docs/mdoc --in docs/guides/<guide-id>.md --out website/docs/guides/<guide-id>.md"` and confirm zero `[error]` lines (mandatory before claiming guide done)

## Companion Examples

- [ ] Package directory exists in `<examples-module>/src/main/scala/<packagename>/` (module name from this guide's own examples setup, not fixed; see `docs-examples`)
- [ ] One example file per major guide step (typically 3-5 files)
- [ ] `CompleteExample.scala` (or descriptively named equivalent) holds full "Putting It Together" code
- [ ] Each example file fully self-contained (compiles and runs independently)
- [ ] Each example file has complete imports
- [ ] Each example file has scaladoc with guide title, step description, and `sbt runMain` command
- [ ] Each example file prints meaningful results with `println`
- [ ] All examples compile (`sbt "<examples-module>/compile"`)

## Running the Examples Section

- [ ] "Running the Examples" section comes after "Putting It Together"
- [ ] Section clones and `cd`s in one path straight into examples module dir (`cd <repo>/<examples-module>`, not separate `cd <repo>` then `cd <examples-module>`)
- [ ] Every companion example file embedded, per step in order, in collapsible `<details><summary>` via `mdoc:embed:<path>:showLineNumbers` (same pattern as "Putting It Together"), with short run sentence and its `sbt "<examples-module>/runMain ..."` command
- [ ] Section includes `sbt "<examples-module>/compile"` as alternative

## Style and Integration

- [ ] Frontmatter `id` matches filename and names task, not type (`docs/guides/` also holds tutorials: check directory listing before choosing id; existing path belongs to another page)
- [ ] Guide added to `sidebars.js`
- [ ] Guide linked from `docs/index.md`
- [ ] Related reference pages link back to guide
- [ ] Writing style follows rules (present tense, "we"/"you", concise, no emojis)
- [ ] Prose direct and imperative ("Define a schema", "Run the effect"). Fail warm, tutorial register ("Welcome", "Let's", "notice that"); that belongs to `docs-tutorial`
- [ ] Admonitions used sparingly, for genuinely important callouts
