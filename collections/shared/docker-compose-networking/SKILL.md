---
name: docker-compose-networking
user-invocable: false
description: Design Docker Compose networking - default and custom bridge networks, internal (no-egress) tiers, aliases, external networks shared across projects, port publishing, host mode, static IPs, IPv6 and connectivity debugging. Use when services must be segmented, discovered or exposed; see docker-compose-basics for general Compose files.
allowed-tools: [Read, Bash(docker compose config --no-interpolate --no-env-resolution:*), Bash(docker compose ps:*), Bash(docker network ls:*), Bash(docker network inspect:*)]
---

# Docker Compose Networking

Network design for single-host Compose projects (Compose v2, `docker compose`). Overlay networks (Swarm mode) out of scope. Omit obsolete top-level `version:` key in every file.

## How Compose networks work

- Compose creates one bridge network per project (`<project>_default`). Every service not declaring `networks:` joins it.
- Services resolve by **service name** (and aliases) via Docker's embedded DNS at `127.0.0.11`. Scaled replicas share name; DNS returns all.
- `ports:` publishes to host. Container-to-container traffic on shared network needs no `ports:`; `expose:` is documentation only.
- Service on several networks is reachable from each. Services sharing no network cannot talk to each other.

## Decision table

| Need | Use |
|---|---|
| Simple app, all services may talk | Default network (declare nothing) |
| Database reachable only from API | Separate `backend` network; DB attached only there |
| Tier with no internet egress | `internal: true` on that network |
| Two Compose projects must talk | One `external: true` network, created once |
| Expose only to local machine | `"127.0.0.1:8080:80"` |
| Stable hostname independent of service name | `aliases:` |
| Fixed IP (legacy allowlists, appliances) | `ipam` subnet + `ipv4_address` (last resort) |
| Max throughput / needs host interfaces (Linux) | `network_mode: host` (no isolation, no `ports:`) |

## Segmented tiers

```yaml
services:
  proxy:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
      - "443:443"
    networks: [edge]

  api:
    build: ./api
    networks: [edge, backend]
    environment:
      DATABASE_URL: postgres://app@db:5432/app
      REDIS_URL: redis://cache:6379

  db:
    image: postgres:17.2-alpine
    networks: [backend]
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets: [db_password]
    volumes: [pgdata:/var/lib/postgresql/data]

  cache:
    image: redis:7.4-alpine
    networks: [backend]

networks:
  edge: {}
  backend:
    internal: true          # no route to the outside world

volumes:
  pgdata:

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

Result: `proxy` reaches `api` only; `api` reaches `db` and `cache`; `db` and `cache` have no published ports, no egress. Service that must call external APIs cannot sit only on `internal` network.

## Aliases

```yaml
services:
  db:
    image: postgres:17.2-alpine
    networks:
      backend:
        aliases: [postgres, primary-db]
```

Aliases are per network: resolve only for services on that network.

## External networks (cross-project)

```yaml
services:
  api:
    networks: [default, shared]

networks:
  shared:
    external: true
    name: company-shared        # created outside Compose
```

```bash
docker network create company-shared
docker compose up -d
```

Compose never creates or deletes external networks; `up` fails if network does not exist.

## Port publishing

```yaml
services:
  web:
    ports:
      - "8080:80"                 # all host interfaces
      - "127.0.0.1:9090:9090"     # loopback only
      - "53:53/udp"               # UDP
      - "8000-8005:8000-8005"     # range
      - "3000"                    # random host port (see: docker compose port web 3000)
  api:
    ports:
      - target: 3000
        published: "3000"
        host_ip: 127.0.0.1
        protocol: tcp
```

On many Linux setups, published ports bypass ufw/firewalld host firewalls, because Docker writes its own iptables/nftables rules. Bind admin and database ports to `127.0.0.1` instead of relying on host firewall.

## Static IPs and custom subnets

```yaml
services:
  appliance:
    networks:
      lan:
        ipv4_address: 172.28.1.10

networks:
  lan:
    ipam:
      config:
        - subnet: 172.28.0.0/16
          gateway: 172.28.0.1
```

Pick subnets that do not overlap host LAN, VPNs or other Docker networks. Prefer service names; static IPs break scaling, invite collisions.

## Host networking (Linux)

```yaml
services:
  node-exporter:
    image: prom/node-exporter:v1.8.2
    network_mode: host
```

`network_mode: host` cannot combine with `ports:` or `networks:`. On Docker Desktop, host networking behaves differently; check documentation for installed version.

## IPv6

```yaml
networks:
  v6:
    enable_ipv6: true
    ipam:
      config:
        - subnet: 2001:db8:1::/64     # use a real ULA/GUA prefix in practice
```

Depending on engine version, Docker daemon may need IPv6 enabled (`daemon.json`).

## DNS overrides

```yaml
services:
  api:
    dns: [10.0.0.2]
    dns_search: [corp.internal]
    extra_hosts:
      - "legacy-api.corp.internal:10.0.5.20"
      - "host.docker.internal:host-gateway"   # reach the host from the container (Linux)
```

## Debugging connectivity

```bash
docker compose config --no-interpolate --no-env-resolution   # effective networks per service
docker network ls
docker network inspect <project>_backend   # attached containers and IPs
docker compose exec api getent hosts db    # DNS resolution from inside a container
docker run --rm -it --network <project>_backend nicolaka/netshoot:v0.16 \
  sh -c 'dig db && nc -zv db 5432'
```

Plain `config` inlines `.env`, shell and `env_file` values, secrets included: never paste it into chat or logs.

Common failures:

| Symptom | Cause |
|---|---|
| `could not resolve host` | Services share no network, or name is alias on different network |
| Connection refused on right host | App listens on `127.0.0.1` inside container; bind `0.0.0.0` |
| Works once, fails after restart | Dependency not ready; use `depends_on` with `condition: service_healthy` |
| No internet from container | Container is only on `internal: true` network |
| Pool overlaps with other network | Custom subnet collides; change `ipam` subnet or daemon's `default-address-pools` |

## Done when

- `docker compose config --no-interpolate --no-env-resolution` shows each service on only networks it needs.
- Data stores have no published ports (or loopback-only ones) and sit on internal or backend-only network.
- Isolation tested: forbidden path (for example `proxy` to `db`) fails to resolve or connect.

## Related skills

- `docker-compose-basics` - core Compose file, healthchecks, env and secrets.
- `docker-compose-production` - production hardening for single-host deployments.
- `architecting-networks` - cloud VPC and subnet design beyond single Docker host.
