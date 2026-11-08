# `gopls` CLI reference

Go team documents this interface as experimental: "not efficient, complete, flexible, or officially supported." Use as debugging and one-shot-scripting fallback, not primary way to drive `gopls`. Prefer MCP tools or native `LSP` tool when available (see [mcp.md](mcp.md)).

## Table of contents

- [Position syntax](#position-syntax)
- [Global flags](#global-flags)
- [Shared write flags](#shared-write-flags)
- [Navigation commands](#navigation-commands)
- [Diagnostics](#diagnostics)
- [Transformation commands](#transformation-commands)
- [Code actions and code lenses](#code-actions-and-code-lenses)
- [Introspection](#introspection)
- [CodeAction kind reference](#codeaction-kind-reference)

## Position syntax

Two interchangeable position formats:

- `file.go:line:column` — both 1-indexed. Columns count UTF-8 bytes, not runes or UTF-16 code units; on non-ASCII lines, an editor that counts differently can report a different column.
- `file.go:#1234` — 0-indexed byte offset from file start.

```bash
gopls definition internal/cmd/definition.go:44:47
gopls definition internal/cmd/definition.go:#1270
```

## Global flags

Flags for `gopls` itself, before subcommand:

| Flag | Value | Purpose |
| --- | --- | --- |
| `-logfile=<path>` | file path, or literal string `auto` | Log destination; `auto` picks default output file instead of stderr |
| `-profile.cpu=<path>` | file path | CPU profile output |
| `-profile.mem=<path>` | file path | Memory profile output |
| `-profile.alloc=<path>` | file path | Allocation profile output |
| `-profile.block=<path>` | file path | Blocking-profile output |
| `-profile.trace=<path>` | file path | Execution trace output |
| `-v`, `-verbose` | boolean, no value | Verbose output |
| `-vv`, `-veryverbose` | boolean, no value | Very verbose output |

`gopls mcp` has own, narrower flags: `-listen=<addr>` (SSE/HTTP instead of stdio; bind `localhost` only), `-logfile=<path>` (default stderr), `-rpc.trace` (cannot combine with `-listen`).

## Shared write flags

Every source-modifying command (`format`, `imports`, `rename`, `codeaction`, `codelens`, `execute`) accepts these boolean flags (no value):

| Flag | Purpose |
| --- | --- |
| `-w`, `-write` | Write edits back to source file(s) |
| `-d`, `-diff` | Print unified diff instead of writing |
| `-l`, `-list` | Print only names of files that would be/were edited |
| `-preserve` | With `-w`: keep copy of each original before overwriting |

Not mutually exclusive. With none, edit is computed but neither printed nor written.

## Navigation commands

| Command | Flags | Example | Notes |
| --- | --- | --- | --- |
| `definition` | `-json` (boolean), `-markdown` (boolean) | `gopls definition helper/helper.go:8:6` | `-json` for structured output, `-markdown` renders doc comments as Markdown |
| `references` | `-d`, `-declaration` (boolean) | `gopls references helper/helper.go:8:6` | When set, results include declaration itself |
| `implementation` | none | `gopls implementation helper/helper.go:8:6` | — |
| `call_hierarchy` | none | `gopls call_hierarchy helper/helper.go:8:6` | Static calls only |
| `symbols` | none | `gopls symbols helper/helper.go` | File-scoped outline |
| `workspace_symbol` | `-matcher=<value>` — one of `fuzzy`, `fastfuzzy`, `casesensitive`, `caseinsensitive` (default `caseinsensitive`) | `gopls workspace_symbol -matcher fuzzy 'wsymbols'` | Query matching algorithm |
| `signature` | none | `gopls signature helper/helper.go:8:6` | Function signature at position |
| `highlight` | none | `gopls highlight helper/helper.go:8:6` | Same-symbol identifier highlights |
| `folding_ranges` | none | `gopls folding_ranges helper/helper.go` | Collapsible regions |
| `links` | `-json` (boolean) | `gopls links internal/cmd/check.go` | Structured output when set |
| `prepare_rename` | none | `gopls prepare_rename helper/helper.go:8:6` | Checks rename is possible at position before attempting it |
| `semtok` | none | `gopls semtok internal/cmd/semtok.go` | Semantic token dump |

## Diagnostics

| Command | Flags | Example |
| --- | --- | --- |
| `check` | `-severity=<value>` — one of `hint`, `info`, `warning`, `error` (default `warning`); reports diagnostics at or above this severity | `gopls check -severity=error internal/cmd/check.go` |

## Transformation commands

All also accept [shared write flags](#shared-write-flags) above.

| Command | Positional args | Example | Notes |
| --- | --- | --- | --- |
| `format` | one or more `<filerange>` (file, or range within one) | `gopls format -w internal/cmd/check.go` | Canonical `gofmt`-equivalent; ignores client formatting options |
| `imports` | `<filename>` | `gopls imports -w internal/cmd/check.go` | Adds/removes/sorts imports |
| `rename` | `<position> <new-name>` | `gopls rename helper/helper.go:8:6 Foo` | `<new-name>` is plain identifier; if unsure, validate first with `prepare_rename` |

## Code actions and code lenses

`codeaction` and `codelens` also accept [shared write flags](#shared-write-flags).

| Command | Extra flags | Notes |
| --- | --- | --- |
| `codeaction` | `-kind=<value>` — comma-separated kinds, see [CodeAction kind reference](#codeaction-kind-reference) below; `-title=<regex>` — filter actions by title; `-exec` (boolean) — execute first match instead of only listing | `-kind=refactor` matches every kind nested under it (kinds are hierarchical); only one action executes per invocation, no conflict resolution for applying more; `source.test` actions excluded unless explicitly requested via `-kind` |
| `codelens` | `-exec` (boolean) — run first matching lens instead of only listing | Positional args: `<file>`, `<file:line>`, or `<file> <title>` |
| `execute` | none beyond shared write flags | Takes `<command> <json-argument>`; sends raw LSP `ExecuteCommand` request. gopls's command set (`command.Interface`) is unstable, may change between versions |

```bash
# List available code actions for a range
gopls codeaction -kind=quickfix ./gopls/main.go

# Execute the first matching action and show a diff
gopls codeaction -kind=quickfix -exec -diff ./gopls/main.go

# Filter by title (regex) in addition to kind
gopls codeaction -kind=refactor.rewrite -title 'Fill struct' -exec -w file.go:12:3

# Code lenses: list, or run a specific one
gopls codelens a_test.go                     # list lenses in a file
gopls codelens a_test.go:10                  # list lenses on line 10
gopls codelens a_test.go "run test"          # list gopls.run_tests commands
gopls codelens -exec a_test.go:10 "run test" # run a specific test

# Execute a raw LSP ExecuteCommand
gopls execute gopls.add_import '{"ImportPath": "fmt", "URI": "file:///hello.go"}'
gopls execute gopls.run_tests '{"URI": "file:///a_test.go", "Tests": ["Test"]}'
gopls execute gopls.list_known_packages '{"URI": "file:///hello.go"}'
```

## Introspection

| Command | Flags | Notes |
| --- | --- | --- |
| `stats` | `-anon` (boolean) | JSON summary of performance-relevant workspace info; populates file cache as side effect. `-anon` redacts fields that could leak user/file names or source text |
| `version` | none | Print gopls version info |
| `api-json` | none | Print gopls' full API surface as JSON |
| `bug` | none | Report bug in gopls |
| `licenses` | none | Print licenses of bundled software |

## CodeAction kind reference

Passed to `-kind` on `codeaction` (comma-separated, hierarchical — `refactor` matches all `refactor.*`):

```
gopls.doc.features
quickfix
refactor
refactor.extract
refactor.extract.constant
refactor.extract.function
refactor.extract.method
refactor.extract.toNewFile
refactor.extract.variable
refactor.inline
refactor.inline.call
refactor.rewrite
refactor.rewrite.changeQuote
refactor.rewrite.fillStruct
refactor.rewrite.fillSwitch
refactor.rewrite.invertIf
refactor.rewrite.joinLines
refactor.rewrite.removeUnusedParam
refactor.rewrite.splitLines
source
source.assembly
source.doc
source.fixAll
source.freesymbols
source.organizeImports
source.test
```

More kinds exist beyond this `-kind`-documented set, reachable only through editor UI or `execute`/code lens, not by name filter: `refactor.extract.variable-all`, `refactor.extract.constant-all`, `refactor.inline.variable`, `refactor.rewrite.moveParamLeft`, `refactor.rewrite.moveParamRight`, `refactor.rewrite.eliminateDotImport`, `refactor.rewrite.addTags`, `refactor.rewrite.removeTags`, `refactor.rewrite.implementInterface`, `source.addTest`, `source.splitPackage`, `source.toggleCompilerOptDetails`. What each does: [features.md](features.md#transformation).
