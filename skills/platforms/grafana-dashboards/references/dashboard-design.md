# Dashboard design review

## Inputs

Per panel, name operational question, service filter, datasource, expected units.

## Procedure and verification

Impact and trend first, then diagnostic detail. Keep ratios on same population and time range. Include descriptions, refresh time, no-data state. Test known incident, zero traffic, empty variable selection, multiple service selections. Compare hand-calculated fixture to displayed value.

## Limitations

Dashboard JSON depends on Grafana version. Export from installed instance. Test import in staging folder. Panel colors and labels alone do not establish alert policy.
