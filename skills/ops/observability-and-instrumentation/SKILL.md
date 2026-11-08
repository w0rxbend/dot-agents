---
name: observability-and-instrumentation
description: Add structured logs, RED/USE metrics, traces, SLO-based alerts and runbooks to application code while building or reviewing a feature (on-call questions first, bounded cardinality, correlation IDs). Use when shipping production code or when an incident showed you couldn't tell what happened; for deploying the OTel/LGTM backend use implementing-observability, for error-tracker setup use error-debugging-error-trace.
---

# Observability and Instrumentation

## When to Use

- Any feature bound for production
- New service, endpoint, background job or external integration
- Production incident took too long to diagnose ("we couldn't tell what happened")
- Setting up or reviewing alerting rules
- Reviewing PR adding I/O, retries, queues or cross-service calls

**NOT for:**
- Diagnosing a failure happening right now: `debugging-and-error-recovery` skill (observability speeds it next time)
- Profiling and optimizing measured slowness: `performance-optimization` skill
- Launch-day monitoring checklists and rollback triggers: `shipping-and-launch` skill. This skill covers instrumentation feeding them

## Process

### 1. Define "working" before instrumenting

Before instrumenting, write 2–4 questions on-call will ask about this feature:

```
FEATURE: checkout payment retry
QUESTIONS ON-CALL WILL ASK:
1. What fraction of payments succeed on first attempt vs after retry?
2. When a payment fails permanently, why? (provider error? timeout? validation?)
3. Is the payment provider slower than usual?
→ Every signal below must help answer one of these.
```

Can't name them? Not ready to instrument: you'll log everything, learn nothing.

### 2. Pick the right signal for each question

| Signal | Answers | Cost profile | Example |
|---|---|---|---|
| **Structured log** | "What happened in this specific case?" | Per-event; grows with traffic | `payment_failed` with provider error code |
| **Metric** | "How often / how fast, in aggregate?" | Fixed per series; cheap to query | p99 latency of provider calls |
| **Trace** | "Where did time go across services?" | Per-request; usually sampled | One slow checkout, split by hop |

Rule of thumb: metrics show **that** something is wrong, traces **where**, logs **why**.

### 3. Structured logging

Log events, not prose: each line a JSON object with stable event name and machine-readable fields:

```typescript
// BAD: string interpolation — unqueryable, inconsistent
logger.info(`Payment ${id} failed for user ${userId} after ${n} retries`);

// GOOD: stable event name + structured fields
logger.warn({
  event: 'payment_failed',
  paymentId: id,
  provider: 'stripe',
  errorCode: err.code,
  attempt: n,
}, 'payment failed');
```

**Log levels — use consistently:**

| Level | Meaning | On-call action |
|---|---|---|
| `error` | Invariant broken; someone may need to act | Investigate |
| `warn` | Degraded but handled (retry succeeded, fallback used) | Watch trends |
| `info` | Significant business event (order placed, job finished) | None |
| `debug` | Diagnostic detail | Off in production by default |

**Correlation IDs are mandatory.** Generate (or accept) request ID at system boundary; attach it to every log line, span and outbound call. Without it, one request cannot be reconstructed from interleaved logs:

```typescript
// Express: child logger per request, ID propagated downstream
app.use((req, res, next) => {
  req.id = req.headers['x-request-id'] ?? crypto.randomUUID();
  req.log = logger.child({ requestId: req.id });
  res.setHeader('x-request-id', req.id);
  next();
});
```

**When several entry points write to one log, name the entry point.** Correlation ID identifies a run, not the code path that started it. Scheduler, replay endpoint and manual CLI running same job yield interchangeable lines in one sink. Attribution then means elimination via scheduler history, process table, deploy log: valid only while those external records still exist. Stamp entry point at run start, beside correlation ID; propagate both same way:

```typescript
// One helper for every entry point: the run's own logger carries both fields.
// `entryPoint`, not `source` — ECS reserves `source.*` for network fields.
export const runLog = (entryPoint: 'scheduler' | 'replay_endpoint' | 'cli', runId: string) =>
  logger.child({ entryPoint, requestId: runId });

// scheduler tick        -> runLog('scheduler', crypto.randomUUID())
// POST /jobs/:id/replay -> runLog('replay_endpoint', req.id)
// CLI invocation        -> runLog('cli', process.env.RUN_ID ?? crypto.randomUUID())
```

Both fields must cross same boundaries as correlation ID (queue metadata, HTTP headers), or worker re-derives entry point and guesses. Field merely correlating with entry point is a hint, not attribution: anything that can invoke the job can reproduce it.

**Never log secrets, tokens, passwords, or full PII.** Hard rule from `security-and-hardening` skill; telemetry pipelines are classic data-leak path. Allowlist fields; don't log whole request bodies.

### 4. Metrics

Request-driven services: instrument **RED** on every endpoint and external dependency: **R**ate (requests/sec), **E**rrors (failure rate), **D**uration (latency histogram, not average). Resources (queues, pools, hosts): **USE**: **U**tilization, **S**aturation, **E**rrors.

Vendor-neutral path, as with tracing: OpenTelemetry metrics API (same SDK and context as step 5). Example uses Prometheus' `prom-client`, one common backend, not the only one; RED/USE and cardinality rules identical either way.

```typescript
import { Histogram } from 'prom-client';

const httpDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration',
  labelNames: ['method', 'route', 'status_class'],  // '2xx', not '200'
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
});
```

**Cardinality is the failure mode.** Each unique label combination is a separate time series. Labels must come from small, fixed sets (route template, status class, provider name). Never label with user IDs, raw URLs, error messages or other unbounded values; those belong in logs and traces.

```
OK as label:    route="/api/tasks/:id"   status_class="5xx"   provider="stripe"
NEVER a label:  user_id, email, request_id, full URL, error message text
```

Never averages, always percentiles: average hides the 1% of users having a terrible time. Use histograms; read p50/p95/p99.

### 5. Distributed tracing

Use OpenTelemetry, the vendor-neutral standard; auto-instrumentation covers HTTP, gRPC and common DB clients with near-zero code:

```typescript
// tracing.ts — must be imported before anything else
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';

const sdk = new NodeSDK({
  serviceName: 'checkout-service',
  instrumentations: [getNodeAutoInstrumentations()],
});
sdk.start();
```

Add manual spans only around meaningful internal units of work (e.g., `applyDiscounts`, `chargeProvider`), carrying attributes on-call will filter by. Propagate context across every async boundary (HTTP headers, queue message metadata) or trace dies at the gap. Default: low-rate head-based sampling; keep 100% of errors if backend supports tail sampling.

### 6. Alerting

Alert on **symptoms users feel**, not causes:

```
SYMPTOM (page-worthy):           CAUSE (dashboard, not a page):
error rate > 1% for 5 min        CPU at 85%
p99 latency > 2s                 one pod restarted
queue age > 10 min               disk at 70%
```

**Error-budget worked example.** Checkout API, agreed 99.9% success SLO. Window: 100,000 eligible requests, 120 failures. Observed success 99.88%, error ratio 0.12%, 1.2× the permitted 0.1%: window burns budget faster than allowed. Before alerting on it, write down which requests are eligible, how retries count, and whether failures are measured at user or server boundary. Check numerator and denominator cover same population. Decide alert behavior with no traffic or missing series. Arithmetic is illustration, not a prescribed paging threshold.

Rules for every alert:

1. **It must be actionable.** If response is "ignore it, it self-heals", delete the alert.
2. **It links to a runbook** — even three lines: what it means, first query to run, escalation path.
3. **It has a threshold and duration** justified by SLO or historical data, not a guess.
4. Two severities only: **page** (user-facing, act now) and **ticket** (degradation, act this week). Third tier becomes noise that trains people to ignore everything.

#### Writing Runbooks

Store in `docs/runbooks/`, named after alert.

**Minimum viable runbook (three lines):**

```markdown
# Runbook: High Error Rate on /api/tasks
**Means:** DB connection pool likely exhausted, or a bad deploy.
**First check:** `SELECT count(*) FROM pg_stat_activity WHERE backend_type = 'client backend';`
  — if count > pool limit, see Step 2. (Swap in the equivalent for your database.)
**Escalate to:** #db-oncall or engineering on-call rotation.
```

**When to expand beyond three lines:** add steps only when first check alone can't decide. Five steps covering three most common causes beat twenty covering every edge case and getting skimmed.

**Keep runbooks current.** Update runbook when closing each incident that used it. Step wrong or missing? Fix it before marking incident resolved.

### 7. Verify the telemetry itself

Instrumentation is code; it can be wrong. Before calling work done, trigger paths and inspect actual output:

- Force error in staging; find it in logs by `requestId`, confirm fields structured (not `[object Object]`)
- Send test traffic; confirm metric series appear with expected labels and sane values
- Follow one request across services in tracing UI; no broken spans
- Fire each new alert once (temporarily lower threshold); confirm it reaches right channel and runbook link works

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll add logging after it works" | "After" becomes "after the first incident": costliest moment to discover you're blind. Instrument as you build. |
| "More logs = more observability" | Unstructured noise slows incidents down. Three queryable events beat three hundred prose lines. |
| "console.log is fine for now" | Unstructured output can't be filtered, correlated or alerted on. Structured logger costs five extra minutes, once. |
| "We can just look at the dashboards when something breaks" | Dashboards built without defined questions show everything except the answer. Start from on-call questions. |
| "Alert on everything important, we'll tune later" | Noisy pager trains people to ignore it. Tuning never happens; missed real page does. |
| "User ID as a metric label makes debugging easier" | Also makes metrics backend fall over. High-cardinality lookups belong in logs and traces. |
| "Tracing is overkill for our two services" | Two services already raise cross-service latency questions logs can't answer. Auto-instrumentation makes cost trivial. |

## Red Flags

- Feature PR with retries, queues or external calls and zero new telemetry
- One log stream fed by scheduler, webhook and manual runs, no field naming which produced the line
- Alerts that fire daily and get acknowledged without action
- "It works on my machine" as only evidence a production feature is healthy

## Verification

After instrumenting a feature, confirm:

- [ ] On-call questions written down; each signal maps to one
- [ ] All log output structured (JSON): stable event names, correlation ID on every line
- [ ] Every log sink with more than one entry point carries entry-point field, set at run start, propagated with correlation ID, not inferred downstream
- [ ] No secrets, tokens or unredacted PII in any log line (spot-check actual output)
- [ ] RED metrics on every new endpoint and external dependency, bounded label sets
- [ ] Latency is histogram; p95/p99 queryable
- [ ] One request followable end-to-end in tracing UI, no broken spans
- [ ] Every new alert symptom-based, runbook-linked, test-fired once
- [ ] Induced staging failure located via telemetry alone, without reading source

## Limitations

- Missing telemetry means unknown health, not zero errors. Alerts and dashboards must show "no data" distinctly from "healthy".
- Sampled traces can't give unbiased total request or error count without justified estimator; compute SLO ratios from unsampled metrics.
- Production instrumentation changes, alert delivery to real channels and test-firing pages need authorization for that environment.
