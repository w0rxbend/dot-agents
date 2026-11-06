---
name: render-networking
description: >-
  Connects Render services over the private network—internal DNS, service
  discovery, and cross-service communication. Use when the user needs to wire
  services together, resolve internal hostnames, troubleshoot connectivity
  between services, configure environment isolation, or understand which
  services can reach each other.
license: MIT
compatibility: Render services in the same region and workspace
metadata:
  author: Render
  version: "1.0.0"
  category: networking
---

# Render private networking

## When to Use This Skill

- Designing or debugging **service-to-service** traffic on Render
- **Internal hostnames**, **internal URLs**, **Connect > Internal** in Dashboard
- **Service discovery** across multiple instances (custom load balancing, mesh-style setups)
- **Port limits**, reserved ports, **multi-port** web services (public vs private)
- **Free-tier** web services; **who can send vs receive** private traffic
- **Environment isolation** (Professional+), **AWS PrivateLink** for private egress/ingress patterns

## Private Network Basics

Private connectivity works only when **all** hold:

- Services in **same region**
- Services in **same workspace**

If either differs, private DNS and internal routing will not connect them.

### Who can communicate

| Resource | Private inbound | Private outbound | Internal hostname |
|----------|-----------------|------------------|-------------------|
| **Web Service** | Yes (paid tiers; see Free tier below) | Yes | Yes |
| **Private Service** | Yes | Yes | Yes |
| **Background Worker** | No | Yes | No |
| **Cron Job** | No | Yes | No |
| **Workflow Run** | No | Yes | No |
| **Static Site** | — | — | **Not on private network** |
| **Managed Postgres** | Via internal URL (from allowed clients) | N/A (datastore) | Via internal URL |
| **Key Value** | Via internal URL (from allowed clients) | N/A (datastore) | Via internal URL |

**Free-tier Web Services:** Can **send** private traffic, **cannot receive** it inbound. Upgrade or change topology if one must accept private connections.

## Internal Addresses

- Render Dashboard → **Connect** → **Internal** tab: canonical internal hostname, URL, connection details.
- Clients often need **explicit scheme**, e.g. `http://service-name:port`, or `https://...` when TLS applies. Do not assume bare hostname works for every HTTP client.
- **URL shape:** `http://[internal-hostname]:[port]/path` (adjust scheme/port per service).

## Service Discovery

Services with **multiple instances** get **discovery DNS** name resolving to **all instance IPs**. Pattern: **`[hostname]-discovery`** (Dashboard docs show exact hostname).

- **`RENDER_DISCOVERY_SERVICE`** is set where discovery applies. Combine with discovery hostname pattern in scripts and app code needing instance lists.
- **Use case:** Custom load balancing, health aggregation, or logic that must fan out or pick instances explicitly instead of one internal hostname.

## Port Rules

- **Maximum 75 open ports** per service.
- **Reserved ports** (do not bind app to these for normal use): **18012**, **18013**, **19099**. Port **10000** is not reserved: it is usual default `PORT` value, which web service should bind.
- **Multi-port Web Services:** Only **one** port gets **public** HTTP traffic; it must match **`PORT`** environment variable. **Additional** ports: **private network** access only.

On connection failure, verify target listens on expected port and port is not reserved or blocked by misconfiguration.

## Environment Isolation

**Professional and higher** workspaces can set **per-environment** rules so private traffic does **not** cross certain environment boundaries. If private calls work in one environment but not another, check workspace **environment isolation** before suspecting DNS or app bugs.

## AWS PrivateLink

**Professional+** workspaces can use **AWS PrivateLink** to extend private connectivity to or from external AWS VPCs and approved endpoints. Separate from default service-to-service private DNS. Use when architecture needs **private** access to Render, or from Render to specific AWS resources, without public internet.

## References

| Document | Purpose |
|----------|---------|
| `references/communication-patterns.md` | Gateway, worker→DB, mesh, URL construction, Blueprint `fromService`, discovery load balancing, private health checks |
| `references/troubleshooting.md` | DNS, ports, region/workspace, free tier, protocol, resolver, environment isolation |

## Related Skills

- **render-web-services** — Public web services, `PORT`, HTTP behavior
- **render-private-services** — Private Service–specific setup and scaling
- **render-blueprints** — `render.yaml`, `fromService`, multi-service wiring
