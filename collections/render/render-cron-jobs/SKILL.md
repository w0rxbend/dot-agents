---
name: render-cron-jobs
description: >-
  Configures and troubleshoots scheduled tasks on Render using cron job
  services. Use when the user needs to run something on a schedule, write a
  cron expression, set up a periodic job, migrate from Heroku Scheduler,
  choose between cron jobs and background workers, or fix a cron that isn't
  firing.
  Trigger terms: cron job, scheduled task, periodic job, cron expression,
  schedule, run every, timer, Heroku Scheduler migration.
license: MIT
compatibility: Render cron job services
metadata:
  author: Render
  version: "1.0.0"
  category: compute
---

# Render Cron Jobs

## When to Use

- **Scheduled** work: **starts on cron**, runs command, **exits** when done
- Choosing **cron**, **background worker**, or **workflow** for periodic or long-running jobs
- **Blueprint** fields: `type: cron`, `schedule`, commands
- **Constraints**: no disk, single concurrent run, 12-hour max duration, private-network **outbound** only
- **UTC** scheduling pitfalls (expressions **not** local time)

## Configuration

- **Schedule**: **cron expression, evaluated in UTC**, not team’s local timezone. All Dashboard and Blueprint times UTC.
- **Command**: any valid **Linux shell command** or **bash script** path. Process must **exit** when done. **Billed by run duration**, prorated by the second.
- **Source**:
  - **Git repository** — Render **builds on push** (same deploy model as other repo-backed services); built artifact runs on each scheduled invocation.
  - **Prebuilt Docker image** — image **pulled before each run**, **not retained between runs** (no warm image-layer cache across invocations, unlike long-lived service).

## Constraints

- **No persistent disk** — cron job services **cannot** provision or attach Render persistent disks. Use object storage or databases.
- **Single-run guarantee** — at most **one active run** per cron service at a time. New scheduled tick never starts second overlapping instance.
- **Maximum run length**: **12 hours** per invocation.
- **Pricing**: **$1/month minimum** per cron job service; usage **prorated by the second** beyond plan/minimum rules for your account.
- **Private network**: cron jobs **can send** traffic **to** other private-network services. They **cannot receive** inbound private-network connections (no internal hostname to accept traffic).

## Execution Behavior

- **Manual “Trigger Run”** during **active** run: Render **cancels** active run, then **starts** new one.
- **New Git build / deploy** does **not** affect run **in progress**. In-flight process keeps its starting revision until exit.
- **UTC everywhere**: cron expressions and “midnight” in docs mean **UTC**. Common mistake: copying local-time schedule without converting to UTC.

## Cron vs Worker vs Workflow

| Need | Use | Why |
|------|-----|-----|
| Periodic task **under 12h** | **Cron Job** | Scheduled, simple, exits when done |
| **Continuous** job processing | **Background Worker** | Always running, polls queue |
| Periodic but **over 12h** | **Background Worker** | No 12h cron run ceiling |
| **Scheduled parallel** compute | **Cron Job + Workflow** | Cron triggers workflow runs on schedule; workflows fan out or orchestrate parallel steps |

## Blueprint Configuration

```yaml
services:
  - type: cron
    name: nightly-cleanup
    schedule: "0 * * * *" # hourly at minute 0 — must be quoted in YAML
    buildCommand: pip install -r requirements.txt
    startCommand: python cleanup.py
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: my-db
          property: connectionString
```

- **`schedule`**: standard five-field cron (`minute hour day-of-month month day-of-week`), **UTC**.
- **`buildCommand`** / **`startCommand`**: same roles as other non-Docker services. Image-backed crons use image and start command as configured.
- **`envVars`**: same patterns as web services and workers (secrets, linked databases, etc.).

**YAML note**: `schedule` value **must be quoted** so `*` and similar characters are not parsed as YAML aliases or flow syntax.

## References

| Topic | File |
|--------|------|
| Expression examples, framework commands, errors, env vars | `references/cron-patterns.md` |
| Heroku Scheduler → Render mapping, blueprint example | `references/migration-from-scheduler.md` |

## Related Skills

- **render-deploy** — First-time deploy, service creation, Dashboard flow
- **render-blueprints** — Full `render.yaml` schema, previews, common mistakes
- **render-background-workers** — Long-lived processes, queues, no 12h cap
- **render-workflows** — Orchestrated and parallel jobs, often triggered on schedule from cron
