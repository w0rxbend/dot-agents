# Capability → CLI → MCP → native LSP

Each gopls capability mapped to CLI command, MCP tool, native `LSP` tool operation, where one exists. `—`: that surface has no path to capability.

| Capability | CLI | MCP tool | Native LSP op |
| --- | --- | --- | --- |
| Workspace layout (module/workspace/GOPATH) | `gopls stats` | `go_workspace` | — |
| Fuzzy-find symbol by name, workspace-wide | `gopls workspace_symbol <query>` | `go_search` | `workspaceSymbol` |
| Go to definition | `gopls definition f:l:c` | — (use `go_file_context`/`go_package_api`) | `goToDefinition` |
| Go to type definition | — (unsupported) | — | — (not in native tool's fixed op list) |
| Find all references | `gopls references f:l:c` | `go_symbol_references` | `findReferences` |
| Implements / implemented-by | `gopls implementation f:l:c` | — | `goToImplementation` |
| Full subtype/supertype tree | — (not yet supported) | — | Type Hierarchy |
| Call graph (callers/callees) | `gopls call_hierarchy f:l:c` | — | Call Hierarchy |
| Expand/contract selection along syntax boundaries | — (unsupported) | — | `selectionRange` (editor gesture, no agent-invoked path) |
| File's own symbols (outline) | `gopls symbols <file>` | `go_file_context` | `documentSymbol` |
| Package's public API | — | `go_package_api` | (hover per symbol) |
| File's intra-package dependencies | — | `go_file_context` | — |
| Hover info (type, doc, size/offset) | — | — | `hover` |
| Signature help | `gopls signature f:l:c` | — | signature help |
| Same-symbol identifier highlights | `gopls highlight f:l:c` | — | `documentHighlight` (not in native tool's fixed op list) |
| Semantic tokens (rich syntax coloring) | `gopls semtok <file>` | — | `semanticTokens` (editor-automatic, not agent-invoked) |
| Folding ranges (collapsible regions) | `gopls folding_ranges <file>` | — | `foldingRange` (editor-automatic, not agent-invoked) |
| Document links (URLs in doc comments/imports) | `gopls links <file>` | — | `documentLink` (editor-automatic, not agent-invoked) |
| Compiler + analyzer diagnostics | `gopls check <file>` | `go_diagnostics` | automatic, pushed after every edit |
| Vulnerability reachability (current build) | — | `go_vulncheck` | — |
| Safe rename (symbol, receiver, package move, signature) | `gopls rename -w f:l:c NewName` | `go_rename_symbol` | rename |
| Organize / fix imports | `gopls imports -w <file>` | — | `source.organizeImports` code action |
| Format | `gopls format -w <file>` | — | `textDocument/formatting` |
| Refactor (extract, inline, fill, rewrite — see [features.md](features.md)) | `gopls codeaction -kind=<kind> -exec -w <file>` | — | code action |
| Generate test for function | `gopls codelens -exec <file:line> "..."` (via `source.addTest`) | — | code action / code lens |
| Rendered package docs (incl. internal packages) | — | — | `source.doc` code action → browser report |
| Free symbols of selection (inputs before extracting) | — | — | `source.freesymbols` code action → browser report |
| Function assembly listing | — | — | `source.assembly` code action → browser report |
| Split-package dependency planning | — | — | `source.splitPackage` code action → browser report |
