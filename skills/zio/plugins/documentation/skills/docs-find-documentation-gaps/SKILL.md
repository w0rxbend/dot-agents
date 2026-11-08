---
name: docs-find-documentation-gaps
description: Find and report undocumented areas of a ZIO library project that need documentation coverage in the docs directory. Generates a TODO-style report.
argument-hint: "[optional: module-name or 'all']"
allowed-tools: Read, Glob, Grep, Bash(scan-undocumented:*)
---

# Finding Undocumented Areas

Scan project for documentation gaps: public types, modules and packages without coverage in `docs/`. Save full report to `target/undocumented-report.md`. It stays outside `docs/`, so Docusaurus build never publishes this internal tracking file. Create `target/` if needed; sbt projects normally git-ignore it.

## Scope

$ARGUMENTS

If module name given (e.g., `schema`, `chunk`, `scope`), focus analysis and recommendations on that module. Otherwise scan whole project.

## Step 1: Run the Scanner Script

Run scanner for raw coverage data:

Paths: `<this-skill-dir>` is this skill's own directory (where this file lives).

```bash
bash <this-skill-dir>/scan-undocumented.sh \
  > target/undocumented-report.md
```

Pass optional project root to scan sub-module: `scan-undocumented.sh <path>`. Run with `--help` for full usage.

**Exit codes:**

| Code | Meaning                                                                |
|------|------------------------------------------------------------------------|
| `0`  | Scan completed; report on stdout. Exit code does not reflect coverage; inspect report for undocumented types. |
| `2`  | Invocation error (extra arguments, project root not found, missing `docs/` directory). |

## Step 2: Enrich the Report with Manual Analysis

### 2a. Review the undocumented types

For each undocumented type script flags:

1. **Read the source file** to learn what type does.
2. **Classify its documentation priority**:
   - **Critical**: Core public API types users touch directly (e.g., `Schema`, `Codec`, `Chunk`). Need dedicated reference pages.
   - **High**: Important supporting types in public API signatures (e.g., `Validation`, `Modifier`, `DynamicValue`). Need at least a section in related page.
   - **Medium**: Internal-but-visible types advanced users may meet (e.g., `Deriver`, `ReflectTransformer`). Need brief mention.
   - **Low**: Truly internal types, platform-specific implementations or test helpers. Can be skipped.
3. **Update the priority** in report: move types into correct priority section.

### 2b. Check documentation depth

For types that DO have doc pages, check whether coverage is adequate:

1. Read existing doc page.
2. Read type's source file.
3. Look for:
   - **Missing methods**: Undocumented public methods on type or companion.
   - **Missing examples**: Prose but no code examples.
   - **Outdated signatures**: Doc signatures not matching current source.
   - **Missing cross-references**: Related types missing links to each other.

Add findings to report as "Documentation Depth" section.

### 2c. Identify conceptual gaps

Beyond type-level coverage, look for missing conceptual docs:

1. **Getting started guide**: Check for quick-start for new users.
2. **Migration guides**: Any version migration docs needed?
3. **How-to guides**: Common tasks needing step-by-step guides.
4. **Architecture overview**: High-level design docs for contributors.

Add these as separate "Conceptual Gaps" section.

## Step 3: Write the Final Report

Write final report to `target/undocumented-report.md` (never under `docs/`) with this structure:

```markdown
---
id: undocumented-report
title: "Documentation Coverage Report"
---

# Documentation Coverage Report

## Summary
[Coverage statistics table from script]

## Critical: Missing Reference Pages
[Types that need dedicated doc pages, with brief description of each]

## High Priority: Incomplete Coverage
[Types with pages that need expansion, or important types without pages]

## Medium Priority: Brief Mentions Needed
[Types that should be mentioned in related pages]

## Documentation Depth Issues
[Existing pages that need updates — missing methods, examples, etc.]

## Conceptual Gaps
[Missing guides, overviews, tutorials]

## Low Priority / Skip
[Internal types that don't need documentation, with brief justification]

## Suggested Actions
[Ordered TODO checklist of documentation tasks]
```

### Report Guidelines

- Use `- [ ]` checkboxes for actionable items so report doubles as TODO list.
- Include source file paths so doc writer finds code fast.
- For each suggested action, estimate scope: "new page", "new section", "brief mention", or "update existing".
- Group suggestions by module for easy assignment.

## Step 4: Update Index

Do NOT add report to `docs/index.md` or move it under `docs/`.
