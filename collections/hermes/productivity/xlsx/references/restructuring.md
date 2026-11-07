# Reference-aware restructuring (xlsx_restructure.py)

`scripts/xlsx_restructure.py` does one row/column insert or delete and
rewrites everything referencing moved cells.

## What gets rewritten

| Artifact | Scope | Behavior |
|---|---|---|
| Formula references | ALL sheets | A1 refs into edited sheet shifted; refs into fully deleted region become `#REF!` |
| Merged-cell ranges | edited sheet | shifted; expanded when spanning insertion point; dropped (reported `to: null`) when fully deleted |
| Autofilter ref | edited sheet | shifted/expanded like range |
| Freeze panes | edited sheet | anchor cell shifted (never below row/col of pane's own minimum) |
| Data validations | edited sheet | each sqref range shifted; deleted ranges removed |
| Conditional formats | edited sheet | applied range (sqref) shifted |
| Native tables | edited sheet | table `ref` shifted/expanded |
| Defined names | workbook scope | `attr_text` refs into edited sheet rewritten |
| Row heights / column widths | edited sheet | dimension keys re-indexed |

## Reference grammar handled

- Relative and absolute coordinates, any mix: `B2`, `$B2`, `B$2`,
  `$B$2`. `$` flags survive shift.
- Ranges `B2:D9`, including partial-absolute endpoints.
- Cross-sheet refs: `Data!B2`, `'My Sheet'!$A$1:$C$9` (quoted names may
  contain doubled quotes `''`). Only refs whose sheet qualifier matches
  edited sheet are touched; unqualified refs count as formula's own
  sheet.
- String literals in formulas (`"See B2"`): never rewritten.
- Cell-like function names (`LOG10(...)`): not touched, since a
  reference is never followed by `(`.
- Whole-row/column refs (`B:B`, `2:2`) pass through unchanged; Excel
  semantics keep them valid across inserts within span.

## Shift semantics

Insert of N at index i: every coordinate >= i moves +N. Range
endpoints move independently, so range spanning i grows by N.

Delete of N at index i: coordinates before i unchanged; coordinates
past deleted block move -N; single cell inside block becomes `#REF!`;
RANGE partially covering block is clamped (as in Excel); range
entirely inside block becomes `#REF!` (formulas) or is removed
(merges/validations).

## What it CANNOT shift (honest limits)

- **Chart anchors and plotted ranges**: openpyxl does not reliably
  round-trip chart objects; anchors stay put. If their data moved,
  re-create charts after restructuring.
- **Images / drawings**: same reason.
- **Conditional-format RULE formulas**: applied range (sqref) shifts;
  formulas inside `cell_is`/`expression` rules (e.g. `$B1>100`) do
  not. Review them if they reference moved cells.
- **Sheet-local defined names**, and names using R1C1 or
  union/intersection operators: rewritten only if they parse as plain
  A1 refs; otherwise pass through untouched.
- **Structured table references** in formulas (`Table1[Sales]`)
  follow table, need no shifting; left alone.

Every run prints JSON report of exactly which formulas, merges,
tables, names, ranges changed, plus fixed `not_shifted` list of above
limits. Inspect it after any structural edit.

## One op per invocation

CLI takes exactly one of `--insert-rows/--delete-rows/
--insert-cols/--delete-cols` (as `IDX[:N]`; columns accept letters).
For several operations, run repeatedly.
