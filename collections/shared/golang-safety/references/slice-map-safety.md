# Slice and Map Safety Deep Dive

## Table of Contents

- [Range Loop Variable Capture](#range-loop-variable-capture)
  - [Pre-Go 1.22: shared loop variable](#pre-go-122-shared-loop-variable)
  - [Go 1.22+: per-iteration scoping](#go-122-per-iteration-scoping)
- [Storing Pointer to Loop Variable](#storing-pointer-to-loop-variable)
- [Slice Header vs Backing Array](#slice-header-vs-backing-array)
- [Subslice Retains Full Backing Array](#subslice-retains-full-backing-array)
- [Standard Library Clone Helpers (Go 1.21+)](#standard-library-clone-helpers-go-121)
- [Map Iteration Order](#map-iteration-order)
- [Deleting During Iteration](#deleting-during-iteration)
  - [Maps — safe](#maps--safe)
  - [Slices — needs care](#slices--needs-care)
- [Comparing Slices and Maps](#comparing-slices-and-maps)

## Range Loop Variable Capture

### Pre-Go 1.22: shared loop variable

NEVER store pointers to loop variables in Go < 1.22; capture by value. Before Go 1.22, range loop variable was reused across iterations. Capturing it in closure or storing its address made all references point to final value:

```go
// ✗ Bad (pre-1.22) — all goroutines see the last value of v
var funcs []func()
for _, v := range []string{"a", "b", "c"} {
    funcs = append(funcs, func() { fmt.Println(v) })
}
for _, f := range funcs {
    f() // prints "c", "c", "c"
}

// ✓ Fix (pre-1.22) — shadow the variable
for _, v := range []string{"a", "b", "c"} {
    v := v // re-declare v in inner scope
    funcs = append(funcs, func() { fmt.Println(v) })
}
```

### Go 1.22+: per-iteration scoping

Go 1.22 changed loop variable semantics: each iteration creates new variable, so closure bug no longer occurs. Old behavior still applies if module targets `go 1.21` or earlier in `go.mod`. Check `go.mod` version.

## Storing Pointer to Loop Variable

Same pre-1.22 issue applies to storing `&v`:

```go
// ✗ Bad (pre-1.22) — all pointers point to the same address
type Item struct{ Name string }
items := []Item{{Name: "a"}, {Name: "b"}}
var ptrs []*Item
for _, item := range items {
    ptrs = append(ptrs, &item) // all point to same loop variable
}
// ptrs[0].Name == "b", ptrs[1].Name == "b"

// ✓ Good — take address of the slice element directly
for i := range items {
    ptrs = append(ptrs, &items[i])
}
```

In Go 1.22+, `&item` is safe because each iteration has own `item`. Taking `&items[i]` is still clearer and avoids copy.

## Slice Header vs Backing Array

Slice is 3-word struct: `{pointer, length, capacity}`. Multiple slices can share same backing array:

```
a := make([]int, 3, 5)
┌─────┬─────┬─────┐
│ ptr │ len=3│cap=5│  ← slice header for a
└──┬──┴─────┴─────┘
   │
   ▼
┌───┬───┬───┬───┬───┐
│ 0 │ 0 │ 0 │   │   │  ← backing array (5 elements)
└───┴───┴───┴───┴───┘

b := a[1:2]
┌─────┬─────┬─────┐
│ ptr │ len=1│cap=4│  ← slice header for b (shares backing array)
└──┬──┴─────┴─────┘
   │ (points to a[1])
```

So `append(a, x)` can affect `b` if `a` has spare capacity. Use full slice expression `a[:len(a):len(a)]` to set cap == len and force new allocation on append.

## Subslice Retains Full Backing Array

Subslice retention: MUST use `slices.Clone` or `copy` when keeping small slice from large backing array. Slicing large slice for small piece prevents GC of entire backing array:

```go
// ✗ Bad — small keeps the entire 1MB array alive
func getHeader(data []byte) []byte {
    return data[:64] // shares backing array with data
}

// ✓ Good — copy to release the large array
func getHeader(data []byte) []byte {
    header := make([]byte, 64)
    copy(header, data[:64])
    return header
}

// ✓ Good (Go 1.21+) — use slices.Clone
import "slices"

func getHeader(data []byte) []byte {
    return slices.Clone(data[:64])
}
```

## Standard Library Clone Helpers (Go 1.21+)

```go
import (
    "maps"
    "slices"
)

// Shallow copy a slice
clone := slices.Clone(original)

// Shallow copy a map
clone := maps.Clone(original)
```

Preferred way to make defensive copies. Handle nil inputs correctly (return nil, not empty collection).

## Map Iteration Order

Map iteration order MUST NOT be depended upon. Runtime randomizes it:

```go
// ✗ Bad — output order changes between runs
m := map[string]int{"a": 1, "b": 2, "c": 3}
for k, v := range m {
    fmt.Printf("%s=%d ", k, v) // could be "b=2 a=1 c=3" or any permutation
}

// ✓ Good (Go 1.23+) — sort keys when order matters
keys := slices.Sorted(maps.Keys(m))
for _, k := range keys {
    fmt.Printf("%s=%d ", k, m[k])
}
```

## Deleting During Iteration

### Maps — safe

Deleting map entries during `range` is explicitly safe in Go:

```go
// ✓ Safe — defined behavior
for k, v := range m {
    if shouldDelete(v) {
        delete(m, k) // safe during range
    }
}
```

### Slices — needs care

Deleting from slice during iteration needs index management:

```go
// ✗ Bad — skips elements after deletion
for i, v := range items {
    if shouldDelete(v) {
        items = append(items[:i], items[i+1:]...) // shifts elements, next iteration skips one
    }
}

// ✓ Good — iterate backwards
for i := len(items) - 1; i >= 0; i-- {
    if shouldDelete(items[i]) {
        items = append(items[:i], items[i+1:]...)
    }
}

// ✓ Good (Go 1.21+) — use slices.DeleteFunc
items = slices.DeleteFunc(items, shouldDelete)
```

## Comparing Slices and Maps

Slice/map comparison MUST use `slices.Equal`/`maps.Equal` (Go 1.21+), NEVER `==` (doesn't compile for slices):

```go
import (
    "maps"
    "slices"
)

// ✓ Good (Go 1.21+)
slices.Equal(a, b)      // element-wise comparison
maps.Equal(m1, m2)      // key-value comparison

// For custom comparison
slices.EqualFunc(a, b, func(x, y Item) bool {
    return x.ID == y.ID
})
```

→ See `samber/cc-skills-golang@golang-modernize` skill for Go 1.22+ loop variable semantics.
