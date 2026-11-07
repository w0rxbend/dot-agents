# I/O & Networking Optimization

## Table of Contents

- [HTTP Transport Configuration](#http-transport-configuration)
  - [Connection pooling](#connection-pooling)
  - [Timeouts](#timeouts)
  - [Drain response body for connection reuse](#drain-response-body-for-connection-reuse)
- [Streaming vs Buffering](#streaming-vs-buffering)
  - [Avoid io.ReadAll for large payloads](#avoid-ioreadall-for-large-payloads)
  - [Streaming JSON](#streaming-json)
- [JSON Performance](#json-performance)
- [Cgo Overhead](#cgo-overhead)
- [Buffered I/O](#buffered-io)
- [Concurrent Multi-Stage Pipelines](#concurrent-multi-stage-pipelines)
  - [The unusual scenario](#the-unusual-scenario)
  - [When to use this (and when NOT to)](#when-to-use-this-and-when-not-to)
- [Batch Operations](#batch-operations)
  - [Database: batch inserts over row-by-row](#database-batch-inserts-over-row-by-row)
  - [HTTP: batch API calls](#http-batch-api-calls)
  - [Channel: batch processing from a stream](#channel-batch-processing-from-a-stream)

## HTTP Transport Configuration

**Diagnose:** 1- `go tool pprof` (goroutine + block profile) — many goroutines blocked on `net/http.(*Transport).dialConn` or `net/http.(*persistConn).readLoop` means connection pool exhaustion 2- `fgprof` — captures on-CPU and off-CPU wait time; look for HTTP calls dominating wall-clock time even when CPU profile shows them cheap 3- `go tool trace` — visualize goroutine lifecycles; long gaps waiting on network I/O instead of processing 4- Prometheus `go_goroutines` — production goroutine count; steady rise under stable load suggests connection or goroutine leaks from misconfigured HTTP clients

### Connection pooling

Default `http.Transport` pools conservatively — `MaxIdleConnsPerHost` defaults to 2. Under high concurrency, requests queue for connections instead of running in parallel:

```go
// Bad — default transport, only 2 idle connections per host
client := &http.Client{}

// Good — tuned for high-concurrency service-to-service calls
var apiClient = &http.Client{
    Timeout: 30 * time.Second,
    Transport: &http.Transport{
        MaxIdleConns:          100,             // total idle connections across all hosts
        MaxIdleConnsPerHost:   20,              // per-host idle connections (default is 2!)
        MaxConnsPerHost:       50,              // cap total connections per host (0 = unlimited)
        IdleConnTimeout:       90 * time.Second,
        TLSHandshakeTimeout:  5 * time.Second,
        ResponseHeaderTimeout: 10 * time.Second,
    },
}
```

Crawlers hitting many different hosts: disable keep-alive so idle connections don't pile up:

```go
crawlerClient := &http.Client{
    Transport: &http.Transport{DisableKeepAlives: true},
}
```

### Timeouts

Zero-value `http.Client` and `http.Server` have NO timeouts. Slow or malicious peer holds connections open indefinitely, exhausting file descriptors and memory:

```go
// Server — always set timeouts to prevent Slowloris attacks
server := &http.Server{
    Addr:         ":8080",
    Handler:      handler,
    ReadTimeout:  5 * time.Second,
    WriteTimeout: 10 * time.Second,
    IdleTimeout:  120 * time.Second,
}
```

### Drain response body for connection reuse

Connections return to pool only after body is fully read. Drain body even when you don't need it:

```go
resp, err := client.Get(url)
if err != nil { return err }
defer resp.Body.Close()
_, _ = io.Copy(io.Discard, resp.Body) // drain to enable connection reuse
```

## Streaming vs Buffering

**Diagnose:** 1- `go tool pprof -inuse_space` — large single allocations (MB-sized) from `io.ReadAll`, `bytes.Buffer.Grow` or `json.Unmarshal` mean whole payloads buffered instead of streamed

### Avoid io.ReadAll for large payloads

`io.ReadAll` loads whole stream into memory. Large files or HTTP responses cause massive memory spikes:

```go
// Bad — 2GB file = 2GB allocation
data, _ := io.ReadAll(f)

// Good — process line by line, O(1) memory
scanner := bufio.NewScanner(f)
for scanner.Scan() { processLine(scanner.Bytes()) }

// Good — stream between reader and writer (32KB internal buffer)
io.Copy(w, resp.Body)
```

`io.ReadAll` is fine for small, bounded payloads (< 1MB) of known size.

### Streaming JSON

Use `json.NewDecoder` for large JSON payloads instead of `json.Unmarshal` (buffers whole body):

```go
dec := json.NewDecoder(r)
for dec.More() {
    var item Item
    if err := dec.Decode(&item); err != nil { return err }
    process(item) // one item at a time
}
```

## JSON Performance

**Diagnose:** 1- `go tool pprof` (CPU profile) — `encoding/json.(*Decoder).Decode`, `reflect.Value.*` or `encoding/json.Marshal` taking significant CPU means reflection-based JSON is the bottleneck 2- `go test -bench -benchmem` — measure ns/op and allocs/op for marshal/unmarshal; expect high alloc counts from reflection; code-gen alternatives should show 2-5x fewer allocs

**Options for faster JSON:**

- **Custom `MarshalJSON`/`UnmarshalJSON`** — hand-written methods for hot-path types remove reflection
- **Code-generation libraries** — `easyjson`, `ffjson` generate marshal/unmarshal methods at build time, no reflection at runtime
- **Drop-in replacements** — `github.com/goccy/go-json`, `github.com/json-iterator/go`, `github.com/bytedance/sonic` offer 2-5x better performance
- **`encoding/json/v2`** (default JSON implementation since Go 1.27; introduced experimental behind `GOEXPERIMENT=jsonv2` in Go 1.25) — migrate deliberately: stricter than v1 (rejects duplicate object keys and invalid UTF-8), so re-run tests against real payloads before relying on it in hot path

For third-party JSON libraries, check official docs for up-to-date API signatures.

## Cgo Overhead

**Diagnose:** 1- `go tool pprof` (CPU profile + threadcreate profile) — `runtime.cgocall` or `runtime.asmcgocall` taking CPU; high threadcreate count means cgo calls pin goroutines to OS threads 2- `go test -bench` — compare cgo call loop with pure Go equivalent; expect ~50-100ns overhead per cgo crossing

Each Go-to-C call via cgo costs ~50-100ns: stack switching, signal mask manipulation, scheduler coordination:

```go
// Bad — cgo overhead per element dominates for tight loops
for i, v := range values {
    values[i] = float64(C.sqrt(C.double(v))) // ~100ns overhead PER CALL
}

// Good — use pure Go stdlib (math.Sqrt is as fast as C and inlineable)
for i, v := range values { values[i] = math.Sqrt(v) }

// Good — batch when C code is unavoidable
C.batch_sqrt((*C.double)(&values[0]), C.int(len(values))) // amortize overhead
```

Other cgo costs: goroutine pinned to OS thread, C code cannot be preempted (may delay GC), function inlining blocked at boundary.

## Buffered I/O

**Diagnose:** 1- `go test -bench` — compare buffered vs unbuffered I/O; expect 3-10x improvement from fewer syscalls 2- `go tool trace` — frequent short syscalls (`pread`, `pwrite`) in rapid succession mean unbuffered access

Unbuffered file reads/writes cost one syscall per operation. `bufio.Reader` and `bufio.Writer` batch small operations, cutting syscalls 10x or more:

```go
// Bad — syscall per line
for _, line := range lines { f.WriteString(line + "\n") }

// Good — buffered, batches writes into larger chunks
w := bufio.NewWriter(f)
for _, line := range lines { w.WriteString(line + "\n") }
w.Flush()
```

## Concurrent Multi-Stage Pipelines

**Diagnose:** 1- `go tool trace` — visualize resource use across stages; look for sequential idle gaps where CPU, disk or network sit unused while another resource is busy 2- `go tool pprof` (CPU + goroutine profile) — confirm each stage saturates a _different_ resource; if stages compete for same resource (e.g., both CPU-bound), concurrency won't help

In rare cases where each stage saturates a _different_ resource (CPU, disk I/O, network), concurrent stages can beat sequential throughput — even with batching between stages.

### The unusual scenario

Example: Stage A compresses records (CPU-bound), Stage B writes to disk (I/O-bound), Stage C uploads to network (network-bound). Sequential execution wastes resources:

```
Time:    0       10      20      30      40      50
CPU:     AAAAAAAAAA|..........|..........|..........|
Disk:    ..........|BBBBBBBBBB|..........|..........|
Network: ..........|..........|CCCCCCCCCC|..........|
```

Concurrent stages let resources work in parallel:

```
Time:    0       10      20      30      40      50
CPU:     AAAAAAAAAA|AA........|
Disk:    ..........|BBBBBBBBBB|BB........|
Network: ..........|..........|CCCCCCCCCC|CC........|
```

**Code pattern:**

```go
// Each stage runs in its own goroutine, bounded by channel buffers
compressedCh := make(chan []byte, 100)    // A → B buffer
uploadedCh := make(chan bool, 100)        // B → C buffer

// Stage A: CPU-bound compression
go func() {
    for record := range inputCh {
        compressed := compress(record)    // saturates CPU
        compressedCh <- compressed
    }
    close(compressedCh)
}()

// Stage B: I/O-bound disk writes
go func() {
    for compressed := range compressedCh {
        diskFile.Write(compressed)        // saturates disk I/O
        uploadedCh <- true
    }
    close(uploadedCh)
}()

// Stage C: network-bound uploads
go func() {
    for <-uploadedCh {
        client.Post(uploadURL, ...)       // saturates network
    }
}()
```

With batching per stage, total throughput = min(A_throughput, B_throughput, C_throughput). Without concurrency, throughput = sequential sum of stages. **Concurrent stages only help when bottlenecks don't overlap.**

### When to use this (and when NOT to)

**Use concurrent pipelines only when ALL of these are true:**

1. **Resource saturation is predictable and non-overlapping** — Measured: A saturates one resource (e.g., CPU = 95%), B another (disk I/O = 90%), C a third (network = 85%).
2. **Bottleneck shifts don't hurt latency** — Order doesn't matter, or records can flow out-of-order through stages.
3. **Buffering overhead is acceptable** — Inter-stage channels consume memory. Large records can push channel buffers past system limits.
4. **You've benchmarked the alternative** — Profile sequential and concurrent versions. Sequential + batching often wins: simpler, no context-switching overhead.

**Avoid concurrent pipelines if:**

- **Records must be ordered** — Concurrent processing may reorder records; if downstream expects order, required synchronization kills speedup.
- **Resources overlap** — If A and B both compete for CPU (e.g., both compress), concurrency adds context-switching overhead with no utilization gain.
- **Latency matters more than throughput** — Single record now travels through 3 stages in parallel, increasing per-record latency.
- **Memory is tight** — Each stage's channel buffer costs memory; deep buffers can exhaust available RAM.

→ See `samber/cc-skills-golang@golang-concurrency` skill for detailed channel patterns and when to use worker pools instead.

## Batch Operations

**Diagnose:** 1- `go test -bench` — compare single-item vs batched operations; expect N-fold throughput gain from amortizing per-operation overhead (syscalls, round-trips) 2- `go tool trace` — repeated short network/disk operations with idle gaps between them; gaps are wasted round-trip time batching removes

### Database: batch inserts over row-by-row

Inserting 1,000 rows one at a time means 1,000 round-trips, 1,000 query parses and 1,000 transaction commits. One batch insert needs one round-trip:

```go
// Bad — 1,000 round-trips, ~500ms
for _, user := range users {
    db.Exec("INSERT INTO users (name, email) VALUES ($1, $2)", user.Name, user.Email)
}

// Good — 1 round-trip with multi-row VALUES, ~5ms
const batchSize = 1000
for i := 0; i < len(users); i += batchSize {
    end := min(i+batchSize, len(users))
    batch := users[i:end]
    // Build multi-row INSERT or use COPY protocol
    tx, _ := db.Begin()
    stmt, _ := tx.Prepare(pq.CopyIn("users", "name", "email"))
    for _, u := range batch { stmt.Exec(u.Name, u.Email) }
    stmt.Exec()
    tx.Commit()
}
```

→ See `samber/cc-skills-golang@golang-database` skill for detailed batch patterns and connection pool configuration.

### HTTP: batch API calls

Send one request with N items instead of N individual HTTP requests when API supports it:

```go
// Bad — 100 HTTP round-trips
for _, id := range ids {
    resp, _ := client.Get(fmt.Sprintf("/api/users/%s", id))
    // ...
}

// Good — 1 HTTP request with all IDs
resp, _ := client.Post("/api/users/batch", "application/json",
    bytes.NewReader(marshalIDs(ids)))
```

### Channel: batch processing from a stream

Accumulate channel items and process in bulk to cut per-item overhead:

```go
func batchProcessor(in <-chan Item, batchSize int) {
    batch := make([]Item, 0, batchSize)
    ticker := time.NewTicker(100 * time.Millisecond) // flush on timeout too
    defer ticker.Stop()
    for {
        select {
        case item, ok := <-in:
            if !ok { flush(batch); return }
            batch = append(batch, item)
            if len(batch) >= batchSize { flush(batch); batch = batch[:0] }
        case <-ticker.C:
            if len(batch) > 0 { flush(batch); batch = batch[:0] }
        }
    }
}
```
