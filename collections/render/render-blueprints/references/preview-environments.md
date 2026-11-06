# Preview Environments

Pull request (PR) previews spin up temporary stacks from Blueprint to test each PR in isolation.

## Top-level `previews`

```yaml
previews:
  generation: off          # default
  expireAfterDays: 3
```

### `previews.generation`

| Value | Behavior |
|-------|----------|
| `off` | No automatic preview creation from PRs (default). |
| `manual` | Previews created on demand (Dashboard/workflow action; exact UX may vary by integration). |
| `automatic` | Previews created for eligible PRs per Render’s Git integration rules. |

### `previews.expireAfterDays`

- Positive integer: auto-**delete** preview environments after **N** days, controlling cost and clutter.
- For “no expiry” behavior, omit or set per product/docs.

---

## Service-level override

Individual services may override preview generation:

```yaml
services:
  - type: web
    name: api
    runtime: node
    # ...
    previews:
      generation: off
```

Use when heavy or sensitive service should not run in every preview (e.g. workers touching billing).

---

## `previewPlan` constraints

- **`previewPlan`** selects instance type for preview **service** instances.
- **Cannot mix** flexible and non-flexible instance types between **`plan`** and **`previewPlan`** in ways Render rejects (same family constraints as production).
- If previews fail validation, align `previewPlan` with primary `plan` category or pick supported preview size.

---

## Database previews: `previewDiskSizeGB`

- Preview databases may use **`previewDiskSizeGB`** (and related preview fields per schema) for smaller/cheaper storage than production.
- Keep disk large enough for migrations and CI seed data.

---

## `sync: false` env vars in previews

- Env vars with **`sync: false`** are **excluded** from automatic preview configuration.
- **Users must set these manually** on preview services (Dashboard or automation), or app may fail at runtime (missing secrets).

**Mitigation:** Prefer per-preview generated secrets, non-secret placeholders, or CI pipeline injection into preview env, as security model allows.

---

## Autoscaling in previews

- **Autoscaling is disabled** in preview environments.
- Instance counts follow **minimum instance** behavior (pinned to floor: usually `scaling.minInstances` when autoscaling exists, or single instance).
- Do not rely on preview traffic to test autoscale rules; test scaling in staging/production-like environments.

---

## PR workflow — how previews map to Git

1. **Pull request** opened against tracked branch (e.g. `main`).
2. Render uses **PR head commit** (and Blueprint at that revision) to propose or create preview stack, per `previews.generation` and service overrides.
3. **Build filters** and **branch** settings on services still matter: misconfigured `branch` can break expectation that previews track PR (see `common-mistakes.md`).
4. When PR closes or merges, previews typically get torn down per product rules; **`expireAfterDays`** enforces maximum lifetime regardless.

---

## Checklist

- [ ] `previews.generation` matches team workflow (`off` / `manual` / `automatic`).
- [ ] `expireAfterDays` set if org needs automatic cleanup.
- [ ] `previewPlan` compatible with primary `plan`.
- [ ] `previewDiskSizeGB` (if used) enough for migrations.
- [ ] No reliance on `sync: false` secrets without preview secret strategy.
- [ ] Service-level `previews` overrides reviewed for workers/cron/private services.

Validate with `render blueprints validate` and `https://render.com/schema/render.yaml.json`.
