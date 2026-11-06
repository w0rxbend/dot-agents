---
name: render-background-workers
description: >-
  Sets up and configures background workers on Render for queue-based job
  processing. Use when the user needs to process async jobs, consume from a
  queue, run Celery/Sidekiq/BullMQ/Asynq/Oban workers, handle graceful
  shutdown with SIGTERM, wire a worker to Key Value (Redis), or choose between
  workers and cron jobs for background work.
  Trigger terms: background worker, async jobs, queue consumer, Celery,
  Sidekiq, BullMQ, Asynq, Oban, job processing, SIGTERM, graceful shutdown.
license: MIT
compatibility: Render background worker services
metadata:
  author: Render
  version: "1.0.0"
  category: compute
---

# Render Background Workers

Worker services on Render: processes that consume queue jobs instead of serving HTTP. Pair with **render-blueprints**, **render-env-vars** and **render-networking** for `render.yaml` and private connectivity.

## When to Use

- Design or debug queue-backed workers (Celery, Sidekiq, BullMQ, Asynq, etc.)
- Choose worker, Cron Job or Workflow for background work
- Configure Render Key Value as broker (not cache) with correct eviction policy
- Implement graceful shutdown so deploys do not lose in-flight jobs

## How Workers Work

- Long-running, no inbound (HTTP) traffic. Unlike web or private services, workers get no public URL or internal hostname. **Workers cannot receive private network traffic directed at them.**
- Typical pattern: poll loop. Process connects to queue backend (often Render Key Value, Redis-compatible Valkey 8) and pulls jobs.
- Workers can open outbound connections: private network to PostgreSQL, Key Value, private services, web services (internal URLs); also public internet. Plan and firewall rules apply.

## Queue Framework Overview

| Framework | Language | Queue backend |
|-----------|----------|---------------|
| Celery | Python | Redis / Key Value |
| Sidekiq | Ruby | Redis / Key Value |
| BullMQ | Node.js | Redis / Key Value |
| Asynq | Go | Redis / Key Value |
| Oban | Elixir | **Postgres** (not Redis) |

## Pairing with Key Value

- Use Render Key Value as job broker when framework expects Redis.
- Set maxmemory policy to **`noeviction`**. `allkeys-lru` and similar suit caches; evicting queue keys **drops jobs**.
- In Blueprint, wire `REDIS_URL` (or framework equivalent) via `fromService` with `type: keyvalue`, `property: connectionString`.
- Blueprints require `ipAllowList` on Key Value: CIDRs allowed to reach instance (often `[]` for private-network-only; see **render-blueprints** / Key Value field reference).

Per-framework (Celery, Sidekiq, BullMQ, Asynq, Oban) minimal app + YAML examples: `references/queue-framework-setup.md`.

## Worker vs Cron vs Workflow

| Need | Use | Why |
|------|-----|-----|
| Always-on queue consumer | Background Worker | Polls continuously; long-lived |
| Periodic scheduled task | Cron Job | Runs on schedule, exits; 12h max per run |
| Distributed parallel compute | Workflow | Each run gets own instance; fan-out |
| High-volume or bursty jobs | Workflow | Scales per run; no idle instance cost between runs |

## Graceful Shutdown

- Before stopping instance, Render sends `SIGTERM`, waits up to `maxShutdownDelaySeconds` (1–300, default 30), then sends `SIGKILL`.
- Worker steps: (1) stop accepting new jobs, (2) finish current job or checkpoint progress, (3) close connections, (4) exit 0.
- Set `maxShutdownDelaySeconds` to at least longest safe job duration (Dashboard or Blueprint).

Language- and framework-specific handlers: `references/graceful-shutdown.md`.

## Blueprint Configuration

Minimal pattern: `type: worker`, `runtime`, `buildCommand`, `startCommand`, plus `envVars` from Key Value.

```yaml
services:
  - type: keyvalue
    name: jobs
    plan: starter
    region: oregon
    ipAllowList: []

  - type: worker
    name: task-worker
    runtime: python
    region: oregon
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A tasks worker --loglevel=info
    envVars:
      - key: REDIS_URL
        fromService:
          name: jobs
          type: keyvalue
          property: connectionString
```

Optional: `maxShutdownDelaySeconds` on worker for long-draining jobs.

## Related Skills

- **render-deploy** — First deploy, CLI, service creation
- **render-blueprints** — Full `render.yaml` schema, `fromService`, projects
- **render-networking** — Private URLs, what can call what
- **render-scaling** — Worker plans, instance counts, limits
