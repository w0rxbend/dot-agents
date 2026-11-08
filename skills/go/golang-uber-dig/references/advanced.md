# Advanced — uber-go/dig

Detail topics referenced from `SKILL.md`.

## Table of Contents

- [Decorate](#decorate)
- [Scopes](#scopes)
- [Optional Dependencies](#optional-dependencies)
- [Error Handling](#error-handling)
- [Visualization](#visualization)
- [Quick Reference](#quick-reference)
  - [Container](#container)
  - [Provide options](#provide-options)
  - [Container options](#container-options)
  - [Errors](#errors)

## Decorate

`Decorate` modifies value already provided in container. Decorator receives original instance, returns replacement. Common uses: enrich logger with context, wrap metrics scope with tags, swap real client for recording one in child scope.

```go
c.Decorate(func(log *zap.Logger) *zap.Logger {
    return log.Named("worker")
})
```

Decorators apply to scope where registered and to its descendants. Use them at scope or package wiring boundaries, not in main(), so changes stay local.

## Scopes

A `Scope` is child container that inherits parent's providers and can add or override its own. Scopes let request-, tenant- or module-level dependencies coexist with shared singletons:

```go
root := dig.New()
root.Provide(NewLogger)
root.Provide(NewDatabase)

requestScope := root.Scope("request")
requestScope.Provide(NewRequestContext)            // only visible inside requestScope
requestScope.Decorate(func(l *zap.Logger) *zap.Logger {
    return l.With(zap.String("scope", "request"))
})
```

By default, providers registered to scope are private to that scope and its children. Pass `dig.Export(true)` to `Provide` inside scope to make type visible from parent:

```go
requestScope.Provide(NewSharedCache, dig.Export(true))
```

## Optional Dependencies

`optional:"true"` lets consumer compile and run when provider missing. Use sparingly: optional dependencies hide configuration mistakes. Fit for genuinely optional features (tracing exporter, in-memory cache), not core services like database.

```go
type Params struct {
    dig.In

    Logger *zap.Logger
    Tracer trace.Tracer `optional:"true"`
}
```

## Error Handling

dig wraps constructor error with dependency path, showing _which_ graph edge failed:

```go
if err := c.Invoke(run); err != nil {
    // err describes the chain: "could not build *http.Server: ..."
}
```

Useful helpers:

- `errors.As(err, &dig.Error{})` — true if error originated inside dig
- `dig.RootCause(err)` — unwrap to original constructor error returned by user code
- `dig.IsCycleDetected(err)` — true if graph contains cycle (typically reported at first `Invoke` unless `DeferAcyclicVerification` set)
- `errors.As(err, &dig.PanicError{})` — with `RecoverFromPanics` enabled, panicking constructor surfaces as this typed error

## Visualization

dig can emit dependency graph in DOT format. Use when wiring gets too tangled to reason about by reading code:

```go
f, _ := os.Create("graph.dot")
_ = dig.Visualize(c, f)
// then: dot -Tpng graph.dot -o graph.png
```

`dig.VisualizeError(err)` highlights failed edges when `Invoke` returns error. Invaluable for debugging "missing type" failures in deep graphs.

## Quick Reference

### Container

| Function/Method | Purpose |
| --- | --- |
| `dig.New(opts...)` | Create root container |
| `c.Provide(ctor, opts...)` | Register constructor |
| `c.Invoke(fn, opts...)` | Run function with injected dependencies |
| `c.Decorate(fn, opts...)` | Modify previously-provided value within scope |
| `c.Scope(name, opts...)` | Create child scope (private providers by default) |
| `c.String()` | Human-readable text summary of providers (not DOT; use `dig.Visualize` for DOT) |

### Provide options

| Option | Purpose |
| --- | --- |
| `dig.Name("...")` | Disambiguate same-typed providers |
| `dig.Group("...")` | Add result to value group |
| `dig.As(new(I))` | Provide concrete value as one or more interfaces |
| `dig.Export(true)` | Make scope-level provider visible from root |
| `dig.FillProvideInfo(&info)` | Capture metadata for tooling |

### Container options

| Option | Purpose |
| --- | --- |
| `dig.DeferAcyclicVerification()` | Defer cycle check to first `Invoke` |
| `dig.RecoverFromPanics()` | Convert constructor panics into `dig.PanicError` |
| `dig.DryRun(true)` | Validate without invoking constructors |

### Errors

| Helper                              | Purpose                       |
| ----------------------------------- | ----------------------------- |
| `dig.RootCause(err)`                | Unwrap to user-returned error |
| `dig.IsCycleDetected(err)`          | True if graph has cycle       |
| `errors.As(err, &dig.PanicError{})` | Detect recovered panic        |
| `dig.Visualize(c, w, opts...)`      | Write graph in DOT format     |
