# gopls settings reference

Source: [tip.golang.org/gopls/settings](https://tip.golang.org/gopls/settings); full canonical list (incl. experimental and client-specific keys): `gopls api-json`. Tables below cover only settings most likely to change day-to-day navigation, diagnostics or refactor behavior, not full API. Settings go through LSP client's `initializationOptions` (editor-specific config file/UI); by default, no `gopls.json` is read from workspace. Record chosen settings in project's agent-config file (CLAUDE.md, AGENTS.md, or equivalent) so future sessions reuse them without rediscovery.

## Table of contents

- [Build](#build)
- [Formatting](#formatting)
- [Diagnostics](#diagnostics)
- [Documentation](#documentation)
- [Inlay hints](#inlay-hints)
- [Navigation](#navigation)

## Build

| Setting | Type | Default | Purpose |
| --- | --- | --- | --- |
| `buildFlags` | `[]string` | `[]` | Extra build-system flags, usually `-tags=<tag>` to bring build-tagged files into scope |
| `env` | `map[string]string` | `{}` | Environment variables for external commands gopls runs (`go list`, etc.) |
| `directoryFilters` | `[]string` | `["-**/node_modules"]` | Include/exclude workspace directories from loading and workspace-symbol search; `+`/`-` prefixed glob patterns |
| `expandWorkspaceToModule` | `bool` | `true` | Whether enclosing module (not just opened directory) counts as "workspace" for diagnostics scope |
| `templateExtensions` | `[]string` | `[]` | File extensions treated as Go templates (templates have no canonical extension, so empty by default) |

**When it matters:** symbol behind build tag (`//go:build integration`) is invisible to `references`/`go_search` until `buildFlags: ["-tags=integration"]` is set. Same root cause as References build-configuration scoping gotcha in [features.md](features.md#navigation).

## Formatting

| Setting | Type | Default | Purpose |
| --- | --- | --- | --- |
| `local` | `string` | `""` | Import path prefix treated as "local" for import grouping/sort order; equivalent to `goimports -local` |
| `gofumpt` | `bool` | `false` | Format with `mvdan.cc/gofumpt`'s stricter rules instead of plain `gofmt` |

## Diagnostics

| Setting | Type | Default | Purpose |
| --- | --- | --- | --- |
| `analyses` | `map[string]bool` | `{}` | Enable/disable individual analyzers by name (`go vet`-based framework plus gopls's own) |
| `staticcheck` | `bool` | `false` | Add staticcheck.io analyzer suite to built-in analyzers |
| `vulncheck` | enum: `Off`\|`Imports`\|`Prompt` | `"Prompt"` (or `"Off"` in some client defaults) | Whether/how vulnerability-driven diagnostics on `go.mod` run |
| `diagnosticsDelay` | `time.Duration` | `"1s"` | Idle time after edit before workspace-wide analysis diagnostics recompute (open-file compile errors update sooner regardless) |
| `diagnosticsTrigger` | enum: `Edit`\|`Save` | `"Edit"` | Recompute diagnostics on every edit or only on save |
| `pullDiagnostics` | `bool` | `false` | Let client request diagnostics on demand (`textDocument/diagnostic`), not only receive pushed updates |

**When it matters:** in large monorepo, `diagnosticsTrigger: "Edit"` (default) with `diagnosticsDelay: "1s"` can feel laggy at every keystroke pause. Switching to `"Save"` trades immediacy for fewer full-workspace recomputations. Enabling `staticcheck` surfaces materially different (larger) set of findings than default analyzers; expect more `go_diagnostics`/`gopls check` output afterward, not a regression.

## Documentation

| Setting | Type | Default | Purpose |
| --- | --- | --- | --- |
| `hoverKind` | enum: `FullDocumentation`\|`SingleLine`\|`Structured`\|`NoDocumentation`\|`SynopsisDocumentation` | `"FullDocumentation"` | How much doc text Hover renders |
| `linksInHover` | `bool` | `true` | Whether hover markdown includes doc-comment links |
| `linkTarget` | `string` | `"pkg.go.dev"` | Base host for generated documentation links (hover, Document Link, diagnostics) |

## Inlay hints

| Setting | Type | Default | Purpose |
| --- | --- | --- | --- |
| `hints` | `map[string]bool` | `{}` (all off) | Enables specific inlay hint kinds; keys: `parameterNames`, `assignVariableTypes`, `compositeLiteralFields`, `compositeLiteralTypes`, `constantValues`, `functionTypeParameters`, `rangeVariableTypes` |

Example:

```json
"hints": {
  "parameterNames": true,
  "assignVariableTypes": true
}
```

## Navigation

| Setting | Type | Default | Purpose |
| --- | --- | --- | --- |
| `symbolMatcher` | enum: `FastFuzzy`\|`Fuzzy`\|`CaseSensitive`\|`CaseInsensitive` | `"FastFuzzy"` | Matching algorithm for `workspace/symbol` / `go_search` |
| `symbolScope` | enum: `all`\|`workspace` | `"all"` | Whether symbol search covers only workspace packages or every loaded package (including dependencies) |
| `symbolStyle` | enum | — | How matched symbols are qualified in response (package-qualified vs. bare) |
| `codelenses` | `map[string]bool` | — | Enables/disables individual code lenses (e.g. `generate`, `tidy`, `vendor`, `run_tests`) |
