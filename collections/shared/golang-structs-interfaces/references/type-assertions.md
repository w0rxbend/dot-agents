# Type Assertions & Type Switches

## Safe Type Assertion

Type assertions MUST use comma-ok form. Single-value form panics when dynamic type does not match, turning recoverable branch into crash:

```go
// Good — safe
s, ok := val.(string)
if !ok {
    // handle
}

// Bad — panics if val is not a string
s := val.(string)
```

## Type Switch

Discover interface value's dynamic type:

```go
switch v := val.(type) {
case string:
    fmt.Println(v)
case int:
    fmt.Println(v * 2)
case io.Reader:
    io.Copy(os.Stdout, v)
default:
    fmt.Printf("unexpected type %T\n", v)
}
```

Cases evaluate in order: put concrete types before interface types. Concrete type after an interface it satisfies is unreachable.

`nil` interface value matches `case nil`, not `default`. Add that case explicitly when nil is valid input. Otherwise nil silently falls to `default` and gets reported as unexpected type.

## Optional Behavior with Type Assertions

Check for extra capabilities without requiring them upfront. Declared parameter type stays minimal; richer implementations still exploited:

```go
type Flusher interface {
    Flush() error
}

func writeData(w io.Writer, data []byte) error {
    if _, err := w.Write(data); err != nil {
        return err
    }
    // Flush only if the writer supports it
    if f, ok := w.(Flusher); ok {
        return f.Flush()
    }
    return nil
}
```

Standard library uses this pattern widely (e.g., `http.Flusher`, `io.ReaderFrom`, `io.WriterTo`).

## Asserting to an Interface, not a Concrete Type

Assert to smallest interface carrying needed behavior, not concrete type. Asserting to `*os.File` binds code to one implementation; asserting to `interface{ Sync() error }` accepts every type that can do the job.

## Errors

Error inspection has dedicated helpers: `errors.As` walks wrap chain, plain type assertion does not. Bare `err.(*MyError)` misses error wrapped with `%w` anywhere up the stack.

→ See `samber/cc-skills-golang@golang-error-handling` skill for error wrapping and inspection.
