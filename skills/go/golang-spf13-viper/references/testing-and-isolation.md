# Viper Test Isolation

## Table of Contents

- [The global state problem](#the-global-state-problem)
- [viper.New() per test (correct approach)](#vipernew-per-test-correct-approach)
- [Injecting viper into your app](#injecting-viper-into-your-app)
- [Reading config files in tests](#reading-config-files-in-tests)
- [t.Setenv interactions](#tsetenv-interactions)
- [viper.Reset() — use with caution](#viperreset--use-with-caution)
- [Snapshot and restore pattern](#snapshot-and-restore-pattern)

## The global state problem

Top-level `viper.*` functions share one global `*viper.Viper` across all tests in process. Tests calling `viper.SetConfigFile`, `viper.Set`, or `viper.ReadInConfig` pollute it; test ordering turns flaky.

```go
// ✗ Bad — sets global state that affects later tests
func TestPortConfig(t *testing.T) {
    viper.SetDefault("port", 8080)
    viper.Set("port", 9090)
    assert.Equal(t, 9090, viper.GetInt("port"))
    // global viper now has port=9090 for all subsequent tests
}
```

## viper.New() per test (correct approach)

```go
func TestPortConfig(t *testing.T) {
    v := viper.New()
    v.SetDefault("port", 8080)
    v.Set("port", 9090)
    assert.Equal(t, 9090, v.GetInt("port"))
}

func TestDefaultPort(t *testing.T) {
    v := viper.New()
    v.SetDefault("port", 8080)
    assert.Equal(t, 8080, v.GetInt("port"))  // clean — not affected by TestPortConfig
}
```

## Injecting viper into your app

Test isolation requires app code to accept `*viper.Viper`, not call global functions directly:

```go
// ✓ Good — accepts a viper instance
type Server struct {
    cfg *viper.Viper
}

func NewServer(v *viper.Viper) *Server {
    return &Server{cfg: v}
}

func (s *Server) Port() int {
    return s.cfg.GetInt("port")
}

// In tests:
func TestServer(t *testing.T) {
    v := viper.New()
    v.Set("port", 9090)
    s := NewServer(v)
    assert.Equal(t, 9090, s.Port())
}

// In main:
func main() {
    // viper setup...
    s := NewServer(viper.GetViper())  // pass the global instance in production
}
```

## Reading config files in tests

```go
func TestReadConfig(t *testing.T) {
    v := viper.New()
    v.SetConfigFile("testdata/config.yaml")
    require.NoError(t, v.ReadInConfig())
    assert.Equal(t, "localhost", v.GetString("host"))
}
```

Keep config files in `testdata/`. Go test tooling sets working directory to package directory, so relative paths work reliably.

## t.Setenv interactions

`t.Setenv` sets env var for test duration, restores it on cleanup. Combined with `viper.New()` + `AutomaticEnv`, lets you test env binding without global pollution:

```go
func TestEnvBinding(t *testing.T) {
    t.Setenv("MYAPP_PORT", "9090")

    v := viper.New()
    v.SetEnvPrefix("MYAPP")
    v.AutomaticEnv()

    assert.Equal(t, 9090, v.GetInt("port"))
    // t.Setenv restores original MYAPP_PORT (or unsets it) after this test
}
```

## viper.Reset() — use with caution

`viper.Reset()` resets global instance to zero state. Rarely right fix:

- Affects all concurrent code also using global viper.
- Does not stop active `WatchConfig` goroutines.
- In `TestMain` or `t.Cleanup`, makes tests order-dependent.

Prefer `viper.New()` per test. Reserve `Reset()` for tools that call viper-based libraries and must restore state between runs.

## Snapshot and restore pattern

When you cannot refactor to inject `*viper.Viper` and must use global:

```go
func snapshotViper() map[string]interface{} {
    return viper.AllSettings()
}

func restoreViper(snapshot map[string]interface{}) {
    viper.Reset()
    for k, v := range snapshot {
        viper.Set(k, v)
    }
}

func TestWithGlobalViper(t *testing.T) {
    snapshot := snapshotViper()
    t.Cleanup(func() { restoreViper(snapshot) })

    viper.Set("port", 9090)
    // test code...
}
```

Fragile: `AllSettings()` captures only resolved values, not binding state (defaults, env bindings, etc.). Prefer injection.
