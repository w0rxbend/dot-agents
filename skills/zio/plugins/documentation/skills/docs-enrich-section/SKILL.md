---
name: docs-enrich-section
description: Use when a section of ZIO-ecosystem library documentation (Docusaurus + mdoc) exists but lacks motivation or use-cases — thin sections that show a signature and a toy example but never explain why a reader would choose this API over alternatives.
---

# Enrich a Documentation Section with Motivation and Use-Cases

## Signals That a Section Needs Enriching

- Only signature + trivial example (toy type, no realistic scenario)
- No alternatives, no word on when *not* to use API
- From section alone, reader cannot choose between this and nearest related operation
- Opening sentence restates method name, adds no context

## Source Research (Do This First)

Read implementation before writing any prose:

1. **Read the source** — what method does, not only its signature
2. **Find the contrast** — nearest alternative (e.g. `rebind` vs `toSchema`): exact difference in
   return type, requirements, guarantees
3. **Find real usage** — search docs and example files for existing uses of this API; anchor
   realistic example on them
4. **Identify the gap** — ask: "In what situation would a reader need this but *not* the
   alternative?" That gap is the motivation.

## The Five-Part Expansion Pattern

Replace thin section with these five parts, in order:

### 1. Opening sentence
State what method returns and one-line rule for when to use it. Lead with return type and key
constraint that sets it apart from alternatives.

> `DynamicSchema#toSchema` returns a `Schema[DynamicValue]` — it stays fully in the dynamic world
> and requires no bindings. Use it when you have received a `DynamicSchema` over the wire and need
> a codec-compatible schema that enforces structural conformance without binding any Scala types.

### 2. Motivation paragraph
Explain gap method fills. Name scenario where alternative fails or is impractical. Name concrete
contexts (middleware, gateways, converters, validators) where method is right tool.

### 3. Contrast sentence or table
State explicitly: "Use X when … Use Y instead when …". Clear distinction: one sentence. Multiple
dimensions: two-row table.

| Situation | Right choice |
|---|---|
| No Scala types available; need structural validation only | `toSchema` |
| Have a `BindingResolver`; need a fully operational `Schema[A]` | `rebind[A]` |

### 4. Signature block
Keep existing signature block unchanged. Precede with bridging sentence ending in `:`.

### 5. Realistic example
Replace any toy example (single-field type, no context) with plausible real-application scenario.
Scenario must exercise what sets method apart from alternative.

Example checklist:
- [ ] Models plausible real scenario (gateway, registry, pipeline, validator)
- [ ] Uses `mdoc:compile-only`
- [ ] Imports everything it needs
- [ ] No hardcoded output comments (`// None`, `// "hello"`, etc.)

### Cross-references

Link to sibling types or related sections the enriched API composes with.

### When a part is intentionally omitted

Some sections have no natural "naive approach": API has no precursor readers reach for first. Say
so briefly in section itself, so future reader does not mistake omission for oversight.

## Avoid Bloat

Doubled length is earned only if every added paragraph carries information reader needs. No
filler, no restatement, nothing already said elsewhere on same page. No content from different
section type (Construction example does not belong inside enriched Advanced Usage subsection).

## Common Mistakes

| Mistake | Fix |
|---|---|
| Motivation paragraph is abstract ("useful in many cases") | Name one concrete scenario |
| Example reuses old toy type | New type reflecting motivated use-case |
| Sentence before code does not end with `:` | Every sentence right before code fence must end with `:` |
| Output comments added to show what expressions return | Delete. mdoc evaluates and renders output automatically |

## Verification

After enriching, run mdoc compilation check. All code examples must be syntactically correct and type-check:

```bash
# Single file:
sbt "docs/mdoc --in <path/to/file.md> --out website/<path/to/file.md>"

# Multiple files — repeat --in/--out pairs:
sbt "docs/mdoc --in docs/reference/file1.md --out out/file1.md --in docs/reference/file2.md --out out/file2.md"
```

> **Never use bare `sbt docs/mdoc`** without `--in`: recompiles all documentation (~90 seconds).

**Success criterion:** Output has **zero `[error]` lines**. Warnings acceptable.

**If mdoc reports errors:** Fix immediately, before marking enrichment complete. Do not commit or claim done until all errors resolved.

## Final Verification

Before committing, walk every item in sibling **[`CHECKLIST.md`](CHECKLIST.md)**, including its mandatory compliance gates.
