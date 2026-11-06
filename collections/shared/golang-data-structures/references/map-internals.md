# Map Internals Deep Dive

## Hash Table Structure (Go 1.24+: Swiss tables)

Since Go 1.24, runtime implements maps as [Swiss tables](https://go.dev/blog/swisstable) (`internal/runtime/maps`). Check `go.mod`'s `go`/`toolchain` line before relying on details below.

- **Groups**: slots in groups of 8. Each group has 8-byte control word: one control byte per slot, holding 7 bits of key's hash (or empty/deleted marker). Lookup compares all 8 control bytes at once, then full keys only for matching slots.
- **Open addressing**: no overflow chains. Lookup probes groups in quadratic sequence until it finds key or empty slot.
- **Small maps**: map with at most 8 entries is single group, with no table or directory.
- **Directory of tables**: larger maps are directory of independent tables, each with bounded capacity (1024 slots in current implementation). Full table grows alone or splits in two (extendible hashing). Growth touches one bounded table at a time instead of rehashing whole map. Keeps worst-case single-insert latency low.
- **Load factor**: table grows when it would exceed 7/8 full.
- **No shrinking**: `delete` marks slots deleted or empty but never releases table memory. To reclaim memory from once-large map, build new map and copy surviving entries.
- **No `cap()` function**: use `make(map[K]V, hint)` to size up front.

Exact constants are runtime internals; they can change between releases. Do not write code that depends on them.

### Before Go 1.24 (classic buckets)

Older toolchains used: buckets of 8 key/value pairs (keys and values in separate arrays), overflow bucket chains, load factor of 6.5 entries per bucket, power-of-two bucket doubling, incremental evacuation from old to new buckets during growth.

## Preallocation

```go
// Without preallocation — multiple growths as entries are added
m := map[string]int{}

// With preallocation — sizes the map for expectedSize entries upfront
m := make(map[string]int, expectedSize)
```

Hint is approximate: runtime allocates enough capacity for `hint` entries under its load factor.

## Pointers vs Values

For large value types, pointers cut copy overhead:

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

See `samber/cc-skills-golang@golang-safety` skill for `Clone`, `Equal`, sorted iteration patterns.

## Map Key Requirements

Map keys must be comparable (`==` must work). Includes:

- All numeric types, `string`, `bool`
- Pointers, channels, interfaces (compared by identity)
- Arrays of comparable types
- Structs where all fields are comparable

Slices, maps, and functions **cannot** be map keys.
