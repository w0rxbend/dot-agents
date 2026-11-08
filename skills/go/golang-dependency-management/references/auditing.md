# Auditing Dependencies

## Test-Only vs Binary Dependencies

`go.mod` does **not** separate test-only from production dependencies. All modules appear together; `// indirect` marks transitive ones.

### What Gets Included in Your Binary

- `*_test.go` files are **never** compiled by `go build`, only by `go test`
- Packages imported only by tests are not linked into final binary
- Their modules still appear in `go.mod`

### Module Graph Pruning (Go 1.17+)

With `go 1.17` or higher in `go.mod`, Go prunes module graph: transitive dependencies needed only by other modules' tests drop out of build graph.

### Upgrading With or Without Test Dependencies

```bash
go get -u ./...       # Upgrade deps, EXCLUDING test-only deps
go get -u -t ./...    # Upgrade deps, INCLUDING test-only deps
```

### Impact on Binary Size

To see whether large dependency is linked or only used in tests, run `goweight` or `go-size-analyzer`. If absent from binary breakdown, it is test-only and adds no size.

## Vulnerability Scanning with govulncheck

`govulncheck` reports known vulnerabilities affecting your code. Static analysis limits reports to code paths your project calls; generic CVE scanners flag every dependency regardless of usage.

```bash
# Scan source code (most common)
govulncheck ./...
# Or, when govulncheck is pinned with a Go 1.24+ tool directive:
go tool govulncheck ./...

# Scan a compiled binary
govulncheck -mode=binary ./bin/myapp

# JSON output (for CI integration)
govulncheck -format json ./...

# Include test code in analysis
govulncheck -test ./...
```

Output: vulnerability ID, affected module, fixed version, call trace from your code to vulnerable function.

CI integration: see `samber/cc-skills-golang@golang-continuous-integration` skill.

## Tracking Outdated Dependencies with go-mod-outdated

`psampaz/go-mod-outdated` lists direct dependencies with available updates.

```bash
# Show outdated direct dependencies with available updates
go list -u -m -json all | go-mod-outdated -update -direct

# Fail in CI if dependencies are outdated
go list -u -m -json all | go-mod-outdated -update -direct -ci

# Markdown output
go list -u -m -json all | go-mod-outdated -update -direct -style markdown
```

Output columns: MODULE, CURRENT version, WANTED (latest minor/patch), LATEST (latest overall), VALID TIMESTAMPS (warns if "update" is chronologically older than current).

## Analyzing Dependency Size with goweight

`jondot/goweight` lists every package linked into binary, sorted by size.

```bash
goweight          # Sort by size
goweight --json   # JSON output for CI tracking
```

**Modern alternative**: [go-size-analyzer](https://github.com/Zxilly/go-size-analyzer) (`gsa`) supports ELF, Mach-O, PE, WebAssembly; interactive HTML/SVG visualization:

```bash
go get -tool github.com/Zxilly/go-size-analyzer/cmd/gsa@latest
go build -o ./myapp ./cmd/myapp
go tool gsa -f html -o size-report.html ./myapp
```
