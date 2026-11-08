# Go Development Tools

## Debugging

**Delve** (<https://github.com/go-delve/delve>) Source-level debugger for Go programs.

## Linting & Code Quality

**golangci-lint** (<https://github.com/golangci/golangci-lint>) Fast Go linters runner. Runs many linters in parallel, highly configurable. Industry standard for Go code quality.

## Testing

**gotest** (standard library - go test) Built-in Go testing command. Runs tests, coverage reports, benchmarks.

**cover** (golang.org/x/tools/cmd/cover) Coverage analysis for Go tests. Generates and visualizes coverage reports.

**benchstat** (golang.org/x/perf/cmd/benchstat) Compares benchmark results statistically to judge performance significance.

**goleak** (<https://github.com/uber-go/goleak>) Goroutine leak detector for Go tests. Verifies tests do not leak goroutines between runs.

## Dependency Management

**go-mod-outdated** (<https://github.com/psampaz/go-mod-outdated>) Finds outdated dependencies in go.mod.

**goweight** (<https://github.com/jondot/goweight>) Measures package dependency weight. Spots heavy dependencies and transitive bloat.
