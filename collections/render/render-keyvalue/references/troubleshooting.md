# Key Value Troubleshooting

## AUTH failed: Client IP address is not in the allowlist

**Cause:** Connecting via external URL from IP not in instance's access control list.

**Fix:**
1. In Dashboard, go to Key Value instance > Networking
2. Add your IP address (CIDR notation, e.g. `203.0.113.5/32`)
3. Retry connection

Applies only to external connections. IP allowlist does not affect internal connections from Render services in same region.

## Connection refused (internal URL)

**Cause:** Service and Key Value instance in different regions, or Key Value instance not yet available.

**Fix:**
- Verify both resources in **same region** (e.g. both in `oregon`)
- Check instance status in Dashboard; should show "Available"
- Use **internal** URL (starts with `redis://`), not external URL

## WRONGPASS / invalid username-password pair

**Cause:** Internal authentication enabled, but client uses unauthenticated URL.

**Fix:** Update connection URL to include credentials:

```
redis://default:PASSWORD@red-xxx:6379
```

Get authenticated URL from Dashboard > Connect menu.

## OOM command not allowed (maxmemory reached)

**Cause:** Instance memory full and `maxmemoryPolicy` is `noeviction`.

**Fix options:**
- **Upgrade** to larger instance type (Dashboard > Key Value Instance > Update)
- **Add TTLs** to keys that don't need to persist forever
- **Switch policy** to `allkeys-lru` if data loss acceptable (cache use case)
- **Review data patterns**: check for more data stored than intended

## Data lost after upgrade from Free

**Expected behavior.** Free instances have no disk persistence. Upgrading from Free to paid plan wipes all data, because instance is recreated with disk backing.

**Prevention:** Export critical data before upgrading, or use paid instance from start for production workloads.

## Data lost after restart (Free tier)

**Expected behavior.** Free Key Value instances do not persist data to disk. Data is in-memory only; lost on restart, redeploy, or platform maintenance.

**Fix:** Upgrade to paid plan for `appendfsync everysec` persistence.

## Legacy Redis 6 instances

Instances created before February 2025 run Redis 6. They still operate but do not receive version updates. New instances run Valkey 8.

No action required unless you need Valkey 8-specific features. Migration to new instance requires creating new Key Value and updating connection strings.

## Cannot downgrade instance type

Instance type changes are **upgrade-only**. Cannot move to smaller instance. If you need less capacity, create new smaller instance and migrate data.
