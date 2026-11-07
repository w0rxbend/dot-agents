# Performance Troubleshooting

## CPU Profiling

Capture 30s sample with pprof CPU profile (see [pprof.md](./pprof.md) for commands). Inspect with `top`, `web`, or `list funcName`.

**Common CPU hogs:**

1. JSON marshal/unmarshal in hot path — preallocate buffers, use faster libraries
2. Reflection in critical path
3. Unnecessary allocations — use sync.Pool
4. O(n^2) hidden in nested loops
5. Too many syscalls — batch operations

## Memory Profiling

Use pprof heap profile (see [pprof.md](./pprof.md)). Find growth by comparing heap snapshots over time with `go tool pprof -base heap1.prof heap2.prof`. Use escape analysis (see [diagnostic-tools.md](./diagnostic-tools.md)) to find unexpected heap allocations in hot paths.

**Common memory leaks:**

1. Unbounded cache without eviction
2. Growing slices in loops (forgot to reset)
3. Global maps never cleared
4. String concatenation in loops (use `strings.Builder`)
5. Large structs passed by value

## Lock Contention

**Symptoms:** CPU high but throughput low, latency rises with load, more cores don't help.

**Enable profiling in code:**

```go
runtime.SetMutexProfileFraction(1)
runtime.SetBlockProfileRate(1)
```

Then use pprof mutex and block profiles (see [pprof.md](./pprof.md)).

**Solutions:**

1. Reduce critical section — hold lock minimal time
2. Sharding — multiple locks for different data
3. `sync.Map` — for read-heavy workloads
4. `atomic` — for simple counters
5. `RWMutex` — when reads >> writes
