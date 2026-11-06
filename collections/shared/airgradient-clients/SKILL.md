---
name: airgradient-clients
description: Maintain AirGradient LAN clients, dashboards, shared desktop configuration, Android monitoring, and observability data contracts across worxbend repositories.
license: MIT
---

# AirGradient client ecosystem

Identify transport and app before editing. Distinct contracts: local device JSON at `/measures/current`, Prometheus `/metrics`, proxy/history API, AQI LED device protocol. Android, GTK, CLI, GNOME, QML, and Solid clients differ in lifecycle and persistence. Keep chosen frontend/runtime; no generic replacement.

Read [measurements-config.md](references/measurements-config.md) for optional measurements, units, alias precedence, timestamps, shared JSON updates. Read [lifecycle-observability.md](references/lifecycle-observability.md) for UI polling, monitoring, Prometheus series, validation boundaries.

Keep parsing, units, AQI/status calculation, display formatting, networking, notification decisions separable. Missing or invalid sensor values stay visibly missing; failed fetch must not become fresh zero. Check status/color/label changes against current project's fixtures and threshold source. No medical-assessment claims.

Respect local-only intent: do not add cloud accounts, analytics, proxy dependence, or public exposure as incidental improvements. Use synthetic device addresses and payloads in tests. Follow each repository's real wrapper, language, CI gates. Prefer Mill for new JVM builds; existing Android Gradle projects keep their build.
