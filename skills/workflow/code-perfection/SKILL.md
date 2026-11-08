---
name: code-perfection
description: "Smell and style gate for code you write or change. Bans known code smells (long method, large class, primitive obsession, long parameter list, data clumps, duplicate code, dead code, feature envy, shotgun surgery, flag arguments, message chains) and enforces behavior-preserving structure. On Scala files, enforces worxbend style. Use while implementing, reviewing a diff for smells, or when a smell or style violation is suspected. Routine construction stays with code-complete. SOLID and DRY stay with clean-code-guard. One named structural refactor stays with refactoring-guru."
license: MIT
---

# Code perfection

New code gets no known smell. Changed lines get no new smell. A smell already in those lines goes only when it has a real cost. Behavior stays.

## When to use

Use while writing or changing code. Use on a review that asks about smells or style. Use when a smell is suspected.

Skip install, prose, and research that changes no code.

Other skills keep their jobs:

- `code-complete` builds the routine.
- `clean-code-guard` owns SOLID, DRY, KISS, YAGNI, and LLM failure modes.
- `refactoring-guru` owns the mechanics of one named structural refactor.
- `code-simplification` owns readability cleanup of a recent change.
- `code-refactoring-tech-debt` picks which debt to pay across a codebase.

Name the treatment here. Open `refactoring-guru` when the mechanics are unclear. Do not copy those mechanics into this skill.

## Before the edit

1. Read [references/smells.md](references/smells.md) and [references/rules.md](references/rules.md). Apply both to every line you add or change.
2. Name the behavior that must stay the same.
3. Cover that behavior with a test. No test covers a refactor: write a characterization test first. Run it on the current code.
4. Stay inside this change. A requested smell sweep stays inside the named files. One smell at a time.

## While editing

- Change structure only. Results, errors, order, and side effects stay.
- Each step stays buildable. Run the same test after a risky step.
- A fix that creates the opposite smell: undo that fix.
- Do not restyle untouched code.
- Do not weaken a warning, a compiler flag, or a test.
- No secret in source, tests, logs, errors, or docs.
- Scala file, or Scala in a worxbend repo: the Scala section of [references/rules.md](references/rules.md) applies. Conflict winners live only in [references/sources.md](references/sources.md).

## Stop

Stop when the new code is clean and each smell you chose to fix is gone. Log the rest. Do not widen the diff.

## Report

For each fix: smell, treatment, test run. Then list smells you left, and why.

## Limits

This skill does not run a linter, a formatter, or a type checker. Use the project's tools for that. It does not replace tests. Scala rules apply to Scala. The smell list is a distillation, not the books. Cite from [references/sources.md](references/sources.md).
