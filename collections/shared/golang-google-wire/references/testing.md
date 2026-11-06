# Testing — google/wire

## Table of Contents

- [Unit Tests: Plain Constructor Injection](#unit-tests-plain-constructor-injection)
- [Test Injectors: Swapping Providers](#test-injectors-swapping-providers)
- [Passing Mocks as Injector Arguments](#passing-mocks-as-injector-arguments)
- [CI: Detecting Stale `wire_gen.go`](#ci-detecting-stale-wire_gengo)
- [Testing Interface Bindings](#testing-interface-bindings)

## Unit Tests: Plain Constructor Injection

Generated code has no wire dependency. Test constructors directly:

```go
func TestUserService_GetUser(t *testing.T) {
    mockStore := &MockUserStore{users: map[int64]*User{1: &User{ID: 1, Name: "Alice"}}}
    cache := newTestRedis(t)
    svc := service.NewUserService(mockStore, cache)

    u, err := svc.GetUser(context.Background(), 1)
    require.NoError(t, err)
    assert.Equal(t, "Alice", u.Name)
}
```

Pass mocks directly as constructor arguments. No wire, no container, no file to generate. Idiomatic approach for unit tests.

## Test Injectors: Swapping Providers

For integration or component tests needing full wired graph with selected dependencies replaced, create test-only injector in `_test.go` file.

```go
// app_test.go
//go:build wireinject

package main

import (
    "testing"
    "github.com/google/wire"
)

// TestSet replaces real infra with in-memory fakes
var TestSet = wire.NewSet(
    NewTestConfig,
    NewInMemoryUserStore,
    wire.Bind(new(repo.UserStore), new(*InMemoryUserStore)),
    NewTestRedis,
)

func InitTestApp(t *testing.T) (*App, func(), error) {
    wire.Build(TestSet, service.ServiceSet, NewApp)
    return nil, nil, nil
}
```

```go
// app_integration_test.go
//go:build !wireinject  // compiles when the wireinject tag is NOT set

package main

func TestApp_GetUser(t *testing.T) {
    app, cleanup, err := InitTestApp(t)
    require.NoError(t, err)
    defer cleanup()

    // test against the fully-wired app with fake dependencies
    u, err := app.GetUser(context.Background(), 1)
    require.NoError(t, err)
    assert.NotNil(t, u)
}
```

Run `wire ./...` to generate `wire_gen.go`. Test injector is included because `_test.go` file compiles as part of package during `go test`.

**Key pattern from upstream best practices:** Prefer test-only provider set over passing mocks as injector arguments (both work). Set approach keeps test injector composable.

## Passing Mocks as Injector Arguments

Alternative to test set: pass mock directly as injector parameter. Wire treats it as pre-built provider.

```go
//go:build wireinject

func InitTestApp(store repo.UserStore) (*App, func(), error) {
    wire.Build(config.ConfigSet, service.ServiceSet, NewApp)
    return nil, nil, nil
}

// Test
func TestApp(t *testing.T) {
    mock := &MockUserStore{}
    app, cleanup, err := InitTestApp(mock)
    require.NoError(t, err)
    defer cleanup()
    // ...
}
```

Use when replacing only one or two dependencies and full `TestSet` is overkill.

## CI: Detecting Stale `wire_gen.go`

If `wire_gen.go` is not regenerated after provider change, CI builds pass but graph is wrong. Enforce freshness in CI:

```bash
# Option 1: re-run wire and check for diffs
wire ./...
git diff --exit-code -- '**/wire_gen.go'
```

```yaml
# .github/workflows/ci.yml
- name: Check wire_gen.go is up-to-date
  run: |
    go install github.com/google/wire/cmd/wire@v0.7.0
    wire ./...
    git diff --exit-code -- '**/wire_gen.go'
```

```bash
# Option 2: use wire check (verifies graph without regenerating)
wire check ./...
```

`wire check` exits non-zero if graph is inconsistent but does **not** update `wire_gen.go`. Use for fast graph-validity check without modifying files.

## Testing Interface Bindings

Use `wire.Bind` in test sets to bind fake to same interface:

```go
// Fake implements the same interface as the real provider
type FakeMailer struct{ sent []string }
func (f *FakeMailer) Send(to, body string) error { f.sent = append(f.sent, to); return nil }

var TestMailerSet = wire.NewSet(
    NewFakeMailer,
    wire.Bind(new(notification.Mailer), new(*FakeMailer)),
)

var TestSet = wire.NewSet(
    TestMailerSet,
    realServiceSet,  // everything else is real
)
```

Keeps test injector narrow: only Mailer is faked; rest of graph is real.
