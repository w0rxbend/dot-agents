# CPU Optimization

## Table of Contents

- [Function Inlining](#function-inlining)
  - [Value receivers enable inlining](#value-receivers-enable-inlining)
- [Cache Locality](#cache-locality)
  - [Row-major traversal](#row-major-traversal)
  - [Contiguous 2D allocation](#contiguous-2d-allocation)
  - [Struct of Arrays (SoA) vs Array of Structs (AoS)](#struct-of-arrays-soa-vs-array-of-structs-aos)
  - [Pointer-heavy vs value-heavy data](#pointer-heavy-vs-value-heavy-data)
- [False Sharing](#false-sharing)
- [Instruction-Level Parallelism](#instruction-level-parallelism)
- [SIMD (Single Instruction, Multiple Data)](#simd-single-instruction-multiple-data)
  - [Handling CPU-specific instruction sets](#handling-cpu-specific-instruction-sets)
- [Tight Loops and the Scheduler](#tight-loops-and-the-scheduler)
- [Reflection and Type Assertions](#reflection-and-type-assertions)
- [Monotonic Time](#monotonic-time)

## Function Inlining

**Diagnose:** 1- `go tool pprof` (CPU profile) — small helper dominating cumulative CPU time is likely not inlined 2- `go build -gcflags="-m"` — grep hot-path functions for `"cannot inline"`; reason (e.g., `"function too complex"`, `"unhandled op"`) shows what to simplify

Go compiler inlines small functions, removing call overhead. Too-complex functions (loops, many statements, calls to non-inlineable functions) are not inlined — costly in tight loops called millions of times.

```go
// Bad — log call prevents inlining
func abs(x int) int {
    if x < 0 {
        log.Printf("negative: %d", x) // blocks inlining
        return -x
    }
    return x
}

// Good — simple enough to inline
func abs(x int) int {
    if x < 0 { return -x }
    return x
}
```

**Check inlining decisions:**

```bash
go build -gcflags="-m" ./... 2>&1 | grep "can inline"
go build -gcflags="-m" ./... 2>&1 | grep "inlining call"
```

Move side effects (logging, metrics) out of hot-path functions or guard them with conditionals.

### Value receivers enable inlining

Value receivers let compiler fully inline fluent method chains. Pointer receivers add indirection that blocks inlining:

```go
// Pointer receiver — indirection prevents inlining, constant overhead per call
func (c *config) WithTimeout(d time.Duration) *config { c.timeout = d; return c }

// Value receiver — fully inlined, -80% time in fluent chains
func (c config) WithTimeout(d time.Duration) config { c.timeout = d; return c }
```

## Cache Locality

**Diagnose:** 1- `go tool pprof` (CPU profile) — loops over slices/matrices taking disproportionate CPU; cache-miss-heavy code shows high `runtime.memmove` or flat time in simple index operations 2- `go test -bench` — compare row-first vs column-first traversal; expect 10-50x gap on large matrices purely from cache effects

CPUs fetch data in 64-byte cache lines. Sequential access far outpaces random access because prefetcher loads next cache line before code needs it.

### Row-major traversal

Go stores 2D arrays row-major. Column-first traversal jumps across memory, causing cache misses:

```go
// Bad — column-first, jumps across memory (~10M cache misses)
for col := 0; col < 1024; col++ {
    for row := 0; row < 1024; row++ {
        sum += matrix[row][col]
    }
}

// Good — row-first, sequential access (~125K cache misses)
for row := 0; row < 1024; row++ {
    for col := 0; col < 1024; col++ {
        sum += matrix[row][col]
    }
}
```

### Contiguous 2D allocation

Per-row allocation scatters data across heap:

```go
// Bad — N separate allocations, poor cache locality
matrix := make([][]float64, rows)
for i := range matrix { matrix[i] = make([]float64, cols) }

// Good — single contiguous allocation, cache-friendly
data := make([]float64, rows*cols)
matrix := make([][]float64, rows)
for i := range matrix { matrix[i] = data[i*cols : (i+1)*cols] }
```

### Struct of Arrays (SoA) vs Array of Structs (AoS)

Iterating one struct field, AoS wastes cache loading unused fields:

```go
// AoS — loading each Point (24 bytes) to read only x (8 bytes) = 66% cache waste
type Point struct { x, y, z float64 }
points := make([]Point, n)
for i := range points { sum += points[i].x }

// SoA — all x values contiguous, 100% cache utilization
type Points struct { xs, ys, zs []float64 }
for i := range ps.xs { sum += ps.xs[i] }
```

Use SoA when iterating subset of fields (physics, graphics, analytics). AoS fine when accessing all fields together or for small structs.

### Pointer-heavy vs value-heavy data

Index-based structures (nodes in contiguous array, referenced by index) beat pointer-based ones for cache locality:

```go
// Pointer-based tree — each node scattered in heap, random cache misses
type Node struct { value int; left, right *Node }

// Index-based tree — nodes in contiguous array, cache-friendly
type Tree struct { nodes []Node }
type Node struct { value int; left, right int } // indices into nodes
```

## False Sharing

**Diagnose:** 1- `go tool pprof` (CPU profile + mutex profile) — atomic operations or counter updates with unexpectedly high CPU; in mutex profile, contention on variables that shouldn't need locking 2- `go test -bench` — benchmark concurrent counter increments; if more goroutines make it _slower_ instead of faster, false sharing is likely

Goroutines updating variables on one 64-byte CPU cache line invalidate each other's core cache on every write, causing severe degradation:

```go
// Bad — a and b on same cache line, cores fight for it
type Counters struct { a, b int64 }

// Good — separate cache lines, no interference
type Counters struct {
    a int64    // 8 bytes
    _ [56]byte // 64 - 8 = 56 bytes padding
    b int64    // 8 bytes
}
```

Only apply cache-line padding when profiling confirms contention on concurrent counters/flags.

## Instruction-Level Parallelism

**Diagnose:** 1- `go tool pprof` (CPU profile) — tight arithmetic loops (sum, dot product) whose body dominates CPU are multi-accumulator candidates 2- `go test -bench` — compare single vs multi-accumulator versions; expect 2-4x when loop is truly CPU-bound with dependency chain

CPUs execute independent instructions simultaneously. Single accumulator forms dependency chain — each addition waits for previous one:

```go
// Bad — sequential dependency, CPU pipeline stalls
var total int64
for _, v := range data { total += v }

// Good — 4 independent accumulators, CPU pipelines all 4 in parallel
var s0, s1, s2, s3 int64
limit := len(data) - len(data)%4
for i := 0; i < limit; i += 4 {
    s0 += data[i]; s1 += data[i+1]; s2 += data[i+2]; s3 += data[i+3]
}
for i := limit; i < len(data); i++ { s0 += data[i] }
total := s0 + s1 + s2 + s3
```

Only use when profiling shows loop is a bottleneck.

## SIMD (Single Instruction, Multiple Data)

**Diagnose:** 1- `go tool pprof` (CPU profile) — confirm numeric inner loop consumes >20% of CPU; SIMD only helps CPU-bound numeric work, not allocation or I/O bottlenecks 2- `go test -bench` — record loop baseline ns/op as reference to validate SIMD gains 3- `go build -gcflags="-d=ssa/prove/debug=2"` — check if compiler already auto-vectorized loop; `"Proved"` bounds-check eliminations enable vectorization 4- `GOSSAFUNC=MyFunc go build` — SSA dump (`ssa.html`) shows whether compiler emits vector instructions for hot loop 5- `go tool objdump -s MyFunc ./binary` — verify final assembly has SIMD instructions (e.g., `VMOVAPD`, `VADDPD` on amd64), not scalar equivalents

Go 1.26+ includes experimental `simd/archsimd` package (requires `GOEXPERIMENT=simd` flag): low-level, architecture-specific SIMD intrinsics — amd64 with 128/256/512-bit vectors, and arm64/wasm at 128-bit as of Go 1.27. Go 1.27 also adds portable `simd` package (vector types like `Int8s`, `Float32s`) that works across architectures and falls back to scalar code without hardware support.

**Options for explicit SIMD in Go:**

- **Experimental `simd`/`simd/archsimd` (Go 1.26+, speculative)** — Direct SIMD intrinsics via vector types with CPU feature detection. Use with caution: both are experimental, in-progress APIs (`GOEXPERIMENT=simd`); package paths and type names may change before stabilization. Not covered by Go 1 compatibility guarantees. Never expose them in public APIs. Verify import path and API against your Go toolchain.

  ```go
  // Requires: GOEXPERIMENT=simd go build
  // WARNING: experimental API — package path and types may change
  import "simd/archsimd"

  v := archsimd.Int32x4{1, 2, 3, 4}
  ```

- **Let the compiler do it** — write simple, idiomatic loops on `[]float64`/`[]int32` slices. Check auto-vectorization: `go build -gcflags="-d=ssa/prove/debug=2" ./...`
- **`math/bits`** — `OnesCount`, `LeadingZeros`, `RotateLeft` map directly to hardware instructions (POPCNT, CLZ, ROL)
- **Hand-written assembly** — `.s` files with AVX2/NEON instructions for critical inner loops. `klauspost/compress` and `minio/sha256-simd` use this approach
- **Third-party vectorized libraries** — for common operations (hashing, compression, encoding), use libraries that already ship optimized SIMD instead of writing your own

### Handling CPU-specific instruction sets

Hand-written assembly unlocks higher performance but ties code to specific CPU features (AVX2, NEON, etc.). Three strategies:

**1. Compile on a production-similar machine**

Build on hardware matching deployment target, so compiler generates code for exact CPU instruction set available at runtime:

```bash
# Compiling on production hardware ensures optimal code generation
# for that specific CPU architecture and generation
ssh prod-server "cd /path && go build -o app ."
```

**Tradeoff:** Simplest, but requires production hardware access and different binaries per CPU type (Intel vs AMD vs Apple Silicon). Breaks CI/CD portability.

**2. Runtime CPU feature detection + multiple implementations**

Implement function once per CPU capability; dispatch at runtime:

```go
// dispatch.go
var sumImpl func([]int64) int64

func init() {
    if cpu.X86.HasAVX2 {
        sumImpl = sumAVX2
    } else {
        sumImpl = sumGeneric
    }
}

func Sum(data []int64) int64 {
    return sumImpl(data)
}

// sum_generic.go
func sumGeneric(data []int64) int64 {
    var total int64
    for _, v := range data { total += v }
    return total
}

// sum_amd64.s
TEXT ·sumAVX2(SB), NOSPLIT, $0-32
    // AVX2 implementation
    VMOVAPD (SI), Y0
    // ...
```

**Tradeoff:** Single binary works everywhere; one function-call dispatch overhead buys full CPU feature utilization. `encoding/base64` and `sha256` use this pattern.

**3. Compile-time selection with `//go:build` tags**

Use conditional compilation to generate different code per target at build time:

```go
// sum_fast.go
//go:build amd64 && !nosimd

package mylib

// AVX2 assembly via cgo or inline
func Sum(data []int64) int64 {
    return sumAVX2(data) // or calls to .s file
}

// sum_generic.go
//go:build !amd64 || nosimd

package mylib

func Sum(data []int64) int64 {
    var total int64
    for _, v := range data { total += v }
    return total
}
```

Build different binaries per target:

```bash
GOOS=linux GOARCH=amd64 go build -o app-avx2 .     # Uses sum_fast.go
GOOS=darwin GOARCH=arm64 go build -o app-neon .    # Uses sum_generic.go
go build -tags=nosimd -o app-safe .                # Fallback everywhere
```

**Tradeoff:** Zero runtime overhead; each binary fully optimized for its target. Requires shipping multiple binaries and coordinating which runs where.

**When SIMD is NOT worth pursuing:**

- Go lacks intrinsics, so SIMD requires assembly — high maintenance burden, platform-specific, harder to debug
- Auto-vectorization covers most common cases (simple numeric loops)

**Recommendation:**

- Start with auto-vectorization.
- For Go 1.27+, evaluate portable `simd` package for cross-architecture code, or `simd/archsimd` for architecture-specific tuning (amd64, arm64, wasm). Both are experimental.
- Move to runtime detection (option 2 above) if profiling shows bottleneck and code must run on heterogeneous hardware.
- Only use compile-time selection (option 3) if you control deployment environment and can test each per-binary variant.

Only invest in hand-written SIMD when profiling shows numeric inner loop consuming >20% of CPU and compiler isn't auto-vectorizing it.

## Tight Loops and the Scheduler

**Diagnose:** 1- `go tool pprof` (goroutine profile) — many goroutines stuck in `"runnable"` state (waiting for CPU) while one monopolizes execution 2- `go tool trace` — goroutine scheduling over time; long uninterrupted spans on one goroutine while others show scheduling gaps 3- `GODEBUG=schedtrace=1000` — prints scheduler state every second; unbalanced `runqueue` counts across P's mean one P is starved 4- `runtime/metrics` (`/sched/latencies:seconds`, Go 1.19+) — measures how long goroutines wait for CPU; high p99 latencies confirm starvation 5- Prometheus `rate(process_cpu_seconds_total[2m])` — if CPU hits GOMAXPROCS ceiling while other goroutines starve, tight loop is monopolizing P's

CPU-intensive tight loop without function calls may not yield to scheduler, starving other goroutines. Go 1.14+ added asynchronous preemption, but very tight loops of fully inlined operations can still cause issues:

```go
// Potential starvation — pure computation, no function calls
for { x = x*a + b }

// Safe — non-inlined call triggers preemption check
for item := range work {
    processBatch(item) // function call = preemption point
}
```

**When to use non-inlined calls for scheduling:**

- Loop runs long (hundreds of milliseconds or more of uninterrupted computation)
- Other goroutines wait to run (e.g., handling requests, I/O completion, channel operations)
- Loop contains only arithmetic or memory operations, no function calls

For short bursts (< 10ms), preemption isn't critical; inlining for CPU efficiency takes priority.

**Observable starvation symptoms:** high response latency, request timeouts, uneven request distribution, climbing goroutine counts.

**Preventing inlining with `//go:noinline`:** To keep a normally inlinable function (small, hot) from inlining so its call forces scheduler preemption checks, use `//go:noinline` compiler directive:

```go
//go:noinline
func processBatch(item WorkItem) {
    // CPU-intensive work here
    // This call site will NOT be inlined, even if the function is small
    // The function call itself becomes a preemption point for the scheduler
}

// In tight loop
for item := range work {
    processBatch(item) // Guaranteed preemption point
}
```

**Trade-off:** `//go:noinline` prevents inlining, which:

- **Pros:** Guarantees scheduler preemption checks; prevents goroutine starvation
- **Cons:** Adds function call overhead (~10-30 CPU cycles); reduces instruction-level parallelism (ILP) in caller

Only use `//go:noinline` if profiling shows scheduler preemption starvation actually blocks other goroutines.

## Reflection and Type Assertions

**Diagnose:** 1- `go tool pprof` (CPU profile) — `reflect.Value.*`, `reflect.DeepEqual` or `fmt.Sprintf` (uses reflect internally) in hot paths 2- `go test -bench` — compare reflection-based vs typed versions; expect 10-200x gap depending on reflection operation

- **`reflect` in hot paths** — 10-100x slower from type introspection and boxing. Replace with generics or typed code
- **`reflect.DeepEqual`** — 50-200x slower than typed comparisons. Use `slices.Equal`, `maps.Equal`, `bytes.Equal` (Go 1.21+)
- **Type switch vs repeated assertions** — type switch dispatches in one evaluation:

```go
// Bad — evaluates interface multiple times
if s, ok := v.(string); ok { return s }
if i, ok := v.(int); ok { return strconv.Itoa(i) }

// Good — single dispatch
switch v := v.(type) {
case string: return v
case int:    return strconv.Itoa(v)
}
```

## Monotonic Time

**Diagnose:** 1- `go test -bench` — compare `time.Since(start)` vs `time.Now().Sub(start)`; expect small but consistent gain from monotonic clock avoiding wall-clock syscall

`time.Since(start)` uses monotonic clock: immune to wall-clock adjustments (NTP, DST) and slightly faster:

```go
var appStart = time.Now() // captures monotonic time + wall-clock on program start

func myFunc() {
    // Compare durations, not wall-clock times
    elapsed := time.Since(appStart)
    if elapsed > threshold { ... }
}
```
