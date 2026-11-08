---
name: docs-markdown-table
description: How to produce a Markdown table that is aligned and structurally valid — generate it from a Python script with a cell-count and escaping check, never by hand. Use when a page compares things across three or more columns, such as a type roster, an edge-case table, or a variant comparison.
allowed-tools: Read, Write
---

# Markdown Tables

Method behind writing-style rule 22 ("align table columns with spaces for readability"): how to
line columns up without eyeballing.

## Method — do not hand-align

1. Write Python script holding data as header list plus row lists — never pre-formatted strings.
2. Column width is its widest cell. Pad every cell to it.
3. Assert before emitting: each row has exactly `len(header)` cells, no raw newlines, every in-cell
   `|` escaped. Print `TABLE CHECK: ok`, or failures.
4. Assert emitted lines share one `len()` and one `|` count. Print `LINE CHECK: aligned`, or
   differing widths.
5. Run it. Fix **script** and rerun — never patch rendered table.
6. Paste only verified output.

Second check must count with `len()`. Custom width function treating some characters as two columns
agrees with padding it produced: check and bug share an assumption, so ragged source passes. `len()`
cannot fail that way: diffs, editors and byte counts all use it.

## Syntax rules

- Header row, then separator of plain `---` per column. Renderers left-align anyway; marker on
  every column is noise: ✅ `|------|------|` ❌ `|:-----|:-----|`
- Use marker only for non-default alignment: `---:` right-aligns numbers, `:---:` centres short
  flags. Mixed markers in one row are fine; they signal deliberate choice.
- Separator has no padding spaces of its own: dashes fill whole cell, including the space either side
  that data rows pad with. Column of width `w` gets `w + 2` characters between pipes: ✅ `|----------|` ❌ `| -------- |`
- Escape in-cell `|` as `\|`, **including inside backticks**, where it still breaks table.
- Cells single-line; `<br/>` forces break. Cell needing list or code block means table is wrong
  container — use definition list or headings.
- Docusaurus renders MDX: escape `{` and `<` in cells or wrap them in backticks, else parser reads
  JSX and build fails.
- Prefer single-width characters. Emoji and CJK are ambiguous-width: padded to you, ragged to others.
  If a cell must contain them, pad by display width, not `len()`.

## Content rules

- First column: key readers scan, what they already know. Sort by it, or by prose order.
- Every column must vary: ✅ values differ per row ❌ one repeated value (belongs in sentence above
  table)
- Three or more columns, or cross-row comparison. Two prose columns is a list:
  ✅ `| Method | Returns | Cost |` ❌ `| Method | What it does |` (write bullets)
- Header labels: short nouns, no wider than column data.
- No trailing "Notes" catch-all column. What does not fit a column is prose.
- Introduce table with sentence naming what to compare. Do not restate rows below.

## Output

Keep script off page. Report its `TABLE CHECK` line in your result so next reader knows table was
verified, not eyeballed.

## Worked shape

```python
header = ["Method", "Returns", "Cost"]
rows = [
    ["`record(name, by)`", "`Ledger`", "O(1)"],
    ["`tallyOf(name)`", "`Long`", "O(1)"],
    ["`absorb(that)`", "`Ledger`", "O(n)"],
]
align = [None, None, "right"]  # None is plain `---`; name one only where it is needed

bad = [(i, len(r)) for i, r in enumerate(rows) if len(r) != len(header)]
bad += [(i, "newline") for i, r in enumerate(rows) for c in r if "\n" in c]
bad += [(i, "unescaped |") for i, r in enumerate(rows) for c in r if "|" in c.replace(r"\|", "")]
print("TABLE CHECK: ok" if not bad else f"TABLE CHECK FAILED: {bad}")

width = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(header)]

def rule(w, a):  # w + 2, because the separator also covers the spaces a data row pads with
    if a == "right":  return "-" * (w + 1) + ":"
    if a == "center": return ":" + "-" * w + ":"
    return "-" * (w + 2)

sep = [rule(w, a) for w, a in zip(width, align)]
line = lambda cells: "| " + " | ".join(
    c.rjust(w) if a == "right" else c.center(w) if a == "center" else c.ljust(w)
    for c, w, a in zip(cells, width, align)
) + " |"

out = [line(header), "|" + "|".join(sep) + "|", *(line(r) for r in rows)]
lens, pipes = {len(l) for l in out}, {l.count("|") for l in out}
print("LINE CHECK: aligned" if len(lens) == len(pipes) == 1
      else f"LINE CHECK FAILED: widths={sorted(lens)} pipes={sorted(pipes)}")
print("\n".join(out))
```

`|`-escaping check strips `\|` first on purpose: escaped pipe passes, bare one fails. Bare pipe
renders as stray extra column.
