# Go Tooling for Refactoring

## Table of Contents

- [1. gopls — the Primary Actuator](#1-gopls--the-primary-actuator)
- [2. Bulk Mechanical Rewrite Tools](#2-bulk-mechanical-rewrite-tools)
  - [`gofmt -r` — syntactic, single-expression](#gofmt--r--syntactic-single-expression)
  - [`eg` — type-aware, example-based](#eg--type-aware-example-based)
  - [`gopatch` — statement-level, import-aware](#gopatch--statement-level-import-aware)
  - [`go/analysis` + SuggestedFixes — bespoke, testable](#goanalysis--suggestedfixes--bespoke-testable)
  - [`go fix` — the `go/analysis`-based fixer suite](#go-fix--the-goanalysis-based-fixer-suite)
  - [`dave/dst` — comment- and formatting-preserving AST edits](#davedst--comment--and-formatting-preserving-ast-edits)
  - [Always run after a bulk rewrite](#always-run-after-a-bulk-rewrite)
- [4. Structure-Discovery Tools (blast-radius mapping)](#4-structure-discovery-tools-blast-radius-mapping)
- [Cross-References](#cross-references)

## 1. gopls — the Primary Actuator

- gopls performs most Low- and Medium-risk transforms in this skill: Rename, Inline, Extract, `refactor.rewrite.*` family.
- Action per refactoring: Risk Stratification table in [SKILL.md](../SKILL.md), and `Tool:` line per entry in [catalog.md](catalog.md).
- Full code-action reference, CLI invocation, safety behavior, MCP server setup: `samber/cc-skills-golang@golang-gopls`. This file covers tools that skill doesn't.

## 2. Bulk Mechanical Rewrite Tools

Change recurring across many call sites: use generated rewrite tool, not hand edits. Ordered by increasing power. Start at top; move down only when current tool's limits block the rewrite.

### `gofmt -r` — syntactic, single-expression

- Purely syntactic: matches expression shape, not types. One rewrite covers a single expression only.
- Wildcards: single lowercase identifiers matching any sub-expression.

```bash
gofmt -r 'bytes.Compare(a, b) == 0 -> bytes.Equal(a, b)' -w file.go
gofmt -r 'bytes.Compare(a, b) != 0 -> !bytes.Equal(a, b)' -w file.go
gofmt -s -w file.go    # -s additionally simplifies (e.g. s[a:len(s)] -> s[a:])
gofmt -l .             # list non-conforming files — useful as a CI gate
gofmt -d file.go       # show the diff without writing
```

- Type-blind, so cannot target "every `bytes.Compare` call on a `[]byte`, but not a look-alike function of the same name from another package". That needs `eg`.

### `eg` — type-aware, example-based

`golang.org/x/tools/cmd/eg` rewrites by example, à la Refaster. Template declares `before`/`after` functions of identical type, each with single-expression body.

```go
// template.go
package template

import (
	"errors"
	"fmt"
)

func before(s string) error { return fmt.Errorf("%s", s) }
func after(s string) error  { return errors.New(s) }
```

```bash
eg -t template.go -w ./...
```

- Semantic match by type and structure, not text: `func(x int)` in template also matches `func(y int)` at call site.
- Limits: expressions only, no statements or function-literal patterns. Can't change expression's type. Adds imports, never removes them (run `goimports` afterward). Wildcard repeated in `after` template duplicates matched expression's side effects.

### `gopatch` — statement-level, import-aware

`github.com/uber-go/gopatch` works on statements and tracks imports in the patch, so it runs on code that doesn't fully compile mid-refactor: the messy middle of a large migration. Patch: metavariables between `@@` markers, then diff-like body:

```
@@
var x expression
@@
-errors.New(fmt.Sprintf(x))
+fmt.Errorf(x)
```

```bash
gopatch -p rewrite.patch ./...
gopatch -d -p rewrite.patch ./...    # dry-run — show the diff only
```

- Still beta; project frames it as covering roughly 80% of a migration, not 100%.
- Pattern can't match an import statement in isolation; something must follow it for a match.

### `go/analysis` + SuggestedFixes — bespoke, testable

- Rewrite too specific for those three: write `analysis.Analyzer`. Its `Run(pass)` walks type-checked AST, reports `analysis.Diagnostic{SuggestedFixes: [...]}` per match.
- Test against `.golden` files with `analysistest.RunWithSuggestedFixes`. Ship as `singlechecker`/`multichecker -fix` binary, or run via `go vet -vettool=<path>`.

### `go fix` — the `go/analysis`-based fixer suite

- As of Go 1.26, `go fix` runs on `go/analysis` framework, converged with `go vet`. Hosts `modernize` fixer suite (`rangeint`, `mapsloop`, `minmax`, `any`, `stringscut`, `omitzero`, more). Coverage shifts per release: Go 1.27 added `atomictypes`, `embedlit`, `slicesbackward`, `unsafefuncs`, removed `fmtappendf`, renamed `waitgroup` to `waitgroupgo`. → See `samber/cc-skills-golang@golang-modernize` skill for idiom-by-idiom breakdown.
- Older toolchain without this convergence: run equivalent analyzers via `singlechecker`/`multichecker -fix` instead of `go fix`.
- `//go:fix inline` directive marks function or constant so `go fix` inlines every call site into its replacement. Machine-executable finish of a deprecation migration once replacement exists:

```bash
go fix ./...
go run golang.org/x/tools/go/analysis/passes/inline/cmd/inline@v0.52.0 -fix ./...   # pin reviewed x/tools version, never @latest
```

### `dave/dst` — comment- and formatting-preserving AST edits

- `go/ast` keeps comments in side table keyed by byte offset; reordering, moving or deleting nodes desyncs them from their code. Root cause of Extract/Inline comment-loss caveat above.
- `github.com/dave/dst` (Decorated Syntax Tree) stores comments and blank-line spacing as node-local decorations, so hand-rolled AST rewrites round-trip them via `decorator.Parse` / `decorator.Print`.
- `dstutil.Apply` mirrors `astutil.Apply`'s visitor API, so existing `go/ast` rewrite logic ports directly.
- Use only when bespoke `go/analysis` fixer must keep comments that `go/ast`-based rewriting would scatter.

### Always run after a bulk rewrite

```bash
goimports -w .    # organizes imports added/left dangling by gofmt -r, eg, or a hand-rolled fixer
```

```bash
deadcode ./...                     # find code orphaned by a removal-heavy refactor
deadcode -test ./...                # include test binaries — unreached public API here signals a coverage gap, not dead code
deadcode -whylive=funcName ./...    # shortest reachability path proving a function is still live
```

- `golang.org/x/tools/cmd/deadcode` builds reachability graph with Rapid Type Analysis from `main`/`init`. Unsound for assembly, `go:linkname` and reflection-driven dispatch; on such code, "dead" verdict is strong hint, not proof.
- **Never `sed`/`perl` a structural Go change by hand.** No grammar awareness: matches inside string literals or comments get rewritten with real code.
- Always finish bulk rewrite with `goimports`, even after tools claiming to manage imports.

## 4. Structure-Discovery Tools (blast-radius mapping)

These feed planning gate in [workflow.md](workflow.md): map blast radius before picking a tool above.

| Tool | What it answers |
| --- | --- |
| `golang.org/x/tools/go/callgraph` (`rta`/`cha`/`static`/`vta` algorithms) | Who can reach this function statically, across whole build. Algorithms trade precision for speed differently |
| gopls call hierarchy (`textDocument/prepareCallHierarchy`) | Incoming/outgoing calls for one symbol, interactively |
| `go_references` / `go_symbol_references` (gopls MCP) | Every reference to a symbol from agent context, no full callgraph build |
| `go mod graph` | Module-level dependency edges (which modules require which), for blast radius crossing module boundaries |

## Cross-References

- [catalog.md](catalog.md) — Fowler catalog mapped to Go, with the tool from this file mechanizing each entry.
- [workflow.md](workflow.md) — planning gate these structure-discovery tools feed; where tool-driven steps fit staged-PR process.
