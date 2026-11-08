# Section-Type-Specific Patterns

Templates for each canonical section type used by `docs-add-missing-section`. Load in **Step 4**, once section type is identified.

---

## Construction Section Pattern

One `###` subsection per major factory method or constructor group.

**For each subsection:**

1. Subsection heading is method name (e.g., `### apply`, `### empty`, `### from[B]`).
2. One sentence on what method does and its typical use case.
3. Signature block in plain ```` ```scala ```` (not mdoc):
   ```scala
   object TypeName {
     def method(...): TypeName[...]
   }
   ```
4. Prose sentence ending in `:` introducing example.
5. Self-contained code block using `mdoc:compile-only`:
   ```scala mdoc:compile-only
   // Complete example, no output needed
   ```

---

## Predefined Instances Section Pattern

Use Markdown table with columns: **Instance Name**, **Type**, **Description**.

Group instances by category (e.g., "Common Types", "Numeric Types", "Collections") if more than 5 instances exist.

After table, add one example using a few predefined instances:

```scala mdoc:compile-only
// Show using 2–3 predefined instances together
```

---

## Comparison Section Pattern

1. Create dimensions table:
   - Column 1: Type / Alternative name.
   - Columns 2–N: Dimensions (Mutability, Performance, API Breadth, Laziness, …).
   - Use `✓` / `✗` for binary dimensions, short text for continuous dimensions.

2. Follow table with **mandatory** "Use X when… Use Y instead when…" paragraphs:

   > **Use `TypeA` when:**
   > - You need immutability
   > - Performance is critical
   >
   > **Use `TypeB` instead when:**
   > - You need lazy evaluation
   > - API breadth is more important than performance

3. Include code example **only** if API differences require demonstrating calling conventions. Otherwise skip example (comparison is conceptual, not operational).

---

## Advanced Usage Section Pattern

Create 2–4 `###` subsections, each with:

1. Subsection heading: realistic scenario name (e.g., `### Composing with Results`, `### Custom Derivations`).
2. Brief scenario explanation.
3. Prose sentence ending in `:` introducing example.
4. Code block using `mdoc:compile-only`:
   ```scala mdoc:compile-only
   // Realistic scenario code
   ```

---

## Motivation Section Pattern

1. **Problem paragraph**: describe limitation or gap that motivated type's creation.
2. **Naive approach paragraph**: show what reader might try without this type, and why it fails.
3. **Working example**: show how type solves problem:
   ```scala mdoc:compile-only
   // Solution using the type
   ```

---

## Cross-Pattern Rules

- Every code block must respect `docs-mdoc-conventions`. Pick right modifier (`mdoc`, `mdoc:silent`, `mdoc:compile-only`, `mdoc:reset`) based on whether block needs scope sharing or output rendering.
- Prose immediately preceding code block must end with `:` (`docs-writing-style` Rule 15).
- Type definitions use plain ```` ```scala ```` without mdoc modifiers. They are structural illustrations, not executable examples.
