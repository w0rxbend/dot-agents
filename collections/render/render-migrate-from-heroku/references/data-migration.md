# Data Migration Guide

## 5a. Pre-migration checks

Verify readiness before generating any migration commands:

1. **Render Postgres is provisioned** — call `list_postgres_instances()` to find Postgres ID and confirm database exists. Note ID for `render psql` in Step 5c.
2. **Render Key Value is provisioned** (if Redis data needs migrating) — call `list_key_value()` to find Key Value ID and confirm instance exists. Note ID for Dashboard deeplink in Step 5d.
3. **Check source database size** — Heroku MCP `pg_info` (look for `Data Size`), or ask user to paste output of `heroku pg:info -a <app>`.
4. **Compare disk sizes** — warn if Heroku `Data Size` exceeds Render `diskSizeGB`. If so, user must raise `diskSizeGB` before restoring.
5. **Render CLI** — confirm installed and authenticated (required for `render psql` restore):

   ```bash
   render --version
   render whoami
   ```

   If not installed, offer install:
   - macOS: `brew install render`
   - Linux/macOS without Homebrew: download pinned release zip and its `SHA256SUMS` from [CLI releases page](https://github.com/render-oss/cli/releases/), verify checksum, put `cli_v<version>` binary on `PATH` as `render` (see render-cli skill). Ask user before installing anything. Do not pipe install script from `curl` into `sh`.

   If not authenticated, run `render login` to authorize via Dashboard.

6. **`pg_dump` and `pg_restore`** — check user has PostgreSQL client tools locally:

   ```bash
   pg_dump --version
   pg_restore --version
   ```

   Both needed: `pg_dump` for all approaches, `pg_restore` for traditional approach (databases over 2 GB). If missing, suggest installing PostgreSQL client tools (e.g., `brew install libpq` on macOS, `apt install postgresql-client` on Linux).

7. **Redis tools** (if migrating Redis data) — check for `redis-cli`:

   ```bash
   redis-cli --version
   ```

## 5b. Gather connection strings

**Render Postgres** connection string is **not needed**: `render psql` connects directly with Postgres ID from Step 5a. Need only Heroku source URLs and Render Key Value URL (if applicable).

Connection strings are secrets: user loads them into env vars in own shell (same shell as migration commands). Never fetch them into chat, ask user to paste them, echo them, or put literal values in commands.

**Heroku Postgres** (user runs):

```bash
export HEROKU_DB_URL="$(heroku config:get DATABASE_URL -a <app>)"
```

**Render Key Value** (if migrating Redis data):

Render MCP does not return Key Value connection strings. Build Dashboard deeplink from Key Value ID (Step 5a); user copies external connection URL into own shell:

```
Dashboard link: https://dashboard.render.com/d/<key-value-id>
→ ask user to open link, go to the Connections tab, copy the External Access URL
→ user runs `read -rs RENDER_REDIS_URL && export RENDER_REDIS_URL` and pastes it there (not in chat)
```

**Heroku Redis** (if migrating Redis data; user runs):

```bash
export HEROKU_REDIS_URL="$(heroku config:get REDIS_URL -a <app>)"
```

**Important:** Generated commands reference `"$HEROKU_DB_URL"`, `"$RENDER_DB_URL"`, `"$HEROKU_REDIS_URL"`, `"$RENDER_REDIS_URL"`. Fill in only non-secret IDs (`<app>`, `<postgres-id>`).

## 5c. Postgres migration

Generate commands with env vars (Step 5b) and Render Postgres ID (Step 5a) filled in. Present full sequence to user.

**1. Put Heroku in maintenance mode** to stop writes during migration:

Takes production offline: confirm with user immediately before. Then use `maintenance_on` via Heroku MCP if available, or tell user to run:

```bash
heroku maintenance:on -a <app>
```

**2. Dump and restore** — pick approach by database size (`Data Size` from `pg_info`, Step 5a):

Before any restore, confirm with user that target is the new Render DB (`--clean` drops existing objects there). Run dumps from a private dir outside repo (`umask 077`); never commit dump files; user deletes them after validation passes.

**Render CLI approach** (databases under 2 GB — simplest, no Render connection string needed):

Plain-text SQL dump plus [Render CLI's `render psql`](https://render.com/docs/cli) in non-interactive mode, connecting directly with Postgres ID.

```bash
# Dump from Heroku (plain-text SQL format)
pg_dump --clean --no-acl --no-owner -d "$HEROKU_DB_URL" > heroku_dump.sql
# Restore to Render via CLI
render psql <postgres-id> --confirm -o text -- -f heroku_dump.sql
```

Replace `<postgres-id>` with Render Postgres ID from Step 5a (e.g., `dpg-abc123`).

**Traditional approach** (databases 2-50 GB — faster, compressed, supports parallel restore):

Custom-format dump with `pg_restore`. Needs Render **external connection string**; ask user to copy it from Render Dashboard:

```
Dashboard link: https://dashboard.render.com/d/<postgres-id>
→ ask user to open link, go to the Connection tab, copy the External Connection String
→ user runs `read -rs RENDER_DB_URL && export RENDER_DB_URL` and pastes it there (not in chat)
```

Then generate:

```bash
# Dump from Heroku (compressed custom format)
pg_dump -Fc --no-acl --no-owner -d "$HEROKU_DB_URL" > heroku_dump.dump
# Restore to Render (parallel with 4 jobs)
pg_restore --clean --no-acl --no-owner -j 4 -d "$RENDER_DB_URL" heroku_dump.dump
```

Pipe approach (no local disk usage):

```bash
pg_dump -Fc --no-acl --no-owner -d "$HEROKU_DB_URL" | pg_restore --clean --no-acl --no-owner -d "$RENDER_DB_URL"
```

Note: pipe approach cannot use `-j` for parallel restore.

**Very large databases** (over 50 GB): recommend user [contact Render support](https://render.com/contact) for assisted migration. Do not generate commands; process needs coordination.

Remind user to schedule a maintenance window. App is down on Heroku from maintenance mode until DNS cutover to Render.

## 5d. Key Value / Redis migration

Most Heroku Redis instances are ephemeral caches; no data migration needed. Ask user before proceeding:

- **Ephemeral cache** (most common) — skip migration. App repopulates cache after Render deploy.
- **Persistent data** — if user confirms Redis holds persistent data (e.g., session store, queues, application state), generate migration commands with env vars from Step 5b:

  ```bash
  # Dump from Heroku Redis (private dir outside repo, umask 077, as in 5c; never commit; delete after validation)
  redis-cli -u "$HEROKU_REDIS_URL" --rdb heroku_dump.rdb
  # Restore to Render Key Value (requires redis-cli 5.0+)
  redis-cli -u "$RENDER_REDIS_URL" --pipe < heroku_dump.rdb
  ```

  Blueprint sets Key Value `ipAllowList: []` (internal only), so user temporarily adds own IP (`<ip>/32`) in Dashboard for restore and removes it after.

  Note: some Heroku Redis plans may not support RDB dump/restore. If it fails, use per-key `DUMP`/`RESTORE` or have application re-seed data.

## 5e. Data validation

After user confirms restore completed, validate before Step 6:

**1. Check schema exists on Render:**

```
query_render_postgres(
  postgresId: "<postgres-id>",
  sql: "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
)
```

**2. Compare row counts on key tables:**

```
query_render_postgres(
  postgresId: "<postgres-id>",
  sql: "SELECT 'users' AS tbl, count(*) FROM users UNION ALL SELECT 'orders', count(*) FROM orders"
)
```

Adjust table names to app. Pick 2-3 key tables holding core data.

**3. Compare against Heroku source** (if Heroku MCP is available):

```
pg_psql(app: "<app>", command: "SELECT 'users' AS tbl, count(*) FROM users UNION ALL SELECT 'orders', count(*) FROM orders")
```

**4. Present a side-by-side summary:**

```
DATA VALIDATION
─────────────────────────────
Table     | Heroku  | Render
users     | 12,450  | 12,450  ✅
orders    | 84,321  | 84,321  ✅
products  | 1,203   | 1,203   ✅
─────────────────────────────
```

If counts don't match, warn user and suggest re-running restore. Do not proceed to Step 6 until validation passes.
