---
name: render-domains
description: >-
  Configures custom domains and TLS certificates on Render—DNS setup, CNAME
  records, apex domains, wildcard domains, and certificate troubleshooting.
  Use when the user needs to add a custom domain, configure DNS, set up
  HTTPS/TLS, troubleshoot certificate issuance, disable the onrender.com
  subdomain, or add a wildcard domain.
  Trigger terms: custom domain, DNS, CNAME, TLS, SSL, HTTPS, certificate,
  apex domain, wildcard domain, onrender.com, domain verification.
license: MIT
compatibility: Render web services and static sites
metadata:
  author: Render
  version: "1.0.0"
  category: networking
---

# Render Custom Domains

Render auto-provisions and renews TLS certificates (via Let's Encrypt and Google Trust Services) for all custom domains. HTTP always redirects to HTTPS. Custom domains work on **web services** and **static sites** only.

## Domain Limits

| Workspace tier | Custom domain limit |
|---------------|---------------------|
| Hobby | 2 custom domains (across all services) |
| Professional+ | Unlimited |

## Setup Steps

### 1. Add domain in Dashboard

1. Open service **Settings > Custom Domains**
2. Click **+ Add Custom Domain**
3. Enter domain (e.g. `app.example.com`)
4. Click **Save**

Adding `www` subdomain auto-adds root domain (and vice versa), redirecting between them.

### 2. Configure DNS

At DNS provider, point record to Render service:

| Domain type | Record type | Name | Value |
|-------------|-------------|------|-------|
| **Subdomain** (`app.example.com`) | CNAME | `app` | `<service>.onrender.com` |
| **Apex** (`example.com`) on Cloudflare | CNAME (flattened) | `@` | `<service>.onrender.com` |
| **Apex** on other providers | A | `@` | Render-provided IP (see Dashboard) |

**Important:** Remove any `AAAA` (IPv6) records for domain. Render uses IPv4; stale `AAAA` records cause unexpected behavior.

Provider-specific guides:
- [Cloudflare](https://render.com/docs/configure-cloudflare-dns)
- [Namecheap](https://render.com/docs/configure-namecheap-dns)
- [Other providers](https://render.com/docs/configure-other-dns)

### 3. Verify domain

Click **Verify** in Dashboard. If it fails, DNS may not have propagated yet: wait a few minutes, retry.

Flush DNS caches to speed up verification:
- [Google Public DNS](https://developers.google.com/speed/public-dns/cache)
- [Cloudflare DNS](https://1.1.1.1/purge-cache/)
- [OpenDNS](https://cachecheck.opendns.com/)

Once verified, Render issues TLS certificate automatically.

## Wildcard Domains

Wildcard domains (`*.example.com`) route all matching subdomains to one service.

Requires **three CNAME records**:

| Name | Value | Purpose |
|------|-------|---------|
| `*` | `<service>.onrender.com` | Routes traffic |
| `_acme-challenge` | `<service-id>.verify.renderdns.com` | Let's Encrypt validation |
| `_cf-custom-hostname` | `<service-id>.hostname.renderdns.com` | Cloudflare DDoS validation |

**Cloudflare users:** If `*.example.com` is added without root domain on Render, disable proxying (gray cloud) for root domain. Avoids routing conflicts.

## CAA Records

If domain has `CAA` records, add entries for Render's certificate authorities:

```
example.com IN CAA 0 issue "letsencrypt.org"
example.com IN CAA 0 issuewild "letsencrypt.org"
example.com IN CAA 0 issue "pki.goog; cansignhttpexchanges=yes"
example.com IN CAA 0 issuewild "pki.goog; cansignhttpexchanges=yes"
```

Without these, TLS certificate issuance fails silently.

## Disabling the `onrender.com` Subdomain

Requires at least one custom domain:

1. Settings > Custom Domains > **Render Subdomain** > toggle to **Disabled**
2. All requests to `onrender.com` URL get 404
3. Re-enable any time

## Blueprint Configuration

Set custom domains in `domains` field:

```yaml
services:
  - type: web
    name: api
    runtime: node
    plan: starter
    domains:
      - app.example.com
      - www.example.com
```

Blueprint `domains` only **declare** domain association; configure DNS at provider manually.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Verifying too quickly | Wait 2-5 minutes for DNS propagation, then flush caches |
| 502 after verification | Routing rules updating — wait a few minutes |

## References

| Document | Contents |
|----------|----------|
| `references/dns-configuration.md` | Provider-specific DNS setup, apex domain options, TTL recommendations |

## Related Skills

- **render-web-services** — Web service configuration, TLS, port binding
- **render-static-sites** — Static site domains, CDN, headers
- **render-blueprints** — `domains` field in `render.yaml`
