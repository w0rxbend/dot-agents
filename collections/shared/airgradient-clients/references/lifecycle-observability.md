# Polling, monitoring, and observability

## Polling belongs to an owned lifecycle

One owner should schedule a shared device fetch; panels consume snapshots rather than each creating a poller. Bound timeouts, cancel obsolete requests, and ignore results belonging to an old URL/session. Dispose timers, listeners, subscriptions, chart observers, and file monitors when the UI/extension/widget stops. Keep the existing framework's lifecycle tools: Relm4 messages, GNOME cancellables, QML timers, Kotlin scopes, and Solid cleanup are different APIs.

Prefer source-derived state transitions for loading, configured/unconfigured, fresh/stale, unreachable, and recovered. Do not clear a good snapshot merely because the next request failed, or report a cached successful reading as a completed new check. Render units and status text together with color/icons so unknown glyphs or color perception do not hide meaning.

## Android monitoring

Foreground refresh, always-on foreground monitoring, and battery-friendly periodic work share persisted notification decision state. Respect opt-in, notification permission, severity, cooldown, stale-data, recovery, and device-unreachable behavior. Clearing the device URL stops monitoring and clears its diagnostics. Historical readings are not automatically persisted just because notification state is.

Keep privacy/backup rules aligned when adding another DataStore or credential. The reviewed Android app excludes local device settings and monitoring state from backup/device transfer. Don't silently add analytics, cloud history, or remote services. See [monitoring modes, persistence, and privacy contract](https://github.com/worxbend/airgradient-android/blob/f25ec0419cc1ff2d590b2de4b84d1485877967c0/README.md) and [Gradle test, lint, detekt, and packaging gates](https://github.com/worxbend/airgradient-android/blob/f25ec0419cc1ff2d590b2de4b84d1485877967c0/.github/workflows/android.yml).

## Metrics and history are different transports

AirGradient observability scrapes `/metrics` on a LAN edge host with vmagent, sends HTTPS authenticated remote_write to VictoriaMetrics, and exposes data through Grafana/Go. A local current-measurement endpoint does not replace that historical pipeline. Preserve metric-key/query mappings, units, label filtering, time-window/step validation, context deadlines, and cache keys.

The reviewed service distinguishes zero series (empty result) from multiple matching series (an error). Do not select an arbitrary sensor by taking the first series unless the API deliberately promises that behavior. Relative windows and explicit millisecond ranges need distinct cache identities; don't reuse a current-value TTL as a history freshness guarantee. See [query, caching, range, and series handling](https://github.com/worxbend/airgradient-observability/blob/6e2b2c65ca6c9fbb7ea0ad9020e349126c77077c/app/backend/internal/metrics/service.go) and [edge/OCI architecture and frontend documentation scope](https://github.com/worxbend/airgradient-observability/blob/6e2b2c65ca6c9fbb7ea0ad9020e349126c77077c/README.md).

## Physical display boundaries

Neoncore receives a classified status code; it does not calculate sensor thresholds. E-paper firmware has refresh guards and sleep/power constraints unlike a browser dashboard. Use the device's documented contract and host protocol tests before changing sender/receiver bytes or refresh behavior. Do not treat a successful firmware compile as evidence of panel health, battery life, or physical behavior. See [status-sender division of responsibility](https://github.com/worxbend/neoncore/blob/6eb16847d95ff6cd0847c32c1a3b698f3057ce98/README.md) and [e-paper refresh guard implementation](https://github.com/worxbend/airgradient-papr/blob/23f460b63de5db2785b106d35e5e11bbd2a4d3a7/src/adapters/epd_guard.cpp).

## Validation evidence

Run parser/model/notification tests without a physical device first, then repository-specific network fakes and UI tests. Desktop/CLI Cargo tests, Android Gradle tests and instrumentation builds, GNOME Node/GJS validation, and backend Go tests are independent tiers. State which live-device, Android runtime, shell session, Grafana, or physical-panel paths were actually exercised. Mock or compile coverage must remain labeled as such.
