---
name: legacy-seams
description: "When changing untested legacy code, pin the observed results with characterization tests and open the smallest seam that substitutes only the blocking dependency, separate from any later logic change. Use when a clock, random source, I/O, global, or hidden constructor blocks a test or a safe edit. Use test-driven-development for a new behavior or a bug, refactoring-guru for one named structural refactor after the seam exists, and code-refactoring-tech-debt to choose which legacy to replace."
license: MIT
---

# Legacy seams

Pin what the untested code does now. Open one seam. Substitute only the dependency that blocks the change. Keep the logic edit in a later change.

## When to Use

Use when the code you must change has no test at the change point, and a clock, a random source, I/O, a global, or a hidden constructor blocks that test or a safe edit.

Skip code that already has a test there. Skip a greenfield routine.

Other skills keep their jobs:

- `test-driven-development` owns a failing test for a new behavior or a bug.
- `refactoring-guru` owns one named structural refactor after this seam exists.
- `code-perfection` owns smell judgment on the lines you change.
- `code-refactoring-tech-debt` owns which legacy to replace, and the larger strangler program.

## Before the edit

1. Read [references/rules.md](references/rules.md). Apply it to this change.
2. Name the observed result that must stay, quirks included. Name the one dependency that blocks the test.
3. Write a characterization test at the change point. Run it on the current code. It passes for the behavior you found, not the behavior you want.
4. Name the seam and its enabling point. Select the substitute only at that point.

## While editing

- Open the seam in one behavior-preserving edit. Do not change a decision, a calculation, or an error in that edit.
- Prefer a parameter or an object seam. Use a link or a preprocessing seam only when no explicit seam reaches the dependency.
- Call pure single-implementation code directly. Do not wrap it.
- If the legacy body cannot be covered in time, put the new behavior in tested code and call it from one line in the old path.
- Translate a foreign legacy type at the seam. Do not let it enter the new model.
- Do not add a pass-through type, a locator, or a container. Delete a transitional seam once callers no longer need it.

## Stop

Stop when the characterization test passes, the blocking dependency is substitutable at the named enabling point, and the logic change is still unmixed. Log that logic change as the next edit.

## Report

Report the seam name, the enabling point, the dependency substituted, the characterization test you ran, and any logic change left for later. If a transitional seam remains, say what deletes it.

## Limitations

This skill does not pick which system to replace. It does not perform the named refactor. It does not write the failing test for a new rule. The rules are a distillation. Cite [references/sources.md](references/sources.md). Do not copy a locator from a source example. Conflict winners live only in that file.
