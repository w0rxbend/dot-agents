# Private network communication patterns

Limits (region, workspace, free tier, ports): main `SKILL.md`.

## Gateway pattern

**Flow:** Public **Web Service** → one or more **Private Services** (or other internal targets).

- Expose only gateway on public internet.
- Gateway calls backends by **internal hostname and port**: `http://[internal-hostname]:[port]/...`
- Keep sensitive APIs and admin surfaces on Private Services. Restrict security groups / auth at gateway and each service.

## Worker-to-DB

**Flow:** **Background Worker** → **Managed Postgres** (or **Key Value**) via **internal URL**.

- Workers **cannot** receive inbound private connections (no internal hostname); always clients.
- Put datastore **internal URL** from Dashboard (**Connect > Internal**) in env var worker reads at runtime.
- Size connection pooling for worker concurrency.

## Service mesh (lightweight)

**Flow:** Multiple **Private Services** (and optionally internal ports on Web Services) call each other by **internal hostnames**.

- Standardize on one scheme (`http` vs `https`) per hop; some clients require explicit `http://` or `https://` prefix.
- For cross-service **health checks**, use private hostname:port from service allowed to initiate private egress (e.g., another Private Service or Web Service). Not from Static Site, nor from Worker if target must be another compute service’s inbound port.

## URL construction

Use consistent template:

```text
http://[internal-hostname]:[port]/path
```

- Replace `[internal-hostname]` and `[port]` with values from **Connect > Internal**.
- Keep trailing slashes if upstream is sensitive to them.

## Blueprint wiring

In `render.yaml`, set **`fromService`** on consumer to link services for private access:

- Use properties such as **`host`** or **`hostport`** when template needs private service’s internal hostname or `host:port`. Exact key names follow Blueprint schema version; check current Render Blueprint docs.

Producer service type must support private networking; region/workspace must match consumer.

## Discovery hostname for custom load balancing

When service scales to multiple instances:

- **`[hostname]-discovery`** resolves to **all** instance IPs.
- Pair with **`RENDER_DISCOVERY_SERVICE`** where provided for custom selection, retries, or per-instance metrics.
- Use when application code must implement round-robin or sticky behavior instead of relying on single internal A-record.

## Cross-service health checking via private network

- Prefer health endpoints on **private** listener port when checks come from another Render service in same region/workspace.
- Do not assume public health URLs prove private reachability. Firewalls, bindings, and `PORT` vs extra ports differ for multi-port web services.
