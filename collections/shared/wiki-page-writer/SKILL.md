---
name: wiki-page-writer
description: "Write an evidence-backed technical deep-dive page for one component, system or feature: traced code paths, file:line citations, Mermaid diagrams, and fact marked separately from inference. Use when asked to document how a specific part of a codebase works or to fill a wiki/docs-site section; use wiki-builder for a multi-source research wiki and documentation-and-adrs for ADRs and READMEs."
risk: safe
source: community
date_added: "2026-02-27"
---

# Wiki Page Writer

## Depth Rules

1. **Trace actual code paths.** Read implementation. Do not infer behavior from file names.
2. **Cite every non-trivial claim** as `(path/to/file.ext:line)` or path plus symbol.
3. **Separate fact from inference.** State what you read. Mark inference as inference.
4. **Explain why before what.** Open with problem component solves.
5. **No hand-waving.** Replace "this likely handles..." with code reading, or mark `(Unknown - verify in path/to/check)`.

Cite as many files as component actually involves. Do not pad citations to reach a count.

## Procedure

1. **Scope:** name component, audience (new contributor, operator, API consumer), entry points. Size page to code: 3-file module gets short page.
2. **Analyze:** read relevant files, follow calls across module boundaries. Note data flow, state, error paths, configuration, dependencies.
3. **Write** in this structure; drop sections that do not apply:
   Overview (why) -> Architecture -> Components -> Data flow -> Implementation details -> Configuration -> References.
4. **Validate:** every cited path and line exists, symbol names match, every Mermaid block renders, links resolve.

## Format

- Match target docs system. For VitePress, Docusaurus or MkDocs, follow its frontmatter and conventions, for example:

  ```yaml
  ---
  title: "Page Title"
  description: "One-line description"
  ---
  ```

- Use tables for APIs, configuration options, component summaries. Add comparison tables for alternatives.
- Pseudocode in familiar language for complex paths. Short, cited real snippets for key logic.

### Mermaid diagrams

- Add diagram when it shows what prose can't: architecture or component relationships, request sequence, state machine, entity model. Usually one or two per page.
- Pick matching type: `flowchart`, `sequenceDiagram` (with `autonumber`), `classDiagram`, `stateDiagram-v2` or `erDiagram`.
- Use site's default theme. Do not hard-code colors. If styling needed, use `classDef` so light and dark themes stay readable.
- Use `<br>`, not `<br/>`, for line breaks in labels.

### Static-site compatibility (VitePress/Vue-based)

- Wrap generics and angle brackets outside code fences in backticks (`` `List<T>` ``). Else they parse as HTML.
- Hex colors must be 3 or 6 digits.

## Done When

- Page states what it covers and leaves out. Links to related pages.
