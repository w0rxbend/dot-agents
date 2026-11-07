# Caching Patterns

## Table of Contents

- [Compiled Pattern Caching](#compiled-pattern-caching)
  - [Regexp at package level](#regexp-at-package-level)
  - [Template caching](#template-caching)
  - [Precomputed lookup tables](#precomputed-lookup-tables)
- [Request-Level Caching](#request-level-caching)
  - [singleflight for cache stampede prevention](#singleflight-for-cache-stampede-prevention)
  - [LRU caches](#lru-caches)
- [Algorithmic Complexity](#algorithmic-complexity)
- [Work Avoidance](#work-avoidance)
  - [Map lookups over slice scanning](#map-lookups-over-slice-scanning)
  - [Early returns and short-circuit loops](#early-returns-and-short-circuit-loops)
  - [Avoid iterator chains](#avoid-iterator-chains)
  - [Replace indirect function calls with direct loops](#replace-indirect-function-calls-with-direct-loops)

## Compiled Pattern Caching

**Diagnose:** 1- `go tool pprof` (CPU profile) — `regexp.Compile`, `regexp.MustCompile` or `template.Parse` in hot paths means patterns recompile per call instead of once 2- `go test -bench -benchmem` — compare per-call vs cached compilation; expect 10-12x speedup and compilation allocs/op dropping to zero

### Regexp at package level

`regexp.Compile` builds state machine from pattern: ~5,700ns per compilation. Match on compiled regexp: ~450ns. Per-call compilation wastes 10-12x:

```go
// Bad — compiled on every call
func isValid(email string) bool {
    re := regexp.MustCompile(`^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$`)
    return re.MatchString(email)
}

// Good — compiled once, safe for concurrent use
var emailRegex = regexp.MustCompile(`^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$`)

func isValid(email string) bool { return emailRegex.MatchString(email) }
```

Note: `regexp.MustCompile` panics on invalid patterns — fine for package-level constants (caught at startup). Use `regexp.Compile` for user-provided patterns. Go regexp matches in linear time (no backtracking).

### Template caching

`template.Parse` equally expensive. Parse once at startup:

```go
var reportTmpl = template.Must(template.ParseFiles("templates/report.html"))
```

### Precomputed lookup tables

Pure computation (same input → same output) over small input space: replace calculation with array lookup:

```go
var hexDigit = [16]byte{'0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f'}

func byteToHex(b byte) (byte, byte) {
    return hexDigit[b>>4], hexDigit[b&0x0f] // two array lookups vs branching logic
}
```

Table that fits in L1/L2 cache beats even simple computation.

## Request-Level Caching

**Diagnose:** 1- `go tool pprof` (goroutine profile) — many goroutines blocked on same external call (HTTP fetch, DB query) signal cache stampede: N goroutines miss cache at once 2- `fgprof` — shows off-CPU wait; same fetch function dominating wall-clock time across many goroutines confirms duplicated concurrent work 3- `go tool pprof -alloc_objects` — high alloc counts on fetch functions mean stampede also adds GC pressure

### singleflight for cache stampede prevention

On expiry, many goroutines may hit the miss at once and all start same expensive computation. `singleflight` lets only one goroutine fetch; others wait:

```go
import "golang.org/x/sync/singleflight"

var (
    cache sync.Map
    sf    singleflight.Group
)

func GetWeather(city string) (string, error) {
    if val, ok := cache.Load(city); ok {
        return val.(string), nil
    }

    // Only one goroutine fetches; others block on the same key
    result, err, _ := sf.Do(city, func() (any, error) {
        data, err := fetchFromAPI(city)
        if err == nil { cache.Store(city, data) }
        return data, err
    })
    return result.(string), err
}
```

→ See `samber/cc-skills-golang@golang-concurrency` skill for `singleflight` API details and `sync.Map` vs `RWMutex` choice. → **Generics alternative:** `github.com/samber/go-singleflightx` avoids interface{} boxing overhead; expect 2-4x faster result retrieval than standard library `singleflight.Group`.

### LRU caches

Standard library `container/list` works for bounded eviction caches but has poor cache locality (one heap allocation per node). For high-performance LRU:

- **`github.com/hashicorp/golang-lru`** — thread-safe, simple API
- **`github.com/elastic/go-freelru`** — merges hashmap and ringbuffer into contiguous memory, ~37x faster than sharded implementations

For third-party cache libraries, check official docs for current API signatures.

## Algorithmic Complexity

**Diagnose:** 1- `go tool pprof` (CPU profile) — high cumulative time in functions with nested loops or repeated linear scans marks algorithmic bottleneck 2- `go test -bench` — benchmark at input sizes 100, 1K, 10K, 100K; quadratic growth (10x input → 100x time) means O(n²), replace algorithm

**Common complexity traps in Go:**

| Pattern | Complexity | Fix | Fixed complexity |
| --- | --- | --- | --- |
| `slices.Contains` in loop | O(n·m) | Build `map[T]struct{}` first, then look up | O(n+m) |
| Nested loops for matching | O(n²) | Index with map, sort+binary search, or `slices.BinarySearch` | O(n log n) or O(n) |
| Repeated `append` without prealloc | O(n²) amortized copies | `make([]T, 0, n)` | O(n) |
| String concatenation with `+=` | O(n²) total copies | `strings.Builder` | O(n) |
| Linear scan for min/max/dedup | O(n) per query | Sort once, query many times | O(n log n) + O(log n) per query |

**Think in Big-O first, then optimize constants.** 10x constant-factor gain matters; O(n²) to O(n) matters more.

## Work Avoidance

**Diagnose:** 1- `go tool pprof` (CPU profile) — linear scans (`slices.Contains`, `slices.Index`) or iterator chains (`Filter`, `Map`) burning CPU in hot paths 2- `go test -bench` — compare against map-based or early-return version; expect O(n) → O(1) for membership tests, big gains for short-circuit loops

### Map lookups over slice scanning

`Contains(slice, element)` is O(n); map lookup is O(1). For repeated membership tests on one collection, build map once:

```go
// Bad — O(n*m), checking Contains per element
for _, item := range subset {
    if !Contains(collection, item) { return false } // O(n) per check
}

// Good — O(n+m), build map once, O(1) lookups
seen := make(map[T]struct{}, len(collection))
for _, item := range collection { seen[item] = struct{}{} }
for _, item := range subset {
    if _, ok := seen[item]; !ok { return false }
}
```

Use `struct{}` (0 bytes), not `bool` (1 byte), for set maps.

### Early returns and short-circuit loops

Return once answer is known. Match on iteration 3 of 1000 saves 997 iterations:

```go
// Bad — always iterates full collection
found := false
for _, item := range collection {
    if item == target { found = true }
}
return found

// Good — returns on first match
for i := range collection {
    if collection[i] == target { return true }
}
return false
```

### Avoid iterator chains

Chained iterators (`Filter → Map → First`) build closures and extra machinery. Direct loop is simpler and faster:

```go
// Bad — creates 2 iterators with closures
result, ok := First(Filter(collection, predicate))

// Good — single pass, early return, no closures
for i := range collection {
    if predicate(collection[i]) { return collection[i], true }
}
```

### Replace indirect function calls with direct loops

Wrapper calling another function through closure (e.g., `FromSlicePtr` calling `Map`) blocks inlining. Use direct loop:

```go
// Bad — Map() with closure, per-element function call overhead
func FromSlicePtr(items []*T) []T {
    return Map(items, func(p *T) T { return *p })
}

// Good — direct loop, inlineable, -13% to -17% time
func FromSlicePtr(items []*T) []T {
    result := make([]T, len(items))
    for i := range items { result[i] = *items[i] }
    return result
}
```
