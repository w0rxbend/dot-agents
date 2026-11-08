---
name: golang-modernize
description: "Adopt newer Go language or library features when compatible with the module's declared Go version and consumers. Use for an intentional modernization; preserve behavior and avoid unrelated toolchain upgrades."
user-invocable: true
license: MIT
compatibility: Designed for Claude Code, Codex or similar harness, and for projects using Golang.
metadata:
  author: samber
  version: "1.5.1"
  openclaw:
    emoji: "🔄"
    homepage: https://github.com/samber/cc-skills-golang
    requires:
      bins:
        - go
    install: []
    skill-library-version: "1.27"
allowed-tools: Read Edit Write Glob Grep Bash(go version:*) Bash(go build:*) Bash(go test:*) Bash(go vet:*) Bash(go fix:*) Bash(go doc:*) Bash(go list:*) Bash(go mod tidy:*) Bash(go mod why:*) Bash(go tool govulncheck:*) Bash(golangci-lint:*) Bash(git diff:*) Bash(git status:*) Bash(git log:*) Bash(git show:*) Agent WebFetch(domain:go.dev) AskUserQuestion EnterWorktree ExitWorktree
paths:
  - "**/*.go"
---

<!-- markdownlint-disable ol-prefix -->

**Persona:** Go modernization engineer. Keep codebases on latest Go idioms and standard library improvements.

**Modes:**

- **Inline mode** (developer actively coding): suggest only modernizations for current file or feature. Note other opportunities plus quality gain each; developer schedules them.
- **Full-scan mode** (explicit `/golang-modernize` invocation or CI): up to 5 parallel sub-agents. Agent 1: deprecated packages and API replacements. Agent 2: language features (range-over-int, min/max, any, iterators). Agent 3: standard library upgrades (slices, maps, cmp, slog). Agent 4: testing patterns (t.Context, b.Loop, synctest). Agent 5: tooling and infra (golangci-lint v2, govulncheck, PGO, CI pipeline). Consolidate, prioritize by migration priority guide. Scan is read-only. Apply consolidated codebase-wide rewrite in isolated worktree; it never touches developer's main tree until reviewed. On Claude Code, `ultracode` opts into multi-agent orchestration explicitly.

**Questions:** Inline mode triggers while developer works on something else. Ask once via environment's question tool: suggest noticed opportunities, or skip for now? On skip, stop immediately; never raise modernization again this session.

# Go Code Modernization Guide

**Scope**: Roughly last 3 years of Go releases (oldest to newest row of Go Version Changelogs table below, updated each Go release). `go.mod` older than oldest row still gets suggestions, narrower coverage; upgrade Go version first for best results. Some older modernizations (e.g., `any` instead of `interface{}`, `errors.Is`/`errors.As`, `strings.Cut`) included: still commonly missed. Many pre-1.21 improvements omitted on purpose: baseline Go practice by now.

MUST NEVER do large refactoring while developer works on a different task.

## Workflow

When invoked:

1. **Check `go.mod` or `go.work`** for current Go version (`go` directive)
2. **Check latest Go version** in Go Version Changelogs table below; if `go.mod` is behind, suggest upgrade and explain benefits unlocked
3. **Read `.modernize`** in project root: previously ignored suggestions. Do NOT re-suggest anything listed there
4. **Scan codebase** for opportunities matching target Go version
5. **Run `golangci-lint`** with `modernize` linter if available, and `go test ./...`. Go 1.27+ runs `stdversion` vet check by default, flagging APIs newer than module's `go` directive. Bump directive or revert suggestion; don't ignore hit
6. **Suggest improvements contextually**: developer actively coding → only code they're working on, no refactoring unrelated files; mention other opportunities and why they help, developer decides. Explicit `/golang-modernize` or CI → scan and suggest across entire codebase.
7. **Large codebases**: parallelize scan across up to 5 sub-agents, one modernization category each (see Full-scan mode). Apply ready changes in isolated worktree.
8. **Before suggesting dependency update**, run `go mod tidy` and test suite to verify compatibility. Ask developer to check dependency changelog and release notes for breaking changes first.
9. **Developer explicitly ignores suggestion**: write short memo to `.modernize` in project root so it is not suggested again. One line per ignored suggestion, short description.

When modernization renames identifier or replaces deprecated API (e.g. `reflect.PtrTo` → `PointerTo`, `math/rand` → `math/rand/v2`), → See `samber/cc-skills-golang@golang-gopls` skill. Safe rename updates every call site and refuses renames breaking interface satisfaction. Post-edit diagnostics catch compile errors across rewritten files that blind Edit or grep/sed sweep leaves broken.

### `.modernize` file format

```
# Ignored modernization suggestions
# Format: <date> <category> <description>
2026-01-15 slog-migration Team decided to keep zap for now
2026-02-01 math-rand-v2 Legacy module requires math/rand compatibility
```

## Go Version Changelogs

Cite relevant changelog when suggesting modernization:

| Version | Release       | Changelog                   |
| ------- | ------------- | --------------------------- |
| Go 1.21 | August 2023   | <https://go.dev/doc/go1.21> |
| Go 1.22 | February 2024 | <https://go.dev/doc/go1.22> |
| Go 1.23 | August 2024   | <https://go.dev/doc/go1.23> |
| Go 1.24 | February 2025 | <https://go.dev/doc/go1.24> |
| Go 1.25 | August 2025   | <https://go.dev/doc/go1.25> |
| Go 1.26 | February 2026 | <https://go.dev/doc/go1.26> |
| Go 1.27 | August 2026   | <https://go.dev/doc/go1.27> |

Newer than Go 1.27: consult official Go release notes.

## Using the modernize linter

`modernize` linter (since **golangci-lint v2.6.0**) detects code rewritable with newer Go features. Origin: `golang.org/x/tools/go/analysis/passes/modernize`. `gopls` and `go fix` cover overlapping checks; exact coverage differs by tool version. `go fix` was rewritten onto `go/analysis` framework in Go 1.26; fixer coverage still growing in Go 1.27 (exact fixer list: [Tooling modernization](./references/tooling.md)). Configuration: `samber/cc-skills-golang@golang-lint` skill.

## Version-specific modernizations

Before/after examples per Go version (1.21–1.27) plus general modernizations: [Go version modernizations](./references/versions.md).

## Tooling modernization

CI tooling, govulncheck, PGO, golangci-lint v2, AI-powered modernization pipelines: [Tooling modernization](./references/tooling.md).

## Deprecated Packages Migration

| Deprecated | Replacement | Since |
| --- | --- | --- |
| `math/rand` | `math/rand/v2` | Go 1.22 |
| `crypto/elliptic` (most functions) | `crypto/ecdh` | Go 1.21 |
| `reflect.SliceHeader`, `StringHeader` | `unsafe.Slice`, `unsafe.String` | Go 1.21 |
| `reflect.PtrTo` | `reflect.PointerTo` | Go 1.22 |
| `runtime.GOROOT()` | `go env GOROOT` | Go 1.24 |
| `runtime.SetFinalizer` (not deprecated; docs say new code should consider `AddCleanup`) | prefer `runtime.AddCleanup` | Go 1.24 |
| `crypto/cipher.NewOFB`, `NewCFB*` | AEAD modes or `NewCTR` | Go 1.24 |
| `golang.org/x/crypto/sha3` | `crypto/sha3` | Go 1.24 |
| `golang.org/x/crypto/hkdf` | `crypto/hkdf` | Go 1.24 |
| `golang.org/x/crypto/pbkdf2` | `crypto/pbkdf2` | Go 1.24 |
| `testing/synctest.Run` | `testing/synctest.Test` | Go 1.25 |
| `crypto/rsa.EncryptPKCS1v15` for new encryption | RSA-OAEP (`rsa.EncryptOAEP` / `rsa.EncryptOAEPWithOptions`) or HPKE/KEM design | Go 1.26 |
| `net/http/httputil.ReverseProxy.Director` | `ReverseProxy.Rewrite` | Go 1.26 |
| `crypto/tls.Config.Rand` | `testing/cryptotest.SetGlobalRandom()` | Go 1.27 |
| `github.com/google/uuid` (simple cases) | `uuid` (stdlib) | Go 1.27 |

## Go 1.27+ version-bump risk checklist

Several Go 1.27 changes need **verification, not a rewrite**, before `go.mod` bump ships. Key one: `godebug` line in `go.mod` (or `//go:debug` comment) still pinning `asynctimerchan`, `tlsunsafeekm`, `tlsrsakex`, `tls3des`, `tls10server`, `x509keypairleaf`, or `gotypesalias` to **old** value now fails build. Full checklist: [Go version modernizations](./references/versions.md#go-127-version-bump-risk-checklist-verify-dont-rewrite).

## Migration Priority Guide

### High priority (safety and correctness)

1. Remove loop variable shadow copies _(Go 1.22+)_ — prevents subtle bugs
2. Replace `math/rand` with `math/rand/v2` _(Go 1.22+)_ — remove `rand.Seed` calls
3. Use `os.Root` for user-supplied file paths _(Go 1.24+)_ — prevents path traversal
4. Run `govulncheck` _(Go 1.22+)_ — catch known vulnerabilities
5. Use `errors.Is`/`errors.As` instead of direct comparison _(Go 1.13+)_
6. Migrate deprecated crypto packages _(Go 1.24+)_ — security critical
7. Before bumping to `go 1.27`, resolve removed `GODEBUG` keys and `crypto/tls.Config.Rand` callers _(Go 1.27+)_ — see risk checklist above; stale `GODEBUG` value fails build

### Medium priority (readability and maintainability)

8. Replace `interface{}` with `any` _(Go 1.18+)_
9. Use `min`/`max` builtins _(Go 1.21+)_
10. Use `range` over int _(Go 1.22+)_
11. Use `slices` and `maps` packages _(Go 1.21+)_
12. Use `cmp.Or` for default values _(Go 1.22+)_
13. Use `sync.OnceValue`/`sync.OnceFunc` _(Go 1.21+)_
14. Use `sync.WaitGroup.Go` _(Go 1.25+)_
15. Use `t.Context()` in tests _(Go 1.24+)_
16. Use `b.Loop()` in benchmarks _(Go 1.24+)_
17. Use generic methods for helpers scoped to one type, and `strings.CutLast`/`bytes.CutLast` instead of `LastIndex` slicing _(Go 1.27+)_
18. Migrate to `encoding/json/v2` API, default since Go 1.27; first check duplicate-key and invalid-UTF-8 strictness against real payloads _(Go 1.27+)_

### Lower priority (gradual improvement)

19. Migrate to `slog` from third-party loggers _(Go 1.21+)_
20. Adopt iterators where they simplify code _(Go 1.23+)_
21. Replace `sort.Slice` with `slices.SortFunc` _(Go 1.21+)_
22. Use `strings.SplitSeq` and iterator variants _(Go 1.24+)_
23. Move tool deps to `go.mod` tool directives _(Go 1.24+)_
24. Enable PGO for production builds _(Go 1.21+)_
25. Upgrade to golangci-lint v2 with modernize linter _(golangci-lint v2.6.0+)_
26. Add `govulncheck` to CI pipeline
27. Set up monthly modernization CI pipeline
28. Replace `google/uuid`/`gofrs/uuid` with stdlib `uuid` package, after checking for RFC-variant features stdlib doesn't cover _(Go 1.27+)_
29. Run `go fix ./...` after toolchain upgrade for safe automated transformations _(Go 1.27+)_
30. Set up AI-driven code review in CI — loads these skills per review area; see `samber/cc-skills-golang@golang-continuous-integration`

## Related Skills

See `samber/cc-skills-golang@golang-concurrency`, `samber/cc-skills-golang@golang-testing`, `samber/cc-skills-golang@golang-observability`, `samber/cc-skills-golang@golang-error-handling`, `samber/cc-skills-golang@golang-lint`, `samber/cc-skills-golang@golang-continuous-integration` skills.

- → See `samber/cc-skills-golang@golang-refactoring` skill to stage large modernization sweep as small human-reviewed PRs instead of one big worktree sweep.
