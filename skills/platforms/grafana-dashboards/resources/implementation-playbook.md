# Grafana dashboard implementation

## Inputs

Installed Grafana version, datasource UID, metric names/labels, viewer role, operational question.

## Procedure

1. Inspect real series and units before drafting panels. Choose service filter and time window. Keep numerator and denominator populations identical.
2. Build one representative panel in target Grafana version. Export its supported schema. Keep secrets out of exported JSON. Use stable datasource references.
3. Validate normal traffic, no traffic, missing data, known incident. Check variables, units, thresholds, query cost. Then import into staging folder and inspect rendered result.

## Worked example

API error panel: compare known 5-error/100-request sample with displayed 5%. Empty source must show no data, not healthy zero.

## Verification and handoff

Report actual files or configuration changed, checks performed, observed results, any untested environment. Keep original inputs and enough evidence to reproduce conclusion.

## Limitations

Legacy graph and embedded-alert JSON is not universally importable. Configure alert rules through installed version's supported interface.
