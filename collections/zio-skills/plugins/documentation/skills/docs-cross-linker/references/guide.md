# Cross-Linking Guide

Make ONE page reachable. It exists and is finished, but nothing points at it. Find pages that should
mention it; add one prose link from each.

## Measuring inbound links

Run from repo root, with the docs directory your task gives.

**Is anything linking to the target?** Link paths are relative to their page. Resolve each hit against
the *source* page's directory before comparing:

```bash
target="docs/reference/stm/tref.md"
grep -rIn --include='*.md' --include='*.mdx' -oE '\]\([^)]+\.mdx?(#[^)]*)?\)' docs \
| sed -E 's/^([^:]+):[0-9]+:\]\(([^)#]+).*/\1 \2/' \
| while read -r src href; do
    case "$href" in http*|/*) continue ;; esac
    [ "$(realpath -m --relative-to=. "$(dirname "$src")/$href")" = "$target" ] && echo "$src"
  done | sort -u
```

Do not shortcut to a basename grep. `index.md` exists in many directories, so filename matches report
links pointing elsewhere.

**An index link is not discoverability.** A section index lists every page beneath it, so almost no
page has zero inbound links; counting them hides the problem. Split them:

```bash
# every inbound link in the tree, tagged IDX when the source is an index page, PRO otherwise
grep -rIn --include='*.md' --include='*.mdx' -oE '\]\([^)]+\.mdx?(#[^)]*)?\)' docs \
| sed -E 's/^([^:]+):[0-9]+:\]\(([^)#]+).*/\1 \2/' \
| while read -r src href; do
    case "$href" in http*|/*) continue ;; esac
    t="$(realpath -m --relative-to=. "$(dirname "$src")/$href")"
    [ "$t" = "$src" ] && continue
    case "$(basename "$src")" in index.md|index.mdx) echo "IDX $t" ;; *) echo "PRO $t" ;; esac
  done | sort -u
```

A page with `IDX` lines and no `PRO` lines is the case to fix: in the sidebar, but no prose sends a
reader there. Orphan means "no `PRO` inbound". Say in the receipt when the target already had index links.

**Finding candidate sources.** Pages that should link to the target already discuss its subject:

```bash
grep -rIln --include='*.md' --include='*.mdx' -F "TypeName" docs
```

Read each candidate before editing. One mention inside a code example: not a candidate. Prose
explaining a related concept: candidate.

**Read to a budget, not exhaustively.** Real-tree candidate sets are larger than they look: `TRef` has
6 pages, `Promise` 24, `Task` 45, `ZLayer` 63. `ZLayer`'s 63 pages are ~186k tokens, most of a context
window on one target. So:

- Rank candidates by subject mentions (`grep -c`); read densest first.
- Read in full only what you can act on: a handful.
- For a page over about 40 KB, read around the match, not the whole file. In the real tree,
  `docs/guides/migrate/migration-guide.md` is 112 KB and a candidate for nearly every subject.
- Stop reading a target's candidates once you have the links you intend to add.

## Where a link may sit, and where it may not

**Never put a link inside an inline-code span.** It renders as literal text, and nothing catches it:
not `mdoc` (not a fenced block), not the site build (not a link):

- ❌ ``return a `[URIO](../core/zio/urio.md)[Random, T]` value`` — the link is inside the backticks
- ✅ ``return a [`URIO`](../core/zio/urio.md)`[Random, T]` value`` — the link wraps the backticked word

The two differ by one character of position; check every edit against both shapes.

**Never link inside a fenced block, of any fence length**, and never inside frontmatter. In a
`scala mdoc` block a link breaks the compile; in a ` ````scala mdoc:passthrough ` block it breaks it
less readably; in frontmatter it corrupts page metadata.

- ❌ a link anywhere between a line starting with ``` (or ~~~, or four or more backticks) and its close
- ❌ a link between the opening `---` and closing `---` of the frontmatter block

**Never link inside another link.** An image inside a link is legitimate (`[![badge](svg)](url)`); a
second `[text](path)` inside the first's brackets is not.

**Never put a link in a heading.** Heading text becomes the page's anchor. Editing it silently breaks
any link targeting it, and nothing reports the break.

**Never edit code to create a link opportunity.** If the name appears only in code blocks and headings
on every candidate, add nothing and say so in the receipt. A run reporting "no suitable prose mention"
is correct.

## Anchor text

- One to three words: shortest phrase naming the concept.
- Match the page's capitalisation exactly; link a complete word. Classic failure: `Ref` matching
  inside `careful`.
- Prefer the first prose mention. Later mentions may stay unlinked.
- Never let the anchor drift wider than the concept:
  - ✅ ``[`URIO`](../core/zio/urio.md)`` — the type name
  - ❌ a link on the bare word `value`, taken from a phrase like "models an `IO` value"

The second comes from trimming a long phrase to whatever matched. Choose the short form up front.

## Bounds

- **One link per source page, across the whole run.** Target discussed in three places: link the
  first. A candidate for two targets in one run still gets **one** link, not one per target. Corpus
  norm for a non-index page: seven internal links or fewer. A run adding one link per target per page
  passes that within a handful of invocations, and nothing in the files records the total.
- **Whole pages only.** Never `file.md#heading`: only a full site build checks anchors, so a wrong one
  stays invisible until much later.
- **Link form is writing-style rule 7** (relative path, full `.md` filename). Follow that spec, do not
  restate it, including its repair: drop a link whose target does not exist; never create the target
  to make it resolve.
- **Never rewrite the sentence you are linking.** Wrap an existing phrase. Goal: make one page
  findable, not improve these pages' prose.
- **Three good links beat ten speculative ones.** No number to reach. A page belonging in two other
  pages' prose gets two links.

## Verifying before you report

For every page you edited:

```bash
# 1. the inserted path resolves from the page it sits in
( cd "$(dirname "$src")" && test -f "$href" && echo "ok $src -> $href" || echo "BROKEN $src -> $href" )

# 2. no link ended up inside an inline-code span — expect no output
grep -nE '`\[[^]]*\]\([^)]+\)' "$src"

# 3. no link ended up inside another link — expect no output
grep -nE '\[[^]]*\[[^]]*\]\([^)]+\)[^]]*\]\(' "$src"

# 4. the target is now reachable from prose — rerun the PRO/IDX recipe above
```

Check 3 exists because a batch makes nested links reachable: two targets' anchors on one page can
nest, and check 2 is blind to it. One legitimate shape matches: an image inside a link,
`[![badge](svg.svg)](url)`. Anything else is a defect.

Then re-run the target's inbound check. Still no `PRO` line: edits did not achieve the task, and the
receipt must say so, not claim success.

**Once, at the end of the run**, confirm every line you added names a target you were asked about:

```bash
git diff -U0 -- docs | grep '^+' | grep -v '^+++' | grep -vF -e 'tref.md' -e 'tmap.md'   # your targets
```

Expect no output. A single-target run gets this free: every added line holds the one target's path, so
a one-token grep audits the whole diff. Several targets need several alternatives, so run it
deliberately.

## Working a batch

Request may name several targets. Handle each exactly as a single target, one at a time, in
instruction order (densest subject first). Finish each receipt block before starting the next. Never
widen a batch beyond what the request named. Never continue after a verification grep fails: the same
instruction would repeat that edit on the next target.

## The receipt

Per source page: path, wrapped anchor text, section. Then each candidate read and deliberately left
alone, with reason. Most common and most useful: "mentions the type only inside a code block".

Say plainly when you added nothing. A subject appearing nowhere in prose is a real result, more useful
than a link forced into an off-subject page.
