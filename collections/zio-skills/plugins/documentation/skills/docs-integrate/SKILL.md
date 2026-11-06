---
name: docs-integrate
description: Shared integration checklist for new ZIO library documentation pages. Include after writing any new reference page or how-to guide to ensure it is wired into the site navigation.
allowed-tools: Read, Edit, Glob, Grep, Bash(git ls-files:*)
---

# Documentation Integration Checklist

## Step 1: Add to `sidebars.js`

**Edit git-tracked file, not build artifact.** Find it with `git ls-files "*sidebars.js"` (typically
`docs/sidebars.js`). Never edit `website/docs/sidebars.js`: it is mdoc's gitignored output. Build
regenerates it and silently discards edits there.

Add page's `id` to sidebar in git-tracked file, under matching category:

- **Reference pages**: under `"Reference"` category, in alphabetical or logical order.
- **How-to guides**: under `"Guides"` category. If category is missing, append it as new entry in top-level `sidebars.docs` array (next to `"Reference"`).

Example: Guides category appended to existing `sidebars.docs` array:

```javascript
// docs/sidebars.js
module.exports = {
  docs: [
    "index",
    {
      type: "category",
      label: "Reference",
      items: [
        "reference/chunk",
        "reference/schema",
        // ... existing reference pages
      ],
    },
    // 👇 NEW category, added by this step
    {
      type: "category",
      label: "Guides",
      items: [
        "guides/guide-id-here",
      ],
    },
  ],
};
```

After editing, verify file still parses:

```bash
node -e "require('./docs/sidebars.js')" && echo "✓ sidebars.js is valid"
```

If `node` reports syntax error (e.g., unmatched brace, trailing comma without ES2017 support), revert edit and retry. Docusaurus fails to start on malformed sidebar.

## Step 2: Update `docs/index.md`

Link new page under matching section in `docs/index.md`:

- Reference pages go under "Reference Documentation" heading.
- Guides go under "Guides" heading (create it after reference section if missing).

## Step 3: Cross-Reference Related Pages

Link new page from related existing docs. Aim for **at least two** inbound cross-references: one isn't discoverable, three is plenty.

- For each data type or topic new page covers, add "See also" link near relevant section of existing pages that mention it.
- If guide uses specific type (e.g., `Schema`, `DynamicOptic`), link guide from that type's reference page.

Find candidate inbound pages with:

```bash
grep -rl "<TypeName or topic keyword>" docs/ | grep -v "<your-new-page-stem>.md"
```

## Step 4: Verify Compilation and Links (Mandatory Gate)

mdoc compile-checks every code example in documentation.

### Check Relative Links

Verify relative links in new page and every updated page:

- Internal links use relative paths: `[TypeName](./type-name.md)`.
- Anchor links match actual heading text (Docusaurus converts headings to lowercase kebab-case
  anchors).
- Run `sbt "docs/mdoc --in <path-to-new-page> --out website/<path-to-new-page>"` to catch broken mdoc
  links (shown as `[error] Unknown link '...'`). One `--in`/`--out` pair per touched file; `--out` is
  same path prefixed with `website/`. Never unscoped `sbt docs/mdoc` for this check.

### If mdoc Fails

If mdoc reports errors, do **not** commit. Fix reported lines in offending page, re-run same `sbt "docs/mdoc --in <path> --out website/<path>"` command, repeat until clean. If stack trace says only "mdoc failed" with no detail ("stack trace is suppressed; run 'last <scope>'"), run the `sbt "last <scope>"` it names for real error. Common causes:

| Error                                | Likely cause                                     | Fix                                                  |
|--------------------------------------|--------------------------------------------------|------------------------------------------------------|
| `Unknown link '/foo/bar.md'`         | Relative path wrong or target renamed            | Match link to actual path under `docs/`              |
| `Reference '...' not found`          | Anchor doesn't match a heading                   | Use lowercase-kebab-case of heading text             |
| `not found: value Foo`               | Code block missing an `import` or previous block | Add import or chain via `mdoc` (not `mdoc:reset`)    |
| `value foo is not a member of …`     | API drift since page was written                 | Re-derive example against current source             |

### Verify Full Site Build

After mdoc passes, run full Docusaurus build:

```bash
cd website && yarn build
```

On `yarn build` errors (e.g., `Doc id not found`, broken links, sidebar entry missing), fix them and re-run until clean. Do **not** commit until build passes.

| Error                              | Likely cause                                  | Fix                                                         |
|------------------------------------|-----------------------------------------------|-------------------------------------------------------------|
| `Doc id not found: foo/bar`        | ID in `sidebars.js` doesn't match md filename | Check `id:` frontmatter in .md file, align `sidebars.js`    |
| `Broken link on page …`            | Relative link targets nonexistent page        | Fix path or target filename                                 |
| `sidebars.js` not found            | `website/` directory missing or wrong path    | Verify repo's `website/` layout                             |

**If build fails with many unrelated "Doc id not found" errors**, `website/docs` is likely stale
from earlier scoped mdoc run. Most pages never regenerated, so their sidebar ids don't resolve yet.
Clean `website/docs`, run the ONE sanctioned unscoped pass (`sbt docs/mdoc`, no `--in`/`--out`) to
fill every page, then retry build once.

**Never create a page to make a link or the build resolve.** Remove link to missing target; never
manufacture target. Stub page ships unreviewed content and takes name real page will later want:
✅ drop the link, report the gap ❌ write `<Type>.md` containing "full
documentation coming soon" so the sidebar entry stops erroring.

**Fix only what your changes broke.** If build surfaces pre-existing failure on page you never
touched, name it in report and leave it. Never delete sibling's sidebar entry or document sibling
module to force build green.
