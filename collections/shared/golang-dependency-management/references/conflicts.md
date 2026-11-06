# Dependency Conflicts & Resolution

## Diagnosing Conflicts

```bash
# See why a module is in your build
go mod why -m github.com/some/module

# See which version is selected
go list -m github.com/some/module

# See the full requirement graph
go mod graph

# List all modules in the build
go list -m all
```

## Resolution Strategies

**Force specific version** (when two deps require incompatible versions):

```bash
go mod edit -replace=example.com/pkg@v1.2.0=example.com/pkg@v1.3.1
```

```go
// go.mod
replace example.com/pkg v1.2.0 => example.com/pkg v1.3.1
```

**Use local fork** (for debugging or patching):

```go
replace example.com/pkg => ../my-local-fork
```

**Block problematic version**:

```bash
go mod edit -exclude=example.com/pkg@v1.3.0
```

Excluding version redirects any requirement on it to next higher available version.

**Force upgrade transitive dependency**:

```bash
go get github.com/transitive/dep@v1.5.0
```

Adds explicit requirement to your `go.mod`, overriding what transitive chain would select via MVS.

## Resolution Workflow

1. Run `go mod graph` and `go mod why -m <module>` to trace dependency chain
2. Find which direct dependency pulls in conflicting version
3. Try upgrading that direct dependency first: `go get github.com/direct/dep@latest`
4. If that fails, use `replace` or `exclude` as temporary fix
5. Run `go mod tidy` to clean up
6. Verify with `go build ./...` and `go test ./...`

**Important**: `replace` and `exclude` directives take effect only in **main module's** `go.mod`. Go ignores them when your module is a dependency. Remove `replace` directives before publishing library.

## Retract (For Module Authors)

Mark versions broken or accidentally published:

```go
// go.mod
retract v1.0.0         // Contains critical bug in auth
retract [v1.1.0, v1.2.0] // Range of broken versions
```

Retracted versions stay downloadable, but `go get` does not select them by default and `go list -m -u` warns about them.
