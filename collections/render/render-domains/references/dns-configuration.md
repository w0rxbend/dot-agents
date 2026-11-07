# DNS Configuration for Render Custom Domains

## Record Types by Domain Type

### Subdomain (e.g. `app.example.com`, `api.example.com`)

| Provider | Record type | Name | Value |
|----------|-------------|------|-------|
| Any | CNAME | `app` | `<service>.onrender.com` |

### Apex domain (e.g. `example.com`)

Per DNS standards, apex domains cannot have CNAME records. Options:

| Provider | Record type | Name | Value | Notes |
|----------|-------------|------|-------|-------|
| **Cloudflare** | CNAME (flattened) | `@` | `<service>.onrender.com` | Cloudflare auto-flattens at zone apex |
| **Namecheap** | ALIAS | `@` | `<service>.onrender.com` | Namecheap supports ALIAS records |
| **Other** | A | `@` | Render-provided IP | Check Dashboard for IP address |

**Preferred approach:** DNS provider with CNAME flattening or ALIAS records (Cloudflare, Namecheap, DNSimple, NS1). Avoids hardcoding IP that could change.

### www + apex pattern

Adding `www.example.com` auto-adds `example.com` (redirects to `www`). Adding `example.com` auto-adds `www.example.com` (redirects to root).

Set up DNS for both:

```
example.com     → CNAME (flattened) or A → <service>.onrender.com or IP
www.example.com → CNAME                  → <service>.onrender.com
```

## Provider-Specific Guides

### Cloudflare

1. Open domain's DNS settings
2. Add CNAME record:
   - Name: `@` (for apex) or subdomain
   - Target: `<service>.onrender.com`
   - Proxy status: **DNS only** (gray cloud) recommended for initial setup
3. Once verified, optionally enable orange cloud (proxy)

**Cloudflare proxy (orange cloud) considerations:**
- Adds Cloudflare's CDN and WAF in front of Render
- May cache responses (configure cache rules)
- Set SSL mode **Full (strict)**: Render provides valid TLS

### Namecheap

1. Open domain's Advanced DNS
2. Add CNAME record:
   - Host: `@` (for apex, uses ALIAS) or subdomain
   - Value: `<service>.onrender.com`
   - TTL: Automatic

### Other providers

1. Subdomains: CNAME record to `<service>.onrender.com`
2. Apex domains: ALIAS/ANAME record if provider supports it. If not, A record with IP from Render Dashboard.

## TTL Recommendations

| Scenario | Recommended TTL |
|----------|-----------------|
| Initial setup / migration | 300 (5 minutes) — fast iteration |
| After verified and stable | 3600 (1 hour) or higher |
| During DNS provider migration | 60-300 — minimize stale cache risk |

## IPv6 (AAAA Records)

**Remove all AAAA records** for domains pointed to Render. Render is IPv4 only. Stale AAAA records make some clients try IPv6 connections that fail.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Verification fails | DNS not propagated | Wait 2-5 min, flush caches, retry |
| 502 after verification | Routing rules updating | Wait 2-5 min |
| Certificate not issued | CAA records blocking | Add `letsencrypt.org` and `pki.goog` CAA entries |
| ERR_SSL_VERSION_OR_CIPHER_MISMATCH | AAAA record present | Remove all AAAA records |
| Redirect loop | Cloudflare SSL mode not "Full (strict)" | Set SSL to Full (strict) in Cloudflare |
