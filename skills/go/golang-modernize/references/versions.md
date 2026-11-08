# Go Version Modernizations

## Table of Contents

- [Go 1.21 Modernizations (August 2023)](#go-121-modernizations-august-2023)
  - [Use built-in `min`, `max`, `clear` _(Go 1.21+)_](#use-built-in-min-max-clear-go-121)
  - [Use `log/slog` instead of third-party loggers _(Go 1.21+)_](#use-logslog-instead-of-third-party-loggers-go-121)
  - [Use `slices` package instead of `sort` and manual loops _(Go 1.21+)_](#use-slices-package-instead-of-sort-and-manual-loops-go-121)
  - [Use `maps` package _(Go 1.21+)_](#use-maps-package-go-121)
  - [Use `cmp.Or` for default values _(Go 1.22+)_](#use-cmpor-for-default-values-go-122)
  - [Use `sync.OnceFunc`, `sync.OnceValue`, `sync.OnceValues` _(Go 1.21+)_](#use-synconcefunc-synconcevalue-synconcevalues-go-121)
  - [Use enhanced `context` functions _(Go 1.21+)_](#use-enhanced-context-functions-go-121)
- [Go 1.22 Modernizations (February 2024)](#go-122-modernizations-february-2024)
  - [SHOULD use `range` over integers _(Go 1.22+)_](#should-use-range-over-integers-go-122)
  - [Remove loop variable shadow copies _(Go 1.22+)_](#remove-loop-variable-shadow-copies-go-122)
  - [`math/rand` MUST be replaced with `math/rand/v2` _(Go 1.22+)_](#mathrand-must-be-replaced-with-mathrandv2-go-122)
  - [Use enhanced `net/http` routing _(Go 1.22+)_](#use-enhanced-nethttp-routing-go-122)
  - [Use `strings.CutPrefix` and `strings.CutSuffix` _(Go 1.20+)_](#use-stringscutprefix-and-stringscutsuffix-go-120)
  - [Use `reflect.TypeFor[T]()` _(Go 1.22+)_](#use-reflecttypefort-go-122)
  - [Use `database/sql.Null[T]` _(Go 1.22+)_](#use-databasesqlnullt-go-122)
- [Go 1.23 Modernizations (August 2024)](#go-123-modernizations-august-2024)
  - [Use iterators (`range` over functions) _(Go 1.23+)_](#use-iterators-range-over-functions-go-123)
  - [Use iterator-based `slices` and `maps` functions _(Go 1.23+)_](#use-iterator-based-slices-and-maps-functions-go-123)
  - [Use `unique` package for value interning _(Go 1.23+)_](#use-unique-package-for-value-interning-go-123)
  - [Timer/Ticker behavior change _(Go 1.23+)_](#timerticker-behavior-change-go-123)
- [Go 1.24 Modernizations (February 2025)](#go-124-modernizations-february-2025)
  - [Use generic type aliases _(Go 1.24+)_](#use-generic-type-aliases-go-124)
  - [Use `os.Root` for directory-scoped file access _(Go 1.24+)_](#use-osroot-for-directory-scoped-file-access-go-124)
  - [Use `omitzero` JSON tag _(Go 1.24+)_](#use-omitzero-json-tag-go-124)
  - [Use `strings.SplitSeq`, `strings.FieldsSeq`, `strings.Lines` _(Go 1.24+)_](#use-stringssplitseq-stringsfieldsseq-stringslines-go-124)
  - [`t.Context()` SHOULD replace manual `context.Background()` in tests _(Go 1.24+)_](#tcontext-should-replace-manual-contextbackground-in-tests-go-124)
  - [`b.Loop()` MUST be used in benchmarks _(Go 1.24+)_](#bloop-must-be-used-in-benchmarks-go-124)
  - [Use `runtime.AddCleanup` instead of `runtime.SetFinalizer` _(Go 1.24+)_](#use-runtimeaddcleanup-instead-of-runtimesetfinalizer-go-124)
  - [Use `weak` package for weak references _(Go 1.24+)_](#use-weak-package-for-weak-references-go-124)
  - [Use `crypto/sha3`, `crypto/hkdf`, `crypto/pbkdf2` _(Go 1.24+)_](#use-cryptosha3-cryptohkdf-cryptopbkdf2-go-124)
  - [Use tool directives in `go.mod` _(Go 1.24+)_](#use-tool-directives-in-gomod-go-124)
  - [Use `fmt.Appendf`, `fmt.Appendln` _(Go 1.19+, often overlooked)_](#use-fmtappendf-fmtappendln-go-119-often-overlooked)
- [Go 1.25 Modernizations (August 2025)](#go-125-modernizations-august-2025)
  - [Use `sync.WaitGroup.Go` _(Go 1.25+)_](#use-syncwaitgroupgo-go-125)
  - [Use `testing/synctest` for concurrent code testing _(Go 1.25+, experimental in 1.24)_](#use-testingsynctest-for-concurrent-code-testing-go-125-experimental-in-124)
  - [Use `runtime/trace.FlightRecorder` _(Go 1.25+)_](#use-runtimetraceflightrecorder-go-125)
  - [Container-aware `GOMAXPROCS` _(Go 1.25+)_](#container-aware-gomaxprocs-go-125)
  - [`encoding/json/v2` — introduced experimental _(Go 1.25+, GOEXPERIMENT=jsonv2)_](#encodingjsonv2--introduced-experimental-go-125-goexperimentjsonv2)
  - [Go 1.25 additions to prefer when target allows](#go-125-additions-to-prefer-when-target-allows)
- [Go 1.26 Modernizations (February 2026)](#go-126-modernizations-february-2026)
  - [Use `errors.AsType[T]()` _(Go 1.26+)_](#use-errorsastypet-go-126)
  - [Use enhanced `new()` _(Go 1.26+)_](#use-enhanced-new-go-126)
  - [Use `crypto/hpke` _(Go 1.26+)_](#use-cryptohpke-go-126)
  - [Use RSA-OAEP or HPKE instead of new PKCS#1 v1.5 encryption _(Go 1.26+)_](#use-rsa-oaep-or-hpke-instead-of-new-pkcs1-v15-encryption-go-126)
  - [Green Tea GC enabled by default _(Go 1.26+)_](#green-tea-gc-enabled-by-default-go-126)
  - [Go 1.26+ test artifacts](#go-126-test-artifacts)
  - [Go 1.26+ slog multi-handler](#go-126-slog-multi-handler)
  - [Go 1.26+ ReverseProxy](#go-126-reverseproxy)
  - [Small Go 1.26+ API preferences](#small-go-126-api-preferences)
  - [Go 1.26+ goroutine leak profile](#go-126-goroutine-leak-profile)
  - [Go 1.26+ documentation command](#go-126-documentation-command)
  - [Go 1.26+ module target note](#go-126-module-target-note)
  - [Modernized `go fix` _(Go 1.26+)_](#modernized-go-fix-go-126)
- [Go 1.27 Modernizations (August 2026)](#go-127-modernizations-august-2026)
  - [Use generic methods to scope generics to a type _(Go 1.27+)_](#use-generic-methods-to-scope-generics-to-a-type-go-127)
  - [Use `strings.CutLast` and `bytes.CutLast` instead of `LastIndex` slicing _(Go 1.27+)_](#use-stringscutlast-and-bytescutlast-instead-of-lastindex-slicing-go-127)
  - [Use `net/url` `URL.Clone()` and `Values.Clone()` _(Go 1.27+)_](#use-neturl-urlclone-and-valuesclone-go-127)
  - [Use `math/big.Int.Divide` for rounding-mode division _(Go 1.27+)_](#use-mathbigintdivide-for-rounding-mode-division-go-127)
  - [Use stdlib `uuid` instead of a UUID dependency _(Go 1.27+)_](#use-stdlib-uuid-instead-of-a-uuid-dependency-go-127)
  - [Migrate to `encoding/json/v2` — default since Go 1.27 _(Go 1.27+)_](#migrate-to-encodingjsonv2--default-since-go-127-go-127)
  - [Use `testing/synctest.Sleep()` inside a synctest bubble _(Go 1.27+)_](#use-testingsynctestsleep-inside-a-synctest-bubble-go-127)
  - [Use `net/http/httptest.NewTestServer()` for in-memory server tests _(Go 1.27+)_](#use-nethttphttptestnewtestserver-for-in-memory-server-tests-go-127)
  - [`runtime/pprof` `goroutineleak` profile is generally available _(Go 1.27+)_](#runtimepprof-goroutineleak-profile-is-generally-available-go-127)
  - [`go fix` gains new modernizers _(Go 1.27+)_](#go-fix-gains-new-modernizers-go-127)
  - [`go test` runs the `stdversion` vet check _(Go 1.27+)_](#go-test-runs-the-stdversion-vet-check-go-127)
  - [`go mod tidy` merges duplicate require blocks _(Go 1.27+)_](#go-mod-tidy-merges-duplicate-require-blocks-go-127)
  - [Small Go 1.27+ API preferences](#small-go-127-api-preferences)
  - [Go 1.27+ version-bump risk checklist (verify, don't rewrite)](#go-127-version-bump-risk-checklist-verify-dont-rewrite)
- [General Modernization (Any Version)](#general-modernization-any-version)
  - [Code MUST use `any` instead of `interface{}` _(Go 1.18+)_](#code-must-use-any-instead-of-interface-go-118)
  - [Use generics instead of `interface{}` + type assertions _(Go 1.18+)_](#use-generics-instead-of-interface--type-assertions-go-118)
  - [Use `errors.Join` instead of multi-error libraries _(Go 1.20+)_](#use-errorsjoin-instead-of-multi-error-libraries-go-120)
  - [Use `net.JoinHostPort` instead of `fmt.Sprintf` _(any version)_](#use-netjoinhostport-instead-of-fmtsprintf-any-version)

## Go 1.21 Modernizations (August 2023)

Changelog: <https://go.dev/doc/go1.21>

### Use built-in `min`, `max`, `clear` _(Go 1.21+)_

Remove custom implementations. `min`/`max` work with any ordered type, accept variadic arguments:

```go
// Before
func minInt(a, b int) int {
    if a < b { return a }
    return b
}
x := minInt(a, b)

// After (Go 1.21+)
x := min(a, b)
smallest := min(a, b, c, d)
```

`clear` zeroes maps and slices:

```go
// Before
for k := range m { delete(m, k) }

// After (Go 1.21+)
clear(m)
```

### Use `log/slog` instead of third-party loggers _(Go 1.21+)_

`log/slog`: standard structured logging. New code SHOULD migrate to `slog` over `zap`, `logrus`, or `zerolog`.

```go
// Before: zap
logger, _ := zap.NewProduction()
logger.Info("request handled", zap.String("method", r.Method), zap.Int("status", status))

// Before: logrus
logrus.WithFields(logrus.Fields{"method": r.Method, "status": status}).Info("request handled")

// After (Go 1.21+): slog
slog.Info("request handled", "method", r.Method, "status", status)
// Or with type-safe attributes:
slog.Info("request handled", slog.String("method", r.Method), slog.Int("status", status))
```

**Migration guidance**: optional for existing projects heavily invested in third-party loggers; new projects prefer `slog`. `samber/slog-*` handlers route slog output to various backends. Go 1.24 added `slog.DiscardHandler` for silent loggers.

### Use `slices` package instead of `sort` and manual loops _(Go 1.21+)_

```go
// Before
sort.Strings(names)
sort.Slice(users, func(i, j int) bool { return users[i].Name < users[j].Name })

// After (Go 1.21+)
slices.Sort(names)
slices.SortFunc(users, func(a, b User) int { return cmp.Compare(a.Name, b.Name) })
```

```go
// Before: manual search
found := false
for _, v := range items { if v == target { found = true; break } }

// After (Go 1.21+)
found := slices.Contains(items, target)
```

```go
// Before: manual clone
clone := append([]string(nil), original...)

// After (Go 1.21+)
clone := slices.Clone(original)
```

### Use `maps` package _(Go 1.21+)_

```go
// Before
clone := make(map[string]int, len(original))
for k, v := range original { clone[k] = v }

// After (Go 1.21+)
clone := maps.Clone(original)
```

### Use `cmp.Or` for default values _(Go 1.22+)_

```go
// Before
addr := os.Getenv("ADDR")
if addr == "" { addr = ":8080" }

// After (Go 1.22+)
addr := cmp.Or(os.Getenv("ADDR"), ":8080")
```

### Use `sync.OnceFunc`, `sync.OnceValue`, `sync.OnceValues` _(Go 1.21+)_

```go
// Before
var (
    once   sync.Once
    client *http.Client
)
func getClient() *http.Client {
    once.Do(func() { client = &http.Client{Timeout: 10 * time.Second} })
    return client
}

// After (Go 1.21+)
var getClient = sync.OnceValue(func() *http.Client {
    return &http.Client{Timeout: 10 * time.Second}
})
```

### Use enhanced `context` functions _(Go 1.21+)_

```go
ctx := context.WithoutCancel(parent)          // detach from parent cancellation
ctx, cancel := context.WithTimeoutCause(parent, 5*time.Second, errTimeout)
ctx, cancel := context.WithDeadlineCause(parent, deadline, errDeadline)
stop := context.AfterFunc(ctx, func() { cleanup() })
```

---

## Go 1.22 Modernizations (February 2024)

Changelog: <https://go.dev/doc/go1.22>

### SHOULD use `range` over integers _(Go 1.22+)_

```go
// Before
for i := 0; i < n; i++ { process(i) }

// After (Go 1.22+)
for i := range n { process(i) }

// When index isn't needed
for range 10 { fmt.Println("hello") }
```

### Remove loop variable shadow copies _(Go 1.22+)_

Go 1.22 changed loop variable semantics: new variable per iteration. Loop variable captures (`v := v`) SHOULD be removed in Go 1.22+ codebases.

**Requirement**: `go` directive in `go.mod` must be `go 1.22` or later.

```go
// Before (Go < 1.22)
for _, v := range items {
    v := v // shadow copy to avoid closure bug
    go func() { process(v) }()
}

// After (Go 1.22+): safe by default
for _, v := range items {
    go func() { process(v) }()
}
```

### `math/rand` MUST be replaced with `math/rand/v2` _(Go 1.22+)_

```go
// Before
import "math/rand"
rand.Seed(time.Now().UnixNano()) // no longer needed
n := rand.Intn(100)

// After (Go 1.22+)
import "math/rand/v2"
n := rand.IntN(100) // IntN, not Intn
```

Key `math/rand/v2` changes:

- No global seed needed; seeded automatically
- `Intn` -> `IntN`, `Int63n` -> `Int64N` (renamed)
- `rand.N[T]()` generic function for any integer type
- Better algorithms (ChaCha8, PCG)
- `Read` removed; use `crypto/rand` for random bytes

### Use enhanced `net/http` routing _(Go 1.22+)_

```go
// Before: gorilla/mux or chi
r := mux.NewRouter()
r.HandleFunc("/users/{id}", getUser).Methods("GET")

// After (Go 1.22+): stdlib
mux := http.NewServeMux()
mux.HandleFunc("GET /users/{id}", getUser)

func getUser(w http.ResponseWriter, r *http.Request) {
    id := r.PathValue("id")
}
```

### Use `strings.CutPrefix` and `strings.CutSuffix` _(Go 1.20+)_

```go
// Before
if strings.HasPrefix(s, "Bearer ") {
    token := strings.TrimPrefix(s, "Bearer ")
}

// After (Go 1.20+)
if token, ok := strings.CutPrefix(s, "Bearer "); ok {
    // use token
}
```

### Use `reflect.TypeFor[T]()` _(Go 1.22+)_

```go
// Before
t := reflect.TypeOf((*MyInterface)(nil)).Elem()

// After (Go 1.22+)
t := reflect.TypeFor[MyInterface]()
```

### Use `database/sql.Null[T]` _(Go 1.22+)_

```go
// Before
var name sql.NullString
var age  sql.NullInt64

// After (Go 1.22+)
var name sql.Null[string]
var age  sql.Null[int64]
```

---

## Go 1.23 Modernizations (August 2024)

Changelog: <https://go.dev/doc/go1.23>

### Use iterators (`range` over functions) _(Go 1.23+)_

Go 1.23 added range-over-func with `iter` package:

```go
// Before: collect all results into a slice
func AllUsers(db *sql.DB) ([]User, error) {
    rows, err := db.Query("SELECT ...")
    if err != nil { return nil, err }
    defer rows.Close()
    var users []User
    for rows.Next() {
        var u User
        rows.Scan(&u.ID, &u.Name)
        users = append(users, u)
    }
    return users, rows.Err()
}

// After (Go 1.23+): lazy iteration
func AllUsers(db *sql.DB) iter.Seq2[User, error] {
    return func(yield func(User, error) bool) {
        rows, err := db.Query("SELECT ...")
        if err != nil { yield(User{}, err); return }
        defer rows.Close()
        for rows.Next() {
            var u User
            if err := rows.Scan(&u.ID, &u.Name); err != nil {
                yield(User{}, err); return
            }
            if !yield(u, nil) { return }
        }
        if err := rows.Err(); err != nil { yield(User{}, err) }
    }
}
```

### Use iterator-based `slices` and `maps` functions _(Go 1.23+)_

```go
// Sorted keys via iterator
for k := range slices.Sorted(maps.Keys(m)) {
    fmt.Println(k, m[k])
}

// Collect iterator into slice
users := slices.Collect(maps.Values(userMap))

// Chunk a slice into batches
for chunk := range slices.Chunk(items, 100) {
    processBatch(chunk)
}
```

### Use `unique` package for value interning _(Go 1.23+)_

```go
// Before: manual string interning
var mu sync.Mutex
var interned = make(map[string]string)

// After (Go 1.23+)
handle := unique.Make(s)  // Handle[string], comparable, memory-efficient
s = handle.Value()
```

### Timer/Ticker behavior change _(Go 1.23+)_

With `go 1.23` or later in `go.mod`:

- `time.Timer` and `time.Ticker` are garbage collected without calling `Stop()`
- Timer channels now unbuffered (capacity 0, was 1)

Remove unneeded `Stop()` calls in defer patterns where timer goes out of scope.

---

## Go 1.24 Modernizations (February 2025)

Changelog: <https://go.dev/doc/go1.24>

### Use generic type aliases _(Go 1.24+)_

```go
// Now valid (Go 1.24+)
type Set[T comparable] = map[T]struct{}
type Result[T any] = struct { Value T; Err error }
```

### Use `os.Root` for directory-scoped file access _(Go 1.24+)_

**Security-critical**: `os.Root` prevents path traversal attacks (CWE-22) at OS level. For user-supplied paths, replace all manual `filepath.Clean` + `strings.HasPrefix` validation with `os.Root`. Rejects symlinks resolving outside root. Supports `Open`, `Create`, `Stat`, `OpenFile`, `Mkdir`, `Remove`, and more.

```go
// Before: manual path validation (risk of path traversal)
path := filepath.Join(baseDir, userInput)
data, err := os.ReadFile(path)

// After (Go 1.24+): safe directory-scoped access
root, err := os.OpenRoot("/opt/data")
if err != nil { return err }
defer root.Close()
f, err := root.Open(userInput) // cannot escape root directory
```

### Use `omitzero` JSON tag _(Go 1.24+)_

`omitzero` is more correct than `omitempty` for `time.Time`, `bool`, and custom types:

```go
// Before: omitempty doesn't work well for time.Time
type Event struct {
    At time.Time `json:"at,omitempty"` // zero time.Time is NOT omitted
}

// After (Go 1.24+)
type Event struct {
    At time.Time `json:"at,omitzero"` // zero time.Time IS omitted
}
```

### Use `strings.SplitSeq`, `strings.FieldsSeq`, `strings.Lines` _(Go 1.24+)_

Iterator-returning variants avoid allocating `[]string`:

```go
// Before: allocates a []string
parts := strings.Split(csv, ",")
for _, part := range parts { process(part) }

// After (Go 1.24+): lazy, zero-allocation iteration
for part := range strings.SplitSeq(csv, ",") { process(part) }
```

### `t.Context()` SHOULD replace manual `context.Background()` in tests _(Go 1.24+)_

```go
// Before
func TestFoo(t *testing.T) {
    ctx := context.Background()
}

// After (Go 1.24+): auto-cancelled when test ends
func TestFoo(t *testing.T) {
    ctx := t.Context()
}
```

### `b.Loop()` MUST be used in benchmarks _(Go 1.24+)_

```go
// Before
func BenchmarkFoo(b *testing.B) {
    for i := 0; i < b.N; i++ { foo() }
}

// After (Go 1.24+)
func BenchmarkFoo(b *testing.B) {
    for b.Loop() { foo() }
}
```

### Use `runtime.AddCleanup` instead of `runtime.SetFinalizer` _(Go 1.24+)_

```go
// Before
runtime.SetFinalizer(obj, func(o *Object) { o.Close() })

// After (Go 1.24+): more flexible, no cycle issues
runtime.AddCleanup(obj, func(resource Resource) { resource.Close() }, obj.resource)
```

### Use `weak` package for weak references _(Go 1.24+)_

```go
import "weak"

ptr := weak.Make(obj)
if v := ptr.Value(); v != nil {
    // object still alive
}
```

### Use `crypto/sha3`, `crypto/hkdf`, `crypto/pbkdf2` _(Go 1.24+)_

Replace `golang.org/x/crypto` sub-packages with standard library equivalents:

```go
// Before
import "golang.org/x/crypto/sha3"
import "golang.org/x/crypto/hkdf"
import "golang.org/x/crypto/pbkdf2"

// After (Go 1.24+)
import "crypto/sha3"
import "crypto/hkdf"
import "crypto/pbkdf2"
```

### Use tool directives in `go.mod` _(Go 1.24+)_

Use `tool` directives instead of `tools.go` blank imports.

```bash
go get -tool golang.org/x/tools/cmd/stringer@latest
go get -tool github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest
go tool stringer -type=Kind
go tool golangci-lint run ./...
```

`go.mod` shape for module targeting Go 1.26 or newer. Example target, not cap: keep project's actual `go` directive, do not change it solely to add tools.

```go.mod
module example.com/project

go 1.26

tool (
    golang.org/x/tools/cmd/stringer
    github.com/golangci/golangci-lint/v2/cmd/golangci-lint
)
```

`go install tool` installs all module-pinned tools when needed; `go get -u tool` updates them deliberately.

### Use `fmt.Appendf`, `fmt.Appendln` _(Go 1.19+, often overlooked)_

```go
// Before
buf = append(buf, fmt.Sprintf("count: %d", n)...)

// After (Go 1.19+)
buf = fmt.Appendf(buf, "count: %d", n)
```

---

## Go 1.25 Modernizations (August 2025)

Changelog: <https://go.dev/doc/go1.25>

### Use `sync.WaitGroup.Go` _(Go 1.25+)_

```go
// Before
var wg sync.WaitGroup
wg.Add(1)
go func() {
    defer wg.Done()
    process()
}()
wg.Wait()

// After (Go 1.25+)
var wg sync.WaitGroup
wg.Go(func() {
    process()
})
wg.Wait()
```

### Use `testing/synctest` for concurrent code testing _(Go 1.25+, experimental in 1.24)_

```go
// Before
func TestConcurrent(t *testing.T) {
    var count atomic.Int32
    var wg sync.WaitGroup

    wg.Add(1)
    go func() {
        defer wg.Done()
        count.Add(1)
    }()

    wg.Wait()

    // Problem: Race conditions are hard to detect, timing-dependent,
    // and flaky tests are common
    if count.Load() != 1 {
        t.Fatal("expected 1")
    }
}

// After (Go 1.25+)
func TestConcurrent(t *testing.T) {
    synctest.Test(t, func(t *testing.T) {
        var count atomic.Int32
        go func() { count.Add(1) }()
        synctest.Wait() // wait for all goroutines to park
        if count.Load() != 1 { t.Fatal("expected 1") }
    })
}
```

**Note**: Use `synctest.Test` in Go 1.25+ and Go 1.26+. Do not use old Go 1.24 experimental `synctest.Run` API in Go 1.25+ code.

### Use `runtime/trace.FlightRecorder` _(Go 1.25+)_

Lightweight always-on ring-buffer tracing for production:

```go
fr := trace.NewFlightRecorder(trace.FlightRecorderConfig{})
if err := fr.Start(); err != nil {
    return err
}
// ... later, on error:
fr.WriteTo(file) // captures recent trace data
```

### Container-aware `GOMAXPROCS` _(Go 1.25+)_

Go 1.25 automatically respects cgroup CPU limits on Linux. Remove manual workarounds:

```go
// Before: using uber-go/automaxprocs
import _ "go.uber.org/automaxprocs"

// After (Go 1.25+): built-in, remove the import
// GOMAXPROCS is set automatically from cgroup CPU limits
```

### `encoding/json/v2` — introduced experimental _(Go 1.25+, GOEXPERIMENT=jsonv2)_

Major JSON revision, experimental via `GOEXPERIMENT=jsonv2` in Go 1.25–1.26. Default implementation since Go 1.27; see Go 1.27 section below for stable API and migration hazards.

### Go 1.25 additions to prefer when target allows

- `sync.WaitGroup.Go`: simple fire-and-wait goroutines; function must not panic; no errors/cancellation.
- `net/http.CrossOriginProtection`: stdlib helper for cross-origin / CSRF-style protection in HTTP servers.
- `reflect.TypeAssert[T](v)`: prefer over `v.Interface().(T)` in reflection code.
- `os.Root.FS` and additional `os.Root` methods: use for confined filesystem APIs.
- New vet checks: `waitgroup` misuse and manual host:port formatting; prefer `net.JoinHostPort`.

---

## Go 1.26 Modernizations (February 2026)

Changelog: <https://go.dev/doc/go1.26>

### Use `errors.AsType[T]()` _(Go 1.26+)_

```go
// Before
var pathErr *os.PathError
if errors.As(err, &pathErr) {
    fmt.Println(pathErr.Path)
}

// After (Go 1.26+)
if pathErr, ok := errors.AsType[*os.PathError](err); ok {
    fmt.Println(pathErr.Path)
}
```

### Use enhanced `new()` _(Go 1.26+)_

`new(expr)` now accepts value expression and returns pointer to it (not zero-initialized):

```go
// Before: helper function needed
func ptr[T any](v T) *T { return &v }
cfg := Config{Timeout: ptr(30)}

// After (Go 1.26+): new(expr) initializes the value — equivalent to ptr(30)
cfg := Config{Timeout: new(30)} // *int pointing to 30, not 0
```

### Use `crypto/hpke` _(Go 1.26+)_

Hybrid Public Key Encryption (RFC 9180) now in standard library.

### Use RSA-OAEP or HPKE instead of new PKCS#1 v1.5 encryption _(Go 1.26+)_

For new encryption use, avoid `crypto/rsa.EncryptPKCS1v15`. Prefer RSA-OAEP (`rsa.EncryptOAEP` / `rsa.EncryptOAEPWithOptions`) or modern KEM/HPKE design.

### Green Tea GC enabled by default _(Go 1.26+)_

Re-evaluate GC and allocation tuning under Go 1.26 Green Tea GC via profiles and benchmarks; remove legacy tuning only when data supports it. Keep `GOMEMLIMIT` when it reflects real container or service memory ceiling. Remove third-party `automaxprocs` workarounds unless project has measured reason: Go 1.25+ `GOMAXPROCS` is container-aware by default.

### Go 1.26+ test artifacts

Use `t.ArtifactDir()`, `b.ArtifactDir()`, and `f.ArtifactDir()` for test, benchmark, and fuzzer files that should persist for inspection.

### Go 1.26+ slog multi-handler

Simple fan-out to multiple slog handlers: try stdlib `slog.NewMultiHandler` before adding third-party handler-composition dependencies.

### Go 1.26+ ReverseProxy

New reverse proxy code: prefer `httputil.ReverseProxy{Rewrite: ...}`. Do not generate new `Director`-based proxy code unless preserving old compatibility.

```go
proxy := &httputil.ReverseProxy{
    Rewrite: func(pr *httputil.ProxyRequest) {
        pr.SetURL(targetURL)
        pr.SetXForwarded()
    },
}
```

### Small Go 1.26+ API preferences

- Use `bytes.Buffer.Peek(n)` to inspect upcoming bytes without consuming them.
- Use reflect iterators where they simplify code:
  - `reflect.Type.Fields()`
  - `reflect.Type.Methods()`
  - `reflect.Type.Ins()`
  - `reflect.Type.Outs()`
  - `reflect.Value.Fields()`
  - `reflect.Value.Methods()`
- Prefer these over manual `NumField`/`Field(i)` or `NumMethod`/`Method(i)` loops when iterator form is clearer.

### Go 1.26+ goroutine leak profile

Go 1.26 has experimental goroutine leak profile for production-oriented leak investigation, gated by `GOEXPERIMENT=goroutineleakprofile`; do not rely on it as default stable behavior. Generally available since Go 1.27 without experiment flag; see Go 1.27 section.

### Go 1.26+ documentation command

Use `go doc`, not `go tool doc`. Go 1.26 removed old `cmd/doc` / `go tool doc` path.

### Go 1.26+ module target note

With Go 1.26 or newer toolchain, `go mod init` may create module with older default `go` directive. If project intentionally targets Go 1.26+ APIs, update directive deliberately:

```bash
go mod edit -go=1.26
go mod tidy
```

Future Go versions: use project's intended target version. Do not use APIs newer than module's `go` directive until project explicitly agrees to upgrade it.

### Modernized `go fix` _(Go 1.26+)_

Go 1.26 rewrote `go fix` to apply subset of modernize-style analyzers automatically. Check `go tool fix help` for exact coverage; some modernizations still need linting or manual review.

```bash
go fix ./...  # applies the enabled safe transformations
```

---

## Go 1.27 Modernizations (August 2026)

Changelog: <https://go.dev/doc/go1.27>

### Use generic methods to scope generics to a type _(Go 1.27+)_

Go 1.27 lifted restriction dating from generics' arrival in Go 1.18: methods may now declare own type parameters ([go.dev/issue/77273](https://go.dev/issue/77273), [spec: Method declarations](https://go.dev/ref/spec#Method_declarations)). Helper logically belonging to one type no longer needs package-scope generic function. Interface methods still cannot declare type parameters, and generic method cannot satisfy an interface. Keep package-level function when operation must be part of interface contract.

```go
// Before: package-scope generic function, disconnected from the type it serves
func FilterInts[T any](s []T, pred func(T) bool) []T { ... }

// After (Go 1.27+): generic method, scoped to the receiver
func (s Set[T]) Filter[U comparable](pred func(T) U) Set[T] { ... }
```

Reference example: standard library's own `(*rand.Rand).N[Int intType](n Int) Int` (`math/rand/v2`).

### Use `strings.CutLast` and `bytes.CutLast` instead of `LastIndex` slicing _(Go 1.27+)_

```go
// Before: manual index arithmetic — easy to get the offset wrong
if i := strings.LastIndex(path, "/"); i >= 0 {
    dir, file := path[:i], path[i+1:]
}

// After (Go 1.27+)
if dir, file, ok := strings.CutLast(path, "/"); ok {
    // dir, file
}
```

`bytes.CutLast(b, sep []byte) (before, after []byte, found bool)` mirrors `strings.CutLast(s, sep string) (before, after string, found bool)`.

### Use `net/url` `URL.Clone()` and `Values.Clone()` _(Go 1.27+)_

```go
// Before: Values is map[string][]string — a shallow copy shares the slices
clone := url.Values{}
for k, v := range original {
    clone[k] = append([]string(nil), v...)
}

// After (Go 1.27+)
clone := original.Clone()
u2 := u.Clone()
```

### Use `math/big.Int.Divide` for rounding-mode division _(Go 1.27+)_

```go
// Before: sign-correction dance for floor/ceil division
q, r := new(big.Int).QuoRem(x, y, new(big.Int))
if r.Sign() != 0 && (r.Sign() < 0) != (y.Sign() < 0) {
    q.Sub(q, big.NewInt(1))
}

// After (Go 1.27+)
q, r := new(big.Int).Divide(x, y, new(big.Int), big.Floor)
// modes: big.Trunc, big.Floor, big.Round, big.Ceil
```

### Use stdlib `uuid` instead of a UUID dependency _(Go 1.27+)_

```go
// Before
import "github.com/google/uuid"
id := uuid.NewString()

// After (Go 1.27+): no external dependency
import "uuid"
id := uuid.New().String()
```

Stdlib generators (`uuid.New()`, `uuid.NewV4()`, `uuid.NewV7()`) return values without errors. v7 UUIDs are time-ordered; prefer `uuid.NewV7()` for database primary keys where index locality matters. Before dropping dependency, check `go mod why -m github.com/google/uuid` (or `gofrs/uuid`): some codebases depend on v3/v5 namespace UUIDs, SQL `Scanner`/`driver.Valuer` integration, or other RFC-specific variants stdlib package does not (yet) cover.

### Migrate to `encoding/json/v2` — default since Go 1.27 _(Go 1.27+)_

`encoding/json/v2` and `encoding/json/jsontext` now stable (experimental since Go 1.25 via `GOEXPERIMENT=jsonv2`). `encoding/json/v2` is default JSON implementation; `encoding/json` becomes thin wrapper over it; unmarshal significantly faster. New code: prefer v2 API directly:

```go
// Before
data, err := json.Marshal(v)
err = json.Unmarshal(data, &v)

// After (Go 1.27+)
import "encoding/json/v2"
data, err := json.Marshal(v)                 // same names, v2 semantics
err = json.UnmarshalRead(r, &v)              // stream from an io.Reader without a wrapper buffer
```

Use `encoding/json/jsontext` (`Encoder`, `Decoder`, `Token`, `Value`) for syntactic, streaming-level JSON work instead of hand-rolled `json.RawMessage` juggling.

**Migrate deliberately, not blindly. Default got stricter:**

- Duplicate object member names now rejected; v1 silently kept last one.
- Invalid UTF-8 in JSON strings now rejected; v1 replaced it silently.
- `format` and `unknown` struct tags, `DiscardUnknownMembers`, and `SkipFunc` are gone.
- `inline` tag renamed `embed`.
- Roll back with `GOEXPERIMENT=nojsonv2` only as temporary compatibility bridge, not permanent stance. Documented escape hatch, not intended steady state.

### Use `testing/synctest.Sleep()` inside a synctest bubble _(Go 1.27+)_

```go
synctest.Test(t, func(t *testing.T) {
    go worker()
    synctest.Sleep(time.Second) // advances the bubble's fake clock
})
```

### Use `net/http/httptest.NewTestServer()` for in-memory server tests _(Go 1.27+)_

```go
// Before: httptest.Server binds a real socket, forcing real goroutines/timers
srv := httptest.NewServer(handler)
defer srv.Close()

// After (Go 1.27+): in-memory fake network, composes with testing/synctest
synctest.Test(t, func(t *testing.T) {
    srv := httptest.NewTestServer(handler)
    defer srv.Close()
})
```

### `runtime/pprof` `goroutineleak` profile is generally available _(Go 1.27+)_

Goroutine leak profile (experimental behind `GOEXPERIMENT=goroutineleakprofile` in Go 1.26) is now standard `runtime/pprof` profile, also served at `/debug/pprof/goroutineleak`. No build flag required. Reports goroutines blocked on concurrency primitive that can never unblock. Does not detect leaks reachable from global variables or still-runnable goroutines. → See `samber/cc-skills-golang@golang-concurrency` and `samber/cc-skills-golang@golang-troubleshooting` skills for leak investigation use.

### `go fix` gains new modernizers _(Go 1.27+)_

New analyzers: `atomictypes`, `embedlit`, `slicesbackward`, `unsafefuncs`. `waitgroup` analyzer renamed to `waitgroupgo`; `fmtappendf` removed. Run `go fix ./...` after upgrading toolchain. → See [Tooling modernization](./tooling.md) for full `go fix`/`go doc`/`go mod tidy` command reference.

### `go test` runs the `stdversion` vet check _(Go 1.27+)_

`go test` now reports standard library symbols too new for file's effective Go version (`go` directive in `go.mod` plus build tags). CI failing after toolchain upgrade: bump module's `go` directive or gate newer API behind build tags. Don't silence check.

### `go mod tidy` merges duplicate require blocks _(Go 1.27+)_

For modules with `go 1.27` or later in `go.mod`, `go mod tidy` merges duplicate `require` blocks into standard two-block layout (one direct, one indirect), keeping existing comments. Run once after bumping `go` directive to clean blocks left by manual edits and merge conflicts.

### Small Go 1.27+ API preferences

- `hash/maphash.Hasher` and `maphash.ComparableHasher`: contracts between a type and future hash-based data structures (hash tables, Bloom filters).
- `database/sql.ConvertAssign` and `driver.RowsColumnScanner`: for database driver authors.
- `runtime/secret.Do`: goroutines started in secret mode now execute in secret mode themselves.

### Go 1.27+ version-bump risk checklist (verify, don't rewrite)

Review before or during bump to `go 1.27`. None need code rewrite; skipping check risks build failure or silent behavior change:

- **Removed `GODEBUG` settings** — `asynctimerchan`, `tlsunsafeekm`, `tlsrsakex`, `tls3des`, `tls10server`, `x509keypairleaf`, `gotypesalias`. `godebug` line in `go.mod` or `//go:debug` comment still pinning one of these to its old value now **fails the build**. Pinning it to its current default value is accepted. Search with `grep -rn 'go:debug\|godebug' go.mod **/*.go`.
- **json/v2 default strictness** — see above. Before bump ships, re-run integration tests against real-world payloads, not only unit tests.
- **Size-specialized allocator** — up to 30% faster allocations under 80 bytes, roughly 1% faster overall, costs ~60 KB binary size. On by default. Disable with `GOEXPERIMENT=nosizespecializedmalloc` if binary size constrained; flag scheduled for removal in Go 1.28, not long-term setting.
- **Darwin floor raised to macOS 13 (Ventura)** — older macOS targets can no longer run binaries from this toolchain.
- **`linux/ppc64` now builds ELFv2 binaries** and requires Linux kernel 3.13+ (RHEL 7's 3.10 kernel with backports). Relevant only to ppc64 deployments.
- **`bzr` version control support removed** from `go` command. Irrelevant unless module still vendors from Bazaar.
- **Tracebacks now include `runtime/pprof` goroutine labels** for `go 1.27+` modules by default. Disable with `GODEBUG=tracebacklabels=0` if labels leak sensitive data into crash logs or panic output.

---

## General Modernization (Any Version)

### Code MUST use `any` instead of `interface{}` _(Go 1.18+)_

```go
// Before
func process(data interface{}) interface{} { ... }

// After (Go 1.18+)
func process(data any) any { ... }
```

### Use generics instead of `interface{}` + type assertions _(Go 1.18+)_

```go
// Before
func Contains(slice []interface{}, item interface{}) bool { ... }

// After (Go 1.18+)
func Contains[T comparable](slice []T, item T) bool { ... }
// Or better (Go 1.21+): slices.Contains
```

### Use `errors.Join` instead of multi-error libraries _(Go 1.20+)_

```go
// Before: hashicorp/go-multierror or uber-go/multierr
errs = multierror.Append(errs, err1)
return errs.ErrorOrNil()

// After (Go 1.20+)
return errors.Join(err1, err2)
```

### Use `net.JoinHostPort` instead of `fmt.Sprintf` _(any version)_

```go
// Before (broken for IPv6)
addr := fmt.Sprintf("%s:%d", host, port)

// After (handles IPv6 correctly: [::1]:8080)
addr := net.JoinHostPort(host, strconv.Itoa(port))
```
