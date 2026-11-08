# Sync Primitives Deep Dive

## Table of Contents

- [sync.Mutex](#syncmutex)
  - [Embedding Convention](#embedding-convention)
- [sync.RWMutex](#syncrwmutex)
- [sync/atomic](#syncatomic)
- [sync.Map](#syncmap)
- [sync.Pool](#syncpool)
- [sync.Once](#synconce)
- [sync.WaitGroup](#syncwaitgroup)
  - [Go 1.25+: `wg.Go`](#go-125-wggo)
  - [Go <1.25 fallback](#go-125-fallback)
- [golang.org/x/sync/singleflight](#golangorgxsyncsingleflight)
- [golang.org/x/sync/errgroup](#golangorgxsyncerrgroup)
  - [Bounded Concurrency with SetLimit](#bounded-concurrency-with-setlimit)

## sync.Mutex

Exclusive access to shared state. MUST hold lock as briefly as possible. NEVER hold mutex across I/O, network calls, or channel operations.

```go
type SafeCache struct {
    mu    sync.Mutex
    items map[string]string
}

func (c *SafeCache) Get(key string) (string, bool) {
    c.mu.Lock()
    defer c.mu.Unlock()
    v, ok := c.items[key]
    return v, ok
}

func (c *SafeCache) Set(key, value string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.items[key] = value
}
```

### Embedding Convention

Embed mutex as unexported field, directly above fields it protects:

```go
type Registry struct {
    mu      sync.Mutex // protects entries
    entries map[string]Entry
}
```

## sync.RWMutex

SHOULD be used when reads greatly outnumber writes. Multiple goroutines can hold `RLock` at once; `Lock` is exclusive.

```go
type Config struct {
    mu     sync.RWMutex
    values map[string]string
}

func (c *Config) Get(key string) string {
    c.mu.RLock()
    defer c.mu.RUnlock()
    return c.values[key]
}

func (c *Config) Set(key, value string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.values[key] = value
}
```

**Pitfall**: Do not upgrade RLock to Lock — deadlocks. Release RLock first, then acquire Lock.

## sync/atomic

Lock-free operations on simple values. SHOULD be preferred over Mutex for simple counters. Faster than mutex for low-contention counters and flags.

```go
// ✓ Good — atomic for a simple counter
var requestCount atomic.Int64

func handleRequest() {
    requestCount.Add(1)
}

func getCount() int64 {
    return requestCount.Load()
}
```

```go
// ✓ Good — atomic.Bool for a shutdown flag
var shuttingDown atomic.Bool

func shutdown() {
    shuttingDown.Store(true)
}

func isRunning() bool {
    return !shuttingDown.Load()
}
```

Go 1.19+ typed atomics (`atomic.Int64`, `atomic.Bool`, `atomic.Pointer[T]`): prefer over raw `atomic.AddInt64`/`atomic.LoadInt64`.

## sync.Map

SHOULD only be used for write-once/read-many patterns. Optimized for two cases: (1) keys written once, read many times, (2) goroutines read/write disjoint key sets. Otherwise plain `map` + `sync.RWMutex` is faster.

```go
var cache sync.Map

func Get(key string) (any, bool) {
    return cache.Load(key)
}

func Set(key string, value any) {
    cache.Store(key, value)
}

func GetOrSet(key string, compute func() any) any {
    if v, ok := cache.Load(key); ok {
        return v
    }
    v, _ := cache.LoadOrStore(key, compute())
    return v
}
```

**When NOT to use `sync.Map`**: you need iteration or length, or writes are frequent with heavily overlapping keys. Use `sync.RWMutex` + `map` instead.

## sync.Pool

Reuses temporary objects to cut GC pressure. MUST NOT store pointers to stack-allocated objects. Any GC cycle may reclaim pooled objects. Do not store persistent state.

```go
var bufPool = sync.Pool{
    New: func() any {
        return new(bytes.Buffer)
    },
}

func process(data []byte) string {
    buf := bufPool.Get().(*bytes.Buffer)
    defer func() {
        buf.Reset()
        bufPool.Put(buf)
    }()

    buf.Write(data)
    // ... transform ...
    return buf.String()
}
```

**Rules**:

- Always `Reset()` before `Put()` — returning dirty objects causes bugs
- Do not assume `Get()` object is zeroed — `New` func only runs if pool is empty
- Best for short-lived, frequently allocated objects (buffers, encoders, temporary structs)

## sync.Once

MUST be used for one-time initialization. Runs exactly once, regardless of how many goroutines call it concurrently. Thread-safe by design.

```go
type DBClient struct {
    initOnce  sync.Once
    closeOnce sync.Once
    conn      *sql.DB
}

func (c *DBClient) getConn() *sql.DB {
    c.initOnce.Do(func() {
        var err error
        c.conn, err = sql.Open("postgres", dsn)
        if err != nil {
            panic(fmt.Sprintf("db init: %v", err))
        }
    })
    return c.conn
}

func (c *DBClient) Close() error {
    var err error
    c.closeOnce.Do(func() {
        err = c.conn.Close()
    })
    return err
}
```

Go 1.21+ also has `sync.OnceFunc`, `sync.OnceValue`, `sync.OnceValues` for simpler cases:

```go
var loadConfig = sync.OnceValue(func() *Config {
    cfg, err := parseConfig("config.yaml")
    if err != nil {
        panic(err)
    }
    return cfg
})

// Usage: cfg := loadConfig()
```

## sync.WaitGroup

Use `sync.WaitGroup` when you only need to wait for goroutines to finish.

### Go 1.25+: `wg.Go`

`WaitGroup.Go` starts goroutine, adds it to group, removes it when function returns.

```go
func processAll(items []Item) {
    var wg sync.WaitGroup

    for _, item := range items {
        // Go 1.22+ loop variables are per-iteration when the module has `go 1.22+`.
        // Do not add `item := item` solely for closure capture in modern modules.
        wg.Go(func() {
            process(item)
        })
    }

    wg.Wait()
}
```

Rules:

- `WaitGroup.Go` is Go 1.25+, not Go 1.24.
- Function passed to `wg.Go` must not panic.
- `WaitGroup` does not propagate errors and does not cancel siblings.
- For first-error-wins, cancellation, concurrency limits, or returned values, use `golang.org/x/sync/errgroup`.

### Go <1.25 fallback

```go
func processAll(ctx context.Context, items []Item) {
    var wg sync.WaitGroup
    for _, item := range items {
        wg.Add(1) // Add BEFORE go
        go func(item Item) {
            defer wg.Done()
            process(ctx, item)
        }(item)
    }
    wg.Wait() // blocks until all goroutines finish
}
```

```go
// ✗ Bad — Add inside the goroutine (race: Wait may return before Add runs)
go func() {
    wg.Add(1)
    defer wg.Done()
    process(item)
}()
```

## golang.org/x/sync/singleflight

Deduplicates concurrent calls per key. When multiple goroutines request same resource at once, only one executes; rest wait and share result.

```go
var group singleflight.Group

func GetUser(ctx context.Context, id string) (*User, error) {
    v, err, _ := group.Do(id, func() (any, error) {
        // Only one goroutine executes this for a given id
        return db.QueryUser(ctx, id)
    })
    if err != nil {
        return nil, err
    }
    return v.(*User), nil
}
```

**Use cases**: cache stampede prevention, deduplicating expensive lookups (DB, API), rate-limited external service calls.

## golang.org/x/sync/errgroup

Goroutine group with error propagation. Returns first error from any goroutine. `WithContext` also cancels remaining goroutines on first error.

```go
func fetchAll(ctx context.Context, urls []string) ([]Response, error) {
    g, ctx := errgroup.WithContext(ctx) // cancel siblings on first error
    results := make([]Response, len(urls))

    for i, url := range urls {
        g.Go(func() error {
            resp, err := fetch(ctx, url)
            if err != nil {
                return fmt.Errorf("fetching %s: %w", url, err)
            }
            results[i] = resp // safe: each goroutine writes to its own index
            return nil
        })
    }

    if err := g.Wait(); err != nil {
        return nil, err
    }
    return results, nil
}
```

### Bounded Concurrency with SetLimit

SHOULD use `SetLimit` to bound concurrency and avoid unbounded goroutine spawning.

```go
g, ctx := errgroup.WithContext(ctx)
g.SetLimit(10) // at most 10 goroutines run concurrently

for _, task := range tasks {
    g.Go(func() error {
        return process(ctx, task)
    })
}
return g.Wait()
```

Replaces hand-rolled worker pools in most cases.

→ See `samber/cc-skills-golang@golang-concurrency` skill for high-level patterns and decision trees.
