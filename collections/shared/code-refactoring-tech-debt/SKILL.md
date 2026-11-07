---
name: code-refactoring-tech-debt
description: "Inventory and prioritize technical debt from the actual code, change history, and incident record, then produce a bounded remediation plan with explicit assumptions and no invented cost figures. Use for a tech-debt audit, 'what should we refactor first', or code-health planning; to carry out one refactoring use refactoring-guru."
risk: safe
source: community
date_added: "2026-02-27"
---

# Technical Debt Analysis and Remediation

Find debt actually slowing change, causing defects or creating risk. Rank it with evidence; plan bounded fixes that can run alongside feature work.

## When to use

- Tech-debt audit, code-health review, or "what should we refactor first?"
- Justifying or sequencing refactoring of module, service or repository.
- Recurring bugs or slow changes point to structural cause.

Not for: single refactoring (`refactoring-guru`), simplifying recent diff (`code-simplification`), PR review (`code-review`).

## Ground rules

- **Evidence over estimates.** Each item cites code locations, history or incidents. Missing cost, usage or time figure: write "unknown". Never fill it with fabricated hours, dollars, percentages or ROI.
- **Review-only by default.** Audit does not authorize broad refactors, policy changes, CI gates or deployment.
- **Thresholds are prompts, not gates.** Numbers like "cyclomatic complexity > 10" or "file > 500 lines" flag where to look. Judge each against project's own norms.

## Process

### 1. Find hotspots

Debt that never changes rarely matters. Intersect complexity with change frequency:

```bash
# Files changed most often in the last year
git log --since="1 year ago" --name-only --format= | grep -v '^$' | sort | uniq -c | sort -rn | head -30

# Files most often touched by bug-fix commits (adjust the pattern to the repo's conventions)
git log --since="1 year ago" -i -E --grep='fix|bug|hotfix' --name-only --format= | grep -v '^$' | sort | uniq -c | sort -rn | head -30
```

Add complexity and size signals from existing project tools (linters, coverage reports, static analysis) where configured. Don't install new tooling only for audit unless user asks. Also check incident notes, flaky-test lists and TODO/FIXME clusters in hotspot files.

### 2. Inventory by category

| Type | Examples | Typical risk |
|------|----------|--------------|
| **Code** | Duplicated business rules, god classes, deep nesting, feature envy, shotgun surgery | Bugs, slow changes |
| **Architecture** | Violated layer boundaries, circular dependencies, leaky abstractions, wrong data store | Scaling limits, change ripple |
| **Test** | Untested critical paths, flaky or slow suites, tests coupled to implementation | Regressions ship |
| **Dependency** | Outdated or unmaintained libraries, deprecated APIs, known vulnerabilities | Security exposure, forced upgrades |
| **Documentation** | Missing runbooks, stale READMEs, single-person knowledge | Onboarding pain, slow incident response |
| **Infrastructure** | Manual deploy steps, no rollback, missing monitoring | Incidents, slow recovery |

Per item, record location (`path` or `path:line`), evidence (commit counts, bug links, incident, measurement), and what it blocks or slows today.

### 3. Score and rank

Score each item 1 to 5 on three dimensions, with one line of justification per score:

- **Impact**: how much it slows current or planned work.
- **Risk**: what happens if it stays (defects, outage, security, data loss).
- **Effort**: how hard fix is (1 = small, 5 = large).

`Priority = (Impact + Risk) × (6 − Effort)`, range 2 to 50. Sort by priority, then sanity-check order: security or data-loss items outrank convenience work regardless of score. Scores are relative ordering judgments, not measurements.

### 4. Plan bounded remediation

Group ranked items:

- **Quick wins**: high priority, effort 1–2. Doable this sprint, each as own change.
- **Planned refactors**: medium effort, tied to upcoming feature work in same area ("refactor while you are there", kept as separate change).
- **Larger initiatives**: need design note and incremental migration. Use strangler or facade approach: put stable interface in front of legacy code, build replacement behind it, move callers in slices (feature flag if project uses them), delete legacy path once unused.

Per item, state scope boundary, how behavior preservation is verified, and what "done" means.

### 5. Prevent recurrence (only where asked)

Suggest smallest guard that would have caught each debt class: lint rule, dependency update bot, critical-path test or architecture check. Recommend them; don't install CI gates unless user asks. `constraint-driven-development` covers writing and enforcing project quality bar.

## Output

1. **Scope and evidence sources**: what was inspected, what was unavailable.
2. **Debt inventory**: table of type, location, evidence, impact today.
3. **Ranked list**: Impact, Risk, Effort, Priority, one-line justification per item.
4. **Remediation plan**: quick wins, planned refactors, larger initiatives, each with scope and verification.
5. **Assumptions and unknowns**: every figure you could not measure.
6. **Optional prevention suggestions.**
