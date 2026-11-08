---
name: grafana-dashboards
description: Design, build, review and provision Grafana dashboards (RED/USE layout, timeseries/stat/table/heatmap panels, template variables, file provisioning, dashboards-as-code) and the matching Grafana-managed alert rules. Use when creating or reviewing a Grafana dashboard or moving dashboards into version control; for deploying the Grafana/Loki/Tempo stack itself use implementing-observability.
risk: safe
source: community
date_added: "2026-02-27"
---

# Grafana Dashboards

## Inputs to pin first

- **Installed Grafana version.** Panel JSON and alerting differ by version. Grafana 11 removed legacy dashboard-embedded alerts. Angular-based panels such as old `graph` panel are disabled by default from Grafana 11, with removal following. Use `timeseries` and Grafana-managed alert rules. Export panel from target instance to see its schema.
- Datasource type and **UID**, metric names, labels, units. Inspect real series first.
- Questions each dashboard answers, plus its audience (on-call triage, service owner, capacity review, business).

## Design procedure

1. **One question per panel.** Write question as panel description ("Are users getting errors right now?").
2. **Lay out top-down:** impact first (stat panels: error rate, p95 latency, throughput vs SLO), then trends (timeseries), then diagnostic detail (tables, heatmaps, per-instance breakdowns).
3. **Pick a method:** RED for request-driven services (Rate, Errors, Duration), USE for resources (Utilization, Saturation, Errors).
4. **Keep ratios honest:** numerator and denominator over same labels and range. Show "No data" as no data, never as healthy 0.
5. **Use variables** (`$namespace`, `$service`) instead of per-service copies. Set units and thresholds on every panel.
6. **Test** with known incident window, zero traffic, empty variable selection, multi-select. Hand-check one value (e.g. 5 errors / 100 requests displays 5%).

## Panel examples (current panel types)

PromQL examples assume Prometheus-style `http_requests_total` and `http_request_duration_seconds` histograms. Adapt names to your metrics.

```json
{
  "type": "timeseries",
  "title": "Error rate (5xx)",
  "description": "Share of requests failing with 5xx, by service",
  "datasource": { "type": "prometheus", "uid": "${datasource}" },
  "targets": [{
    "refId": "A",
    "expr": "sum by (service) (rate(http_requests_total{status=~\"5..\", service=~\"$service\"}[5m])) / sum by (service) (rate(http_requests_total{service=~\"$service\"}[5m]))",
    "legendFormat": "{{service}}"
  }],
  "fieldConfig": { "defaults": { "unit": "percentunit", "min": 0 } },
  "gridPos": { "x": 0, "y": 4, "w": 12, "h": 8 }
}
```

```json
{
  "type": "stat",
  "title": "p95 latency",
  "datasource": { "type": "prometheus", "uid": "${datasource}" },
  "targets": [{
    "refId": "A",
    "expr": "histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{service=~\"$service\"}[5m])))"
  }],
  "options": { "reduceOptions": { "calcs": ["lastNotNull"], "values": false }, "colorMode": "value" },
  "fieldConfig": { "defaults": {
    "unit": "s",
    "thresholds": { "mode": "absolute", "steps": [
      { "color": "green", "value": null }, { "color": "orange", "value": 0.5 }, { "color": "red", "value": 1 }
    ] }
  } }
}
```

| Panel | Use for | Notes |
|---|---|---|
| `stat` | Current headline value vs threshold | Use `lastNotNull`. Set unit and thresholds |
| `timeseries` | Trends, comparisons | Replaces legacy `graph` panel |
| `table` | Per-instance/per-route detail | Instant query + `format: table`. `organize` transform renames columns |
| `heatmap` | Latency distribution | Query `sum by (le) (rate(..._bucket[5m]))` with `format: heatmap` |
| `bargauge` | Ranked top-N | Pair with `topk()` |

### Variables

```json
"templating": { "list": [
  { "name": "datasource", "type": "datasource", "query": "prometheus" },
  { "name": "namespace", "type": "query", "datasource": { "type": "prometheus", "uid": "${datasource}" },
    "query": "label_values(kube_pod_info, namespace)", "refresh": 1 },
  { "name": "service", "type": "query", "datasource": { "type": "prometheus", "uid": "${datasource}" },
    "query": "label_values(http_requests_total{namespace=\"$namespace\"}, service)", "refresh": 2,
    "multi": true, "includeAll": true }
] }
```

Use `=~"$service"` for multi-value variables. Keep variable queries cheap. High-cardinality `label_values` lookups slow every dashboard load.

## Alerting (Grafana-managed alert rules)

Do not put alerts in panel JSON. Current Grafana stores alert rules separately from dashboards. Build rule in UI against target version, then **export it** (alert rule → More → Export, YAML/JSON/HCL) and commit export. Provisioning file shape:

```yaml
# provisioning/alerting/api-alerts.yaml
apiVersion: 1
groups:
  - orgId: 1
    name: api-slo
    folder: Production
    interval: 1m
    rules:
      - uid: api-error-rate
        title: API 5xx error rate above 5%
        condition: C
        for: 5m
        noDataState: NoData        # missing data is not "OK"
        execErrState: Error
        labels: { severity: page, team: api }
        annotations:
          summary: "5xx ratio {{ $values.B }} on {{ $labels.service }}"
          runbook_url: https://example.internal/runbooks/api-error-rate
        data:
          # refId A = query, B = reduce, C = threshold; copy these blocks from a UI export
          # for your Grafana version rather than writing the model by hand.
```

Rules for every alert: symptom-based, owner label, runbook link, threshold justified by SLO, notification routing via contact points/notification policies (also provisionable), one test fire.

## Provisioning and dashboards as code

**File provisioning** (`provisioning/dashboards/dashboards.yaml`):

```yaml
apiVersion: 1
providers:
  - name: default
    orgId: 1
    folder: Production
    type: file
    disableDeletion: true
    allowUiUpdates: false        # repo is the source of truth
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
```

Provisioned dashboard files hold dashboard model itself (`{"title": ..., "panels": [...]}`), not `{"dashboard": {...}}` wrapper used by HTTP API. Give every dashboard stable `uid`. Reference datasources by `${datasource}` variable or fixed UID so imports work across environments.

| Approach | When |
|---|---|
| Exported JSON in git + file provisioning | Few dashboards, edited in UI then exported |
| Terraform `grafana` provider (`grafana_folder`, `grafana_dashboard`, `grafana_rule_group`, contact points) | Grafana managed alongside other infra |
| Generated code (Grafonnet/Jsonnet, Grafana Foundation SDK) | Many similar dashboards. Enforce conventions in code |

```hcl
resource "grafana_folder" "production" {
  title = "Production"
}

resource "grafana_dashboard" "api" {
  folder      = grafana_folder.production.uid
  config_json = file("${path.module}/dashboards/api-overview.json")
}
```

Check argument names in installed provider version's docs. Keep secrets (API keys, datasource passwords) out of exported JSON.

## Review checklist

- [ ] Each panel has title, description, unit, sensible thresholds.
- [ ] Top row answers "is it broken and how badly" without scrolling.
- [ ] Percentiles from histograms, not averages. Ratios over identical populations.
- [ ] No legacy `graph` panels or embedded `alert` blocks (on Grafana 11+).
- [ ] Variables work with All, single and empty selections.
- [ ] Dashboard has stable `uid`, lives in git, imports cleanly into staging folder.

## References

- `references/dashboard-design.md`: short design-review procedure (inputs, verification cases).
- `resources/implementation-playbook.md`: step-by-step build-and-validate procedure for new dashboard.

## Related skills

- `observability-and-instrumentation`: emitting RED/USE metrics these dashboards need.
- `implementing-observability`: deploying Grafana, Prometheus/Mimir, Loki and Tempo.
- `creating-dashboards` / `visualizing-data`: general dashboard and chart design outside Grafana.
