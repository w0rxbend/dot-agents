---
name: docs-organize-reference-docs
description: Group an existing ZIO-ecosystem (Docusaurus) reference section, or a set of per-type reference pages, into categories — propose the grouping from what the pages document, write each category's index page, and update sidebars.js without moving any file. Use when reorganizing an already-written reference section (any set of pages, not only single-type reference pages), rather than writing a new page.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*), Bash(node:*), Bash(npm:*)
---

# Organize Reference Docs

The full procedure is in [`references/guide.md`](references/guide.md) — how a grouping is proposed and
checked, the category index page's shape, the `sidebars.js` rules, and the bounds that keep a
reorganization from breaking links.

This targets an already-written reference **section** — any set of existing pages you are grouping.
When that section is exactly a set of per-type reference pages, also follow
[`references/per-type-mode.md`](references/per-type-mode.md): manual categorization (named types into a
named category) or automatic categorization (scan `docs/reference/` and propose groupings). The guide
above still applies on top of it: the section-level receipt, the `sidebars.js` ESM/CJS verification
gotcha, and the ordered verification pass.
