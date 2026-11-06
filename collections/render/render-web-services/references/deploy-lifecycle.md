# Web Service deploy lifecycle on Render

## Build phase

- Render **clones** repo at configured **branch/commit**.
- Runs **`buildCommand`** (or environment default).
- Output: **build artifact** or image for **runtime** container.

**Persistent disk** (if any) **not** available during build. Do not assume disk mount paths exist at build time.

## Pre-deploy command

- Optional **`preDeployCommand`** runs in **new** image **before** production traffic moves.
- Typical use: **database migrations**, one-off schema updates, validation that must pass before serving traffic.
- If command **exits non-zero** (fails), **deploy is canceled**; previous live revision keeps serving (subject to current product behavior).

## Zero-downtime deploy (when enabled)

For services **without** attached persistent disks (subject to plan/type rules):

1. **New instances** start from new build.
2. **Health checks** must pass for new revision.
3. **Traffic switches** to healthy new instances.
4. **Old instances drain** in-flight requests, then shut down.

With **persistent disk**, zero-downtime deploys **disabled**; rollout differs (single instance, swap behavior per platform docs).

## Graceful shutdown and `maxShutdownDelaySeconds`

- **`maxShutdownDelaySeconds`**: how long **old instances** may keep handling requests during drain before shutdown (range **1–300**, **default 30**).
- Raise for **long-lived** requests (large uploads, slow streaming): fewer hard cuts for clients. Lower for faster replacement (understand tradeoffs).

## Rollback

- **Dashboard**: **revert** to **previous successful deploy** when release misbehaves.
- For bad config or failed migrations, roll back only after checking **data** compatibility (migrations may be one-way).

## Auto-deploy triggers

Blueprint / service settings use **`autoDeployTrigger`** (or Dashboard equivalents):

| Value | Behavior |
|--------|----------|
| **`commit`** | Deploy on every push to **connected branch** |
| **`checksPass`** | Deploy only when required **Git provider checks** pass |
| **`off`** | **Manual** deploys only |

Pair with branch protection and CI so **`checksPass`** matches org quality gates.

## Build filters

- **Path filters** run builds only when certain paths change.
- Exact YAML keys depend on Blueprint version; check current Render Blueprint docs when generating `render.yaml`.

## Manual deploy

- Trigger from **Dashboard** (Manual Deploy).
- CLI: **`render deploys create`** (needs correct service context and authentication); useful in scripts and non-Git triggers. Confirm target service with user before deploying.
- Render CLI sends usage analytics by default; prefix with `RENDER_CLI_DISABLE_ANALYTICS=1` (or export it) wherever `render` runs, incl. commands given to user.

## Deploy hooks

- **Webhook URLs** can **trigger deploys** when called (e.g. external CI or release systems).
- Secure hooks (secrets, allowlists); avoid exposing them in public repos.

## PR previews

- Blueprint **`previews.generation`** and related settings control them. When enabled and repo-connected, previews spin up **ephemeral** service instances for pull requests.

## Mental model

```text
push / hook / manual
       ↓
    BUILD (no disk mount)
       ↓
 PRE-DEPLOY (new image; optional)
       ↓
 NEW INSTANCES + HEALTH CHECKS
       ↓
 TRAFFIC SWITCH (if healthy)
       ↓
 OLD INSTANCES DRAIN (maxShutdownDelaySeconds)
```

If deploys “succeed” in UI but never take traffic, check **`healthCheckPath`** and **`PORT`** first.
