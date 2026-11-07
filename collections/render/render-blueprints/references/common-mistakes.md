# Common Blueprint Mistakes

## 1. Setting `branch` while using preview environments

**Mistake:** Global or service-level `branch` (e.g. `main`) set while PR previews enabled.

**Effect:** Previews build **pull request** refs. Forced single branch can make preview builds ignore PR commit under test, undermining PR workflows.

**Fix:** Use default branch settings for production services; let previews use PR head refs. Avoid hardcoding production `branch` on services that must track arbitrary PRs. Check preview behavior in Dashboard after changes.

---

## 2. `buildFilter` sync — omitting `paths` clears filters

**Mistake:** Syncing Blueprint whose `buildFilter` **omits** `paths` or `ignoredPaths` keys.

**Effect:** Missing keys may be read as “set to empty,” **replacing** existing path filters with empty lists. Result: builds on every unrelated commit, or broken ignore rules.

**Fix:** Always specify **full** desired `paths` and `ignoredPaths` arrays with `buildFilter`. Filters replace, not patch.

---

## 3. `readReplicas` — empty list or name drift

**Mistake A:** Setting `readReplicas: []` to “leave unchanged.”

**Effect:** **Empty list destroys all read replicas**.

**Mistake B:** Renaming replica identifiers in YAML without understanding reconcile behavior.

**Effect:** Unmatched replicas may be **removed** and new ones **created**, causing churn or brief disconnects.

**Fix:** `readReplicas` is authoritative. Only include entries you want to exist. Prefer additive changes, made carefully; validate in non-production environment first.

---

## 4. Deprecated fields

| Deprecated | Use instead |
|------------|-------------|
| `env` | `runtime` |
| `redis` (service type) | `keyvalue` (alias `redis` if still accepted—prefer `keyvalue` in new files) |
| `autoDeploy` | `autoDeployTrigger` |
| `pullRequestPreviewsEnabled` | `previews.generation` (`off` / `manual` / `automatic`) |

**Fix:** Migrate to current keys; validate schema against `https://render.com/schema/render.yaml.json`.

---

## 5. Same resource defined in multiple places

**Mistake:** Service or database defined at **root** and again under **project environment**, or duplicated across environments.

**Effect:** Confusing reconcile behavior, name collisions, or unintended duplicate infrastructure.

**Fix:** Each logical resource lives in **exactly one** scope: root `services` / `databases` **or** one `projects[].environments[]` block, not both.

---

## 6. Mixing flexible and non-flexible instance types in `previewPlan`

**Mistake:** `plan` uses one instance family; `previewPlan` uses incompatible (flex vs non-flex) type.

**Effect:** Preview deploy failures or plan validation errors.

**Fix:** Match preview plan family to primary plan constraints per Render’s current plan catalog. If unsure, set `previewPlan` to conservative same-family plan or validate via CLI.

---

## 7. `fromService` / `fromDatabase` to non-existent names

**Mistake:** Typo in `name` under `fromService` / `fromDatabase`, or reference before resource is defined in scope.

**Effect:** Validation failures or broken deploys with missing env vars.

**Fix:** Keep one naming table; grep `name:` and cross-check references. Run `render blueprints validate`.

---

## 8. Forgetting `ipAllowList` on Key Value

**Mistake:** Provisioning `keyvalue` without proper network restrictions.

**Effect:** Security exposure or service creation errors (per account defaults and product requirements).

**Fix:** Always set **`ipAllowList`** to explicit CIDRs for your private services and regions.

---

## 9. Hardcoding connection strings

**Mistake:** Pasting `postgres://...` or `redis://...` into `value:`.

**Effect:** Secrets in Git, drift across environments, rotation pain, preview breakage.

**Fix:** Use **`fromDatabase`** and **`fromService`** with `connectionString` or discrete fields; use **`generateValue`** for app secrets.

---

## Quick prevention

1. `render blueprints validate` (CLI v2.7.0+).
2. JSON Schema in IDE: `https://render.com/schema/render.yaml.json`.
3. Diff previews against production wiring before merging.
