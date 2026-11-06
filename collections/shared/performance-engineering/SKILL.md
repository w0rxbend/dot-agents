---
name: performance-engineering
description: Plan and run load, stress, soak and spike tests (k6, Locust), profile backend CPU/memory/I/O (py-spy, pprof, clinic.js), and set performance SLOs and CI performance gates. Use for capacity validation, pre-launch load checks and regression gates; to fix one known slow page, query or endpoint use performance-optimization.
---

# Performance Engineering

## When to Use This Skill

**Common Triggers:**
- "Validate API can handle expected traffic"
- "Find maximum capacity and breaking points"
- "Detect memory leaks or resource exhaustion"
- "Set up performance testing in CI/CD"
- "How many instances do we need for the expected peak?"

**Use Cases:**
- Pre-launch capacity planning and load validation
- Post-refactor performance regression testing
- Investigating slow responses or high latency
- Detecting memory leaks in long-running services
- Measuring database query latency under load (fixes: performance-optimization)
- Validating auto-scaling configuration
- Setting performance SLOs and budgets

## Performance Testing Types

### Load Testing
**When to use:** Pre-launch capacity planning, regression testing after refactors, auto-scaling validation.

### Stress Testing
Find capacity limits and failure modes.

**When to use:** Capacity planning, understanding failure behavior, infrastructure sizing.

### Soak Testing
Find memory leaks, resource exhaustion and degradation over time.

**When to use:** Memory leak detection, connection pool cleanup checks, long-running batch job testing.

### Spike Testing
**When to use:** Auto-scaling validation, event-driven systems (product launches), confirming rate limiting works.

## Quick Decision Framework

**Which test type?**

```
What am I trying to learn?
├─ Can my system handle expected traffic? → LOAD TEST
├─ What's the maximum capacity? → STRESS TEST
├─ Will it stay stable over time? → SOAK TEST
└─ Can it handle traffic spikes? → SPIKE TEST
```

Testing patterns, load scenarios and result interpretation: `references/testing-types.md`.

## Load Testing Quick Starts

**Before any load, stress, soak or spike run:** confirm with user that target is an environment they own and may load (production only with explicit approval), plus peak VUs/RPS and duration. Never aim tests at third-party hosts.

### k6 (JavaScript)

**Installation:**
```bash
brew install k6  # macOS
sudo apt-get install k6  # Debian/Ubuntu, after adding Grafana's k6 apt repository (see k6 install docs)
```

**Basic Load Test:**
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },
    { duration: '1m', target: 20 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get('https://api.example.com/products');
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(1);
}
```

**Run:** `k6 run --no-usage-report script.js`. k6 sends anonymous usage stats by default; keep `--no-usage-report` (or env `K6_NO_USAGE_REPORT=true`) on every run, CI included.

Stress and soak scripts: `examples/k6/` (`stress-test.js`, `soak-test.js`). Spike profiles: `references/testing-types.md`.

### Locust (Python)

**Installation:**
```bash
pip install locust
```

**Basic Load Test:**
```python
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    host = "https://api.example.com"

    @task(3)
    def view_products(self):
        self.client.get("/products")

    @task(1)
    def view_product_detail(self):
        self.client.get("/products/123")
```

**Run:** `locust -f locustfile.py --headless -u 100 -r 10 --run-time 10m`

Fuller Locust example: `examples/locust/load_test.py`.

## Profiling Quick Starts

### When to Profile

| Symptom | Profiling Type | Tool |
|---------|----------------|------|
| High CPU (>70%) | CPU Profiling | py-spy, pprof, DevTools |
| Memory growing | Memory Profiling | memory_profiler, pprof heap |
| Slow response, low CPU | I/O Profiling | Query logs, pprof block |

### Python Profiling

**py-spy (Production-Safe):**
```bash
pip install py-spy

# Profile running process
py-spy record -o profile.svg --pid <PID> --duration 30

# Top-like view
py-spy top --pid <PID>
```

**Memory Profiling:**
```python
from memory_profiler import profile

@profile
def my_function():
    a = [1] * (10 ** 6)
    return a

# Run: python -m memory_profiler script.py
```

### Go Profiling

**pprof (Built-in):**
```go
import (
    "net/http"
    _ "net/http/pprof"
)

func main() {
    go func() {
        http.ListenAndServe("localhost:6060", nil)
    }()
    startApp()
}
```

**Capture profile:**
```bash
# CPU profile (30 seconds)
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# Interactive analysis
(pprof) top
(pprof) web
```

### TypeScript/JavaScript Profiling

**Chrome DevTools (Browser/Node.js):**

Node.js:
```bash
node --inspect app.js
# Open chrome://inspect
# Performance tab → Record
```

**clinic.js (Node.js):**
```bash
npm install -g clinic
NO_INSIGHT=1 clinic doctor -- node app.js
```

Always set `NO_INSIGHT=1` for clinic: without it, non-interactive runs send usage stats to Google Analytics.

Profiling workflows for Python, Go and Node.js: `references/profiling-guide.md`. Runnable py-spy script: `examples/profiling/python/pyspy_example.sh`.

## After Finding the Bottleneck

Skill measures and gates. It does not own fixes. Once a load test or profile points at a specific
slow query, endpoint, cache miss or page, hand off to **performance-optimization** (caching, N+1
queries, indexing, pagination, Core Web Vitals, bundle size). Then re-run same test here to confirm
gain. Background on common fixes: `references/optimization-strategies.md`, `references/frontend-performance.md`.

## Performance SLOs

### Recommended SLOs by Service Type

| Service Type | p95 Latency | p99 Latency | Availability |
|--------------|-------------|-------------|--------------|
| User-Facing API | < 200ms | < 500ms | 99.9% |
| Internal API | < 100ms | < 300ms | 99.5% |
| Database Query | < 50ms | < 100ms | 99.99% |
| Background Job | < 5s | < 10s | 99% |
| Real-time API | < 50ms | < 100ms | 99.95% |

### SLO Selection Process

1. Measure baseline performance
2. Identify user expectations
3. Set targets at or slightly below measured baseline, so SLO is met from day one
4. Tighten targets as reliability improves

SLO framework and performance budgets: `references/slo-framework.md`.

## CI/CD Integration

### Performance Testing in Pipelines

**GitHub Actions example:**
```yaml
name: Performance Tests

on:
  pull_request:
    branches: [main]

jobs:
  load-test:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Install k6
        uses: grafana/setup-k6-action@v1   # pin a k6 version via its `k6-version` input for reproducible runs

      - name: Run load test
        run: k6 run --no-usage-report tests/load/api-test.js
```

Pin third-party actions to full commit SHAs (version tag in a comment); keep `permissions` read-only.

**Performance budgets:**
```javascript
// k6 test with thresholds (fail build if violated)
export const options = {
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};
```

## Profiling Workflow

**Standard process:**
1. Observe symptoms (high CPU, memory growth, slow response)
2. Hypothesize bottleneck (CPU? Memory? I/O?)
3. Pick profiling type from hypothesis
4. Run profiler under realistic load
5. Analyze profile (flamegraph, call tree)
6. Identify hot spots (top 20% functions using 80% resources)
7. Optimize bottlenecks, biggest first
8. Re-profile to validate improvement

**Best practices:**
- Use sampling profilers (py-spy, pprof) in production (low overhead)

## Tool Recommendations

### Load Testing

**Primary: k6** (JavaScript-based, Grafana-backed)
- JavaScript DSL (ES6+)
- Grafana/Prometheus integration
- Multi-protocol (HTTP/1.1, HTTP/2, WebSocket, gRPC)

**When to use:** Modern APIs, microservices, CI/CD integration.

**Alternative: Locust** (Python-based)
- Web UI for real-time monitoring
- Handles complex user scenarios

**When to use:** Python-heavy teams, complex user flows.

### Profiling

**Python:**
- py-spy (sampling, production-safe)
- cProfile (deterministic, detailed)
- memory_profiler (memory leak detection)

**Go:**
- pprof (built-in, CPU/heap/goroutine/block profiling)

**TypeScript/JavaScript:**
- Chrome DevTools (browser/Node.js)
- clinic.js (Node.js performance suite)

Tool comparisons: `references/testing-types.md`, `references/profiling-guide.md`.

## Reference Documentation

**Detailed Guides:**
- `references/testing-types.md` - Load, stress, soak, spike testing patterns
- `references/profiling-guide.md` - CPU, memory, I/O profiling across languages
- `references/optimization-strategies.md` - Caching, database, API optimization
- `references/frontend-performance.md` - Core Web Vitals, bundle optimization
- `references/slo-framework.md` - Setting SLOs, performance budgets
- `references/benchmarking.md` - Benchmarking best practices

**Examples:**
- `examples/k6/` - Load, stress and soak tests
- `examples/locust/load_test.py` - Python-based load testing
- `examples/profiling/python/pyspy_example.sh` - py-spy CPU profiling
- `examples/optimization/api_optimization.ts` - API caching and pagination patterns

## Related Skills

Full testing strategies: `testing-strategies` skill.

CI/CD integration patterns: `building-ci-pipelines` skill.

Fixing a specific measured bottleneck (frontend, query, algorithm): `performance-optimization` skill.

Kubernetes resource requests/limits and autoscaling validated by load tests: `operating-kubernetes` skill.
