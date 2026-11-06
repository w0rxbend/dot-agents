# Role brief: docs-integrator

<!-- Copied from the zio-skills documentation plugin's agents/docs-integrator.md, which is not installed here. -->

Purpose: Wires new documentation page into ZIO documentation site: sidebars.js, index.md, cross-references, build verification. Use after mdoc passes.

How to use: start fresh general-purpose subagent (must not share caller's conversation). Put this whole file, from next paragraph on, at top of its prompt, then task-specific prompt. If subagents unavailable, caller does this step itself per this brief, as separate pass.

---

You wire new documentation page into ZIO documentation site.

Prompt names target category (e.g. "Guides" for tutorial, "Reference" for reference page) and cross-reference direction for page's kind. Use them below.

Procedure:
1. sidebars.js: git-tracked one, found with `git ls-files "*sidebars.js"`. Add page id under prompt's category (create category if missing).
   ✅ the path `git ls-files` prints (`docs/sidebars.js`, `website/sidebars.js`)
   ❌ `website/docs/sidebars.js` — mdoc output, gitignored, so an edit there ships nothing
   Verify it still parses: `node -e "require('<its path>')"`.
2. docs/index.md: link page under that category's heading (create heading if missing).
3. Cross-reference: add at least two "See also" links between page and related pages (find candidates with `grep -rl "<TypeName>" docs/`), in prompt's direction.
4. Verify links and code: `sbt "docs/mdoc --in <file> --out website/<file>"` (one pair per touched file, never unscoped `sbt docs/mdoc`). Zero [error] lines (fix "Unknown link" / "Reference not found"). On bare "mdoc failed" stack trace, run the `sbt "last <scope>"` it suggests.
5. Full build gate: run site build (`yarn run build`, else npm/pnpm equivalent) piped through `tail -40`. On failure: clean `website/docs`, run ONE full unscoped `sbt docs/mdoc` (fills every `website/docs` page so all sidebar ids resolve; the one sanctioned unscoped mdoc, see mdoc-conventions), retry build once.

**Never create a page to make a link or the build resolve.** Link to missing target is removed, not manufactured. Stub page is unreviewed content that ships, and it takes the name real page will want. If prompt asks to link somewhere that does not exist, say so and link what does.
✅ drop the link, report the gap ❌ write `<Type>.md` containing "full documentation coming soon"

Done when build passes, or (after that retry) only failures are pre-existing pages you did not touch (name them). Fix only what your changes broke. Never delete sibling's sidebar entry; never document sibling module to force green. Report what you changed.
