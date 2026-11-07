---
name: docker-compose-basics
user-invocable: false
description: Define and run multi-container apps with Docker Compose v2 - services, healthcheck-gated startup, profiles, include/extends, override layering, env precedence, secrets, volumes, develop/watch and config validation. Use for any compose.yaml task; see docker-compose-networking for network design and docker-compose-production for production hardening.
allowed-tools: []
---

# Docker Compose Basics

Core Compose Specification usage with Docker Compose v2 plugin (`docker compose`, not legacy `docker-compose` binary). Top-level `version:` key is obsolete: Compose ignores it and prints a warning. Omit it.

## Baseline file

Name file `compose.yaml` (Compose also reads `docker-compose.yml`).

```yaml
name: myapp

services:
  web:
    build: ./web
    ports:
      - "127.0.0.1:8080:8080"     # bind to loopback unless it must be reachable from the LAN
    environment:
      API_URL: http://api:3000    # service name is the DNS name on the default network
    depends_on:
      api:
        condition: service_healthy

  api:
    build: ./api
    env_file: .env
    environment:
      DATABASE_URL: postgres://app@db:5432/app
    secrets:
      - db_password
    depends_on:
      db:
        condition: service_healthy
        restart: true             # restart api when db is restarted by Compose
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3000/health"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 20s

  db:
    image: postgres:17.2          # pin a version; never :latest
    environment:
      POSTGRES_USER: app
      POSTGRES_DB: app
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  pgdata:

secrets:
  db_password:
    file: ./secrets/db_password.txt   # keep out of git
```

## Startup ordering

| `depends_on` form | Waits for |
|---|---|
| list (`- db`) | container **started** only - app may still be booting |
| `condition: service_healthy` | dependency's `healthcheck` passing |
| `condition: service_completed_successfully` | one-shot job (migrations, seeding) exiting 0 |

`service_healthy` condition requires a `healthcheck` on the dependency (in image or compose file). Health command must exist in the image. Many slim images lack `curl`; use `wget`, app's own binary, or a tool like `pg_isready`.

## Volumes vs bind mounts

| Use | Syntax | When |
|---|---|---|
| Named volume | `pgdata:/var/lib/postgresql/data` | Persistent service data managed by Docker |
| Bind mount | `./src:/app/src` | Development source code, config files you edit |
| Read-only bind | `./nginx.conf:/etc/nginx/nginx.conf:ro` | Config the container must not change |
| tmpfs | `tmpfs: [/tmp]` | Scratch data that must not persist |

`docker compose down` keeps named volumes; `down -v` deletes them (data loss; confirm with user first).

## Environment variables

Two separate mechanisms:

1. **Interpolation** of `${VAR}` inside compose file. Sources, highest priority first: shell environment, then `--env-file` files (or project's `.env` when none given). Use `${VAR:-default}` for defaults, `${VAR:?message}` to fail fast when a variable is required.
2. **Container environment**. For same variable: `docker compose run -e` beats `environment:`, which beats `env_file:`, which beats image's `ENV`.

`.env` only feeds interpolation. Not injected into containers unless a service lists it in `env_file:`. Put real secrets in `secrets:` (mounted at `/run/secrets/<name>`), not in `environment:`.

## Profiles

```yaml
services:
  adminer:
    image: adminer:4.8.1
    profiles: [debug]
```

Services with `profiles` start only when profile is enabled: `docker compose --profile debug up` or `COMPOSE_PROFILES=debug`. Services without `profiles` always start.

## Composing files

| Mechanism | Use when |
|---|---|
| `compose.override.yaml` | Local dev overrides; merged automatically after `compose.yaml` |
| `-f a.yaml -f b.yaml` | Explicit layering (later files override earlier; lists like `ports` merged) |
| `include:` | Pull in another team's/component's compose file as own unit with own relative paths |
| `extends:` | Reuse one service definition as base for another |

```yaml
include:
  - ./observability/compose.yaml

services:
  worker:
    extends:
      file: common.yaml
      service: base-app
    command: ["node", "worker.js"]
```

Use `!reset` / `!override` YAML tags in override file to remove or replace a value instead of merging.

## Development with watch

```yaml
services:
  web:
    build: ./web
    develop:
      watch:
        - action: sync           # copy changed files into the running container
          path: ./web/src
          target: /app/src
        - action: rebuild        # rebuild the image when dependencies change
          path: ./web/package.json
```

Run with `docker compose watch` (or `docker compose up --watch`).

## Commands

```bash
docker compose config                 # render the merged, interpolated model; validates the file
docker compose config --quiet         # validation only (CI)
docker compose up -d --wait           # start and block until services are running/healthy
docker compose ps
docker compose logs -f api
docker compose exec api sh
docker compose run --rm api npm test  # one-off container
docker compose build --pull
docker compose pull
docker compose down                   # keeps named volumes; add -v to delete them
```

`config` output inlines `.env`, shell and `env_file` values, secrets included: never paste it into chat or logs; inspect structure with `--no-interpolate --no-env-resolution`.

`--scale api=3` only works when service has no `container_name` and no fixed host port.

## Done when

- `docker compose config --quiet` passes; file has no `version:` key.
- Every dependency used with `service_healthy` has working healthcheck; `docker compose up -d --wait` exits 0.
- No secrets in compose file or committed `.env`. Images pinned.
- Ports needing no LAN access bound to `127.0.0.1`.

## Related skills

- `docker-compose-networking` - custom networks, isolation, service discovery.
- `docker-compose-production` - resource limits, logging, restart policies and hardening for single-host production.
- `dockerfile-optimise` - images the services build.
