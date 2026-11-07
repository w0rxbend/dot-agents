# Autoscaling configuration guide

Render autoscaling applies to **Web Services**, **Private Services**, and **Background Workers** on **Professional+** workspaces.

## Enabling autoscaling

- **Dashboard:** open service → **Scaling** → **Autoscaling**, then set min/max and targets.
- **Blueprint:** add top-level **`scaling`** object to service (example below).

At least **one** of **CPU** or **memory** targeting must be enabled. If both disabled, autoscaling is off.

## Choosing targets

- **CPU target** — Best for **compute-bound** services. Common starting point: **~70%**; tune after observing real traffic and latency.
- **Memory target** — Best for **memory-bound** services. Common starting point: **~80%**; adjust on OOM risk or wasted RAM.
- **Both CPU and memory** — **Recommended** for many production services. Render computes scale per metric and applies **larger** instance count (more aggressive scale-out).

## Min and max instances

- **minInstances** — Baseline capacity. Use **at least 1**; use **2+** to keep capacity during scale events or rolling behavior (subject to plan and service type).
- **maxInstances** — **Cost ceiling** and upper bound. Platform still enforces **absolute maximum of 100** instances per service.

## Monitoring

- Watch **scaling events** and instance count in **Dashboard**.
- Correlate with **CPU/memory** charts (and logs) to see if targets are too loose (high cost) or too tight (latency, errors).

## Blueprint example

```yaml
scaling:
  minInstances: 2
  maxInstances: 10
  targetCPUPercent: 70
  targetMemoryPercent: 80
```

For one signal only, omit a target field or disable that metric in Dashboard (e.g. memory-only for cache-heavy worker).

## Common mistakes

| Mistake | Effect |
|---------|--------|
| **CPU and memory targets too low** | **Over-provisioning**, higher cost than needed |
| **Targets too high** | **Under-provisioning**, slow responses or instability |
| **No practical max** (max too high vs traffic) | Risk of **many instances** during attacks or bugs—**100** still hard cap |
| **Autoscaling + persistent disk** | **Not allowed**—disk-attached services stay **single-instance** |
| **`numInstances` alongside `scaling`** | **Autoscaling wins**; manual count does not override policy |

## Preview environments

- **Autoscaling is disabled** in preview environments.
- Preview instances typically follow **`minInstances`** (or equivalent preview defaults), not dynamic scaling. Do not assume preview behavior matches production autoscaling.
