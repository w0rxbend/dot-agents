# Viper WatchConfig and Hot Reload

## Table of Contents

- [Basic setup](#basic-setup)
- [The atomic-rename trap](#the-atomic-rename-trap)
- [Race-safe reload pattern](#race-safe-reload-pattern)
- [Debouncing rapid changes](#debouncing-rapid-changes)
- [Validating config before applying](#validating-config-before-applying)
- [Stopping the watcher](#stopping-the-watcher)

## Basic setup

```go
viper.WatchConfig()
viper.OnConfigChange(func(e fsnotify.Event) {
    log.Printf("config changed: %s (op: %s)", e.Name, e.Op)
    // re-read affected values and apply them
})
```

`WatchConfig` starts background goroutine watching config file via fsnotify. Call after `ReadInConfig`.

## The atomic-rename trap

Most editors (vim, neovim, many CI tools) save by writing new file and renaming it over old one. That replaces the inode fsnotify is watching: event may not fire, may fire as `Op: RENAME` instead of `Op: WRITE`, or may fire twice.

**Test hot reload with direct file writes, not editor saves:**

```go
// reliable in tests:
os.WriteFile("config.yaml", newContent, 0644)

// unreliable for testing:
// opening vim and :w — may trigger RENAME instead of WRITE
```

In production, less of an issue if config management tool (Kubernetes ConfigMap volume mount, Consul Template, etc.) is aware of inode behavior.

## Race-safe reload pattern

Reload runs in background goroutine. Synchronize any shared state updated in `OnConfigChange`:

```go
type Config struct {
    mu       sync.RWMutex
    LogLevel string `mapstructure:"log_level"`
    MaxConn  int    `mapstructure:"max_conn"`
}

var cfg Config

viper.OnConfigChange(func(e fsnotify.Event) {
    var newCfg Config
    if err := viper.Unmarshal(&newCfg); err != nil {
        log.Printf("error reloading config: %v", err)
        return  // keep old config on error
    }

    cfg.mu.Lock()
    cfg.LogLevel = newCfg.LogLevel
    cfg.MaxConn = newCfg.MaxConn
    cfg.mu.Unlock()

    log.Printf("config reloaded: log_level=%s", newCfg.LogLevel)
})
```

Reads use `appCfg.mu.RLock()`. Never read viper directly in hot paths during reload: gap between `OnConfigChange` firing and viper updating internal state is non-deterministic.

## Debouncing rapid changes

Some filesystems fire multiple events per save. Debounce to avoid repeated reloads:

```go
var reloadTimer *time.Timer
var reloadMu sync.Mutex

viper.OnConfigChange(func(e fsnotify.Event) {
    reloadMu.Lock()
    defer reloadMu.Unlock()
    if reloadTimer != nil {
        reloadTimer.Stop()
    }
    reloadTimer = time.AfterFunc(100*time.Millisecond, func() {
        applyNewConfig()
    })
})
```

## Validating config before applying

Always validate reloaded config before applying. Invalid config mid-reload should keep previous working config:

```go
viper.OnConfigChange(func(e fsnotify.Event) {
    var candidate Config
    if err := viper.Unmarshal(&candidate); err != nil {
        log.Printf("reload: invalid config, keeping previous: %v", err)
        return
    }
    if err := validate(candidate); err != nil {
        log.Printf("reload: validation failed, keeping previous: %v", err)
        return
    }
    applyConfig(candidate)
})
```

## Stopping the watcher

No documented way to stop `WatchConfig` once started. Match watcher lifetime to process lifetime. In tests, create new `viper.New()` instance per test: watcher is per-instance, garbage-collected with it.
