# Package Guide

## Table of Contents

- [Import Paths and Aliases](#import-paths-and-aliases)
- [`lo` — Core (Immutable)](#lo--core-immutable)
- [`lo/parallel` (lop) — Concurrent Transforms](#loparallel-lop--concurrent-transforms)
- [`lo/mutable` (lom) — In-Place Mutations](#lomutable-lom--in-place-mutations)
- [`lo/it` (loi) — Lazy Iterators](#loit-loi--lazy-iterators)
- [`lo/exp/simd` — Experimental SIMD](#loexpsimd--experimental-simd)
- [Decision Flowchart](#decision-flowchart)
- [Comparison Table](#comparison-table)

## Import Paths and Aliases

```go
import (
    "github.com/samber/lo"            // lo  — core, immutable
    "github.com/samber/lo/parallel"    // lop — concurrent transforms
    "github.com/samber/lo/mutable"     // lom — in-place mutations
    "github.com/samber/lo/it"          // loi — lazy iterators (Go 1.23+)
    "github.com/samber/lo/exp/simd"    // experimental SIMD
)
```

## `lo` — Core (Immutable)

Default package. 300+ functions returning new collections without modifying inputs.

**Mental model:** JavaScript's `Array.prototype.map/filter/reduce`, but type-safe via generics.

**Characteristics:**

- Every function allocates new result slice/map; input never modified
- Safe for concurrent reads on input while transforms run
- Composable: one function's output feeds directly into next

**Use when:** Always start here. Move to other packages only when profiling reveals measured bottleneck.

```go
// Immutable — users slice is untouched
active := lo.Filter(users, func(u User, _ int) bool {
    return u.Active
})
```

## `lo/parallel` (lop) — Concurrent Transforms

Parallel variants of core functions. Each element processed in separate goroutine with automatic worker pooling.

**Available functions:** `Map`, `ForEach`, `Times`, `GroupBy`, `PartitionBy`

**Characteristics:**

- Results preserve original order despite concurrent execution
- Internal goroutine pool manages concurrency (not configurable via API; one goroutine per element)
- Synchronization via `sync.WaitGroup`

**Use when:**

- CPU-bound transforms on large datasets (~1000+ items)
- Expensive transform function (parsing, hashing, computing)
- Order must be preserved

**Do NOT use when:**

- Small datasets (<100 items): goroutine creation overhead exceeds benefit
- I/O-bound work (HTTP calls, DB queries): use `errgroup` with context cancellation instead
- Trivial transform function (field access, type cast): `lo.Map` is faster

```go
// CPU-heavy: parse 10k JSON documents in parallel
parsed := lop.Map(rawDocs, func(doc []byte, _ int) *Document {
    return parseDocument(doc) // expensive operation
})
```

**Diagnose:** `go tool pprof -cpu`. If transform function dominates CPU profile on large dataset, `lop` helps.

## `lo/mutable` (lom) — In-Place Mutations

Modifies original slice directly. Zero allocation overhead.

**Available functions:** `Filter`, `Map`, `Shuffle`, `Reverse`, `Replace`

**Characteristics:**

- Modifies input slice; callers must expect side effects
- `lom.Filter` shortens slice (removes non-matching elements in-place)
- `lom.Map` transforms elements in-place (preserves length)
- Uses Fisher-Yates for `Shuffle`
- Not safe for concurrent access to source slice

**Use when:**

- `go tool pprof -alloc_objects` confirms allocation pressure from `lo.Filter`/`lo.Map`
- Very large slices with measurable GC pressure
- Source modification explicitly wanted; original not needed afterwards

**Do NOT use when:**

- Multiple goroutines read same slice
- Original data needed after transform
- Code readability matters more than micro-optimization

```go
// In-place filter — modifies 'items' directly
items = lom.Filter(items, func(item Item, _ int) bool {
    return item.Price > 0
})
```

**Diagnose:** 1- `go tool pprof -alloc_objects`: find which `lo.*` calls allocate most 2- `go build -gcflags="-m"`: check if result slices escape to heap

## `lo/it` (loi) — Lazy Iterators

Go 1.23+ iterator support with lazy evaluation. Transforms deferred until consumed; no intermediate slices allocated.

**Characteristics:**

- Uses `range`-over-func (Go 1.23+)
- Composable pipelines: `loi.Map` → `loi.Filter` → `loi.Take` runs as single pass
- No intermediate slice allocations between pipeline stages
- Modules: `channel`, `find`, `intersect`, `map`, `math`, `seq`, `string`, `tuples`, `type_manipulation`

**Use when:**

- Chaining 3+ transforms on large datasets: eliminates intermediate allocations
- Sequences where only subset needed (lazy `Take`/`TakeWhile`)
- Composable pipelines with range-over-func

**Do NOT use when:**

- Go version < 1.23
- Simple single-step transforms: `lo.Map` is clearer, negligible overhead
- Random access to intermediate results needed

```go
// Lazy pipeline — no intermediate slices allocated
for name := range loi.Map(
    loi.Filter(users, func(u User) bool { return u.Active }),
    func(u User) string { return u.Name },
) {
    fmt.Println(name)
}
```

## `lo/exp/simd` — Experimental SIMD

SIMD (Single Instruction Multiple Data) optimized operations for numeric types on amd64.

**Use when:** Bulk numeric operations after benchmarking confirms bottleneck. Very specialized.

**Warning:** Experimental, not covered by semver stability guarantees; API may break between minor versions. Do not use in production without version pinning.

## Decision Flowchart

```
Start with lo.Map/Filter/Reduce (immutable, safe)
  │
  ├─ Profiler shows allocation pressure?
  │    └─ Yes → Switch specific calls to lom (mutable)
  │
  ├─ Profiler shows CPU-bound transform is slow?
  │    └─ Yes + large dataset → Switch to lop (parallel)
  │
  ├─ Chaining 3+ transforms with intermediate allocations?
  │    └─ Yes + Go 1.23+ → Switch to loi (lazy iterators)
  │
  └─ Need reactive/streaming over infinite events?
       └─ Yes → Use samber/ro instead (different library)
```

## Comparison Table

| Aspect | `lo` | `lop` | `lom` | `loi` | `simd` |
| --- | --- | --- | --- | --- | --- |
| Allocations | New slice/map | New slice/map | Zero (in-place) | Zero (lazy) | Varies |
| Goroutines | None | 1 per element | None | None | None |
| Order preserved | Yes | Yes | Yes | Yes | Yes |
| Input modified | No | No | Yes | No | Varies |
| Concurrent-safe | Read-safe | Read-safe | Not safe | Read-safe | Varies |
| API stability | Stable | Stable | Stable | Stable | Experimental |
| Go version | 1.18+ | 1.18+ | 1.18+ | 1.23+ | 1.25+ |
