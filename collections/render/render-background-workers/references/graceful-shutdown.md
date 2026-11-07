# Graceful shutdown for Render workers

Render stops worker instances on deploys, manual restarts and scale-in. Process must exit cleanly within configured window, or work may be lost or duplicated (per queue’s ack/retry semantics).

## Platform behavior

1. Render sends `SIGTERM`.
2. Platform waits up to `maxShutdownDelaySeconds` (1–300, default 30).
3. If process still runs, Render sends `SIGKILL` (not catchable).

Configure `maxShutdownDelaySeconds` in Dashboard (service settings) or on worker service in `render.yaml`. Set it to cover longest job allowed to finish during shutdown, plus buffer for flushing metrics, closing DB pools, etc.

## General pattern

1. **Stop accepting new jobs** — stop consumer loop, pause polling or drain framework’s internal fetch.
2. **Finish current job** or **checkpoint** durable progress so another worker can resume safely.
3. **Close connections** — Redis/Postgres pools, HTTP clients.
4. **Exit with code 0**.

## Python

**Low-level handler**

```python
import signal
import sys

def handle_sigterm(signum, frame):
    # set a flag; main loop checks it and stops dequeuing
    global shutting_down
    shutting_down = True

signal.signal(signal.SIGTERM, handle_sigterm)
```

**Celery** — run cleanup from lifecycle signals like `worker_shutting_down`. Make tasks honor soft time limit or cooperative cancel flag, so shutdown finishes within `maxShutdownDelaySeconds`.

## Ruby (Sidekiq)

Sidekiq handles SIGTERM by default: stops fetching new work, waits for in-flight jobs up to configurable timeout (`:timeout` in Sidekiq options, seconds). Keep that timeout **≤** Render’s `maxShutdownDelaySeconds` minus small margin.

## Node.js

```javascript
let accept = true;

process.on("SIGTERM", async () => {
  accept = false;
  await worker.close(); // BullMQ: stops accepting, waits for active jobs
  process.exit(0);
});
```

**BullMQ** — prefer `worker.close()` (and `queue.close()` where applicable) so active jobs complete per library defaults. For stricter bounds, tune `stalledInterval` / job locks.

## Go

Use `signal.NotifyContext` (or `signal.Notify` + `context.WithCancel`) to cancel root context passed to consumer loop and job handlers. Wait on `sync.WaitGroup` or channels until in-flight work finishes, then exit.

```go
ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
defer stop()
// run consumer until ctx.Done(), then drain workers
```

## Anti-patterns

- **Ignoring SIGTERM** — process lives until `SIGKILL`, often mid-job: lost work or stuck queue entries.
- **`maxShutdownDelaySeconds` too low** for p95 job duration — frequent hard kills and retries.
- **No idempotency** — job retried after ambiguous failure at shutdown can cause duplicate side effects.
