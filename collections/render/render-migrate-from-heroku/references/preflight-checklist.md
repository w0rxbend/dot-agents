# Pre-Flight Checklist

Before creating any resources, validate migration plan and present it to user. Check each item:

## Validation Checks

1. **Runtime supported?** If buildpack maps to `docker`, warn user a Dockerfile is needed
2. **Worker dynos?** Flag them. Blueprint can define them (`type: worker`, minimum plan `starter`); MCP tools cannot create them directly
3. **Release phase?** If Procfile has `release:`, suggest appending to build command
4. **Static site?** Check for static buildpack, `static.json`, or SPA framework deps — use `create_static_site`, not `create_web_service`. Detection rules: [buildpack mapping](buildpack-mapping.md).
5. **Third-party add-ons?** List add-ons without direct Render equivalents (e.g., Papertrail, SendGrid) — user must find alternatives and update env vars
6. **Multiple process types?** If Procfile has >1 entry, each becomes a separate Render service (except `release:`)
7. **Repo URL available?** Verify a Git remote exists:

   ```bash
   git remote -v
   ```

   If no remote exists, stop. Guide user to create a GitHub/GitLab/Bitbucket repo, add it as `origin`, and push before continuing.

   Strip any embedded credentials (`user:token@`) from URL. If URL is SSH format, convert to HTTPS for service creation and deeplinks. **Conversion pattern:** Replace `git@<host>:` with `https://<host>/` and remove `.git` suffix.

8. **Database size?** If Postgres is Premium/large tier, recommend contacting Render support for assisted migration

## Migration Plan Table

Look up each Heroku dyno size and add-on plan in [service mapping](service-mapping.md) for Render plan. Present full plan as table:

```
MIGRATION PLAN — [app-name]
─────────────────────────────────
CREATE (include only items that apply):
  ✅ Web service ([runtime], [mapped-plan]) — startCommand: [cmd]
     Heroku: [dyno-size] ($X/mo) → Render: [mapped-plan] ($Y/mo)
  ✅ Background worker ([runtime], [mapped-plan]) — startCommand: [cmd]
     Heroku: [dyno-size] ($X/mo) → Render: [mapped-plan] ($Y/mo)
  ✅ Cron job ([mapped-plan]) — schedule: [cron expr] — command: [cmd]
  ✅ Postgres ([mapped-plan], diskSizeGB: [size])
     Heroku: [plan-slug] ($X/mo) → Render: [mapped-plan] ($Y/mo + storage)
  ✅ Key Value ([mapped-plan])
     Heroku: [plan-slug] ($X/mo) → Render: [mapped-plan] ($Y/mo)

ESTIMATED MONTHLY COST:
  Heroku: $[total]/mo → Render: $[total]/mo
  (Render storage billed separately at $0.30/GB/mo in 5 GB increments; cannot be scaled down once provisioned)

METHOD: [Blueprint | MCP Direct Creation]

MANUAL STEPS REQUIRED:
  ⚠️ Custom domain: [domain] — configure after deploy
  ⚠️ Replace add-on: [name] → find alternative

ENV VARS: [N] to migrate, [M] filtered out
DATABASE: [size] — pg_dump/render psql required
─────────────────────────────────
Proceed? (y/n)
```

Cost from pricing columns in [service mapping](service-mapping.md): sum Render $/mo per service, database, Key Value store. Postgres storage is billed separately; say so.

Wait for user confirmation before creating any resources.
