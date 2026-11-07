# Code Style Details

## Extract Complex Conditions

When `if` conditions span multiple operands, extract named booleans:

```go
// Good — self-documenting
isAdmin := user.Role == RoleAdmin
isOwner := resource.OwnerID == user.ID
hasOverride := permissions.Contains(PermOverride)
if isAdmin || isOwner || hasOverride {
    allow()
}

// Bad — wall of logic
if user.Role == RoleAdmin || resource.OwnerID == user.ID || permissions.Contains(PermOverride) {
    allow()
}
```

**Exception:** if last condition is expensive, keep it inline for short-circuit evaluation:

```go
// Good — avoid expensive operation when possible
if isAdmin || isOwner || expensivePermissionCheck(user, resource) {
    allow()
}

// Wasteful — always runs expensive check
canOverride := expensivePermissionCheck(user, resource)
if isAdmin || isOwner || canOverride {
    allow()
}
```

## Value vs Pointer Arguments

Covers **function parameters**, not method receivers (receiver rules: `samber/cc-skills-golang@golang-structs-interfaces` skill).

Pass small, fixed-size types by value — strings are already (pointer, length) pairs internally:

```go
// Good — value types by value
func FormatUser(name string, age int, createdAt time.Time) string

// Good — pointer for mutation
func PopulateDefaults(cfg *Config)

// Good — pointer when nil is meaningful (optional field update)
func UpdateUser(ctx context.Context, id string, name *string) error

// Bad — pointer for no reason
func Greet(name *string) string
```

**When to use pointers**:

- Function **mutates** value
- Struct is **large** (~128+ bytes) — avoids copying
- **Nil is meaningful** (optional/nullable parameter)

**When NOT to use pointers**:

- `string`, `int`, `bool`, `float64`, `time.Time` — pass by value
- Read-only access to small structs — pass by value (better cache locality)
- "Just to save memory" — value copy negligible; stack allocation fast

**Memory access trade-offs when performance is critical**:

- **Values (no pointer)**: stack allocation, excellent CPU cache locality for small types, zero indirection. Slower only when copying large structs.
- **Pointers**: one extra dereference (negligible on modern CPUs), but risk cache misses if pointed-to data isn't cached. Essential for large structs (>~128 bytes) where copy cost dominates.
- **Rule of thumb**: read-only structs <~128 bytes: values usually faster (cache locality). Mutation or large structs: pointers win. In doubt, benchmark.
