# gopls MCP server & native `LSP` tool reference

## Table of contents

- [Starting the server](#starting-the-server)
- [Registering the MCP server](#registering-the-mcp-server)
- [MCP tools](#mcp-tools)
- [The native `LSP` tool](#the-native-lsp-tool)
- [What the MCP server can and cannot do](#what-the-mcp-server-can-and-cannot-do)

## Starting the server

Standalone gopls instance speaking MCP over stdin/stdout, fresh per session, no LSP client involved:

```bash
gopls mcp
```

Sees files only as they exist **on disk**: unsaved edits made through another tool are invisible to it.

## Registering the MCP server

Launch command (`gopls mcp`) is harness-agnostic; any MCP-capable host can point at it. Claude Code registers it via own CLI:

```bash
claude mcp add gopls -- gopls mcp
```

Other MCP-capable harnesses (Cursor, Windsurf, others) each register it in own settings file, with `gopls mcp` as launch command. No shared config format.

## MCP tools

Eight tools, all keyed by name/path/query, not cursor position: main ergonomic difference from native `LSP` tool.

| Tool | Purpose | Example |
| --- | --- | --- |
| `go_workspace` | Workspace's overall structure: module, multi-module workspace, or GOPATH project. | `go_workspace({})` |
| `go_vulncheck` | On-demand reachability check: which known vulnerabilities _current_ build actually reaches. | `go_vulncheck({"pattern":"./..."})` |
| `go_search` | Fuzzy search for type, function or variable by name, workspace-wide. Use when exact location unknown. | `go_search({"query":"server"})` |
| `go_file_context` | File's dependencies on other files in _same package_. | `go_file_context({"file":"/path/to/server.go"})` |
| `go_package_api` | Package's public API. Most valuable for third-party dependencies or monorepo sibling packages not read file by file. | `go_package_api({"packagePaths":["example.com/internal/storage"]})` |
| `go_symbol_references` | Every reference to symbol. | `go_symbol_references({"file":"/path/to/server.go","symbol":"Server.Run"})` |
| `go_diagnostics` | Build/analysis errors for given files. Mandatory after every edit. | `go_diagnostics({"files":["/path/to/server.go"]})` |
| `go_rename_symbol` | Rename symbol and every reference, workspace-wide, with same safety checks as LSP rename (blocks changes that would break interface satisfaction). | — |

Read/Edit workflow order for chaining these tools: [SKILL.md](../SKILL.md#efficient-workflows).

## The native `LSP` tool

Claude Code's built-in editor-style integration; different mechanism from MCP server above. Wire it in addition to MCP server, not instead of it.

**Enabling it:**

1. Set environment variable `ENABLE_LSP_TOOL=1` (off by default).
2. Install `gopls` (`go install golang.org/x/tools/gopls@v0.24.0`, pinned reviewed release; ask user first).
3. Install official `gopls-lsp@claude-plugins-official` marketplace plugin; it wires `gopls` as Go language server behind the tool.

**Operations**, all keyed by `line`/`character`, not name/path:

- `goToDefinition`
- `findReferences`
- `hover`
- `documentSymbol`
- `workspaceSymbol`
- `goToImplementation`
- call hierarchy

`goToTypeDefinition` intentionally absent: native tool does not expose it, so type-definition navigation has no agent-invocable path (see [features.md](features.md#navigation)).

These need location up front, so most efficient once you have one (right after grep or file read), not as first investigation move. First move: `go_search` on MCP server.

**Its unique value:** compiler diagnostics pushed into context **automatically after every edit**, no explicit diagnostics call needed. MCP server's `go_diagnostics` needs explicit invocation each time.

## What the MCP server can and cannot do

gopls MCP server wraps LSP functionality within these boundaries:

- **Can**: read files from filesystem and return contents; run `go` commands to load package metadata (may reach `proxy.golang.org` and write to local Go module/build cache); write to gopls's own cache/configuration files; upload telemetry if user opted in.
- **Cannot**: make arbitrary writes to source tree beyond edits a tool call explicitly returns; make arbitrary network requests beyond what `go` itself needs to resolve build.
