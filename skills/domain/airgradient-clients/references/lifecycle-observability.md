# Polling, monitoring, and observability

## Polling belongs to an owned lifecycle

One owner schedules shared device fetch; panels consume snapshots instead of each creating a poller. Bound timeouts, cancel obsolete requests, ignore results from old URL/session. On UI/extension/widget stop, dispose timers, listeners, subscriptions, chart observers, file monitors. Use the framework's own lifecycle tools; Relm4 messages, GNOME cancellables, QML timers, Kotlin scopes, Solid cleanup are different APIs.

Prefer source-derived transitions: loading, configured/unconfigured, fresh/stale, unreachable, recovered. Failed next request must not clear good snapshot. Do not report cached successful reading as completed new check. Pair units and status text with color/icons so unknown glyphs or color perception do not hide meaning.

## Android monitoring

Foreground refresh, always-on foreground monitoring, battery-friendly periodic work share persisted notification decision state. Respect opt-in, notification permission, severity, cooldown, stale-data, recovery, device-unreachable behavior. Clearing device URL stops monitoring and clears its diagnostics. Persisted notification state does not imply persisted history.

New DataStore or credential: keep privacy/backup rules aligned. Reviewed Android app excludes local device settings and monitoring state from backup/device transfer. Do not silently add analytics, cloud history, or remote services. See [monitoring modes, persistence, and privacy contract](https://github.com/worxbend/airgradient-android/blob/f25ec0419cc1ff2d590b2de4b84d1485877967c0/README.md) and [Gradle test, lint, detekt, and packaging gates](https://github.com/worxbend/airgradient-android/blob/f25ec0419cc1ff2d590b2de4b84d1485877967c0/.github/workflows/android.yml).

## Metrics and history are different transports

AirGradient observability: vmagent on LAN edge host scrapes `/metrics`, sends HTTPS authenticated remote_write to VictoriaMetrics; Grafana/Go expose data. Local current-measurement endpoint does not replace this history pipeline. Preserve metric-key/query mappings, units, label filtering, time-window/step validation, context deadlines, cache keys.

Reviewed service: zero series means empty result, multiple matching series means error. Do not take first series as the sensor unless API deliberately promises it. Relative windows and explicit millisecond ranges need distinct cache identities. Current-value TTL is not history freshness guarantee. See [query, caching, range, and series handling](https://github.com/worxbend/airgradient-observability/blob/6e2b2c65ca6c9fbb7ea0ad9020e349126c77077c/app/backend/internal/metrics/service.go) and [edge/OCI architecture and frontend documentation scope](https://github.com/worxbend/airgradient-observability/blob/6e2b2c65ca6c9fbb7ea0ad9020e349126c77077c/README.md).

## Physical display boundaries

Neoncore receives classified status code; it does not calculate sensor thresholds. E-paper firmware has refresh guards and sleep/power limits browser dashboards lack. Before changing sender/receiver bytes or refresh behavior, use device's documented contract and host protocol tests. Firmware compile success is not evidence of panel health, battery life, or physical behavior. See [status-sender division of responsibility](https://github.com/worxbend/neoncore/blob/6eb16847d95ff6cd0847c32c1a3b698f3057ce98/README.md) and [e-paper refresh guard implementation](https://github.com/worxbend/airgradient-papr/blob/23f460b63de5db2785b106d35e5e11bbd2a4d3a7/src/adapters/epd_guard.cpp).

## Validation evidence

First run parser/model/notification tests without physical device, then repository-specific network fakes and UI tests. Independent tiers: Desktop/CLI Cargo tests, Android Gradle tests and instrumentation builds, GNOME Node/GJS validation, backend Go tests. State which live-device, Android runtime, shell session, Grafana, or physical-panel paths actually ran. Label mock or compile coverage as such.
