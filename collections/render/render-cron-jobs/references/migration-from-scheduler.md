# Migrating from Heroku Scheduler

## Schedule Mapping

| Heroku Scheduler | Render Cron Expression |
|-----------------|----------------------|
| Every 10 minutes | `*/10 * * * *` |
| Every hour | `0 * * * *` |
| Every day at midnight UTC | `0 0 * * *` |

Render supports arbitrary schedules Heroku Scheduler cannot express (e.g., weekdays only, twice daily, every 15 minutes).

## Command Conversion

Commands mostly unchanged:

| Heroku | Render |
|--------|--------|
| `rake db:cleanup` | startCommand: `bundle exec rake db:cleanup` |
| `python scripts/sync.py` | startCommand: `python scripts/sync.py` |
| `node scripts/report.js` | startCommand: `node scripts/report.js` |

Set `buildCommand` to install dependencies (e.g., `bundle install`, `pip install -r requirements.txt`, `npm ci`).

## Key Differences

| Aspect | Heroku Scheduler | Render Cron Job |
|--------|-----------------|-----------------|
| Schedule options | 3 presets (10min, hourly, daily) | Full cron expression (any schedule) |
| Max run time | No explicit limit (but dyno restarts) | 12 hours hard limit |
| Concurrent runs | May overlap | Single-run guarantee (at most one active) |
| Execution guarantee | Best-effort (may skip) | Reliable (runs at scheduled time) |
| Dedicated service | No (runs on one-off dyno) | Yes (own build/deploy cycle) |
| Cost model | Per-dyno-second | $1/month minimum + per-second billing |
| Persistent disk | N/A | Not available |

## Blueprint Example

Ruby cron job migrated from Heroku Scheduler:

```yaml
services:
  - type: cron
    name: daily-cleanup
    runtime: ruby
    plan: starter
    schedule: "0 0 * * *"
    buildCommand: bundle install
    startCommand: bundle exec rake db:cleanup
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: my-db
          property: connectionString
      - key: RAILS_ENV
        value: production

databases:
  - name: my-db
    plan: starter
```

## Migration Steps

Heroku and Render CLIs send usage data by default; keep the opt-out prefixes below.

1. **List Heroku Scheduler tasks**: `DISABLE_TELEMETRY=true heroku addons:open scheduler -a <app>` or check Scheduler dashboard.
2. **Map each task** to Render cron job service (one service per task, or combine related tasks into one script).
3. **Choose cron expressions** using mapping table above.
4. **Add to Blueprint** with appropriate `buildCommand`, `startCommand`, and `envVars`.
5. **Validate**: `RENDER_CLI_DISABLE_ANALYTICS=1 render blueprints validate`
6. **Deploy** via Blueprint deeplink or Dashboard.
7. **Verify**: check cron run logs in Render Dashboard after first scheduled execution.
