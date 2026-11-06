---
name: render-disks
description: >-
  Attaches and manages persistent disks on Render services—mount paths, sizing,
  snapshots, file transfers, and single-instance constraints. Use when the user
  needs persistent storage, file uploads, a custom database on disk, CMS media
  storage, or needs to understand why their service can't scale horizontally
  or use zero-downtime deploys.
  Trigger terms: persistent disk, disk, storage, mount path, sizeGB, SSD,
  file uploads, snapshots, disk restore, ephemeral filesystem.
license: MIT
compatibility: Render paid web services, private services, and background workers
metadata:
  author: Render
  version: "1.0.0"
  category: storage
---

# Render Persistent Disks

Persistent disks: high-performance SSDs attached to Render service. Keep filesystem changes across deploys and restarts. Without disk, services have an **ephemeral filesystem**—all local file changes lost on every deploy.

## When to Use

- Storing **file uploads**, CMS media, user-generated content
- Running **self-managed database** (MySQL, MongoDB, ClickHouse) on Render
- Deploying **stateful infrastructure** (Elasticsearch, Kafka, RabbitMQ, Mattermost)
- Understanding **why scaling is blocked** or **zero-downtime deploys are disabled**
- **Restoring data** from automatic disk snapshot

For managed databases, prefer **Render Postgres** (render-postgres) or **Key Value** (render-keyvalue) over self-managed alternatives on disk.

## Critical Constraints

Understand these **before** attaching disk:

| Constraint | Impact |
|------------|--------|
| **Single instance only** | Cannot scale horizontally (`numInstances` must be 1, no autoscaling) |
| **No zero-downtime deploys** | Old instance stops before new one starts (brief downtime each deploy) |
| **Runtime access only** | Disk not available during `buildCommand` or `preDeployCommand` (those run on separate compute) — move logic to start command |
| **Not accessible from other services** | Only attached service can read/write disk |
| **Not available on cron jobs** | Attach to web service, private service, or background worker instead |
| **Not available on one-off jobs** | One-off jobs run on separate compute without disk access |
| **Can increase size, cannot decrease** | Start small, grow as needed |

## Setup

### Dashboard

1. Go to service's **Disks** page
2. Set **mount path** (absolute path for persistent data)
3. Choose **size** in GB
4. Click **Add disk** — triggers new deploy

### Blueprint

```yaml
services:
  - type: web
    name: cms
    runtime: node
    plan: starter
    region: oregon
    buildCommand: npm ci && npm run build
    startCommand: npm start
    disk:
      name: cms-data
      mountPath: /var/data
      sizeGB: 10
```

## Mount Path

Only files written **under mount path** persist. Everything else stays ephemeral.

| Runtime | Source code path | Example mount path |
|---------|------------------|--------------------|
| Node.js, Python, Ruby, Elixir, Rust | `/opt/render/project/src` | `/opt/render/project/src/uploads` |
| Go | `/opt/render/project/go/src/github.com/<user>/<repo>` | `.../data` |
| Docker | Dockerfile's `WORKDIR` (commonly `/app`) | `/app/storage` |

### Disallowed mount paths

Cannot mount at: `/`, `/opt`, `/opt/render`, `/opt/render/project`, `/opt/render/project/src`, `/home`, `/home/render`, `/etc`, `/etc/secrets`.

Subdirectories of these paths fine (e.g. `/opt/render/project/src/uploads`).

## Snapshots

- Render creates **automatic snapshot every 24 hours**
- Snapshots kept **at least 7 days**
- Restore from service's **Disks** page in Dashboard
- **Full restore only** — cannot restore individual files
- **Destructive** — all changes after snapshot lost

**Do not restore snapshots for custom database recovery.** Use database-native backup tools (mysqldump, mongodump) instead. Disk snapshots may capture corrupted database state.

## File Transfers

### SCP (via SSH)

```bash
# Download from service
scp -s YOUR_SERVICE@ssh.YOUR_REGION.render.com:/mount/path/file ./local-file

# Upload to service
scp -s ./local-file YOUR_SERVICE@ssh.YOUR_REGION.render.com:/mount/path/file
```

Requires SSH access enabled for service.

### Magic-Wormhole

Available on all native runtimes (install manually on Docker):

```bash
# On the service shell
wormhole send /mount/path/file

# On your local machine
wormhole receive
```

## Common Patterns

| Pattern | Service type | Mount path | Notes |
|---------|-------------|------------|-------|
| WordPress / Ghost / CMS | Web Service | `/var/data` or `/app/content` | Media uploads, SQLite |
| Self-managed MySQL | Private Service | `/var/lib/mysql` | Use mysqldump for backups, not disk snapshots |
| File upload API | Web Service | `/opt/render/project/src/uploads` | Single-instance constraint |
| Elasticsearch | Private Service | `/usr/share/elasticsearch/data` | Stateful search infrastructure |

## References

| Document | Contents |
|----------|----------|
| `references/sizing-and-snapshots.md` | Sizing guidance, snapshot lifecycle, restore procedures, cost patterns |

## Related Skills

- **render-web-services** — Deploy lifecycle, health checks (disk disables zero-downtime)
- **render-private-services** — Internal services with disks (Elasticsearch, MySQL)
- **render-blueprints** — `disk` field reference in `render.yaml`
- **render-postgres** — Managed database alternative (no disk management needed)
