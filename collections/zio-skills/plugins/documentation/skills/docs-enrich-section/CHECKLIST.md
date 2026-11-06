# Enrich Section — Review Checklist

## Diagnosis Was Correct

- [ ] Section genuinely thin per `SKILL.md` Signals (signature + toy example, no motivation)
- [ ] Purpose not "API reference" only: readers need *why*, not only *what*
- [ ] Enrichment needed, not a rewrite for taste

## Five-Part Expansion Pattern Applied

- [ ] **Motivation** paragraph: states problem API solves
- [ ] **Naive approach** (when applicable): what readers might try without this API, why it falls short
- [ ] **Realistic example**: use-case-grounded, not toy
- [ ] **Common Mistakes / Pitfalls**: covers at least one non-obvious behaviour readers will hit
- [ ] **Cross-references**: links to related sections / types API composes with

## Content Quality

- [ ] No filler ("It's worth noting that…", "Importantly…", "As we can see…")
- [ ] Every code block preceded by prose sentence ending in `:`
- [ ] Examples concrete (real types, real values), not `Foo`/`Bar`/`x`/`y`
- [ ] Section now answers: "When would I reach for this?"

## Technical Accuracy

- [ ] Every signature matches source code
- [ ] Every example uses correct mdoc modifiers and would compile
- [ ] Imports complete in every code block

## Compliance Checks (Mandatory Gates)

Paths: `<docs-mdoc-conventions-skill-dir>` is the `docs-mdoc-conventions` skill directory; `<docs-writing-style-skill-dir>` is the `docs-writing-style` skill directory. Both come from same zio-skills set, installed next to this one (e.g. as `zio-skills--docs-mdoc-conventions`, `zio-skills--docs-writing-style`).

- [ ] `bash <docs-writing-style-skill-dir>/check-docs-style.sh <doc-file>` → exit 0
- [ ] `bash <docs-mdoc-conventions-skill-dir>/check-mdoc-conventions.sh <doc-file>` → exit 0
- [ ] `sbt "docs/mdoc --in <doc-file> --out website/<doc-file>"` → zero `[error]` lines

## Avoid Bloat

- [ ] Longer than before, not gratuitously: if doubled, every paragraph earns its place
- [ ] No content belonging to different section type (don't put Construction examples in an Advanced Usage subsection)
- [ ] No information duplicated from another section of same document

## Commit

- [ ] One commit per enriched section (don't bundle unrelated enrichments)
- [ ] Commit message names section and doc file (e.g., "docs(chunk): enrich Construction with motivation and pitfalls")
