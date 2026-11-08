# Per-Type Mode: Organize Data Types in Sidebars

Folded in from former `docs-organize-types` skill. Use when section is exactly single-type reference
pages under `docs/reference/`. Invocations below are shorthand requests to this skill, not CLI commands.

**A category is a sidebar grouping plus one index page: never a directory, never a file move.**
Links are relative to page location, so moving a type's `.md` file breaks every reference to it and
every `../` inside it. Type files stay put. Only sidebar `items` entries move into the category,
keeping existing ids (`reference/chunk`, not `reference/collections/chunk`). Only new file: category
index page, flat at `docs/reference/[category-kebab-case].md`, not `[category]/index.md`, since nothing
lives in that directory.

## Two Modes of Operation

### Mode 1: Manual Categorization

When you know exactly which types go into a category.

**Invocation:**
```
organize types [type1] [type2] [type3] --category "[Category Name]"
```

**Example:**
```
organize types chunk list vector --category "Collections"
```

### Mode 2: Automatic Categorization

When you want the skill to analyze all data types and suggest groupings.

**Invocation:**
```
organize types --auto
```

Skill will:
1. **Scan** `docs/reference/` for all data type files
2. **Extract** type signatures, descriptions, relationships
3. **Analyze** integration patterns (which types depend on others)
4. **Group** by functional area, from each type's own definition of its purpose (Step 3 below), never from
   name alone. Typical resulting shapes, illustrative rather than a rulebook:
   - **Collections**: Chunk, List, Vector, etc.
   - **Type System**: TypeId, Schema, DynamicValue, etc.
   - **Resource Management**: Resource, Scope, Wire, etc.
   - **Context & DI**: Context, Wire, etc.
   - **Error Handling**: SchemaError, Validation, etc.
   - **Utilities**: MediaType, Syntax, Docs, etc.
5. **Suggest** category assignments with confidence levels
6. **Preview** new sidebars.js structure

## Workflow: Manual Mode

### Step 1: Validate Input

- Verify each type has a `.md` file in `docs/reference/`
- Confirm category name is reasonable (not duplicating an existing category)
- If any type is missing, report and stop
- **Three types minimum.** One or two is sidebar noise, not structure. Report the unmet bound and suggest
  leaving them at top level, unless request explicitly overrides after being told

### Step 2: Check Existing Structure

- Read `docs/sidebars.js`
- Find Reference section
- If category already exists, note its contents

### Step 3: Create/Update the Category Index Page

Create flat file `docs/reference/[category-kebab-case].md`, sibling of the pages it groups:

```markdown
---
id: [category-kebab-case]
title: "[Category Name]"
---

## Introduction

[2-3 sentences explaining the category and its purpose]

**Related Types:**
- [`TypeName1`](./<type1>.md) — brief description
- [`TypeName2`](./<type2>.md) — brief description
- [`TypeName3`](./<type3>.md) — brief description

## Overview

[Additional context about how these types work together and when to use them as a group]
```

Links use each type's real, unchanged path (`./<type1>.md`, since index sits beside it in
`docs/reference/`). Descriptions: first sentence after opening definition in each type's `.md` file.

### Step 4: Update sidebars.js

If category doesn't exist, create it:
```javascript
{
  type: "category",
  label: "[Category Name]",
  link: { type: "doc", id: "reference/[category-kebab-case]" },
  items: [
    "reference/[type1]",
    "reference/[type2]",
    "reference/[type3]"
  ]
}
```

Each item is type's **existing** doc id, unchanged from before this run. Confirm each resolves to a real
file before writing. An id for a nonexistent file is never valid, even temporarily.

If category exists, append new types alphabetically.

Keep categories alphabetical in Reference section, and items alphabetical within each category.

### Step 5: Verify Syntax

Check `sidebars.js` JavaScript syntax with Node.js:
```bash
node -c docs/sidebars.js
```

On errors, report and revert.

### Step 6: Report Changes

Show:
- **Added Category**: Yes/No (new category created)
- **Index File Created**: path to new `docs/reference/[category-kebab-case].md`
- **Types Added**: types moved into category
- **Verification**: ✅ Syntax valid | ❌ Syntax error (reverted)
- **Preview**: before/after snippet of Reference section

---

## Workflow: Automatic Mode

### Step 1: Scan Documentation

Find all `.md` files in `docs/reference/` with `Glob`:
```bash
glob("docs/reference/*.md")
```

Extract `id` from each frontmatter (line 2, `id: <name>`).

### Step 2: Analyze Type Relationships

**Read** each type file to extract:
- **Title** (frontmatter `title:`)
- **Definition** (opening 1-3 sentences)
- **Key features** (bullet points, if present)
- **Mentions of other types** (grep for references: `[TypeName](./type-name.md)`)

Build a **relationship graph**: if Type A mentions Type B, record that edge.

### Step 3: Propose Categories

**Never group by name substring.** Matching "chunk" | "list" | "vector" in a name and calling it
"Collections" fails whenever a name poorly proxies purpose (a `ValidationError` is not a validator;
`HttpClientConfig` is configuration, not a client). A category claims what its types are *for*; only the
page itself says that.

Per type, read its opening definition (prose after frontmatter, before first `##`): the author's own
statement of purpose. Group types whose stated purposes align. Step 2's relationship graph corroborates
(mutually referencing types likely belong together); it is not the primary signal.

Typical shapes in a ZIO-style library, illustrative, not a lookup table to match names against:
- Collection/sequence types grouped by "stores or iterates a sequence of values" in their definitions
- Schema/type-representation types grouped by "describes or validates a value's shape"
- Resource/lifecycle types grouped by "acquires, releases, or scopes a resource"
- Error/validation types grouped by "represents a failure or a validation result"
- Format/codec utilities grouped by "encodes or decodes a specific wire format"

Confidence level per proposed grouping:
- **High** (90%+): every member's definition states the same purpose in different words
- **Medium** (70-89%): most definitions align; one or two are judgment calls
- **Low** (<70%): grouped mainly on relationship graph; definitions don't clearly agree. Flag these for
  user instead of proposing them with unwarranted confidence

A proposed category under three types is not a category. Fold it into "Unassigned"; don't force a group
to reach the bound.

### Step 4: Preview Proposed Structure

Show user:
- **Proposed Categories** with grouped types and confidence levels
- **Before/After** snippet of sidebars.js
- **Unassigned Types** (if any): types that don't fit well in any category

### Step 5: User Confirmation

Wait for user input:
- **Accept All**: Apply all proposed categories
- **Selective**: Accept specific categories only
- **Reject**: Keep current flat structure

### Step 6: Create Category Index Pages

Per approved category, create flat file `docs/reference/[category-kebab-case].md` beside the pages it
groups, shaped as Manual Mode Step 3, linking types at real, unchanged paths. Write introduction from
Step 2 analysis (descriptions and relationships).

### Step 7: Update sidebars.js

After approval, update sidebars.js, keeping:
- Categories alphabetical
- Types alphabetical within each category, referenced by **existing** doc ids (`reference/<type>`,
  unchanged; see Step 3/4 of Manual Mode for exact shape)
- A `link` to category's index page id (`reference/[category-kebab-case]`)
- Existing non-categorized types (if kept)

### Step 8: Verify & Report

As manual mode: verify syntax, report changes including index page creation.

---

## Output Format

**Summary Report** (shown to user):

```
✅ Categorization Complete

Added Categories: [N]
- [Category 1]: [type1], [type2], [type3]
- [Category 2]: [type4], [type5]

Modified Categories: [N]
- [Category]: added [type6]

Verification: ✅ Syntax valid

Preview:
  Reference
    ├─ [Category 1]
    │  ├─ chunk
    │  ├─ list
    │  └─ vector
    ├─ [Category 2]
    │  ├─ schema
    │  └─ typeid
    └─ [Uncategorized] (if any)
       └─ mediatype
```

---

## Implementation Notes

- **Syntax validation** mandatory; invalid changes reverted
- **No breaking changes**: existing structure and existing categories preserved; only new categories added
- **A page belongs to at most one category**: if two fit, pick the better. Duplicate sidebar entry for one
  id is a Docusaurus bug, not a feature

---

## Common Failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `node -e "require('./docs/sidebars.js')"` reports a syntax error | Edit added unmatched brace, trailing comma in unsupported syntax, or stray quote. | **Revert the edit**, reapply carefully. Validate after each insertion. |
| Docusaurus build complains "Doc id ... not found" | Item id resolves to no real file. Usually a leftover `reference/<cat>/<type>`-shaped id from moving a sidebar entry instead of reusing its real, unchanged id. | **Remove the entry**; never create a page to make it resolve. A stub shipped for a broken id is unreviewed content taking a real page's future name. Fix id to type's existing path (`reference/<type>`), re-add it. |
| Same type appears in two categories | Auto-categorization fired twice, or manual entry added without removing old one. | Sidebar entries must be unique. Keep better-fitting category, remove other entry. |
| Category link 404s in Docusaurus | `link: { type: "doc", id: "reference/<cat>" }` set but `docs/reference/<cat>.md` missing. | Create `docs/reference/<cat>.md` (category index page, the one file this skill IS allowed to create) or omit `link` field. |
| Type that doesn't fit any obvious category | Genuinely cross-cutting type (e.g., utility used by many categories). | **Stop and ask the user.** Don't force a fit; cross-cutting types often belong in own "Utilities" category. |
| Edit duplicated existing structure (no diff) | Skill ran in idempotency-check mode, produced no change. | Confirm with `git diff sidebars.js`. If empty, structure was already correct. Report and exit. |
