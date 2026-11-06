# pprof Reference

This file covers how to **use** the `go tool pprof` CLI and **interpret** output. For enabling pprof endpoints on running services (net/http/pprof import, authentication, security), → See `samber/cc-skills-golang@golang-troubleshooting` skill.

## Table of Contents

- [Profile Types](#profile-types)
  - [Choosing between alloc_objects and alloc_space](#choosing-between-alloc_objects-and-alloc_space)
  - [Choosing between inuse_space and alloc_space](#choosing-between-inuse_space-and-alloc_space)
  - [Enabling mutex and block profiles](#enabling-mutex-and-block-profiles)
- [Generating Profiles](#generating-profiles)
  - [From benchmarks (no HTTP server needed)](#from-benchmarks-no-http-server-needed)
  - [From running service](#from-running-service)
  - [From code (programmatic)](#from-code-programmatic)
- [Interactive CLI Commands](#interactive-cli-commands)
  - [`top` — self time ranking (start here)](#top--self-time-ranking-start-here)
  - [`top -cum` — cumulative time ranking](#top--cum--cumulative-time-ranking)
  - [`list funcName` — annotated source](#list-funcname--annotated-source)
  - [`peek funcName` — callers and callees](#peek-funcname--callers-and-callees)
  - [`tree` — hierarchical call tree](#tree--hierarchical-call-tree)
  - [`traces` — raw stack traces](#traces--raw-stack-traces)
  - [`web` / `svg` — graphical call graph](#web--svg--graphical-call-graph)
  - [`disasm funcName` — assembly-level](#disasm-funcname--assembly-level)
  - [`weblist funcName` — annotated source in browser](#weblist-funcname--annotated-source-in-browser)
  - [`tags` — profile label breakdown](#tags--profile-label-breakdown)
  - [`tagroot` and `tagleaf` — group by labels](#tagroot-and-tagleaf--group-by-labels)
  - [`granularity` — control grouping level](#granularity--control-grouping-level)
  - [`sort` — change sort order](#sort--change-sort-order)
  - [`source` — show source for matching regex](#source--show-source-for-matching-regex)
  - [`focus`, `ignore`, `hide`, `show` — filtering](#focus-ignore-hide-show--filtering)
  - [`normalize` — normalize against a base profile](#normalize--normalize-against-a-base-profile)
  - [`sample_index` — switch metric in multi-metric profiles](#sample_index--switch-metric-in-multi-metric-profiles)
  - [`unit` — change display units](#unit--change-display-units)
  - [`callgrind` — export for KCachegrind](#callgrind--export-for-kcachegrind)
  - [`proto` — save processed profile](#proto--save-processed-profile)
  - [`help` — list all commands](#help--list-all-commands)
  - [`show_from=regex` — trim callers above match](#show_fromregex--trim-callers-above-match)
  - [`noinlines` — flatten inlined functions](#noinlines--flatten-inlined-functions)
  - [Full command reference](#full-command-reference)
- [Graphical / Web UI](#graphical--web-ui)
- [Comparing Profiles](#comparing-profiles)
  - [Memory leak detection with `-base`](#memory-leak-detection-with--base)
  - [Comparing CPU profiles across code versions](#comparing-cpu-profiles-across-code-versions)
- [Common Patterns](#common-patterns)
  - [Flat high + cum high](#flat-high--cum-high)
  - [Flat low + cum high](#flat-low--cum-high)
  - [`alloc_objects` high, `inuse_space` low](#alloc_objects-high-inuse_space-low)
  - [`inuse_space` growing over time](#inuse_space-growing-over-time)
  - [Mutex/block profile hot](#mutexblock-profile-hot)
  - [Many goroutines blocked on same channel/mutex](#many-goroutines-blocked-on-same-channelmutex)
  - [`runtime.mallocgc` dominates CPU profile](#runtimemallocgc-dominates-cpu-profile)
  - [`runtime.memmove` high in CPU profile](#runtimememmove-high-in-cpu-profile)
  - [`runtime.scanobject` high in CPU profile](#runtimescanobject-high-in-cpu-profile)

## Profile Types

Match symptom to profile before capturing.

| Profile | Flag / Endpoint | Use when | Why this profile and not another |
| --- | --- | --- | --- |
| **CPU** | `-cpuprofile` or `/debug/pprof/profile?seconds=30` | High CPU usage, slow functions | Samples which functions are on-CPU at 100Hz; misses off-CPU time (I/O, sleep) |
| **Heap (alloc_objects)** | `-memprofile` then `pprof -alloc_objects` | GC pressure, too many allocations | Counts allocation events regardless of size; for when allocation frequency and object churn dominate |
| **Heap (alloc_space)** | `pprof -alloc_space` | Largest allocation sites by volume | Total bytes allocated; for reducing peak memory, not just GC frequency |
| **Heap (inuse_space)** | `pprof -inuse_space` | Memory growing over time, suspected leaks | Currently live heap objects; compare two snapshots to isolate leak sources |
| **Heap (inuse_objects)** | `pprof -inuse_objects` | Object count growth, suspected leak of small objects | Counts live objects regardless of size; for leaks of many small objects not visible in inuse_space |
| **Goroutine** | `/debug/pprof/goroutine` | Blocked I/O, goroutine leaks, pool exhaustion | Snapshots all goroutine stacks; look for goroutines piling up on same call site |
| **Mutex** | `/debug/pprof/mutex` | Lock contention between goroutines | Cumulative time goroutines waited to acquire mutexes. Must enable first: `runtime.SetMutexProfileFraction(5)` |
| **Block** | `/debug/pprof/block` | Goroutines blocked on channels, mutexes, timers, select | Cumulative time goroutines spent blocked on synchronization primitives. Must enable first: `runtime.SetBlockProfileRate(1)` |
| **Threadcreate** | `/debug/pprof/threadcreate` | Excessive OS thread creation | Stack traces that created new OS threads; typically cgo calls or blocking syscalls that pin a thread |

High latency but low CPU: Goroutine + Block + Trace (scheduling delays, I/O waits). See [Trace Reference](./trace.md).

### Choosing between alloc_objects and alloc_space

- **alloc_objects**: "where do I allocate most often?" Use when allocation frequency and object churn drive GC work.
- **alloc_space**: "where do I allocate most bytes?" Use to reduce peak memory usage and RSS.
- Start with `alloc_objects`. GC churn is Go's most common allocation-related bottleneck.

### Choosing between inuse_space and alloc_space

- **alloc_space**: cumulative since program start, includes objects already freed by GC
- **inuse_space**: point-in-time snapshot, currently live objects only
- `alloc_space` finds allocation hot spots to optimize. `inuse_space` debugs memory leaks.

### Enabling mutex and block profiles

Disabled by default because they add overhead. Enable before capturing:

```go
import "runtime"

// Mutex profiling: fraction of mutex contention events recorded.
// 5 means 1 out of 5 events is recorded. Higher = less overhead but less detail.
runtime.SetMutexProfileFraction(5)

// Block profiling: time-based sampling rate.
// 1 = record all blocking events. Higher values sample about one event per rate nanoseconds blocked.
// Use 1 for debugging, higher values (e.g. 1000000 = 1ms) for production.
runtime.SetBlockProfileRate(1)
```

Disable after investigation to remove overhead:

```go
runtime.SetMutexProfileFraction(0)
runtime.SetBlockProfileRate(0)
```

## Generating Profiles

### From benchmarks (no HTTP server needed)

```bash
# CPU profile — measures where compute time goes during benchmark execution
go test -bench=BenchmarkParse -cpuprofile=cpu.prof ./pkg/parser

# Memory profile — captures allocation patterns during benchmark
go test -bench=BenchmarkParse -memprofile=mem.prof ./pkg/parser

# Both at once — but be aware CPU profiling adds ~5% overhead which can skew memory results
go test -bench=BenchmarkParse -cpuprofile=cpu.prof -memprofile=mem.prof ./pkg/parser
```

### From running service

Requires `import _ "net/http/pprof"` (see `samber/cc-skills-golang@golang-troubleshooting` skill for secure setup):

```bash
# CPU profile — fetch 30 seconds of samples and open interactive mode
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# CPU profile — fetch and immediately generate SVG (no interactive mode)
go tool pprof -svg http://localhost:6060/debug/pprof/profile?seconds=10 > cpu.svg

# CPU profile — fetch with a timeout
go tool pprof -timeout=60 "http://localhost:6060/debug/pprof/profile?seconds=30"

# Heap profile — fetch and show top allocation sites
go tool pprof -top -alloc_objects http://localhost:6060/debug/pprof/heap

# Goroutine profile — fetch and show top goroutine stacks
go tool pprof -top http://localhost:6060/debug/pprof/goroutine

# Mutex profile — fetch contention data
go tool pprof -top http://localhost:6060/debug/pprof/mutex

# Block profile — fetch blocking data
go tool pprof -top http://localhost:6060/debug/pprof/block

# Fetch and save to a file without analysis (using curl)
curl -o heap.prof http://localhost:6060/debug/pprof/heap

# Human-readable goroutine dump (no go tool pprof needed)
curl http://localhost:6060/debug/pprof/goroutine?debug=1

# Goroutine dump with full stack traces, creation site, and labels
curl http://localhost:6060/debug/pprof/goroutine?debug=2

# Human-readable heap stats
curl http://localhost:6060/debug/pprof/heap?debug=1

# Fetch over TLS with client certificate
go tool pprof -tls_cert=client.crt -tls_key=client.key -tls_ca=ca.crt https://myservice:6060/debug/pprof/profile?seconds=30

# Last resort, trusted network only: skips server cert verification (MITM risk); prefer -tls_ca above
go tool pprof https+insecure://myservice:6060/debug/pprof/profile?seconds=30
```

Mutex and block profiles hold data since last reset.

### From code (programmatic)

```go
import "runtime/pprof"

// CPU profile
f, _ := os.Create("cpu.prof")
pprof.StartCPUProfile(f)
defer pprof.StopCPUProfile()

// Heap snapshot at a specific point
f, _ := os.Create("heap.prof")
pprof.WriteHeapProfile(f)
f.Close()

// Named profile (goroutine, threadcreate, etc.)
pprof.Lookup("goroutine").WriteTo(f, 0)
```

## Interactive CLI Commands

Open profile in interactive mode:

```bash
go tool pprof cpu.prof
# or from a URL:
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30
```

### `top` — self time ranking (start here)

Run first. Ranks functions by time (or allocations) spent in function itself:

```
(pprof) top
Showing nodes accounting for 4.2s, 84% of 5s total
      flat  flat%   sum%        cum   cum%
     1.50s 30.00% 30.00%      2.80s 56.00%  encoding/json.Marshal
     0.80s 16.00% 46.00%      0.80s 16.00%  runtime.mallocgc
     0.60s 12.00% 58.00%      0.60s 12.00%  runtime.memmove
     0.50s 10.00% 68.00%      0.50s 10.00%  runtime.scanobject
     0.40s  8.00% 76.00%      1.90s 38.00%  myapp/pkg/parser.Parse
     0.30s  6.00% 82.00%      0.30s  6.00%  syscall.syscall
     0.10s  2.00% 84.00%      0.10s  2.00%  runtime.futex
```

| Column | Meaning | How to read it |
| --- | --- | --- |
| **flat** | Time in function itself, excluding callees | High flat = function's own code is expensive |
| **flat%** | flat as percentage of total sample time | Quick view of relative cost |
| **sum%** | Running total of flat% down the list | "The top 3 functions account for 58% of total time" |
| **cum** | Time in function + all functions it calls (cumulative) | High cum with low flat = function delegates to expensive callees |
| **cum%** | cum as percentage of total | Compare with flat%; big gap means cost is in callees |

**Limiting output:**

```
(pprof) top 5              # show only top 5 functions
(pprof) top -cum 10        # top 10 by cumulative time
(pprof) top -flat 20       # top 20 by flat time (default sort)
```

### `top -cum` — cumulative time ranking

Critical when runtime functions (`runtime.mallocgc`, `runtime.memmove`, `runtime.scanobject`) dominate `top`. They are symptoms, not causes. `top -cum` reveals which **application** functions trigger them:

```
(pprof) top -cum
      flat  flat%   sum%        cum   cum%
     0.40s  8.00%  8.00%      3.80s 76.00%  myapp/pkg/handler.HandleRequest
     0.10s  2.00% 10.00%      2.80s 56.00%  myapp/pkg/handler.serializeResponse
     1.50s 30.00% 40.00%      2.80s 56.00%  encoding/json.Marshal
```

Hot path: `HandleRequest` → `serializeResponse` → `json.Marshal`. Optimize `serializeResponse`, not `runtime.mallocgc`.

### `list funcName` — annotated source

Function source with per-line cost. Pinpoints **exact line** causing the bottleneck:

```
(pprof) list serializeResponse
Total: 5s
ROUTINE ======================== myapp/pkg/handler.serializeResponse
     0.10s      2.80s (flat, cum) 56.00% of Total
         .          .     38:func serializeResponse(w http.ResponseWriter, data any) {
         .      0.20s     39:    w.Header().Set("Content-Type", "application/json")
     0.10s      2.60s     40:    buf, err := json.Marshal(data)
         .          .     41:    if err != nil {
         .          .     42:        http.Error(w, err.Error(), 500)
         .          .     43:        return
         .          .     44:    }
         .      0.20s     45:    w.Write(buf)
         .          .     46:}
```

- Left column = **flat** time (this line's own work)
- Right column = **cumulative** time (this line + everything it calls)
- Line 40 has 2.60s cumulative because `json.Marshal` is expensive

**Use `list` with regex** to match multiple functions:

```
(pprof) list Parse.*       # all functions starting with Parse
(pprof) list \.Handle      # all Handle methods across packages
```

### `peek funcName` — callers and callees

One-hop call graph neighborhood: who calls a function, what it calls. Use to trace responsibility when a function is hot and cause could be upstream (too many calls) or downstream (expensive callees):

```
(pprof) peek json.Marshal
Showing nodes accounting for 5s, 100% of 5s total
----------------------------------------------+-------------
                                               |      flat  flat%   sum%        cum   cum%
 myapp/pkg/handler.serializeResponse 2.60s     |
 myapp/pkg/api.buildResponse         0.20s     |     1.50s 30.00% 30.00%      2.80s 56.00%  encoding/json.Marshal
----------------------------------------------+-------------
                                               |
 reflect.Value.MapRange              0.40s     |
 encoding/json.(*encodeState).marshal 0.30s    |
 runtime.mallocgc                     0.80s    |
```

Top section = callers (who calls json.Marshal). Bottom section = callees (what json.Marshal calls internally).

### `tree` — hierarchical call tree

Full call tree, cumulative cost at each level. Use when `peek` gives too little context:

```
(pprof) tree
     0.40s  8.00%  8.00%      3.80s 76.00%  myapp/pkg/handler.HandleRequest
              0.10s  myapp/pkg/handler.serializeResponse
                     1.50s  encoding/json.Marshal
                            0.80s  runtime.mallocgc
              0.20s  myapp/pkg/handler.validateInput
              0.10s  myapp/pkg/handler.fetchData
```

### `traces` — raw stack traces

Dumps all raw sample stack traces. Each shows what program was doing when sampled:

```
(pprof) traces
-----------+-------------------------------------------------------
     bytes:  1.5MB
     1.50s   encoding/json.Marshal
             myapp/pkg/handler.serializeResponse
             myapp/pkg/handler.HandleRequest
             net/http.(*ServeMux).ServeHTTP
-----------+-------------------------------------------------------
```

Spots unexpected call paths (e.g., an unexpected function called from a hot path).

### `web` / `svg` — graphical call graph

`web` opens call graph in browser. `svg` saves it to file. Both require graphviz (`brew install graphviz` or `apt install graphviz`).

Visual encoding:

- **Thicker edges** = more time through that call
- **Larger nodes** = more time in that function
- **Red/dark nodes** = hot spots (high flat time)
- **Edge labels** = time through that call path

Use when text output doesn't show full picture.

### `disasm funcName` — assembly-level

Assembly with per-instruction cost. For micro-optimization: verify SIMD instructions, bounds check elimination, or inlining:

```
(pprof) disasm Parse
Total: 5s
ROUTINE ======================== myapp/pkg/parser.Parse
     0.40s      1.90s (flat, cum) 38.00% of Total
     0.10s      0.10s    4a3b20: MOVQ 0x8(SP), AX          ;parser.go:15
     0.20s      0.20s    4a3b28: CMPQ AX, $0x100           ;parser.go:16
         .      0.10s    4a3b2f: JGE 0x4a3b80              ;parser.go:16
     0.10s      1.50s    4a3b35: CALL runtime.makeslice(SB) ;parser.go:17
```

### `weblist funcName` — annotated source in browser

Like `list`, but in browser with color-coded cost. Lines shade from white (no cost) to red (hot):

```
(pprof) weblist serializeResponse
```

Requires browser. Falls back to `list` if none is available.

### `tags` — profile label breakdown

Tag values in profile. Runtime profiles carry tags like `thread_id`; custom profiles add arbitrary labels via `pprof.Do()`:

```go
labels := pprof.Labels("request_type", "api", "endpoint", "/users")
pprof.Do(ctx, labels, func(ctx context.Context) {
    handleRequest(ctx)
})
```

```
(pprof) tags
request_type: api (85%), batch (15%)
endpoint: /users (40%), /orders (35%), /products (25%)
```

### `tagroot` and `tagleaf` — group by labels

Group profile data by tag values into a virtual call tree rooted on tag names:

```
(pprof) tagroot request_type    # group everything by request_type first
(pprof) top                     # now shows breakdown per request_type
(pprof) tagleaf endpoint        # add endpoint as leaf grouping
```

For multi-tenant profiling or breakdown by request type without code changes.

### `granularity` — control grouping level

Sets sample aggregation level:

```
(pprof) granularity=functions    # default — group by function name
(pprof) granularity=filefunctions # group by file:function
(pprof) granularity=files        # group by file only
(pprof) granularity=lines        # group by exact source line
(pprof) granularity=addresses    # group by instruction address (most granular)
```

`lines` helps when one function has multiple hot spots: shows expensive lines without needing `list`.

### `sort` — change sort order

```
(pprof) sort=flat     # sort by flat time (default for top)
(pprof) sort=cum      # sort by cumulative time (same as top -cum)
```

### `source` — show source for matching regex

Like `list`, but annotated source for all functions matching a pattern:

```
(pprof) source handler   # show annotated source for all functions matching "handler"
```

### `focus`, `ignore`, `hide`, `show` — filtering

Narrow to specific functions or drop noise. Filters persist across commands until explicitly cleared:

```
(pprof) focus=myapp            # only show call paths that pass through "myapp"
(pprof) ignore=runtime         # remove runtime functions from display
(pprof) hide=testing           # hide testing framework noise from graphs
(pprof) show=handler           # only show functions matching "handler"
(pprof) tagfocus=endpoint=/users  # only show samples with this tag value
(pprof) tagignore=request_type=batch  # exclude samples with this tag value
```

**Difference between `focus`, `show`, `hide`, and `ignore`:**

- `focus` — keeps only paths containing a matching function; drops the rest
- `ignore` — removes matching functions from graph entirely; their costs are attributed to callers
- `show` — like `focus` but only affects display, not cost accounting
- `hide` — like `ignore` but only hides from display, not cost accounting

**Clear all filters:**

```
(pprof) reset
```

### `normalize` — normalize against a base profile

With `-base`, values are deltas by default. `normalize` scales base profile to main profile total, so ratios stay comparable even if run durations differ:

```
(pprof) normalize
```

### `sample_index` — switch metric in multi-metric profiles

Heap profiles hold multiple metrics (alloc_objects, alloc_space, inuse_objects, inuse_space). Switch without reloading:

```
(pprof) sample_index=alloc_objects
(pprof) top                       # now shows allocation counts
(pprof) sample_index=inuse_space
(pprof) top                       # now shows live memory
```

### `unit` — change display units

```
(pprof) unit=ms         # display time in milliseconds
(pprof) unit=seconds    # display in seconds
(pprof) unit=MB         # display memory in megabytes
(pprof) unit=auto       # automatic (default)
```

### `callgrind` — export for KCachegrind

Exports callgrind format. Open in KCachegrind or QCachegrind for advanced visualization:

```
(pprof) callgrind
Generating report in callgrind format
```

### `proto` — save processed profile

Saves current profile (after filtering) as protobuf, for sharing or later analysis:

```
(pprof) proto > filtered.pb.gz
```

### `help` — list all commands

```
(pprof) help             # full command list with descriptions
(pprof) help top         # detailed help for a specific command
```

### `show_from=regex` — trim callers above match

Hides all frames above first matching function. Use when only one subsystem matters, to strip framework/routing noise above it:

```
(pprof) show_from=handler.Handle   # start the graph from Handle, hide all callers above
```

### `noinlines` — flatten inlined functions

Attributes inlined functions to their first out-of-line caller. Use when inlining makes graph call chains confusing:

```
(pprof) noinlines
```

### Full command reference

Each command below works in shell and inside interactive `(pprof)` prompt. Interactive form drops `go tool pprof` and profile path: `go tool pprof -top cpu.prof` becomes just `top`.

**Reporting commands:**

```bash
# Top functions by self (flat) cost — the first command to run
go tool pprof -top cpu.prof

# Top 20 functions by cumulative cost (self + callees)
go tool pprof -cum -top -nodecount=20 cpu.prof

# Annotated source for a specific function — pinpoints the exact expensive line
go tool pprof -list=json.Marshal cpu.prof

# Callers and callees of a function — trace the responsibility chain
go tool pprof -peek=serializeResponse cpu.prof

# Hierarchical call tree with costs at each level
go tool pprof -tree cpu.prof

# Raw sample stack traces — spot unexpected call paths
go tool pprof -traces cpu.prof

# Per-instruction assembly cost — verify SIMD, bounds checks, inlining
go tool pprof -disasm=Parse cpu.prof

# Annotated source for all functions matching a regex
go tool pprof -source='handler\..*' cpu.prof

# Text output (flat table, alternative to -top)
go tool pprof -text cpu.prof
```

**Graph/export commands:**

```bash
# SVG call graph (viewable in any browser, no graphviz server needed)
go tool pprof -svg cpu.prof > cpu.svg

# SVG of only the subgraph matching a regex
go tool pprof -svg -focus=handler cpu.prof > handler.svg

# PDF call graph
go tool pprof -pdf cpu.prof > cpu.pdf

# PNG call graph
go tool pprof -png cpu.prof > cpu.png

# GIF call graph
go tool pprof -gif cpu.prof > cpu.gif

# DOT format (for custom graphviz processing: dot -Tsvg cpu.dot > cpu.svg)
go tool pprof -dot cpu.prof > cpu.dot

# Callgrind format (open with KCachegrind / QCachegrind)
go tool pprof -callgrind cpu.prof > cpu.callgrind

# Save current profile (with filters applied) in protobuf format
go tool pprof -proto -focus=handler cpu.prof > handler-only.pb.gz

# Annotated source in browser with color-coded cost per line
go tool pprof -weblist=serializeResponse cpu.prof
```

**Filtering flags** — narrow analysis to relevant functions:

```bash
# Focus: keep only call paths passing through matching functions
go tool pprof -focus=myapp/pkg/handler -top cpu.prof

# Ignore: remove matching functions — their cost is attributed to callers
go tool pprof -ignore=runtime -top cpu.prof

# Show: display only matching functions (display-only, does not change cost accounting)
go tool pprof -show=handler -top cpu.prof

# Hide: hide matching functions from display (does not change cost accounting)
go tool pprof -hide=testing -svg cpu.prof > clean.svg

# Show_from: trim all frames above the first match — hides framework/routing callers
go tool pprof -show_from=handler.Handle -top cpu.prof

# Noinlines: attribute inlined functions to their first out-of-line caller
go tool pprof -noinlines -top cpu.prof

# Combine multiple filters
go tool pprof -cum -top -nodecount=10 -focus=handler -ignore=runtime cpu.prof
```

**Tag-based filtering** — for profiles with labels (via `pprof.Do()`):

```bash
# Show all tag keys and their value distributions
go tool pprof -tags cpu.prof

# Keep only samples tagged with a specific key=value
go tool pprof -tagfocus=endpoint=/users -top cpu.prof

# Exclude samples with a specific tag
go tool pprof -tagignore=request_type=batch -top cpu.prof

# Group by tag — insert pseudo frames at root, breaking down by tag value
go tool pprof -tagroot=request_type -top cpu.prof

# Group by tag as leaf — breaks down each function by tag value
go tool pprof -tagleaf=endpoint -top cpu.prof

# Show/hide tags as annotations in graph output
go tool pprof -tagshow=endpoint -svg cpu.prof > tagged.svg
go tool pprof -taghide=thread_id -svg cpu.prof > clean.svg
```

**Granularity and display control:**

```bash
# Group by source line instead of function — reveals hot lines in multi-hot-spot functions
go tool pprof -granularity=lines -top cpu.prof

# Group by file:function
go tool pprof -granularity=filefunctions -top cpu.prof

# Group by file only
go tool pprof -granularity=files -top cpu.prof

# Group by instruction address (most granular)
go tool pprof -granularity=addresses -top cpu.prof

# Change display units
go tool pprof -unit=ms -top cpu.prof

# Edge/node fraction cutoffs — hide small contributions from graphs
go tool pprof -edgefraction=0.01 -nodefraction=0.005 -svg cpu.prof > clean.svg

# Disable trimming — show the full graph including tiny nodes
go tool pprof -trim=false -svg cpu.prof > full.svg
```

**Heap profile commands:**

```bash
# Top allocation sites by object count — diagnose GC churn
go tool pprof -top -alloc_objects mem.prof

# Top allocation sites by bytes — diagnose peak memory
go tool pprof -top -alloc_space mem.prof

# Currently live objects — diagnose memory leaks
go tool pprof -top -inuse_space mem.prof

# Currently live object count — diagnose leak of many small objects
go tool pprof -top -inuse_objects mem.prof

# Annotated source showing allocation sites by object count
go tool pprof -alloc_objects -list=Parse mem.prof

# SVG call graph colored by allocation objects
go tool pprof -alloc_objects -svg mem.prof > allocs.svg

# Compare two heap snapshots — show only growth (memory leak detection)
go tool pprof -top -base heap-baseline.prof heap-after.prof

# Diff with normalization — makes ratios comparable when capture durations differ
go tool pprof -normalize -top -base heap-baseline.prof heap-after.prof

# Diff as SVG — visualize what grew
go tool pprof -base heap-baseline.prof -svg heap-after.prof > leak.svg

# Diff with annotated source for a specific function
go tool pprof -base heap-baseline.prof -list=handleRequest heap-after.prof
```

**Comparison commands (diff two profiles):**

```bash
# Diff: subtract base from source — all values become deltas
go tool pprof -base cpu-before.prof cpu-after.prof

# Diff base: percentages shown relative to base profile
go tool pprof -diff_base=cpu-before.prof cpu-after.prof

# Diff with normalization — scale base to match source total
go tool pprof -normalize -base heap-before.prof heap-after.prof

# Diff as top report
go tool pprof -top -base cpu-before.prof cpu-after.prof

# Diff as SVG graph
go tool pprof -svg -base cpu-before.prof cpu-after.prof > diff.svg
```

**Symbolization flags:**

```bash
# Disable symbolization (show raw addresses)
go tool pprof -symbolize=none cpu.prof

# Only use local binaries for symbolization (don't contact remote)
go tool pprof -symbolize=local cpu.prof

# Contact running service for symbol information
go tool pprof -symbolize=remote http://localhost:6060/debug/pprof/profile?seconds=10

# Show mangled C++ names (relevant for cgo profiles)
go tool pprof -symbolize=demangle=none cpu.prof

# Full demangling without simplification
go tool pprof -symbolize=demangle=full cpu.prof
```

**Environment variables:**

| Variable | Purpose |
| --- | --- |
| `PPROF_BINARY_PATH` | Search path for local binaries used in symbolization (default: `$HOME/pprof/binaries`). Set when profiling remote servers whose binaries aren't in default path. |
| `PPROF_TOOLS` | Directory with binutils tools (`addr2line`, `nm`, `objdump`). Set when these tools aren't in `$PATH`. |

## Graphical / Web UI

For interactive exploration when CLI output is insufficient:

```bash
# Open interactive web UI with flamegraph, graph, source, and disassembly views
go tool pprof -http=:8080 cpu.prof

# Open on a different port
go tool pprof -http=:9090 mem.prof

# Open with a specific sample type pre-selected
go tool pprof -http=:8080 -alloc_objects mem.prof

# Open with filters pre-applied
go tool pprof -http=:8080 -focus=handler cpu.prof

# Open a diff view in the web UI
go tool pprof -http=:8080 -base heap-baseline.prof heap-after.prof

# Open with no browser auto-launch (just start the server)
go tool pprof -http=:8080 -no_browser cpu.prof
```

Web UI views:

- **Flamegraph** (most intuitive) — width proportional to cost; click to zoom into subtrees; inverted flamegraph (icicle graph) available
- **Graph** — directed call graph with edge weights; nodes and edges sized/colored by cost; interactive zoom and click-to-focus
- **Top** — like `top` command, with sortable columns; click to navigate to source
- **Source** — annotated source with per-line cost; browsable across all functions
- **Disassembly** — like `disasm`, browsable across functions
- **Peek** — interactive peek with expandable callers/callees

Default to CLI for quick diagnosis. Use web UI to explore unfamiliar call graphs, compare profiles visually, or present findings.

## Comparing Profiles

### Memory leak detection with `-base`

Diff two heap profiles to isolate what grew between them:

```bash
# Step 1: take a baseline snapshot
curl http://localhost:6060/debug/pprof/heap > heap-baseline.prof

# Step 2: wait for the suspected leak to accumulate (minutes to hours)

# Step 3: take a second snapshot
curl http://localhost:6060/debug/pprof/heap > heap-after.prof

# Step 4: diff — shows only what grew between the two snapshots
go tool pprof -base heap-baseline.prof heap-after.prof
# Then use top, list, peek as usual — all values are deltas
```

### Comparing CPU profiles across code versions

```bash
# Before your change
go test -bench=BenchmarkParse -cpuprofile=cpu-before.prof ./pkg/parser

# After your change
go test -bench=BenchmarkParse -cpuprofile=cpu-after.prof ./pkg/parser

# Compare visually — load both in separate browser tabs
go tool pprof -http=:8080 cpu-before.prof
go tool pprof -http=:8081 cpu-after.prof
```

For statistical comparison of benchmark numbers (not profiles), use [benchstat](./benchstat.md).

## Common Patterns

### Flat high + cum high

Function itself is the bottleneck: does expensive work directly (tight loop, heavy computation, complex string processing). Optimize its own code: algorithm, data structure, or implementation.

### Flat low + cum high

Coordinator or dispatcher: calls slow things, does little work itself. Drill into callees with `list` or `peek`. Fix is usually in callees, or in calling them less often.

### `alloc_objects` high, `inuse_space` low

Short-lived allocations cause GC churn: each is cheap, but aggregate volume triggers frequent GC cycles. Common sources: `fmt.Errorf` in hot paths (allocates every call), interface boxing (`any` arguments), string-to-byte conversions, slice growth without preallocation. → See `samber/cc-skills-golang@golang-performance` skill for allocation reduction patterns.

### `inuse_space` growing over time

Memory leak. Take two heap snapshots minutes apart, compare with `-base` (see Comparing Profiles above). Growing types reveal leak source. Common causes: unbounded caches, maps that never shrink (Go maps don't release bucket memory on delete), goroutine leaks holding references.

### Mutex/block profile hot

Contention, not CPU: goroutines wait on same lock or channel instead of working. Reduce critical section scope, shard locks across multiple mutexes, or use lock-free structures (`sync/atomic`, `sync.Map` for read-heavy workloads). → See `samber/cc-skills-golang@golang-concurrency` skill.

### Many goroutines blocked on same channel/mutex

Serialization bottleneck: all work funnels through one point, so its speed caps throughput. Options: worker pools with multiple independent queues, sharding work, or buffered channels to smooth bursts.

### `runtime.mallocgc` dominates CPU profile

Allocation rate, not computation, is the bottleneck: runtime spends more time allocating and collecting garbage than running your code. Find top allocators with `alloc_objects` heap profile, then → See `samber/cc-skills-golang@golang-performance` skill for reduction patterns.

### `runtime.memmove` high in CPU profile

Large memory copies, usually from slice `append` growing beyond capacity, `copy()` of large slices, or string-to-byte conversions. Pre-allocate slices to final capacity, reuse buffers, or work with `[]byte` directly.

### `runtime.scanobject` high in CPU profile

GC pointer scanning: heap holds many pointers GC must trace. Reduce pointer density: use value types instead of pointers in slices/maps, flatten nested structures, consider `[N]byte` arrays instead of `string` in hot structs.
