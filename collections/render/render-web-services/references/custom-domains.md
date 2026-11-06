# Custom domains on Render Web Services

## Adding a domain (Dashboard)

1. Open **Render Dashboard** → select **Web Service**.
2. Go to **Settings** → **Custom Domains**.
3. Add hostname (e.g. `www.example.com` or `api.example.com`).
4. Follow shown **DNS** and **verification** instructions.

## DNS: CNAME to onrender.com

- **Subdomain**: **CNAME** record to service’s Render hostname **`[service-name].onrender.com`** (copy exact target from Dashboard).
- **Propagation**: minutes to hours, depending on TTL and provider caching.

## Apex (root) domains

Plain **CNAME at zone apex** (`example.com`) is **not supported** by DNS RFCs at many providers.

- Use provider **ALIAS**, **ANAME**, or **CNAME flattening** (synthesizes A/AAAA records from CNAME-like target), **or** use **redirect** subdomain (e.g. `www`) as canonical hostname.
- Follow Render’s Dashboard guidance for exact record type provider needs.

## Wildcard domains

- **Wildcard** hostnames like **`*.example.com`** allowed when plan and workflow support it.
- DNS must include matching **wildcard** record per provider rules. TLS certificates provisioned after **verification**.

## TLS certificates

- Render **auto-provisions** certificates for verified custom domains.
- Certificates **renew automatically**. Avoid serving own cert on public listener for standard Web Services (TLS at edge).

## Verification

- Render verifies domain **control** via **DNS** (and/or UI instructions).
- Unverified domain may not serve traffic or may show certificate warnings.

## Multiple domains

- **Several hostnames** can target **same** Web Service. Add each in **Custom Domains**, or list in Blueprint **`domains`** field as **list of strings** (hostnames).

Example Blueprint fragment:

```yaml
domains:
  - www.example.com
  - api.example.com
```

## Troubleshooting

| Issue | What to check |
|--------|----------------|
| Domain does not resolve | CNAME/ALIAS target typos; **TTL**; old records still cached |
| Certificate pending or invalid | Verification not complete; **conflicting** A/AAAA/CNAME records |
| Wrong site | CNAME points to **different** `[service-name].onrender.com` |
| Apex not working | Provider lacks **flattening**; use **www** or ALIAS/ANAME |

**Free tier:** Custom domains **not** available on free Web Service instance types. Use paid instance type for custom hostnames.
