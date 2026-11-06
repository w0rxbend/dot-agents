# General Debugging Methodology

For any bug, follow this process:

## Table of Contents

- [Step 1: Understand Expected vs Actual](#step-1-understand-expected-vs-actual)
- [Step 2: Get the Full Error](#step-2-get-the-full-error)
- [Step 3: Isolate the Problem](#step-3-isolate-the-problem)
- [Step 4: Check External Dependencies](#step-4-check-external-dependencies)
- [Step 5: Check Observability Tools](#step-5-check-observability-tools)
- [Step 6: Compare with Working Code](#step-6-compare-with-working-code)
- [Step 7: Form a Hypothesis and Test It](#step-7-form-a-hypothesis-and-test-it)
- [Step 8: Trace to Root Cause](#step-8-trace-to-root-cause)
- [Step 9: Fix and Verify](#step-9-fix-and-verify)
- [Step 10: Defense-in-Depth](#step-10-defense-in-depth)
- [When You're Stuck: Escalation Protocol](#when-youre-stuck-escalation-protocol)

## Step 1: Understand Expected vs Actual

Before touching code, state clearly:

- What **should** happen?
- What **actually** happens?
- What **changed** recently?

```bash
# What changed recently?
git log --oneline -20
git diff HEAD~5

# Binary search for the breaking commit
git bisect start
git bisect bad          # current commit is broken
git bisect good abc123  # this commit was working
# git bisect will walk you to the breaking commit
```

## Step 2: Get the Full Error

```bash
# Full build errors
go build ./... 2>&1

# Verbose test output
go test ./... -v 2>&1

# Static analysis
go vet ./...

# Run linters — see the golang-lint skill for configuration
golangci-lint run ./...
```

Run `golangci-lint` early: catches unchecked errors, suspicious constructs, other issues easy to miss when reading code. See `samber/cc-skills-golang@golang-lint` skill for configuration and usage.

## Step 3: Isolate the Problem

Narrow scope before investigating deeper:

```bash
# Does a single test fail?
go test -run TestSpecificName -v ./pkg/...

# Does it fail without cache?
go test -count=1 -run TestSpecificName ./pkg/...

# Is it a specific package?
go build ./pkg/suspect/...

# Is it flaky? Run multiple times
go test -count=10 -run TestSuspect ./pkg/...
```

Write more tests if you suspect missing test cases or need to test under different conditions.

## Step 4: Check External Dependencies

Sometimes bug is not in your code. Before diving deeper, verify external components behave as expected:

```bash
# Reproduce an API call outside your app (staging or read-only; confirm mutating calls with user)
curl -v -X POST https://api.example.com/endpoint \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'

# Check database content directly
psql -h localhost -U myuser -d mydb -c "SELECT * FROM orders WHERE id = 123"
# Or: mysql, mongosh, redis-cli, etc.
# Or use a database MCP server to query interactively

# Test connectivity and DNS resolution
dig api.example.com
nc -zv api.example.com 443

# Check if an external service is responding at all
curl -o /dev/null -s -w "HTTP %{http_code} in %{time_total}s\n" https://api.example.com/health

# Inspect message queue state
rabbitmqctl list_queues
# Or: kafka-console-consumer, redis-cli LLEN, etc.

# Check certificate validity
openssl s_client -connect api.example.com:443 -brief

# Verify environment variables exist (names only; never print secret values)
env | cut -d= -f1 | grep -E 'DATABASE|API_KEY'
```

**Common external causes:**

- API contract changed (new required field, different response shape, deprecated endpoint)
- Database schema drift (missing column, changed type, new constraint, migration not applied)
- Expired or rotated credentials, tokens, or certificates
- DNS resolution failure or stale DNS cache
- Rate limiting or quota exhaustion
- External service degraded (slow responses, partial failures, 5xx errors)
- Message queue full, consumer lag, or rebalancing
- Different behavior between environments (staging vs production config, feature flags)
- Clock skew affecting JWT validation, cache TTLs, or scheduled jobs
- TLS/mTLS misconfiguration or CA bundle mismatch
- Network policy or firewall rule change blocking traffic
- Proxy or load balancer misconfiguration (wrong backend, sticky sessions, health check)
- Disk full or read-only filesystem
- File permissions changed
- OOM killer terminated dependency (database, cache, sidecar)
- Docker/K8s: wrong image tag, missing env var, resource limits, liveness probe misconfigured
- Third-party SDK or library upgrade with breaking behavioral change
- Locale, timezone, or encoding mismatch between systems
- Connection pool exhaustion (database, HTTP, gRPC)
- Upstream returning cached/stale data
- Network issue. Webhook or callback URL changed or unreachable

## Step 5: Check Observability Tools

Production debugging MUST start with observability data. Project may already have observability tools with the answer. Look in codebase for imports or dependencies like `prometheus`, `opentelemetry`, `datadog`, `sentry`, `elastic/apm`. Even if absent from code, developer may deploy them separately.

If information is missing, **ask the user** which monitoring and observability tools they use. Common stacks:

- **Prometheus + Grafana** — Dashboards may show error rate spikes, latency changes, resource saturation. Query examples:

  ```promql
  rate(http_requests_total{status=~"5.."}[5m])           # error rate
  histogram_quantile(0.99, rate(http_duration_seconds_bucket[5m]))  # p99 latency
  go_goroutines                                           # goroutine count over time
  go_memstats_alloc_bytes                                 # heap allocations
  rate(go_gc_duration_seconds_sum[5m])                    # GC pressure
  ```

- **Datadog** — APM traces, error tracking, infrastructure metrics. Query examples:

  ```
  avg:trace.http.request.duration{service:myapp} by {resource_name}
  sum:trace.http.request.errors{service:myapp}.as_count()
  avg:runtime.go.num_goroutine{service:myapp}
  ```

- **Sentry** — Captured exceptions, breadcrumbs, error grouping. Often has full stack trace and context of first occurrence.
- **ELK (Elasticsearch + Logstash + Kibana)** — Search structured logs for error patterns:

  ```
  level:error AND service:myapp AND @timestamp:[now-1h TO now]
  ```

- **OpenTelemetry / Jaeger / Zipkin** — Distributed traces show latency breakdowns across services, failed spans, propagation issues.

If user has MCP server for any of these tools (Datadog MCP, Grafana MCP, etc.), interactive queries may be available through it.

## Step 6: Compare with Working Code

Before forming hypothesis, find similar code that **works**:

- Search codebase for analogous functionality without the bug
- Read working reference implementation **completely** — don't skim
- List **every difference** between working and broken code
- Check: same dependencies? Config? Initialization order? Error handling?

## Step 7: Form a Hypothesis and Test It

- Form **single, specific** hypothesis with clear reasoning
- Add targeted logging or focused test
- Change **one thing**, observe, confirm or reject
- If hypothesis was wrong, **revert the change** — don't stack fixes on failed attempts

## Step 8: Trace to Root Cause

When symptom appears deep in call stack, don't fix where error surfaces. Trace backward:

1. **Find the immediate cause** — what line panics or returns wrong value?
2. **Ask "what called this?"** — trace one level up call chain
3. **Keep tracing** — repeat until you find where invalid data **originated**, not where it was **consumed**
4. **Fix at the source** — fix belongs where bad value was created, not where it caused crash

```go
// Example: panic in handler — but the bug is in the constructor
// ✗ Bad — fixing at the symptom
func (s *Server) Handle(w http.ResponseWriter, r *http.Request) {
    if s.db == nil {  // nil check masks the real bug
        http.Error(w, "db unavailable", 500)
        return
    }
    // ...
}

// ✓ Good — fixing at the source
func NewServer(db *sql.DB) *Server {
    if db == nil {
        panic("NewServer: db must not be nil")  // fail fast at construction
    }
    return &Server{db: db}
}
```

When you can't trace manually, add temporary instrumentation:

```go
// Log the full call chain before the dangerous operation
func suspectFunction(val string) {
    fmt.Fprintf(os.Stderr, "DEBUG suspectFunction: val=%q\n%s\n", val, debug.Stack())
    // ...
}
```

## Step 9: Fix and Verify

- Fix root cause, not symptom
- Failing test from step 1 should now pass
- Run full test suite to check for regressions

## Step 10: Defense-in-Depth

After fixing bug, ask: "How do I make this bug structurally impossible?" Add validation at multiple layers:

1. **Entry point** — reject invalid input at public API boundaries (`New*` constructors, exported functions)
2. **Business logic** — assert preconditions inside internal functions receiving the data
3. **Runtime guards** — use build tags or env checks to catch dangerous operations in tests (e.g., refuse writes outside temp dirs)
4. **Observability** — add structured logging or metrics so same bug class is instantly visible if it recurs

Not every fix needs all four layers; use judgment. When bug could cause data loss, corruption, or security issues, multi-layer defense is worth the cost.

## When You're Stuck: Escalation Protocol

If fix doesn't work:

- **< 3 failed attempts:** Return to Step 1. Root cause was misidentified. Gather more evidence.
- **>= 3 failed attempts:** Stop fixing. Problem is likely architectural, not a simple bug. Step back, question assumptions about how system works. Ask: "Is the design fundamentally sound, or am I patching a broken abstraction?"
- **Each fix reveals a new problem:** Chasing symptoms, not root cause. See Red Flags section in [SKILL.md](../SKILL.md).
