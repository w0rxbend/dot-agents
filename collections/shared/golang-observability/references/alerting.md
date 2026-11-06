# Alerting

> Multi-window burn-rate SLO alerting and PromQL patterns for application metrics: see [metrics.md](metrics.md).

## Table of Contents

- [The Four Golden Signals](#the-four-golden-signals)
- [Awesome Prometheus Alerts](#awesome-prometheus-alerts)
  - [Categories](#categories)
  - [How to Use It](#how-to-use-it)
  - [Integration Example](#integration-example)
  - [Workflow for New Dependencies](#workflow-for-new-dependencies)
- [Go Runtime Alerts](#go-runtime-alerts)
- [Alert Severity Levels](#alert-severity-levels)
- [Common Mistakes](#common-mistakes)

## The Four Golden Signals

Every Go service SHOULD alert on all four golden signals from Google's SRE book:

| Signal | What it measures | Example metric | Alert trigger |
| --- | --- | --- | --- |
| **Latency** | Time to serve request | `http_request_duration_seconds` (Histogram) | P99 > 2s for 5 minutes |
| **Traffic** | Demand on system | `http_requests_total` (Counter) | Zero requests for 10 minutes |
| **Errors** | Rate of failed requests | `http_requests_total{status=~"5.."}` (Counter) | Error ratio > 1% for 5 minutes |
| **Saturation** | How full system is | `db_connections_active / db_connections_max` | Pool > 90% saturated for 5 minutes |

## Awesome Prometheus Alerts

[awesome-prometheus-alerts](https://samber.github.io/awesome-prometheus-alerts/): ~500 curated, ready-to-use Prometheus alerting rules. Starting point for infrastructure and dependency alerting.

### Categories

| Category | Rules | Covers |
| --- | --: | --- |
| **Basic Resource Monitoring** | ~107 | Host metrics, Docker containers, hardware |
| **Databases and Brokers** | ~233 | PostgreSQL, MySQL, Redis, MongoDB, Kafka, RabbitMQ, etc. |
| **Reverse Proxies and Load Balancers** | ~45 | Nginx, Apache, HAProxy, Traefik |
| **Runtimes** | ~4 | PHP-FPM, JVM, Sidekiq |
| **Orchestrators** | ~74 | Kubernetes, Nomad, Consul, ArgoCD |
| **Network, Security, and Storage** | ~40 | Ceph, MinIO, SSL/TLS, DNS |

### How to Use It

Rules grouped by technology. Each is ready-to-use Prometheus YAML with customizable thresholds and `for:` durations.

1. **Find by technology** — locate relevant database, message broker or infrastructure component
2. **Adapt the YAML rule** — tune thresholds (`> 0.01`, `> 100`, etc.) and `for:` duration to your SLOs and traffic patterns
3. **Place in Prometheus config** — add to `prometheus/rules/` directory

### Integration Example

Prometheus loads alerting rules from YAML files its config references. Put copied rules in your rules directory:

```yaml
# prometheus/rules/postgresql.yml
groups:
  - name: postgresql
    rules:
      # From awesome-prometheus-alerts — PostgreSQL section
      - alert: PostgresqlDown
        expr: pg_up == 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL down (instance {{ $labels.instance }})"
          description: "PostgreSQL instance is down.\n  VALUE = {{ $value }}"

      - alert: PostgresqlTooManyConnections
        expr: sum by (instance, datname) (pg_stat_activity_count{datname!~"template.*|postgres"}) > pg_settings_max_connections * 0.8
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL too many connections (> 80%) (instance {{ $labels.instance }})"
          description: "PostgreSQL has {{ $value }} connections on {{ $labels.datname }}."
```

```yaml
# prometheus.yml
rule_files:
  - "rules/*.yml"
```

### Workflow for New Dependencies

When adding infrastructure dependency (database, cache, message broker, reverse proxy) to Go service, follow steps above and verify exporter is deployed (e.g., `postgres_exporter`, `redis_exporter`) before adding rules. Alerts depend on exporter metrics.

## Go Runtime Alerts

Prometheus Go client exposes runtime metrics automatically. Alert on them to catch resource leaks and GC pressure before users notice.

```yaml
# prometheus/rules/go-runtime.yml
groups:
  - name: go-runtime
    rules:
      # Goroutine leak — count growing steadily indicates a leak
      # Diagnose: GET /debug/pprof/goroutine?debug=1 to see goroutine stack traces
      - alert: GoroutineLeak
        expr: go_goroutines > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High goroutine count (instance {{ $labels.instance }})"
          description: "Goroutine count is {{ $value }}, possible leak."

      # GC taking too long — P99 GC pause > 100ms degrades tail latency
      - alert: HighGCDuration
        expr: go_gc_duration_seconds{quantile="1"} > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High GC duration (instance {{ $labels.instance }})"
          description: "Max GC pause is {{ $value }}s. Check heap allocations."

      # Heap growing unbounded — likely a memory leak
      - alert: HighMemoryUsage
        expr: go_memstats_alloc_bytes / go_memstats_sys_bytes > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage (instance {{ $labels.instance }})"
          description: "Allocated heap is {{ $value | humanizePercentage }} of system memory."

      # Too many threads — usually caused by blocking syscalls or cgo
      - alert: HighThreadCount
        expr: go_threads > 500
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High OS thread count (instance {{ $labels.instance }})"
          description: "Thread count is {{ $value }}. Check for blocking syscalls."
```

## Alert Severity Levels

Two severity levels: "wake someone up" vs "look at it tomorrow":

| Severity | Action | `for:` duration | Example |
| --- | --- | --- | --- |
| **critical** | Page on-call | 2-5 minutes | Service down, error rate > 5%, data loss risk |
| **warning** | Create ticket | 10-30 minutes | P99 latency high, connection pool > 80%, goroutine leak |

`for:` sets how long condition must hold before alert fires. Short durations catch fast incidents but risk false positives from transient spikes. Long durations cut noise but delay response.

**Guidelines:**

- NEVER set `for: 0m` on non-binary alerts — one bad scrape triggers false page
- Binary alerts (service up/down) can use `for: 0m` or `for: 1m`

## Common Mistakes

```yaml
# Bad -- irate() is too volatile for alerts, reacts to a single scrape interval
# A brief spike or a single slow request triggers the alert
- alert: HighErrorRate
  expr: irate(http_requests_total{status=~"5.."}[5m]) > 0.01

# Good -- rate() smooths over the full window, reducing false positives
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
  for: 5m
```

```yaml
# Bad -- no "for:" duration, fires on a single bad scrape
- alert: HighLatency
  expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2

# Good -- must be true for 5 minutes to fire
- alert: HighLatency
  expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 5m
```
