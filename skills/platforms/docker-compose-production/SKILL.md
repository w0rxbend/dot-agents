---
name: docker-compose-production
user-invocable: false
description: Run Docker Compose in production on a single host - pinned images, secrets, non-root read-only containers, resource limits, healthchecks, restart policies, log rotation, backups, monitoring and safe updates, with Swarm-only keys called out. Use when a compose.yaml is going to a server; see docker-compose-basics for core syntax and docker-compose-networking for network design.
allowed-tools: [Read, Bash(docker compose config --quiet:*), Bash(docker compose ps:*)]
---

# Docker Compose Production Deployment

Plain `docker compose` manages one host. Restarts crashed containers and orders startup. No scheduler, no multi-host failover, no rolling updates. For those, move to Swarm (`docker stack deploy`) or Kubernetes (see `operating-kubernetes`). Omit obsolete top-level `version:` key.

## Production baseline

```yaml
name: shop

x-defaults: &defaults
  restart: unless-stopped
  security_opt: ["no-new-privileges:true"]
  cap_drop: [ALL]
  logging:
    driver: json-file            # or "local", which rotates by default
    options: { max-size: "10m", max-file: "5" }

services:
  proxy:
    <<: *defaults
    image: nginx:${NGINX_VERSION:?pin nginx}-alpine
    cap_add: [NET_BIND_SERVICE, CHOWN, SETGID, SETUID]
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
    networks: [edge]
    depends_on:
      api: { condition: service_healthy }
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/healthz"]
      interval: 30s
      timeout: 5s
      retries: 3

  api:
    <<: *defaults
    image: registry.example.com/shop/api:${API_VERSION:?set API_VERSION}   # immutable tag or @sha256 digest
    user: "10001:10001"
    read_only: true
    tmpfs: [/tmp]
    networks: [edge, backend]
    environment:
      NODE_ENV: production
      DATABASE_HOST: db
      DATABASE_PASSWORD_FILE: /run/secrets/db_password
    secrets: [db_password, jwt_secret]
    depends_on:
      db: { condition: service_healthy }
    healthcheck:
      test: ["CMD", "node", "healthcheck.js"]
      interval: 15s
      timeout: 3s
      retries: 3
      start_period: 30s
    deploy:
      replicas: 2                # honored by docker compose; no container_name on scaled services
      resources:
        limits: { cpus: "1.0", memory: 1G, pids: 256 }
        reservations: { memory: 512M }

  db:
    <<: *defaults
    image: postgres:${POSTGRES_VERSION:?pin postgres}
    cap_add: [CHOWN, DAC_OVERRIDE, FOWNER, SETGID, SETUID]
    networks: [backend]
    environment:
      POSTGRES_DB: shop
      POSTGRES_USER: shop
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets: [db_password]
    volumes: [pgdata:/var/lib/postgresql/data]
    shm_size: 256m
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U shop -d shop"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    deploy:
      resources:
        limits: { memory: 2G }

networks:
  edge: {}
  backend: { internal: true }

volumes:
  pgdata: {}

secrets:
  db_password: { file: ./secrets/db_password.txt }   # mode 0600, owned by the deploy user, not in git
  jwt_secret:  { file: ./secrets/jwt_secret.txt }
```

Notes:

- `container_name` incompatible with `replicas`/`--scale`; omit it on any service that may scale. Compose names containers `<project>-<service>-<n>`.
- Never use `:latest`. Pin tags via variables in committed `.env` (or digests). Deploys stay reproducible.
- Required variables use `${VAR:?message}`: missing value fails `docker compose config` instead of starting broken stack.
- Capability lists depend on image: entrypoints that `chown` or drop privileges need `CHOWN`/`SETUID`/`SETGID`. Start from `cap_drop: [ALL]`, run, add only what fails.

## Which `deploy` keys apply

| Key | `docker compose up` | Swarm `docker stack deploy` |
|---|---|---|
| `deploy.resources.limits` / `reservations` | Yes | Yes |
| `deploy.replicas` | Yes | Yes |
| `deploy.restart_policy` | Partially (prefer top-level `restart:`) | Yes |
| `deploy.update_config`, `rollback_config` | No (ignored) | Yes |
| `deploy.placement`, `mode: global` | No | Yes |
| Templates like `{{.Task.Slot}}` | No | Yes |

Do not rely on Swarm-only keys for zero-downtime updates under plain Compose.

## Hardening checklist

| Control | Setting |
|---|---|
| Non-root | `user: "<uid>:<gid>"` or `USER` in image |
| Immutable root FS | `read_only: true` plus `tmpfs:` for writable paths |
| No privilege escalation | `security_opt: ["no-new-privileges:true"]` |
| Minimal capabilities | `cap_drop: [ALL]`, add back individually |
| Process limit | `deploy.resources.limits.pids` |
| No Docker socket | never mount `/var/run/docker.sock` into app containers (equals root on host) |
| Exposure | publish only proxy; databases on `internal` network; admin UIs on `127.0.0.1` |
| Secrets | `secrets:` files, apps read `*_FILE`; nothing secret in `environment:` or image |

## Deploy and update

On live host, show planned `pull`/`up`/`scale`/`stop`/`down` commands and get user confirmation before running. `up -d` recreates changed containers; `down -v` deletes volumes.

```bash
docker compose config --quiet                  # validates and fails on missing required vars
docker compose pull                            # fetch pinned images before touching running containers
docker compose up -d --wait --wait-timeout 120 # recreate changed services; exit non-zero if unhealthy
docker compose ps
```

`up -d` recreates changed services, so single-replica service has short outage. To narrow it: run two or more replicas behind proxy, roll them by hand (`docker compose up -d --no-deps --scale api=4 api`, verify, scale back). Or adopt tool or orchestrator built for rolling updates. Roll back: set previous version variable, run `up -d --wait` again.

Run Compose under systemd unit or Docker daemon restart policies so stack returns after reboot. `restart: unless-stopped` covers containers once daemon starts.

## Logging

- Set rotation on every service (`json-file` with `max-size`/`max-file`, or `local` driver). Unrotated logs fill disk.
- Prefer structured JSON to stdout, shipped from host. For Loki, use Grafana Alloy. If existing setup still runs Promtail, plan migration: Grafana deprecated it in favor of Alloy.

## Backups

- Logical dumps: run `pg_dump`/`pg_dumpall` from scheduled job (host cron/systemd timer running `docker compose exec -T db pg_dump ...`, or pinned backup image) to off-host storage.
- Consistent volume snapshots need service stopped or filesystem/LVM snapshot.
- Backup only valid once restored: schedule restore test into scratch container, record it.

## Monitoring

Expose app metrics, scrape with Prometheus. Add node-exporter and cAdvisor for host and container metrics. Alert on healthcheck failures, restarts, disk and memory. Pinned example stack with Alloy-based log shipping: [references/monitoring-stack.md](references/monitoring-stack.md).

## Done when

- `docker compose config --quiet` passes with no `version:` key, no `:latest`, no `container_name` on scaled services.
- `docker compose up -d --wait` exits 0; every service has healthcheck, restart policy, log rotation and memory limit.
- Only proxy publishes public ports; secrets come from `secrets:`; containers run non-root with `no-new-privileges`.
- Backup restored successfully at least once; reboot recovery tested.

## Related skills

- `docker-compose-basics` - core file structure, env precedence, profiles, watch.
- `docker-compose-networking` - segmentation and exposure.
- `dockerfile-optimise` - building images (non-root user, small runtime).
- `implementing-observability` - full metrics/logs/traces backends.
