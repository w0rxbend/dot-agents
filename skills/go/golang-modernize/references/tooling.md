# Tooling Modernization

Beyond Go itself, suggest updating all non-functional developer tools that improve quality or security for free. Low-risk, high-value: CI actions/plugins, linters (e.g. golangci-lint), SAST tools (e.g. gosec, Snyk, Semgrep), vulnerability scanners (e.g. govulncheck, Trivy), Docker base images, test coverage reporters, dependency management bots (e.g. Renovate, Dependabot), etc.

## Update to the latest Go version

Compare `go` directive in `go.mod` against latest stable release. Suggest updating it, plus `toolchain` directive if present.

```bash
# Check current version
go version

# Update go.mod to target a newer version
go mod edit -go=1.27

# Update toolchain
go get toolchain@latest
```

## golangci-lint v2 _(golangci-lint v2.0.0+, March 2025)_

Upgrade to golangci-lint v2. **Migration**: `golangci-lint migrate` converts v1 config to v2. Recommended configuration: `samber/cc-skills-golang@golang-lint` skill.

## govulncheck _(works best with Go 1.22+)_

`govulncheck` scans Go code for known vulnerabilities via Go vulnerability database at `vuln.go.dev`. Call-graph analysis reports only **reachable** vulnerabilities.

**Note**: Database tracks Go standard library issues from Go 1.18 on. Third-party module vulnerabilities tracked regardless of Go version. Use Go 1.22+ for best results (better call graph analysis).

```bash
# Pin in the module (Go 1.24+)
go get -tool golang.org/x/vuln/cmd/govulncheck@latest

# Scan source code
go tool govulncheck ./...

# Scan a compiled binary
go tool govulncheck -mode=binary ./myapp
```

## Profile-Guided Optimization (PGO) _(Go 1.21+)_

PGO generally available since Go 1.21; 2-14% performance gains:

```bash
# 1. Build and run with CPU profiling
go test -cpuprofile=default.pgo -bench=. ./...

# 2. Place default.pgo in the main package directory
# 3. Rebuild — PGO is applied automatically
go build ./...
```

Go 1.22+ PGO devirtualizes more interface calls. Go 1.23+ cut PGO build time overhead to single digits.

## `go fix` and `go doc` changes _(Go 1.27+)_

`go fix` now applies more of `modernize` fixer suite automatically. Coverage changes from Go 1.26 to 1.27:

- **Added**: `atomictypes`, `embedlit`, `slicesbackward`, `unsafefuncs`
- **Removed**: `fmtappendf` (superseded by other fixers)
- **Renamed**: `waitgroup` → `waitgroupgo`

```bash
go fix ./...          # applies the enabled safe transformations
go tool fix help      # check exact fixer coverage for the installed toolchain
```

`go doc` accepts `package@version` to look up specific module version without changing `go.mod`; `-ex` lists executable examples:

```bash
go doc golang.org/x/tools/cmd/stringer@v0.30.0
go doc -ex net/http.Client
```

`go mod tidy` (modules with `go 1.27` or newer) auto-merges duplicate `require` blocks and enforces two-block layout (direct dependencies, then indirect), keeping existing comments.

`go test -json` output gained optional `OutputType` field (`"error"`, `"error-continue"`, `"frame"`) so consumers can tell test-output kinds apart programmatically.

`go tool trace -http` now binds to localhost by default. Pass `-http=0.0.0.0:6060` explicitly to expose trace viewer beyond local machine (e.g. tracing inside container or remote dev environment).

## AI-Driven Code Review in CI

Add AI agent as PR reviewer next to static analysis. With this skill plugin, agent loads relevant Go skills (`golang-security` for security, `golang-concurrency` for concurrency, `golang-error-handling` for error handling, etc.).

Ready-to-use GitHub Actions assets for Claude Code and GitHub Copilot: `samber/cc-skills-golang@golang-continuous-integration` skill.
