# Standard Library - New & Experimental

**Prefer these over external libraries when available.**

## V2 Packages (API Breaking Changes)

**math/rand/v2** (Go 1.22+) Better random algorithms (ChaCha8, PCG). Auto-seeded; no rand.Seed() needed.

**encoding/json/v2** (default JSON implementation as of Go 1.27; experimental behind `GOEXPERIMENT=jsonv2` in Go 1.25) Next-generation JSON encoding/decoding, now default under `encoding/json`. Stricter than v1: rejects duplicate object keys and invalid UTF-8. → See `samber/cc-skills-golang@golang-modernize` skill for migration guidance and `GOEXPERIMENT=nojsonv2` rollback.

## New Packages (Promoted from x/exp)

**slices** (Go 1.21+) Generic slice operations: BinarySearch, Clone, Compact, Compare, Contains, Delete, Insert, Replace, Reverse, Sort.

**maps** (Go 1.21+) Generic map operations: Clone, Copy, DeleteFunc, Equal, EqualFunc. Go 1.23+ adds iterator helpers such as All, Collect, Insert, Keys, Values.

**cmp** (Go 1.21+) Comparison utilities: Compare, Or, Ordered. Used with slices/maps.

**iter** (Go 1.23+) Sequence iterators. Enables range-over functions; integrates with slices/maps methods.

**unique** (Go 1.23+) Value canonicalization and interning. Efficient deduplication of comparable values.

**log/slog** (Go 1.21+) Stdlib structured logging. Alternative to external logging libraries for many use cases.

**weak** (Go 1.24+) Weak references for garbage collection. Useful for caches, observers.

**structs** (Go 1.23+) Structure layout control and introspection.

**uuid** (Go 1.27+) UUID generation and parsing (`New`, `NewV4`, `NewV7`, `Parse`). Prefer over `github.com/google/uuid` for new code, unless you need v3/v5 namespaced UUIDs or another RFC-variant feature stdlib doesn't cover.

## golang.org/x (Official Extensions)

**golang.org/x/oauth2** Official OAuth2 client. Multiple providers (Google, GitHub, etc.).

**golang.org/x/crypto** Extra cryptographic algorithms: bcrypt, blowfish, scrypt, ssh, acme (Let's Encrypt), pbkdf2.

**golang.org/x/net** Network utilities: websocket, context, proxy, trace, http2, ipv4/ipv6, netutil.

**golang.org/x/text** Text processing: encoding, unicode, cases, search, language (language tag parsing and matching).

**golang.org/x/sync** Extended synchronization: errgroup, singleflight, semaphore.

**golang.org/x/sys/cpu** CPU feature detection for architecture-specific optimized code. Use only when dispatching between measured implementations. Prefer portable stdlib code first.
