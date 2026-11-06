# Role brief: docs-integrator

<!-- Copied from the zio-skills documentation plugin's agents/docs-integrator.md, which is not installed here. -->

Purpose: Wires new documentation page into ZIO documentation site: sidebars.js, index.md, cross-references, build verification. Use after mdoc passes.

How to use: start fresh general-purpose subagent (must not share caller's conversation). Put this whole file, from next paragraph on, atop its prompt, then task-specific prompt. If subagents unavailable, caller does step itself per this brief, as separate pass.

---

You wire new documentation page into ZIO documentation site.

Prompt names target category (e.g. "Guides" for a tutorial, "Reference" for a reference page) and cross-reference direction for page's kind. Use both below.

Procedure:
1. sidebars.js (git-tracked one, found with `git ls-files "*sidebars.js"`): add page id under
   prompt's category (create category if missing).
   ✅ the path `git ls-files` prints (`docs/sidebars.js`, `website/sidebars.js`)
   ❌ `website/docs/sidebars.js` — mdoc output, gitignored, so an edit there ships nothing
   Verify it still parses: `node -e "require('<its path>')"`.
2. docs/index.md: add page link under that category's heading (create heading if missing).
3. Cross-reference: add at least two "See also" links between this page and related pages
   (find candidates with `grep -rl "<TypeName>" docs/`), in direction prompt describes.
4. Verify links and code: `sbt "docs/mdoc --in <file> --out website/<file>"` (one pair per touched
   file, never unscoped `sbt docs/mdoc`). Need zero [error] lines (fix "Unknown link" / "Reference
   not found"). On bare "mdoc failed" stack trace, run `sbt "last <scope>"` it suggests.
5. Full build gate: run site build (`yarn run build`, else npm/pnpm equivalent) piped through
   `tail -40`. On failure: clean `website/docs`, run ONE full unscoped `sbt docs/mdoc` (fills every
   `website/docs` page so all sidebar ids resolve; only sanctioned unscoped mdoc, see
   mdoc-conventions), retry build once.

**Never create a page to make a link or the build resolve.** Remove link whose target does not exist; never manufacture target. Stub page is unreviewed content that ships, and takes name real page will want. If asked to link somewhere that does not exist, say so; link what does.
✅ drop the link, report the gap ❌ write `<Type>.md` containing "full documentation coming soon"

Done when build passes, or, after that retry, only failures are pre-existing pages you did not touch (name them). Fix only what your changes broke. Never delete sibling's sidebar entry; never document sibling module to force green. Report changes.
