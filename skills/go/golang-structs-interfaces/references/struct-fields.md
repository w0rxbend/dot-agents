# Struct Fields: Tags and Copy Safety

## Struct Field Tags

Exported fields in serialized structs MUST have field tags. Without tag, encoder uses Go field name; renaming field silently changes wire format:

```go
type Order struct {
    ID        string    `json:"id"         db:"id"`
    UserID    string    `json:"user_id"    db:"user_id"`
    Total     float64   `json:"total"      db:"total"`
    Items     []Item    `json:"items"      db:"-"`
    CreatedAt time.Time `json:"created_at" db:"created_at"`
    DeletedAt time.Time `json:"-"          db:"deleted_at"`
    Internal  string    `json:"-"          db:"-"`
}
```

| Directive               | Meaning                                     |
| ----------------------- | ------------------------------------------- |
| `json:"name"`           | Field name in JSON output                   |
| `json:"name,omitempty"` | Omit field if zero value                    |
| `json:"name,omitzero"`  | Omit field if zero (Go 1.24+, type-aware)   |
| `json:"-"`              | Always exclude from JSON                    |
| `json:"-,"`             | Field literally named `-`                   |
| `json:",string"`        | Encode number/bool as JSON string           |
| `db:"column"`           | Database column mapping (sqlx, etc.)        |
| `yaml:"name"`           | YAML field name                             |
| `xml:"name,attr"`       | XML attribute                               |
| `validate:"required"`   | Struct validation (go-playground/validator) |

Notes that bite in production:

- **Unexported fields are never serialized**, tag or not. Their tags are dead weight; `go vet` flags only malformed ones.
- **`omitempty` is length/zero based, not semantic.** Drops `0`, `""`, `false`: explicit "zero" indistinguishable from "absent". Use pointer, `mo.Option[T]`, or `omitzero` (Go 1.24+) when difference matters.
- **Tag syntax is unchecked at compile time.** Missing backtick or `json: "id"` with stray space yields silently ignored tag. Run `go vet`'s `structtag` analyzer in CI to catch malformed tags.

**Diagnose:** 1- `go vet ./...` — `structtag` analyzer reports malformed or duplicated tags 2- round-trip test: marshal, unmarshal, compare — catches field-name drift compiler cannot see

## Preventing Struct Copies with `noCopy`

Some structs must never be copied after first use (e.g., holding mutex, channel, or internal pointers). Copy duplicates lock state: two goroutines guard two different mutexes, invariant silently gone. Embed `noCopy` sentinel so `go vet` catches accidental copies:

```go
// noCopy may be added to structs which must not be copied after first use.
// See https://pkg.go.dev/sync#noCopy
type noCopy struct{}

func (*noCopy) Lock()   {}
func (*noCopy) Unlock() {}

type ConnPool struct {
    noCopy noCopy
    mu     sync.Mutex
    conns  []*Conn
}
```

`go vet` reports error when `ConnPool` value is copied (passed by value, assigned, returned by value, ranged over). Detection is purely name-based: `vet`'s `copylocks` analyzer flags any type whose fields implement `Lock`/`Unlock`. Standard library does same for `sync.WaitGroup`, `sync.Mutex`, `strings.Builder`, others.

Pass these structs by pointer:

```go
// Good
func process(pool *ConnPool) { ... }

// Bad — go vet will flag this
func process(pool ConnPool) { ... }
```

**Diagnose:** 1- `go vet ./...` — `copylocks` reports every value copy of a lock-bearing struct 2- `go test -race ./...` — surfaces data races a silent copy introduces
