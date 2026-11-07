# Pipeline Patterns

## Table of Contents

- [Fanout — Broadcast to All](#fanout--broadcast-to-all)
- [Router — Predicate-Based Routing](#router--predicate-based-routing)
- [FirstMatch — Short-Circuit Routing](#firstmatch--short-circuit-routing)
- [Failover — Sequential Fallback](#failover--sequential-fallback)
- [Pool — Load-Balanced Dispatch](#pool--load-balanced-dispatch)
- [Pipe — Middleware Chain](#pipe--middleware-chain)
- [Inline Handlers and Middleware](#inline-handlers-and-middleware)
- [AttrFromContext — Request-Scoped Attributes](#attrfromcontext--request-scoped-attributes)
- [Full Production Pipeline](#full-production-pipeline)

## Fanout — Broadcast to All

Every record to every handler, sequentially. Latency = sum of handler latencies.

```go
import slogmulti "github.com/samber/slog-multi"

logger := slog.New(
    slogmulti.Fanout(
        slog.NewJSONHandler(os.Stdout, nil),           // stdout
        slog.NewTextHandler(logFile, nil),              // file
        slogsentry.Option{Level: slog.LevelError}.NewSentryHandler(), // Sentry
    ),
)
```

**When to use:** every destination must receive every record (audit logs, compliance). **When NOT to use:** handlers need different records (use Router) or have high latency (use Pool).

## Router — Predicate-Based Routing

Sends records to ALL handlers whose predicate matches.

```go
logger := slog.New(
    slogmulti.Router().
        Add(sentryHandler, slogmulti.LevelIs(slog.LevelError)).
        Add(slackHandler, slogmulti.LevelIs(slog.LevelWarn)).
        Add(lokiHandler, slogmulti.LevelIs(slog.LevelInfo, slog.LevelDebug)).
        Add(slog.NewJSONHandler(os.Stdout, nil)). // catch-all: no predicate
        Handler(),
)
```

**Built-in predicates:**

```go
slogmulti.LevelIs(slog.LevelError)             // match specific levels
slogmulti.LevelIsNot(slog.LevelDebug)          // exclude levels
slogmulti.MessageIs("payment processed")       // exact message match
slogmulti.MessageIsNot("healthcheck")          // exclude exact message
slogmulti.MessageContains("timeout")           // partial message match
slogmulti.MessageNotContains("debug")          // exclude partial message
slogmulti.AttrValueIs("module", "billing")     // match attribute value
slogmulti.AttrKindIs(slog.KindString)          // match attribute kind
```

**Custom predicate:**

```go
func recordMatchRegion(region string) func(ctx context.Context, r slog.Record) bool {
    return func(ctx context.Context, r slog.Record) bool {
        match := false
        r.Attrs(func(attr slog.Attr) bool {
            if attr.Key == "region" && attr.Value.String() == region {
                match = true
                return false
            }
            return true
        })
        return match
    }
}

logger := slog.New(
    slogmulti.Router().
        Add(slackUS, recordMatchRegion("us")).
        Add(slackEU, recordMatchRegion("eu")).
        Handler(),
)
```

**Warning:** records matching no predicate are silently dropped. Always add catch-all handler (no predicate) unless discarding them is intended.

## FirstMatch — Short-Circuit Routing

Router that stops at first matching handler. Each record reaches exactly one destination.

```go
logger := slog.New(
    slogmulti.Router().
        Add(queryHandler, matchQueryLogs).     // priority 1
        Add(requestHandler, matchRequestLogs). // priority 2
        Add(defaultHandler).                   // fallback
        FirstMatch().
        Handler(),
)
```

**When to use:** priority routing. Order matters: most specific handlers first.

## Failover — Sequential Fallback

Tries handlers in order until one succeeds (returns `nil` error). If primary fails, falls through to secondary.

```go
logger := slog.New(
    slogmulti.Failover()(
        slogloki.Option{Level: slog.LevelDebug, Client: lokiClient}.NewLokiHandler(),
        slog.NewJSONHandler(localFile, nil), // fallback to local file
        slog.NewTextHandler(os.Stderr, nil), // last resort
    ),
)
```

**When to use:** possibly unreliable network sinks (Loki, Logstash, remote syslog). Primary handles 99.9% of traffic; fallback catches rest.

## Pool — Load-Balanced Dispatch

Sends each record to one random handler in pool.

```go
logger := slog.New(
    slogmulti.Pool()(
        lokiHandler1, // shard 1
        lokiHandler2, // shard 2
        lokiHandler3, // shard 3
    ),
)
```

**When to use:** multiple equivalent sinks, throughput distribution. Latency = single handler latency (not sum like Fanout).

## Pipe — Middleware Chain

Chains middleware that intercepts, transforms or enriches records before final handler.

```go
logger := slog.New(
    slogmulti.
        Pipe(samplingMiddleware).              // step 1: drop noise
        Pipe(piiScrubbingMiddleware).          // step 2: mask PII
        Pipe(traceInjectionMiddleware).        // step 3: add trace_id
        Pipe(slogmulti.RecoverHandlerError(    // step 4: catch handler panics
            func(ctx context.Context, record slog.Record, err error) {
                log.Println("handler error:", err)
            },
        )).
        Handler(slog.NewJSONHandler(os.Stdout, nil)),
)
```

## Inline Handlers and Middleware

Quick handlers without full struct.

```go
// Inline handler — for testing or simple consumers
handler := slogmulti.NewHandleInlineHandler(
    func(ctx context.Context, groups []string, attrs []slog.Attr, record slog.Record) error {
        fmt.Printf("LOG: %s %s\n", record.Level, record.Message)
        return nil
    },
)

// Inline middleware — intercept and transform records
middleware := slogmulti.NewHandleInlineMiddleware(
    func(ctx context.Context, record slog.Record, next func(context.Context, slog.Record) error) error {
        record.AddAttrs(slog.String("service", "my-api"))
        return next(ctx, record)
    },
)
```

## AttrFromContext — Request-Scoped Attributes

HTTP middlewares (`slog-gin`, `slog-echo`, etc.) inject request attributes into context; backend handlers extract them via `AttrFromContext`.

```go
// Backend handler extracts trace_id from context
handler := slogsentry.Option{
    Level: slog.LevelError,
    AttrFromContext: []func(ctx context.Context) []slog.Attr{
        func(ctx context.Context) []slog.Attr {
            if traceID := ctx.Value("trace_id"); traceID != nil {
                return []slog.Attr{slog.String("trace_id", traceID.(string))}
            }
            return nil
        },
    },
}.NewSentryHandler()
```

**Important:** `AttrFromContext` only works when context holds expected values, so HTTP middleware (like `slog-gin`) must populate context first. Without middleware, `AttrFromContext` silently returns nil.

## Full Production Pipeline

Canonical ordering: sampling → middleware (PII, trace) → routing → sinks.

```go
import (
    slogmulti "github.com/samber/slog-multi"
    slogsampling "github.com/samber/slog-sampling"
    slogformatter "github.com/samber/slog-formatter"
    slogsentry "github.com/samber/slog-sentry/v2"
    slogloki "github.com/samber/slog-loki/v3"
)

// 1. Sampling: first 20 per 5s, then 10%
sampling := slogsampling.ThresholdSamplingOption{
    Tick: 5 * time.Second, Threshold: 20, Rate: 0.1,
}.NewMiddleware()

// 2. PII scrubbing
pii := slogformatter.NewFormatterMiddleware(
    slogformatter.PIIFormatter("user"),
    slogformatter.IPAddressFormatter("client_ip"),
)

// 3. Error recovery
recovery := slogmulti.RecoverHandlerError(func(ctx context.Context, r slog.Record, err error) {
    log.Printf("slog handler error: %v", err)
})

// 4. Sinks
sentryHandler := slogsentry.Option{Level: slog.LevelError}.NewSentryHandler()
lokiHandler := slogloki.Option{Level: slog.LevelDebug, Client: lokiClient}.NewLokiHandler()
defer lokiClient.Stop() // flush buffered logs

// 5. Compose — errors bypass sampling, everything else is sampled
logger := slog.New(
    slogmulti.
        Pipe(pii).            // scrub PII on all records
        Pipe(recovery).       // catch panics
        Handler(
            slogmulti.Router().
                Add(sentryHandler, slogmulti.LevelIs(slog.LevelError)).  // errors: no sampling
                Add(slogmulti.                                            // everything else: sampled
                    Pipe(sampling).
                    Handler(lokiHandler),
                ).
                FirstMatch().  // stop at first matching route — errors won't fall through to sampled path
                Handler(),
        ),
)
slog.SetDefault(logger)
```
