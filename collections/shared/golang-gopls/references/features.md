# gopls feature catalog

Source: [tip.golang.org/gopls/features](https://tip.golang.org/gopls/features/).

## Table of contents

- [Navigation](#navigation)
- [Passive (always-on)](#passive-always-on)
- [Diagnostics](#diagnostics)
- [Transformation](#transformation)
- [Web-based features](#web-based-features)
- [Non-Go files](#non-go-files)
- [Completion](#completion)

## Navigation

**Definition** (`textDocument/definition`, CLI `gopls definition`) — jumps to symbol's declaration. Beyond plain identifiers: import path lists imported package's declarations; `go:linkname` directive finds linked symbol; `go:embed` pattern finds embedded file; doc-comment link follows reference; non-Go function can return assembly implementation; `return` locates named result variables; `goto`/`break`/`continue` finds target label or block. Already at declaration: most clients reinterpret request as "find references".

**Type Definition** (`textDocument/typeDefinition`, no CLI equivalent) — jumps to _named type_ underlying symbol, unwrapping pointer, array, slice, channel, map constructors first. For `x chan []*T`, reports `T`'s definition. Symbols only, not arbitrary expressions. No agent-invocable path: absent from native `LSP` tool's fixed operation list, so only full editor LSP client reaches it.

**References** (`textDocument/references`, CLI `gopls references`) — every use of symbol. Interface method: includes concrete implementations. Package declaration: includes direct imports and other files' package clauses. Embedded field: only field references (use Type Definition for references to type itself). **Scoping gotcha:** results reflect only queried file's build configuration; query on `foo_windows.go` will not surface match in `bar_linux.go`. Built-in symbols (`int`, `append`) rejected as too numerous to be useful.

**Implementation** (`textDocument/implementation`, CLI `gopls implementation`) — interface: concrete implementations and sub-interfaces. Concrete type: interfaces it satisfies. Interface method: concrete methods satisfying it, and vice versa. Matches method sets for types, signatures for functions; generic types are wildcards. Candidate included if _any_ instantiation would let one implement the other, without full unification check. LSP's built-in subtype bias makes query directionally asymmetric; for full bidirectional traversal, use Type Hierarchy.

**Document Symbol** (`textDocument/documentSymbol`, CLI `gopls symbols`) — outline of one file's top-level declarations. File-scoped; cross-file search: Symbol.

**Symbol / Workspace Symbol** (`workspace/symbol`, CLI `gopls workspace_symbol`) — fuzzy search across whole workspace. Default matcher `fastFuzzy` (FZF-inspired): abbreviations and typos still match, `DocSym` matches `DocumentSymbol`. Controlled by `symbolMatcher`, `symbolStyle`, `symbolScope` settings (see [settings.md](settings.md)); `directoryFilters` excludes directories from search.

**Selection Range** (`textDocument/selectionRange`, no CLI equivalent) — expands/contracts selection along syntactic boundaries (expression → statement → block → function). Use to select exact region an Extract refactor needs.

**Call Hierarchy** (`textDocument/prepareCallHierarchy` + `callHierarchyItem/incomingCalls`/`outgoingCalls`, CLI `gopls call_hierarchy`) — function's callers and callees as static graph. **Only static calls are included**: calls through function value or interface method invisible (not analytically tractable). Invoke on function declaration's name; corroborate with References when dynamically-dispatched call site matters.

**Type Hierarchy** (`textDocument/prepareTypeHierarchy` + `typeHierarchyItem/subtypes`/`typeHierarchy/supertypes`, no CLI equivalent yet) — bidirectional subtyping view: types implementing interface, interfaces type satisfies. Resolves Implementation's asymmetry. Limited to **named types** (Implementation also matches unnamed function types); alias types excluded; function-local types visible only within same package.

## Passive (always-on)

No explicit invocation; fire continuously during editor session. Most degrade when surrounding package has build errors, since they depend on successful type-checking.

**Hover** (`textDocument/hover`) — symbol name/kind/type/value; doc comment (clickable doc links like `[fmt.Printf]`); promoted methods from embedded fields; struct field size/offset and wasted-space percentage (flagged at ≥20% waste); expanded `//go:embed` patterns; `//go:linkname` targets; Go release that introduced stdlib symbol. Controlled by `hoverKind` (verbosity), `linkTarget` (base URI for doc links).

**Signature Help** (`textDocument/signatureHelp`) — parameter names/types/docs for called function, active parameter highlighted. Works with cursor inside function name too, not only inside parens.

**Document Highlight** (`textDocument/documentHighlight`) — highlights every identifier for same symbol in view, plus related tokens: named results and their return statements, loop control keywords (`for`/`break`/`continue`), switch tokens, function and its own return statements. Clients typically color read vs. write references differently.

**Inlay Hint** (`textDocument/inlayHint`) — inline annotations, off by default (visual clutter); toggle per kind via `hints` setting: `parameterNames` (call-site argument labels), `assignVariableTypes`, `compositeLiteralFields`, `compositeLiteralTypes`, `constantValues` (including computed `iota` values), `functionTypeParameters` (generic instantiations), `rangeVariableTypes`.

**Semantic Tokens** (`textDocument/semanticTokens`) — richer coloring than naive lexing: token types (`function`, `keyword`, `macro`, `method`, `namespace`, `number`, `operator`, `parameter`, `string`, `type`, `typeParameter`, `variable`, …) plus modifiers, including custom `shadowing` modifier flagging shadowed declarations. Off by default due to type-checking latency (`semanticTokens` setting). `noSemanticString`/`noSemanticNumber` let client opt out of only those two kinds to keep own lexical highlighting for them.

**Folding Range** (`textDocument/foldingRange`) — collapsible regions for large comments, functions, blocks.

**Document Link** (`textDocument/documentLink`) — makes URLs in doc comments and import declarations clickable (imports link to their pkg.go.dev page). Controlled by `importShortcut`, `linkTarget`.

## Diagnostics

Three sources, distinguished by LSP diagnostic's `source` field:

1. **Compilation errors** — gopls doesn't invoke real compiler. Runs `go list` for package metadata (`source: "go list"`), then mimics compiler front-end: read, scan, parse, type-check (`source: "compiler"`).
2. **Analysis findings** — `go vet` analysis framework plus gopls's own analyzers; each reports analyzer name as `source`. Representative example: `printf` analyzer (format-string/argument mismatches).
3. **Compiler optimization details** — off by default; toggle per package with `source.toggleCompilerOptDetails` code action. Shows escape analysis, nil-check elimination, inlining decisions. Only on packages otherwise error-free.

**Recomputation timing:** open-file compile errors update within tens of milliseconds of keystroke. Workspace-wide analysis diagnostics recompute after roughly one second idle, tunable via `diagnosticsDelay`; `diagnosticsTrigger` switches to save-triggered instead of edit-triggered. Clients initialized with `pullDiagnostics: true` can request diagnostics explicitly (`textDocument/diagnostic`, "pull diagnostics"); off by default for performance.

**Notable quick fixes**, offered as code actions attached to diagnostic:

- `fillreturns` — heuristically completes incomplete `return` statement.
- `stubMissingInterfaceMethods` — stubs methods when concrete type doesn't yet satisfy required interface.
- `StubMissingCalledFunction` — stubs undefined function/method, signature inferred from call site.
- `CreateUndeclared` — declares missing variable or function from how it's used.
- `source.fixAll` fixes count as unconditionally safe; most editors apply all with one shortcut.

CLI: `gopls check <file>` (`-severity=hint|info|warning|error`, default `warning`).

## Transformation

Three mechanisms: **Formatting** and **Rename** are primary LSP requests; almost everything else is a **CodeAction** (per range; returns direct edit or lazily computed command); a few dependency-management actions are **CodeLenses**.

**Formatting** (`textDocument/formatting`, CLI `gopls format`) — canonical Go formatting; client formatting options ignored. `gofumpt: true` switches to `mvdan.cc/gofumpt`'s stricter rules.

**Organize Imports** (`source.organizeImports`, CLI `gopls imports`) — removes unused/duplicate imports, adds missing ones (workspace-wide heuristics, occasionally surprising), sorts. `local` setting groups path prefix as "local," matching `goimports -local`. Most editors run it on save; disable per language if unwanted.

**Rename** (`textDocument/rename`, CLI `gopls rename`) — two-stage: `prepareRename` reports current name, then `rename` applies change everywhere. Refuses renames that would introduce shadowing or break interface satisfaction. Special positions unlock extra behavior:

- Rename **method's receiver declaration**: renames receiver across every method of that type. Rename receiver **use**: renames only that one variable.
- Rename **package name in `package` clause**: moves every package file to new directory (subpackages stay put unless `renameMovesSubpackages` set). Refused across module boundaries or into existing package.
- Rename **`func` keyword** of declaration: edit whole signature. Parameter/result count and types must stay same; no adding/removing parameters this way (for that, see `refactor.rewrite.removeUnusedParam`/`moveParamLeft`/`moveParamRight`).

**Extract** (`refactor.extract.*`) — replaces selection with reference to new declaration:

- `refactor.extract.variable` / `.constant` — new local binding for selected expression; `-all` variants rewrite every occurrence in enclosing function.
- `refactor.extract.function` / `.method` — one or more complete statements become call to new function (or method on same receiver, if extracted inside method).
- `refactor.extract.toNewFile` (gopls ≥ v0.17.0) — moves selected top-level declarations to new file, adding imports as needed; filename derives from first declared symbol.

Extract less rigorous than Rename/Inline: comments sometimes dropped; files with `DO NOT EDIT` generated-code marker get no code actions at all.

**Inline** (`refactor.inline.*`):

- `refactor.inline.call` — replaces call with function body, substituting parameters for arguments. Only static calls to accessible functions/methods: not through function value or interface method, not to unexported names outside package, not into `internal` packages, not generic functions. Preserves side-effect order (adds `var`s when argument must not be duplicated or reordered). Keeps qualified references correct (`Printf` → `fmt.Printf`, import added). Keeps implicit conversions explicit. Never drops variable's last use. `defer` bodies stay wrapped in closure, since defer semantics tie to function boundaries.
- `refactor.inline.variable` — replaces local variable's use with its initializer expression. Refuses if identifier in initializer was shadowed since declaration.

**Miscellaneous rewrites** (`refactor.rewrite.*`):

- `removeUnusedParam` — `unusedparams` analyzer offers rename to `_` (trivial) or full signature change updating every caller, preserving side-effecting arguments.
- `moveParamLeft` / `moveParamRight` — reorders one parameter, updating every call site.
- `changeQuote` — toggles string literal between raw (`` `...` ``) and interpreted (`"..."`) form; idempotent to apply twice.
- `invertIf` — negates plain `if`/`else` condition (no `else if` chain), swaps the two blocks.
- `splitLines` / `joinLines` — expands or collapses bracketed list (composite literal, call arguments, signature) one item per line. Skipped for lists already containing `//` comments or with fewer than two items.
- `fillStruct` — fills missing struct-literal fields, matching field names to in-scope variables/constants/functions where possible, zero value otherwise. Searches only current file, above cursor; if struct type was just introduced, run `source.organizeImports` first.
- `fillSwitch` — adds missing cases for enum-like set of named constants, or for type switch (one case per concrete type implementing interface, plus default that panics on unexpected type).
- `eliminateDotImport` — removes dot import, qualifies every reference; offered only when no name collision would result.
- `addTags` / `removeTags` — adds/removes struct field tags (e.g. `json`); interactive clients pick naming transform (`camelCase`, `snake_case`, `lisp-case`, `PascalCase`, `Title Case`).
- `implementInterface` — adds placeholder methods so named type satisfies chosen interface (default `error`). Interactive-dialog only, gopls-specific.

**Add Test For Function** (`source.addTest`) — generates table-driven test for selected function/method. Creates `_test.go` file if needed, copying copyright/build-constraint comments. Uses external `p_test` package to encourage testing exported API only. Results named `got`/`got2`/…, compared against `want`/`want2`/…; adds `wantErr bool` field when final result is `error`. For method, searches package for constructor (prefers `NewT` for type `T`). Leading `context.Context` parameter gets `t.Context()` on Go 1.24+, otherwise `context.Background()`.

## Web-based features

gopls runs small localhost web server (LSP `window/showDocument`) for reports too rich for inline editor UI. Every endpoint URL embeds random auth token; restarting gopls invalidates old links and shows disconnected banner on any page still open.

- **Package Documentation** (`source.doc`) — pkgsite-style rendered package docs, including **internal, unpublished packages** pkg.go.dev never sees. Symbol links jump editor to source declaration; reload without saving to see current edits.
- **Free Symbols** (`source.freesymbols`) — symbols a selection references but doesn't define itself, grouped as imported (with doc links), local, or package-level. Exact input list an Extract Function/Method refactor would need.
- **Assembly** (`source.assembly`) — compiled assembly listing for function, source-line-linked, recompiled on each reload. Architecture follows file's build tags (e.g. `foo_amd64.go`). Not yet supported for generic functions, `func init`, or functions in test packages.
- **Split Package** (`source.splitPackage`) — interactive dependency-graph tool for planning split of package into smaller, acyclic components. Visualizes split; does not yet perform code movement/renaming.

All send edits/navigation back to editor via `showDocument`, which works even against modified-but-unsaved source.

## Non-Go files

**Templates** (`text/template`/`html/template`) — disabled until `templateExtensions` lists at least one extension (templates have no canonical extension). Editor must also associate that extension with `tmpl`/`gotmpl` language ID (e.g. VS Code's `files.associations`). Inside `{{ }}` delimiters: diagnostics (parse errors; missing functions not flagged), full syntax highlighting, definitions and references (all templates share one global scope), completions. Hover, semantic tokens, symbol search, document highlight not yet implemented; custom delimiters other than `{{`/`}}` not understood.

**go.mod / go.work** — supports hover, hints, vulncheck-driven diagnostics, code lenses (add dependency, upgrade dependency, tidy, run `govulncheck`). Upstream page marks fine-grained behavior of each as still under documentation. Verify current behavior directly against `go.mod` file in editor session.

**Assembly (`.s`) files** — basic support; treat as best-effort.

## Completion

Upstream docs for this feature are a stub as of this writing (tracked as [golang/go#62022](https://github.com/golang/go/issues/62022)). Rely on empirical behavior plus these known settings, not documented spec: `usePlaceholders` (fills placeholder parameter names on completion), `completeFunctionCalls` (adds trailing parentheses, on by default). `completeUnimported` and `matcher`/`deepCompletion`-style settings shape whether not-yet-imported packages and nested field/method completions are offered. Full settings surface: [settings.md](settings.md).
