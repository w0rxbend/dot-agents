# Production Patterns

## Table of Contents

- [Stale-While-Revalidate](#stale-while-revalidate)
- [Sharding](#sharding)
- [Missing Key Caching (Negative Caching)](#missing-key-caching-negative-caching)
  - [Dedicated missing cache (recommended)](#dedicated-missing-cache-recommended)
  - [Shared missing cache](#shared-missing-cache)
  - [Manual missing key marking](#manual-missing-key-marking)
- [Loader Chains](#loader-chains)
- [Copy-on-Read / Copy-on-Write](#copy-on-read--copy-on-write)
- [Prometheus Monitoring](#prometheus-monitoring)
  - [Setup](#setup)
  - [Key PromQL Queries](#key-promql-queries)
- [Warm-Up on Startup](#warm-up-on-startup)
- [Graceful Shutdown](#graceful-shutdown)

## Stale-While-Revalidate

Serve stale data immediately, refresh in background. Two time thresholds:

1. **TTL** — after it, entries turn "stale" and trigger async background refresh via loaders
2. **Stale duration** — after TTL + stale, entries hard-expire and get removed

```go
refreshLoader := func(keys []string) (map[string]*Config, error) {
    return fetchConfigsFromDB(keys)
}

cache := hot.NewHotCache[string, *Config](hot.WTinyLFU, 1_000).
    WithTTL(5 * time.Minute).                              // stale after 5min
    WithRevalidation(1 * time.Minute, refreshLoader).       // hard-expire after 6min total
    WithRevalidationErrorPolicy(hot.KeepOnError).           // keep stale value if refresh fails
    WithJitter(0.1, 30*time.Second).                        // spread expirations
    WithJanitor().
    Build()
defer cache.StopJanitor()
```

**Timeline for entry set at T=0 with this config:**

- T=0 to T=5min: fresh — returned directly
- T=5min to T=6min: stale — returned immediately, background refresh triggered
- T>6min: expired — removed, next `Get()` blocks on loader

**Error policies:**

- `hot.KeepOnError` — if background refresh fails, keep stale value until hard expiry
- `hot.DropOnError` — if refresh fails, drop entry immediately

Use `KeepOnError` when stale data beats no data (config caches, product catalogs). Use `DropOnError` when correctness beats availability.

## Sharding

Split cache into N independent segments to cut lock contention under high concurrency:

```go
cache := hot.NewHotCache[string, *User](hot.WTinyLFU, 100_000).
    WithTTL(5 * time.Minute).
    WithSharding(16, func(key string) uint64 {
        h := fnv.New64a()
        h.Write([]byte(key))
        return h.Sum64()
    }).
    WithJanitor().
    Build()
defer cache.StopJanitor()
```

**Sizing guidance:**

- Use powers of 2 (4, 8, 16, 32) for optimal hash distribution
- Rule of thumb: shard count ~= number of CPU cores for high-contention workloads
- Each shard gets `capacity / shards` items
- Over-sharding (>64 shards) adds overhead without benefit

## Missing Key Caching (Negative Caching)

Stops repeated loader calls for keys that don't exist in source:

### Dedicated missing cache (recommended)

Own eviction algorithm and capacity, for fine-grained control:

```go
cache := hot.NewHotCache[string, *User](hot.WTinyLFU, 100_000).
    WithTTL(1 * time.Hour).
    WithMissingCache(hot.LFU, 10_000).  // separate LFU cache for missing keys
    WithLoaders(userLoader).
    WithJanitor().
    Build()
defer cache.StopJanitor()
```

### Shared missing cache

Missing entries live in main cache. Simpler, but consumes main cache capacity:

```go
cache := hot.NewHotCache[string, *User](hot.WTinyLFU, 100_000).
    WithTTL(1 * time.Hour).
    WithMissingSharedCache().
    WithLoaders(userLoader).
    WithJanitor().
    Build()
defer cache.StopJanitor()
```

### Manual missing key marking

```go
// Mark individual key as missing
cache.SetMissing("nonexistent-user")
cache.SetMissingWithTTL("temp-missing", 5*time.Minute)

// Batch mark missing
cache.SetMissingMany([]string{"user:404", "user:405"})
```

**Important:** `Keys()`, `Values()`, `All()` exclude missing entries and return only real values.

## Loader Chains

Multiple loaders run sequentially for L1/L2 cache patterns:

```go
redisLoader := func(keys []string) (map[string]*User, error) {
    return redis.MGet(ctx, keys...)
}

dbLoader := func(keys []string) (map[string]*User, error) {
    return db.GetUsersByIDs(ctx, keys)
}

cache := hot.NewHotCache[string, *User](hot.WTinyLFU, 10_000).
    WithTTL(5 * time.Minute).
    WithLoaders(redisLoader, dbLoader).  // Redis first, then DB for remaining
    WithJanitor().
    Build()
defer cache.StopJanitor()
```

**Chain behavior:**

- `redisLoader` called first with all missing keys
- `dbLoader` called only with keys NOT found by `redisLoader`
- If both return same key, `dbLoader`'s value wins (later overwrites earlier)
- Any error stops chain. Partial results from earlier loaders are discarded.

## Copy-on-Read / Copy-on-Write

Required for mutable cached values (pointers, slices, maps):

```go
cache := hot.NewHotCache[string, *User](hot.WTinyLFU, 10_000).
    WithTTL(5 * time.Minute).
    WithCopyOnRead(func(u *User) *User {
        copy := *u
        return &copy
    }).
    WithCopyOnWrite(func(u *User) *User {
        copy := *u
        return &copy
    }).
    WithJanitor().
    Build()
defer cache.StopJanitor()
```

- **CopyOnRead** — clones at retrieval: callers get independent copies, mutations don't affect cache
- **CopyOnWrite** — clones at storage: cache holds snapshot, external mutations to original don't corrupt cached value
- Use both when callers read and write concurrently. Use only one when mutation direction is known.

## Prometheus Monitoring

### Setup

```go
cache := hot.NewHotCache[string, *User](hot.WTinyLFU, 10_000).
    WithTTL(5 * time.Minute).
    WithPrometheusMetrics("user_cache").
    WithJanitor().
    Build()
defer cache.StopJanitor()

prometheus.MustRegister(cache)
```

### Key PromQL Queries

```promql
# Hit ratio (target: >80%)
rate(hot_cache_hit_count{cache="user_cache"}[5m]) /
rate(hot_cache_get_count{cache="user_cache"}[5m])

# Eviction rate (high = cache too small or TTL too short)
rate(hot_cache_eviction_count{cache="user_cache"}[5m])

# Cache size vs capacity
hot_cache_len{cache="user_cache"} / hot_cache_capacity{cache="user_cache"}
```

**Alerts to consider:**

- Hit rate below 70% for >5 minutes — cache may be undersized
- Eviction rate spikes — working set exceeds capacity
- Cache size near capacity — consider increasing capacity or reviewing TTLs

## Warm-Up on Startup

Pre-populate cache before serving traffic:

```go
cache := hot.NewHotCache[string, *User](hot.WTinyLFU, 10_000).
    WithTTL(1 * time.Hour).
    WithWarmUp(func() (map[string]*User, []string, error) {
        users, err := db.GetFrequentUsers(ctx)
        if err != nil {
            return nil, nil, err
        }
        missingKeys := []string{"deleted-user-1", "deleted-user-2"}
        return users, missingKeys, nil  // values + known missing keys + error
    }).
    WithJanitor().
    Build()
defer cache.StopJanitor()
```

Bound startup time with `WithWarmUpWithTimeout(30*time.Second, fn)`.

## Graceful Shutdown

Always stop janitor goroutine before exit (`defer cache.StopJanitor()`). With graceful shutdown orchestration, call `cache.StopJanitor()` in shutdown phase alongside other resource cleanup.
