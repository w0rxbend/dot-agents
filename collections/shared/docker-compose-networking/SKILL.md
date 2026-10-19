---
name: docker-compose-networking
user-invocable: false
description: Design Docker Compose networking - default and custom bridge networks, internal (no-egress) tiers, aliases, external networks shared across projects, port publishing, host mode, static IPs, IPv6 and connectivity debugging. Use when services must be segmented, discovered or exposed; see docker-compose-basics for general Compose files.
allowed-tools: [Bash, Read]
---

# Docker Compose Networking

Network design for single-host Compose projects (Compose v2, `docker compose`). Overlay networks belong to Swarm mode and are out of scope here. Omit the obsolete top-level `version:` key in every file.

## How Compose networks work

- Compose creates one bridge network per project (`<project>_default`) and attaches every service that does not declare `networks:`.
- Each service is resolvable by its **service name** (and any aliases) through Docker's embedded DNS at `127.0.0.11`. Scaled replicas share the name; DNS returns all of them.
- `ports:` publishes to the host. Container-to-container traffic on a shared network needs no `ports:`; `expose:` is documentation only.
- A service on several networks is reachable from each of them; services sharing no network cannot talk to each other.

## Decision table

| Need | Use |
|---|---|
| Simple app, all services may talk | Default network (declare nothing) |
| Database reachable only from the API | Separate `backend` network; DB attached only there |
| Tier with no internet egress | `internal: true` on that network |
| Two Compose projects must talk | One `external: true` network, created once |
| Expose only to the local machine | `"127.0.0.1:8080:80"` |
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

Result: `proxy` reaches `api` only; `api` reaches `db` and `cache`; `db` and `cache` have no published ports and no egress. A service that must call external APIs cannot sit only on an `internal` network.

## Aliases

```yaml
services:
  db:
    image: postgres:17.2-alpine
    networks:
      backend:
        aliases: [postgres, primary-db]
```

Aliases are per network: they resolve only for services on that network.

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

Compose never creates or deletes an external network; `up` fails if it does not exist.

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

Published ports bypass host firewalls managed with ufw/firewalld on many Linux setups because Docker writes its own iptables/nftables rules. Bind admin and database ports to `127.0.0.1` rather than relying on the host firewall.

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

Pick subnets that do not overlap the host LAN, VPNs or other Docker networks. Prefer service names; static IPs break scaling and make collisions likely.

## Host networking (Linux)

```yaml
services:
  node-exporter:
    image: prom/node-exporter:v1.8.2
    network_mode: host
```

`network_mode: host` cannot be combined with `ports:` or `networks:`. On Docker Desktop host networking behaves differently; check the installed version's documentation.

## IPv6

```yaml
networks:
  v6:
    enable_ipv6: true
    ipam:
      config:
        - subnet: 2001:db8:1::/64     # use a real ULA/GUA prefix in practice
```

The Docker daemon may need IPv6 enabled (`daemon.json`) depending on the engine version.

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
docker compose config                      # confirm effective networks per service
docker network ls
docker network inspect <project>_backend   # attached containers and IPs
docker compose exec api getent hosts db    # DNS resolution from inside a container
docker run --rm -it --network <project>_backend nicolaka/netshoot \
  sh -c 'dig db && nc -zv db 5432'
```

Common failures:

| Symptom | Cause |
|---|---|
| `could not resolve host` | Services share no network, or the name is an alias on a different network |
| Connection refused on the right host | App listens on `127.0.0.1` inside the container; bind `0.0.0.0` |
| Works once, fails after restart | Dependency not ready; use `depends_on` with `condition: service_healthy` |
| No internet from a container | It is only on an `internal: true` network |
| Pool overlaps with other network | Custom subnet collides; change the `ipam` subnet or the daemon's `default-address-pools` |

## Done when

- `docker compose config` shows each service on only the networks it needs.
- Data stores have no published ports (or loopback-only ones) and sit on an internal or backend-only network.
- Isolation is tested: a forbidden path (for example `proxy` to `db`) fails to resolve or connect.

## Related skills

- `docker-compose-basics` - core Compose file, healthchecks, env and secrets.
- `docker-compose-production` - production hardening for single-host deployments.
- `architecting-networks` - cloud VPC and subnet design beyond a single Docker host.
