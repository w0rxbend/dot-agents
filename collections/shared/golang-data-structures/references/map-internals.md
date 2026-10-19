# Map Internals Deep Dive

## Hash Table Structure (Go 1.24+: Swiss tables)

Since Go 1.24 the runtime implements maps as [Swiss tables](https://go.dev/blog/swisstable) (`internal/runtime/maps`). Check `go.mod`'s `go`/`toolchain` line before relying on details below.

- **Groups**: slots are organized in groups of 8. Each group has an 8-byte control word, one control byte per slot, holding 7 bits of the key's hash (or an empty/deleted marker). A lookup compares all 8 control bytes at once and only compares full keys for matching slots.
- **Open addressing**: there are no overflow chains. A lookup probes groups in a quadratic sequence until it finds the key or an empty slot.
- **Small maps**: a map with at most 8 entries is a single group, with no table or directory.
- **Directory of tables**: larger maps are a directory of independent tables, each with a bounded capacity (1024 slots in the current implementation). A full table grows by itself, or splits into two (extendible hashing). Growth therefore touches one bounded table at a time instead of rehashing the whole map, which keeps the worst-case latency of a single insert low.
- **Load factor**: a table grows when it would exceed 7/8 full.
- **No shrinking**: `delete` marks slots deleted or empty but never releases table memory. To reclaim memory from a map that was once large, build a new map and copy the surviving entries.
- **No `cap()` function**: use `make(map[K]V, hint)` to size it up front.

Exact constants are runtime internals and can change between releases; do not write code that depends on them.

### Before Go 1.24 (classic buckets)

Older toolchains used buckets of 8 key/value pairs (keys and values in separate arrays), overflow bucket chains, a load factor of 6.5 entries per bucket, power-of-two bucket doubling, and incremental evacuation from old to new buckets during growth.

## Preallocation

```go
// Without preallocation — multiple growths as entries are added
m := map[string]int{}

// With preallocation — sizes the map for expectedSize entries upfront
m := make(map[string]int, expectedSize)
```

Preallocation avoids repeated growths. The hint is approximate: the runtime allocates enough capacity for `hint` entries under its load factor.

## Pointers vs Values

For large value types, storing pointers reduces copy overhead:

```go
// Large struct — copied on every read/write
m := map[string]BigStruct{}  // copies large struct

// Pointer — only pointer is copied
m := map[string]*BigStruct{} // copies 8-byte pointer
```

Trade-off: pointer maps add GC pressure. For small structs (< 128 bytes), value maps are typically faster.

## `maps` Package (Go 1.21+)

| Function | Description |
| --- | --- |
| `Clone`, `Equal`, `EqualFunc` | Shallow copy and equality comparison |
| `Keys`, `Values`, `All` (1.23+) | Iterators over keys, values, or pairs |
| `Collect`, `Insert` (1.23+) | Build maps from iterators or insert entries |

See `samber/cc-skills-golang@golang-safety` skill for `Clone`, `Equal`, and sorted iteration patterns.

## Map Key Requirements

Map keys must be comparable (`==` must work). This includes:

- All numeric types, `string`, `bool`
- Pointers, channels, interfaces (compared by identity)
- Arrays of comparable types
- Structs where all fields are comparable

Slices, maps, and functions **cannot** be map keys.
