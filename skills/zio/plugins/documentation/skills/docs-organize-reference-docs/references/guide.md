# Organizing Reference Docs

Past a dozen pages, a reference section becomes an unscannable flat list.

**You move no files.** Whole design rests on this.

## Why nothing moves

Links are relative to page location. Move `docs/reference/chunk.md` into `docs/reference/collections/`
and every `[Chunk](./chunk.md)` elsewhere breaks. Every `../` inside resolves one level wrong.
`onBrokenLinks: 'throw'` then fails the build without naming the move.

So a category is a **sidebar grouping plus an index page**, not a directory. Pages stay put and keep
their ids. If asked to relocate pages, call it out of bounds; offer grouping instead.

Two failures from getting this wrong, both seen in this repo:

- **A sidebar id for a path that does not exist.** A predecessor emitted `reference/<category>/<type>`
  ids while moving nothing, pointing at files it never created. Derive each id from the page's real
  location (`git ls-files` it or read it), never from category name.
- **Creating a page so the build passes.** Fix an entry pointing at a missing page by removing it, never
  by writing the page. A stub ships unreviewed and takes the real page's future name.

## Proposing the grouping

Read the pages. A category claims what its types are *for*: take that from each page's opening
definition and frontmatter `description`, if any.

```bash
# the reference section's pages and their titles
git ls-files 'docs/reference/*.md' | while read -r f; do
  printf '%s\t%s\n' "$f" "$(sed -n 's/^title: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/p' "$f" | head -1)"
done
```

Do **not** group by name substring. A predecessor mapped "name contains chunk, list, vector" to
Collections. That misfiles anything called `ChunkBuilder` and misses differently-named types sharing one
purpose.

Proposal bounds:

- **Three pages minimum per category.** One or two is sidebar noise; leave them at top level.
- **Every page keeps exactly one home.** A page in two categories is a sidebar bug: Docusaurus renders it
  twice, and second entry usually loses its label.
- **Leftovers stay at top level, uncategorized.** Never invent a "Miscellaneous" category for full
  coverage. Receipt names ungrouped pages and why.
- **Name category for reader's concern, not implementation.** ✅ `Resource Management`
  ❌ `Scope And Friends` ❌ `Core Types`

If request names category and members, check those bounds, flag any unmet, then follow the request.

## The category index page

One per category: `docs/reference/<category-kebab>/index.md` **only if pages already live in that
directory**, else `docs/reference/<category-kebab>.md`. Use plugin's page-metadata frontmatter contract
(id, title, description, keywords; see `docs-backfill-metadata`). Short body:

- Two or three sentences: what category covers, why these types group. Lets reader tell whether their
  problem is here.
- Pages list, each linked at its real location, with a clause on what it does.
- No API, no examples, no prose duplicated from pages.

Apply `docs-writing-style` rules to it, as to any page. Rule 7's link form governs; every link must resolve from
the index's own directory.

## Editing `sidebars.js`

**Which file.** Git-tracked one: `git ls-files "*sidebars.js"`. Never `website/docs/sidebars.js`:
mdoc output, gitignored, so edits there ship nothing.

**The entry.** Category with `link` to its index page, pages as items:

```javascript
{
  type: 'category',
  label: 'Collections',
  link: { type: 'doc', id: 'reference/collections' },
  items: ['reference/chunk', 'reference/non-empty-chunk'],
}
```

Every id is page's real path minus extension. Alphabetical within `items` and among section categories.

**Verify it still parses**, every time, before continuing:

```bash
node -e "require('./$(git ls-files '*sidebars.js' | head -1)')"
```

Catches syntax errors, the usual hand-edit breakage. Does **not** prove sidebar loaded. If
`package.json` sets `"type": "module"`, a `.js` sidebar is ESM. `require()` then returns `{}` with no
error, since `module.exports` never took effect. So never enumerate ids by requiring the file; read them
from text, as below.

**Never delete an entry that is not yours to delete.** Pages you did not group keep their entries
exactly as they were. Removing a sibling's entry to tidy up is the one edit here that loses work invisibly.

## Verifying

In order; each catches something the next cannot:

1. `sidebars.js` parses (command above).
2. Every sidebar id resolves to an existing page. Text extraction works for CJS or ESM, covering both
   `id:` form and bare items strings:
   ```bash
   grep -oE "(id|\"id\"): *['\"][^'\"]+['\"]|['\"](reference|guides)/[a-z0-9/-]+['\"]" docs/sidebars.js \
   | sed -E "s/.*['\"]([^'\"]+)['\"]$/\1/" | sort -u | while read -r id; do
       [ -f "docs/$id.md" ] || echo "MISSING docs/$id.md"
     done
   ```
   Any `MISSING` line is a broken entry. Remove it; never create the page to satisfy it.
3. Every link in each index page you wrote resolves from that page's directory.
4. Site build (`npm run build`, or this repo's Docusaurus build command). A broken link surviving steps 2
   and 3 usually sits on some *other* page, pointing at a page whose sidebar position changed. Fix the
   link, never by creating a file.

## The receipt

Per category: name, index page path, pages held. Then ungrouped pages with reasons. Then build result.

Say plainly when proposing no change. Eight reference pages need no categories; saying so beats grouping
for its own sake.
