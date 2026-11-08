# Testing with uber-go/dig

dig containers cheap to create. Build fresh one per test, override what you need, drive system with `Invoke`.

## Table of Contents

- [Per-test container](#per-test-container)
- [Shared test wiring](#shared-test-wiring)
- [Validate the production graph in CI](#validate-the-production-graph-in-ci)
- [Detecting cycles before deploy](#detecting-cycles-before-deploy)
- [Asserting a constructor's error path](#asserting-a-constructors-error-path)
- [Recovering from constructor panics](#recovering-from-constructor-panics)

## Per-test container

```go
func TestUserService_Create(t *testing.T) {
    c := dig.New()

    fakeDB := &fakeDatabase{}
    require.NoError(t, c.Provide(func() Database { return fakeDB }))
    require.NoError(t, c.Provide(NewUserService))

    require.NoError(t, c.Invoke(func(s *UserService) {
        err := s.Create(context.Background(), "alice@example.com")
        require.NoError(t, err)
    }))

    require.Len(t, fakeDB.inserted, 1)
}
```

## Shared test wiring

For larger suites, factor common providers into helper:

```go
func newTestContainer(t *testing.T, overrides ...func(*dig.Container)) *dig.Container {
    t.Helper()
    c := dig.New()
    require.NoError(t, c.Provide(NewTestLogger))
    require.NoError(t, c.Provide(NewInMemoryCache))
    require.NoError(t, c.Provide(func() Database { return &fakeDatabase{} }))
    require.NoError(t, c.Provide(NewUserService))

    for _, override := range overrides {
        override(c)
    }
    return c
}

func TestUserService_NotFound(t *testing.T) {
    c := newTestContainer(t, func(c *dig.Container) {
        // Replace the default DB with one that returns sql.ErrNoRows.
        require.NoError(t, c.Decorate(func(db Database) Database {
            return &notFoundDB{Database: db}
        }))
    })

    require.NoError(t, c.Invoke(func(s *UserService) {
        _, err := s.Get(context.Background(), "missing")
        require.ErrorIs(t, err, ErrUserNotFound)
    }))
}
```

`Decorate` is cleanest way to swap dependency in tests.

## Validate the production graph in CI

```go
func TestProductionGraph(t *testing.T) {
    c := dig.New(dig.DryRun(true))

    // Replicate every Provide() from main()
    require.NoError(t, registerAll(c))

    // Invoke the same root the production binary does
    require.NoError(t, c.Invoke(func(*http.Server, *Worker, *MetricsExporter) {}))
}
```

`DryRun(true)` skips constructor execution; graph validated structurally. Catches missing-provider and type-mismatch errors without spinning up real DB connections.

## Detecting cycles before deploy

Cyclic graph fails at first `Invoke` (or at `Provide` time when `DeferAcyclicVerification` is off, which is default):

```go
func TestNoCycles(t *testing.T) {
    c := dig.New()
    require.NoError(t, registerAll(c))

    err := c.Invoke(func(*App) {})
    require.False(t, dig.IsCycleDetected(err), "cycle in dependency graph: %v", err)
}
```

## Asserting a constructor's error path

When constructor returns error, dig wraps it with dependency path. Assert original error with `dig.RootCause`:

```go
func TestDBProvider_BadDSN(t *testing.T) {
    c := dig.New()
    require.NoError(t, c.Provide(func() *Config {
        return &Config{DSN: "not a dsn"}
    }))
    require.NoError(t, c.Provide(NewDB))

    err := c.Invoke(func(*sql.DB) {})
    require.Error(t, err)
    require.ErrorContains(t, dig.RootCause(err), "invalid connection string")
}
```

## Recovering from constructor panics

Wrap constructors that may panic on misuse, so test reports typed error instead of crashing runner:

```go
c := dig.New(dig.RecoverFromPanics())

require.NoError(t, c.Provide(func() *App {
    panic("intentionally broken")
}))

err := c.Invoke(func(*App) {})

var pe dig.PanicError
require.True(t, errors.As(err, &pe))
require.Contains(t, pe.Error(), "intentionally broken")
```
