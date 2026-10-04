---
name: airgradient-clients
description: Maintain AirGradient LAN clients, dashboards, shared desktop configuration, Android monitoring, and observability data contracts across worxbend repositories.
license: MIT
---

# AirGradient client ecosystem

Identify the transport and application before editing: local device JSON at `/measures/current`, Prometheus `/metrics`, a proxy/history API, and an AQI LED device protocol are different contracts. The Android, GTK, CLI, GNOME, QML, and Solid clients have different lifecycles and persistence. Preserve the selected frontend/runtime rather than scaffolding a generic replacement.

Read [measurements-config.md](references/measurements-config.md) for optional measurements, units, alias precedence, timestamps, and shared JSON updates. Read [lifecycle-observability.md](references/lifecycle-observability.md) for UI polling, monitoring, Prometheus series, and validation boundaries.

Keep parsing, units, AQI/status calculation, display formatting, networking, and notification decisions separable. Missing or invalid sensor values must remain visibly missing; a failed fetch must not become a fresh zero reading. Verify status/color/label changes against the current project's fixtures and threshold source, without claiming a medical assessment.

Respect local-only intent. Do not add cloud accounts, analytics, proxy dependence, or public exposure as incidental improvements. Use synthetic device addresses and payloads in tests. Follow each repository's actual wrapper, language, and CI gates; Mill is preferred for new JVM builds, while existing Android Gradle projects stay on their chosen build.
