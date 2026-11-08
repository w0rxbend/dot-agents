# Test Naming

## Test Functions

Test functions: `Test` + name of what is tested. Underscores for subcases.

```go
func TestParseToken(t *testing.T) { ... }
func TestServer_Handle(t *testing.T) { ... }           // method test
func TestParseToken_InvalidInput(t *testing.T) { ... }  // subcase
```

## Table-Driven Tests

Table-driven case names SHOULD be **fully lowercase, descriptive phrases**, acronyms included. Use `input` for inputs and `expected` for expected outputs so data flow is clear:

```go
tests := []struct {
    name         string
    input        string
    expectedCode int
    expectedErr  bool
}{
    {name: "empty input", input: "", expectedCode: 400, expectedErr: true},
    {name: "valid token", input: "abc123", expectedCode: 200},
    {name: "expired token", input: "exp", expectedCode: 401, expectedErr: true},
    {name: "invalid id", input: "???", expectedCode: 400, expectedErr: true},  // "id" not "ID"
}

// Bad — mixed case in test names
{name: "valid ID", ...}      // should be "valid id"
{name: "Empty Input", ...}   // should be "empty input"
```

## Test Helpers

Test helpers that panic on failure conventionally use `must` prefix: `mustLoadFixture()`, `mustParseURL()`.
