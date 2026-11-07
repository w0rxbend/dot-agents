# Execution Trace Reference

`go tool trace` shows what pprof cannot: **scheduling delays**, GC stop-the-world phases, goroutine state transitions, and why goroutines are **not** running. pprof samples on-CPU work; trace records every state transition at nanosecond precision.

Use execution tracer when:

- pprof shows low CPU% but high latency (goroutines waiting, not working)
- GC pauses suspected of causing tail latency spikes
- Goroutine scheduling and contention need explaining
- Wall-clock timeline of concurrent operations needed

## Generating Traces

Benchmarks and tests: add `-trace=trace.out` to `go test` (see [workflows](#full-capture-to-analysis-workflows) 1 and 3).

### From running service

Requires `import _ "net/http/pprof"`:

```bash
# Capture 5 seconds of trace data (adjust duration as needed)
curl -o trace.out http://localhost:6060/debug/pprof/trace?seconds=5
go tool trace trace.out
```

**Warning:** traces generate MB/s. Keep captures short (5-10 seconds typical). Longer traces are unwieldy, slow to parse, may use significant memory when opened.

### From code (programmatic)

```go
import "runtime/trace"

// Start tracing only when needed
f, _ := os.Create("trace.out")
trace.Start(f)

doExpensiveWork()

trace.Stop()
f.Close()
```

## Full Command Reference

### Opening traces

```bash
# Open trace in web browser (default — starts HTTP server, opens browser)
go tool trace trace.out

# Open on a specific port
go tool trace -http=:8080 trace.out

# Remote host: UI has no auth and exposes stacks, so keep it on localhost and tunnel
go tool trace -http=localhost:8080 trace.out   # on remote host
ssh -L 8080:localhost:8080 user@remote-host    # locally, then browse localhost:8080
```

### Extracting pprof profiles from traces

`go tool trace` converts trace data into pprof-compatible profiles. Capture with tracer (nanosecond events), analyze with pprof (statistical aggregation with `top`, `list`, `peek`):

```bash
# Network blocking profile — where goroutines wait on network I/O
go tool trace -pprof=net trace.out > net.prof
go tool pprof -top net.prof

# Synchronization blocking profile — mutexes, channels, wait groups
go tool trace -pprof=sync trace.out > sync.prof
go tool pprof -top sync.prof

# Syscall blocking profile — system calls that block goroutines
go tool trace -pprof=syscall trace.out > syscall.prof
go tool pprof -top syscall.prof

# Scheduler latency profile — time between becoming runnable and actually running
go tool trace -pprof=sched trace.out > sched.prof
go tool pprof -top sched.prof
```

### Full capture-to-analysis workflows

```bash
# Workflow 1: benchmark trace — capture, view, extract blocking profile
go test -bench=BenchmarkParse -trace=trace.out ./pkg/parser
go tool trace trace.out                                         # visual timeline
go tool trace -pprof=sync trace.out > sync.prof                 # extract sync blocking
go tool pprof -top -cum sync.prof                               # find worst sync blockers
go tool pprof -list=processOrder sync.prof                      # annotated source

# Workflow 2: production trace — capture from running service, analyze scheduling
curl -o trace.out http://localhost:6060/debug/pprof/trace?seconds=5
go tool trace trace.out                                         # visual timeline
go tool trace -pprof=sched trace.out > sched.prof               # extract scheduling latency
go tool pprof -top sched.prof                                   # goroutines with worst scheduling delay
go tool pprof -svg sched.prof > sched.svg                       # graph of scheduling bottlenecks

# Workflow 3: test trace — capture during test run
go test -trace=trace.out -run=TestSlowIntegration ./pkg/api
go tool trace trace.out                                         # visual timeline
go tool trace -pprof=net trace.out > net.prof                   # extract network blocking
go tool pprof -top net.prof                                     # find network wait sites
```

### HTTP endpoints served by the web UI

HTTP server started by `go tool trace trace.out` exposes these pages:

| Endpoint | What it shows |
| --- | --- |
| `/` | Index with links to all views |
| `/trace` | Interactive timeline viewer (Chrome trace viewer), main visualization |
| `/goroutines` | Goroutine analysis: summary of all goroutine types, counts, execution stats |
| `/goroutine/<id>` | One goroutine's full lifecycle timeline |

## Web UI

### Main views

Web UI (opened by `go tool trace trace.out`) shows timeline. Each horizontal lane is a processor (P), goroutine, or system event:

- **Trace viewer** (`/trace`) — interactive timeline with:
  - **P lanes** — one per logical processor (GOMAXPROCS): which goroutine runs on each P at each moment
  - **Goroutine lanes** — each goroutine's lifecycle: created → runnable → running → waiting → running → …
  - **GC events** — mark phases, sweep, STW pauses as colored bands across all P lanes
  - **System events** — syscalls, network I/O, timer events
  - **User annotations** — tasks, regions, log messages from `runtime/trace` API

- **Goroutine analysis** (`/goroutines`) — summary table:
  - Groups goroutines by creation stack trace (type)
  - Shows count and totals for execution time, scheduling wait, blocking time
  - Click type for per-goroutine statistics
  - Click goroutine for its timeline

### Navigating the trace viewer

Trace viewer uses Chrome tracing UI (also used by Chrome DevTools):

| Key/Action | Effect |
| --- | --- |
| `W` / scroll up | Zoom in (time axis) |
| `S` / scroll down | Zoom out (time axis) |
| `A` | Pan left |
| `D` | Pan right |
| Click on event | Details panel at bottom: goroutine ID, duration, stack trace |
| `Shift+click` | Select time range, highlighting all events in it |
| `M` | Mark current selection |
| `/` | Search events by name |
| `?` | Show keyboard shortcuts |

### Reading the timeline

**Color coding:**

- **Green bars** on P lanes = goroutine actively executing
- **Blue bars** = syscall (goroutine pinned to OS thread)
- **Orange/yellow marks** = scheduling events (goroutine becoming runnable)
- **Red bands** across all P lanes = GC stop-the-world pause
- **Light blue bands** = GC concurrent mark phase
- **Purple** = user-defined regions (from `trace.WithRegion`)

**Gaps in P lanes** = processor idle (no runnable goroutines, or goroutines blocked). Many idle gaps with pending runnable goroutines suggest scheduling contention.

## What to Look For

### Goroutine states

Trace timeline color-codes goroutine states:

| Color | State | Meaning | What it indicates |
| --- | --- | --- | --- |
| **Green** | Running | Executing on a P | Normal: useful work |
| **Yellow/Orange** | Runnable | Ready, waiting for a P | CPU saturation: too many runnable goroutines for too few processors |
| **Red/Pink** | Waiting | Blocked on I/O, channel, mutex, sleep, select | I/O-bound or contention: check what it waits on |
| **Blue** | GC assist | Drafted by GC to help mark/sweep | GC pressure: allocations force goroutines to help collector |

### GC phases

- **Mark assist** — goroutines drafted to help GC scan heap. Show as gaps in application goroutine execution. Runtime makes goroutines assist in proportion to allocation rate, so heavy allocators pay more.
- **STW (stop-the-world)** — brief phases with all goroutines stopped (mark setup, mark termination). Cause latency spikes, seen as vertical bands across all lanes.
- **Sweep** — concurrent sweep of unreachable objects. Usually cheap, but can accumulate if heap is large.

**Diagnosing GC issues from traces:**

- Frequent GC cycles with long mark assist = too many allocations (reduce allocation rate)
- Long STW phases = too many pointers to scan (reduce pointer density)
- GC cycles clustering after specific operations = those operations allocate heavily

### Scheduling latency

Time from goroutine becoming **runnable** to **running**. High scheduling latency means:

- Too many goroutines competing for GOMAXPROCS processors
- OS scheduling interference (noisy neighbors, CPU throttling)
- Goroutines pinned to busy threads by cgo or long syscalls

**What to look for:**

- Yellow (runnable) gaps before green (running) segments. Longer gap means higher scheduling latency
- Many goroutines runnable at once: CPU saturation
- Uneven load across Ps (one overloaded, others idle): work imbalance

### Network/sync blocking

- **Long red/pink periods** on a goroutine = blocked waiting. Click block event to see cause (channel receive, mutex lock, network read, etc.)
- **Many goroutines blocked on the same channel or mutex** = serialization bottleneck; all work funnels through one point.
- **Goroutines blocked on network I/O** = external dependency latency. Bottleneck is upstream, not in Go code. Use `-pprof=net` for pprof profile of network wait locations.

### Goroutine creation and destruction

Trace shows goroutine lifecycle events. Look for:

- **Goroutines created in a loop without bound** = potential goroutine leak
- **Goroutines that are created but never finish** = leak; they accumulate over time
- **Very short-lived goroutines created repeatedly** = goroutine creation/scheduling overhead (consider batching or worker pools)

## Custom Annotations

### Tasks

Task: logical operation, possibly spanning multiple goroutines:

```go
import "runtime/trace"

func processOrder(ctx context.Context, order Order) error {
    ctx, task := trace.NewTask(ctx, "processOrder")
    defer task.End()

    // All trace events in this context are grouped under the task
    validate(ctx, order)
    charge(ctx, order)
    fulfill(ctx, order)
    return nil
}
```

Tasks show as named groups in timeline. Trace view can filter to one task's events.

### Regions

Region: phase within task or goroutine:

```go
func validate(ctx context.Context, order Order) {
    trace.WithRegion(ctx, "validateAddress", func() {
        // this block is annotated as a region
        validateAddress(order.Address)
    })

    trace.WithRegion(ctx, "validatePayment", func() {
        validatePayment(order.Payment)
    })
}
```

Regions show as labeled spans on goroutine timeline, revealing which phase takes most wall-clock time.

### Log messages

Add point-in-time log messages:

```go
trace.Log(ctx, "orderID", order.ID)
trace.Log(ctx, "status", "payment_verified")
```

Logs show as timeline markers for correlating trace events with specific data.

### When to use annotations

- **Always** in server request handlers — wrap each request in task
- **Performance-critical paths** — add regions to phases to measure their wall-clock time
- **Debugging intermittent latency** — add logs at key decision points to see what happened in slow trace

Annotations cost negligible overhead when tracing is disabled (flag check, immediate return).

## Flight Recorder (Go 1.25+)

Solves key problem of execution traces in long-running services: once problem occurs (timeout, failed health check), calling `trace.Start()` is too late. Flight recorder keeps circular in-memory buffer of recent trace data. Snapshot it to disk when something goes wrong.

### Setup

```go
import "runtime/trace"

fr := trace.NewFlightRecorder(trace.FlightRecorderConfig{
    MinAge:   10 * time.Second, // keep at least 10s of data
    MaxBytes: 5 << 20,          // cap at 5 MiB to limit memory usage
})
if err := fr.Start(); err != nil {
    return err
}
```

**Sizing guidance:**

- **MinAge** — ~2x problem window. For 5-second timeout debugging, use 10 seconds. Runtime may retain more than MinAge if MaxBytes allows.
- **MaxBytes** — busy services generate ~1-10 MB/s of trace data. Start at 1-5 MiB, adjust. MaxBytes wins over MinAge: full buffer discards older data regardless of age.

### Snapshot on error

Capture trace buffer on unexpected events. `sync.Once` prevents multiple snapshots overwriting each other:

```go
var snapshotOnce sync.Once

func captureSnapshot(fr *trace.FlightRecorder) {
    snapshotOnce.Do(func() {
        f, err := os.Create("snapshot.trace")
        if err != nil {
            log.Printf("snapshot file: %v", err)
            return
        }
        defer f.Close()

        if _, err := fr.WriteTo(f); err != nil {
            log.Printf("snapshot write: %v", err)
            return
        }
        fr.Stop()
        log.Printf("captured snapshot to %s", f.Name())
    })
}
```

### Trigger patterns

```go
// Pattern 1: slow request detection
http.HandleFunc("/api/order", func(w http.ResponseWriter, r *http.Request) {
    start := time.Now()
    // ... handler logic ...

    if fr.Enabled() && time.Since(start) > 100*time.Millisecond {
        go captureSnapshot(fr)
    }
})

// Pattern 2: health check failure
if !healthCheck() && fr.Enabled() {
    go captureSnapshot(fr)
}

// Pattern 3: HTTP endpoint for on-demand capture (internal/admin listener with auth only; traces expose stacks and logged data)
http.HandleFunc("/debug/flightrecorder", func(w http.ResponseWriter, r *http.Request) {
    if !fr.Enabled() {
        http.Error(w, "flight recorder not active", http.StatusServiceUnavailable)
        return
    }
    w.Header().Set("Content-Type", "application/octet-stream")
    w.Header().Set("Content-Disposition", "attachment; filename=trace.out")
    fr.WriteTo(w)
})
```

### Analyzing a snapshot

```bash
go tool trace snapshot.trace
```

Snapshot has same data as regular trace; same analysis techniques apply (timeline viewer, goroutine analysis, pprof extraction). Its flow events help diagnose lock contention and goroutine stalls behind the anomaly.

### Constraints

- **At most one flight recorder** active at a time (may be relaxed in future Go versions)
- Flight recorder **can run concurrently** with `trace.Start`
- Only one goroutine may call `WriteTo` at a time; `sync.Once` pattern handles this
- `Stop()` blocks until any concurrent `WriteTo` completes

### When to use flight recorder vs regular tracing

| Scenario | Tool | Why |
| --- | --- | --- |
| Known slow operation | `go test -trace` or `trace.Start`/`Stop` | Start and stop points known |
| Intermittent production latency spikes | Flight recorder | Spike timing unknown; buffer captures it retroactively |
| Post-mortem after timeout or crash | Flight recorder | Problem already happened; regular tracing misses it |
| Continuous performance monitoring | `samber/cc-skills-golang@golang-observability` (Pyroscope) | Flight recorder is one-shot diagnosis, not continuous collection |

## Overhead and Practical Limits

| Concern | Guidance |
| --- | --- |
| **Runtime overhead** | ~1-2% CPU during capture; negligible when not capturing |
| **Data volume** | Traces generate MB/s. 10-second trace of busy service can hit 50-100MB |
| **Capture duration** | 5-10 seconds typical. Longer traces slow to open, hard to navigate |
| **Memory to view** | `go tool trace` loads whole trace into memory. Large traces may need 1GB+ RAM |
| **Browser performance** | Web UI may struggle with traces >100MB. Use short captures. |
| **Production use** | Safe for short captures on one instance. Do not capture continuously. |

## Trace vs pprof: When to Use Which

| Question | Tool | Why |
| --- | --- | --- |
| Where does CPU time go? | pprof CPU profile | Statistical sampling, low overhead, aggregate view |
| Why is latency high but CPU low? | go tool trace | Shows goroutine waiting states: I/O, channels, mutexes |
| Where do allocations happen? | pprof heap profile | Per-function allocation counts and sizes |
| Why are GC pauses long? | go tool trace | Shows STW phases, mark assist, GC timeline |
| Is there lock contention? | pprof mutex/block + trace | pprof quantifies it; trace shows timeline |
| Are goroutines leaking? | pprof goroutine + trace | pprof shows stack; trace shows creation/lifecycle |
| Which goroutines compete for CPU? | go tool trace | Shows runnable vs running states across all Ps |
| What's the wall-clock breakdown of a request? | go tool trace (with annotations) | Timeline view with tasks and regions |

Unsure: start with pprof (lower overhead, simpler output). Use trace when pprof doesn't explain latency or wall-clock timeline is needed.
