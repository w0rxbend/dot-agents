---
name: render-scaling
description: >-
  Scales Render services—configures autoscaling targets, chooses instance
  types, sets manual instance counts, and optimizes cost. Use when the user
  needs to handle more traffic, set up autoscaling, pick the right instance
  type, reduce costs, or troubleshoot scaling behavior like slow scale-down or
  stuck instances.
license: MIT
compatibility: Render web services, private services, and background workers
metadata:
  author: Render
  version: "1.0.0"
  category: operations
---

# Render Scaling

## When to Use

- Set or change **instance count** (Dashboard, CLI, API, or Blueprint)
- Configure **autoscaling** (min/max, CPU and memory targets)
- Choose **vertical** (plan) vs **horizontal** (more instances) scaling
- **Constraints** (disks, static sites, cron/workflows, 100-instance cap)
- **Cost** of multi-instance and per-second billing
- **Blueprint** fields: `numInstances`, `scaling`, `plan`

## Manual Scaling

- Set **instance count** from **1 to 100** via **Dashboard**, **CLI**, or **API**.
- **All instances share same instance type** (plan); cannot mix plans on one service.
- Changes apply **immediately**: Render **provisions** new instances, **deprovisions** excess capacity.

## Autoscaling

- **Professional and higher** workspaces only.
- Configure **minimum** and **maximum** instances and **CPU** and/or **memory** utilization targets (**1–90%** each).
- **At least one metric must be enabled** (CPU or memory). If **both** CPU and memory autoscaling toggles **off**, autoscaling **disabled**.
- If **both** manual instance settings and autoscaling set, **autoscaling wins**—manual count does not override active policy.

## Autoscaling Formula

Render computes candidate instance count from utilization vs target:

`new_instances = ceil(current_instances * (current_utilization / target_utilization))`

- With **both** CPU and memory targets set, platform uses **larger** of the two `new_instances` values (more conservative scale-out).

## Scaling Constraints

| Constraint | Behavior |
|------------|----------|
| **Per service** | **Maximum 100** instances |
| **Persistent disk** | **Cannot** scale to multiple instances—**single instance only** |
| **Static sites** | **Not** scalable (served by CDN) |
| **Cron jobs & Workflows** | Scaling model **does not apply** (different execution model) |

## Scale-Down Behavior

- **Scale-up** is **immediate** when utilization supports it.
- **Scale-down** waits **a few minutes** after conditions allow reduction (**spike protection**).

## Instance Types

- In Blueprints, instance type is **`plan`** field (e.g. `standard`, `pro`).
- Options span **free** / **starter** through **standard**, **pro**, **pro_plus**, **pro_max**, **pro_ultra**—each with defined **CPU** and **RAM** (see `references/instance-types.md`).

### Vertical vs Horizontal

| Need | Approach | When |
|------|----------|------|
| More throughput | **Horizontal** (add instances) | Stateless services, request-based workloads |
| More RAM/CPU per process | **Vertical** (upgrade **plan**) | Memory-intensive or single-threaded apps |
| Both | **Combine** | Right-size plan, then scale out for traffic |

## Cost Patterns

- **Per-second billing**; **no separate fee** for scaling actions.
- Pay roughly **compute time × number of running instances** (see [Render pricing](https://render.com/pricing) for current rates).
- **Right-size** by monitoring **CPU and memory** utilization (see **render-monitor**).

## Blueprint Configuration

**Manual instance count:**

```yaml
numInstances: 3
```

**Autoscaling:**

```yaml
scaling:
  minInstances: 1
  maxInstances: 10
  targetCPUPercent: 70
  targetMemoryPercent: 80
```

**Instance type (plan):**

```yaml
plan: standard
```

Do not rely on `numInstances` to cap autoscaling when a `scaling` block is present—**autoscaling takes precedence**. Preview scaling behavior: see `references/autoscaling-guide.md`.

## References

| Topic | File |
|--------|------|
| Plan names, CPU/RAM, flexible vs non-flexible, free tier | `references/instance-types.md` |
| Enabling autoscaling, targets, min/max, mistakes, previews | `references/autoscaling-guide.md` |

## Related Skills

- **render-web-services** — Web Service settings, disks, deploy lifecycle
- **render-background-workers** — Worker-specific configuration and scaling context
- **render-blueprints** — Full Blueprint schema and field reference
- **render-monitor** — Metrics, logs, and utilization for right-sizing
