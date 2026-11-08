# Investigation Session Setup

Tools and techniques for **temporary deep-dive performance investigation**, not everyday monitoring. Enable for hours or days while debugging specific issue, then disable.

## Table of Contents

- [Setting Up a Session](#setting-up-a-session)
- [Prometheus Go Runtime Collector](#prometheus-go-runtime-collector)
  - [Key Series](#key-series)
- [PromQL Deep-Dive Queries](#promql-deep-dive-queries)
  - [GC pressure](#gc-pressure)
  - [Memory leak detection](#memory-leak-detection)
  - [Goroutine leak detection](#goroutine-leak-detection)
  - [CPU saturation](#cpu-saturation)
  - [Post-deploy regression detection](#post-deploy-regression-detection)
  - [Example alerting rules](#example-alerting-rules)
- [Host-Level Correlation](#host-level-correlation)
- [Cost Warnings](#cost-warnings)

## Setting Up a Session

Before profiling, set up high-resolution data collection. These steps change production config and restart pods: confirm with user before each; revert afterward.

1. **Reduce Prometheus scrape interval** to <=10s on target instance (normally 15-30s). More data points in short window reveal patterns 30s intervals miss. Revert afterward.

2. **Enable pprof** via environment variable, no recompile:

   ```bash
   kubectl set env deployment/my-service PPROF_ENABLED=true
   kubectl rollout restart deployment/my-service
   ```

3. **Enable continuous profiling** on target instance only, not fleet-wide. Pyroscope/Parca on one instance is manageable; 50 replicas overwhelm backend.

   ```bash
   kubectl set env deployment/my-service PYROSCOPE_ENABLED=true
   kubectl rollout restart deployment/my-service
   ```

4. **Enable debug logging** via env var if needed, only on target instance. Significant throughput impact:

   ```bash
   kubectl set env deployment/my-service LOG_LEVEL=debug
   kubectl rollout restart deployment/my-service
   ```

**Key principle:** all costly debug features (pprof HTTP, continuous profiling, debug log level, trace collection) SHOULD be configurable via environment variables, for instant toggle without recompile. Design for this from day one.

## Prometheus Go Runtime Collector

`prometheus/client_golang` library automatically registers Go runtime metric collectors. Invaluable during investigation: time-series of memory, GC, goroutines, CPU complements point-in-time profiles.

When using `prometheus/client_golang`, verify collector setup and available options in its official documentation.

### Key Series

See [prometheus-go-metrics.md](./prometheus-go-metrics.md): **exhaustive reference** of all Go runtime metrics (verified from official sources). **Note:** runtime/metrics list varies by Go version; use `metrics.All()` at runtime for yours.

**Performance note:** `go_memstats_*` metrics call `runtime.ReadMemStats()` internally, triggering short stop-the-world pause. Go 1.17+ runtime/metrics collector (`collectors.NewGoCollector()`) uses cheaper `runtime/metrics`. Prefer modern collector in high-throughput services:

```go
import "github.com/prometheus/client_golang/prometheus/collectors"

// Use runtime/metrics-based collector (lower overhead)
reg := prometheus.NewRegistry()
reg.MustRegister(collectors.NewGoCollector(
    collectors.WithGoCollectorRuntimeMetrics(collectors.MetricsAll),
))
reg.MustRegister(collectors.NewProcessCollector(collectors.ProcessCollectorOpts{}))
```

## PromQL Deep-Dive Queries

Use during investigation with reduced scrape interval.

### GC pressure

| PromQL | What to look for |
| --- | --- |
| `rate(go_gc_duration_seconds_count[5m])` | GC cycles/s. >2/s sustained = excessive allocation rate. Reduce allocations per request. |
| `rate(go_gc_duration_seconds_sum[5m]) / rate(go_gc_duration_seconds_count[5m])` | Average GC pause. Increasing trend = heap growing or too many pointers to scan. |
| `go_gc_duration_seconds{quantile="1"}` | Worst-case GC pause. Spikes here cause tail latency (P99). |

### Memory leak detection

| PromQL | What to look for |
| --- | --- |
| `go_memstats_alloc_bytes` | Should stay roughly stable under constant load. Continuous increase = memory leak. |
| `rate(go_memstats_alloc_bytes_total[5m])` | Allocation rate (bytes/s). Compare before/after deploy; significant increase = new allocation pattern. |
| `process_resident_memory_bytes - go_memstats_sys_bytes` | Gap = non-Go memory (cgo, mmap). Growing gap = non-Go leak. |

### Goroutine leak detection

| PromQL | What to look for |
| --- | --- |
| `go_goroutines` | Should correlate with load. Growing independently of traffic = leak. |
| `delta(go_goroutines[1h])` | Net goroutine change over 1h. Positive without load increase = leak. |

### CPU saturation

| PromQL | What to look for |
| --- | --- |
| `rate(process_cpu_seconds_total[5m])` | CPU cores consumed. Compare to GOMAXPROCS. |
| `rate(process_cpu_seconds_total[5m]) / <GOMAXPROCS>` | CPU utilization ratio. >0.8 sustained = CPU-saturated. |

### Post-deploy regression detection

| PromQL | What to look for |
| --- | --- |
| `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` | P99 latency increase after deploy = performance regression. Requires app-level histogram. |

### Example alerting rules

```yaml
# GC taking too much time
- alert: HighGCPauseTime
  expr: rate(go_gc_duration_seconds_sum[5m]) / rate(go_gc_duration_seconds_count[5m]) > 0.01
  for: 10m
  annotations:
    summary: "Average GC pause >10ms — reduce allocations or tune GOGC"

# Goroutine leak
- alert: GoroutineLeak
  expr: go_goroutines > 10000
  for: 5m
  annotations:
    summary: "Goroutine count >10K — check for leaked goroutines"

# Memory approaching container limit
- alert: MemoryNearLimit
  expr: predict_linear(process_resident_memory_bytes[1h], 3600) > <container_limit_bytes>
  for: 15m
  annotations:
    summary: "RSS projected to exceed container limit within 1h"
```

Adjust thresholds per application: data pipeline has different baselines than API server.

## Host-Level Correlation

Go runtime metrics alone miss full picture. Host metrics show whether problem is application or infrastructure.

- **`node_exporter`** — host CPU, memory, disk I/O, network. Correlate with Go app metrics: high `node_cpu_seconds_total` with low `process_cpu_seconds_total` = noisy neighbor, not your app.
- **`process-exporter`** — per-process metrics on Linux. Use when multiple Go services share host.

## Cost Warnings

**Profiles and traces are expensive to collect.** Keep short-term and localized:

- **pprof CPU profiling** — CPU-intensive during capture. Don't run 30s profiles back-to-back in production; space them out.
- **Pyroscope continuous profiling** — ~2-5% CPU overhead **per instance, always-on**. At scale (hundreds of instances), compute cost and backend storage add up. Enable on instance subset or on-demand via environment variable. See `samber/cc-skills-golang@golang-observability` skill for Pyroscope setup.
- **Execution traces** — generate large files fast (MB/s). Capture 5-10s max. Longer traces are unwieldy, slow to analyze.
- **Debug log level** — significant throughput impact (allocation, I/O overhead). Never leave on permanently.
