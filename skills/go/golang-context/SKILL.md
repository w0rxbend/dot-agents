---
name: golang-context
description: "Propagate Go context.Context cancellation, deadlines, and request-scoped values through APIs. Use when work needs a cancellation contract or context misuse causes leaks or timeouts."
user-invocable: true
license: MIT
compatibility: Designed for Claude Code, Codex or similar harness, and for projects using Golang.
metadata:
  author: samber
  version: "1.3.1"
  openclaw:
    emoji: "🔗"
    homepage: https://github.com/samber/cc-skills-golang
    requires:
      bins:
        - go
    install: []
allowed-tools: Read Edit Write Glob Grep Bash(go build:*) Bash(go test:*) Bash(go vet:*) Bash(golangci-lint run:*) Bash(git status:*) Bash(git diff:*) Bash(git log:*) Bash(git show:*) Agent
paths:
  - "**/*.go"
---

> **Community default.** Company skill explicitly superseding `samber/cc-skills-golang@golang-context` skill takes precedence.

# Go context.Context Best Practices

## Best Practices Summary

1. Propagate same context through whole request lifecycle: HTTP handler → service → DB → external APIs. Any link starting fresh context keeps running after client leaves.
2. Take `ctx` as first parameter, named `ctx context.Context`. Fixed position makes context-aware APIs obvious at a glance; linters check it.
3. Pass context as function parameter, not struct field. Struct outlives its request, so later calls reuse context already cancelled or owned by someone else.
4. Pass `context.TODO()`, not `nil` context. `nil` panics on first `Done()` or `Value()` call, far from caller that passed it.
5. Call `cancel()` on all control-flow paths for `WithCancel`/`WithTimeout`/`WithDeadline`, unless ownership of context and cancel function is explicitly returned or transferred. Uncalled `cancel()` keeps child attached to parent and leaks its timer until parent finishes.
6. Create `context.Background()` only at top-level entry points (main, init, tests). Deeper in call chain, especially mid-request, it detaches work from caller's deadline and cancellation (propagation break below).
7. Use `context.TODO()` as placeholder when context needed but none exists yet. Marks gap for later fix instead of hiding it behind deliberate-looking `Background()`.
8. Declare context value keys as unexported types. Plain `string` key: two packages using `"user"` silently overwrite each other.
9. Carry only request-scoped metadata in context values, never function parameters. `Value()` results lose compile-time typing and vanish from function signature.
10. Use `context.WithoutCancel` (Go 1.21+) for background work that must outlive parent request. Otherwise handler return cancels just-started audit log or cleanup.

## Creating Contexts

| Situation | Use |
| --- | --- |
| Entry point (main, init, test) | `context.Background()` |
| Function needs context, caller doesn't provide one yet | `context.TODO()` |
| Inside HTTP handler | `r.Context()` |
| Need cancellation control | `context.WithCancel(parentCtx)` |
| Need deadline/timeout | `context.WithTimeout(parentCtx, duration)` |

## Context Propagation: The Core Principle

Key rule: **propagate same context through entire call chain**. Then cancelling parent cancels all downstream work automatically.

```go
// ✗ Bad — creates a new context, breaking the chain
func (s *OrderService) Create(ctx context.Context, order Order) error {
    _, err := s.db.ExecContext(context.Background(), "INSERT INTO orders ...", order.ID)
    return err
}

// ✓ Good — propagates the caller's context
func (s *OrderService) Create(ctx context.Context, order Order) error {
    _, err := s.db.ExecContext(ctx, "INSERT INTO orders ...", order.ID)
    return err
}
```

## Deep Dives

- **[Cancellation, Timeouts & Deadlines](./references/cancellation.md)** — How cancellation propagates: `WithCancel` (manual), `WithTimeout` (after a duration), `WithDeadline` (absolute time). Listening (`<-ctx.Done()`) in concurrent code, `AfterFunc` callbacks, `WithoutCancel` for operations that must outlive parent request (e.g., audit logs).

- **[Context Values & Cross-Service Tracing](./references/values-tracing.md)** — Safe value patterns: unexported key types prevent namespace collisions; when to use context values (request ID, user ID) vs function parameters. Trace propagation: OpenTelemetry trace headers, correlation IDs for log aggregation, marshaling/unmarshaling context across service boundaries.

- **[Context in HTTP Servers & Service Calls](./references/http-services.md)** — Handler context: `r.Context()` for request-scoped cancellation, middleware, propagation to services. HTTP clients: `NewRequestWithContext`, client timeouts, context-aware retries. Database: always use `*Context` variants (`QueryContext`, `ExecContext`) to respect deadlines.

## Cross-References

- → See `samber/cc-skills-golang@golang-concurrency` skill for goroutine cancellation patterns using context
- → See `samber/cc-skills-golang@golang-database` skill for context-aware database operations (QueryContext, ExecContext)
- → See `samber/cc-skills-golang@golang-observability` skill for trace context propagation with OpenTelemetry
- → See `samber/cc-skills-golang@golang-design-patterns` skill for timeout and resilience patterns

## Enforce with Linters

`govet` and `staticcheck` linters catch many context pitfalls automatically. → See `samber/cc-skills-golang@golang-lint` skill for configuration and usage.
