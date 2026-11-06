---
name: docs-cross-linker
description: >
  Make one or more existing ZIO documentation pages reachable by adding inbound
  prose links from pages that already discuss their subject. Use when a page is
  finished but nothing links to it, or the user asks to "cross-link", "make
  reachable", or "fix orphan pages".
argument-hint: "<path/to/page.md> [path/to/another.md ...]"
allowed-tools: Read, Glob, Grep, Edit, Bash(git diff:*)
---

Make the ZIO documentation pages named in the request reachable. Change nothing else.

Each page exists, is finished, passed review. Nothing points at it, so a reader unaware of it cannot
arrive. Task: add inbound links from pages already discussing its subject. Not improving those pages
or the target, not adding sections.

Request names the targets. **Never choose them yourself**, never from a survey. The
[guide](references/guide.md)'s tree-wide orphan recipe is a report for a person to filter. On a real
299-page tree, its head is `adopters.md`, `code-of-conduct.md` and 27 ecosystem listing pages, which
must never be cross-linked, and 44% of its orphans have their subject in no other page, so working
down it in order repeats the same three no-ops every invocation.

Direction is the whole task; easy to invert. Do not link out from a page to what it mentions; those
pages are already findable. Make one page nothing links to findable.

## What you do

1. **Establish the targets.** Request names one or several repo-relative paths. Shell starts in the
   checkout; read them there. Confirm each file exists first.
2. **Order the batch by how much material each target has.** Count pages mentioning each subject in
   prose (`grep -rIln --include='*.md' -F "<Subject>" docs | wc -l`). Richest first, so an early stop
   has done the work likeliest to succeed. **A target whose count is 1 or 0 is finished immediately**:
   nowhere to link from. Report "nothing to link"; read nothing more for it.
3. **Confirm each remaining target is actually an orphan.** Run the [guide](references/guide.md)'s
   inbound-link recipe. Already linked from prose: not your business. Report what links to it, move
   on. Index links do not count; the [guide](references/guide.md) says why.
4. **Find the candidates.** Grep the docs tree for the subject. Read each candidate before deciding:
   a grep line cannot show where a mention sits. Read to the [guide](references/guide.md)'s candidate
   budget, not exhaustively. Reading all 63 `ZLayer` candidate pages would fill the whole context on
   one target.
5. **Add at most one link per source page, across the whole run.** Wrap an existing prose phrase.
   Never rewrite the sentence; never touch code, headings or frontmatter. The
   [guide](references/guide.md)'s ✅/❌ pairs are the spec for link placement; check every edit
   against them. A candidate for two targets still gets one link, not one per target.
6. **Verify, and file that target's receipt block before starting the next.** Confirm each inserted
   path resolves from its page; re-run the target's inbound check. Write each block as its target
   finishes: the receipt is the run's only record, so a cut-short run still accounts for edits on disk.

## When to stop without editing

Four cases, each a real result, not a failure. Each applies per target: it ends that target's block,
not the run.

- **The target does not exist.** Report the path. Do not create it; do not pick a similar name.
- **The target already has prose links pointing at it.** Report which pages link to it.
- **One page or none mentions its subject.** Step 2 catches this before any reading. Report the count.
- **No candidate mentions the target's subject in prose.** Report candidates read and where mentions
  sit, usually code blocks. Adding nothing is correct.

One case stops the whole run: **a link that landed inside an inline-code span, a fence, a heading
or another link.** The [guide](references/guide.md)'s verification greps find it. Abandon remaining
targets: the same instruction would repeat that edit. Say so on the line the Reporting section requires.

## When the request names no page

Ask, and stop. Do not hunt for an orphan. Do not offer a tree survey instead.

Never infer a target. This run edits prose in several files, so a wrong guess spreads damage across
unrequested pages. A whole directory is the same case: "make docs/reference reachable" names no target.

- ✅ "Which pages should I make reachable? The request names none — the [guide](references/guide.md)'s orphan recipe lists the
  candidates." ❌ running the orphan recipe and picking the first three results

## What you are not

Not author of pages you edit. Wrap an existing phrase; do not rewrite, improve, or fix a typo in
passing.

Not the target's author. If it needs work, say so in the receipt and leave it.

Not a reviewer. Grade no page; report nothing beyond the receipt's lines.

Never create a page, not even a stub so a link resolves. Drop a link whose target is absent.

- ✅ `left  docs/reference/stm/index.md  mentions TRef only in a code block` ❌ editing the code block
  so a prose mention exists

## Reporting

Receipt is the run's whole output and only record: nothing downstream re-checks, and the run report
cannot see touched pages. One block per target, written as it finishes, then one closing line.

Per target:

- target path, prose-mention count from step 2
- each edited page: path, wrapped anchor text, section
- each candidate **read in full** and left, with reason. Not every grep hit: fifty unread paths are
  worse than the four that mattered
- verdict: reachable from prose now, per verification, not intent. If not, say so plainly; a target
  with edits but still unreachable is not done

Then, always, one closing line naming what the run covered:

```
targets: 3 of 3 — remaining: none
```

After a failed verification grep, that line instead, before you stop:

```
HALTED: docs/reference/foo.md — a link landed inside an inline-code span; targets 2 and 3 not attempted
```

Both lines are required output, not a behaviour to remember. Without the HALTED line an early stop
looks like nothing to report, and this run's edits are only visible in `git diff`.
