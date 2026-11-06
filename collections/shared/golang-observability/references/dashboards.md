# Grafana Dashboards for Go Services

Community Grafana dashboards for Go runtime performance. They use metrics `github.com/prometheus/client_golang` exposes by default. No custom instrumentation needed.

## Recommended Dashboards

| Dashboard | ID | What it shows |
| --- | --: | --- |
| [Go Host & Runtime Metrics](https://grafana.com/grafana/dashboards/21221-go-host-runtime-metrics-dashboard/) | 21221 | Host metrics + Go runtime (goroutines, heap, GC, threads) in one view |
| [Go Processes](https://grafana.com/grafana/dashboards/6671-go-processes/) | 6671 | Multi-process comparison — CPU, memory, goroutines, GC across all Go services |
| [Go Metrics](https://grafana.com/grafana/dashboards/10826-go-metrics/) | 10826 | Focused Go runtime view — memory breakdown, GC pauses, allocations, goroutines |

## How to Install

In Grafana, open **Dashboards > New > Import**, enter dashboard ID (e.g., `21221`), select Prometheus data source.

Needs default Go collector metrics (`go_goroutines`, `go_memstats_*`, `go_gc_duration_seconds`, `process_*`).

## When to Use Each

- **21221** (Host & Runtime) — daily monitoring of one Go service plus its host. Best default.
- **6671** (Go Processes) — compare Go services or replicas side by side. Spots cross-instance regressions during deployments.
- **10826** (Go Metrics) — deep dive into memory and GC of one service. Best for performance investigations.
