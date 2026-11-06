# Profiling and Continuous Profiling

## On-Demand Profiling with `pprof`

pprof endpoints MUST be protected with basic auth. NEVER expose them publicly: they leak sensitive runtime information and invite DoS abuse.

→ See `samber/cc-skills-golang@golang-troubleshooting` pprof.md for full pprof CLI reference (profile types, capturing, analyzing, commands).

`goroutineleak` profile (`/debug/pprof/goroutineleak`, generally available since Go 1.27) is worth exposing alongside standard ones. It reports goroutines blocked on unreachable concurrency primitives, which standard `goroutine` profile doesn't surface directly. Since Go 1.27, tracebacks for `go 1.27+` modules carry `runtime/pprof` goroutine labels by default. If labels could leak sensitive request data into crash logs, disable with `GODEBUG=tracebacklabels=0`.

## Continuous Profiling with Pyroscope

Continuous profiling runs always-on in background with low overhead (~2-5% CPU), so profiles exist after the fact. Toggle with environment variable.

```go
import "github.com/grafana/pyroscope-go"

func setupContinuousProfiling() {
    if os.Getenv("PROFILING_ENABLED") != "true" {
        return
    }

    _, err := pyroscope.Start(pyroscope.Config{
        ApplicationName:   "my-service",
        ServerAddress:     os.Getenv("PYROSCOPE_URL"), // no user:pass in URL; credentials go below
        BasicAuthUser:     os.Getenv("PYROSCOPE_USER"),
        BasicAuthPassword: os.Getenv("PYROSCOPE_PASSWORD"),
        ProfileTypes: []pyroscope.ProfileType{
            pyroscope.ProfileCPU,
            pyroscope.ProfileAllocObjects,
            pyroscope.ProfileAllocSpace,
            pyroscope.ProfileInuseObjects,
            pyroscope.ProfileInuseSpace,
            pyroscope.ProfileGoroutines,
            pyroscope.ProfileMutexCount,
            pyroscope.ProfileMutexDuration,
            pyroscope.ProfileBlockCount,
            pyroscope.ProfileBlockDuration,
        },
    })
    if err != nil {
        slog.Error("failed to start pyroscope", "error", err)
    } else {
        slog.Info("continuous profiling enabled")
    }
}
```

## Cost of Continuous Profiling

Overhead hits every running instance: CPU to collect stack samples, memory for buffering, network to ship profiles to backend. Typically low (~2-5% CPU), but **per-instance and always-on**.

**Cost factors:**

- **CPU overhead** — profiling consumes CPU. In CPU-bound services, even 2-5% matters.
- **Network/storage** — profile data ships continuously to Pyroscope/your backend. More replicas multiply this.
- **All profile types enabled** — each extra type (mutex, block, goroutine) adds overhead.

**Mitigation:**

- Toggle via environment variable (`PROFILING_ENABLED`). Enable only when needed or on subset of instances
- Start with CPU + heap profiles only. Add mutex/block/goroutine when investigating specific issues
- Large deployments: enable on fraction of replicas (e.g., 1 in 10), not all

## When to Profile

1. Metrics show high CPU/memory usage → look at CPU/heap profiles
2. P99 latency spikes → CPU profile + mutex profile to find contention
3. Goroutine count growing → goroutine profile to find leaks
4. Before and after optimization → compare profiles to verify improvement
