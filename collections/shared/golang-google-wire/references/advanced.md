# Advanced — google/wire

Detail topics referenced from `SKILL.md`.

## Table of Contents

- [Cleanup Chains](#cleanup-chains)
- [Multiple Injectors in One Package](#multiple-injectors-in-one-package)
- [wire.NewSet Nesting Strategies](#wirenewset-nesting-strategies)
- [`wire:"-"` Exclusion Tag](#wire--exclusion-tag)
- [Common Codegen Errors](#common-codegen-errors)
- [Codegen Flags](#codegen-flags)
- [`panic(wire.Build(...))` Alternate Syntax](#panicwirebuild-alternate-syntax)

## Cleanup Chains

When provider returns `(T, func(), error)`, Wire adds cleanup to chain. Generated injector runs cleanups in **reverse construction order**: last-built dependant cleans up first, so dependants tear down before their dependencies.

```go
// Provider with cleanup
func NewDB(cfg *Config) (*sql.DB, func(), error) {
    db, err := sql.Open("postgres", string(cfg.DSN))
    if err != nil { return nil, nil, err }
    return db, func() { db.Close() }, nil
}

func NewCache(cfg *Config) (*redis.Client, func(), error) {
    c := redis.NewClient(&redis.Options{Addr: cfg.CacheAddr})
    return c, func() { c.Close() }, nil
}
```

Wire generates something like:

```go
func InitApp() (*App, func(), error) {
    cfg := NewConfig()
    db, dbCleanup, err := NewDB(cfg)
    if err != nil { return nil, nil, err }
    cache, cacheCleanup, err := NewCache(cfg)
    if err != nil {
        dbCleanup()  // already-built cleanups run on partial failure
        return nil, nil, err
    }
    app := NewApp(db, cache)
    return app, func() {
        cacheCleanup()  // reverse order
        dbCleanup()
    }, nil
}
```

**Caller pattern**: guard against nil cleanup on construction failure:

```go
app, cleanup, err := InitApp()
if err != nil { log.Fatal(err) }
defer cleanup()
```

Wire always returns non-nil cleanup function when construction succeeds. If construction fails midway, returned `cleanup` is nil. Guard before calling.

## Multiple Injectors in One Package

Package can contain multiple injector functions. Each must live in file with `//go:build wireinject`. All generated functions land in `wire_gen.go` in same package.

```go
//go:build wireinject

package main

// Production injector
func InitProdApp() (*App, func(), error) {
    wire.Build(ProdSet, NewApp)
    return nil, nil, nil
}

// Development injector with debug providers
func InitDevApp() (*App, func(), error) {
    wire.Build(DevSet, NewApp)
    return nil, nil, nil
}
```

Select at runtime with flag, or at build time with separate `//go:build prod` / `//go:build !prod` constraints on injector files.

## wire.NewSet Nesting Strategies

Sets can contain other sets, building hierarchy that mirrors package structure.

```go
// pkg/config/wire.go
var ConfigSet = wire.NewSet(NewConfig)

// pkg/infra/wire.go
var InfraSet = wire.NewSet(
    config.ConfigSet, // embed upstream set
    NewDB,
    NewCache,
)

// pkg/service/wire.go
var ServiceSet = wire.NewSet(
    NewUserService,
    wire.Bind(new(UserStore), new(*UserRepo)),
)

// wire.go (injector)
wire.Build(infra.InfraSet, service.ServiceSet, NewApp)
```

**Library set stability rules** (from upstream best practices):

- Safe: replace provider with one that has same or fewer inputs, in same release.
- Safe: introduce brand-new output type not previously provided.
- Breaking: add new required input to provider. Downstream injectors cannot satisfy it.
- Breaking: remove provided output type. Downstream injectors depending on it fail.
- Breaking: add type injector already provides. Wire reports duplicate.

## `wire:"-"` Exclusion Tag

Exclude struct field from `wire.Struct` injection by tagging it:

```go
type Server struct {
    Logger  *zap.Logger
    DB      *sql.DB
    mu      sync.Mutex   `wire:"-"` // unexported — auto-excluded
    Timeout time.Duration `wire:"-"` // exported but opt-out
}

wire.Struct(new(Server), "*") // injects Logger and DB; skips mu and Timeout
```

Unexported fields always skipped regardless of tag.

## Common Codegen Errors

| Error message | Root cause | Fix |
| --- | --- | --- |
| `no provider found for TYPE` | Dependency not provided by any set in `wire.Build` | Add missing provider or set |
| `multiple bindings for TYPE` | Two providers return same type | Use named types or remove duplicate |
| `argument N has no provider for TYPE` | Interface requested but no `wire.Bind` maps to it | Add `wire.Bind(new(Iface), new(*Impl))` to a set |
| `cycle detected` | A → B → A circular dependency | Break cycle by introducing interface or factory |
| `wire.Build used outside of injector function` | `wire.Build` called from non-injector function | Only call `wire.Build` inside functions with build tag |
| duplicate symbol / redeclared in this block | Injector file missing `//go:build wireinject` | Add build tag as first line |

## Codegen Flags

```bash
# Specify output file prefix (default: wire_gen)
wire -output_file_prefix=init gen ./cmd/server

# Apply build tags during generation
wire -tags=integration gen ./...

# Prepend a header file (e.g., license comment) to generated output
wire -header_file=hack/boilerplate.go.txt gen ./...
```

## `panic(wire.Build(...))` Alternate Syntax

Wire accepts dummy return or `panic` call as injector body. `panic` form avoids writing zero-value returns for complex types:

```go
// Preferred when return types are complex or error-prone to zero-initialize
func InitApp(ctx context.Context) (*App, func(), error) {
    panic(wire.Build(AppSet))
}
```

Wire detects both forms and replaces body during codegen. `panic` is never reached in compiled binary; only generated `wire_gen.go` version is compiled.
