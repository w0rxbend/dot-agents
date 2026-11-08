# Diagnostic Tools Quick Reference

Validate slowdown root cause with these tools BEFORE applying any optimization. Do NOT use auto-fix flags (e.g. `--fix`). Coding agent interprets results and applies changes manually, with explanatory comments.

Per-tool details in dedicated reference files:

- [pprof Reference](./pprof.md) — profiling (CPU, heap, goroutine, mutex, block)
- [benchstat Reference](./benchstat.md) — statistical benchmark comparison
- [Trace Reference](./trace.md) — execution tracer
- [Compiler Analysis](./compiler-analysis.md) — escape analysis, inlining, SSA, assembly

## GC and Runtime Diagnostics

Set via environment variables. No recompile needed.

| Command | Use for |
| --- | --- |
| `GODEBUG=gctrace=1 ./app` | GC frequency, pause times, heap sizes, CPU%; one line per GC cycle |
| `GODEBUG=gcpacertrace=1 ./app` | Why GC triggers when it does: pacer decisions (trigger ratio, heap goal) |
| `GODEBUG=schedtrace=1000 ./app` | Load balancing, goroutine distribution across Ps; prints every 1000ms |
| `GODEBUG=schedtrace=1000,scheddetail=1 ./app` | Per-goroutine state detail on top of schedtrace |
| Heap/alloc profiles (`go tool pprof -alloc_objects`) | Allocation sites and object churn; use instead of removed/stale allocation trace flags |

→ See `samber/cc-skills-golang@golang-troubleshooting` skill for detailed GODEBUG usage and interpretation.

### Programmatic APIs

- **`runtime.ReadMemStats`** — heap size, NumGC, pause durations (PauseNs circular buffer), TotalAlloc (cumulative). For dashboards, alerting on heap growth.
- **`debug.ReadGCStats`** — GC-specific: pause percentiles, pause timeline, total pause duration. Narrower than ReadMemStats.
- **`runtime/metrics` (Go 1.16+)** — stable API, safe for concurrent reads, lower overhead than ReadMemStats. Keys: `/gc/cycles/total:gc-cycles`, `/gc/heap/allocs:bytes`, `/gc/pauses:seconds`, `/sched/latencies:seconds`, `/memory/classes/heap/released:bytes`.
- **`debug.FreeOSMemory()`** — forces GC + returns memory to OS. One-off use after large temporary allocations, not regular use. Let runtime manage this.
- **`expvar`** — stdlib metrics at `/debug/vars` as JSON. `import _ "expvar"` auto-registers. Lightweight, no dependencies. Feeds Netdata, Telegraf, or custom dashboards.

## Static Analysis

| Command | Use for |
| --- | --- |
| `fieldalignment ./...` | Detect suboptimal struct field ordering (padding waste). Do NOT use `-fix` flag. |
| `unsafe.Sizeof` / `Alignof` / `Offsetof` | Inspect struct memory layout at compile time. Compare before/after reordering to quantify savings. |
| `go vet ./...` | Suspicious constructs: printf format mismatches, unreachable code, unused results, suspicious shifts. |
| `staticcheck ./...` | Advanced linter: performance pitfalls (SA9003: empty branch, SA4006: unused value, SA1019: deprecated API). |
| `go test -race ./...` | Runtime data race detection. Also helps confirm false sharing. |

## Third-Party Profiling

| Tool | What it adds | When to use |
| --- | --- | --- |
| **fgprof** (`github.com/felixge/fgprof`) | Full goroutine profiler: on-CPU and off-CPU (I/O wait) time in one profile. Standard pprof CPU profiles only show on-CPU time. | pprof CPU profile shows low CPU% but high latency. |
| **Pyroscope / Parca** | Continuous profiling platforms: aggregate pprof profiles over time, compare across deployments, detect regressions. | Production performance monitoring, historical trends. → See `samber/cc-skills-golang@golang-observability` skill for setup. |
| **Linux perf** (`perf record -g ./app && perf report`) | Hardware performance counters: cache misses, branch mispredictions, TLB misses. Requires `perf_data_converter` for pprof format. | CPU microarchitecture-level analysis when pprof isn't granular enough. |
