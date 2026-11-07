# Distributed Tracing with OpenTelemetry

→ See `samber/cc-skills-golang@golang-context` skill for propagating context across service boundaries. → See `samber/cc-skills-golang@golang-samber-oops` skill for structured errors with stack traces in spans.

For OpenTelemetry Go SDK, check official library docs for current API signatures and examples.

## Table of Contents

- [OTel SDK Setup](#otel-sdk-setup)
- [Creating Spans](#creating-spans)
- [HTTP Middleware with `otelhttp`](#http-middleware-with-otelhttp)
- [Span Status and Recording Errors](#span-status-and-recording-errors)
- [Structured Errors with `samber/oops`](#structured-errors-with-samberoops)
- [Trace Sampling](#trace-sampling)
- [Cost of Tracing](#cost-of-tracing)

## OTel SDK Setup

Set up TracerProvider early. On new projects, do it first, then add spans everywhere incrementally.

```go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/sdk/resource"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.26.0"
)

func initTracer(ctx context.Context) (func(), error) {
    exporter, err := otlptracegrpc.New(ctx)
    if err != nil {
        return nil, fmt.Errorf("creating OTLP exporter: %w", err)
    }

    res, err := resource.New(ctx,
        resource.WithAttributes(
            semconv.ServiceNameKey.String("my-service"),
            semconv.ServiceVersionKey.String("1.0.0"),
        ),
    )
    if err != nil {
        return nil, fmt.Errorf("creating resource: %w", err)
    }

    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(res),
    )
    otel.SetTracerProvider(tp)

    shutdown := func() {
        _ = tp.Shutdown(context.Background())
    }
    return shutdown, nil
}
```

## Creating Spans

```go
import "go.opentelemetry.io/otel"

var tracer = otel.Tracer("myapp/order-service")

func (s *OrderService) Create(ctx context.Context, req CreateOrderRequest) (*Order, error) {
    ctx, span := tracer.Start(ctx, "OrderService.Create")
    defer span.End()

    // Add attributes that help with debugging
    span.SetAttributes(
        attribute.String("order.payment_method", req.PaymentMethod),
        attribute.Float64("order.amount", req.Amount),
    )

    order, err := s.repo.Insert(ctx, req.ToOrder())
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, err.Error())
        return nil, fmt.Errorf("inserting order: %w", err)
    }

    return order, nil
}

func (r *OrderRepo) Insert(ctx context.Context, order Order) (*Order, error) {
    ctx, span := tracer.Start(ctx, "OrderRepo.Insert")
    defer span.End()

    _, err := r.db.ExecContext(ctx, "INSERT INTO orders ...", order.ID)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, err.Error())
        return nil, fmt.Errorf("exec insert: %w", err)
    }
    return &order, nil
}
```

**Where to add spans** — MUST create spans for:

- Every service method (business logic layer)
- Every database query
- Every external API call
- Every message queue publish/consume
- Any operation that takes measurable time or could fail

## HTTP Middleware with `otelhttp`

Creates spans automatically for incoming and outgoing HTTP requests:

```go
import "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"

// Incoming requests — wrap your handler
mux.Handle("/orders", otelhttp.NewHandler(orderHandler, "CreateOrder"))

// Outgoing requests — HTTP clients MUST use otelhttp for automatic span propagation
client := &http.Client{
    Transport: otelhttp.NewTransport(http.DefaultTransport),
}
```

## Span Status and Recording Errors

```go
import (
    "go.opentelemetry.io/otel/codes"
)

// On success — no need to set status (Unset is fine)

// On error — MUST call both RecordError() and SetStatus(Error)
if err != nil {
    span.RecordError(err)
    span.SetStatus(codes.Error, "operation failed")
    return err
}
```

## Structured Errors with `samber/oops`

Standard Go errors lose critical debug data: no stack trace, no structured context, no request-scoped metadata. Trace shows `"connection refused"` but not its origin or affected user/tenant.

[`samber/oops`](https://github.com/samber/oops) is drop-in error library filling these gaps. Every `oops` error carries stack trace and structured attributes, and works with OpenTelemetry spans and `slog`:

```go
import "github.com/samber/oops"

func (s *OrderService) Create(ctx context.Context, req CreateOrderRequest) (*Order, error) {
    ctx, span := tracer.Start(ctx, "OrderService.Create")
    defer span.End()

    order, err := s.repo.Insert(ctx, req.ToOrder())
    if err != nil {
        // oops wraps the error with stack trace, structured context, and error code
        return nil, oops.
            In("order-service").
            Code("order_insert_failed").
            With("order_id", req.OrderID).
            With("user_id", req.UserID).
            Wrapf(err, "inserting order")
    }

    return order, nil
}
```

Logged or recorded on span, this error gives full stack trace, domain (`order-service`), error code (`order_insert_failed`), and structured attributes (`order_id`, `user_id`).

`oops` errors work with `span.RecordError()`, `errors.Is`/`errors.As`, and `slog`. See `samber/cc-skills-golang@golang-error-handling` and `samber/cc-skills-golang@golang-samber-oops` skills for full usage patterns.

## Trace Sampling

Tracing every request in high-throughput services is expensive. Sample to control volume:

```go
tp := sdktrace.NewTracerProvider(
    // Sample 10% of traces in production
    sdktrace.WithSampler(sdktrace.TraceIDRatioBased(0.1)),
    sdktrace.WithBatcher(exporter),
    sdktrace.WithResource(res),
)
```

For finer control, use `sdktrace.ParentBased()` to respect parent's sampling decision. Keeps traces complete across service boundaries.

## Cost of Tracing

**Cost factors:**

- **Span volume** — service at 10k req/s with 5 spans per request emits 50k spans/s. Enormous at 100% sampling.
- **Span attributes** — each attribute grows payload. Large attributes (request/response bodies) multiply cost.
- **Storage and indexing** — tracing backends (Jaeger, Tempo, Datadog) charge by volume. Unsampled traces can easily become largest line item in observability bill.

**Mitigation:**

- Use sampling (see above): start with 10% (`TraceIDRatioBased(0.1)`), adjust by traffic volume and budget
- For high-throughput services, consider head-based sampling (decide at trace start) or tail-based sampling (decide after trace completes; keep only interesting traces like errors or slow requests)
- Avoid large payloads as span attributes: log them instead, correlate via trace_id
