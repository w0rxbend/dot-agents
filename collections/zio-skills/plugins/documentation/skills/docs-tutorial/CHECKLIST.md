# Tutorial Review Checklist

After writing, verify every item:

## Content Quality

- [ ] States target reader (newcomer, assumed prior knowledge)
- [ ] Learning objectives upfront as bullet list
- [ ] Objectives restated at end in "What You've Learned"
- [ ] Strict linear path (no branching, no "alternatively")
- [ ] Each section: exactly one new concept, or incremental build
- [ ] No pure-prose section without code example
- [ ] Every code example annotated line-by-line in bullets
- [ ] Intermediate results shown (printed or observed) after each major step
- [ ] Running example simple, clearly demonstrates core concepts
- [ ] Types and APIs introduced only as needed (no front-loaded theory)
- [ ] Warm, welcoming tone (uses "welcome", "let's", "notice that")
- [ ] "Putting It Together" is complete, self-contained, copy-paste-ready example
- [ ] "Background" (if present) explains motivation without code

## Technical Accuracy

- [ ] Method signatures and type names match actual source
- [ ] Code examples use correct mdoc modifiers, would compile
- [ ] Imports complete and correct in every code block
- [ ] sbt dependency (if mentioned) correct
- [ ] No deprecated methods or outdated patterns
- [ ] Run `sbt "docs/mdoc --in docs/guides/<tutorial-id>.md --out website/docs/guides/<tutorial-id>.md"` and confirm zero `[error]` lines (mandatory before claiming done). Tutorials live in `docs/guides/`, not `docs/tutorials/`; this checklist once contradicted SKILL.md's own file-location instructions here.
- [ ] "Putting It Together" is EMPTY block fenced `scala mdoc:embed:<path-to-CompleteExample.scala>` (or project's `SourceFile.print` equivalent; see `docs-examples`), never code inlined in page. Examples build compiles embedded file; inlined code ships with no build verifying it standalone.

## Companion Examples

- [ ] Package directory exists in `<examples-module>/src/main/scala/<packagename>/` (module name from tutorial's own examples setup, not fixed; see `docs-examples`)
- [ ] One example file per major concept (typically 3-5 files)
- [ ] `CompleteExample.scala` (or descriptively named equivalent) holds full "Putting It Together" code
- [ ] Each example file fully self-contained (compiles and runs independently)
- [ ] Each example file has complete imports
- [ ] Each example file has scaladoc: tutorial title, concept name, description, `sbt runMain` command
- [ ] Each example file prints meaningful results with `println`
- [ ] All examples compile (`sbt "<examples-module>/compile"`)

## Running the Examples Section

- [ ] Includes "Running the Examples" section after "Putting It Together"
- [ ] Clones and `cd`s in one path straight into examples module dir (`cd <repo>/<examples-module>`, not separate `cd <repo>` then `cd <examples-module>`)
- [ ] Every companion example file embedded, per concept in order, in collapsible `<details><summary>` via `mdoc:embed:<path>:showLineNumbers` (same pattern as "Putting It Together"), with short how-to-run sentence and its `sbt "<examples-module>/runMain ..."` command
- [ ] Includes `sbt "<examples-module>/compile"` as alternative

## Style and Integration

- [ ] Frontmatter `id` matches filename
- [ ] Tutorial in `docs/guides/` (same directory as how-to guides)
- [ ] Added to `sidebars.js` under "Guides" category
- [ ] Linked from `docs/index.md`
- [ ] Related reference pages link back
- [ ] Every "Where to Go Next" link targets page that actually exists. Check before linking; if it doesn't, leave mention unlinked (never placeholder). Never accept stub page written just to make link resolve.
- [ ] Writing style follows rules (warm tone, present tense, "we"/"you", concise, no emojis)
- [ ] Admonitions sparing, for genuinely important callouts
