---
name: code-refactoring-tech-debt
description: "Inventory and prioritize technical debt from the actual code, change history, and incident record, then produce a bounded remediation plan with explicit assumptions and no invented cost figures. Use for a tech-debt audit, 'what should we refactor first', or code-health planning; to carry out one refactoring use refactoring-guru."
risk: safe
source: community
date_added: "2026-02-27"
---

# Technical Debt Analysis and Remediation

Find the debt that is actually slowing change, causing defects, or creating risk. Rank it with evidence, and plan bounded fixes that can run alongside feature work.

## When to use

- The user asks for a tech-debt audit, a code-health review, or "what should we refactor first?"
- You need to justify or sequence refactoring work for a module, service, or repository.
- A recurring class of bugs or slow changes points to a structural cause.

Not for: executing a single refactoring (`refactoring-guru`), simplifying a recent diff (`code-simplification`), or reviewing a PR (`code-review`).

## Ground rules

- **Evidence over estimates.** Every item cites code locations, history, or incidents. When you lack a cost, usage, or time figure, write "unknown". Never fill it with fabricated hours, dollars, percentages, or ROI.
- **Review-only by default.** An audit does not authorize broad refactors, policy changes, CI gates, or deployment.
- **Thresholds are prompts, not gates.** Numbers like "cyclomatic complexity > 10" or "file > 500 lines" flag where to look. Judge each against the project's own norms.

## Process

### 1. Find hotspots

Debt that never changes rarely matters. Intersect complexity with change frequency:

```bash
# Files changed most often in the last year
git log --since="1 year ago" --name-only --format= | grep -v '^$' | sort | uniq -c | sort -rn | head -30

# Files most often touched by bug-fix commits (adjust the pattern to the repo's conventions)
git log --since="1 year ago" -i -E --grep='fix|bug|hotfix' --name-only --format= | grep -v '^$' | sort | uniq -c | sort -rn | head -30
```

Add complexity and size signals from the project's existing tools (linters, coverage reports, static analysis) where they are configured. Don't install new tooling just for the audit unless the user asks. Also check incident notes, flaky-test lists, and TODO/FIXME clusters in hotspot files.

### 2. Inventory by category

| Type | Examples | Typical risk |
|------|----------|--------------|
| **Code** | Duplicated business rules, god classes, deep nesting, feature envy, shotgun surgery | Bugs, slow changes |
| **Architecture** | Violated layer boundaries, circular dependencies, leaky abstractions, wrong data store | Scaling limits, change ripple |
| **Test** | Untested critical paths, flaky or slow suites, tests coupled to implementation | Regressions ship |
| **Dependency** | Outdated or unmaintained libraries, deprecated APIs, known vulnerabilities | Security exposure, forced upgrades |
| **Documentation** | Missing runbooks, stale READMEs, knowledge held by one person | Onboarding pain, slow incident response |
| **Infrastructure** | Manual deploy steps, no rollback, missing monitoring | Incidents, slow recovery |

For each item, record the location (`path` or `path:line`), the evidence (commit counts, bug links, incident, measurement), and what it blocks or slows today.

### 3. Score and rank

Score each item from 1 to 5 on three dimensions, and write one line of justification for each score:

- **Impact**: how much it slows current or planned work.
- **Risk**: what happens if it stays (defects, outage, security, data loss).
- **Effort**: how hard the fix is (1 = small, 5 = large).

`Priority = (Impact + Risk) × (6 − Effort)`, which ranges from 2 to 50. Sort by priority, then sanity-check the order: a security or data-loss item outranks convenience work regardless of score. The scores are relative judgments for ordering, not measurements.

### 4. Plan bounded remediation

Group the ranked items:

- **Quick wins**: high priority, effort 1–2. Can be done this sprint, each as its own change.
- **Planned refactors**: medium effort, tied to upcoming feature work in the same area ("refactor while you are there", kept as a separate change).
- **Larger initiatives**: need a design note and incremental migration. Use a strangler or facade approach: put a stable interface in front of the legacy code, build the replacement behind it, move callers in slices (a feature flag if the project uses them), and delete the legacy path once it is unused.

For each item, state the scope boundary, how behavior preservation will be verified, and what "done" means.

### 5. Prevent recurrence (only where asked)

Suggest the smallest guard that would have caught each class of debt, such as a lint rule, a dependency update bot, a test for the critical path, or an architecture check. Recommend these, but don't install CI gates unless the user asks. `constraint-driven-development` covers writing and enforcing a project quality bar.

## Output

1. **Scope and evidence sources**: what was inspected and what was unavailable.
2. **Debt inventory**: a table with type, location, evidence, and impact today.
3. **Ranked list**: Impact, Risk, Effort, Priority, and a one-line justification per item.
4. **Remediation plan**: quick wins, planned refactors, larger initiatives, each with scope and verification.
5. **Assumptions and unknowns**: every figure you could not measure.
6. **Optional prevention suggestions.**
