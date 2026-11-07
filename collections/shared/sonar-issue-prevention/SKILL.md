---
name: sonar-issue-prevention
description: Prevent recurring Sonar findings while writing or refactoring Scala libraries and tests, Python build tooling, and GitHub Actions. Check complexity, repeated semantic literals, regex behavior, output paths, temporary-state ownership, test precision, and shell injection while preserving existing contracts.
---

# Prevent recurring Sonar issues

Apply relevant checks while writing; review changed diff before finishing. Auto-selectable for applicable work. Does not replace CI or guarantee all future findings disappear.

Read only the relevant reference:

- Scala, tests, or control-flow refactoring: [maintainability.md](references/maintainability.md).
- GitHub Actions, Python CLI paths, temporary storage, or regexes: [tooling-safety.md](references/tooling-safety.md).

Keep repository's language version, build wrapper, effect model, public contracts, chosen test/coverage gates. Prefer small named operations and explicit data flow. Do not replace local maintainability fix with framework migration, universal abstraction, or new dependency.

Use project's configured rule thresholds, not hard-coded universal limits. Sonar rule IDs below trace observed findings, not proof local code was reanalyzed. No broad exclusions, `NOSONAR`, renamed secret literals, or deleted assertions as shortcut. Justified false positive gets evidence-based disposition. Changing cloud issue is separate authorized action.

Before finishing: inspect formatted code, run focused behavioral checks and required repository gates, separate verified local results from later scanner result. Keep complete generated-output fixtures during generator refactors. In fingerprinted coverage workflows, finish all measured source/doc edits before final run. Do not automatically run live integration services or publish artifacts to satisfy code-quality check.
