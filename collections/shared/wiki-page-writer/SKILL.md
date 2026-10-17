---
name: wiki-page-writer
description: "Write an evidence-backed technical deep-dive page for one component, system or feature: traced code paths, file:line citations, Mermaid diagrams, and fact marked separately from inference. Use when asked to document how a specific part of a codebase works or to fill a wiki/docs-site section; use wiki-builder for a multi-source research wiki and documentation-and-adrs for ADRs and READMEs."
risk: safe
source: community
date_added: "2026-02-27"
---

# Wiki Page Writer

Generate a technical documentation page whose every claim can be checked against the code.

## When to Use

- The user asks to document a specific component, subsystem or feature.
- The user wants a technical deep dive with diagrams.
- A wiki or docs-site section needs its content written.

## Depth Rules

1. **Trace actual code paths.** Read the implementation; do not infer behavior from file names.
2. **Cite every non-trivial claim** as `(path/to/file.ext:line)` or by path plus symbol.
3. **Separate fact from inference.** If you read it, state it. If you are inferring, say so.
4. **Explain why before what.** Start with the problem the component solves.
5. **No hand-waving.** Replace "this likely handles..." with a reading of the code, or mark it `(Unknown - verify in path/to/check)`.

Cite as many files as the component actually involves. Do not pad citations to reach a count.

## Procedure

1. **Scope:** name the component, the audience (new contributor, operator, API consumer) and the entry points. Size the page to the code: a 3-file module gets a short page.
2. **Analyze:** read the relevant files, follow calls across module boundaries, and note data flow, state, error paths, configuration and dependencies.
3. **Write** using this structure, dropping sections that do not apply:
   Overview (why) -> Architecture -> Components -> Data flow -> Implementation details -> Configuration -> References.
4. **Validate:** every cited path and line exists, symbol names match, every Mermaid block renders, and links resolve.

## Format

- Match the target docs system. If the site uses VitePress, Docusaurus or MkDocs, follow its frontmatter and conventions, for example:

  ```yaml
  ---
  title: "Page Title"
  description: "One-line description"
  ---
  ```

- Use tables for APIs, configuration options and component summaries. Add comparison tables when introducing alternatives.
- Use pseudocode in a familiar language for complex paths, and real snippets (short, cited) for key logic.

### Mermaid diagrams

- Include a diagram when it shows something prose can't: architecture or component relationships, a request sequence, a state machine, an entity model. Usually one or two per page.
- Pick the type to match: `flowchart`, `sequenceDiagram` (with `autonumber`), `classDiagram`, `stateDiagram-v2` or `erDiagram`.
- Use the site's default theme. Do not hard-code colors. If styling is needed, use `classDef` so both light and dark themes stay readable.
- Use `<br>`, not `<br/>`, for line breaks inside labels.

### Static-site compatibility (VitePress/Vue-based)

- Wrap generics and angle brackets outside code fences in backticks (`` `List<T>` ``), or they are parsed as HTML.
- Hex colors must be 3 or 6 digits.

## Done When

- Every section is backed by citations, and unknowns are marked rather than guessed.
- Cited paths and lines were spot-checked, and the diagrams render.
- The page states what it covers and what it leaves out, and links to related pages.
