# Context Values & Cross-Service Tracing

## Using context values correctly

Context values carry request-scoped metadata crossing API boundaries, not function parameters, configuration or optional arguments. Good candidates: trace IDs, span IDs, request IDs, authenticated user info, correlation IDs.

Always use unexported key type to prevent collisions between packages:

```go
// ✓ Good — unexported key type prevents collisions
type contextKey string

const (
    traceIDKey   contextKey = "trace_id"
    requestIDKey contextKey = "request_id"
)

func WithTraceID(ctx context.Context, traceID string) context.Context {
    return context.WithValue(ctx, traceIDKey, traceID)
}

func TraceIDFromContext(ctx context.Context) (string, bool) {
    traceID, ok := ctx.Value(traceIDKey).(string)
    return traceID, ok
}
```

```go
// ✗ Bad — string keys collide across packages
ctx = context.WithValue(ctx, "trace_id", traceID) // another package could use the same key
```

## What belongs in context values vs function parameters

| Data | Context value? | Why |
| --- | --- | --- |
| trace_id, span_id, request_id | Yes | Request-scoped metadata for observability |
| Authenticated user/tenant | Yes | Request-scoped, crosses API boundaries |
| Database connection | No | Infrastructure dependency, pass explicitly |
| Feature flags | No | Configuration, pass explicitly or inject |
| Function arguments (user ID, order data) | No | Business logic parameters, pass as arguments |
| Logger | Depends | OK if enriched with request-scoped fields (trace_id); otherwise pass explicitly |

## Trace propagation between services

In microservices, `context.Context` carries trace propagation. When Service A calls Service B, trace_id and span_id travel in context values, then into outgoing HTTP headers (typically via OpenTelemetry).

```go
// Middleware injects trace_id from incoming request headers into context
func TracingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        traceID := r.Header.Get("X-Trace-ID")
        if traceID == "" {
            traceID = generateTraceID()
        }

        ctx := WithTraceID(r.Context(), traceID)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// When making outbound HTTP calls, inject trace_id from context into headers
func (c *HTTPClient) Do(ctx context.Context, method, url string, body io.Reader) (*http.Response, error) {
    req, err := http.NewRequestWithContext(ctx, method, url, body)
    if err != nil {
        return nil, fmt.Errorf("creating request: %w", err)
    }

    // Propagate trace_id to downstream service
    if traceID, ok := TraceIDFromContext(ctx); ok {
        req.Header.Set("X-Trace-ID", traceID)
    }

    return c.client.Do(req)
}
```

OpenTelemetry automates this via `otel` SDK and `propagation.TraceContext`. Same mechanism: context carries trace state and must pass through every layer.
