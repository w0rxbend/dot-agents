---
name: docs-backfill-metadata
description: >
  Fill in the missing `description` and `keywords` frontmatter fields on one
  documentation page, without touching anything else on it. Use when a page has
  no description or keywords for Docusaurus to index it with, or the user asks
  to "backfill metadata" or "add frontmatter".
argument-hint: "<path/to/page.md>"
allowed-tools: Read, Edit
---

Fill two missing frontmatter fields on one documentation page. Change nothing else: page's prose,
headings, code blocks and existing frontmatter are out of bounds.

## What you do

1. **Establish the page.** Request names it as repo-relative path; read it in checkout, where shell
   starts.
2. **Read the whole page before writing anything.** Description claims what page teaches; keywords
   are terms it uses. Title, first paragraph or filename cannot decide either.
3. **Check what is actually missing.** Write only fields with no value. Populated `description`
   stays, even if you would phrase it better. Two-entry `keywords` list stays too: chosen value is
   not empty.
4. **Write only those fields**, per [`references/rules.md`](references/rules.md), editing frontmatter
   block in place.
5. **File the receipt** as final reply: what you filled, what you left alone.

Three shapes mean stop, not edit:

- **No frontmatter block at all.** Creating one means choosing page's `id` and `title`: not your
  call; page may not be a Docusaurus doc page. Report and stop.
- **No `title`.** Same reason.
- **Both fields already populated.** Nothing to do. Say so plainly; run that finds nothing to fill
  is correct run.

## When the request names no page

Ask, and stop. Do not walk docs tree hunting a page with missing metadata to fill.

Do not infer page path. Guess means editing an unrequested file in place: damage, not wasted effort.

- ✅ "Which page? The request names none." ❌ picking `docs/reference/lens.md` because it lacks a description

## What you are not

Not page's author. Do not fix prose, headings, links or code: not a typo, not a broken sentence, not
a fence missing its language. Body must come out of run byte-for-byte as it went in.

Not reviewer. Real problem on page: name it in receipt, leave it.

Do not translate or restate `title`; it stays as is.

- ✅ `left  title  "Overview" is vague, but it is not mine to rename` ❌ rewriting it to "Lens Overview"

## Reporting

Receipt is run's whole output; must stand alone: reader of reply alone should know what file now
contains that it did not before. Quote written `description` and list `keywords`, so reply is
judgeable without opening file.

Filled nothing? Say so plainly, with reason: already populated, no frontmatter, no title. Results,
not failures.
