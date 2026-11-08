---
name: docs-writing-style
description: Prose style rules for ZIO-ecosystem library documentation (Docusaurus + mdoc reference pages, how-to guides, tutorials). Use when writing or editing docs in a ZIO or ZIO-style Scala library repo; not for READMEs or docs in unrelated projects.
allowed-tools: Read, Glob, Grep
---

# ZIO Documentation Writing Style

## Agent Workflow

**Phase 1 — Planning only, no edits yet**
Find every prose style violation (Rules 1–25 below). Create one task per violation:

> "Fix style – `<section>`:`<line>` (Rule `<N>`): `<short description>`"

Do not touch any source file until full task list exists and is listed for confirmation.

**Phase 2 — Execution**
Apply all fixes. Mark each task `completed` when done.

**Phase 3 — Mechanical validation**
After all tasks are `completed`, run:
Paths: `<this-skill-dir>` is this skill's own directory (where this file lives).

```
bash <this-skill-dir>/check-docs-style.sh <file.md>
```
Verify exit code is 0. If not, re-open relevant tasks and fix.

## Mechanical Validation

Run the same `check-docs-style.sh` command before validating manually too. It checks Rules 2, 3, 4, 7, 8, 10, 11, 12, 13, 15, 16, 18, 21, 22, 23, and 25 for mechanical violations. Run with `--help` for full rule list and usage examples.

**Exit codes:**

| Code | Meaning                                                          |
|------|------------------------------------------------------------------|
| `0`  | No violations; all checked rules pass.                           |
| `1`  | Violations found; details printed to stdout.                     |
| `2`  | Invocation error (missing/extra arguments, file not found).      |

**Rule 8** detects unqualified methods by heuristics (camelCase in backticks, confident if qualified elsewhere). Update `SAFE_NAMES` in `check-docs-style.sh` to avoid false positives.

## Prose Style Rules

1. **Person pronouns**: Use "we" when guiding reader or walking through examples ("we can create...", "we need to..."). Use "you" for reader's choices ("if you need...", "you might want to...").
2. **Tense**: Present tense only ("returns", "creates", "modifies"). Exception: promises about reader's future are fine ("By the end of this tutorial, you will...").
3. **No padding/filler**: No filler phrases like "as we can see" or "it's worth noting that". State the fact. Exception: tutorial warmth ("Welcome!", "Let's", "That's it!", "notice that") is required tone, not filler.
4. **Bullet capitalization**: Start full-sentence bullet with capital letter.
5. **No manual line breaks in prose**: Do not hard-wrap paragraphs at fixed column. Write each paragraph as one continuous line.
6. **ASCII art usage**: Use for diagrams of data flow, type relationships, or architecture.
7. **Link to related docs**: Link sibling type's first mention in prose, not only in trailing "See also" list. Use relative paths with full filename including `.md` extension, never bare directory name: ✅ `[Endpoint](./reference/endpoint/index.md)`, ❌ `[Endpoint](./reference/endpoint)`. Markdown links only, never templating syntax: ❌ `{{< reference_path "Endpoint" >}}`.

   **Link only a page that exists** — verify it before writing link. If it does not exist, write sentence without link. Link to missing page fails site build (`onBrokenLinks: 'throw'`). Fix: drop link, never create target page just to make it resolve.

## Referencing Types, Operations, and Constructors

8. **Always qualify method/constructor names**:

   **Bad vs. Good:**
   - ❌ "Call `map` to transform elements" → ✅ "Call `Chunk#map` to transform elements"
   - ❌ "Use `apply` to construct a binding" → ✅ "Use `BindingResolver.apply` to construct a binding"
   - ❌ "Use `.query` to add a parameter" → ✅ "Use `Endpoint#query` to add a parameter"

   Dot-prefixed references (`` `.method` `` or `` `.method(args)` ``) are always a violation — they imply receiver without naming it.

9. **Type name alone rule**: For type (not method), use only its name in backticks, no qualifier: "`As` derives automatically", "`List` is a sequence type", "convert to `Option`".

## Frontmatter Titles

10. **No duplicate markdown heading**: Do not create markdown heading (`#`) duplicating frontmatter title. Frontmatter title suffices:

   **Bad vs. Good:**
   - ❌ Frontmatter has `title: "As Type"`, then document starts with `# As Type`
   - ✅ Start directly with `## Overview` or `## Use Cases`

## Heading and Code Block Layout Rules

11. **Heading hierarchy**: `##` for major sections, `###` for subsections, `####` for subsubsections. All three levels fully supported and encouraged.
12. **No bare subheaders**: Always write intro sentence between `##` header and its first `###` subheader. Say why section exists and what problem it solves, in one sentence or short paragraph.

   **Bad vs. Good:**
   - ❌ `## Operations` → `### Map` (no intro between them)  
     ✅ `## Operations` → `To transform values, use these operations.` → `### Map`
13. **No lone subheaders**: Never create subsection with only one child — except Core Operations category may keep one method when no related category fits.

   **Bad vs. Good:**
   - ❌ `## Overview` → `### Definition` (only one subsection)  
     ✅ `## Overview` (put the definition content directly here)
14. **When to use `####`**: Use `####` to organize multiple related topics under single `###`. Example:
    ```
    ### Operations
    #### Transformations
    #### Filtering
    #### Zipping
    #### Scanning
    ```
15. **Every code block must be preceded by a prose sentence ending with `:`**: Never put code block directly after heading.

    **Bad vs. Good:**
    - ❌ `#### Chunk#map` → (code block immediately)  
      ✅ `#### Chunk#map` → `To transform each element:` → (code block)
Between consecutive code blocks, add bridging prose explaining what next block shows:
    - ❌ (code block) (code block) (no prose between)  
      ✅ (code block) `Next, create the result:` (code block)

## Code Block Rules

16. **Always include imports**: Every code block must start with needed import statements. Exception for mdoc pages: mdoc blocks share one scope, so imports in page's first block satisfy this rule for every later block reusing that scope.
17. **One concept per code block**: Each code block shows one cohesive idea.
18. **Prefer `val` over `var`**: Use immutable patterns everywhere possible.
19. **Show method signatures within their containing type**: Document methods inside their containing trait/class, not as bare signatures.

   **Bad vs. Good:**
   - ❌ `def map[B](f: A => B): ZIO[R, E, B] = ???`
   - ✅ `trait ZIO[-R, +E, +A] { def map[B](f: A => B): ZIO[R, E, B] = ??? }`

   Drop trailing `(implicit trace: Trace)` from these illustrative signatures — plumbing, not part of what method teaches:
   - ❌ `def recurs(n: Long)(implicit trace: Trace): Schedule.WithState[Long, Any, Any, Long]`
   - ✅ `def recurs(n: Long): Schedule.WithState[Long, Any, Any, Long]`

   Drop empty parens too if that was only parameter list (`def once: X`, not `def once(): X`). Applies only to illustrative signature-listing blocks — real `mdoc:compile-only` example still needs implicit in scope to compile.

20. **Write contextualized descriptions for code blocks**: Intro sentence before every code block (ending with `:`) must explain what code does and why it is relevant, related to what it demonstrates in context. Avoid generic phrases like "here's an example" or "we can see this in action".

   **Bad vs. Good:**
   - ❌ "Here's an example:"  
     ✅ "To extract the first three elements from the end of the chunk:"
   - ❌ "We can see this in action:"  
     ✅ "When filtering an empty chunk, the result contains no elements:"

21. **Bullet list formatting**: Use bullets only for independent, enumerable items — never to explain single definition, never for only one or two items; write prose instead. When items form connected narrative (building on each other, explaining cause-and-effect, or describing single concept), write prose. Never put blank lines between bullet items.

   **Bad vs. Good (connected narrative):**
   - ❌ "The code above:\n  - We open three streams\n  - Each has its own queues\n  - There is no crosstalk"
   - ✅ "The code above opens three streams, each with its own queues. There is no crosstalk."

   **Bad vs. Good (blank lines between bullets):**
   - ❌ "- item one\n\n- item two\n\n- item three"
   - ✅ "- item one\n- item two\n- item three"

## Table Formatting

22. **Pad column alignment**: Align table columns with spaces for readability.

   **Bad (minimal spacing):**
   ```
   | Name | Value |
   | - | - |
   ```

   **Good (padded for alignment):**
   ```
   | Name  | Value     |
   | ----- | --------- |
   ```

## Scala Version

23. **Default to Scala 2.13.x syntax**: Use Scala 2.13 syntax only. Always use `import x._` for wildcard imports, never `import x.*`.
24. **Use tabs for version-specific syntax**: Use tabbed code blocks to show syntax differences between Scala 2 and 3 (e.g., `using` vs `implicit`, wildcard imports). Scala 2 is always default tab.

## Dependency Declarations

25. **Use @VERSION@ placeholder for versions**:

   **Bad vs. Good:**
   - ❌ `libraryDependencies += "dev.zio" %% "zio-blocks" % "1.0.0"`
   - ❌ `libraryDependencies += "dev.zio" %% "zio-blocks" % "<version>"`
   - ✅ `libraryDependencies += "dev.zio" %% "zio-blocks" % "@VERSION@"`

## Audience and Vocabulary

26. **Frame by audience tier**: Lead with end-user / high-level path. When section documents low-level building block (one that higher-level API wraps), open it with signal: "You rarely call this directly; it is an advanced API for `<case>` — prefer `<high-level API>`." Document it fully; change framing, not coverage.
27. **Never surface internal planning vocabulary in the doc**: names, categories, or shape labels a writer uses to organize the *work* of documenting are not reader-facing terms.

    **Bad vs. Good:**
    - ❌ "the Tracing sub-domain" (an internal planning category leaking into prose)
    - ✅ "the Tracing area of the telemetry module" or just "Tracing"
28. **Title Case every heading**: ✅ `## Open a Span and Record Work` ❌ `## Open a span and record work`.
