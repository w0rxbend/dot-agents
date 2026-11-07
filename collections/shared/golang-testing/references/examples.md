# Examples as Documentation

Examples are executable documentation: `go test` runs them and compares stdout to `// Output:` comment; `pkg.go.dev` renders them beside documented symbol. Example drifting from API fails build, unlike README code block.

```go
func ExampleCalculatePrice() {
    price := CalculatePrice(100, 10.0)
    fmt.Printf("Price: %.2f\n", price)
    // Output: Price: 900.00
}

func ExampleCalculatePrice_singleItem() {
    price := CalculatePrice(1, 25.50)
    fmt.Printf("Price: %.2f\n", price)
    // Output: Price: 25.50
}
```

## Naming

Suffix decides where godoc attaches example; typo silently detaches it from its symbol:

| Function name               | Documents                     |
| --------------------------- | ----------------------------- |
| `Example()`                 | Package itself                |
| `ExampleCalculatePrice()`   | `CalculatePrice` function     |
| `ExampleStore_Get()`        | `Get` method of `Store`       |
| `ExampleStore_Get_cached()` | Named variant of same method  |

Suffix after second underscore MUST start lowercase. Otherwise Go reads it as type or method name and orphans example.

## Output directives

- `// Output:` — stdout MUST match exactly (leading/trailing whitespace is trimmed).
- `// Unordered output:` — lines may arrive in any order. Use for map iteration and concurrent producers (no stable order).
- **No output comment** — example compiles but does not run. Fits code needing live dependency, but stops verifying behavior; prefer real output assertion.

## Placement

Examples live in `_test.go` files, in `package foo_test` external test package. Example compiling only against exported API proves public surface is usable, which is its point.
