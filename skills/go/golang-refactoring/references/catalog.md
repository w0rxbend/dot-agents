# The Fowler Catalog, Mapped to Go

Entry fields: **Smell trigger** (code shape signaling it), **Go mechanics** (transform in Go), **Tool** (what performs it), **Risk** (per Risk Stratification table in [SKILL.md](../SKILL.md)).

## Table of Contents

- [Extract Function / Extract Method](#extract-function--extract-method)
- [Inline Function / Inline Call](#inline-function--inline-call)
- [Extract Variable / Inline Variable, Extract Constant](#extract-variable--inline-variable-extract-constant)
- [Rename](#rename)
- [Change Function Declaration (Signature)](#change-function-declaration-signature)
- [Move Function / Move Field / Move Type](#move-function--move-field--move-type)
- [Split Package / Merge Package](#split-package--merge-package)
- [Replace Nested Conditional with Guard Clauses](#replace-nested-conditional-with-guard-clauses)
- [Introduce Parameter Object](#introduce-parameter-object)
- [Replace Conditional with Polymorphism](#replace-conditional-with-polymorphism)
- [Hide Delegate / Remove Middle Man](#hide-delegate--remove-middle-man)
- [Sprout Method / Wrap Method](#sprout-method--wrap-method)
- [Replace Temp with Query](#replace-temp-with-query)
- [Smell → Refactoring Quick Reference](#smell--refactoring-quick-reference)
- [Cross-References](#cross-references)

## Extract Function / Extract Method

- **Smell trigger:** Long Function: mixed abstraction levels, or a comment introducing a block that could be a function name.
- **Go mechanics:** Select statements. Tool infers parameters (free variables), returns (variables used after block), and receiver for a method.
- **Tool:**

```
gopls codeaction -exec -kind=refactor.extract.function file.go:#start,#end
gopls codeaction -exec -kind=refactor.extract.method   file.go:#start,#end
```

Editor-integrated as "Extract function"/"Extract method" in code actions menu.

- **Risk:** Medium. gopls docs call Extract "considerably less rigorous" than Rename or Inline. Known to drop comments attached to extracted statements (golang/go#20744). Always diff and re-read extracted body. Not behavior-preserving by construction, unlike Rename and Inline.

## Inline Function / Inline Call

- **Smell trigger:** Trivial one-line forwarder, or Middle Man that never gained behavior of its own.
- **Go mechanics:** Call site replaced with callee's body by real substitution, not text-splicing. Side-effecting arguments hoist into `var` temporaries instead of duplicating. Implicit conversions at call boundary become explicit. Callee body with `defer` wraps in immediately-invoked function literal, so deferred call fires at right point. Cannot cross dynamic dispatch (interface method call, function value) or inline a generic function.
- **Tool:**

```
gopls codeaction -exec -kind=refactor.inline.call file.go:#offset
```

- **Risk:** Low. With Rename, one of two gopls operations provably behavior-preserving by construction. Refuses rather than inline wrongly.

## Extract Variable / Inline Variable, Extract Constant

- **Smell trigger:** Same non-trivial expression repeats, or one occurrence makes reader pause to work out what it computes.
- **Go mechanics:** Extract Variable adds `:=` binding right above first use. `-all` variant rewrites every syntactic occurrence in scope. Extract Constant does same for a literal deserving a name and compile-time immutability. Inline Variable reverses: substitutes value at use site(s), removes binding.
- **Tool:**

```
gopls codeaction -exec -kind=refactor.extract.variable     file.go:#start,#end
gopls codeaction -exec -kind=refactor.extract.variable-all file.go:#start,#end
gopls codeaction -exec -kind=refactor.extract.constant     file.go:#start,#end
gopls codeaction -exec -kind=refactor.inline.variable      file.go:#offset
```

- **Risk:** Low.

## Rename

- **Smell trigger:** Any identifier (variable, function, type, field, package) whose name no longer describes what it holds or does.
- **Go mechanics:**
  - gopls Rename is workspace-wide: updates every reference in every file and importing package, then type-checks.
  - Refuses on shadowing conflict, on a method rename that would break interface satisfaction elsewhere in workspace, or when surrounding code doesn't currently type-check.
  - Two special cases are easy to get backwards. Renaming `p` in `package p` moves package directory and rewrites every import path to it. Renaming a method's _receiver declaration_ (the `s` in `func (s *Store) Get(...)`) propagates to every method of that type; renaming one _use_ of a receiver variable inside one method body touches only that method.
- **Tool:**

```
gopls rename file.go:#offset newName
```

Editor-integrated as "Rename Symbol" (F2 in most gopls-backed editors).

- **Risk:** Low. Treat any refusal as real semantic hazard to investigate, not friction to bypass by hand-editing.

→ See `samber/cc-skills-golang@golang-naming` skill for what to rename identifiers _to_. This entry covers only _how_ to rename safely at scale.

## Change Function Declaration (Signature)

- **Smell trigger:** Long Parameter List, or parameter no longer relevant to function's job.
- **Go mechanics:**
  - Partial gopls support: removing a parameter nobody passes meaningfully, or reordering two adjacent parameters, is mechanical.
  - Adding a parameter at every call site, or broader signature rewrite, is no single gopls action today. Stage it with `eg`: write new variant with added or generalized parameter, migrate call sites via `eg` template (`eg -t template.go -w ./...`), verify, then Rename old function aside (or delete it) once nothing calls it.
- **Tool:**

```
gopls codeaction -exec -kind=refactor.rewrite.removeUnusedParam file.go:#offset
gopls codeaction -exec -kind=refactor.rewrite.moveParamLeft      file.go:#offset
gopls codeaction -exec -kind=refactor.rewrite.moveParamRight     file.go:#offset
eg -t template.go -w ./...   # staged migration for adding/generalizing a parameter
```

- **Risk:** Medium for single-parameter add/remove with a handful of call sites. High for signature changes across many callers with no one-shot mechanical action.

→ See `samber/cc-skills-golang@golang-design-patterns` skill for turning long parameter list into options struct, not only reordering or trimming it.

## Move Function / Move Field / Move Type

- **Smell trigger:** Feature Envy (function uses another package's data more than its own), or type whose responsibilities clearly belong elsewhere.
- **Go mechanics:**
  - No one-shot gopls action moves a symbol across packages yet.
  - Gradual repair: add symbol in new home. In old location leave a **type alias** (`type Old = pkg.New`) for a moved type, or thin wrapper function/forwarding variable for a moved function, so both names work. Migrate callers incrementally, one small commit at a time. Delete old name (and alias/wrapper) only once nothing references it.
  - Splitting a large file into a new file _within the same package_ is a separate one-shot gopls action.
- **Tool:**

```
gopls codeaction -exec -kind=refactor.extract.toNewFile file.go:#start,#end   # same-package file split
```

- **Risk:** High.

→ See `samber/cc-skills-golang@golang-project-layout` skill for target package layout. See [structural.md](structural.md) for full type-alias gradual-repair recipe.

## Split Package / Merge Package

- **Smell trigger:** "God package" (package-level Large Class), or Divergent Change: package keeps changing for unrelated reasons because it hosts unrelated concerns. Merge occasionally fits when two packages are so interdependent their boundary adds ceremony, not isolation.
- **Go mechanics:**
  - Experimental gopls code action partitions top-level declarations into acyclic components, proposing a split. Starting point to review, not final answer: package boundaries also encode API and ownership decisions tool can't see.
  - Merging has no dedicated tool. Move declarations into target package. Resolve resulting import cycle with consumer-side interface (see [structural.md](structural.md)) before falling back to bigger restructuring.
- **Tool:**

```
gopls codeaction -exec -kind=source.splitPackage file.go   # experimental; splitting only
```

- **Risk:** High.

→ See `samber/cc-skills-golang@golang-project-layout` skill for target package layout.

## Replace Nested Conditional with Guard Clauses

- **Smell trigger:** `if`/`else if`/`else` chain or nested `if` blocks where most branches are preconditions or error cases, not equal-weight alternatives.
- **Go mechanics:** Each non-primary branch becomes early `return`/`continue`/`break`, flattening logic to one nesting level. gopls invert-if flips one `if`/`else` in place, one condition at a time. Whole nested chain needs a structural pass using that action, not one tool invocation.
- **Tool:**

```
gopls codeaction -exec -kind=refactor.rewrite.invertIf file.go:#offset
```

- **Risk:** Low.

→ See `samber/cc-skills-golang@golang-code-style` skill for full early-return style rule this refactor targets.

## Introduce Parameter Object

- **Smell trigger:** Data Clumps (same parameters or fields recurring together), or Long Parameter List where several parameters form one unit.
- **Go mechanics:** Define struct holding the group; change each affected signature to take it instead of individual values. Manual Extract-Variable-style step (define struct, construct it at each call site), then signature change at each call site, staged like Change Function Declaration.
- **Tool:** No dedicated gopls action yet: "Extract parameter struct" is planned (golang/go#65552).
- **Risk:** Medium.

→ See `samber/cc-skills-golang@golang-design-patterns` skill for functional options as alternative when struct configures construction, not groups a plain data clump.

## Replace Conditional with Polymorphism

- **Smell trigger:** Repeated Switches: same `switch` on type tag or state value at multiple call sites; new case means updating each.
- **Go mechanics:** Define interface with one method per case-varying behavior; give each case its own implementing type. Callers call interface method. Go interface dispatch replaces repeated `switch`.
- **Tool:** Manual; no mechanical tool does this. Carve each case's behavior into its own type with Extract Function/Interface steps, then clean seams with Rename/Inline.
- **Risk:** Medium.

→ See `samber/cc-skills-golang@golang-design-patterns` skill for target interface-dispatch pattern.

## Hide Delegate / Remove Middle Man

- **Smell trigger:** Message Chains (`a.B().C().D()` reaching through several objects to the one that matters) call for Hide Delegate. Middle Man (method whose whole body is `return x.SameMethod(...)`) calls for Remove Middle Man.
- **Go mechanics:** Go usually hides delegate via struct embedding: delegate's methods promote onto outer struct, callable directly, no accessor chain. Remove Middle Man is inverse: delete pass-through method (after Inline Call at each call site, or Rename-and-redirect). Callers then reach real implementation via exported field or embedded type.
- **Tool:** Manual for embedding decision. `gopls codeaction -exec -kind=refactor.inline.call` mechanizes the "delete the middle man" step once callers are ready.
- **Risk:** Low-Medium.

## Sprout Method / Wrap Method

- **Smell trigger:** Adding behavior to function or method with little or no test coverage.
- **Go mechanics:**
  - **Sprout Method** — write new behavior as brand-new, fully-tested function or method; call it from the one call site needing it. Original code otherwise untouched.
  - **Wrap Method** — rename original method (e.g. `Save` → `saveInternal`); add new method with old name (`Save`) calling renamed original and adding new behavior around it. Manual decorator: Go has no built-in method wrapping.
- **Tool:** `gopls rename` for Wrap Method's rename step. New code is hand-written and tested like any new function.
- **Risk:** Low, by design: Feathers's approach avoids touching untested code directly.

→ See [safety-net.md](safety-net.md) for when low/zero coverage should push you to this pattern instead of editing in place.

## Replace Temp with Query

- **Smell trigger:** Local variable assigned once from an expression, read several times later, name not showing it's derived rather than an input.
- **Go mechanics:** Replace variable with call to small unexported function or method recomputing the expression; each read becomes a call. Manual. Go calls are cheap, so performance rarely matters; only judgment call is readability.
- **Tool:** Manual. If resulting function is called only once, gopls inline action can fold it back anytime without losing readability gain that motivated extracting it.
- **Risk:** Low.

## Smell → Refactoring Quick Reference

| Smell | Go-specific fix |
| --- | --- |
| Long Function | Extract Function/Method |
| Large/God Package | Split Package |
| Long Parameter List | Introduce Parameter Object, or options struct |
| Data Clumps | Extract struct for recurring group |
| Primitive Obsession | Introduce named type instead of bare `string`/`int` |
| Divergent Change (one package, many unrelated reasons to change) | Split Package |
| Shotgun Surgery (one conceptual change touches many packages) | Move Function/Field to consolidate concept into one package |
| Feature Envy | Move Function to package whose data it actually uses |
| Repeated Switches | Replace Conditional with Polymorphism |
| Message Chains | Hide Delegate |
| Middle Man | Remove Middle Man |

Divergent Change and Shotgun Surgery need opposite fixes, though both are "too much change ripples around".

## Cross-References

- → See [go-tooling.md](go-tooling.md) for full gopls code-action reference, `gofmt -r`, `eg`, and `gopatch` invocation details.
- → See `samber/cc-skills-golang@golang-design-patterns` skill for consumer-side interfaces.
