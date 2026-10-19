---
name: docker-compose-production
user-invocable: false
description: Run Docker Compose in production on a single host - pinned images, secrets, non-root read-only containers, resource limits, healthchecks, restart policies, log rotation, backups, monitoring and safe updates, with Swarm-only keys called out. Use when a compose.yaml is going to a server; see docker-compose-basics for core syntax and docker-compose-networking for network design.
allowed-tools: [Bash, Read]
---

# Docker Compose Production Deployment

Plain `docker compose` manages one host. It restarts crashed containers and orders startup, but it has no scheduler, no multi-host failover and no rolling updates. When you need those, move to Swarm (`docker stack deploy`) or Kubernetes (see `operating-kubernetes`). Omit the obsolete top-level `version:` key.

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

- `container_name` is incompatible with `replicas`/`--scale`; leave it out of any service that may scale. Compose names containers `<project>-<service>-<n>`.
- Never use `:latest`. Pin tags via variables in a committed `.env` (or digests), so a deploy is reproducible and roll-back is "set the previous version and `up` again".
- Required variables use `${VAR:?message}` so a missing value fails `docker compose config` instead of starting a broken stack.
- Capability lists depend on the image: entrypoints that `chown` or drop privileges need `CHOWN`/`SETUID`/`SETGID`. Start from `cap_drop: [ALL]`, run, and add only what fails.

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
| Non-root | `user: "<uid>:<gid>"` or a `USER` in the image |
| Immutable root FS | `read_only: true` plus `tmpfs:` for writable paths |
| No privilege escalation | `security_opt: ["no-new-privileges:true"]` |
| Minimal capabilities | `cap_drop: [ALL]`, add back individually |
| Process limit | `deploy.resources.limits.pids` |
| No Docker socket | never mount `/var/run/docker.sock` into app containers (equivalent to root on the host) |
| Exposure | publish only the proxy; databases on an `internal` network; admin UIs on `127.0.0.1` |
| Secrets | `secrets:` files, apps read `*_FILE`; nothing secret in `environment:` or the image |

## Deploy and update

```bash
docker compose config --quiet                  # validates and fails on missing required vars
docker compose pull                            # fetch pinned images before touching running containers
docker compose up -d --wait --wait-timeout 120 # recreate changed services; exit non-zero if unhealthy
docker compose ps
```

`up -d` recreates a changed service, so a single-replica service has a short outage. To narrow it: run two or more replicas behind the proxy and roll them by hand (`docker compose up -d --no-deps --scale api=4 api`, verify, then scale back), or adopt a tool or orchestrator built for rolling updates. Roll back by setting the previous version variable and running `up -d --wait` again.

Run Compose under a systemd unit or the Docker daemon's restart policies so the stack returns after a reboot (`restart: unless-stopped` covers containers once the daemon starts).

## Logging

- Set rotation on every service (`json-file` with `max-size`/`max-file`, or the `local` driver). Unrotated logs fill the disk.
- Prefer writing structured JSON to stdout and shipping from the host. For Loki, use Grafana Alloy; if an existing setup still runs Promtail, plan a migration because Grafana has deprecated it in favor of Alloy. Example stack: [references/monitoring-stack.md](references/monitoring-stack.md).

## Backups

- Logical dumps: run `pg_dump`/`pg_dumpall` from a scheduled job (host cron/systemd timer running `docker compose exec -T db pg_dump ...`, or a pinned backup image) to storage off the host.
- Volume snapshots need the service stopped or a filesystem/LVM snapshot to be consistent.
- A backup is only valid once restored: schedule a restore test into a scratch container and record it.

## Monitoring

Expose app metrics, scrape with Prometheus, add node-exporter and cAdvisor for host and container metrics, and alert on healthcheck failures, restarts, disk and memory. A pinned example stack with Alloy-based log shipping is in [references/monitoring-stack.md](references/monitoring-stack.md).

## Done when

- `docker compose config --quiet` passes with no `version:` key, no `:latest`, no `container_name` on scaled services.
- `docker compose up -d --wait` exits 0; every service has a healthcheck, restart policy, log rotation and memory limit.
- Only the proxy publishes public ports; secrets come from `secrets:`; containers run non-root with `no-new-privileges`.
- A backup has been restored successfully at least once, and reboot recovery has been tested.

## Related skills

- `docker-compose-basics` - core file structure, env precedence, profiles, watch.
- `docker-compose-networking` - segmentation and exposure.
- `dockerfile-optimise` - building the images (non-root user, small runtime).
- `implementing-observability` - full metrics/logs/traces backends.
