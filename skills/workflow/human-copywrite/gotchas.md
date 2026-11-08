# Gotchas

## Source scope notes

### The "Writing inclusively" chapter was intentionally excluded
Source PDF chapter covers gender-neutral pronouns, person-first/identity-first disability terminology, and replacements for terms like *blacklist/whitelist* and *master/slave*. Skipped at ingest per skill-owner preference. Accessibility-related Apple product features (VoiceOver, AssistiveTouch, Guided Access, Live Listen, etc.) stay in `references/apple-features-software.md` as product references, not identity guidance.
Added: 2026-05-17

## Usage gotchas

None yet. Append entries as discovered.

## Validator misfit (known, expected)

`validate-skill.js` reports ~60 errors here under distillation discipline. Nearly all are "missing frontmatter field: title/impact/tags" and "Missing **Incorrect / **Correct code example section" on each topic file.

**Why this is expected:** Distillation schema assumes each `references/*.md` file holds one code-style rule with one Incorrect/Correct code-block pair (canonical shape: `37signals-rails/references/arch-vanilla-rails.md`). Here each topic file catalogs 20-200 short editorial entries copied verbatim from Apple's guide. No meaningful per-file "impact" rating, no code blocks, no single rule per file.

**What to do:** Treat validator errors here as non-blocking. Real quality check for editorial content: substance review (`skill-reviewer` agent against distillation RUBRIC.md). If a future dev-skill discipline adds "reference-catalog" or "editorial" shapes, migrate then.

Added: 2026-05-17
