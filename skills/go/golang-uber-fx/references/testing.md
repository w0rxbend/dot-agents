# Testing with uber-go/fx

`go.uber.org/fx/fxtest` integrates fx applications with `*testing.T`. Errors fail test instead of crashing process. Lifecycle teardown registers automatically.

## Table of Contents

- [Pulling a value out of the graph with `fx.Populate`](#pulling-a-value-out-of-the-graph-with-fxpopulate)
- [`fx.Replace` to swap a real dependency for a fake](#fxreplace-to-swap-a-real-dependency-for-a-fake)
- [Standalone lifecycle for a unit test](#standalone-lifecycle-for-a-unit-test)
- [Asserting wire-time errors](#asserting-wire-time-errors)
- [Validating the production graph in CI](#validating-the-production-graph-in-ci)
- [Test logger that captures fx events](#test-logger-that-captures-fx-events)
- [Testing a lifecycle hook in isolation](#testing-a-lifecycle-hook-in-isolation)

## Pulling a value out of the graph with `fx.Populate`

```go
func TestUserService_Create(t *testing.T) {
    var svc *UserService

    app := fxtest.New(t,
        fx.Provide(
            func() Database { return &fakeDatabase{} },
            NewUserService,
        ),
        fx.Populate(&svc),
    )
    defer app.RequireStop()
    app.RequireStart()

    require.NoError(t, svc.Create(context.Background(), "alice@example.com"))
}
```

`fx.Populate(&svc)` fills `svc` with value graph would resolve. Replaces ad-hoc `fx.Invoke(func(s *UserService) { svc = s })` patterns.

## `fx.Replace` to swap a real dependency for a fake

```go
func TestServer_HandlesDBError(t *testing.T) {
    var srv *http.Server
    fakeDB := &erroringDatabase{}

    app := fxtest.New(t,
        ProductionModule,                                 // the real wiring
        fx.Replace(fx.Annotate(fakeDB, fx.As(new(Database)))),
        fx.Populate(&srv),
    )
    defer app.RequireStop()
    app.RequireStart()

    // Drive the server with a fake DB
    rec := httptest.NewRecorder()
    req := httptest.NewRequest(http.MethodGet, "/users", nil)
    srv.Handler.ServeHTTP(rec, req)
    require.Equal(t, http.StatusInternalServerError, rec.Code)
}
```

`fx.Replace` works even when original provider is buried inside module. Overrides resolved type without rewriting module.

## Standalone lifecycle for a unit test

`fxtest.NewLifecycle(t)` gives `fx.Lifecycle` outside `fx.New` machinery. Use to test single constructor that registers hooks:

```go
func TestWorker_StartStop(t *testing.T) {
    lc := fxtest.NewLifecycle(t)

    worker := NewWorker(lc, zaptest.NewLogger(t))
    require.NotNil(t, worker)

    lc.RequireStart() // runs OnStart hooks
    require.True(t, worker.IsRunning())

    lc.RequireStop()  // runs OnStop hooks
    require.False(t, worker.IsRunning())
}
```

## Asserting wire-time errors

```go
func TestWiring_MissingDependency(t *testing.T) {
    app := fx.New(
        fx.Provide(NewServer), // depends on *sql.DB which is not provided
        fx.NopLogger,
    )
    require.Error(t, app.Err())
    require.Contains(t, app.Err().Error(), "missing type: *sql.DB")
}
```

Use `fx.New` (not `fxtest.New`) when you _expect_ wiring to fail. `fxtest.New` would call `t.Fatal`.

## Validating the production graph in CI

```go
func TestProductionGraph(t *testing.T) {
    app := fx.New(
        ProductionOptions(), // every fx.Provide / fx.Module the binary uses
        fx.NopLogger,
    )
    require.NoError(t, app.Err())
}
```

`fx.New` validates type graph without starting. Test fails before deploy on any missing-provider, cycle or annotation mismatch.

## Test logger that captures fx events

To assert on lifecycle behavior, route fx events into in-memory observer:

```go
// go.uber.org/zap/zaptest/observer
core, recorded := observer.New(zap.InfoLevel)
log := zap.New(core)

app := fxtest.New(t,
    fx.WithLogger(func() fxevent.Logger {
        return &fxevent.ZapLogger{Logger: log}
    }),
    fx.Provide(NewWorker),
    fx.Invoke(func(*Worker) {}),
)
defer app.RequireStop()
app.RequireStart()

require.NotEmpty(t, recorded.FilterMessage("OnStart hook executed").All())
```

## Testing a lifecycle hook in isolation

If constructor returns value _and_ registers hook, test both halves:

```go
func TestNewServer_OnStartFailsBindError(t *testing.T) {
    // Bind a port so :0 is unavailable... no, simpler: pre-bind and pass that addr
    listener, err := net.Listen("tcp", "127.0.0.1:0")
    require.NoError(t, err)
    defer listener.Close()
    addr := listener.Addr().String()

    cfg := &Config{Addr: addr}
    lc := fxtest.NewLifecycle(t)

    NewHTTPServer(lc, zaptest.NewLogger(t), cfg)

    // Use Start directly (not RequireStart) so we can assert the error.
    require.Error(t, lc.Start(context.Background()))
}
```
