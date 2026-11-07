# Runtime Tuning

Tune after profiling; defaults suit most workloads.

## Table of Contents

- [Garbage Collector Tuning](#garbage-collector-tuning)
  - [GOGC (default: 100)](#gogc-default-100)
  - [GOMEMLIMIT (Go 1.19+)](#gomemlimit-go-119)
  - [Programmatic control](#programmatic-control)
  - [Ballast pattern (pre-Go 1.19)](#ballast-pattern-pre-go-119)
- [GC Profiling and Diagnostics](#gc-profiling-and-diagnostics)
  - [GODEBUG=gctrace=1](#godebuggctrace1)
  - [runtime.ReadMemStats](#runtimereadmemstats)
  - [GC pacing](#gc-pacing)
- [Allocation Rate Reduction](#allocation-rate-reduction)
- [GOMAXPROCS in Containers](#gomaxprocs-in-containers)
- [Profile-Guided Optimization (PGO)](#profile-guided-optimization-pgo)
- [Logging Overhead in Hot Paths](#logging-overhead-in-hot-paths)
- [Panic/Recover Cost](#panicrecover-cost)

## Garbage Collector Tuning

**Diagnose:** 1- `GODEBUG=gctrace=1` — one line per GC cycle; watch for high GC frequency (cycles/s), high CPU% (>5% means GC competes for CPU), heap growing faster than expected 2- `runtime.ReadMemStats` — inspect `Alloc`, `TotalAlloc`, `NumGC`, `PauseNs`; `Alloc` vs `Sys` shows memory GC reclaims vs memory OS allocated 3- `go tool trace` — shows GC stop-the-world pauses and GC assist stealing CPU from goroutines; look for long STW bars, frequent assist marks 4- `debug.ReadGCStats` — pause percentiles (p50, p95, p99); high p99 means large heap scans or too many pointers 5- `runtime/metrics` — GC stats for dashboards; monitor `/gc/cycles/total`, `/gc/heap/allocs`, `/gc/pauses` 6- `GODEBUG=gcpacertrace=1` — traces pacer decisions; explains GC triggering earlier or later than expected 7- Prometheus `rate(go_gc_duration_seconds_count[5m])` — production GC frequency; sustained >2 cycles/s suggests excessive allocation rate

### GOGC (default: 100)

Heap growth ratio that triggers next GC cycle. `GOGC=100`: GC runs when heap doubles since last collection. Higher values mean fewer GCs, more memory:

```bash
GOGC=50  ./myapp  # latency-sensitive: more frequent, shorter GC pauses
GOGC=200 ./myapp  # throughput-oriented: less frequent GC, more memory used
GOGC=off ./myapp  # disable GC entirely (testing only!)
```

### GOMEMLIMIT (Go 1.19+)

Soft memory limit; runtime collects more often to stay under it. Essential in containers: exceeding container limit triggers OOM kill:

```bash
# Container with 512MB limit: leave headroom for non-heap memory (goroutine stacks, OS buffers)
GOMEMLIMIT=450MiB ./myapp

# Container with 1GB limit
GOMEMLIMIT=900MiB ./myapp
```

Near limit, GC runs more aggressively regardless of GOGC.

### Programmatic control

```go
import "runtime/debug"

debug.SetGCPercent(200)                    // equivalent to GOGC=200
debug.SetMemoryLimit(450 * 1024 * 1024)   // 450 MiB soft limit
```

Use for dynamic tuning from observed workload, or when environment variables cannot be set.

### Ballast pattern (pre-Go 1.19)

Before GOMEMLIMIT, teams allocated large byte array at startup to inflate live heap and cut GC frequency:

```go
var ballast [1 << 30]byte // 1 GB — obsolete pattern
```

**GOMEMLIMIT is strictly better** — same benefit (fewer GC cycles) without wasting physical memory.

## GC Profiling and Diagnostics

### GODEBUG=gctrace=1

One line per GC cycle to stderr:

```bash
GODEBUG=gctrace=1 ./myapp 2>&1 | head -20
```

Sample output:

```
gc 5 @1.234s 2%: 0.012+12+0.9 ms clock, 0.25+8.9/20+18 ms cpu, 45->92->50 MB, 200 MB goal, 8 P
```

Key fields:

- `gc 5` — 5th GC cycle
- `@1.234s` — time since program start
- `2%` — total CPU time in GC
- `45->92->50 MB` — heap before, peak during collection, after
- `200 MB goal` — target heap size (from GOGC and GOMEMLIMIT)
- `8 P` — processor count

Watch for: GC frequency (too often = too many allocations), pause times (high = large heap or many pointers), CPU% (high = tune GOGC or reduce allocations).

### runtime.ReadMemStats

For dashboards and alerting:

```go
var m runtime.MemStats
runtime.ReadMemStats(&m)

fmt.Printf("Alloc: %d MB\n", m.Alloc/1024/1024)       // currently allocated
fmt.Printf("TotalAlloc: %d MB\n", m.TotalAlloc/1024/1024) // cumulative
fmt.Printf("Sys: %d MB\n", m.Sys/1024/1024)            // requested from OS
fmt.Printf("NumGC: %d\n", m.NumGC)                      // completed collections
fmt.Printf("LastPause: %d ms\n", m.PauseNs[(m.NumGC+255)%256]/1_000_000)
```

### GC pacing

Pacer predicts next collection start from:

1. **Live heap size** after last collection
2. **GOGC percentage** — allowed growth
3. **GOMEMLIMIT** — soft ceiling (if set)
4. **Current allocation rate** — how fast heap grows

Pacer starts early enough to finish before hitting target. Fast allocation means earlier starts.

## Allocation Rate Reduction

**Diagnose:** 1- `go tool pprof -alloc_objects` — ranks functions by allocation count; cutting top allocators gives biggest GC impact 2- `GODEBUG=gctrace=1` — compare GC frequency before and after; expect fewer cycles per second as allocation rate drops 3- Prometheus `rate(go_memstats_alloc_bytes_total[5m])` — production allocation rate trend; compare before/after deploy to catch regressions

Cutting allocations beats tuning GOGC: fixes root cause, not symptom:

- **Value types over pointer types** where possible — values stay on stack (no GC), pointers escape to heap
- **Pool frequently allocated objects** with `sync.Pool` (see [memory.md](./memory.md))
- **Preallocate slices and maps** — see `samber/cc-skills-golang@golang-data-structures` skill
- **Avoid interface boxing** in hot paths — use typed parameters or generics

## GOMAXPROCS in Containers

**Diagnose:** 1- `go tool pprof` (CPU profile) — high `runtime.schedule` or `runtime.findRunnable` overhead means too many P's competing for work or too few P's starving goroutines 2- `go tool trace` — check goroutines spread evenly across P's; uneven spread suggests GOMAXPROCS misconfigured for container 3- `GODEBUG=schedtrace=1000` — scheduler state every second; look for `runqueue` imbalances or idle P's while work is available 4- `runtime.GOMAXPROCS(0)` — current value; host CPU count (e.g., 64) instead of container limit (e.g., 2) means runtime is over-scheduling 5- Prometheus `rate(process_cpu_seconds_total[5m])` — production CPU cores used; consistently near GOMAXPROCS value means CPU-saturated

**Go 1.25+** detects container CPUs better, particularly with cgroup v2. Runtime sets `GOMAXPROCS` from:

- Logical CPUs on machine
- Process CPU affinity mask
- cgroup CPU quota limits (on Linux)

Container with 2 CPU cores on 64-core host, Go 1.25+, **cgroup v2**: `GOMAXPROCS` defaults correctly to 2. On **cgroup v1**, validate detected value at startup; consider `go.uber.org/automaxprocs`.

**For Go 1.24 and earlier**, use `go.uber.org/automaxprocs` for container CPU detection:

```go
// Pre-Go 1.25: explicit container-aware detection
import _ "go.uber.org/automaxprocs"

func main() {
    // GOMAXPROCS is now correctly set to container CPU limit
    startServer()
}
```

**Manual override** (if needed):

```bash
GOMAXPROCS=2 ./myapp
GODEBUG=updatemaxprocs=0 ./myapp  # disable dynamic updates (Go 1.25+)
```

**Known limitations (Go 1.25)**: cgroup v1 on certain systems (Oracle OCPUs) may not detect Kubernetes CPU limits properly. Set `GOMAXPROCS` manually there.

## Profile-Guided Optimization (PGO)

**Diagnose:** 1- `go tool pprof` (CPU profile) — collect representative production profile (30+ seconds); look for hot interface method calls and deep call chains, which PGO optimizes via devirtualization and inlining 2- `go test -bench` — benchmark before and after adding `default.pgo`; expect 2-7% gain on interface-heavy code, less on already-optimized paths

Go 1.21+ supports PGO: compiler uses production CPU profile to guide inlining and devirtualization.

**Workflow:**

1. Collect production CPU profile (30+ seconds of representative load):

   ```bash
   curl http://localhost:6060/debug/pprof/profile?seconds=60 > cpu.pprof
   ```

2. Place as `default.pgo` in main package directory:

   ```bash
   cp cpu.pprof ./cmd/myapp/default.pgo
   ```

3. Build — `go build` auto-detects `default.pgo`:

   ```bash
   go build ./cmd/myapp
   ```

**What the compiler optimizes:**

- **Inlining** — hot function calls inlined more aggressively
- **Devirtualization** — interface method calls likely hitting specific types become direct calls

**Helps most:** many interface calls, hot inlining opportunities, deep call stacks. **Helps least:** already-optimized code, memory-bound workloads.

Rebuild profiles after significant code changes; stale profiles can mislead compiler.

## Logging Overhead in Hot Paths

**Diagnose:** 1- `go tool pprof` (CPU profile) — `fmt.Sprintf`, `log.Printf` or `slog.(*Logger).log` in hot paths means log formatting burns CPU even when level filters message 2- `go build -gcflags="-m"` — check log arguments escaping to heap; expect `"moved to heap"` for arguments boxed into `any` interface by logging functions 3- `go test -bench -benchmem` — benchmark logging enabled vs disabled; if allocs/op doesn't change, logger allocates even when level is off

```go
// Bad — fmt.Sprintf runs BEFORE the logger checks the level
logger.Debug(fmt.Sprintf("processing item %d with data %v", item.ID, item.Data))

// Good — slog defers formatting until level check passes (Go 1.21+)
slog.Debug("processing item", slog.Int("id", item.ID), slog.Any("data", item.Data))

// Best — LogAttrs: zero allocations when level is disabled
slog.LogAttrs(ctx, slog.LevelDebug, "processing item",
    slog.Int("id", item.ID))
```

In hot paths even `slog.Any` can allocate. Prefer typed attributes: `slog.Int`, `slog.String`, `slog.Bool`.

## Panic/Recover Cost

**Diagnose:** 1- `go tool pprof` (CPU profile) — `runtime.gopanic` or `runtime.gorecover` in hot paths means panic/recover used for control flow 2- `go test -bench` — benchmark panic/recover vs error-return versions; expect 10-100x overhead from stack unwinding and defer execution

`panic` unwinds the stack, running all deferred functions up the call stack; `recover` catches it, but unwinding itself is expensive. Never use panic/recover for control flow:

```go
// Bad — panic overhead for a normal condition
defer func() { recover() }()
v, _ := strconv.Atoi(s) // relies on panic for invalid input

// Good — explicit error check, no panic overhead
v, err := strconv.Atoi(s)
if err != nil { continue }
```

Panic only for truly unrecoverable situations (programmer errors, corrupted state). Always convert panics to errors at package boundaries.
