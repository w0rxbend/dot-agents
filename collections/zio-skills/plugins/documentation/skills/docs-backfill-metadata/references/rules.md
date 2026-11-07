Write two frontmatter fields, `description` and `keywords`, only when missing.

Covers only these two fields, never rest of page's frontmatter contract.

## `description`

One line, double-quoted, **50-150 characters**. Shorter reads as stub; longer truncates in listings.

Say what page documents, in reader's terms. Not page kind, not title restated.

- ✅ `description: "Compose lenses to read and update nested immutable fields in a single step."`
- ❌ `description: "Documentation for the Lens type."` (says what the file is, not what it teaches)
- ❌ `description: "Lens"` (restates the title, and misses the floor)

Write from page you just read. Its opening definition is usually best raw material: compress that
sentence to fit; make no fresh claim about library.

Writing-style rule 3 applies: no "as we can see", no "it's worth noting that".

## `keywords`

**3-6 entries**, Title Case, one concept each, always **block list**: one `- "item"` per line.

```
keywords:
  - "Functional Optics"
  - "Lens Composition"
  - "Nested Field Update"
```

Inline `["a", "b"]` form is valid YAML, but Docusaurus does not read it. Do not emit it.

Order general to specific: domain concept reader searches first, then what page does with it, then
type or module name.

Each entry: concept page actually covers, phrased as search-box query.

- ✅ `- "Distributed Tracing"`, `- "Trace Sampling"`, `- "Custom Sampler"`
- ❌ `- "Composition"` (a bare generic word — pair it with what is being composed)
- ❌ `- "AlwaysOnSampler AlwaysOffSampler ParentBasedSampler"` (identifiers glued into one entry)
- ❌ `- "lens"` (lowercase, and it is the title again)

Under three entries means page gave too little to index. Say so in receipt; do not pad to three.

## Editing mechanics

Insert `description` and `keywords` in contract order: after `title`, before anything else page
carries. Every existing key keeps value and position, even one you would write differently.

Leave exactly one blank line between closing `---` and body's first line. Body glued to delimiter
renders wrong.
