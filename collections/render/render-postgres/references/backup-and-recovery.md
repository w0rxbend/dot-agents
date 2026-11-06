# Backup and recovery (Render Managed Postgres)

## Automatic backups

Render takes **automatic daily snapshots**. **Retention** varies by **plan**; see Dashboard and [Render pricing/docs](https://render.com/docs/databases) for current per-tier retention.

## Point-in-time recovery (PITR)

**Paid** plans that include it: **point-in-time recovery** restores to time within **retention window** (plan limits apply). Use Dashboard backup/restore flows for guided recovery.

## Manual exports (`pg_dump`)

Full logical exports you control:

- **`pg_dump`** — flexible; for migrations and archives.
- **Custom format (recommended for larger DBs):**  
  `pg_dump -Fc` makes compressed custom archive for **`pg_restore`**, supporting parallel restore.

DBs **under ~2 GB**: **Render `psql`** (Dashboard/shell access where enabled) often suffices for ad hoc work and small dumps. Check size and timeout limits before relying on it for large datasets.

Always store dumps in **durable storage** (object storage, secure file store), not ephemeral service disks.

## Restore from backup

1. **Dashboard**: Database → **Backups** → choose snapshot or PITR → **Restore**. Follow prompts. May create new instance or overwrite; confirm in UI at restore time.
2. **Manual dump**: **`pg_restore`** for `-Fc` dumps, **`psql`** for plain SQL. Target correct host, credentials, database name.

Periodically test restores on **non-production** database.

## Deletion and retention

**Critical:** Render **does not keep** backups/snapshots of **deleted** Managed Postgres instance. If you need continuity, **export or restore to another instance before deletion**.

## Plan and instance migration

- **Upgrading** instance type / plan supported; expect **brief downtime** (less with **high availability**).
- **Downgrading** from **current-generation** back to **legacy** types **not** supported. Choose instance families deliberately.

## Cross-region

**No built-in cross-region replica** product exists to replace a full migration workflow. Cross-region moves: **`pg_dump` / `pg_restore`**, self-managed logical replication, or other ETL/replication, plus connection string cutover.
