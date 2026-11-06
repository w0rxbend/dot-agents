---
name: docs-check-compliance
description: >
  Audit a documentation file against a rule skill. Checks each rule, fixes violations
  with separate commits, then compiles with mdoc. Reusable across any rule skill and doc file.
argument-hint: "[docs-file.md] [rule-skill-name]"
allowed-tools: Skill, Read, Grep, Edit, Bash(sbt "docs/mdoc --in:*), Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*)
---

# Check Documentation Compliance

## Arguments

1. **docs-file** — Path to documentation file (e.g., `docs/reference/xml.md`)
2. **rule-skill** — Rule skill name (e.g., `docs-writing-style`, `docs-mdoc-conventions`)

## CRITICAL REQUIREMENT

**MUST list every rule from rule skill as checklist, then verify each, step by step, until zero violations remain.** Do not skip rules. Do not assume compliance without verification. Do not move on until each rule is fully checked and its violations fixed.

## Workflow

### Step 1: Load Rule Skill

**MUST use `Skill` tool to invoke rule skill.** Do not substitute a different skill. Example, for rule-skill `docs-writing-style`:

```
Skill: docs-writing-style
```

(If skills are installed with collection prefix, Skill tool may list it as `zio-skills--docs-writing-style`; use whichever name the listing shows.)

Read all rules it defines. For enumerated rule skills, note rule numbers and build checklist. Enforce only these rules.

**Not every rule skill is numbered.** `docs-mdoc-conventions`, for one, is a decision tree plus named checks (modifier selection, public-symbols-only, admonition frequency, …), not a numbered list. When rule skill has no numbers, build checklist from its distinct named points instead. Each named check or named subsection is one checklist item, cited by name, not number (e.g. "mdoc-conventions: modifier-matches-decision-tree" instead of "rule 4").

### Step 2: Read Doc File

Read whole doc file. Example, for docs-file `docs/reference/chunk.md`:

```
Read: <PROJECT_ROOT>/docs/reference/chunk.md
```

Note: Always use absolute paths (starting from `<PROJECT_ROOT>/`)

### Step 3: Check and Fix Each Rule

**MUST: Build full checklist of ALL rules defined by rule skill.** Number each rule; list it with full name and description. Show checklist to user so they see what gets checked.

**Then process checklist rules in order, reaching zero violations on each before moving to next rule.**

For each rule in checklist:

1. **Identify violations** — Adversarial verification: assume document fully complies with THIS RULE, then prove yourself wrong with violation evidence. Cite exact line numbers, quote problematic text, explain why it violates THIS RULE. If no evidence found, rule has zero violations.

2. **Fix violations** — Apply minimal edits (add, remove, edit, or restructure as needed). Preserve document intent.

3. **Commit** — Before first commit, ask user once whether they want one commit per rule
   (default in ZIO-ecosystem repos) or prefer to review and commit changes themselves. If they
   decline commits, skip every `git commit` below and leave edits in working tree. Otherwise run:
   ```bash
   git add <docs-file>
   git commit -m "docs(<docs-file-stem>): fix <rule-name>"
   ```
   Example (numbered rule skill): `git commit -m "docs(chunk): fix rule-2-sentence-clarity"`
   Example (unnumbered rule skill): `git commit -m "docs(chunk): fix mdoc-conventions modifier-selection"`

**Repeat steps 1–3 for each rule until zero violations remain, then go to next rule.**

### Step 4: Compile

Run mdoc to verify doc compiles without errors:

```bash
sbt "docs/mdoc --in docs/reference/chunk.md --out website/docs/reference/chunk.md"
```

(Substitute actual docs-file path for both `--in` and `--out`. `--out` is same path prefixed
with `website/`.) Never run bare `sbt docs/mdoc` without `--in`/`--out`. It recompiles every doc in
tree: minutes of sbt for a one-file check.

If mdoc fails, identify error, fix it, and (if user agreed to commits) commit:
```bash
git add <docs-file>
git commit -m "docs(<docs-file-stem>): fix mdoc error"
```

### Step 5: Report

Output summary with:
- Total violations found and fixed per rule
- Rules with zero violations (no changes needed)
- Final mdoc status (pass/fail)

---

## Key Principles

- **One commit per rule violation, right after its fix** — do not batch into one big commit (once user agreed to commits)
- **Checking several rule skills** — run this workflow once per rule skill (e.g. `docs-writing-style`, then `docs-mdoc-conventions`); final mdoc compile needed only after last one
- **Verify mdoc passes at the end** — final proof of correctness
