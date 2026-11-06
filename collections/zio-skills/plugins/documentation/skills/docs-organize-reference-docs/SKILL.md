---
name: docs-organize-reference-docs
description: Group an existing ZIO-ecosystem (Docusaurus) reference section, or a set of per-type reference pages, into categories — propose the grouping from what the pages document, write each category's index page, and update sidebars.js without moving any file. Use when reorganizing an already-written reference section (any set of pages, not only single-type reference pages), rather than writing a new page.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git ls-files:*), Bash(git diff:*), Bash(node -c docs/sidebars.js)
---

# Organize Reference Docs

Full procedure: [`references/guide.md`](references/guide.md): proposing and checking a grouping, category
index page shape, `sidebars.js` rules, bounds that keep a reorganization from breaking links.

Targets an existing reference **section** (any set of pages). If it is exactly per-type reference pages,
also follow [`references/per-type-mode.md`](references/per-type-mode.md): manual (named types into named
category) or automatic (scan `docs/reference/`, propose groupings). Guide still applies: section-level
receipt, `sidebars.js` ESM/CJS verification gotcha, ordered verification pass.
