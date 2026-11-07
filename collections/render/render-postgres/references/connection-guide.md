# Database connection guide (Render Managed Postgres)

## URL formats

- **Internal** (same region and workspace on Render; private network):

  `postgres://user:password@hostname/dbname`

  Typical internal clients need no SSL/TLS.

- **External** (local dev, external tools, CI outside Render):

  `postgres://user:password@hostname/dbname?sslmode=require`

  TLS **1.2+** required; use `sslmode=require` (or stricter) in clients. Current TLS and networking requirements: [Render database documentation](https://render.com/docs/databases).

## Finding URLs in the Dashboard

1. Open Render Dashboard.
2. Select **database** instance.
3. Open **Connect** tab.
4. Copy **Internal** or **External** connection string.

## Blueprint wiring

In `render.yaml`, `fromDatabase` exposes credentials to services:

- **`property: connectionString`** — single URL (if overriding per environment, ensure runtime picks right internal vs external URL), or
- Individual properties: **`host`**, **`port`**, **`user`**, **`password`**, **`database`**

Full examples and immutable field rules: **render-blueprints** skill.

## Connection pooling

Render **does not** provide managed pooler in front of Managed Postgres. Must use:

- **Framework connection pools** (e.g. Rails, Django, Node pg pool), or
- **External poolers** you operate (PgBouncer, pgpool, etc.)

**Connection limits are enforced**; pooling keeps concurrent load under them.

## Multiple logical databases

1. Connect with `psql` or admin tool, using primary database credentials.
2. Run `CREATE DATABASE new_db;`
3. Point apps at **same host and port** and **same user/password**. Change only URL **path** (database name):

   `postgres://user:password@hostname/new_db`

## Common connection issues

| Symptom | Likely cause | Mitigation |
|---------|----------------|------------|
| Higher latency than expected | Render app using **external** URL | Switch service to **internal** URL |
| SSL / certificate errors | External URL without TLS, or wrong `sslmode` | Use `?sslmode=require` and TLS-capable client |
| “Too many connections” / pool exhausted | Hitting **max_connections** | Shrink per-instance pool, add pooling, scale RAM/plan, or add **read replicas** for read-heavy load |
| Wrong database after `CREATE DATABASE` | URL still points at old DB name | Change URL path to new database name |
