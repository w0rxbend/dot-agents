# Add Missing Section — Review Checklist

Check every item after Step 6 (Verify), before Step 7 (Commit). Mdoc-compile gate is mandatory.

## Section Selection

- [ ] Section is genuinely missing (not just thin). If it exists but lacks substance, use `docs-enrich-section` instead
- [ ] Section type is one of: Construction, Predefined Instances, Comparison, Advanced Usage, Motivation
- [ ] Insertion point follows canonical ordering in `SKILL.md` Step 1
- [ ] Chosen pattern from `references/section-patterns.md` followed exactly (subsection layout, table layout, code-block modifier)

## Content Quality

- [ ] Section opens with one-sentence framing (what it contains, why a reader would read it)
- [ ] Every subsection (`###`) has at least one runnable example
- [ ] Every code block preceded by prose sentence ending in `:` (Rule 15)
- [ ] No bare subheaders (no `###` immediately after `##` without intervening prose)
- [ ] Section reads coherently in isolation: reader who jumped here directly still understands context

## Technical Accuracy

- [ ] Every method signature and type parameter matches source code
- [ ] Every example uses correct mdoc modifiers (use `references/section-patterns.md` cross-pattern rules)
- [ ] Every example has complete imports
- [ ] Type-definition illustrations (e.g., factory signatures) use plain ```` ```scala ```` (no mdoc)

## Compliance Checks (Mandatory Gates)

Paths: `<docs-mdoc-conventions-skill-dir>` is directory of `docs-mdoc-conventions` skill; `<docs-writing-style-skill-dir>` is directory of `docs-writing-style` skill. Both come from same zio-skills set, installed next to this one (e.g. as `zio-skills--docs-mdoc-conventions`, `zio-skills--docs-writing-style`).

- [ ] `bash <docs-writing-style-skill-dir>/check-docs-style.sh <doc-file>` → exit 0
- [ ] `bash <docs-mdoc-conventions-skill-dir>/check-mdoc-conventions.sh <doc-file>` → exit 0
- [ ] `sbt "docs/mdoc --in <doc-file> --out website/<doc-file>"` → zero `[error]` lines

If any check fails, return to new section and fix violations. Do not commit while any check is red.

## Cross-References

- [ ] New section links to related types / sections via relative paths (`[TypeName](./type-name.md)`)
- [ ] At least one existing section in same document updated to point at new section, where sensible (e.g., Construction subsection mentioning a Predefined Instance)
- [ ] No links broke from insertion (mdoc gate covers this)

## Commit

- [ ] One commit per section addition (don't bundle unrelated section additions)
- [ ] Commit message names section type and doc file (e.g., "docs(chunk): add Comparison section vs Vector")
- [ ] If addition revealed unrelated issue (typo, broken link), fix it in separate commit
